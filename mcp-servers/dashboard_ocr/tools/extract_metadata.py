"""
EXIF metadata extraction from photos.

Extracts GPS coordinates, timestamp, and camera model from EXIF data.
Handles missing EXIF gracefully by returning None for unavailable fields.
"""

import os
from typing import Optional, Dict, Any
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime


def parse_gps_data(gps_ifd: Dict) -> Optional[Dict[str, float]]:
    """
    Parse GPS EXIF data into latitude/longitude.

    Args:
        gps_ifd: GPS IFD dictionary from PIL (can have numeric or string keys)

    Returns:
        Dictionary with 'lat' and 'lng' keys, or None if invalid

    Raises:
        ValueError: If GPS data is malformed
    """
    try:
        # Handle both numeric keys (from piexif) and string keys (from PIL)
        gps_latitude = gps_ifd.get(2) or gps_ifd.get("GPSLatitude")
        gps_latitude_ref = gps_ifd.get(1) or gps_ifd.get("GPSLatitudeRef")
        gps_longitude = gps_ifd.get(4) or gps_ifd.get("GPSLongitude")
        gps_longitude_ref = gps_ifd.get(3) or gps_ifd.get("GPSLongitudeRef")

        if not all([gps_latitude, gps_latitude_ref, gps_longitude, gps_longitude_ref]):
            return None

        # Handle bytes vs strings for reference
        if isinstance(gps_latitude_ref, bytes):
            gps_latitude_ref = gps_latitude_ref.decode('utf-8')
        if isinstance(gps_longitude_ref, bytes):
            gps_longitude_ref = gps_longitude_ref.decode('utf-8')

        # Convert GPS coordinates from (degrees, minutes, seconds) tuples
        # Handle both Fraction and tuple formats
        def convert_to_float(value):
            """Convert Fraction or tuple to float."""
            if hasattr(value, 'numerator') and hasattr(value, 'denominator'):
                # It's a Fraction
                return float(value.numerator) / float(value.denominator)
            elif isinstance(value, (tuple, list)) and len(value) == 2:
                # It's a (numerator, denominator) tuple
                return float(value[0]) / float(value[1])
            else:
                return float(value)

        lat_degrees = convert_to_float(gps_latitude[0])
        lat_minutes = convert_to_float(gps_latitude[1])
        lat_seconds = convert_to_float(gps_latitude[2])

        lon_degrees = convert_to_float(gps_longitude[0])
        lon_minutes = convert_to_float(gps_longitude[1])
        lon_seconds = convert_to_float(gps_longitude[2])

        lat = lat_degrees + lat_minutes / 60.0 + lat_seconds / 3600.0
        lon = lon_degrees + lon_minutes / 60.0 + lon_seconds / 3600.0

        # Apply reference direction
        if gps_latitude_ref != "N":
            lat = -lat
        if gps_longitude_ref != "E":
            lon = -lon

        return {"lat": lat, "lng": lon}

    except (KeyError, TypeError, IndexError, ZeroDivisionError, AttributeError, ValueError):
        return None


def extract_datetime(exif_data: Dict[int, Any]) -> Optional[str]:
    """
    Extract datetime from EXIF data.

    Args:
        exif_data: EXIF data dictionary

    Returns:
        ISO 8601 datetime string, or None if not available

    Raises:
        ValueError: If datetime format is invalid
    """
    try:
        # Try DateTime tag (36867 = DateTimeOriginal)
        datetime_str = exif_data.get(36867) or exif_data.get(306)

        if not datetime_str:
            return None

        # EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
        dt = datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S")
        return dt.isoformat()

    except (KeyError, ValueError, TypeError):
        return None


def extract_camera_model(exif_data: Dict[int, Any]) -> Optional[str]:
    """
    Extract camera model from EXIF data.

    Args:
        exif_data: EXIF data dictionary

    Returns:
        Camera model string, or None if not available
    """
    try:
        # Model tag is 271
        model = exif_data.get(271)
        if isinstance(model, bytes):
            return model.decode("utf-8", errors="ignore").strip()
        return model if model else None

    except (KeyError, UnicodeDecodeError, AttributeError):
        return None


