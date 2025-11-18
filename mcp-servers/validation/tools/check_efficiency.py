"""
Check fuel efficiency reasonability.

Validates efficiency against fuel type ranges:
- Diesel: 5-15 L/100km
- Gasoline: 6-20 L/100km
- LPG: 8-25 L/100km
- Hybrid: 3-10 L/100km
- Electric: N/A (uses kWh, not L/100km)
"""

from typing import Dict, Any, Tuple

from ..thresholds import get_efficiency_range

# Input schema for MCP
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "efficiency_l_per_100km": {
            "type": "number",
            "description": "Fuel efficiency in L/100km (European standard)",
        },
        "fuel_type": {
            "type": "string",
            "enum": ["Diesel", "Gasoline", "LPG", "Hybrid", "Electric"],
            "description": "Fuel type",
        },
    },
    "required": ["efficiency_l_per_100km", "fuel_type"],
}


def validate_efficiency_range(
    efficiency: float, fuel_type: str
) -> Tuple[str, str]:
    """
    Validate efficiency against expected range for fuel type.

    Args:
        efficiency: Fuel efficiency in L/100km
        fuel_type: Fuel type (Diesel, Gasoline, LPG, Hybrid, Electric)

    Returns:
        (status, message) - status is 'ok', 'warning', or 'error'
    """
    try:
        range_data = get_efficiency_range(fuel_type)
    except ValueError as e:
        return "error", str(e)

    min_eff = range_data["min"]
    max_eff = range_data["max"]

    # Special handling for Electric vehicles
    if fuel_type == "Electric":
        if efficiency > 0:
            return (
                "error",
                "Electric vehicles should not have fuel efficiency in L/100km. "
                "Use kWh/100km instead.",
            )
        return "ok", "Electric vehicle (uses kWh, not L/100km)"

    # Check if efficiency is within reasonable range
    if efficiency < min_eff:
        return (
            "error",
            f"Unrealistically low efficiency: {efficiency:.2f} L/100km. "
            f"Expected range for {fuel_type}: {min_eff}-{max_eff} L/100km. "
            "Verify measurement or check for data entry error.",
        )
    elif efficiency > max_eff:
        return (
            "error",
            f"Unrealistically high efficiency: {efficiency:.2f} L/100km. "
            f"Expected range for {fuel_type}: {min_eff}-{max_eff} L/100km. "
            "Verify measurement or check for data entry error.",
        )
    else:
        # Check if approaching boundaries (within 10% of range)
        range_span = max_eff - min_eff
        warning_margin = range_span * 0.1

        if efficiency < min_eff + warning_margin:
            return (
                "warning",
                f"Efficiency near lower boundary: {efficiency:.2f} L/100km "
                f"(expected range: {min_eff}-{max_eff} L/100km). "
                "This is very efficient - verify measurement is correct.",
            )
        elif efficiency > max_eff - warning_margin:
            return (
                "warning",
                f"Efficiency near upper boundary: {efficiency:.2f} L/100km "
                f"(expected range: {min_eff}-{max_eff} L/100km). "
                "This is high consumption - check driving conditions.",
            )
        else:
            return (
                "ok",
                f"Efficiency within normal range: {efficiency:.2f} L/100km "
                f"(expected: {min_eff}-{max_eff} L/100km)",
            )


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check fuel efficiency reasonability.

    Args:
        arguments: Tool input arguments

    Returns:
        Validation result with status, efficiency, expected range, and message
    """
    try:
        efficiency = arguments.get("efficiency_l_per_100km")
        fuel_type = arguments.get("fuel_type")

        if efficiency is None:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "efficiency_l_per_100km is required",
                },
            }

        if not fuel_type:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "fuel_type is required",
                },
            }

        # Validate efficiency
        status, message = validate_efficiency_range(efficiency, fuel_type)

        # Get expected range
        try:
            expected_range = get_efficiency_range(fuel_type)
        except ValueError as e:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e),
                },
            }

        return {
            "status": status,
            "efficiency": efficiency,
            "expected_range": expected_range,
            "message": message,
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Efficiency check failed: {str(e)}",
            },
        }
