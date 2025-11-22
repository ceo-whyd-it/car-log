"""
Delete trip template by ID.

Templates are stored in a single file: data/typical-destinations.json
"""

from typing import Dict, Any

from ..storage import get_data_path, read_json, atomic_write_json

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "template_id": {
            "type": "string",
            "description": "UUID of template to delete",
        }
    },
    "required": ["template_id"],
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Delete a trip template.

    Args:
        arguments: Dictionary containing:
            - template_id: UUID of template to delete

    Returns:
        Success/error dictionary
    """
    template_id = arguments["template_id"]

    # Path to templates file (use Path / operator)
    templates_file = get_data_path() / "typical-destinations.json"

    # Read existing templates
    if not templates_file.exists():
        return {
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "No templates exist",
            },
        }

    data = read_json(templates_file)
    templates = data.get("templates", [])

    # Find template
    template_index = None
    for i, template in enumerate(templates):
        if template.get("template_id") == template_id:
            template_index = i
            break

    if template_index is None:
        return {
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": f"Template not found: {template_id}",
            },
        }

    # Remove template
    deleted_template = templates.pop(template_index)

    # Save updated templates
    data["templates"] = templates
    atomic_write_json(templates_file, data)

    return {
        "success": True,
        "template_id": template_id,
        "deleted_template": deleted_template,
        "message": f"Template '{deleted_template.get('name')}' deleted successfully",
    }
