"""
List trips with filters (vehicle_id, date range, purpose).

Returns trips sorted by datetime descending with summary statistics.
"""

from datetime import datetime
from typing import Dict, Any

from ..storage import get_data_path, list_json_files, read_json

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "vehicle_id": {
            "type": "string",
            "format": "uuid",
            "description": "Filter by vehicle ID",
        },
        "start_date": {
            "type": "string",
            "format": "date",
            "description": "Filter by start date (YYYY-MM-DD)",
        },
        "end_date": {
            "type": "string",
            "format": "date",
            "description": "Filter by end date (YYYY-MM-DD)",
        },
        "purpose": {
            "type": "string",
            "enum": ["Business", "Personal"],
            "description": "Filter by trip purpose",
        },
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 500,
            "default": 100,
            "description": "Maximum number of results",
        },
    },
    "required": [],
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    List trips with filters.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with list of trips and summary stats
    """
    try:
        vehicle_id = arguments.get("vehicle_id", "").strip()
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        purpose = arguments.get("purpose")
        limit = arguments.get("limit", 100)

        # Parse date filters
        start_dt = None
        end_dt = None

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid start_date format (use YYYY-MM-DD)",
                        "field": "start_date",
                    },
                }

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                # Set to end of day
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
            except ValueError:
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid end_date format (use YYYY-MM-DD)",
                        "field": "end_date",
                    },
                }

        # Read all trip files
        data_path = get_data_path()
        trips_dir = data_path / "trips"
        trips = []

        if not trips_dir.exists():
            return {
                "success": True,
                "trips": [],
                "count": 0,
                "summary": {
                    "total_distance_km": 0,
                    "business_trips": 0,
                    "personal_trips": 0,
                    "business_distance_km": 0,
                    "personal_distance_km": 0,
                },
            }

        # Search through all month folders
        for month_folder in trips_dir.iterdir():
            if not month_folder.is_dir():
                continue

            for trip_file in list_json_files(month_folder):
                trip = read_json(trip_file)
                if trip is None:
                    continue

                # Filter by vehicle_id
                if vehicle_id and trip.get("vehicle_id") != vehicle_id:
                    continue

                # Filter by purpose
                if purpose and trip.get("purpose") != purpose:
                    continue

                # Filter by date range
                if start_dt or end_dt:
                    try:
                        trip_dt = datetime.fromisoformat(
                            trip["trip_start_datetime"].replace("Z", "+00:00")
                        )

                        if start_dt and trip_dt < start_dt:
                            continue

                        if end_dt and trip_dt > end_dt:
                            continue
                    except:
                        continue

                trips.append(trip)

        # Sort by datetime (most recent first)
        trips.sort(key=lambda t: t.get("trip_start_datetime", ""), reverse=True)

        # Calculate summary statistics (before limiting)
        total_distance = sum(t.get("distance_km", 0) for t in trips)
        business_trips = [t for t in trips if t.get("purpose") == "Business"]
        personal_trips = [t for t in trips if t.get("purpose") == "Personal"]
        business_distance = sum(t.get("distance_km", 0) for t in business_trips)
        personal_distance = sum(t.get("distance_km", 0) for t in personal_trips)

        summary = {
            "total_distance_km": total_distance,
            "business_trips": len(business_trips),
            "personal_trips": len(personal_trips),
            "business_distance_km": business_distance,
            "personal_distance_km": personal_distance,
        }

        # Apply limit
        trips = trips[:limit]

        return {
            "success": True,
            "trips": trips,
            "count": len(trips),
            "summary": summary,
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
