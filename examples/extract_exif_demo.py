#!/usr/bin/env python3
"""
Demonstration of EXIF extraction from photos using dashboard-ocr MCP server.

This example shows:
1. Extracting GPS coordinates from a dashboard photo
2. Extracting timestamp from a receipt photo
3. Validating photo quality before processing
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-servers", "dashboard_ocr"))

from tools.extract_metadata import extract_metadata, check_photo_quality

# Import libraries for creating sample photos with EXIF
from PIL import Image
from fractions import Fraction
from piexif import dump


def create_sample_photo_with_gps(filepath: str, gps_lat: float, gps_lng: float) -> None:
    """
    Create a sample photo with GPS EXIF data.

    Args:
        filepath: Where to save the photo
        gps_lat: GPS latitude (decimal degrees)
        gps_lng: GPS longitude (decimal degrees)
    """
    # Convert decimal degrees to DMS (Degrees, Minutes, Seconds)
    def decimal_to_dms(decimal):
        minutes, seconds = divmod(abs(decimal) * 3600, 60)
        degrees, minutes = divmod(minutes, 60)
        return ((int(degrees), 1), (int(minutes), 1), (int(seconds * 100), 100))

    # Create image
    img = Image.new("RGB", (1024, 768), color=(150, 150, 150))

    # Create EXIF data
    exif_dict = {
        "0th": {
            271: b"Car Dashboard Camera",  # Model
            306: b"2025:11:18 14:30:45",  # DateTime
        },
        "Exif": {
            36867: b"2025:11:18 14:30:45",  # DateTimeOriginal
        },
        "GPS": {
            0: b"\x00\x00\x00\x02",  # GPSVersionID
            1: b"N" if gps_lat >= 0 else b"S",  # GPSLatitudeRef
            2: decimal_to_dms(gps_lat),  # GPSLatitude
            3: b"E" if gps_lng >= 0 else b"W",  # GPSLongitudeRef
            4: decimal_to_dms(gps_lng),  # GPSLongitude
        },
    }

    # Save with EXIF
    exif_bytes = dump(exif_dict)
    img.save(filepath, "jpeg", exif=exif_bytes)
    print(f"Created sample photo: {filepath}")


def main():
    """Run EXIF extraction demonstration."""
    print("=" * 70)
    print("EXIF Extraction Demonstration - Car Log dashboard-ocr MCP Server")
    print("=" * 70)

    # Create temporary directory for demo
    demo_dir = tempfile.mkdtemp()
    print(f"\nDemo directory: {demo_dir}\n")

    try:
        # Example 1: Extract GPS from dashboard photo (Bratislava)
        print("\n1. DASHBOARD PHOTO - GPS Extraction (Bratislava location)")
        print("-" * 70)

        dashboard_photo = os.path.join(demo_dir, "dashboard_bratislava.jpg")
        create_sample_photo_with_gps(
            dashboard_photo,
            gps_lat=48.1486,  # Bratislava latitude
            gps_lng=17.1077,  # Bratislava longitude
        )

        result = extract_metadata(dashboard_photo)
        print(f"\nExtraction Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result["gps_coords"]:
            lat = result["gps_coords"]["lat"]
            lng = result["gps_coords"]["lng"]
            print(f"\nInterpretation:")
            print(f"  Location: {lat:.4f}°N, {lng:.4f}°E")
            print(f"  Region: Bratislava, Slovakia")
            print(f"  Timestamp: {result['timestamp']}")
            print(f"  Camera: {result['camera_model'] or 'Not recorded'}")

        # Example 2: Extract data from receipt photo (Košice)
        print("\n\n2. RECEIPT PHOTO - GPS Extraction (Košice location)")
        print("-" * 70)

        receipt_photo = os.path.join(demo_dir, "receipt_kosice.jpg")
        create_sample_photo_with_gps(
            receipt_photo,
            gps_lat=48.7164,  # Košice latitude
            gps_lng=21.2611,  # Košice longitude
        )

        result = extract_metadata(receipt_photo)
        print(f"\nExtraction Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result["gps_coords"]:
            lat = result["gps_coords"]["lat"]
            lng = result["gps_coords"]["lng"]
            print(f"\nInterpretation:")
            print(f"  Location: {lat:.4f}°N, {lng:.4f}°E")
            print(f"  Region: Košice, Slovakia")
            print(f"  Distance from Bratislava: ~410 km")

        # Example 3: Photo quality validation
        print("\n\n3. PHOTO QUALITY VALIDATION")
        print("-" * 70)

        quality = check_photo_quality(dashboard_photo)
        print(f"\nQuality Check Result:")
        print(json.dumps(quality, indent=2, ensure_ascii=False))

        print(f"\nInterpretation:")
        print(f"  Acceptable for processing: {quality['is_acceptable']}")
        if quality["issues"]:
            print(f"  Issues: {', '.join(quality['issues'])}")
        if quality["suggestions"]:
            print(f"  Suggestions: {', '.join(quality['suggestions'])}")

        # Example 4: Photo without EXIF
        print("\n\n4. PHOTO WITHOUT EXIF DATA")
        print("-" * 70)

        no_exif_photo = os.path.join(demo_dir, "no_exif_photo.jpg")
        img = Image.new("RGB", (1024, 768), color=(200, 100, 100))
        img.save(no_exif_photo, "jpeg")
        print(f"Created photo without EXIF: {no_exif_photo}")

        result = extract_metadata(no_exif_photo)
        print(f"\nExtraction Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        print(f"\nInterpretation:")
        print(f"  Success: {result['success']}")
        print(f"  GPS found: {result['gps_coords'] is not None}")
        print(f"  Timestamp found: {result['timestamp'] is not None}")
        print(f"  Camera info found: {result['camera_model'] is not None}")
        print(f"  Error: {result['error']}")

    finally:
        # Clean up
        import shutil

        shutil.rmtree(demo_dir)
        print(f"\n\nCleaned up demo directory.")

    print("\n" + "=" * 70)
    print("EXIF Extraction Demonstration Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
