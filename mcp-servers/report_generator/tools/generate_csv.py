"""
Generate CSV report for Slovak tax compliance.
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Input schema for MCP
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "start_date": {
            "type": "string",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
            "description": "Start date (YYYY-MM-DD)",
        },
        "end_date": {
            "type": "string",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
            "description": "End date (YYYY-MM-DD)",
        },
        "vehicle_id": {
            "type": "string",
            "description": "Filter by vehicle ID (optional)",
        },
        "business_only": {
            "type": "boolean",
            "default": True,
            "description": "Include only business trips (default: true)",
        },
        "output_filename": {
            "type": "string",
            "description": "Output filename (optional, default: YYYY-MM-report.csv)",
        },
    },
    "required": ["start_date", "end_date"],
}


def get_data_path() -> Path:
    """Get data directory path from environment or use default"""
    data_path = os.getenv("DATA_PATH", "~/Documents/MileageLog/data")
    return Path(data_path).expanduser()


def load_vehicle(vehicle_id: str) -> Dict[str, Any]:
    """Load vehicle data by ID"""
    data_path = get_data_path()
    vehicle_file = data_path / "vehicles" / f"{vehicle_id}.json"

    if not vehicle_file.exists():
        raise ValueError(f"Vehicle not found: {vehicle_id}")

    with open(vehicle_file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_trips_in_range(start_date: str, end_date: str, vehicle_id: str = None) -> List[Dict[str, Any]]:
    """
    Load all trips within date range.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        vehicle_id: Filter by vehicle (optional)

    Returns:
        List of trip dictionaries
    """
    data_path = get_data_path()
    trips_path = data_path / "trips"

    if not trips_path.exists():
        return []

    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    trips = []

    # Iterate through monthly folders
    for month_folder in sorted(trips_path.iterdir()):
        if not month_folder.is_dir():
            continue

        # Load all trip files in this month
        for trip_file in month_folder.glob("*.json"):
            if trip_file.name == "index.json":
                continue

            try:
                with open(trip_file, "r", encoding="utf-8") as f:
                    trip = json.load(f)

                # Filter by vehicle if specified
                if vehicle_id and trip.get("vehicle_id") != vehicle_id:
                    continue

                # Filter by date range
                trip_date = datetime.fromisoformat(trip["trip_start_datetime"].split("T")[0])
                if start_dt <= trip_date <= end_dt:
                    trips.append(trip)

            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip invalid trip files
                continue

    return trips


def calculate_summary(trips: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics for trips"""
    if not trips:
        return {
            "total_trips": 0,
            "total_distance_km": 0.0,
            "total_fuel_liters": 0.0,
            "total_cost_incl_vat": 0.0,
            "total_vat": 0.0,
            "average_efficiency_l_per_100km": 0.0,
        }

    total_distance = sum(trip.get("distance_km", 0) for trip in trips)
    total_fuel = sum(trip.get("fuel_consumption_liters", 0) for trip in trips if trip.get("fuel_consumption_liters"))

    # Calculate average efficiency (weighted by distance)
    total_efficiency_weighted = 0.0
    total_distance_with_efficiency = 0.0

    for trip in trips:
        if trip.get("fuel_efficiency_l_per_100km") and trip.get("distance_km"):
            efficiency = trip["fuel_efficiency_l_per_100km"]
            distance = trip["distance_km"]
            total_efficiency_weighted += efficiency * distance
            total_distance_with_efficiency += distance

    avg_efficiency = (
        total_efficiency_weighted / total_distance_with_efficiency
        if total_distance_with_efficiency > 0
        else 0.0
    )

    return {
        "total_trips": len(trips),
        "total_distance_km": round(total_distance, 2),
        "total_fuel_liters": round(total_fuel, 2),
        "average_efficiency_l_per_100km": round(avg_efficiency, 2),
    }


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate CSV mileage log report.

    Args:
        arguments: Tool arguments (start_date, end_date, vehicle_id, business_only, output_filename)

    Returns:
        Success status, output filename, and summary statistics
    """
    start_date = arguments["start_date"]
    end_date = arguments["end_date"]
    vehicle_id = arguments.get("vehicle_id")
    business_only = arguments.get("business_only", True)
    output_filename = arguments.get("output_filename")

    # Generate default filename if not provided
    if not output_filename:
        start_dt = datetime.fromisoformat(start_date)
        output_filename = f"{start_dt.strftime('%Y-%m')}-report.csv"

    # Load trips
    trips = load_trips_in_range(start_date, end_date, vehicle_id)

    # Filter business trips if requested
    if business_only:
        trips = [t for t in trips if t.get("purpose") == "Business"]

    if not trips:
        return {
            "success": True,
            "message": "No trips found matching criteria",
            "trip_count": 0,
        }

    # Load vehicle data for VIN (use first trip's vehicle if not specified)
    if not vehicle_id and trips:
        vehicle_id = trips[0].get("vehicle_id")

    vehicle = load_vehicle(vehicle_id) if vehicle_id else {}

    # Calculate summary
    summary = calculate_summary(trips)

    # Create output directory
    data_path = get_data_path()
    start_dt = datetime.fromisoformat(start_date)
    output_dir = data_path / "reports" / start_dt.strftime("%Y-%m")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / output_filename

    # Generate CSV
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
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
            "fuel_consumption_liters",
            "fuel_efficiency_l_per_100km",
            "reconstruction_method",
            "confidence_score",
        ]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for trip in trips:
            writer.writerow({
                "trip_date": trip.get("trip_start_datetime", "").split("T")[0],
                "driver_name": trip.get("driver_name", ""),
                "vehicle_vin": vehicle.get("vin", ""),
                "license_plate": vehicle.get("license_plate", ""),
                "trip_start_datetime": trip.get("trip_start_datetime", ""),
                "trip_end_datetime": trip.get("trip_end_datetime", ""),
                "trip_start_location": trip.get("trip_start_location", ""),
                "trip_end_location": trip.get("trip_end_location", ""),
                "distance_km": trip.get("distance_km", ""),
                "purpose": trip.get("purpose", ""),
                "business_description": trip.get("business_description", ""),
                "fuel_consumption_liters": trip.get("fuel_consumption_liters", ""),
                "fuel_efficiency_l_per_100km": trip.get("fuel_efficiency_l_per_100km", ""),
                "reconstruction_method": trip.get("reconstruction_method", ""),
                "confidence_score": trip.get("confidence_score", ""),
            })

    return {
        "success": True,
        "output_file": str(output_path),
        "summary": summary,
        "trip_count": len(trips),
    }
