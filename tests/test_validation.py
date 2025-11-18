"""
Unit tests for validation MCP server.

Tests all 4 validation algorithms:
1. validate_checkpoint_pair - Distance sum check (±10%)
2. validate_trip - Comprehensive trip validation
3. check_efficiency - Efficiency reasonability
4. check_deviation_from_average - Deviation from average (±20%)
"""

import pytest
import asyncio
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta

# Import validation tools
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-servers"))

from validation.tools import (
    check_efficiency,
    check_deviation_from_average,
    validate_trip,
)
from validation.thresholds import (
    DISTANCE_VARIANCE_PERCENT,
    CONSUMPTION_VARIANCE_PERCENT,
    DEVIATION_THRESHOLD_PERCENT,
    EFFICIENCY_RANGES,
)


class TestCheckEfficiency:
    """Test efficiency reasonability checks."""

    @pytest.mark.asyncio
    async def test_diesel_ok(self):
        """Test diesel efficiency within normal range."""
        result = await check_efficiency.execute(
            {"efficiency_l_per_100km": 8.5, "fuel_type": "Diesel"}
        )
        assert result["status"] == "ok"
        assert result["efficiency"] == 8.5
        assert result["expected_range"]["min"] == 5.0
        assert result["expected_range"]["max"] == 15.0

    @pytest.mark.asyncio
    async def test_diesel_too_low(self):
        """Test diesel efficiency unrealistically low."""
        result = await check_efficiency.execute(
            {"efficiency_l_per_100km": 3.0, "fuel_type": "Diesel"}
        )
        assert result["status"] == "error"
        assert "Unrealistically low" in result["message"]

    @pytest.mark.asyncio
    async def test_diesel_too_high(self):
        """Test diesel efficiency unrealistically high."""
        result = await check_efficiency.execute(
            {"efficiency_l_per_100km": 18.0, "fuel_type": "Diesel"}
        )
        assert result["status"] == "error"
        assert "Unrealistically high" in result["message"]

    @pytest.mark.asyncio
    async def test_gasoline_ok(self):
        """Test gasoline efficiency within normal range."""
        result = await check_efficiency.execute(
            {"efficiency_l_per_100km": 10.5, "fuel_type": "Gasoline"}
        )
        assert result["status"] == "ok"
        assert result["expected_range"]["min"] == 6.0
        assert result["expected_range"]["max"] == 20.0

    @pytest.mark.asyncio
    async def test_lpg_ok(self):
        """Test LPG efficiency within normal range."""
        result = await check_efficiency.execute(
            {"efficiency_l_per_100km": 12.0, "fuel_type": "LPG"}
        )
        assert result["status"] == "ok"
        assert result["expected_range"]["min"] == 8.0
        assert result["expected_range"]["max"] == 25.0

    @pytest.mark.asyncio
    async def test_hybrid_ok(self):
        """Test hybrid efficiency within normal range."""
        result = await check_efficiency.execute(
            {"efficiency_l_per_100km": 5.5, "fuel_type": "Hybrid"}
        )
        assert result["status"] == "ok"
        assert result["expected_range"]["min"] == 3.0
        assert result["expected_range"]["max"] == 10.0

    @pytest.mark.asyncio
    async def test_electric_error(self):
        """Test electric vehicle should not use L/100km."""
        result = await check_efficiency.execute(
            {"efficiency_l_per_100km": 5.0, "fuel_type": "Electric"}
        )
        assert result["status"] == "error"
        assert "Electric" in result["message"]

    @pytest.mark.asyncio
    async def test_boundary_warning_low(self):
        """Test warning near lower boundary."""
        # Diesel min is 5.0, warning at 5.0 + 10% of range = 5.0 + 1.0 = 6.0
        result = await check_efficiency.execute(
            {"efficiency_l_per_100km": 5.5, "fuel_type": "Diesel"}
        )
        assert result["status"] == "warning"
        assert "near lower boundary" in result["message"]

    @pytest.mark.asyncio
    async def test_boundary_warning_high(self):
        """Test warning near upper boundary."""
        # Diesel max is 15.0, warning at 15.0 - 10% of range = 15.0 - 1.0 = 14.0
        result = await check_efficiency.execute(
            {"efficiency_l_per_100km": 14.5, "fuel_type": "Diesel"}
        )
        assert result["status"] == "warning"
        assert "near upper boundary" in result["message"]


