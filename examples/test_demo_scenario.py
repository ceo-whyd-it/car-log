"""
Demo scenario test: 820 km gap with Warehouse Run template.

This demonstrates the core use case from the specification:
- Gap: 820 km (Nov 4-8, Bratislava to Bratislava)
- Template: Warehouse Run (410 km, round trip)
- Expected: 1× round trip = 820 km (100% coverage)
"""

import sys
import asyncio
import json

# Add paths
sys.path.insert(0, '/home/user/car-log/mcp-servers/trip_reconstructor')

# Import directly to avoid package issues
import os
os.chdir('/home/user/car-log/mcp-servers/trip_reconstructor')

# Now import
from matching import match_checkpoint_to_template, calculate_hybrid_score


def test_demo_scenario():
    """Test the 820 km demo scenario."""
    print("=" * 70)
    print("DEMO SCENARIO: 820 km Gap with Warehouse Run Template")
    print("=" * 70)

    # Gap checkpoints (both at Bratislava)
    start_checkpoint = {
        "checkpoint_id": "ckpt-1",
        "datetime": "2025-11-04T08:00:00Z",  # Monday
        "odometer_km": 50000,
        "location": {
            "coords": {"latitude": 48.1486, "longitude": 17.1077},
            "address": "Bratislava, Fuel Station",
        }
    }

    end_checkpoint = {
        "checkpoint_id": "ckpt-2",
        "datetime": "2025-11-08T18:00:00Z",  # Friday
        "odometer_km": 50820,
        "location": {
            "coords": {"latitude": 48.1486, "longitude": 17.1077},
            "address": "Bratislava, Fuel Station",
        }
    }

    gap_distance_km = 820

    print("\nGap Analysis:")
    print(f"  Start: {start_checkpoint['datetime']} @ Bratislava")
    print(f"  End: {end_checkpoint['datetime']} @ Bratislava")
    print(f"  Distance: {gap_distance_km} km")
    print(f"  Duration: 4 days (Monday-Friday)")

    # Warehouse Run template
    warehouse_template = {
        "template_id": "tmpl-1",
        "name": "Warehouse Run",
        "from_coords": {"lat": 48.1486, "lng": 17.1077},
        "from_address": "Bratislava",
        "from_label": "Bratislava",
        "to_coords": {"lat": 48.7164, "lng": 21.2611},
        "to_address": "Košice, Warehouse",
        "to_label": "Košice",
        "distance_km": 410,
        "is_round_trip": True,
        "typical_days": ["Monday", "Thursday"],
        "purpose": "business",
        "business_description": "Warehouse pickup",
    }

    print("\nTemplate:")
    print(f"  Name: {warehouse_template['name']}")
    print(f"  Route: {warehouse_template['from_label']} → {warehouse_template['to_label']}")
    print(f"  Distance: {warehouse_template['distance_km']} km (one way)")
    print(f"  Round trip: {warehouse_template['is_round_trip']}")
    print(f"  Typical days: {', '.join(warehouse_template['typical_days'])}")

    # Match start checkpoint to template FROM endpoint
    print("\n" + "-" * 70)
    print("Matching Start Checkpoint (Bratislava) to Template FROM Endpoint")
    print("-" * 70)

    start_match = match_checkpoint_to_template(
        gap_checkpoint=start_checkpoint,
        template=warehouse_template,
        endpoint='from',
        gap_distance_km=gap_distance_km,
        gap_day_of_week="Monday",
    )

    if start_match['success']:
        print(f"✓ Match successful")
        print(f"  Score: {start_match['score']}")
        print(f"  GPS score: {start_match['details']['gps_score']}")
        print(f"  Address score: {start_match['details']['address_score']}")
        print(f"  Distance: {start_match['details']['distance_meters']}m")
        print(f"  Bonuses: +{start_match['details']['distance_bonus'] + start_match['details']['day_bonus']} points")
    else:
        print(f"✗ Match failed: {start_match['error']}")

    # Match end checkpoint to template TO endpoint (should also match FROM since round trip)
    print("\n" + "-" * 70)
    print("Matching End Checkpoint (Bratislava) to Template FROM Endpoint")
    print("(Round trip returns to start, so end also matches FROM)")
    print("-" * 70)

    end_match = match_checkpoint_to_template(
        gap_checkpoint=end_checkpoint,
        template=warehouse_template,
        endpoint='from',  # Round trip, so end also at FROM
        gap_distance_km=gap_distance_km,
        gap_day_of_week="Friday",
    )

    if end_match['success']:
        print(f"✓ Match successful")
        print(f"  Score: {end_match['score']}")
        print(f"  GPS score: {end_match['details']['gps_score']}")
        print(f"  Address score: {end_match['details']['address_score']}")
        print(f"  Distance: {end_match['details']['distance_meters']}m")
        print(f"  Bonuses: +{end_match['details']['distance_bonus'] + end_match['details']['day_bonus']} points")
    else:
        print(f"✗ Match failed: {end_match['error']}")

    # Calculate average confidence
    if start_match['success'] and end_match['success']:
        avg_confidence = (start_match['score'] + end_match['score']) / 2
        print("\n" + "-" * 70)
        print("Overall Match Quality")
        print("-" * 70)
        print(f"  Average confidence: {avg_confidence:.2f}%")
        print(f"  Status: {'✓ ABOVE THRESHOLD' if avg_confidence >= 70 else '✗ BELOW THRESHOLD'} (threshold: 70%)")

        # Reconstruction proposal
        print("\n" + "=" * 70)
        print("RECONSTRUCTION PROPOSAL")
        print("=" * 70)

        effective_distance = warehouse_template['distance_km'] * 2 if warehouse_template['is_round_trip'] else warehouse_template['distance_km']
        num_trips = int(gap_distance_km / effective_distance)
        reconstructed_km = num_trips * effective_distance
        coverage_pct = (reconstructed_km / gap_distance_km * 100)

        print(f"  Gap to fill: {gap_distance_km} km")
        print(f"  Template: {warehouse_template['name']}")
        print(f"  Effective distance: {effective_distance} km (round trip)")
        print(f"  Number of trips: {num_trips}")
        print(f"  Reconstructed: {reconstructed_km} km")
        print(f"  Coverage: {coverage_pct:.1f}%")
        print(f"  Quality: {'EXCELLENT' if coverage_pct >= 90 else 'GOOD' if coverage_pct >= 70 else 'PARTIAL'}")

        print("\n" + "=" * 70)
        if coverage_pct >= 90:
            print("✓ DEMO SCENARIO PASSED: 100% coverage achieved")
        else:
            print(f"⚠ WARNING: Only {coverage_pct:.1f}% coverage")
        print("=" * 70)

        return avg_confidence >= 70 and coverage_pct >= 90

    return False


def main():
    """Run demo scenario."""
    try:
        success = test_demo_scenario()
        if not success:
            print("\n❌ Demo scenario failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
