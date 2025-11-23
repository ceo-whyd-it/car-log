"""
Update existing checkpoint to fix mistakes (odometer, GPS, driver name, etc.).

Priority: P0 CRITICAL
Use case: Users must be able to correct data entry mistakes.
"""

import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from ..storage import (
    get_data_path,
    atomic_write_json,
    read_json,
    list_json_files,
)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "checkpoint_id": {
            "type": "string",
            "format": "uuid",
            "description": "Checkpoint ID to update",
        },
        "updates": {
            "type": "object",
            "properties": {
                "odometer_km": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Updated odometer reading",
                },
                "odometer_source": {
                    "type": "string",
                    "enum": ["photo", "manual", "photo_adjusted"],
                    "description": "Updated odometer source",
                },
                "odometer_confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Updated OCR confidence score",
                },
                "location_address": {
                    "type": "string",
                    "description": "Updated address",
                },
                "location_coords": {
                    "type": "object",
                    "properties": {
                        "lat": {"type": "number", "minimum": -90, "maximum": 90},
                        "lng": {"type": "number", "minimum": -180, "maximum": 180},
                    },
                    "description": "Updated GPS coordinates",
                },
                "fuel_liters": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 500,
                    "description": "Updated fuel quantity",
                },
                "fuel_cost_eur": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Updated fuel cost",
                },
            },
            "description": "Fields to update (only specified fields will be changed)",
        },
    },
    "required": ["checkpoint_id", "updates"],
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


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update checkpoint fields.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with updated checkpoint
    """
    try:
        # Extract required fields
        checkpoint_id = arguments.get("checkpoint_id", "").strip()
        updates = arguments.get("updates", {})

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

        if not updates:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Updates object is required and cannot be empty",
                    "field": "updates",
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

        # Read existing checkpoint
        checkpoint = read_json(checkpoint_file)

        if checkpoint is None:
            return {
                "success": False,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": f"Failed to read checkpoint: {checkpoint_id}",
                },
            }

        # Track which fields were updated
        updated_fields = []

        # Update odometer (with validation)
        if "odometer_km" in updates:
            new_odometer = updates["odometer_km"]

            # Validation: Check if odometer decreased relative to previous checkpoint
            if checkpoint.get("previous_checkpoint_id"):
                prev_id = checkpoint["previous_checkpoint_id"]
                prev_file = find_checkpoint_file(prev_id, data_path)
                if prev_file:
                    prev_checkpoint = read_json(prev_file)
                    if prev_checkpoint and prev_checkpoint.get("odometer_km"):
                        prev_odometer = prev_checkpoint["odometer_km"]
                        if new_odometer < prev_odometer:
                            return {
                                "success": False,
                                "error": {
                                    "code": "VALIDATION_ERROR",
                                    "message": f"Odometer cannot decrease (previous: {prev_odometer} km, new: {new_odometer} km)",
                                    "field": "odometer_km",
                                },
                            }

            checkpoint["odometer_km"] = new_odometer

            # Recalculate distance_since_previous if we have previous checkpoint
            if checkpoint.get("previous_checkpoint_id"):
                prev_id = checkpoint["previous_checkpoint_id"]
                prev_file = find_checkpoint_file(prev_id, data_path)
                if prev_file:
                    prev_checkpoint = read_json(prev_file)
                    if prev_checkpoint and prev_checkpoint.get("odometer_km"):
                        checkpoint["distance_since_previous_km"] = new_odometer - prev_checkpoint["odometer_km"]

            updated_fields.append("odometer_km")

        # Update odometer source
        if "odometer_source" in updates:
            checkpoint["odometer_source"] = updates["odometer_source"]
            updated_fields.append("odometer_source")

        # Update odometer confidence
        if "odometer_confidence" in updates:
            checkpoint["odometer_confidence"] = updates["odometer_confidence"]
            updated_fields.append("odometer_confidence")

        # Update location (nested structure)
        if "location_address" in updates or "location_coords" in updates:
            if "location" not in checkpoint:
                checkpoint["location"] = {}

            if "location_address" in updates:
                checkpoint["location"]["address"] = updates["location_address"]
                updated_fields.append("location.address")

            if "location_coords" in updates:
                checkpoint["location"]["coords"] = updates["location_coords"]
                updated_fields.append("location.coords")

        # Update receipt data (nested structure)
        if "fuel_liters" in updates or "fuel_cost_eur" in updates:
            if "receipt" not in checkpoint:
                checkpoint["receipt"] = {}

            if "fuel_liters" in updates:
                checkpoint["receipt"]["fuel_liters"] = updates["fuel_liters"]
                updated_fields.append("receipt.fuel_liters")

            if "fuel_cost_eur" in updates:
                checkpoint["receipt"]["fuel_cost_eur"] = updates["fuel_cost_eur"]
                updated_fields.append("receipt.fuel_cost_eur")

        # Update metadata
        now = datetime.utcnow().isoformat() + "Z"
        checkpoint["updated_at"] = now

        # Atomic write
        atomic_write_json(checkpoint_file, checkpoint)

        # Update vehicle's current odometer if this is the most recent checkpoint
        if "odometer_km" in updates:
            vehicle_id = checkpoint["vehicle_id"]
            vehicle_file = data_path / "vehicles" / f"{vehicle_id}.json"
            vehicle = read_json(vehicle_file)

            if vehicle:
                # Check if this is the most recent checkpoint for this vehicle
                checkpoints_dir = data_path / "checkpoints"
                all_checkpoints = []

                for month_folder in checkpoints_dir.iterdir():
                    if not month_folder.is_dir():
                        continue

                    for cp_file in list_json_files(month_folder):
                        cp = read_json(cp_file)
                        if cp and cp.get("vehicle_id") == vehicle_id:
                            all_checkpoints.append(cp)

                # Sort by datetime
                all_checkpoints.sort(key=lambda cp: cp["datetime"], reverse=True)

                # If this checkpoint is the most recent, update vehicle
                if all_checkpoints and all_checkpoints[0]["checkpoint_id"] == checkpoint_id:
                    vehicle["current_odometer_km"] = checkpoint["odometer_km"]
                    vehicle["updated_at"] = now
                    atomic_write_json(vehicle_file, vehicle)

        return {
            "success": True,
            "checkpoint_id": checkpoint_id,
            "checkpoint": checkpoint,
            "updated_fields": updated_fields,
            "updated_at": now,
            "message": "Checkpoint updated successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
