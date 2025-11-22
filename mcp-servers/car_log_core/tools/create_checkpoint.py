"""
Create checkpoint from refuel or manual entry.

Note: API uses flat fields for simplicity. We transform to nested structure for storage.
"""

import uuid
from datetime import datetime
from typing import Dict, Any

from ..storage import (
    get_data_path,
    atomic_write_json,
    read_json,
    ensure_month_folder,
    list_json_files,
)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "vehicle_id": {
            "type": "string",
            "format": "uuid",
            "description": "Vehicle ID",
        },
        "checkpoint_type": {
            "type": "string",
            "enum": ["refuel", "manual", "month_end"],
            "description": "Type of checkpoint",
        },
        "datetime": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp",
        },
        "odometer_km": {
            "type": "integer",
            "minimum": 0,
            "description": "Odometer reading in kilometers",
        },
        "odometer_source": {
            "type": "string",
            "enum": ["photo", "manual", "photo_adjusted"],
            "description": "How odometer was captured",
        },
        "odometer_photo_path": {
            "type": "string",
            "description": "Path to dashboard photo",
        },
        "odometer_confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "OCR confidence score",
        },
        "location_address": {
            "type": "string",
            "description": "Human-readable address",
        },
        "location_coords": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "minimum": -90, "maximum": 90},
                "lng": {"type": "number", "minimum": -180, "maximum": 180},
            },
            "description": "GPS coordinates",
        },
        "receipt_id": {
            "type": "string",
            "description": "e-Kasa receipt ID",
        },
        "fuel_liters": {
            "type": "number",
            "minimum": 0,
            "maximum": 500,
            "description": "Fuel quantity in liters",
        },
        "fuel_cost_eur": {
            "type": "number",
            "minimum": 0,
            "description": "Fuel cost in EUR",
        },
    },
    "required": ["vehicle_id", "checkpoint_type", "datetime", "odometer_km"],
}


