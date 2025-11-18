"""
Simple direct test of matching.py algorithms.
"""

import sys
sys.path.insert(0, '/home/user/car-log/mcp-servers/trip_reconstructor')

from matching import (
    haversine_distance,
    score_gps_match,
    normalize_text,
    score_address_match,
    calculate_hybrid_score,
)


def test_haversine_distance():
    """Test Haversine distance calculation."""
    print("\n=== Test 1: Haversine Distance ===")

    # Bratislava to Košice (approximately 400 km)
    bratislava = (48.1486, 17.1077)
    kosice = (48.7164, 21.2611)

    distance = haversine_distance(
        bratislava[0], bratislava[1],
        kosice[0], kosice[1]
    )

    print(f"Bratislava to Košice: {distance / 1000:.2f} km (straight line)")
    assert 300000 < distance < 330000, f"Expected ~313km straight line, got {distance/1000:.2f}km"

    # Very close points (< 100m)
    nearby = (48.1487, 17.1078)
    distance_nearby = haversine_distance(
        bratislava[0], bratislava[1],
        nearby[0], nearby[1]
    )

    print(f"Nearby points: {distance_nearby:.2f} meters")
    assert distance_nearby < 200, "Should be very close"
    print("✓ PASSED")


def test_gps_scoring():
    """Test GPS scoring thresholds."""
    print("\n=== Test 2: GPS Scoring Thresholds ===")

    test_cases = [
        (50, 100, "< 100m"),
        (150, 90, "100-500m"),
        (1000, 70, "500-2000m"),
        (3000, 40, "2000-5000m"),
        (6000, 0, "> 5000m"),
    ]

    for distance, expected_score, description in test_cases:
        score = score_gps_match(distance)
        print(f"  {description}: {distance}m → {score} points")
        assert score == expected_score, f"Expected {expected_score}, got {score}"

    print("✓ PASSED")


def test_address_normalization():
    """Test Slovak address normalization."""
    print("\n=== Test 3: Address Normalization ===")

    test_cases = [
        ("Košice", "kosice"),
        ("Bratislava, Hlavná 45", "bratislava, hlavna 45"),
        ("NITRA", "nitra"),
        ("Mlynská 123", "mlynska 123"),
    ]

    for original, expected in test_cases:
        normalized = normalize_text(original)
        print(f"  '{original}' → '{normalized}'")
        assert normalized == expected, f"Expected '{expected}', got '{normalized}'"

    print("✓ PASSED")


def test_address_matching():
    """Test address matching scores."""
    print("\n=== Test 4: Address Matching ===")

    test_cases = [
        ("Bratislava, Hlavná 45", "Bratislava, Hlavná 45", "Exact match"),
        ("Košice, Mlynská 123", "Košice, Mlynská 124", "Same city"),
        ("Bratislava, Hlavná 45", "Košice, Hlavná 45", "Different cities"),
    ]

    for addr1, addr2, description in test_cases:
        score = score_address_match(addr1, addr2)
        print(f"  {description}: {score} points")
        assert 0 <= score <= 100, f"Score should be 0-100, got {score}"

    print("✓ PASSED")


def test_hybrid_scoring():
    """Test hybrid scoring (GPS 70% + Address 30%)."""
    print("\n=== Test 5: Hybrid Scoring (GPS 70% + Address 30%) ===")

    # Perfect GPS match (< 100m), perfect address match
    bratislava = (48.1486, 17.1077)
    nearby = (48.1487, 17.1078)

    result = calculate_hybrid_score(
        gap_coords=bratislava,
        template_coords=nearby,
        gap_address="Bratislava, Hlavná 45",
        template_address="Bratislava, Hlavná 45",
    )

    print(f"  Perfect match:")
    print(f"    Total score: {result['total_score']}")
    print(f"    GPS score: {result['gps_score']} (weight: 70%)")
    print(f"    Address score: {result['address_score']} (weight: 30%)")
    print(f"    Distance: {result['distance_meters']}m")

    assert result['total_score'] >= 90, f"Perfect match should score >= 90, got {result['total_score']}"

    # Poor GPS match (> 400km), no address
    far_point = (48.7164, 21.2611)  # Košice

    result2 = calculate_hybrid_score(
        gap_coords=bratislava,
        template_coords=far_point,
    )

    print(f"\n  Poor match (400km away):")
    print(f"    Total score: {result2['total_score']}")
    print(f"    GPS score: {result2['gps_score']}")
    print(f"    Distance: {result2['distance_meters']/1000:.1f}km")

    assert result2['total_score'] < 30, f"Poor match should score < 30, got {result2['total_score']}"

    print("✓ PASSED")


def test_bonuses():
    """Test distance and day-of-week bonuses."""
    print("\n=== Test 6: Bonuses (Distance + Day) ===")

    bratislava = (48.1486, 17.1077)
    nearby = (48.1487, 17.1078)

    # With distance bonus (within 10%)
    result = calculate_hybrid_score(
        gap_coords=bratislava,
        template_coords=nearby,
        template_distance_km=100,
        gap_distance_km=105,  # 5% difference
    )

    print(f"  Distance bonus test:")
    print(f"    Template distance: 100 km")
    print(f"    Gap distance: 105 km (5% diff)")
    print(f"    Distance bonus: {result['distance_bonus']} points")

    assert result['distance_bonus'] > 0, "Should have distance bonus for <10% diff"

    # With day-of-week bonus
    result2 = calculate_hybrid_score(
        gap_coords=bratislava,
        template_coords=nearby,
        gap_day_of_week="Monday",
        template_typical_days=["Monday", "Thursday"],
    )

    print(f"\n  Day-of-week bonus test:")
    print(f"    Gap day: Monday")
    print(f"    Template days: Monday, Thursday")
    print(f"    Day bonus: {result2['day_bonus']} points")

    assert result2['day_bonus'] > 0, "Should have day bonus for matching day"

    print("✓ PASSED")


def main():
    """Run all tests."""
    print("=" * 70)
    print("TRIP-RECONSTRUCTOR CORE MATCHING TESTS")
    print("=" * 70)

    try:
        test_haversine_distance()
        test_gps_scoring()
        test_address_normalization()
        test_address_matching()
        test_hybrid_scoring()
        test_bonuses()

        print("\n" + "=" * 70)
        print("ALL CORE TESTS PASSED ✓")
        print("=" * 70)
        print("\nKey Features Verified:")
        print("  • Haversine distance calculation (Bratislava-Košice: ~313km)")
        print("  • GPS scoring thresholds (100m/500m/2km/5km)")
        print("  • Slovak address normalization (á→a, č→c, etc.)")
        print("  • Hybrid scoring (GPS 70% + Address 30%)")
        print("  • Distance and day-of-week bonuses (up to +20 points)")
        print("=" * 70)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
