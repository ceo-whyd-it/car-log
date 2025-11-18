"""
Validation thresholds and constants.

These values are configurable via environment variables.
"""

import os

# Distance validation threshold (percentage)
DISTANCE_VARIANCE_PERCENT = int(os.getenv("DISTANCE_VARIANCE_PERCENT", "10"))

# Fuel consumption validation threshold (percentage)
CONSUMPTION_VARIANCE_PERCENT = int(os.getenv("CONSUMPTION_VARIANCE_PERCENT", "15"))

# Deviation from average warning threshold (percentage)
DEVIATION_THRESHOLD_PERCENT = int(os.getenv("DEVIATION_THRESHOLD_PERCENT", "20"))

# Fuel efficiency ranges (L/100km) by fuel type
EFFICIENCY_RANGES = {
    "Diesel": {
        "min": float(os.getenv("DIESEL_MIN_L_PER_100KM", "5.0")),
        "max": float(os.getenv("DIESEL_MAX_L_PER_100KM", "15.0")),
    },
    "Gasoline": {
        "min": float(os.getenv("GASOLINE_MIN_L_PER_100KM", "6.0")),
        "max": float(os.getenv("GASOLINE_MAX_L_PER_100KM", "20.0")),
    },
    "LPG": {
        "min": float(os.getenv("LPG_MIN_L_PER_100KM", "8.0")),
        "max": float(os.getenv("LPG_MAX_L_PER_100KM", "25.0")),
    },
    "Hybrid": {
        "min": float(os.getenv("HYBRID_MIN_L_PER_100KM", "3.0")),
        "max": float(os.getenv("HYBRID_MAX_L_PER_100KM", "10.0")),
    },
    "Electric": {
        "min": 0.0,  # Electric vehicles don't use L/100km
        "max": 0.0,
    },
}


def get_efficiency_range(fuel_type: str) -> dict:
    """
    Get efficiency range for a fuel type.

    Args:
        fuel_type: One of Diesel, Gasoline, LPG, Hybrid, Electric

    Returns:
        Dict with 'min' and 'max' keys (L/100km)

    Raises:
        ValueError: If fuel_type is unknown
    """
    if fuel_type not in EFFICIENCY_RANGES:
        raise ValueError(
            f"Unknown fuel type: {fuel_type}. "
            f"Must be one of {list(EFFICIENCY_RANGES.keys())}"
        )

    return EFFICIENCY_RANGES[fuel_type]