def find_previous_checkpoint(vehicle_id: str, current_datetime: datetime, data_path) -> tuple[str, int, int]:
    """
    Find the most recent checkpoint before this one.

    Args:
        vehicle_id: Vehicle ID
        current_datetime: Current checkpoint datetime
        data_path: Base data path

    Returns:
        (previous_checkpoint_id, previous_odometer, distance_since_previous)
    """
    checkpoints_dir = data_path / "checkpoints"

    if not checkpoints_dir.exists():
        return None, None, None

    # Search through all month folders
    all_checkpoints = []
    for month_folder in checkpoints_dir.iterdir():
        if not month_folder.is_dir():
            continue

        for checkpoint_file in list_json_files(month_folder):
            checkpoint = read_json(checkpoint_file)
            if checkpoint and checkpoint.get("vehicle_id") == vehicle_id:
                try:
                    cp_dt = datetime.fromisoformat(checkpoint["datetime"].replace("Z", "+00:00"))
                    if cp_dt < current_datetime:
                        all_checkpoints.append(checkpoint)
                except (ValueError, KeyError, TypeError):
                    continue

    if not all_checkpoints:
        return None, None, None

    # Find most recent
    all_checkpoints.sort(key=lambda cp: cp["datetime"], reverse=True)
    previous = all_checkpoints[0]

    previous_odometer = previous["odometer_km"]

    return previous["checkpoint_id"], previous_odometer, None


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create new checkpoint.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with checkpoint data and gap info
    """
    try:
        # Extract required fields
        vehicle_id = arguments.get("vehicle_id", "").strip()
        checkpoint_type = arguments.get("checkpoint_type")
        dt_str = arguments.get("datetime", "").strip()
        odometer_km = arguments.get("odometer_km")

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

        # Verify vehicle exists
        data_path = get_data_path()
        vehicle_file = data_path / "vehicles" / f"{vehicle_id}.json"
        vehicle = read_json(vehicle_file)

        if vehicle is None:
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Vehicle not found: {vehicle_id}",
                },
            }

        # Parse datetime
        try:
            checkpoint_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except ValueError:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid datetime format (use ISO 8601)",
                    "field": "datetime",
                },
            }

        # Validate checkpoint type
        if checkpoint_type not in ["refuel", "manual", "month_end"]:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Checkpoint type must be: refuel, manual, or month_end",
                    "field": "checkpoint_type",
                },
            }

        # Generate checkpoint ID
        checkpoint_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        # Find previous checkpoint for gap detection
        prev_id, prev_odometer, distance_delta = find_previous_checkpoint(
            vehicle_id, checkpoint_dt, data_path
        )

        # Build location object (nested structure)
        location = None
        if arguments.get("location_coords") or arguments.get("location_address"):
            location = {}
            if arguments.get("location_address"):
                location["address"] = arguments["location_address"]
            if arguments.get("location_coords"):
                location["coords"] = arguments["location_coords"]

        # Build receipt object (nested structure)
        receipt = None
        if checkpoint_type == "refuel" and arguments.get("receipt_id"):
            receipt = {
                "receipt_id": arguments["receipt_id"],
            }
            if arguments.get("fuel_liters"):
                receipt["fuel_liters"] = arguments["fuel_liters"]
            if arguments.get("fuel_cost_eur"):
                receipt["fuel_cost_eur"] = arguments["fuel_cost_eur"]

        # Calculate distance since previous
        distance_since_previous = None
        if prev_odometer is not None:
            distance_since_previous = odometer_km - prev_odometer

        # Build checkpoint object
        checkpoint = {
            "checkpoint_id": checkpoint_id,
            "vehicle_id": vehicle_id,
            "checkpoint_type": checkpoint_type,
            "datetime": dt_str,
            "odometer_km": odometer_km,
            "odometer_source": arguments.get("odometer_source", "manual"),
            "odometer_photo_path": arguments.get("odometer_photo_path"),
            "odometer_confidence": arguments.get("odometer_confidence"),
            "location": location,
            "receipt": receipt,
            "previous_checkpoint_id": prev_id,
            "distance_since_previous_km": distance_since_previous,
            "created_at": now,
        }

        # Remove None values
        checkpoint = {k: v for k, v in checkpoint.items() if v is not None}

        # Save to monthly folder
        checkpoints_base = data_path / "checkpoints"
        month_folder = ensure_month_folder(checkpoints_base, checkpoint_dt)
        checkpoint_file = month_folder / f"{checkpoint_id}.json"

        atomic_write_json(checkpoint_file, checkpoint)

        # Update vehicle's current odometer
        vehicle["current_odometer_km"] = odometer_km
        vehicle["updated_at"] = now
        atomic_write_json(vehicle_file, vehicle)

        # Detect gap
        gap_detected = False
        gap_info = None

        if distance_since_previous and distance_since_previous > 0:
            # Gap threshold: 50km or more
            if distance_since_previous >= 50:
                gap_detected = True

                # Calculate time gap
                if prev_id:
                    prev_checkpoint_file = None
                    for month_folder in (data_path / "checkpoints").iterdir():
                        if not month_folder.is_dir():
                            continue
                        test_file = month_folder / f"{prev_id}.json"
                        if test_file.exists():
                            prev_checkpoint_file = test_file
                            break

                    if prev_checkpoint_file:
                        prev_checkpoint = read_json(prev_checkpoint_file)
                        prev_dt = datetime.fromisoformat(prev_checkpoint["datetime"].replace("Z", "+00:00"))
                        time_delta = checkpoint_dt - prev_dt

                        gap_info = {
                            "distance_km": distance_since_previous,
                            "time_period_days": time_delta.total_seconds() / 86400,
                            "previous_checkpoint_id": prev_id,
                            "reconstruction_suggested": distance_since_previous >= 100,
                        }

        return {
            "success": True,
            "checkpoint_id": checkpoint_id,
            "checkpoint": checkpoint,
            "gap_detected": gap_detected,
            "gap_info": gap_info,
            "message": "Checkpoint created successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
