"""
List all vehicles with optional filters.
"""

from typing import Dict, Any

from ..storage import get_data_path, list_json_files, read_json

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "active_only": {
            "type": "boolean",
            "default": True,
            "description": "Only return active vehicles",
        },
        "fuel_type": {
            "type": "string",
            "enum": ["Diesel", "Gasoline", "LPG", "Hybrid", "Electric"],
            "description": "Filter by fuel type",
        },
    },
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    List all vehicles.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with list of vehicles
    """
    try:
        active_only = arguments.get("active_only", True)
        fuel_type_filter = arguments.get("fuel_type")

        # Read all vehicle files
        data_path = get_data_path()
        vehicles_dir = data_path / "vehicles"

        vehicle_files = list_json_files(vehicles_dir)
        vehicles = []

        for vehicle_file in vehicle_files:
            vehicle = read_json(vehicle_file)
            if vehicle is None:
                continue

            # Apply filters
            if active_only and not vehicle.get("active", True):
                continue

            if fuel_type_filter and vehicle.get("fuel_type") != fuel_type_filter:
                continue

            vehicles.append(vehicle)

        # Sort by created_at (most recent first)
        vehicles.sort(key=lambda v: v.get("created_at", ""), reverse=True)

        return {
            "success": True,
            "vehicles": vehicles,
            "count": len(vehicles),
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
