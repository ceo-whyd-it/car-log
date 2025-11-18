"""
Get checkpoint by ID.
"""

from typing import Dict, Any

from ..storage import get_data_path, read_json

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "checkpoint_id": {
            "type": "string",
            "format": "uuid",
            "description": "Checkpoint ID",
        },
    },
    "required": ["checkpoint_id"],
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve checkpoint by ID.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with checkpoint data or error
    """
    try:
        checkpoint_id = arguments.get("checkpoint_id", "").strip()

        if not checkpoint_id:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Checkpoint ID is required",
                    "field": "checkpoint_id",
                },
            }

        # Search through monthly folders
        data_path = get_data_path()
        checkpoints_dir = data_path / "checkpoints"

        if not checkpoints_dir.exists():
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Checkpoint not found: {checkpoint_id}",
                },
            }

        # Search all month folders
        for month_folder in checkpoints_dir.iterdir():
            if not month_folder.is_dir():
                continue

            checkpoint_file = month_folder / f"{checkpoint_id}.json"
            if checkpoint_file.exists():
                checkpoint = read_json(checkpoint_file)
                if checkpoint:
                    return {
                        "success": True,
                        "checkpoint": checkpoint,
                    }

        return {
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": f"Checkpoint not found: {checkpoint_id}",
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