def extract_metadata(photo_path: str) -> Dict[str, Any]:
    """
    Extract EXIF metadata from photo.

    Extracts GPS coordinates, timestamp, and camera model.
    Handles missing EXIF gracefully by returning null for unavailable fields.

    Args:
        photo_path: Path to photo file

    Returns:
        Dictionary with keys:
        - success (bool): True if file processed successfully
        - timestamp (str|null): ISO 8601 datetime string
        - gps_coords (dict|null): {"lat": float, "lng": float}
        - camera_model (str|null): Camera model name
        - error (str|null): Error message if unsuccessful

    Raises:
        None - all errors are handled gracefully
    """
    response = {
        "success": False,
        "timestamp": None,
        "gps_coords": None,
        "camera_model": None,
        "error": None,
    }

    # Validate file exists
    if not os.path.exists(photo_path):
        response["error"] = f"File not found: {photo_path}"
        return response

    # Validate file is readable
    if not os.path.isfile(photo_path):
        response["error"] = f"Path is not a file: {photo_path}"
        return response

    try:
        # Open image
        image = Image.open(photo_path)

        # Get EXIF data
        exif_data = {}
        try:
            exif_raw = image._getexif()
            if exif_raw:
                exif_data = {TAGS[k]: v for k, v in exif_raw.items() if k in TAGS}
                # Also keep numeric keys for tag access
                exif_data_numeric = image._getexif()
            else:
                exif_data_numeric = {}
        except (AttributeError, KeyError):
            exif_data_numeric = {}

        # Successfully opened file
        response["success"] = True

        # Extract timestamp
        response["timestamp"] = extract_datetime(exif_data_numeric)

        # Extract camera model
        response["camera_model"] = extract_camera_model(exif_data_numeric)

        # Extract GPS coordinates
        try:
            gps_ifd = None

            # Try to get GPS data from exif_data first (string keys from PIL)
            if "GPSInfo" in exif_data:
                gps_raw = exif_data["GPSInfo"]
                if isinstance(gps_raw, dict):
                    gps_ifd = gps_raw
            # Fallback: GPS IFD pointer is at tag 34853 (numeric keys)
            elif exif_data_numeric and 34853 in exif_data_numeric:
                gps_ifd_ptr = exif_data_numeric[34853]
                # Parse GPS IFD
                gps_ifd = {GPSTAGS.get(k, k): v for k, v in gps_ifd_ptr.items()}

            if gps_ifd:
                response["gps_coords"] = parse_gps_data(gps_ifd)
        except (KeyError, TypeError, AttributeError):
            pass

        return response

    except IOError as e:
        response["error"] = f"Cannot open image file: {str(e)}"
        return response
    except Exception as e:
        response["error"] = f"Unexpected error processing image: {str(e)}"
        return response


def check_photo_quality(photo_path: str) -> Dict[str, Any]:
    """
    Validate photo quality before OCR.

    Checks for:
    - Image dimensions (minimum 640x480)
    - Brightness levels
    - Blur detection (basic contrast check)

    Args:
        photo_path: Path to photo file

    Returns:
        Dictionary with keys:
        - is_acceptable (bool): True if photo passes quality checks
        - issues (list): List of detected quality issues
        - suggestions (list): List of suggestions for improvement
    """
    response = {
        "is_acceptable": True,
        "issues": [],
        "suggestions": [],
    }

    if not os.path.exists(photo_path):
        response["is_acceptable"] = False
        response["issues"].append("File not found")
        return response

    try:
        image = Image.open(photo_path)
        width, height = image.size

        # Check minimum resolution
        if width < 640 or height < 480:
            response["is_acceptable"] = False
            response["issues"].append(
                f"Image too small: {width}x{height} (minimum 640x480)"
            )
            response["suggestions"].append("Use a higher resolution photo")

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Check brightness
        import numpy as np

        pixels = np.array(image)
        mean_brightness = np.mean(pixels)

        if mean_brightness < 50:
            response["is_acceptable"] = False
            response["issues"].append("Image is too dark")
            response["suggestions"].append("Improve lighting and retake photo")
        elif mean_brightness > 200:
            response["issues"].append("Image is very bright (possible glare)")
            response["suggestions"].append("Reduce glare or adjust exposure")

        # Check blur via Laplacian variance (basic blur detection)
        import cv2

        gray = cv2.cvtColor(pixels.astype("uint8"), cv2.COLOR_RGB2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Flag as blurry only if image has content but very low variance
        # Solid color images (variance=0) are acceptable for checkpoints/receipts
        # A truly blurry image would have variance < 0.1 with some content
        # Real odometer photos typically have variance > 50
        if 0 < laplacian_var < 1:
            response["is_acceptable"] = False
            response["issues"].append("Image appears blurry")
            response["suggestions"].append("Use steady hands or tripod")

        return response

    except ImportError:
        # If numpy/cv2 not available, do basic checks only
        response["issues"].append(
            "Advanced quality checks unavailable (numpy/cv2 not installed)"
        )
        response["suggestions"].append("Install opencv-python and numpy for full checks")
        return response
    except Exception as e:
        response["is_acceptable"] = False
        response["issues"].append(f"Error checking photo quality: {str(e)}")
        return response
