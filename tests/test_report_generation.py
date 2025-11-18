"""
Tests for report generation (CSV and PDF).

Slovak Tax Compliance Verification:
- All mandatory fields present (VIN, driver, trip timing, locations)
- L/100km fuel efficiency format
- Business trip filtering
- Summary calculations
"""

import csv
import json
import os
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add mcp-servers to path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-servers"))

from report_generator.tools.generate_csv import execute as generate_csv


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory with test data"""
    # Set environment variable
    os.environ["DATA_PATH"] = str(tmp_path)

    # Create directory structure
    (tmp_path / "vehicles").mkdir()
    (tmp_path / "trips" / "2025-11").mkdir(parents=True)
    (tmp_path / "reports" / "2025-11").mkdir(parents=True)

    # Create test vehicle
    vehicle = {
        "vehicle_id": "vehicle-001",
        "name": "Ford Transit",
        "vin": "WBAXX01234ABC5678",
        "license_plate": "BA-456CD",
        "fuel_type": "Diesel",
        "make": "Ford",
        "model": "Transit",
    }

    with open(tmp_path / "vehicles" / "vehicle-001.json", "w") as f:
        json.dump(vehicle, f)

    # Create test trips
    trips = [
        {
            "trip_id": "trip-001",
            "vehicle_id": "vehicle-001",
            "driver_name": "Ján Kováč",
            "trip_start_datetime": "2025-11-01T08:00:00+01:00",
            "trip_end_datetime": "2025-11-01T14:30:00+01:00",
            "trip_start_location": "Bratislava",
            "trip_end_location": "Košice",
            "distance_km": 410,
            "purpose": "Business",
            "business_description": "Warehouse pickup",
            "fuel_consumption_liters": 34.85,
            "fuel_efficiency_l_per_100km": 8.5,
            "reconstruction_method": "template",
            "confidence_score": 90.6,
        },
        {
            "trip_id": "trip-002",
            "vehicle_id": "vehicle-001",
            "driver_name": "Ján Kováč",
            "trip_start_datetime": "2025-11-08T08:00:00+01:00",
            "trip_end_datetime": "2025-11-08T14:30:00+01:00",
            "trip_start_location": "Košice",
            "trip_end_location": "Bratislava",
            "distance_km": 410,
            "purpose": "Business",
            "business_description": "Return from warehouse",
            "fuel_consumption_liters": 34.85,
            "fuel_efficiency_l_per_100km": 8.5,
            "reconstruction_method": "template",
            "confidence_score": 90.6,
        },
        {
            "trip_id": "trip-003",
            "vehicle_id": "vehicle-001",
            "driver_name": "Ján Kováč",
            "trip_start_datetime": "2025-11-15T10:00:00+01:00",
            "trip_end_datetime": "2025-11-15T11:00:00+01:00",
            "trip_start_location": "Bratislava",
            "trip_end_location": "Trnava",
            "distance_km": 50,
            "purpose": "Personal",
            "business_description": "",
            "fuel_consumption_liters": 4.25,
            "fuel_efficiency_l_per_100km": 8.5,
            "reconstruction_method": "manual",
            "confidence_score": 100.0,
        },
    ]

    for trip in trips:
        trip_file = tmp_path / "trips" / "2025-11" / f"{trip['trip_id']}.json"
        with open(trip_file, "w") as f:
            json.dump(trip, f)

    yield tmp_path

    # Cleanup
    del os.environ["DATA_PATH"]


@pytest.mark.asyncio
async def test_generate_csv_business_only(temp_data_dir):
    """Test CSV generation with business trips only"""
    result = await generate_csv({
        "start_date": "2025-11-01",
        "end_date": "2025-11-30",
        "business_only": True,
        "output_filename": "november-business-2025.csv",
    })

    assert result["success"] is True
    assert result["trip_count"] == 2  # Only 2 business trips
    assert "summary" in result

    summary = result["summary"]
    assert summary["total_trips"] == 2
    assert summary["total_distance_km"] == 820.0  # 410 + 410
    assert summary["total_fuel_liters"] == 69.7  # 34.85 + 34.85
    assert summary["average_efficiency_l_per_100km"] == 8.5

    # Verify file exists
    output_file = Path(result["output_file"])
    assert output_file.exists()

    # Verify CSV content
    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2

    # Verify mandatory Slovak compliance fields
    for row in rows:
        assert row["vehicle_vin"] == "WBAXX01234ABC5678"
        assert row["driver_name"] == "Ján Kováč"
        assert row["trip_start_datetime"]
        assert row["trip_end_datetime"]
        assert row["trip_start_location"]
        assert row["trip_end_location"]
        assert row["distance_km"]
        assert row["purpose"] == "Business"
        assert row["business_description"]
        assert "fuel_efficiency_l_per_100km" in reader.fieldnames  # Verify L/100km format


@pytest.mark.asyncio
async def test_generate_csv_all_trips(temp_data_dir):
    """Test CSV generation with all trips (business + personal)"""
    result = await generate_csv({
        "start_date": "2025-11-01",
        "end_date": "2025-11-30",
        "business_only": False,
        "output_filename": "november-all-2025.csv",
    })

    assert result["success"] is True
    assert result["trip_count"] == 3  # All 3 trips
    assert result["summary"]["total_trips"] == 3
    assert result["summary"]["total_distance_km"] == 870.0  # 410 + 410 + 50


@pytest.mark.asyncio
async def test_generate_csv_no_trips(temp_data_dir):
    """Test CSV generation with no matching trips"""
    result = await generate_csv({
        "start_date": "2025-12-01",
        "end_date": "2025-12-31",
        "business_only": True,
    })

    assert result["success"] is True
    assert result["trip_count"] == 0
    assert "No trips found" in result["message"]


@pytest.mark.asyncio
async def test_generate_csv_date_filtering(temp_data_dir):
    """Test CSV generation with specific date range"""
    # Only November 1-7 (should get 1 trip)
    result = await generate_csv({
        "start_date": "2025-11-01",
        "end_date": "2025-11-07",
        "business_only": True,
    })

    assert result["success"] is True
    assert result["trip_count"] == 1
    assert result["summary"]["total_distance_km"] == 410.0


@pytest.mark.asyncio
async def test_csv_field_completeness(temp_data_dir):
    """Verify all required Slovak compliance fields are present"""
    result = await generate_csv({
        "start_date": "2025-11-01",
        "end_date": "2025-11-30",
        "business_only": True,
        "output_filename": "compliance-check-2025.csv",
    })

    output_file = Path(result["output_file"])

    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        # Verify all mandatory fields are present
        required_fields = [
            "trip_date",
            "driver_name",
            "vehicle_vin",
            "license_plate",
            "trip_start_datetime",
            "trip_end_datetime",
            "trip_start_location",
            "trip_end_location",
            "distance_km",
            "purpose",
            "business_description",
            "fuel_efficiency_l_per_100km",
        ]

        for field in required_fields:
            assert field in fieldnames, f"Missing required field: {field}"


@pytest.mark.asyncio
async def test_default_filename_generation(temp_data_dir):
    """Test that default filename is generated correctly"""
    result = await generate_csv({
        "start_date": "2025-11-01",
        "end_date": "2025-11-30",
        "business_only": True,
    })

    assert result["success"] is True
    assert "2025-11-report.csv" in result["output_file"]


@pytest.mark.asyncio
async def test_summary_statistics_calculation(temp_data_dir):
    """Test summary statistics are calculated correctly"""
    result = await generate_csv({
        "start_date": "2025-11-01",
        "end_date": "2025-11-30",
        "business_only": True,
    })

    summary = result["summary"]

    # Verify calculations
    assert summary["total_trips"] == 2
    assert summary["total_distance_km"] == 820.0
    assert summary["total_fuel_liters"] == 69.7
    assert summary["average_efficiency_l_per_100km"] == 8.5

    # Verify correct L/100km format (not km/L)
    assert "l_per_100km" in str(result).lower()
    assert "km_per_l" not in str(result).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
