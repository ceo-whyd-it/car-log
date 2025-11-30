"""
@snippet: list_checkpoints
@mcp: car_log_core
@skill: checkpoint
@description: List checkpoints for a vehicle
@triggers: list checkpoints, show checkpoints, get checkpoints, view refuels, show stops
@params: vehicle_id
@returns: List of checkpoint dictionaries with datetime, odometer, type
@version: 1.0
"""
from carlog_ui.adapters.car_log_core import CarLogCoreAdapter

async def run(vehicle_id: str):
    """
    List all checkpoints for a vehicle.

    Args:
        vehicle_id: UUID of the vehicle
    """
    adapter = CarLogCoreAdapter()

    result = await adapter.call_tool("list_checkpoints", {
        "vehicle_id": vehicle_id
    })

    if not result.success:
        print(f"Error: {result.error}")
        return None

    checkpoints = result.data.get("checkpoints", [])
    if not checkpoints:
        print(f"No checkpoints found for vehicle {vehicle_id}")
        return []

    print(f"Found {len(checkpoints)} checkpoint(s):")
    for cp in checkpoints:
        dt = cp.get("datetime", "")[:16]  # Truncate to YYYY-MM-DD HH:MM
        odometer = cp.get("odometer_km", 0)
        cp_type = cp.get("checkpoint_type", "manual")
        print(f"  - {dt} | {odometer:,.0f} km | {cp_type}")

    return checkpoints
