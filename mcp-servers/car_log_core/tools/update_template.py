"""
Update template (GPS coordinates, address, name, business description).

Priority: P1
Use case: Modify template when locations change or descriptions need updating.
"""

from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from ..storage import (
    get_data_path,
    atomic_write_json,
    read_json,
)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "template_id": {
            "type": "string",
            "format": "uuid",
            "description": "Template ID to update",
        },
        "updates": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Updated template name",
                },
                "from_coords": {
                    "type": "object",
                    "properties": {
                        "lat": {"type": "number", "minimum": -90, "maximum": 90},
                        "lng": {"type": "number", "minimum": -180, "maximum": 180},
                    },
                    "required": ["lat", "lng"],
                    "description": "Updated source GPS coordinates",
                },
                "to_coords": {
                    "type": "object",
                    "properties": {
                        "lat": {"type": "number", "minimum": -90, "maximum": 90},
                        "lng": {"type": "number", "minimum": -180, "maximum": 180},
                    },
                    "required": ["lat", "lng"],
                    "description": "Updated destination GPS coordinates",
                },
                "from_address": {
                    "type": "string",
                    "description": "Updated source address",
                },
                "to_address": {
                    "type": "string",
                    "description": "Updated destination address",
                },
                "distance_km": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Updated typical distance",
                },
                "is_round_trip": {
                    "type": "boolean",
                    "description": "Updated round trip flag",
                },
                "typical_days": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                    },
                    "description": "Updated typical days",
                },
                "purpose": {
                    "type": "string",
                    "enum": ["business", "personal"],
                    "description": "Updated trip purpose",
                },
                "business_description": {
                    "type": "string",
                    "description": "Updated business description",
                },
                "notes": {
                    "type": "string",
                    "description": "Updated notes",
                },
            },
            "description": "Fields to update (only specified fields will be changed)",
        },
    },
    "required": ["template_id", "updates"],
}


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update template fields.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with updated template
    """
    try:
        # Extract required fields
        template_id = arguments.get("template_id", "").strip()
        updates = arguments.get("updates", {})

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

        if not updates:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Updates object is required and cannot be empty",
                    "field": "updates",
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

        # Read existing template
        template = read_json(template_file)

        if template is None:
            return {
                "success": False,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": f"Failed to read template: {template_id}",
                },
            }

        # Track which fields were updated
        updated_fields = []

        # Update name
        if "name" in updates:
            if not updates["name"].strip():
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Template name cannot be empty",
                        "field": "name",
                    },
                }
            template["name"] = updates["name"]
            updated_fields.append("name")

        # Update from_coords (GPS)
        if "from_coords" in updates:
            coords = updates["from_coords"]
            if "lat" not in coords or "lng" not in coords:
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "from_coords must have lat and lng",
                        "field": "from_coords",
                    },
                }

            # Validate coordinate ranges
            if not (-90 <= coords["lat"] <= 90 and -180 <= coords["lng"] <= 180):
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid from_coords range (lat: -90 to 90, lng: -180 to 180)",
                        "field": "from_coords",
                    },
                }

            template["from_coords"] = coords
            updated_fields.append("from_coords")

        # Update to_coords (GPS)
        if "to_coords" in updates:
            coords = updates["to_coords"]
            if "lat" not in coords or "lng" not in coords:
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "to_coords must have lat and lng",
                        "field": "to_coords",
                    },
                }

            # Validate coordinate ranges
            if not (-90 <= coords["lat"] <= 90 and -180 <= coords["lng"] <= 180):
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid to_coords range (lat: -90 to 90, lng: -180 to 180)",
                        "field": "to_coords",
                    },
                }

            template["to_coords"] = coords
            updated_fields.append("to_coords")

        # Update addresses
        if "from_address" in updates:
            template["from_address"] = updates["from_address"]
            updated_fields.append("from_address")

        if "to_address" in updates:
            template["to_address"] = updates["to_address"]
            updated_fields.append("to_address")

        # Update distance
        if "distance_km" in updates:
            template["distance_km"] = updates["distance_km"]
            updated_fields.append("distance_km")

        # Update round trip flag
        if "is_round_trip" in updates:
            template["is_round_trip"] = updates["is_round_trip"]
            updated_fields.append("is_round_trip")

        # Update typical days
        if "typical_days" in updates:
            template["typical_days"] = updates["typical_days"]
            updated_fields.append("typical_days")

        # Update purpose
        if "purpose" in updates:
            template["purpose"] = updates["purpose"]
            updated_fields.append("purpose")

            # If purpose changed to personal, clear business_description
            if updates["purpose"] == "personal" and "business_description" in template:
                del template["business_description"]
                updated_fields.append("business_description (cleared)")

        # Update business description
        if "business_description" in updates:
            # Validate: business_description only valid if purpose is business
            if template.get("purpose") == "business":
                template["business_description"] = updates["business_description"]
                updated_fields.append("business_description")
            else:
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "business_description can only be set when purpose is business",
                        "field": "business_description",
                    },
                }

        # Update notes
        if "notes" in updates:
            template["notes"] = updates["notes"]
            updated_fields.append("notes")

        # Update metadata
        now = datetime.utcnow().isoformat() + "Z"
        template["updated_at"] = now

        # Atomic write
        atomic_write_json(template_file, template)

        return {
            "success": True,
            "template_id": template_id,
            "template": template,
            "updated_fields": updated_fields,
            "updated_at": now,
            "message": "Template updated successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }
