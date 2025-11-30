"""
@snippet: generate_monthly_report
@mcp: report_generator
@skill: monthly
@description: Generate a monthly mileage report for a vehicle
@triggers: generate report, monthly report, create report, mileage report, tax report
@params: vehicle_id, month, year
@returns: report file path and summary
@version: 1.1

NOTE: This code is executed in the agent's code execution environment.
Adapters are available as globals: car_log_core, report_generator, etc.
DO NOT import adapters - use them directly.
"""

# Example usage in agent code execution:
# vehicle_id = "test-vehicle-id"
# license_plate = "BA-TEST01"
# month = 11
# year = 2025

# Step 1: Find vehicle by license plate
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

    # Step 2: Format date range
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"

    # Step 3: Get trips for the month
    trips = await car_log_core.list_trips(
        vehicle_id=vehicle_id,
        start_date=start_date,
        end_date=end_date
    )
    trip_list = trips.get('trips', [])

    # Step 4: Get checkpoints for context
    checkpoints = await car_log_core.list_checkpoints(
        vehicle_id=vehicle_id,
        start_date=start_date,
        end_date=end_date
    )
    checkpoint_list = checkpoints.get('checkpoints', [])

    if not trip_list:
        print(f"No trips found for {license_plate} in {month}/{year}")
        print(f"Found {len(checkpoint_list)} checkpoints but no logged trips.")
        print("You may need to reconstruct trips from gaps first.")
    else:
        # Step 5: Calculate summary
        total_km = sum(t.get('distance_km', 0) for t in trip_list)
        business_trips = [t for t in trip_list if t.get('purpose') == 'Business']
        business_km = sum(t.get('distance_km', 0) for t in business_trips)

        print(f"Monthly Report for {license_plate} ({month}/{year})")
        print("=" * 50)
        print(f"Total trips: {len(trip_list)}")
        print(f"  - Business: {len(business_trips)}")
        print(f"  - Personal: {len(trip_list) - len(business_trips)}")
        print(f"Total distance: {total_km:.1f} km")
        print(f"  - Business: {business_km:.1f} km")
        print(f"  - Personal: {total_km - business_km:.1f} km")
        print(f"Checkpoints: {len(checkpoint_list)}")
        print("")
        print("Trip Details:")
        for t in trip_list:
            date = t.get('trip_start_datetime', '')[:10]
            dist = t.get('distance_km', 0)
            purpose = t.get('purpose', 'Unknown')
            desc = t.get('business_description', '')[:30] if t.get('business_description') else ''
            print(f"  {date}: {dist:.1f} km [{purpose}] {desc}")