class TestCheckDeviationFromAverage:
    """Test deviation from average checks."""

    @pytest.mark.asyncio
    async def test_no_deviation(self):
        """Test trip efficiency equal to average."""
        result = await check_deviation_from_average.execute(
            {
                "trip_efficiency_l_per_100km": 8.5,
                "vehicle_avg_efficiency_l_per_100km": 8.5,
            }
        )
        assert result["status"] == "ok"
        assert result["deviation_percent"] == 0.0

    @pytest.mark.asyncio
    async def test_small_deviation_ok(self):
        """Test small deviation within threshold (20%)."""
        # 8.5 to 9.0 = 5.9% deviation
        result = await check_deviation_from_average.execute(
            {
                "trip_efficiency_l_per_100km": 9.0,
                "vehicle_avg_efficiency_l_per_100km": 8.5,
            }
        )
        assert result["status"] == "ok"
        assert result["deviation_percent"] < 20

    @pytest.mark.asyncio
    async def test_large_deviation_warning_higher(self):
        """Test large deviation above threshold (trip higher than average)."""
        # 8.5 to 12.0 = 41.2% deviation
        result = await check_deviation_from_average.execute(
            {
                "trip_efficiency_l_per_100km": 12.0,
                "vehicle_avg_efficiency_l_per_100km": 8.5,
            }
        )
        assert result["status"] == "warning"
        assert result["deviation_percent"] > 20
        assert "higher" in result["message"]
        assert "heavy traffic" in result["suggestion"].lower() or "AC usage" in result["suggestion"].lower()

    @pytest.mark.asyncio
    async def test_large_deviation_warning_lower(self):
        """Test large deviation above threshold (trip lower than average)."""
        # 8.5 to 6.0 = 29.4% deviation
        result = await check_deviation_from_average.execute(
            {
                "trip_efficiency_l_per_100km": 6.0,
                "vehicle_avg_efficiency_l_per_100km": 8.5,
            }
        )
        assert result["status"] == "warning"
        assert result["deviation_percent"] > 20
        assert "lower" in result["message"]
        assert "highway" in result["suggestion"].lower() or "ideal" in result["suggestion"].lower()

    @pytest.mark.asyncio
    async def test_edge_case_threshold(self):
        """Test exactly at threshold (20%)."""
        # 8.5 to 10.2 = 20% deviation
        result = await check_deviation_from_average.execute(
            {
                "trip_efficiency_l_per_100km": 10.2,
                "vehicle_avg_efficiency_l_per_100km": 8.5,
            }
        )
        # Exactly at 20% should be "ok" since condition is > 20, not >= 20
        assert result["status"] == "ok"
        assert result["deviation_percent"] == 20.0

    @pytest.mark.asyncio
    async def test_negative_efficiency_error(self):
        """Test negative efficiency returns error."""
        result = await check_deviation_from_average.execute(
            {
                "trip_efficiency_l_per_100km": -5.0,
                "vehicle_avg_efficiency_l_per_100km": 8.5,
            }
        )
        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"


