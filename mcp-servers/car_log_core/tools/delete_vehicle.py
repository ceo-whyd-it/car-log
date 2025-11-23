"""
Delete vehicle (remove sold/decommissioned vehicle).

Priority: P1
Use case: Remove vehicles no longer in use.
Note: Warns if checkpoints/trips exist for this vehicle.
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
        "vehicle_id": {
            "type": "string",
            "format": "uuid",
            "description": "Vehicle ID to delete",
        },
        "cascade": {
            "type": "boolean",
            "default": False,
            "description": "If true, also delete all checkpoints and trips for this vehicle (default: false, warns instead)",
        },
    },
    "required": ["vehicle_id"],
}


def find_dependent_checkpoints(vehicle_id: str, data_path: Path) -> list[str]:
    """
    Find checkpoints belonging to this vehicle.

    Args:
        vehicle_id: Vehicle ID
        data_path: Base data path

    Returns:
        List of checkpoint IDs
    """
    checkpoints_dir = data_path / "checkpoints"

    if not checkpoints_dir.exists():
        return []

    dependent_checkpoints = []

    # Search through all month folders
    for month_folder in checkpoints_dir.iterdir():
        if not month_folder.is_dir():
            continue

        for checkpoint_file in list_json_files(month_folder):
            checkpoint = read_json(checkpoint_file)
            if checkpoint and checkpoint.get("vehicle_id") == vehicle_id:
                dependent_checkpoints.append(checkpoint["checkpoint_id"])

    return dependent_checkpoints


def find_dependent_trips(vehicle_id: str, data_path: Path) -> list[str]:
    """
    Find trips belonging to this vehicle.

    Args:
        vehicle_id: Vehicle ID
        data_path: Base data path

    Returns:
        List of trip IDs
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
            if trip and trip.get("vehicle_id") == vehicle_id:
                dependent_trips.append(trip["trip_id"])

    return dependent_trips


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Delete vehicle.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with warnings about dependencies
    """
    try:
        # Extract required fields
        vehicle_id = arguments.get("vehicle_id", "").strip()
        cascade = arguments.get("cascade", False)

        # Validate required fields
        if not vehicle_id:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Vehicle ID is required",
                    "field": "vehicle_id",
                },
            }

        # Find vehicle
        data_path = get_data_path()
        vehicle_file = data_path / "vehicles" / f"{vehicle_id}.json"

        if not vehicle_file.exists():
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Vehicle not found: {vehicle_id}",
                },
            }

        # Check for dependent checkpoints and trips
        dependent_checkpoints = find_dependent_checkpoints(vehicle_id, data_path)
        dependent_trips = find_dependent_trips(vehicle_id, data_path)
        warnings = []

        if dependent_checkpoints or dependent_trips:
            if not cascade:
                return {
                    "success": False,
                    "error": {
                        "code": "DEPENDENCY_ERROR",
                        "message": f"Vehicle has {len(dependent_checkpoints)} checkpoint(s) and {len(dependent_trips)} trip(s). Set cascade=true to delete them, or delete data manually first.",
                        "dependent_checkpoints": len(dependent_checkpoints),
                        "dependent_trips": len(dependent_trips),
                    },
                }
            else:
                # Delete dependent checkpoints
                checkpoints_dir = data_path / "checkpoints"
                for month_folder in checkpoints_dir.iterdir():
                    if not month_folder.is_dir():
                        continue

                    for checkpoint_id in dependent_checkpoints:
                        checkpoint_file = month_folder / f"{checkpoint_id}.json"
                        if checkpoint_file.exists():
                            os.remove(checkpoint_file)

                warnings.append(f"Cascade deleted {len(dependent_checkpoints)} checkpoint(s)")

                # Delete dependent trips
                trips_dir = data_path / "trips"
                for month_folder in trips_dir.iterdir():
                    if not month_folder.is_dir():
                        continue

                    for trip_id in dependent_trips:
                        trip_file = month_folder / f"{trip_id}.json"
                        if trip_file.exists():
                            os.remove(trip_file)

                warnings.append(f"Cascade deleted {len(dependent_trips)} trip(s)")

        # Delete vehicle file
        os.remove(vehicle_file)

        return {
            "success": True,
            "vehicle_id": vehicle_id,
            "warnings": warnings if warnings else None,
            "message": "Vehicle deleted successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
