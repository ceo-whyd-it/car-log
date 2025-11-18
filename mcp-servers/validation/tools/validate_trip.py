"""
Validate trip - comprehensive trip validation.

Checks:
1. Distance reasonability
2. Fuel consumption vs expected (±15%)
3. Efficiency reasonability
4. Deviation from vehicle average
"""

from typing import Dict, Any

from ..thresholds import CONSUMPTION_VARIANCE_PERCENT, get_efficiency_range
from .check_efficiency import validate_efficiency_range
from .check_deviation_from_average import calculate_deviation

# Input schema for MCP
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "trip": {
            "type": "object",
            "description": "Complete trip object with all fields",
        }
    },
    "required": ["trip"],
}


def validate_fuel_consumption(
    distance_km: float,
    fuel_liters: float,
    avg_efficiency: float,
) -> tuple[str, str]:
    """
    Validate fuel consumption against expected value.

    Args:
        distance_km: Trip distance
        fuel_liters: Actual fuel consumed
        avg_efficiency: Vehicle average efficiency (L/100km)

    Returns:
        (status, message) - status is 'ok', 'warning', or 'error'
    """
    if distance_km <= 0:
        return "error", "Trip distance must be greater than 0"

    if fuel_liters <= 0:
        return "error", "Fuel consumption must be greater than 0"

    # Calculate expected fuel consumption
    expected_fuel = (distance_km / 100) * avg_efficiency

    # Calculate variance
    variance = abs(expected_fuel - fuel_liters)
    variance_percent = (variance / expected_fuel * 100) if expected_fuel > 0 else 0

    if variance_percent > CONSUMPTION_VARIANCE_PERCENT:
        return (
            "error",
            f"Fuel consumption variance too high: expected {expected_fuel:.2f} L, "
            f"actual {fuel_liters:.2f} L ({variance_percent:.1f}% variance, "
            f"threshold: {CONSUMPTION_VARIANCE_PERCENT}%)",
        )
    elif variance_percent > CONSUMPTION_VARIANCE_PERCENT * 0.5:
        # Warning at 7.5% (half of error threshold)
        return (
            "warning",
            f"Fuel consumption variance approaching threshold: {variance_percent:.1f}% "
            f"(expected: {expected_fuel:.2f} L, actual: {fuel_liters:.2f} L)",
        )
    else:
        return "ok", f"Fuel consumption OK ({fuel_liters:.2f} L, variance: {variance_percent:.1f}%)"


async def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate single trip entry.

    Performs comprehensive validation:
    - Distance check
    - Fuel consumption check (±15%)
    - Efficiency reasonability
    - Deviation from average

    Args:
        arguments: Tool input arguments

    Returns:
        Validation result with status and detailed checks
    """
    try:
        trip = arguments.get("trip")

        if trip is None:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Trip object is required",
                },
            }

        if not isinstance(trip, dict):
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Trip must be a dictionary object",
                },
            }

        warnings = []
        errors = []

        # Extract trip data
        distance_km = trip.get("distance_km", 0)
        fuel_consumption_liters = trip.get("fuel_consumption_liters")
        fuel_efficiency = trip.get("fuel_efficiency_l_per_100km")
        vehicle_avg_efficiency = trip.get("vehicle_avg_efficiency_l_per_100km")
        fuel_type = trip.get("fuel_type", "Gasoline")

        # 1. Distance check
        distance_check = "ok"
        if distance_km <= 0:
            errors.append("Trip distance must be greater than 0")
            distance_check = "error"
        elif distance_km > 2000:
            warnings.append(
                f"Very long trip: {distance_km:.1f} km. Verify this is correct."
            )
            distance_check = "warning"

        # 2. Fuel consumption check (if data available)
        consumption_check = "ok"
        if (
            fuel_consumption_liters is not None
            and fuel_efficiency is not None
            and vehicle_avg_efficiency is not None
        ):
            status, message = validate_fuel_consumption(
                distance_km, fuel_consumption_liters, vehicle_avg_efficiency
            )
            consumption_check = status
            if status == "error":
                errors.append(message)
            elif status == "warning":
                warnings.append(message)

        # 3. Efficiency reasonability check
        efficiency_check = "ok"
        if fuel_efficiency is not None:
            eff_status, eff_message = validate_efficiency_range(
                fuel_efficiency, fuel_type
            )
            efficiency_check = eff_status
            if eff_status == "error":
                errors.append(eff_message)
            elif eff_status == "warning":
                warnings.append(eff_message)

        # 4. Deviation from average check
        deviation_check = "ok"
        if fuel_efficiency is not None and vehicle_avg_efficiency is not None:
            dev_status, dev_percent, dev_message, dev_suggestion = calculate_deviation(
                fuel_efficiency, vehicle_avg_efficiency
            )
            deviation_check = dev_status
            if dev_status == "warning":
                warnings.append(dev_message)

        # Determine overall status
        if errors:
            status = "has_errors"
        elif warnings:
            status = "has_warnings"
        else:
            status = "validated"

        return {
            "status": status,
            "distance_check": distance_check,
            "efficiency_check": efficiency_check,
            "consumption_check": consumption_check,
            "deviation_check": deviation_check,
            "warnings": warnings,
            "errors": errors,
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Trip validation failed: {str(e)}",
            },
        }
