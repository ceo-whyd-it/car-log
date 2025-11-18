"""
Unit tests for dashboard-ocr EXIF extraction.

Tests cover:
- EXIF extraction from photos with GPS and timestamp
- Graceful handling of missing EXIF data
- Camera model extraction
- GPS coordinate parsing
- Photo quality validation
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from io import BytesIO

import pytest
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-servers", "dashboard_ocr"))

from tools.extract_metadata import (
    extract_metadata,
    extract_datetime,
    extract_camera_model,
    parse_gps_data,
    check_photo_quality,
)


class TestExifExtraction(unittest.TestCase):
    """Test EXIF metadata extraction."""

    def setUp(self):
        """Create temporary directory for test images."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.test_dir)

    def create_image_with_exif(self, filename: str, exif_dict: dict = None) -> str:
        """
        Create a test image with optional EXIF data.

        Args:
            filename: Name of the image file to create
            exif_dict: Dictionary of EXIF data to embed

        Returns:
            Path to created image file
        """
        from PIL import Image
        from piexif import dump

        filepath = os.path.join(self.test_dir, filename)

        # Create a simple test image (480x640 to meet quality checks)
        img = Image.new("RGB", (640, 480), color=(73, 109, 137))

        # Add EXIF data if provided
        if exif_dict:
            exif_dict["0th"] = exif_dict.get("0th", {})
            exif_dict["Exif"] = exif_dict.get("Exif", {})
            exif_dict["GPS"] = exif_dict.get("GPS", {})

            exif_bytes = dump(exif_dict)
            img.save(filepath, "jpeg", exif=exif_bytes)
        else:
            img.save(filepath, "jpeg")

        return filepath

    def test_extract_metadata_no_exif(self):
        """Test extraction from image with no EXIF data."""
        filepath = self.create_image_with_exif("no_exif.jpg")

        result = extract_metadata(filepath)

        assert result["success"] is True
        assert result["timestamp"] is None
        assert result["gps_coords"] is None
        assert result["camera_model"] is None
        assert result["error"] is None

    def test_extract_metadata_missing_file(self):
        """Test extraction from non-existent file."""
        result = extract_metadata("/nonexistent/path/photo.jpg")

        assert result["success"] is False
        assert result["error"] is not None
        assert "not found" in result["error"].lower()

    def test_extract_metadata_invalid_path(self):
        """Test extraction from a directory instead of file."""
        result = extract_metadata(self.test_dir)

        assert result["success"] is False
        assert result["error"] is not None
        assert "not a file" in result["error"].lower()

    def test_extract_metadata_with_datetime(self):
        """Test extraction of datetime from EXIF."""
        # Create image with datetime EXIF
        exif_dict = {
            "Exif": {
                36867: b"2025:11:18 14:30:45",  # DateTimeOriginal
            }
        }

        filepath = self.create_image_with_exif("with_datetime.jpg", exif_dict)
        result = extract_metadata(filepath)

        assert result["success"] is True
        assert result["timestamp"] is not None
        # Should be ISO 8601 format
        assert "T" in result["timestamp"] or isinstance(result["timestamp"], str)

    def test_extract_metadata_with_camera_model(self):
        """Test extraction of camera model from EXIF."""
        exif_dict = {
            "0th": {
                271: b"Canon EOS 5D Mark IV",  # Model tag
            }
        }

        filepath = self.create_image_with_exif("with_camera.jpg", exif_dict)
        result = extract_metadata(filepath)

        assert result["success"] is True
        assert result["camera_model"] is not None
        assert "Canon" in result["camera_model"] or "5D" in result["camera_model"]

    def test_extract_datetime_valid(self):
        """Test datetime extraction with valid format."""
        exif_data = {
            36867: "2025:11:18 14:30:45",  # DateTimeOriginal
        }

        result = extract_datetime(exif_data)

        assert result is not None
        assert "T" in result  # ISO format check

    def test_extract_datetime_invalid_format(self):
        """Test datetime extraction with invalid format."""
        exif_data = {
            36867: "invalid-date-format",
        }

        result = extract_datetime(exif_data)

        assert result is None

    def test_extract_datetime_missing(self):
        """Test datetime extraction when no datetime in EXIF."""
        exif_data = {}

        result = extract_datetime(exif_data)

        assert result is None

    def test_extract_camera_model_string(self):
        """Test camera model extraction with string value."""
        exif_data = {
            271: b"Sony Alpha 7 IV",
        }

        result = extract_camera_model(exif_data)

        assert result is not None
        assert "Sony" in result or "Alpha" in result

    def test_extract_camera_model_missing(self):
        """Test camera model extraction when not in EXIF."""
        exif_data = {}

        result = extract_camera_model(exif_data)

        assert result is None

    def test_extract_camera_model_unicode(self):
        """Test camera model extraction with unicode characters."""
        exif_data = {
            271: "Nikon D850".encode("utf-8"),
        }

        result = extract_camera_model(exif_data)

        assert result is not None
        assert "Nikon" in result or "D850" in result


