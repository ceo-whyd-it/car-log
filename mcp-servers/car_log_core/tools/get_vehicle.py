"""
Get vehicle by ID.
"""

from typing import Dict, Any

from ..storage import get_data_path, read_json

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "vehicle_id": {
            "type": "string",
            "format": "uuid",
            "description": "Vehicle ID",
        },
    },
    "required": ["vehicle_id"],
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve vehicle by ID.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with vehicle data or error
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

        # Read vehicle file
        data_path = get_data_path()
        vehicle_file = data_path / "vehicles" / f"{vehicle_id}.json"

        vehicle = read_json(vehicle_file)

        if vehicle is None:
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Vehicle not found: {vehicle_id}",
                    "field": "vehicle_id",
                },
            }

        return {
            "success": True,
            "vehicle": vehicle,
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
