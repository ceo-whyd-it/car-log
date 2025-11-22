"""
Delete trip by ID.

Trips are stored in monthly folders: data/trips/YYYY-MM/{trip_id}.json
"""

import os
from datetime import datetime
from typing import Dict, Any

from ..storage import get_data_path, read_json

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "trip_id": {
            "type": "string",
            "description": "UUID of trip to delete",
        }
    },
    "required": ["trip_id"],
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Delete a trip.

    Args:
        arguments: Dictionary containing:
            - trip_id: UUID of trip to delete

    Returns:
        Success/error dictionary
    """
    trip_id = arguments["trip_id"]

    # Search through monthly folders to find the trip (use Path / operator)
    trips_base = get_data_path() / "trips"

    if not trips_base.exists():
        return {
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "No trips directory exists",
            },
        }

    # Search all monthly folders
    trip_file = None
    trip_data = None

    for month_dir in trips_base.iterdir():
        if not month_dir.is_dir():
            continue

        trip_path = month_dir / f"{trip_id}.json"
        if trip_path.exists():
            trip_file = trip_path
            trip_data = read_json(trip_path)
            break

    if trip_file is None:
        return {
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": f"Trip not found: {trip_id}",
            },
        }

    # Delete the trip file
    try:
        trip_file.unlink()  # Path.unlink() to delete file
    except OSError as e:
        return {
            "success": False,
            "error": {
                "code": "DELETE_ERROR",
                "message": f"Failed to delete trip file: {str(e)}",
            },
        }

    return {
        "success": True,
        "trip_id": trip_id,
        "deleted_trip": trip_data,
        "message": f"Trip deleted successfully",
    }
