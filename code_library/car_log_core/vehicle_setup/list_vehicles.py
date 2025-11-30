"""
@snippet: list_vehicles
@mcp: car_log_core
@skill: vehicle_setup
@description: List all vehicles in the system
@triggers: list vehicles, show vehicles, get vehicles, show all cars, my vehicles
@returns: List of vehicle dictionaries with id, name, make, model
@version: 1.0
"""
from carlog_ui.adapters.car_log_core import CarLogCoreAdapter

async def run():
    """List all vehicles."""
    adapter = CarLogCoreAdapter()
    result = await adapter.call_tool("list_vehicles", {})

    if not result.success:
        print(f"Error: {result.error}")
        return None

    vehicles = result.data.get("vehicles", [])
    if not vehicles:
        print("No vehicles found.")
        return []

    print(f"Found {len(vehicles)} vehicle(s):")
    for v in vehicles:
        print(f"  - {v.get('name')} ({v.get('make')} {v.get('model')}) - {v.get('license_plate')}")

    return vehicles
