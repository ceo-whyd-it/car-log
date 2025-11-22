"""
List checkpoints with filters (vehicle_id, date range, type).
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
        "checkpoint_type": {
            "type": "string",
            "enum": ["refuel", "manual", "month_end"],
            "description": "Filter by checkpoint type",
        },
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "default": 50,
            "description": "Maximum number of results",
        },
    },
    "required": ["vehicle_id"],
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    List checkpoints with filters.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with list of checkpoints
    """
    try:
        vehicle_id = arguments.get("vehicle_id", "").strip()
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        checkpoint_type = arguments.get("checkpoint_type")
        limit = arguments.get("limit", 50)

        if not vehicle_id:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Vehicle ID is required",
                    "field": "vehicle_id",
                },
            }

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

        # Read all checkpoint files
        data_path = get_data_path()
        checkpoints_dir = data_path / "checkpoints"
        checkpoints = []

        if not checkpoints_dir.exists():
            return {
                "success": True,
                "checkpoints": [],
                "count": 0,
            }

        # Search through all month folders
        for month_folder in checkpoints_dir.iterdir():
            if not month_folder.is_dir():
                continue

            for checkpoint_file in list_json_files(month_folder):
                checkpoint = read_json(checkpoint_file)
                if checkpoint is None:
                    continue

                # Filter by vehicle_id
                if checkpoint.get("vehicle_id") != vehicle_id:
                    continue

                # Filter by checkpoint_type
                if checkpoint_type and checkpoint.get("checkpoint_type") != checkpoint_type:
                    continue

                # Filter by date range
                if start_dt or end_dt:
                    try:
                        cp_dt = datetime.fromisoformat(checkpoint["datetime"].replace("Z", "+00:00"))

                        if start_dt and cp_dt < start_dt:
                            continue

                        if end_dt and cp_dt > end_dt:
                            continue
                    except (ValueError, KeyError, TypeError):
                        continue

                checkpoints.append(checkpoint)

        # Sort by datetime (most recent first)
        checkpoints.sort(key=lambda cp: cp.get("datetime", ""), reverse=True)

        # Apply limit
        checkpoints = checkpoints[:limit]

        return {
            "success": True,
            "checkpoints": checkpoints,
            "count": len(checkpoints),
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
