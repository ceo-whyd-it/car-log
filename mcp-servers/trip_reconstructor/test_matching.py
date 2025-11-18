"""
Test suite for trip-reconstructor matching algorithms.

Tests:
- GPS distance calculations (Haversine)
- GPS scoring thresholds
- Address normalization and matching
- Hybrid scoring
- Template matching
"""

import asyncio
from matching import (
    haversine_distance,
    score_gps_match,
    normalize_text,
    score_address_match,
    calculate_hybrid_score,
    match_checkpoint_to_template,
)
from tools.match_templates import execute as match_templates_execute
from tools.calculate_template_completeness import execute as calculate_completeness_execute


def test_haversine_distance():
    """Test Haversine distance calculation."""
    print("\n=== Test Haversine Distance ===")

    # Bratislava to Košice (approximately 410 km)
    bratislava = (48.1486, 17.1077)
    kosice = (48.7164, 21.2611)

    distance = haversine_distance(
        bratislava[0], bratislava[1],
        kosice[0], kosice[1]
    )

    print(f"Bratislava to Košice: {distance / 1000:.2f} km")
    assert 350000 < distance < 450000, "Distance should be approximately 400 km"

    # Very close points (< 100m)
    nearby = (48.1487, 17.1078)
    distance_nearby = haversine_distance(
        bratislava[0], bratislava[1],
        nearby[0], nearby[1]
    )

    print(f"Nearby points: {distance_nearby:.2f} meters")
    assert distance_nearby < 200, "Should be very close"


def test_gps_scoring():
    """Test GPS scoring thresholds."""
    print("\n=== Test GPS Scoring ===")

    test_cases = [
        (50, 100, "< 100m"),
        (150, 90, "100-500m"),
        (1000, 70, "500-2000m"),
        (3000, 40, "2000-5000m"),
        (6000, 0, "> 5000m"),
    ]

    for distance, expected_score, description in test_cases:
        score = score_gps_match(distance)
        print(f"{description}: {distance}m → {score} points (expected {expected_score})")
        assert score == expected_score, f"Expected {expected_score}, got {score}"


def test_address_normalization():
    """Test Slovak address normalization."""
    print("\n=== Test Address Normalization ===")

    test_cases = [
        ("Košice", "kosice"),
        ("Bratislava, Hlavná 45", "bratislava, hlavna 45"),
        ("NITRA", "nitra"),
        ("Mlynská 123", "mlynska 123"),
    ]

    for original, expected in test_cases:
        normalized = normalize_text(original)
        print(f"{original} → {normalized}")
        assert normalized == expected, f"Expected {expected}, got {normalized}"


def test_address_matching():
    """Test address matching scores."""
    print("\n=== Test Address Matching ===")

    test_cases = [
        ("Bratislava, Hlavná 45", "Bratislava, Hlavná 45", ">= 90", "Exact match"),
        ("Košice, Mlynská 123", "Košice, Mlynská 124", ">= 60", "Same city, similar street"),
        ("Bratislava, Hlavná 45", "Košice, Hlavná 45", ">= 30", "Different city, same street"),
        ("Bratislava", "Košice", "< 50", "Different cities"),
    ]

    for addr1, addr2, expected_range, description in test_cases:
        score = score_address_match(addr1, addr2)
        print(f"{description}: {score} points (expected {expected_range})")


def test_hybrid_scoring():
    """Test hybrid scoring (GPS 70% + Address 30%)."""
    print("\n=== Test Hybrid Scoring ===")

    # Perfect GPS match (< 100m), good address match
    bratislava = (48.1486, 17.1077)
    nearby = (48.1487, 17.1078)

    result = calculate_hybrid_score(
        gap_coords=bratislava,
        template_coords=nearby,
        gap_address="Bratislava, Hlavná 45",
        template_address="Bratislava, Hlavná 45",
    )

    print(f"Perfect match: {result['total_score']} points")
    print(f"  GPS: {result['gps_score']} (contribution: {result['breakdown']['gps_contribution']})")
    print(f"  Address: {result['address_score']} (contribution: {result['breakdown']['address_contribution']})")
    print(f"  Distance: {result['distance_meters']} meters")

    assert result['total_score'] >= 90, "Should be very high score"

    # Poor GPS match (> 5km), no address
    far_point = (48.7164, 21.2611)  # Košice

    result2 = calculate_hybrid_score(
        gap_coords=bratislava,
        template_coords=far_point,
    )

    print(f"\nPoor match: {result2['total_score']} points")
    print(f"  GPS: {result2['gps_score']} (contribution: {result2['breakdown']['gps_contribution']})")
    print(f"  Distance: {result2['distance_meters']} meters")

    assert result2['total_score'] < 30, "Should be low score"


