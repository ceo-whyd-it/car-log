"""
Check deviation from average efficiency.

Compares trip efficiency to vehicle average efficiency.
Warning threshold: 20% deviation.
"""

from typing import Dict, Any, Tuple

from ..thresholds import DEVIATION_THRESHOLD_PERCENT

# Input schema for MCP
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "trip_efficiency_l_per_100km": {
            "type": "number",
            "description": "Trip fuel efficiency in L/100km",
        },
        "vehicle_avg_efficiency_l_per_100km": {
            "type": "number",
            "description": "Vehicle average efficiency in L/100km",
        },
    },
    "required": ["trip_efficiency_l_per_100km", "vehicle_avg_efficiency_l_per_100km"],
}


def calculate_deviation(
    trip_efficiency: float, avg_efficiency: float
) -> Tuple[str, float, str, str]:
    """
    Calculate deviation from average efficiency.

    Args:
        trip_efficiency: Trip efficiency (L/100km)
        avg_efficiency: Vehicle average efficiency (L/100km)

    Returns:
        (status, deviation_percent, message, suggestion)
        status is 'ok' or 'warning'
    """
    if avg_efficiency <= 0:
        return "warning", 0.0, "Cannot calculate deviation: vehicle average efficiency is 0", "Check vehicle average efficiency data."

    # Calculate absolute deviation percentage
    deviation = abs(trip_efficiency - avg_efficiency)
    deviation_percent = (deviation / avg_efficiency) * 100

    if deviation_percent > DEVIATION_THRESHOLD_PERCENT:
        # Determine if higher or lower than average
        if trip_efficiency > avg_efficiency:
            comparison = "higher"
            suggestion = (
                "This trip consumed more fuel than average. "
                "Check for: heavy traffic, AC usage, aggressive driving, cargo load, "
                "or terrain (hills/mountains)."
            )
        else:
            comparison = "lower"
            suggestion = (
                "This trip consumed less fuel than average. "
                "Possible reasons: highway driving, ideal conditions, light traffic, "
                "or eco-driving techniques."
            )

        message = (
            f"Trip efficiency {trip_efficiency:.2f} L/100km is {deviation_percent:.1f}% "
            f"{comparison} than vehicle average {avg_efficiency:.2f} L/100km "
            f"(threshold: {DEVIATION_THRESHOLD_PERCENT}%)"
        )

        return "warning", deviation_percent, message, suggestion
    else:
        message = (
            f"Trip efficiency {trip_efficiency:.2f} L/100km is within normal range "
            f"of vehicle average {avg_efficiency:.2f} L/100km "
            f"({deviation_percent:.1f}% deviation)"
        )
        suggestion = "Trip efficiency is consistent with vehicle average."
        return "ok", deviation_percent, message, suggestion


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare trip efficiency to vehicle average.

    Args:
        arguments: Tool input arguments

    Returns:
        Deviation analysis with status, deviation_percent, message, and suggestion
    """
    try:
        trip_efficiency = arguments.get("trip_efficiency_l_per_100km")
        vehicle_avg = arguments.get("vehicle_avg_efficiency_l_per_100km")

        if trip_efficiency is None:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "trip_efficiency_l_per_100km is required",
                },
            }

        if vehicle_avg is None:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "vehicle_avg_efficiency_l_per_100km is required",
                },
            }

        # Validate inputs
        if trip_efficiency < 0:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Trip efficiency cannot be negative",
                },
            }

        if vehicle_avg < 0:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Vehicle average efficiency cannot be negative",
                },
            }

        # Calculate deviation
        status, deviation_percent, message, suggestion = calculate_deviation(
            trip_efficiency, vehicle_avg
        )

        return {
            "status": status,
            "deviation_percent": round(deviation_percent, 2),
            "message": message,
            "suggestion": suggestion,
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Deviation check failed: {str(e)}",
            },
        }
