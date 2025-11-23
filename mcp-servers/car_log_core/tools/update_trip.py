"""
Update existing trip to fix data (business description, driver name, etc.).

Priority: P0
Use case: Users must be able to correct trip data and fix mistakes.
"""

from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from ..storage import (
    get_data_path,
    atomic_write_json,
    read_json,
)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "trip_id": {
            "type": "string",
            "format": "uuid",
            "description": "Trip ID to update",
        },
        "updates": {
            "type": "object",
            "properties": {
                "driver_name": {
                    "type": "string",
                    "description": "Updated driver name",
                },
                "trip_start_datetime": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Updated trip start time",
                },
                "trip_end_datetime": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Updated trip end time",
                },
                "trip_start_location": {
                    "type": "string",
                    "description": "Updated trip origin",
                },
                "trip_end_location": {
                    "type": "string",
                    "description": "Updated trip destination",
                },
                "distance_km": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Updated distance",
                },
                "fuel_consumption_liters": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Updated fuel consumption",
                },
                "fuel_efficiency_l_per_100km": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Updated fuel efficiency in L/100km",
                },
                "purpose": {
                    "type": "string",
                    "enum": ["Business", "Personal"],
                    "description": "Updated trip purpose",
                },
                "business_description": {
                    "type": "string",
                    "description": "Updated business description",
                },
            },
            "description": "Fields to update (only specified fields will be changed)",
        },
    },
    "required": ["trip_id", "updates"],
}


def find_trip_file(trip_id: str, data_path: Path) -> Path:
    """
    Find trip file across all month folders.

    Args:
        trip_id: Trip ID
        data_path: Base data path

    Returns:
        Path to trip file or None if not found
    """
    trips_dir = data_path / "trips"

    if not trips_dir.exists():
        return None

    # Search through all month folders
    for month_folder in trips_dir.iterdir():
        if not month_folder.is_dir():
            continue

        trip_file = month_folder / f"{trip_id}.json"
        if trip_file.exists():
            return trip_file

    return None


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update trip fields.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with updated trip
    """
    try:
        # Extract required fields
        trip_id = arguments.get("trip_id", "").strip()
        updates = arguments.get("updates", {})

        # Validate required fields
        if not trip_id:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Trip ID is required",
                    "field": "trip_id",
                },
            }

        if not updates:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Updates object is required and cannot be empty",
                    "field": "updates",
                },
            }

        # Find trip
        data_path = get_data_path()
        trip_file = find_trip_file(trip_id, data_path)

        if trip_file is None:
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Trip not found: {trip_id}",
                },
            }

        # Read existing trip
        trip = read_json(trip_file)

        if trip is None:
            return {
                "success": False,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": f"Failed to read trip: {trip_id}",
                },
            }

        # Track which fields were updated
        updated_fields = []

        # Update driver name
        if "driver_name" in updates:
            trip["driver_name"] = updates["driver_name"]
            updated_fields.append("driver_name")

        # Update trip timing
        if "trip_start_datetime" in updates:
            trip["trip_start_datetime"] = updates["trip_start_datetime"]
            updated_fields.append("trip_start_datetime")

        if "trip_end_datetime" in updates:
            trip["trip_end_datetime"] = updates["trip_end_datetime"]
            updated_fields.append("trip_end_datetime")

        # Update locations
        if "trip_start_location" in updates:
            trip["trip_start_location"] = updates["trip_start_location"]
            updated_fields.append("trip_start_location")

        if "trip_end_location" in updates:
            trip["trip_end_location"] = updates["trip_end_location"]
            updated_fields.append("trip_end_location")

        # Update distance and fuel
        if "distance_km" in updates:
            trip["distance_km"] = updates["distance_km"]
            updated_fields.append("distance_km")

            # Recalculate fuel efficiency if we have fuel consumption
            if trip.get("fuel_consumption_liters") and updates["distance_km"] > 0:
                trip["fuel_efficiency_l_per_100km"] = (
                    trip["fuel_consumption_liters"] / updates["distance_km"]
                ) * 100

        if "fuel_consumption_liters" in updates:
            trip["fuel_consumption_liters"] = updates["fuel_consumption_liters"]
            updated_fields.append("fuel_consumption_liters")

            # Recalculate fuel efficiency if we have distance
            if trip.get("distance_km") and trip["distance_km"] > 0:
                trip["fuel_efficiency_l_per_100km"] = (
                    updates["fuel_consumption_liters"] / trip["distance_km"]
                ) * 100

        if "fuel_efficiency_l_per_100km" in updates:
            trip["fuel_efficiency_l_per_100km"] = updates["fuel_efficiency_l_per_100km"]
            updated_fields.append("fuel_efficiency_l_per_100km")

        # Update purpose and business description
        if "purpose" in updates:
            trip["purpose"] = updates["purpose"]
            updated_fields.append("purpose")

            # If purpose changed to Personal, clear business_description
            if updates["purpose"] == "Personal" and "business_description" in trip:
                del trip["business_description"]
                updated_fields.append("business_description (cleared)")

        if "business_description" in updates:
            # Validate: business_description only valid if purpose is Business
            if trip.get("purpose") == "Business":
                trip["business_description"] = updates["business_description"]
                updated_fields.append("business_description")
            else:
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "business_description can only be set when purpose is Business",
                        "field": "business_description",
                    },
                }

        # Update metadata
        now = datetime.utcnow().isoformat() + "Z"
        trip["updated_at"] = now

        # Atomic write
        atomic_write_json(trip_file, trip)

        return {
            "success": True,
            "trip_id": trip_id,
            "trip": trip,
            "updated_fields": updated_fields,
            "updated_at": now,
            "message": "Trip updated successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
