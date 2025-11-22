"""
Batch trip creation from reconstruction proposals.

This tool creates multiple trips atomically (all or nothing).
Primarily used for saving approved template-matched trip proposals.
"""

import uuid
from datetime import datetime
from typing import Dict, Any

from ..storage import (
    get_data_path,
    atomic_write_json,
    read_json,
    ensure_month_folder,
)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "trips": {
            "type": "array",
            "description": "Array of trip data objects",
            "items": {
                "type": "object",
                "properties": {
                    "vehicle_id": {"type": "string", "format": "uuid"},
                    "start_checkpoint_id": {"type": "string", "format": "uuid"},
                    "end_checkpoint_id": {"type": "string", "format": "uuid"},
                    "driver_name": {"type": "string"},
                    "trip_start_datetime": {"type": "string", "format": "date-time"},
                    "trip_end_datetime": {"type": "string", "format": "date-time"},
                    "trip_start_location": {"type": "string"},
                    "trip_end_location": {"type": "string"},
                    "distance_km": {"type": "number", "minimum": 0},
                    "fuel_consumption_liters": {"type": "number", "minimum": 0},
                    "fuel_efficiency_l_per_100km": {"type": "number", "minimum": 0},
                    "purpose": {"type": "string", "enum": ["Business", "Personal"]},
                    "business_description": {"type": "string"},
                    "reconstruction_method": {
                        "type": "string",
                        "enum": ["manual", "template", "geo_assisted"],
                    },
                    "template_id": {"type": "string", "format": "uuid"},
                    "confidence_score": {"type": "number", "minimum": 0, "maximum": 100},
                },
                "required": [
                    "vehicle_id",
                    "start_checkpoint_id",
                    "end_checkpoint_id",
                    "driver_name",
                    "trip_start_datetime",
                    "trip_end_datetime",
                    "trip_start_location",
                    "trip_end_location",
                    "distance_km",
                    "purpose",
                ],
            },
        },
    },
    "required": ["trips"],
}