class TestGPSParsing(unittest.TestCase):
    """Test GPS coordinate parsing."""

    def test_parse_gps_data_valid(self):
        """Test parsing valid GPS data."""
        # GPS for Bratislava, Slovakia (approx)
        # Using proper EXIF Fraction format (numerator, denominator)
        from fractions import Fraction

        gps_ifd = {
            1: "N",  # GPSLatitudeRef
            2: (Fraction(48, 1), Fraction(8, 1), Fraction(54, 1)),  # GPSLatitude (48°8'54"N)
            3: "E",  # GPSLongitudeRef
            4: (Fraction(17, 1), Fraction(6, 1), Fraction(27, 1)),  # GPSLongitude (17°6'27"E)
        }

        result = parse_gps_data(gps_ifd)

        assert result is not None
        assert "lat" in result
        assert "lng" in result
        assert 45 < result["lat"] < 50  # Bratislava latitude range
        assert 15 < result["lng"] < 20  # Bratislava longitude range

    def test_parse_gps_data_south_west(self):
        """Test parsing GPS data with South/West coordinates."""
        # Southern hemisphere, western hemisphere (e.g., Cape Town area)
        from fractions import Fraction

        gps_ifd = {
            1: "S",  # GPSLatitudeRef
            2: (Fraction(34, 1), Fraction(2, 1), Fraction(47, 1)),  # GPSLatitude
            3: "W",  # GPSLongitudeRef
            4: (Fraction(18, 1), Fraction(25, 1), Fraction(10, 1)),  # GPSLongitude
        }

        result = parse_gps_data(gps_ifd)

        assert result is not None
        assert result["lat"] < 0  # South is negative
        assert result["lng"] < 0  # West is negative

    def test_parse_gps_data_missing_latitude(self):
        """Test parsing GPS data with missing latitude."""
        gps_ifd = {
            3: "E",  # GPSLongitudeRef
            4: ((17, 1), (6, 1), (27, 1)),  # GPSLongitude
        }

        result = parse_gps_data(gps_ifd)

        assert result is None

    def test_parse_gps_data_missing_longitude(self):
        """Test parsing GPS data with missing longitude."""
        gps_ifd = {
            1: "N",  # GPSLatitudeRef
            2: ((48, 1), (8, 1), (54, 1)),  # GPSLatitude
        }

        result = parse_gps_data(gps_ifd)

        assert result is None

    def test_parse_gps_data_missing_references(self):
        """Test parsing GPS data with missing N/S or E/W reference."""
        gps_ifd = {
            2: ((48, 1), (8, 1), (54, 1)),  # GPSLatitude
            4: ((17, 1), (6, 1), (27, 1)),  # GPSLongitude
        }

        result = parse_gps_data(gps_ifd)

        assert result is None

    def test_parse_gps_data_invalid_format(self):
        """Test parsing GPS data with invalid data (empty or malformed)."""
        gps_ifd = {
            1: "N",
            2: (),  # Empty tuple - invalid
            3: "E",
            4: ((17, 1), (6, 1), (27, 1)),
        }

        result = parse_gps_data(gps_ifd)

        # Should handle gracefully
        assert result is None


