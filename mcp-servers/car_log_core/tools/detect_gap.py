"""
Detect and analyze gap between two checkpoints.
"""

from datetime import datetime
from typing import Dict, Any

from ..storage import get_data_path, read_json

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "start_checkpoint_id": {
            "type": "string",
            "format": "uuid",
            "description": "Start checkpoint ID",
        },
        "end_checkpoint_id": {
            "type": "string",
            "format": "uuid",
            "description": "End checkpoint ID",
        },
    },
    "required": ["start_checkpoint_id", "end_checkpoint_id"],
}


def find_checkpoint(checkpoint_id: str, data_path) -> dict:
    """
    Find checkpoint by ID across all month folders.

    Args:
        checkpoint_id: Checkpoint ID to find
        data_path: Base data path

    Returns:
        Checkpoint data or None
    """
    checkpoints_dir = data_path / "checkpoints"

    if not checkpoints_dir.exists():
        return None

    for month_folder in checkpoints_dir.iterdir():
        if not month_folder.is_dir():
            continue

        checkpoint_file = month_folder / f"{checkpoint_id}.json"
        if checkpoint_file.exists():
            return read_json(checkpoint_file)

    return None


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze gap between two checkpoints.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with gap analysis
    """
    try:
        start_id = arguments.get("start_checkpoint_id", "").strip()
        end_id = arguments.get("end_checkpoint_id", "").strip()

        if not start_id or not end_id:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Both start and end checkpoint IDs are required",
                },
            }

        # Find both checkpoints
        data_path = get_data_path()
        start_checkpoint = find_checkpoint(start_id, data_path)
        end_checkpoint = find_checkpoint(end_id, data_path)

        if start_checkpoint is None:
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Start checkpoint not found: {start_id}",
                },
            }

        if end_checkpoint is None:
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"End checkpoint not found: {end_id}",
                },
            }

        # Verify they're for the same vehicle
        if start_checkpoint.get("vehicle_id") != end_checkpoint.get("vehicle_id"):
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Checkpoints must be for the same vehicle",
                },
            }

        # Calculate distance gap
        start_odometer = start_checkpoint.get("odometer_km")
        end_odometer = end_checkpoint.get("odometer_km")

        if start_odometer is None or end_odometer is None:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Both checkpoints must have odometer readings",
                },
            }

        distance_km = end_odometer - start_odometer

        if distance_km < 0:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Start checkpoint must be before end checkpoint (odometer regression detected)",
                },
            }

        # Calculate time gap
        try:
            start_dt = datetime.fromisoformat(start_checkpoint["datetime"].replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_checkpoint["datetime"].replace("Z", "+00:00"))
        except ValueError as e:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Invalid datetime format: {e}",
                },
            }

        time_delta = end_dt - start_dt

        if time_delta.total_seconds() < 0:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Start checkpoint must be before end checkpoint (time regression detected)",
                },
            }

        days = time_delta.total_seconds() / 86400
        hours = time_delta.total_seconds() / 3600

        # Check if GPS coordinates are available
        start_location = start_checkpoint.get("location", {})
        end_location = end_checkpoint.get("location", {})

        has_gps = (
            start_location.get("coords") is not None
            and end_location.get("coords") is not None
        )

        # Calculate average km per day
        avg_km_per_day = distance_km / days if days > 0 else 0

        # Determine if reconstruction is recommended
        # Threshold: 100km+ distance or 7+ days
        reconstruction_recommended = distance_km >= 100 or days >= 7

        return {
            "success": True,
            "distance_km": distance_km,
            "days": round(days, 2),
            "hours": round(hours, 2),
            "start_checkpoint": start_checkpoint,
            "end_checkpoint": end_checkpoint,
            "has_gps": has_gps,
            "avg_km_per_day": round(avg_km_per_day, 2),
            "reconstruction_recommended": reconstruction_recommended,
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
