"""
Validation MCP Server Demo

Demonstrates all 4 validation algorithms with example data.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-servers"))

from validation.tools import (
    check_efficiency,
    check_deviation_from_average,
    validate_trip,
)


async def demo_check_efficiency():
    """Demo efficiency reasonability checks."""
    print("\n" + "=" * 60)
    print("DEMO 1: Efficiency Reasonability Check")
    print("=" * 60)

    test_cases = [
        {
            "name": "✓ Normal Diesel Efficiency",
            "input": {"efficiency_l_per_100km": 8.5, "fuel_type": "Diesel"},
        },
        {
            "name": "✗ Unrealistically Low Diesel",
            "input": {"efficiency_l_per_100km": 3.0, "fuel_type": "Diesel"},
        },
        {
            "name": "✗ Unrealistically High Diesel",
            "input": {"efficiency_l_per_100km": 18.0, "fuel_type": "Diesel"},
        },
        {
            "name": "⚠ Near Upper Boundary (Diesel)",
            "input": {"efficiency_l_per_100km": 14.5, "fuel_type": "Diesel"},
        },
        {
            "name": "✓ Normal Gasoline Efficiency",
            "input": {"efficiency_l_per_100km": 10.5, "fuel_type": "Gasoline"},
        },
        {
            "name": "✓ Normal Hybrid Efficiency",
            "input": {"efficiency_l_per_100km": 5.5, "fuel_type": "Hybrid"},
        },
    ]

    for case in test_cases:
        print(f"\n{case['name']}")
        print(f"Input: {case['input']}")
        result = await check_efficiency.execute(case["input"])
        print(f"Status: {result['status']}")
        print(f"Range: {result['expected_range']['min']}-{result['expected_range']['max']} L/100km")
        print(f"Message: {result['message']}")


async def demo_check_deviation():
    """Demo deviation from average checks."""
    print("\n" + "=" * 60)
    print("DEMO 2: Deviation from Average Check")
    print("=" * 60)

    test_cases = [
        {
            "name": "✓ No Deviation (Exactly Average)",
            "input": {
                "trip_efficiency_l_per_100km": 8.5,
                "vehicle_avg_efficiency_l_per_100km": 8.5,
            },
        },
        {
            "name": "✓ Small Deviation (6%)",
            "input": {
                "trip_efficiency_l_per_100km": 9.0,
                "vehicle_avg_efficiency_l_per_100km": 8.5,
            },
        },
        {
            "name": "⚠ Large Deviation Higher (41%)",
            "input": {
                "trip_efficiency_l_per_100km": 12.0,
                "vehicle_avg_efficiency_l_per_100km": 8.5,
            },
        },
        {
            "name": "⚠ Large Deviation Lower (29%)",
            "input": {
                "trip_efficiency_l_per_100km": 6.0,
                "vehicle_avg_efficiency_l_per_100km": 8.5,
            },
        },
        {
            "name": "✓ At Threshold (Exactly 20%)",
            "input": {
                "trip_efficiency_l_per_100km": 10.2,
                "vehicle_avg_efficiency_l_per_100km": 8.5,
            },
        },
    ]

    for case in test_cases:
        print(f"\n{case['name']}")
        print(f"Input: Trip {case['input']['trip_efficiency_l_per_100km']} L/100km vs Avg {case['input']['vehicle_avg_efficiency_l_per_100km']} L/100km")
        result = await check_deviation_from_average.execute(case["input"])
        print(f"Status: {result['status']}")
        print(f"Deviation: {result['deviation_percent']:.1f}%")
        print(f"Message: {result['message']}")
        if result["status"] == "warning":
            print(f"Suggestion: {result['suggestion']}")


async def demo_validate_trip():
    """Demo comprehensive trip validation."""
    print("\n" + "=" * 60)
    print("DEMO 3: Comprehensive Trip Validation")
    print("=" * 60)

    test_cases = [
        {
            "name": "✓ Perfect Trip (All Checks Pass)",
            "trip": {
                "distance_km": 410,
                "fuel_consumption_liters": 34.85,
                "fuel_efficiency_l_per_100km": 8.5,
                "vehicle_avg_efficiency_l_per_100km": 8.5,
                "fuel_type": "Diesel",
            },
        },
        {
            "name": "⚠ Very Long Trip",
            "trip": {
                "distance_km": 2500,
                "fuel_efficiency_l_per_100km": 8.5,
                "fuel_type": "Diesel",
            },
        },
        {
            "name": "✗ Zero Distance",
            "trip": {
                "distance_km": 0,
                "fuel_efficiency_l_per_100km": 8.5,
                "fuel_type": "Diesel",
            },
        },
        {
            "name": "✗ Unrealistic Efficiency",
            "trip": {
                "distance_km": 410,
                "fuel_efficiency_l_per_100km": 25.0,
                "fuel_type": "Diesel",
            },
        },
        {
            "name": "⚠ High Deviation from Average",
            "trip": {
                "distance_km": 410,
                "fuel_efficiency_l_per_100km": 12.0,
                "vehicle_avg_efficiency_l_per_100km": 8.5,
                "fuel_type": "Diesel",
            },
        },
    ]

    for case in test_cases:
        print(f"\n{case['name']}")
        print(f"Distance: {case['trip'].get('distance_km')} km")
        print(f"Efficiency: {case['trip'].get('fuel_efficiency_l_per_100km', 'N/A')} L/100km")
        result = await validate_trip.execute({"trip": case["trip"]})
        print(f"Overall Status: {result['status']}")
        print(f"Distance Check: {result['distance_check']}")
        print(f"Efficiency Check: {result['efficiency_check']}")
        print(f"Deviation Check: {result['deviation_check']}")
        if result.get("warnings"):
            print(f"Warnings: {', '.join(result['warnings'])}")
        if result.get("errors"):
            print(f"Errors: {', '.join(result['errors'])}")


async def demo_edge_cases():
    """Demo edge cases and error handling."""
    print("\n" + "=" * 60)
    print("DEMO 4: Edge Cases and Error Handling")
    print("=" * 60)

    print("\n1. Missing Parameters")
    result = await check_efficiency.execute({})
    print(f"Result: {result}")

    print("\n2. Unknown Fuel Type")
    result = await check_efficiency.execute(
        {"efficiency_l_per_100km": 8.5, "fuel_type": "Nuclear"}
    )
    print(f"Result: {result}")

    print("\n3. Negative Efficiency")
    result = await check_deviation_from_average.execute(
        {
            "trip_efficiency_l_per_100km": -5.0,
            "vehicle_avg_efficiency_l_per_100km": 8.5,
        }
    )
    print(f"Result: {result}")

    print("\n4. Empty Trip Object")
    result = await validate_trip.execute({"trip": {}})
    print(f"Result: {result}")


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("VALIDATION MCP SERVER DEMONSTRATION")
    print("=" * 60)
    print("\nThis demo showcases all 4 validation algorithms:")
    print("1. Efficiency Reasonability Check")
    print("2. Deviation from Average Check")
    print("3. Comprehensive Trip Validation")
    print("4. Edge Cases and Error Handling")

    await demo_check_efficiency()
    await demo_check_deviation()
    await demo_validate_trip()
    await demo_edge_cases()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nAll validation algorithms demonstrated successfully!")
    print("See README.md for full documentation.")


if __name__ == "__main__":
    asyncio.run(main())