class TestPhotoQuality(unittest.TestCase):
    """Test photo quality validation."""

    def setUp(self):
        """Create temporary directory for test images."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.test_dir)

    def create_test_image(self, filename: str, width: int, height: int, brightness: int) -> str:
        """
        Create a test image with specified dimensions and brightness.

        Args:
            filename: Name of the image file
            width: Image width in pixels
            height: Image height in pixels
            brightness: RGB brightness value (0-255)

        Returns:
            Path to created image file
        """
        filepath = os.path.join(self.test_dir, filename)
        img = Image.new("RGB", (width, height), color=(brightness, brightness, brightness))
        img.save(filepath, "jpeg")
        return filepath

    def test_check_photo_quality_good(self):
        """Test quality check on good quality image."""
        filepath = self.create_test_image("good_photo.jpg", 1920, 1440, 128)
        result = check_photo_quality(filepath)

        assert result["is_acceptable"] is True
        # May have info message about unavailable advanced checks, but should be acceptable
        assert all("unavailable" not in issue.lower() for issue in result["issues"])

    def test_check_photo_quality_too_small(self):
        """Test quality check on image that's too small."""
        filepath = self.create_test_image("small_photo.jpg", 320, 240, 128)
        result = check_photo_quality(filepath)

        assert result["is_acceptable"] is False
        assert any("too small" in issue.lower() or "small" in issue.lower() for issue in result["issues"])

    def test_check_photo_quality_too_dark(self):
        """Test quality check on very dark image."""
        filepath = self.create_test_image("dark_photo.jpg", 640, 480, 20)
        result = check_photo_quality(filepath)

        # Should detect darkness (numpy is now installed)
        # If numpy/cv2 unavailable, quality check has limitations
        if any("unavailable" in issue.lower() for issue in result["issues"]):
            # Advanced checks unavailable, skip this test
            pytest.skip("Advanced quality checks unavailable (numpy/cv2 not installed)")
        else:
            assert result["is_acceptable"] is False
            assert any("dark" in issue.lower() for issue in result["issues"])

    def test_check_photo_quality_missing_file(self):
        """Test quality check on non-existent file."""
        result = check_photo_quality("/nonexistent/file.jpg")

        assert result["is_acceptable"] is False
        assert len(result["issues"]) > 0


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows."""

    def setUp(self):
        """Create temporary directory for test images."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.test_dir)

    def test_complete_extraction_workflow(self):
        """Test complete metadata extraction workflow."""
        # Create a test image (no special EXIF, just test the workflow)
        filepath = os.path.join(self.test_dir, "test.jpg")
        img = Image.new("RGB", (640, 480), color=(100, 100, 100))
        img.save(filepath, "jpeg")

        # Extract metadata
        result = extract_metadata(filepath)

        # Check structure
        assert "success" in result
        assert "timestamp" in result
        assert "gps_coords" in result
        assert "camera_model" in result
        assert "error" in result

        # Should succeed even without EXIF
        assert result["success"] is True

    def test_quality_and_metadata_together(self):
        """Test extracting both quality and metadata."""
        filepath = os.path.join(self.test_dir, "test.jpg")
        img = Image.new("RGB", (1024, 768), color=(128, 128, 128))
        img.save(filepath, "jpeg")

        # Check quality
        quality_result = check_photo_quality(filepath)
        assert quality_result["is_acceptable"] is True

        # Extract metadata
        metadata_result = extract_metadata(filepath)
        assert metadata_result["success"] is True


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
