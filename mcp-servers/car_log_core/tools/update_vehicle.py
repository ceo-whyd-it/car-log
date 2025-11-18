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

        if "name" in arguments and arguments["name"]:
            vehicle["name"] = arguments["name"].strip()
            updated = True

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

        return {
            "success": True,
            "vehicle": vehicle,
            "message": "Vehicle updated successfully" if updated else "No changes made",
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
