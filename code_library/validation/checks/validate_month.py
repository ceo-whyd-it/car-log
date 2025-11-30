"""
@snippet: validate_month
@mcp: validation
@skill: checks
@description: Validate all trips for a month for Slovak tax compliance
@triggers: validate month, check monthly trips, verify monthly data
@params: vehicle_id, month, year
@returns: monthly validation summary
@version: 1.1

NOTE: This code is executed in the agent's code execution environment.
Adapters are available as globals: car_log_core, validation, etc.
DO NOT import adapters - use them directly.
"""

# Example usage:
# license_plate = "BA-TEST01"
# month = 11
# year = 2025

# Step 1: Find vehicle
vehicles = await car_log_core.list_vehicles()
vehicle_list = vehicles.get('vehicles', [])

vehicle = None
plate_upper = license_plate.upper()
for v in vehicle_list:
    if (v.get('license_plate') or '').upper() == plate_upper:
        vehicle = v
        break

if not vehicle:
    print(f"Vehicle with plate {license_plate} not found")
else:
    vehicle_id = vehicle['vehicle_id']

    # Step 2: Get trips for the month
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"

    trips = await car_log_core.list_trips(
        vehicle_id=vehicle_id,
        start_date=start_date,
        end_date=end_date
    )
    trip_list = trips.get('trips', [])

    if not trip_list:
        print(f"No trips found for {license_plate} in {month}/{year}")
    else:
        print(f"Validating {len(trip_list)} trips for {license_plate} ({month}/{year})")
        print("=" * 50)

        passed = 0
        failed = 0
        all_warnings = []

        for trip in trip_list:
            result = await validation.validate_trip(trip_data=trip)

            if result.get('valid'):
                passed += 1
            else:
                failed += 1

            warnings = result.get('warnings', [])
            all_warnings.extend(warnings)

        compliance_pct = 100 * passed / len(trip_list) if trip_list else 0

        print(f"\nValidation Summary:")
        print(f"  ✓ Passed: {passed}")
        print(f"  ✗ Failed: {failed}")
        print(f"  Compliance: {compliance_pct:.0f}%")

        if all_warnings:
            print(f"\nWarnings ({len(all_warnings)}):")
            for w in all_warnings[:5]:
                print(f"  ⚠ {w}")
            if len(all_warnings) > 5:
                print(f"  ... and {len(all_warnings) - 5} more")

        if compliance_pct >= 95:
            print("\n✓ Excellent! Your mileage log is ready for tax reporting.")
        elif compliance_pct >= 80:
            print("\n⚠ Good, but some trips need attention before tax submission.")
        else:
            print("\n✗ Significant issues found. Please review and fix failed trips.")
