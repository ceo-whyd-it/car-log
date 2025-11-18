"""
Demonstrate template matching with various confidence scores.
"""

import sys
sys.path.insert(0, '/home/user/car-log/mcp-servers/trip_reconstructor')

from matching import calculate_hybrid_score


def demo_confidence_scores():
    """Show how different scenarios produce different confidence scores."""
    print("=" * 80)
    print("TEMPLATE MATCHING CONFIDENCE SCORE EXAMPLES")
    print("=" * 80)

    bratislava = (48.1486, 17.1077)
    kosice = (48.7164, 21.2611)

    scenarios = [
        {
            "name": "Perfect Match",
            "description": "Exact GPS match (<10m) + exact address",
            "gap_coords": bratislava,
            "template_coords": bratislava,
            "gap_address": "Bratislava, Hlavná 45",
            "template_address": "Bratislava, Hlavná 45",
        },
        {
            "name": "Excellent Match",
            "description": "Close GPS match (50m) + same city",
            "gap_coords": bratislava,
            "template_coords": (48.1491, 17.1080),  # ~50m away
            "gap_address": "Bratislava, Hlavná 45",
            "template_address": "Bratislava, Mlynská 10",
        },
        {
            "name": "Good Match (GPS only)",
            "description": "Close GPS match (200m), no address",
            "gap_coords": bratislava,
            "template_coords": (48.1504, 17.1077),  # ~200m away
        },
        {
            "name": "Fair Match",
            "description": "Medium distance (1km) + different address",
            "gap_coords": bratislava,
            "template_coords": (48.1576, 17.1077),  # ~1km away
            "gap_address": "Bratislava, Hlavná 45",
            "template_address": "Bratislava, Štúrova 10",
        },
        {
            "name": "Poor Match",
            "description": "Far distance (5km+)",
            "gap_coords": bratislava,
            "template_coords": (48.2086, 17.1077),  # ~6.5km away
        },
        {
            "name": "No Match",
            "description": "Different city entirely (313km)",
            "gap_coords": bratislava,
            "template_coords": kosice,
            "gap_address": "Bratislava",
            "template_address": "Košice",
        },
    ]

    print("\nScoring Breakdown:")
    print("-" * 80)

    for scenario in scenarios:
        result = calculate_hybrid_score(
            gap_coords=scenario['gap_coords'],
            template_coords=scenario['template_coords'],
            gap_address=scenario.get('gap_address'),
            template_address=scenario.get('template_address'),
        )

        print(f"\n{scenario['name']}: {result['total_score']:.1f} points")
        print(f"  {scenario['description']}")
        print(f"  GPS: {result['gps_score']} → {result['breakdown']['gps_contribution']:.1f} points (70% weight)")
        print(f"  Address: {result['address_score']} → {result['breakdown']['address_contribution']:.1f} points (30% weight)")
        print(f"  Distance: {result['distance_meters']:.0f}m")

        if result['total_score'] >= 90:
            status = "✓ EXCELLENT (>90)"
        elif result['total_score'] >= 70:
            status = "✓ GOOD (>70, passes threshold)"
        elif result['total_score'] >= 50:
            status = "⚠ FAIR (50-70, below threshold)"
        else:
            status = "✗ POOR (<50, rejected)"

        print(f"  → {status}")

    print("\n" + "=" * 80)
    print("CONFIDENCE THRESHOLD: 70 points")
    print("=" * 80)
    print("\nScoring Formula:")
    print("  Base Score = (GPS Score × 70%) + (Address Score × 30%)")
    print("  Total Score = Base Score + Distance Bonus (0-10) + Day Bonus (0-10)")
    print("\nGPS Scoring:")
    print("  < 100m     → 100 points")
    print("  100-500m   → 90 points")
    print("  500-2000m  → 70 points")
    print("  2000-5000m → 40 points")
    print("  > 5000m    → 0 points")
    print("\nBonuses:")
    print("  Distance: +10 points if template distance within 10% of gap")
    print("  Day: +10 points if gap day matches template typical_days")
    print("=" * 80)


if __name__ == "__main__":
    demo_confidence_scores()
