"""
Calculate template completeness and provide improvement suggestions.

Analyzes how complete a template is and suggests missing fields.
"""

from typing import Dict, Any, List


INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "template": {
            "type": "object",
            "description": "Template to analyze",
            "required": True,
        },
    },
    "required": ["template"],
}


# Mandatory fields (must have for basic matching)
MANDATORY_FIELDS = [
    "name",
    "from_coords",
    "to_coords",
]

# Optional enhancement fields (improve matching quality)
OPTIONAL_FIELDS = [
    "from_address",
    "from_label",
    "to_address",
    "to_label",
    "distance_km",
    "is_round_trip",
    "typical_days",
    "purpose",
    "business_description",
]


def check_field_present(template: Dict, field: str) -> bool:
    """
    Check if a field is present and non-empty.

    Args:
        template: Template data
        field: Field name to check

    Returns:
        True if field is present and non-empty
    """
    value = template.get(field)

    if value is None:
        return False

    # Check for empty strings
    if isinstance(value, str) and not value.strip():
        return False

    # Check for empty lists
    if isinstance(value, list) and len(value) == 0:
        return False

    # Check for empty dicts
    if isinstance(value, dict) and len(value) == 0:
        return False

    return True


def generate_improvement_suggestions(
    template: Dict,
    missing_optional: List[str],
) -> List[str]:
    """
    Generate improvement suggestions for template.

    Args:
        template: Template data
        missing_optional: List of missing optional fields

    Returns:
        List of suggestion strings
    """
    suggestions = []

    # Check for address information
    if "from_address" in missing_optional or "to_address" in missing_optional:
        suggestions.append(
            "Add address information to improve matching accuracy (30% of score)"
        )

    # Check for distance
    if "distance_km" in missing_optional:
        suggestions.append(
            "Add distance_km for distance bonus (up to +10 points)"
        )

    # Check for typical days
    if "typical_days" in missing_optional:
        suggestions.append(
            "Add typical_days for day-of-week bonus (up to +10 points)"
        )

    # Check for labels (user-friendly)
    if "from_label" in missing_optional or "to_label" in missing_optional:
        suggestions.append(
            "Add from_label/to_label for better readability in UI"
        )

    # Check for round trip flag
    if "is_round_trip" in missing_optional:
        suggestions.append(
            "Set is_round_trip flag if this template represents a return journey"
        )

    # Check for purpose
    if "purpose" in missing_optional:
        suggestions.append(
            "Add purpose (business/personal) for tax compliance"
        )

    # Check for business description (if purpose is business)
    if template.get("purpose") == "business" and "business_description" in missing_optional:
        suggestions.append(
            "Add business_description (required for business trips in Slovak tax compliance)"
        )

    return suggestions


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate template completeness.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with completeness analysis
    """
    try:
        template = arguments.get("template")

        if not template:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "template is required",
                },
            }

        # Check mandatory fields
        missing_mandatory = []
        for field in MANDATORY_FIELDS:
            if not check_field_present(template, field):
                missing_mandatory.append(field)

        # Template is invalid if mandatory fields are missing
        if missing_mandatory:
            return {
                "success": True,
                "is_valid": False,
                "completeness_percent": 0,
                "missing_mandatory": missing_mandatory,
                "message": f"Template is invalid. Missing mandatory fields: {', '.join(missing_mandatory)}",
            }

        # Check optional fields
        present_optional = []
        missing_optional = []

        for field in OPTIONAL_FIELDS:
            if check_field_present(template, field):
                present_optional.append(field)
            else:
                missing_optional.append(field)

        # Calculate completeness percentage
        # Mandatory fields count as 50%
        # Optional fields count as 50%
        mandatory_pct = 50  # All mandatory fields present
        optional_pct = (len(present_optional) / len(OPTIONAL_FIELDS)) * 50

        completeness_pct = mandatory_pct + optional_pct

        # Generate suggestions
        suggestions = generate_improvement_suggestions(template, missing_optional)

        # Determine quality level
        if completeness_pct >= 90:
            quality = "excellent"
        elif completeness_pct >= 75:
            quality = "good"
        elif completeness_pct >= 60:
            quality = "fair"
        else:
            quality = "basic"

        return {
            "success": True,
            "is_valid": True,
            "completeness_percent": round(completeness_pct, 2),
            "quality": quality,
            "mandatory_fields": {
                "total": len(MANDATORY_FIELDS),
                "present": len(MANDATORY_FIELDS),
                "missing": 0,
            },
            "optional_fields": {
                "total": len(OPTIONAL_FIELDS),
                "present": len(present_optional),
                "missing": len(missing_optional),
                "present_list": present_optional,
                "missing_list": missing_optional,
            },
            "suggestions": suggestions,
            "breakdown": {
                "has_gps": True,  # Already validated by mandatory check
                "has_addresses": (
                    check_field_present(template, "from_address") and
                    check_field_present(template, "to_address")
                ),
                "has_distance": check_field_present(template, "distance_km"),
                "has_typical_days": check_field_present(template, "typical_days"),
                "has_purpose": check_field_present(template, "purpose"),
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
