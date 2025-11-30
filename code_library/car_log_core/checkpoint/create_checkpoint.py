"""
@snippet: create_checkpoint
@mcp: car_log_core
@skill: checkpoint
@description: Create a new checkpoint (refuel or manual stop)
@triggers: create checkpoint, add checkpoint, record refuel, log fuel stop, add odometer reading
@params: vehicle_id, checkpoint_type, datetime, odometer_km
@returns: checkpoint_id with gap detection info
@version: 1.0
"""
from datetime import datetime as dt
from carlog_ui.adapters.car_log_core import CarLogCoreAdapter

async def run(
    vehicle_id: str,
    checkpoint_type: str = "manual",
    checkpoint_datetime: str = None,
    odometer_km: float = None
):
    """
    Create a new checkpoint.

    Args:
        vehicle_id: UUID of the vehicle
        checkpoint_type: "refuel" or "manual"
        checkpoint_datetime: ISO 8601 datetime string (defaults to now)
        odometer_km: Current odometer reading in km
    """
    adapter = CarLogCoreAdapter()

    # Default to current time if not specified
    if checkpoint_datetime is None:
        checkpoint_datetime = dt.now().isoformat()

    params = {
        "vehicle_id": vehicle_id,
        "checkpoint_type": checkpoint_type,
        "datetime": checkpoint_datetime,
        "odometer_km": odometer_km
    }

    result = await adapter.call_tool("create_checkpoint", params)

    if not result.success:
        print(f"Error creating checkpoint: {result.error}")
        return None

    checkpoint_id = result.data.get("checkpoint_id")
    gap_detected = result.data.get("gap_detected", False)

    print(f"Checkpoint created successfully!")
    print(f"  ID: {checkpoint_id}")
    print(f"  Type: {checkpoint_type}")
    print(f"  Odometer: {odometer_km:,.0f} km")

    if gap_detected:
        gap_info = result.data.get("gap_info", {})
        gap_km = gap_info.get("distance_km", 0)
        print(f"  Gap detected: {gap_km:,.0f} km since last checkpoint")

    return {
        "checkpoint_id": checkpoint_id,
        "gap_detected": gap_detected,
        "gap_info": result.data.get("gap_info")
    }
