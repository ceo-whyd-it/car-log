"""
Update vehicle details.
"""

from datetime import datetime
from typing import Dict, Any

from ..storage import get_data_path, read_json, atomic_write_json

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "vehicle_id": {
            "type": "string",
            "format": "uuid",
            "description": "Vehicle ID",
        },
        "name": {
            "type": "string",
            "description": "Updated vehicle name",
        },
        "license_plate": {
            "type": "string",
            "description": "Updated license plate (requires confirmation)",
        },
        "confirm_plate_change": {
            "type": "boolean",
            "description": "Set to true to confirm license plate change (important for tax compliance)",
        },
        "average_efficiency_l_per_100km": {
            "type": "number",
            "minimum": 3.0,
            "maximum": 25.0,
            "description": "Updated average fuel efficiency",
        },
        "active": {
            "type": "boolean",
            "description": "Set vehicle active status",
        },
    },
    "required": ["vehicle_id"],
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update vehicle details.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with updated vehicle data
    """
    try:
        vehicle_id = arguments.get("vehicle_id", "").strip()

        if not vehicle_id:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Vehicle ID is required",
                    "field": "vehicle_id",
                },
            }

        # Read existing vehicle
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

        # Update fields if provided
        updated = False
        warnings = []

        if "name" in arguments and arguments["name"]:
            vehicle["name"] = arguments["name"].strip()
            updated = True

        # Handle license plate change with confirmation
        if "license_plate" in arguments and arguments["license_plate"]:
            new_plate = arguments["license_plate"].strip().upper()
            old_plate = (vehicle.get("license_plate") or "").upper()  # Normalize for comparison

            # Check if plate is actually changing
            if new_plate != old_plate:
                # Require confirmation for plate changes
                if not arguments.get("confirm_plate_change", False):
                    return {
                        "success": False,
                        "error": {
                            "code": "CONFIRMATION_REQUIRED",
                            "message": f"License plate change requires confirmation (changing from '{old_plate}' to '{new_plate}'). This is important for tax compliance and vehicle records. Set 'confirm_plate_change: true' to proceed.",
                            "field": "confirm_plate_change",
                            "current_plate": old_plate,
                            "new_plate": new_plate,
                        },
                    }

                # Validate new plate format (warn if non-standard)
                import re
                if not re.match(r"^[A-Z]{2}-[0-9]{3}[A-Z]{2}$", new_plate):
                    if len(new_plate) < 3:
                        return {
                            "success": False,
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": "License plate is too short (minimum 3 characters)",
                                "field": "license_plate",
                            },
                        }
                    warnings.append(f"New license plate '{new_plate}' doesn't match standard Slovak format XX-123XX. This may be a foreign or special plate.")

                # Update the plate
                vehicle["license_plate"] = new_plate
                updated = True
                warnings.append(f"License plate changed from '{old_plate}' to '{new_plate}' - ensure this is updated in tax records")

        if "average_efficiency_l_per_100km" in arguments:
            efficiency = arguments["average_efficiency_l_per_100km"]
            if efficiency is not None and (efficiency < 3.0 or efficiency > 25.0):
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Efficiency must be between 3.0 and 25.0 L/100km",
                        "field": "average_efficiency_l_per_100km",
                    },
                }
            vehicle["average_efficiency_l_per_100km"] = efficiency
            updated = True

        if "active" in arguments:
            vehicle["active"] = arguments["active"]
            updated = True

        if updated:
            vehicle["updated_at"] = datetime.utcnow().isoformat() + "Z"
            atomic_write_json(vehicle_file, vehicle)

        result = {
            "success": True,
            "vehicle": vehicle,
            "message": "Vehicle updated successfully" if updated else "No changes made",
        }

        # Add warnings if any
        if warnings:
            result["warnings"] = warnings

        return result

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
