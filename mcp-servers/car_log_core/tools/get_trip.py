"""
Get trip by ID.

Retrieves trip data including all Slovak compliance fields.
"""

from typing import Dict, Any

from ..storage import get_data_path, read_json

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "trip_id": {
            "type": "string",
            "format": "uuid",
            "description": "Trip ID",
        },
    },
    "required": ["trip_id"],
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve trip by ID.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with trip data or error
    """
    try:
        trip_id = arguments.get("trip_id", "").strip()

        if not trip_id:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Trip ID is required",
                    "field": "trip_id",
                },
            }

        # Search through monthly folders
        data_path = get_data_path()
        trips_dir = data_path / "trips"

        if not trips_dir.exists():
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Trip not found: {trip_id}",
                },
            }

        # Search all month folders
        for month_folder in trips_dir.iterdir():
            if not month_folder.is_dir():
                continue

            trip_file = month_folder / f"{trip_id}.json"
            if trip_file.exists():
                trip = read_json(trip_file)
                if trip:
                    return {
                        "success": True,
                        "trip": trip,
                    }

        return {
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": f"Trip not found: {trip_id}",
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