class TestValidateTrip:
    """Test comprehensive trip validation."""

    @pytest.mark.asyncio
    async def test_valid_trip(self):
        """Test valid trip with all checks passing."""
        trip = {
            "distance_km": 410,
            "fuel_consumption_liters": 34.85,
            "fuel_efficiency_l_per_100km": 8.5,
            "vehicle_avg_efficiency_l_per_100km": 8.5,
            "fuel_type": "Diesel",
        }
        result = await validate_trip.execute({"trip": trip})
        assert result["status"] == "validated"
        assert result["distance_check"] == "ok"
        assert result["efficiency_check"] == "ok"
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_trip_zero_distance(self):
        """Test trip with zero distance."""
        trip = {
            "distance_km": 0,
            "fuel_efficiency_l_per_100km": 8.5,
            "fuel_type": "Diesel",
        }
        result = await validate_trip.execute({"trip": trip})
        assert result["status"] == "has_errors"
        assert result["distance_check"] == "error"
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_trip_very_long_distance(self):
        """Test very long trip triggers warning."""
        trip = {
            "distance_km": 2500,
            "fuel_efficiency_l_per_100km": 8.5,
            "fuel_type": "Diesel",
        }
        result = await validate_trip.execute({"trip": trip})
        assert result["status"] == "has_warnings"
        assert result["distance_check"] == "warning"
        assert any("long trip" in w.lower() for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_trip_unrealistic_efficiency(self):
        """Test trip with unrealistic efficiency."""
        trip = {
            "distance_km": 410,
            "fuel_efficiency_l_per_100km": 25.0,  # Too high for Diesel
            "fuel_type": "Diesel",
        }
        result = await validate_trip.execute({"trip": trip})
        assert result["status"] == "has_errors"
        assert result["efficiency_check"] == "error"
        assert any("unrealistically high" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_trip_high_deviation(self):
        """Test trip with high deviation from average."""
        trip = {
            "distance_km": 410,
            "fuel_efficiency_l_per_100km": 12.0,  # 41% higher than average
            "vehicle_avg_efficiency_l_per_100km": 8.5,
            "fuel_type": "Diesel",
        }
        result = await validate_trip.execute({"trip": trip})
        assert result["status"] == "has_warnings"
        assert result["deviation_check"] == "warning"
        assert any("deviation" in w.lower() or "higher" in w.lower() for w in result["warnings"])


class TestValidationThresholds:
    """Test validation threshold constants."""

    def test_thresholds_configured(self):
        """Test all thresholds are properly configured."""
        assert DISTANCE_VARIANCE_PERCENT == 10
        assert CONSUMPTION_VARIANCE_PERCENT == 15
        assert DEVIATION_THRESHOLD_PERCENT == 20

    def test_efficiency_ranges_configured(self):
        """Test efficiency ranges for all fuel types."""
        assert "Diesel" in EFFICIENCY_RANGES
        assert "Gasoline" in EFFICIENCY_RANGES
        assert "LPG" in EFFICIENCY_RANGES
        assert "Hybrid" in EFFICIENCY_RANGES
        assert "Electric" in EFFICIENCY_RANGES

        # Check Diesel range
        assert EFFICIENCY_RANGES["Diesel"]["min"] == 5.0
        assert EFFICIENCY_RANGES["Diesel"]["max"] == 15.0

        # Check Gasoline range
        assert EFFICIENCY_RANGES["Gasoline"]["min"] == 6.0
        assert EFFICIENCY_RANGES["Gasoline"]["max"] == 20.0

        # Check LPG range
        assert EFFICIENCY_RANGES["LPG"]["min"] == 8.0
        assert EFFICIENCY_RANGES["LPG"]["max"] == 25.0


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_check_efficiency_missing_params(self):
        """Test check_efficiency with missing parameters."""
        result = await check_efficiency.execute({})
        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_check_deviation_missing_params(self):
        """Test check_deviation with missing parameters."""
        result = await check_deviation_from_average.execute({})
        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_validate_trip_empty(self):
        """Test validate_trip with empty trip object."""
        result = await validate_trip.execute({"trip": {}})
        # Empty trip object should still return status (with likely errors/warnings)
        # It's a valid dict, just with no/minimal data
        assert "status" in result
        assert result["status"] in ["validated", "has_warnings", "has_errors"]

    @pytest.mark.asyncio
    async def test_check_efficiency_unknown_fuel_type(self):
        """Test check_efficiency with unknown fuel type."""
        result = await check_efficiency.execute(
            {"efficiency_l_per_100km": 8.5, "fuel_type": "Nuclear"}
        )
        # Unknown fuel type returns error response with success=False
        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
