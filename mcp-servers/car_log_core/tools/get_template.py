"""
Get single template by ID.

Priority: P1
Use case: Retrieve specific template for viewing or editing.
"""

from typing import Dict, Any
from pathlib import Path

from ..storage import (
    get_data_path,
    read_json,
)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "template_id": {
            "type": "string",
            "format": "uuid",
            "description": "Template ID",
        },
    },
    "required": ["template_id"],
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get template by ID.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with template data
    """
    try:
        # Extract required fields
        template_id = arguments.get("template_id", "").strip()

        # Validate required fields
        if not template_id:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Template ID is required",
                    "field": "template_id",
                },
            }

        # Find template
        data_path = get_data_path()
        template_file = data_path / "templates" / f"{template_id}.json"

        if not template_file.exists():
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Template not found: {template_id}",
                },
            }

        # Read template
        template = read_json(template_file)

        if template is None:
            return {
                "success": False,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": f"Failed to read template: {template_id}",
                },
            }

        return {
            "success": True,
            "template": template,
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
