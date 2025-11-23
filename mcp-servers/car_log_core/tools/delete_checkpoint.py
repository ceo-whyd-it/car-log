"""
Delete checkpoint (remove duplicate or erroneous entry).

Priority: P0 CRITICAL
Use case: Users must be able to remove bad data.
Note: Warns if trips reference this checkpoint.
"""

import os
from typing import Dict, Any
from pathlib import Path

from ..storage import (
    get_data_path,
    read_json,
    list_json_files,
)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "checkpoint_id": {
            "type": "string",
            "format": "uuid",
            "description": "Checkpoint ID to delete",
        },
        "cascade": {
            "type": "boolean",
            "default": False,
            "description": "If true, also delete dependent trips (default: false, warns instead)",
        },
    },
    "required": ["checkpoint_id"],
}


def find_checkpoint_file(checkpoint_id: str, data_path: Path) -> Path:
    """
    Find checkpoint file across all month folders.

    Args:
        checkpoint_id: Checkpoint ID
        data_path: Base data path

    Returns:
        Path to checkpoint file or None if not found
    """
    checkpoints_dir = data_path / "checkpoints"

    if not checkpoints_dir.exists():
        return None

    # Search through all month folders
    for month_folder in checkpoints_dir.iterdir():
        if not month_folder.is_dir():
            continue

        checkpoint_file = month_folder / f"{checkpoint_id}.json"
        if checkpoint_file.exists():
            return checkpoint_file

    return None


def find_dependent_trips(checkpoint_id: str, data_path: Path) -> list[str]:
    """
    Find trips that reference this checkpoint.

    Args:
        checkpoint_id: Checkpoint ID
        data_path: Base data path

    Returns:
        List of trip IDs that reference this checkpoint
    """
    trips_dir = data_path / "trips"

    if not trips_dir.exists():
        return []

    dependent_trips = []

    # Search through all month folders
    for month_folder in trips_dir.iterdir():
        if not month_folder.is_dir():
            continue

        for trip_file in list_json_files(month_folder):
            trip = read_json(trip_file)
            if trip:
                # Check if trip references this checkpoint
                if (trip.get("start_checkpoint_id") == checkpoint_id or
                    trip.get("end_checkpoint_id") == checkpoint_id):
                    dependent_trips.append(trip["trip_id"])

    return dependent_trips


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Delete checkpoint.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with warnings about dependencies
    """
    try:
        # Extract required fields
        checkpoint_id = arguments.get("checkpoint_id", "").strip()
        cascade = arguments.get("cascade", False)

        # Validate required fields
        if not checkpoint_id:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Checkpoint ID is required",
                    "field": "checkpoint_id",
                },
            }

        # Find checkpoint
        data_path = get_data_path()
        checkpoint_file = find_checkpoint_file(checkpoint_id, data_path)

        if checkpoint_file is None:
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Checkpoint not found: {checkpoint_id}",
                },
            }

        # Check for dependent trips
        dependent_trips = find_dependent_trips(checkpoint_id, data_path)
        warnings = []

        if dependent_trips:
            if not cascade:
                return {
                    "success": False,
                    "error": {
                        "code": "DEPENDENCY_ERROR",
                        "message": f"{len(dependent_trips)} trip(s) reference this checkpoint. Set cascade=true to delete them, or delete trips manually first.",
                        "dependent_trips": dependent_trips,
                    },
                }
            else:
                # Delete dependent trips
                trips_dir = data_path / "trips"
                for month_folder in trips_dir.iterdir():
                    if not month_folder.is_dir():
                        continue

                    for trip_id in dependent_trips:
                        trip_file = month_folder / f"{trip_id}.json"
                        if trip_file.exists():
                            os.remove(trip_file)

                warnings.append(f"Cascade deleted {len(dependent_trips)} dependent trip(s)")

        # Delete checkpoint file
        os.remove(checkpoint_file)

        return {
            "success": True,
            "checkpoint_id": checkpoint_id,
            "warnings": warnings if warnings else None,
            "message": "Checkpoint deleted successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
