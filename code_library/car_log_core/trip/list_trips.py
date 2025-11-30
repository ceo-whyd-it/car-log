"""
@snippet: list_trips
@mcp: car_log_core
@skill: trip
@description: List trips for a vehicle
@triggers: list trips, show trips, get trips, view journeys, show drives
@params: vehicle_id
@returns: List of trip dictionaries with dates, locations, distance
@version: 1.0
"""
from carlog_ui.adapters.car_log_core import CarLogCoreAdapter

async def run(vehicle_id: str):
    """
    List all trips for a vehicle.

    Args:
        vehicle_id: UUID of the vehicle
    """
    adapter = CarLogCoreAdapter()

    result = await adapter.call_tool("list_trips", {
        "vehicle_id": vehicle_id
    })

    if not result.success:
        print(f"Error: {result.error}")
        return None

    trips = result.data.get("trips", [])
    if not trips:
        print(f"No trips found for vehicle {vehicle_id}")
        return []

    total_km = sum(t.get("distance_km", 0) for t in trips)

    print(f"Found {len(trips)} trip(s) totaling {total_km:,.0f} km:")
    for trip in trips:
        start_date = trip.get("trip_start_datetime", "")[:10]
        from_loc = trip.get("trip_start_location", "?")
        to_loc = trip.get("trip_end_location", "?")
        distance = trip.get("distance_km", 0)
        purpose = trip.get("purpose", "")
        print(f"  - {start_date} | {from_loc} -> {to_loc} | {distance:,.0f} km | {purpose}")

    return trips
