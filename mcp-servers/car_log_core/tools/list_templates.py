"""
List all trip templates.
"""

from typing import Dict, Any

from ..storage import get_data_path, read_json

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "purpose": {
            "type": "string",
            "enum": ["business", "personal"],
            "description": "Filter by purpose",
        },
    },
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    List all trip templates.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with list of templates
    """
    try:
        purpose_filter = arguments.get("purpose")

        # Read templates file
        data_path = get_data_path()
        templates_file = data_path / "typical-destinations.json"

        templates_data = read_json(templates_file)
        if templates_data is None:
            templates_data = {"templates": []}

        templates = templates_data.get("templates", [])

        # Apply purpose filter
        if purpose_filter:
            templates = [t for t in templates if t.get("purpose") == purpose_filter]

        # Sort by usage_count (most used first), then by name
        templates.sort(key=lambda t: (-t.get("usage_count", 0), t.get("name", "")))

        return {
            "success": True,
            "templates": templates,
            "count": len(templates),
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