def validate_trip(trip_data: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Validate a single trip object.

    Args:
        trip_data: Trip data to validate
        index: Trip index in batch (for error reporting)

    Returns:
        Error dict if validation fails, None if valid
    """
    # Check required fields
    required_fields = [
        "vehicle_id",
        "start_checkpoint_id",
        "end_checkpoint_id",
        "driver_name",
        "trip_start_datetime",
        "trip_end_datetime",
        "trip_start_location",
        "trip_end_location",
        "distance_km",
        "purpose",
    ]

    for field in required_fields:
        if not trip_data.get(field):
            return {
                "code": "VALIDATION_ERROR",
                "message": f"Trip {index}: {field} is required",
                "field": field,
                "trip_index": index,
            }

    # Validate driver name (Slovak compliance)
    if not trip_data.get("driver_name", "").strip():
        return {
            "code": "VALIDATION_ERROR",
            "message": f"Trip {index}: Driver name is MANDATORY for Slovak VAT Act 2025",
            "field": "driver_name",
            "trip_index": index,
        }

    # Validate purpose
    purpose = trip_data.get("purpose", "").strip()
    if purpose not in ["Business", "Personal"]:
        return {
            "code": "VALIDATION_ERROR",
            "message": f"Trip {index}: Purpose must be 'Business' or 'Personal'",
            "field": "purpose",
            "trip_index": index,
        }

    # Validate business trips have description
    if purpose == "Business" and not trip_data.get("business_description"):
        return {
            "code": "VALIDATION_ERROR",
            "message": f"Trip {index}: Business description is required for Business trips",
            "field": "business_description",
            "trip_index": index,
        }

    # Validate datetime format
    try:
        start_dt = datetime.fromisoformat(
            trip_data["trip_start_datetime"].replace("Z", "+00:00")
        )
    except (ValueError, AttributeError):
        return {
            "code": "VALIDATION_ERROR",
            "message": f"Trip {index}: Invalid trip_start_datetime format (use ISO 8601)",
            "field": "trip_start_datetime",
            "trip_index": index,
        }

    try:
        end_dt = datetime.fromisoformat(
            trip_data["trip_end_datetime"].replace("Z", "+00:00")
        )
    except (ValueError, AttributeError):
        return {
            "code": "VALIDATION_ERROR",
            "message": f"Trip {index}: Invalid trip_end_datetime format (use ISO 8601)",
            "field": "trip_end_datetime",
            "trip_index": index,
        }

    # Validate trip end is after start
    if end_dt <= start_dt:
        return {
            "code": "VALIDATION_ERROR",
            "message": f"Trip {index}: Trip end datetime must be after start datetime",
            "field": "trip_end_datetime",
            "trip_index": index,
        }

    return None


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create multiple trips atomically.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with created trip IDs
    """
    try:
        trips_data = arguments.get("trips", [])

        if not trips_data:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "At least one trip is required",
                    "field": "trips",
                },
            }

        if len(trips_data) > 100:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Maximum 100 trips per batch",
                    "field": "trips",
                },
            }

        data_path = get_data_path()

        # Validate all trips first (fail fast)
        for index, trip_data in enumerate(trips_data):
            error = validate_trip(trip_data, index)
            if error:
                return {"success": False, "error": error}

            # Verify vehicle exists
            vehicle_id = trip_data["vehicle_id"]
            vehicle_file = data_path / "vehicles" / f"{vehicle_id}.json"
            vehicle = read_json(vehicle_file)

            if vehicle is None:
                return {
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Trip {index}: Vehicle not found: {vehicle_id}",
                        "trip_index": index,
                    },
                }

        # All validations passed, create trips
        now = datetime.utcnow().isoformat() + "Z"
        created_trips = []
        created_trip_ids = []

        for trip_data in trips_data:
            # Generate trip ID
            trip_id = str(uuid.uuid4())

            # Parse start datetime for monthly folder
            trip_start_dt = datetime.fromisoformat(
                trip_data["trip_start_datetime"].replace("Z", "+00:00")
            )

            # Calculate fuel efficiency if needed
            fuel_efficiency = trip_data.get("fuel_efficiency_l_per_100km")
            fuel_consumption = trip_data.get("fuel_consumption_liters")
            distance_km = trip_data.get("distance_km", 0)

            if fuel_consumption and distance_km > 0 and not fuel_efficiency:
                # Calculate L/100km (European standard)
                fuel_efficiency = (fuel_consumption / distance_km) * 100

            # Build trip object
            trip = {
                "trip_id": trip_id,
                "vehicle_id": trip_data["vehicle_id"],
                "start_checkpoint_id": trip_data["start_checkpoint_id"],
                "end_checkpoint_id": trip_data["end_checkpoint_id"],
                "driver_name": trip_data["driver_name"],
                "trip_start_datetime": trip_data["trip_start_datetime"],
                "trip_end_datetime": trip_data["trip_end_datetime"],
                "trip_start_location": trip_data["trip_start_location"],
                "trip_end_location": trip_data["trip_end_location"],
                "distance_km": distance_km,
                "fuel_consumption_liters": fuel_consumption,
                "fuel_efficiency_l_per_100km": fuel_efficiency,
                "purpose": trip_data["purpose"],
                "business_description": trip_data.get("business_description"),
                "reconstruction_method": trip_data.get("reconstruction_method", "template"),
                "template_id": trip_data.get("template_id"),
                "confidence_score": trip_data.get("confidence_score"),
                "created_at": now,
            }

            # Remove None values
            trip = {k: v for k, v in trip.items() if v is not None}

            # Save to monthly folder
            trips_base = data_path / "trips"
            month_folder = ensure_month_folder(trips_base, trip_start_dt)
            trip_file = month_folder / f"{trip_id}.json"

            atomic_write_json(trip_file, trip)

            created_trips.append(trip)
            created_trip_ids.append(trip_id)

        return {
            "success": True,
            "trip_ids": created_trip_ids,
            "trips": created_trips,
            "count": len(created_trip_ids),
            "message": f"Created {len(created_trip_ids)} trips successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