async def test_template_matching():
    """Test full template matching."""
    print("\n=== Test Template Matching ===")

    # Create gap data (820 km gap)
    gap_data = {
        "distance_km": 820,
        "start_checkpoint": {
            "checkpoint_id": "start-1",
            "datetime": "2025-11-04T08:00:00Z",
            "location": {
                "coords": {"latitude": 48.1486, "longitude": 17.1077},
                "address": "Bratislava",
            }
        },
        "end_checkpoint": {
            "checkpoint_id": "end-1",
            "datetime": "2025-11-08T18:00:00Z",
            "location": {
                "coords": {"latitude": 48.1486, "longitude": 17.1077},
                "address": "Bratislava",
            }
        },
    }

    # Create warehouse template (410 km, round trip)
    warehouse_template = {
        "template_id": "template-1",
        "name": "Warehouse Run",
        "from_coords": {"lat": 48.1486, "lng": 17.1077},
        "from_address": "Bratislava",
        "to_coords": {"lat": 48.7164, "lng": 21.2611},
        "to_address": "Košice, Warehouse",
        "distance_km": 410,
        "is_round_trip": True,
        "typical_days": ["Monday", "Thursday"],
        "purpose": "business",
        "business_description": "Warehouse pickup",
    }

    templates = [warehouse_template]

    # Execute matching
    result = await match_templates_execute({
        "gap_data": gap_data,
        "templates": templates,
        "confidence_threshold": 70,
    })

    print(f"Templates evaluated: {result['templates_evaluated']}")
    print(f"Templates matched: {result['templates_matched']}")

    if result['matched_templates']:
        for match in result['matched_templates']:
            print(f"\nTemplate: {match['template_name']}")
            print(f"  Confidence: {match['confidence_score']}%")
            print(f"  Start match: {match['start_match']['score']} ({match['start_match']['distance_meters']}m)")
            print(f"  End match: {match['end_match']['score']} ({match['end_match']['distance_meters']}m)")

    # Check reconstruction proposal
    proposal = result.get('reconstruction_proposal', {})
    if proposal.get('has_proposal'):
        print(f"\nReconstruction Proposal:")
        print(f"  Gap distance: {proposal['gap_distance_km']} km")
        print(f"  Reconstructed: {proposal['reconstructed_km']} km")
        print(f"  Coverage: {proposal['coverage_percent']}%")
        print(f"  Quality: {proposal['reconstruction_quality']}")

        for trip in proposal.get('proposed_trips', []):
            print(f"\n  Trip: {trip['template_name']}")
            print(f"    Count: {trip['num_trips']} trips")
            print(f"    Distance: {trip['distance_km']} km (round trip: {trip['is_round_trip']})")
            print(f"    Total: {trip['total_distance_km']} km")


async def test_template_completeness():
    """Test template completeness calculation."""
    print("\n=== Test Template Completeness ===")

    # Complete template
    complete_template = {
        "name": "Warehouse Run",
        "from_coords": {"lat": 48.1486, "lng": 17.1077},
        "from_address": "Bratislava",
        "from_label": "Bratislava",
        "to_coords": {"lat": 48.7164, "lng": 21.2611},
        "to_address": "Košice",
        "to_label": "Košice",
        "distance_km": 410,
        "is_round_trip": True,
        "typical_days": ["Monday", "Thursday"],
        "purpose": "business",
        "business_description": "Warehouse pickup",
    }

    result = await calculate_completeness_execute({
        "template": complete_template
    })

    print(f"Complete template:")
    print(f"  Valid: {result['is_valid']}")
    print(f"  Completeness: {result['completeness_percent']}%")
    print(f"  Quality: {result['quality']}")
    print(f"  Optional fields present: {result['optional_fields']['present']}/{result['optional_fields']['total']}")

    # Minimal template
    minimal_template = {
        "name": "Basic Route",
        "from_coords": {"lat": 48.1486, "lng": 17.1077},
        "to_coords": {"lat": 48.7164, "lng": 21.2611},
    }

    result2 = await calculate_completeness_execute({
        "template": minimal_template
    })

    print(f"\nMinimal template:")
    print(f"  Valid: {result2['is_valid']}")
    print(f"  Completeness: {result2['completeness_percent']}%")
    print(f"  Quality: {result2['quality']}")
    print(f"  Suggestions ({len(result2['suggestions'])}):")
    for suggestion in result2['suggestions'][:3]:
        print(f"    - {suggestion}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("TRIP-RECONSTRUCTOR TEST SUITE")
    print("=" * 60)

    try:
        test_haversine_distance()
        test_gps_scoring()
        test_address_normalization()
        test_address_matching()
        test_hybrid_scoring()
        await test_template_matching()
        await test_template_completeness()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
