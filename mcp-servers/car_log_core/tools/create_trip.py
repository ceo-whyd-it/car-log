"""
Create trip with Slovak compliance fields.

Key requirements:
- Validate all Slovak compliance fields (driver_name, trip timing, locations)
- Calculate fuel efficiency in L/100km (NEVER km/L)
- Store in monthly folder: data/trips/YYYY-MM/{trip_id}.json
- Use atomic write pattern
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
        "vehicle_id": {
            "type": "string",
            "format": "uuid",
            "description": "Vehicle ID",
        },
        "start_checkpoint_id": {
            "type": "string",
            "format": "uuid",
            "description": "Starting checkpoint ID",
        },
        "end_checkpoint_id": {
            "type": "string",
            "format": "uuid",
            "description": "Ending checkpoint ID",
        },
        "driver_name": {
            "type": "string",
            "description": "Full name of driver (MANDATORY for Slovak VAT Act 2025)",
        },
        "trip_start_datetime": {
            "type": "string",
            "format": "date-time",
            "description": "When trip started (ISO 8601)",
        },
        "trip_end_datetime": {
            "type": "string",
            "format": "date-time",
            "description": "When trip ended (ISO 8601)",
        },
        "trip_start_location": {
            "type": "string",
            "description": "Trip origin (separate from fuel station)",
        },
        "trip_end_location": {
            "type": "string",
            "description": "Trip destination",
        },
        "distance_km": {
            "type": "number",
            "minimum": 0,
            "description": "Trip distance in kilometers",
        },
        "fuel_consumption_liters": {
            "type": "number",
            "minimum": 0,
            "description": "Fuel consumed during trip in liters",
        },
        "fuel_efficiency_l_per_100km": {
            "type": "number",
            "minimum": 0,
            "description": "Fuel efficiency in L/100km (European standard)",
        },
        "purpose": {
            "type": "string",
            "enum": ["Business", "Personal"],
            "description": "Trip purpose",
        },
        "business_description": {
            "type": "string",
            "description": "Description of business purpose (required if purpose=Business)",
        },
        "reconstruction_method": {
            "type": "string",
            "enum": ["manual", "template", "geo_assisted"],
            "default": "manual",
            "description": "How trip was created",
        },
        "template_id": {
            "type": "string",
            "format": "uuid",
            "description": "Template ID if created from template",
        },
        "confidence_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "description": "Reconstruction confidence score (0-100)",
        },
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
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create new trip.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with trip data
    """
    try:
        # Extract required fields
        vehicle_id = arguments.get("vehicle_id", "").strip()
        start_checkpoint_id = arguments.get("start_checkpoint_id", "").strip()
        end_checkpoint_id = arguments.get("end_checkpoint_id", "").strip()
        driver_name = arguments.get("driver_name", "").strip()
        trip_start_datetime = arguments.get("trip_start_datetime", "").strip()
        trip_end_datetime = arguments.get("trip_end_datetime", "").strip()
        trip_start_location = arguments.get("trip_start_location", "").strip()
        trip_end_location = arguments.get("trip_end_location", "").strip()
        distance_km = arguments.get("distance_km")
        purpose = arguments.get("purpose", "").strip()

        # Validate required fields
        if not vehicle_id:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Vehicle ID is required",
                    "field": "vehicle_id",
                },
            }

        if not driver_name:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Driver name is MANDATORY for Slovak VAT Act 2025",
                    "field": "driver_name",
                },
            }

        if purpose not in ["Business", "Personal"]:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Purpose must be 'Business' or 'Personal'",
                    "field": "purpose",
                },
            }

        # Validate business trips have description
        if purpose == "Business" and not arguments.get("business_description"):
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Business description is required for Business trips",
                    "field": "business_description",
                },
            }

        # Verify vehicle exists
        data_path = get_data_path()
        vehicle_file = data_path / "vehicles" / f"{vehicle_id}.json"
        vehicle = read_json(vehicle_file)

        if vehicle is None:
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Vehicle not found: {vehicle_id}",
                },
            }

        # Parse datetime
        try:
            trip_start_dt = datetime.fromisoformat(trip_start_datetime.replace("Z", "+00:00"))
        except ValueError:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid trip_start_datetime format (use ISO 8601)",
                    "field": "trip_start_datetime",
                },
            }

        try:
            trip_end_dt = datetime.fromisoformat(trip_end_datetime.replace("Z", "+00:00"))
        except ValueError:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid trip_end_datetime format (use ISO 8601)",
                    "field": "trip_end_datetime",
                },
            }

        # Validate trip end is after start
        if trip_end_dt <= trip_start_dt:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Trip end datetime must be after start datetime",
                    "field": "trip_end_datetime",
                },
            }

        # Calculate fuel efficiency if fuel consumption provided
        fuel_efficiency = arguments.get("fuel_efficiency_l_per_100km")
        fuel_consumption = arguments.get("fuel_consumption_liters")

        if fuel_consumption and distance_km > 0 and not fuel_efficiency:
            # Calculate L/100km (European standard)
            fuel_efficiency = (fuel_consumption / distance_km) * 100

        # Generate trip ID
        trip_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        # Build trip object
        trip = {
            "trip_id": trip_id,
            "vehicle_id": vehicle_id,
            "start_checkpoint_id": start_checkpoint_id,
            "end_checkpoint_id": end_checkpoint_id,
            "driver_name": driver_name,
            "trip_start_datetime": trip_start_datetime,
            "trip_end_datetime": trip_end_datetime,
            "trip_start_location": trip_start_location,
            "trip_end_location": trip_end_location,
            "distance_km": distance_km,
            "fuel_consumption_liters": fuel_consumption,
            "fuel_efficiency_l_per_100km": fuel_efficiency,
            "purpose": purpose,
            "business_description": arguments.get("business_description"),
            "reconstruction_method": arguments.get("reconstruction_method", "manual"),
            "template_id": arguments.get("template_id"),
            "confidence_score": arguments.get("confidence_score"),
            "created_at": now,
        }

        # Remove None values
        trip = {k: v for k, v in trip.items() if v is not None}

        # Save to monthly folder (based on trip_start_datetime)
        trips_base = data_path / "trips"
        month_folder = ensure_month_folder(trips_base, trip_start_dt)
        trip_file = month_folder / f"{trip_id}.json"

        atomic_write_json(trip_file, trip)

        return {
            "success": True,
            "trip_id": trip_id,
            "trip": trip,
            "message": "Trip created successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
