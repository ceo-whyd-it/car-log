"""
Validate checkpoint pair - distance sum check.

Compares odometer delta against sum of trip distances between checkpoints.
Threshold: ±10% variance is acceptable.
"""

import os
import json
from typing import Dict, Any
from datetime import datetime

from ..thresholds import DISTANCE_VARIANCE_PERCENT

# Input schema for MCP
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "start_checkpoint_id": {
            "type": "string",
            "format": "uuid",
            "description": "UUID of starting checkpoint",
        },
        "end_checkpoint_id": {
            "type": "string",
            "format": "uuid",
            "description": "UUID of ending checkpoint",
        },
    },
    "required": ["start_checkpoint_id", "end_checkpoint_id"],
}


def get_data_path() -> str:
    """Get data directory path from environment or default."""
    default_path = os.path.expanduser("~/Documents/MileageLog/data")
    return os.getenv("DATA_PATH", default_path)


def load_checkpoint(checkpoint_id: str) -> Dict[str, Any]:
    """
    Load checkpoint from file.

    Args:
        checkpoint_id: UUID of checkpoint

    Returns:
        Checkpoint data

    Raises:
        FileNotFoundError: If checkpoint doesn't exist
    """
    data_path = get_data_path()

    # Search through monthly folders
    checkpoints_dir = os.path.join(data_path, "checkpoints")

    if not os.path.exists(checkpoints_dir):
        raise FileNotFoundError(f"Checkpoints directory not found: {checkpoints_dir}")

    # Search all monthly folders
    for month_dir in os.listdir(checkpoints_dir):
        month_path = os.path.join(checkpoints_dir, month_dir)
        if not os.path.isdir(month_path):
            continue

        checkpoint_file = os.path.join(month_path, f"{checkpoint_id}.json")
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                return json.load(f)

    raise FileNotFoundError(f"Checkpoint not found: {checkpoint_id}")


def list_trips_between(
    vehicle_id: str, start_datetime: str, end_datetime: str
) -> list:
    """
    List all trips for a vehicle between two datetimes.

    Args:
        vehicle_id: Vehicle UUID
        start_datetime: ISO 8601 start datetime
        end_datetime: ISO 8601 end datetime

    Returns:
        List of trip dictionaries
    """
    data_path = get_data_path()
    trips_dir = os.path.join(data_path, "trips")

    if not os.path.exists(trips_dir):
        return []

    trips = []
    start_dt = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(end_datetime.replace("Z", "+00:00"))

    # Search all monthly folders
    for month_dir in os.listdir(trips_dir):
        month_path = os.path.join(trips_dir, month_dir)
        if not os.path.isdir(month_path):
            continue

        # Check each trip file
        for filename in os.listdir(month_path):
            if not filename.endswith(".json") or filename == "index.json":
                continue

            trip_file = os.path.join(month_path, filename)
            with open(trip_file, "r", encoding="utf-8") as f:
                trip = json.load(f)

            # Filter by vehicle and date range
            if trip.get("vehicle_id") != vehicle_id:
                continue

            trip_start = datetime.fromisoformat(
                trip["trip_start_datetime"].replace("Z", "+00:00")
            )

            if start_dt <= trip_start <= end_dt:
                trips.append(trip)

    return trips


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate gap between two checkpoints.

    Compares odometer delta against sum of trip distances.

    Args:
        arguments: Tool input arguments

    Returns:
        Validation result with status, warnings, and errors
    """
    try:
        start_checkpoint_id = arguments.get("start_checkpoint_id")
        end_checkpoint_id = arguments.get("end_checkpoint_id")

        # Load checkpoints
        try:
            start_checkpoint = load_checkpoint(start_checkpoint_id)
        except FileNotFoundError:
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Start checkpoint not found: {start_checkpoint_id}",
                },
            }

        try:
            end_checkpoint = load_checkpoint(end_checkpoint_id)
        except FileNotFoundError:
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"End checkpoint not found: {end_checkpoint_id}",
                },
            }

        # Validate same vehicle
        if start_checkpoint.get("vehicle_id") != end_checkpoint.get("vehicle_id"):
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Checkpoints must be from the same vehicle",
                },
            }

        # Calculate odometer delta
        start_odo = start_checkpoint.get("odometer_km", 0)
        end_odo = end_checkpoint.get("odometer_km", 0)
        odometer_delta = end_odo - start_odo

        if odometer_delta < 0:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "End odometer must be greater than start odometer",
                },
            }

        # Calculate time gap
        start_dt = datetime.fromisoformat(
            start_checkpoint["datetime"].replace("Z", "+00:00")
        )
        end_dt = datetime.fromisoformat(
            end_checkpoint["datetime"].replace("Z", "+00:00")
        )
        days = (end_dt - start_dt).days

        # Get trips between checkpoints
        vehicle_id = start_checkpoint.get("vehicle_id")
        trips = list_trips_between(
            vehicle_id, start_checkpoint["datetime"], end_checkpoint["datetime"]
        )

        # Sum trip distances
        trip_distance_sum = sum(trip.get("distance_km", 0) for trip in trips)

        # Calculate variance
        if odometer_delta > 0:
            variance_percent = (
                abs(odometer_delta - trip_distance_sum) / odometer_delta * 100
            )
        else:
            variance_percent = 0 if trip_distance_sum == 0 else 100

        # Determine status
        warnings = []
        errors = []

        if variance_percent > DISTANCE_VARIANCE_PERCENT:
            error_msg = (
                f"Distance mismatch: odometer shows {odometer_delta:.1f} km, "
                f"but trips sum to {trip_distance_sum:.1f} km "
                f"({variance_percent:.1f}% variance, threshold: {DISTANCE_VARIANCE_PERCENT}%)"
            )
            errors.append(error_msg)
            status = "error"
        elif variance_percent > DISTANCE_VARIANCE_PERCENT * 0.5:
            # Warning at 5% (half of error threshold)
            warning_msg = (
                f"Distance variance approaching threshold: {variance_percent:.1f}% "
                f"(odometer: {odometer_delta:.1f} km, trips: {trip_distance_sum:.1f} km)"
            )
            warnings.append(warning_msg)
            status = "warning"
        else:
            status = "ok"

        # Calculate km/day
        km_per_day = odometer_delta / days if days > 0 else 0

        return {
            "status": status,
            "distance_km": odometer_delta,
            "days": days,
            "km_per_day": round(km_per_day, 2),
            "trip_count": len(trips),
            "trip_distance_sum": round(trip_distance_sum, 2),
            "variance_percent": round(variance_percent, 2),
            "warnings": warnings,
            "errors": errors,
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Validation failed: {str(e)}",
            },
        }
