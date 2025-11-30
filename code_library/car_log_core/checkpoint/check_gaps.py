"""
@snippet: check_gaps
@mcp: car_log_core
@skill: checkpoint
@description: Check for gaps in mileage checkpoints
@triggers: check gaps, find gaps, detect gaps, gaps in mileage, missing trips
@params: vehicle_id
@returns: list of detected gaps
@version: 1.1

NOTE: This code is executed in the agent's code execution environment.
Adapters are available as globals: car_log_core, report_generator, etc.
DO NOT import adapters - use them directly.
"""

# Example usage - finding gaps for a vehicle by license plate:
# license_plate = "BA-TEST01"

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

    # Step 2: Get all checkpoints
    result = await car_log_core.list_checkpoints(vehicle_id=vehicle_id, limit=100)
    checkpoints = result.get('checkpoints', [])

    if len(checkpoints) < 2:
        print(f"Need at least 2 checkpoints to detect gaps. Found: {len(checkpoints)}")
    else:
        # Sort by datetime
        checkpoints.sort(key=lambda c: c.get('datetime', ''))

        gaps = []
        for i in range(len(checkpoints) - 1):
            cp1 = checkpoints[i]
            cp2 = checkpoints[i + 1]

            # Call detect_gap tool
            gap_result = await car_log_core.detect_gap(
                checkpoint1_id=cp1['checkpoint_id'],
                checkpoint2_id=cp2['checkpoint_id']
            )

            if gap_result.get('gap_detected'):
                gap_info = gap_result.get('gap_info', {})
                gaps.append({
                    'from': cp1.get('datetime', '')[:10],
                    'to': cp2.get('datetime', '')[:10],
                    'distance_km': gap_info.get('distance_km', 0),
                    'from_odometer': cp1.get('odometer_km', 0),
                    'to_odometer': cp2.get('odometer_km', 0)
                })

        if gaps:
            print(f"Found {len(gaps)} gap(s) for vehicle {license_plate}:")
            for i, gap in enumerate(gaps, 1):
                print(f"  {i}. {gap['from']} to {gap['to']}: {gap['distance_km']:.1f} km")
                print(f"     Odometer: {gap['from_odometer']} -> {gap['to_odometer']} km")
        else:
            print(f"No gaps detected for vehicle {license_plate}")
