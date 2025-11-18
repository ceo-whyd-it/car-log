"""
Create vehicle tool with Slovak tax compliance (VIN validation).
"""

import re
import uuid
from datetime import datetime
from typing import Dict, Any

from ..storage import get_data_path, atomic_write_json

# Input schema for MCP
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 50,
            "description": "Human-readable vehicle name",
        },
        "license_plate": {
            "type": "string",
            "pattern": "^[A-Z]{2}-[0-9]{3}[A-Z]{2}$",
            "description": "Slovak license plate format (e.g., BA-456CD)",
        },
        "vin": {
            "type": "string",
            "pattern": "^[A-HJ-NPR-Z0-9]{17}$",
            "description": "Vehicle Identification Number (17 characters, no I/O/Q)",
        },
        "make": {
            "type": "string",
            "maxLength": 30,
            "description": "Vehicle manufacturer",
        },
        "model": {
            "type": "string",
            "maxLength": 30,
            "description": "Vehicle model",
        },
        "year": {
            "type": "integer",
            "minimum": 1900,
            "maximum": 2030,
            "description": "Manufacturing year",
        },
        "fuel_type": {
            "type": "string",
            "enum": ["Diesel", "Gasoline", "LPG", "Hybrid", "Electric"],
            "description": "Primary fuel type",
        },
        "initial_odometer_km": {
            "type": "integer",
            "minimum": 0,
            "maximum": 999999,
            "description": "Odometer reading when vehicle was added",
        },
    },
    "required": ["name", "license_plate", "vin", "fuel_type", "initial_odometer_km"],
}


def validate_vin(vin: str) -> tuple[bool, str]:
    """
    Validate VIN format (17 characters, no I/O/Q).

    Args:
        vin: VIN string to validate

    Returns:
        (is_valid, error_message)
    """
    if len(vin) != 17:
        return False, "VIN must be exactly 17 characters"

    if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin):
        return False, "VIN must contain only A-Z and 0-9 (excluding I, O, Q)"

    return True, ""


def validate_license_plate(plate: str) -> tuple[bool, str]:
    """
    Validate Slovak license plate format (XX-123XX).

    Args:
        plate: License plate string

    Returns:
        (is_valid, error_message)
    """
    if not re.match(r"^[A-Z]{2}-[0-9]{3}[A-Z]{2}$", plate):
        return False, "License plate must match Slovak format XX-123XX (e.g., BA-456CD)"

    return True, ""


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create new vehicle.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with vehicle data or error
    """
    try:
        # Extract and validate inputs
        name = arguments.get("name", "").strip()
        license_plate = arguments.get("license_plate", "").strip().upper()
        vin = arguments.get("vin", "").strip().upper()
        fuel_type = arguments.get("fuel_type")
        initial_odometer_km = arguments.get("initial_odometer_km")

        # Validate required fields
        if not name:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Vehicle name is required",
                    "field": "name",
                },
            }

        # Validate VIN
        vin_valid, vin_error = validate_vin(vin)
        if not vin_valid:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": vin_error,
                    "field": "vin",
                    "details": "VIN must be 17 characters (A-Z, 0-9, excluding I, O, Q)",
                },
            }

        # Validate license plate
        plate_valid, plate_error = validate_license_plate(license_plate)
        if not plate_valid:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": plate_error,
                    "field": "license_plate",
                },
            }

        # Validate fuel type
        valid_fuel_types = ["Diesel", "Gasoline", "LPG", "Hybrid", "Electric"]
        if fuel_type not in valid_fuel_types:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Fuel type must be one of: {', '.join(valid_fuel_types)}",
                    "field": "fuel_type",
                },
            }

        # Validate odometer
        if initial_odometer_km is None or initial_odometer_km < 0:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Initial odometer reading must be >= 0",
                    "field": "initial_odometer_km",
                },
            }

        # Generate vehicle ID
        vehicle_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        # Build vehicle object
        vehicle = {
            "vehicle_id": vehicle_id,
            "name": name,
            "license_plate": license_plate,
            "vin": vin,
            "make": arguments.get("make", "").strip() if arguments.get("make") else None,
            "model": arguments.get("model", "").strip() if arguments.get("model") else None,
            "year": arguments.get("year"),
            "fuel_type": fuel_type,
            "initial_odometer_km": initial_odometer_km,
            "current_odometer_km": initial_odometer_km,
            "average_efficiency_l_per_100km": None,
            "active": True,
            "created_at": now,
            "updated_at": now,
        }

        # Save to file
        data_path = get_data_path()
        vehicles_dir = data_path / "vehicles"
        vehicle_file = vehicles_dir / f"{vehicle_id}.json"

        atomic_write_json(vehicle_file, vehicle)

        return {
            "success": True,
            "vehicle_id": vehicle_id,
            "vehicle": vehicle,
            "message": "Vehicle created successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
