"""
Match templates to gap between checkpoints.

Implements stateless template matching using hybrid GPS + address scoring.
"""

from datetime import datetime
from typing import Dict, Any, List

from ..matching import match_checkpoint_to_template


INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "gap_data": {
            "type": "object",
            "description": "Gap analysis data from car-log-core.detect_gap",
            "properties": {
                "distance_km": {"type": "number"},
                "start_checkpoint": {"type": "object"},
                "end_checkpoint": {"type": "object"},
            },
            "required": ["distance_km", "start_checkpoint", "end_checkpoint"],
        },
        "templates": {
            "type": "array",
            "description": "List of trip templates to match against",
            "items": {"type": "object"},
        },
        "confidence_threshold": {
            "type": "number",
            "description": "Minimum confidence score (0-100, default 70)",
            "default": 70,
        },
    },
    "required": ["gap_data", "templates"],
}


def get_day_of_week(iso_datetime: str) -> str:
    """
    Extract day of week from ISO datetime string.

    Args:
        iso_datetime: ISO 8601 datetime string

    Returns:
        Day name (e.g., "Monday")
    """
    try:
        dt = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
        return dt.strftime("%A")
    except:
        return None


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Match templates to gap between checkpoints.

    Args:
        arguments: Tool input arguments

    Returns:
        Success response with matched templates and reconstruction proposal
    """
    try:
        gap_data = arguments.get("gap_data", {})
        templates = arguments.get("templates", [])
        confidence_threshold = arguments.get("confidence_threshold", 70)

        # Validate inputs
        if not gap_data:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "gap_data is required",
                },
            }

        if not isinstance(templates, list):
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "templates must be an array",
                },
            }

        # Extract gap data
        distance_km = gap_data.get("distance_km", 0)
        start_checkpoint = gap_data.get("start_checkpoint")
        end_checkpoint = gap_data.get("end_checkpoint")

        if not start_checkpoint or not end_checkpoint:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "gap_data must include start_checkpoint and end_checkpoint",
                },
            }

        # Check if both checkpoints have GPS
        start_location = start_checkpoint.get("location", {})
        end_location = end_checkpoint.get("location", {})

        has_start_gps = start_location.get("coords") is not None
        has_end_gps = end_location.get("coords") is not None

        if not has_start_gps or not has_end_gps:
            return {
                "success": False,
                "error": {
                    "code": "GPS_REQUIRED",
                    "message": "Both checkpoints must have GPS coordinates for template matching",
                },
            }

        # Get day of week for bonuses
        start_day = get_day_of_week(start_checkpoint.get("datetime", ""))

        # Match all templates
        matched_templates = []

        for template in templates:
            template_id = template.get("template_id")
            template_name = template.get("name", "Unnamed")

            # Match start checkpoint to template FROM endpoint
            start_match = match_checkpoint_to_template(
                gap_checkpoint=start_checkpoint,
                template=template,
                endpoint='from',
                gap_distance_km=distance_km,
                gap_day_of_week=start_day,
            )

            # Match end checkpoint to template TO endpoint
            end_match = match_checkpoint_to_template(
                gap_checkpoint=end_checkpoint,
                template=template,
                endpoint='to',
                gap_distance_km=distance_km,
                gap_day_of_week=start_day,
            )

            # Check if both matches succeeded
            if not start_match.get('success') or not end_match.get('success'):
                continue

            # Calculate average confidence score
            start_score = start_match['score']
            end_score = end_match['score']
            avg_confidence = (start_score + end_score) / 2

            # Filter by confidence threshold
            if avg_confidence >= confidence_threshold:
                matched_templates.append({
                    "template_id": template_id,
                    "template_name": template_name,
                    "confidence_score": round(avg_confidence, 2),
                    "start_match": {
                        "score": round(start_score, 2),
                        "distance_meters": start_match['details']['distance_meters'],
                        "gps_score": start_match['details']['gps_score'],
                        "address_score": start_match['details']['address_score'],
                    },
                    "end_match": {
                        "score": round(end_score, 2),
                        "distance_meters": end_match['details']['distance_meters'],
                        "gps_score": end_match['details']['gps_score'],
                        "address_score": end_match['details']['address_score'],
                    },
                    "template": template,
                })

        # Sort by confidence score (highest first)
        matched_templates.sort(key=lambda x: x['confidence_score'], reverse=True)

        # Generate reconstruction proposal
        proposal = generate_reconstruction_proposal(
            gap_data=gap_data,
            matched_templates=matched_templates,
        )

        return {
            "success": True,
            "gap_distance_km": distance_km,
            "templates_evaluated": len(templates),
            "templates_matched": len(matched_templates),
            "confidence_threshold": confidence_threshold,
            "matched_templates": matched_templates,
            "reconstruction_proposal": proposal,
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }


def generate_reconstruction_proposal(
    gap_data: Dict,
    matched_templates: List[Dict],
) -> Dict:
    """
    Generate reconstruction proposal from matched templates.

    Args:
        gap_data: Gap analysis data
        matched_templates: List of matched templates (sorted by confidence)

    Returns:
        Reconstruction proposal
    """
    gap_distance_km = gap_data.get("distance_km", 0)

    if not matched_templates:
        return {
            "has_proposal": False,
            "message": "No templates matched above confidence threshold",
        }

    # Try to reconstruct gap with templates
    proposed_trips = []
    remaining_distance = gap_distance_km

    for match in matched_templates:
        template = match['template']
        template_distance = template.get('distance_km', 0)
        is_round_trip = template.get('is_round_trip', False)

        if template_distance == 0:
            continue

        # Calculate how many times this template fits
        if is_round_trip:
            # Round trip counts as 2x the distance
            effective_distance = template_distance * 2
        else:
            effective_distance = template_distance

        # Calculate number of trips (round down)
        if effective_distance > 0:
            num_trips = int(remaining_distance / effective_distance)

            if num_trips > 0:
                proposed_trips.append({
                    "template_id": match['template_id'],
                    "template_name": match['template_name'],
                    "confidence_score": match['confidence_score'],
                    "num_trips": num_trips,
                    "distance_km": template_distance,
                    "is_round_trip": is_round_trip,
                    "total_distance_km": num_trips * effective_distance,
                })

                remaining_distance -= num_trips * effective_distance

                # Stop if we've covered enough
                if remaining_distance < 50:  # 50km threshold
                    break

    # Calculate coverage
    reconstructed_km = gap_distance_km - remaining_distance
    coverage_pct = (reconstructed_km / gap_distance_km * 100) if gap_distance_km > 0 else 0

    return {
        "has_proposal": len(proposed_trips) > 0,
        "proposed_trips": proposed_trips,
        "gap_distance_km": gap_distance_km,
        "reconstructed_km": round(reconstructed_km, 2),
        "remaining_km": round(remaining_distance, 2),
        "coverage_percent": round(coverage_pct, 2),
        "reconstruction_quality": (
            "excellent" if coverage_pct >= 90 else
            "good" if coverage_pct >= 70 else
            "partial" if coverage_pct >= 50 else
            "poor"
        ),
    }
