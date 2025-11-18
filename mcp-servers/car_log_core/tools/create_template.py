"""
Create trip template (GPS mandatory, addresses optional).

Templates are stored in a single file: data/typical-destinations.json
"""

import uuid
from datetime import datetime
from typing import Dict, Any

from ..storage import get_data_path, read_json, atomic_write_json

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "description": "Template name (e.g., 'Warehouse Run')",
        },
        "from_coords": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "minimum": -90, "maximum": 90},
                "lng": {"type": "number", "minimum": -180, "maximum": 180},
            },
            "required": ["lat", "lng"],
            "description": "MANDATORY - Source of truth for matching",
        },
        "to_coords": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "minimum": -90, "maximum": 90},
                "lng": {"type": "number", "minimum": -180, "maximum": 180},
            },
            "required": ["lat", "lng"],
            "description": "MANDATORY - Source of truth for matching",
        },
        "from_address": {
            "type": "string",
            "description": "OPTIONAL - Human-readable label",
        },
        "to_address": {
            "type": "string",
            "description": "OPTIONAL - Human-readable label",
        },
        "distance_km": {
            "type": "number",
            "minimum": 0,
            "description": "OPTIONAL - Typical distance",
        },
        "is_round_trip": {
            "type": "boolean",
            "description": "OPTIONAL - Whether this is a round trip",
        },
        "typical_days": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            },
            "description": "OPTIONAL - Days when this trip typically occurs",
        },
        "purpose": {
            "type": "string",
            "enum": ["business", "personal"],
            "description": "Trip purpose",
        },
        "business_description": {
            "type": "string",
            "description": "Business purpose description",
        },
        "notes": {
            "type": "string",
            "description": "Additional notes",
        },
    },
    "required": ["name", "from_coords", "to_coords"],
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create new trip template.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with template data
    """
    try:
        # Validate required fields
        name = arguments.get("name", "").strip()
        from_coords = arguments.get("from_coords")
        to_coords = arguments.get("to_coords")

        if not name:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Template name is required",
                    "field": "name",
                },
            }

        # Validate from_coords (MANDATORY)
        if not from_coords or "lat" not in from_coords or "lng" not in from_coords:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "from_coords with lat/lng is MANDATORY",
                    "field": "from_coords",
                    "details": "GPS coordinates are the source of truth for template matching",
                },
            }

        # Validate to_coords (MANDATORY)
        if not to_coords or "lat" not in to_coords or "lng" not in to_coords:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "to_coords with lat/lng is MANDATORY",
                    "field": "to_coords",
                    "details": "GPS coordinates are the source of truth for template matching",
                },
            }

        # Validate coordinate ranges
        if not (-90 <= from_coords["lat"] <= 90 and -180 <= from_coords["lng"] <= 180):
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid from_coords range (lat: -90 to 90, lng: -180 to 180)",
                    "field": "from_coords",
                },
            }

        if not (-90 <= to_coords["lat"] <= 90 and -180 <= to_coords["lng"] <= 180):
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid to_coords range (lat: -90 to 90, lng: -180 to 180)",
                    "field": "to_coords",
                },
            }

        # Generate template ID
        template_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        # Build template object
        template = {
            "template_id": template_id,
            "name": name,
            "from_coords": from_coords,
            "to_coords": to_coords,
            "from_address": arguments.get("from_address"),
            "to_address": arguments.get("to_address"),
            "distance_km": arguments.get("distance_km"),
            "is_round_trip": arguments.get("is_round_trip", False),
            "typical_days": arguments.get("typical_days", []),
            "purpose": arguments.get("purpose"),
            "business_description": arguments.get("business_description"),
            "notes": arguments.get("notes"),
            "usage_count": 0,
            "last_used_at": None,
            "created_at": now,
        }

        # Remove None values
        template = {k: v for k, v in template.items() if v is not None}

        # Read existing templates file
        data_path = get_data_path()
        templates_file = data_path / "typical-destinations.json"

        templates_data = read_json(templates_file)
        if templates_data is None:
            templates_data = {"templates": []}

        # Check for duplicate name
        existing_names = [t["name"] for t in templates_data.get("templates", [])]
        if name in existing_names:
            return {
                "success": False,
                "error": {
                    "code": "DUPLICATE",
                    "message": f"Template with name '{name}' already exists",
                    "field": "name",
                },
            }

        # Add new template
        templates_data["templates"].append(template)

        # Save atomically
        atomic_write_json(templates_file, templates_data)

        return {
            "success": True,
            "template_id": template_id,
            "template": template,
            "message": "Template created successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
