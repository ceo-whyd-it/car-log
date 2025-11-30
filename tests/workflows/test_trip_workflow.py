"""
End-to-end trip workflow tests.
Tests: Create Vehicle -> Create Checkpoints -> Create Trip -> List Trips -> Cleanup

Run with: pytest tests/workflows/test_trip_workflow.py -v
"""
import pytest
import subprocess
import json


def run_in_container(code: str, timeout: int = 90) -> dict:
    """Run Python code inside the Gradio container and return result."""
    cmd = ['docker', 'exec', 'car-log-gradio', 'python', '-c', code]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }


class TestTripWorkflow:

    def test_create_trip_manually(self):
        """Create trip with start/end checkpoints."""
        code = '''
import asyncio
import sys
import json
import io
from datetime import datetime, timedelta
from contextlib import redirect_stdout
sys.path.insert(0, "/app")
from carlog_ui.adapters.car_log_core import CarLogCoreAdapter

async def test():
    adapter = CarLogCoreAdapter()
    results = {}

    # Setup: Create vehicle
    f = io.StringIO()
    with redirect_stdout(f):
        vehicle = await adapter.call_tool("create_vehicle", {
            "name": "Trip Test Car",
            "make": "Ford",
            "model": "Focus",
            "year": 2020,
            "vin": "WF0XXXGCDXLA12345",
            "license_plate": "BA-TRP01",
            "fuel_type": "Gasoline",
            "fuel_capacity_liters": 52,
            "initial_odometer_km": 30000
        })

    if not vehicle.success:
        print(json.dumps({"phase": "vehicle_create", "error": vehicle.error}))
        return

    vehicle_id = vehicle.data.get("vehicle_id")
    results["vehicle_created"] = True

    now = datetime.now()
    checkpoint_ids = []
    trip_id = None

    try:
        # Create checkpoint 1
        f = io.StringIO()
        with redirect_stdout(f):
            cp1 = await adapter.call_tool("create_checkpoint", {
                "vehicle_id": vehicle_id,
                "checkpoint_type": "manual",
                "datetime": (now - timedelta(hours=2)).isoformat(),
                "odometer_km": 30000
            })

        if not cp1.success:
            print(json.dumps({"phase": "cp1_create", "error": cp1.error}))
            return

        checkpoint_ids.append(cp1.data.get("checkpoint_id"))
        results["cp1_created"] = True

        # Create checkpoint 2
        f = io.StringIO()
        with redirect_stdout(f):
            cp2 = await adapter.call_tool("create_checkpoint", {
                "vehicle_id": vehicle_id,
                "checkpoint_type": "manual",
                "datetime": now.isoformat(),
                "odometer_km": 30050
            })

        if not cp2.success:
            print(json.dumps({"phase": "cp2_create", "error": cp2.error}))
            return

        checkpoint_ids.append(cp2.data.get("checkpoint_id"))
        results["cp2_created"] = True

        # Create trip
        f = io.StringIO()
        with redirect_stdout(f):
            trip_result = await adapter.call_tool("create_trip", {
                "vehicle_id": vehicle_id,
                "start_checkpoint_id": cp1.data.get("checkpoint_id"),
                "end_checkpoint_id": cp2.data.get("checkpoint_id"),
                "driver_name": "Test Driver",
                "trip_start_datetime": (now - timedelta(hours=2)).isoformat(),
                "trip_end_datetime": now.isoformat(),
                "trip_start_location": "Bratislava",
                "trip_end_location": "Trnava",
                "distance_km": 50,
                "purpose": "Business",
                "business_description": "Client meeting"
            })

        if not trip_result.success:
            print(json.dumps({"phase": "trip_create", "error": trip_result.error}))
            return

        trip_id = trip_result.data.get("trip_id")
        results["trip_created"] = True
        results["trip_id"] = trip_id

        # List trips
        f = io.StringIO()
        with redirect_stdout(f):
            list_result = await adapter.call_tool("list_trips", {
                "vehicle_id": vehicle_id
            })

        if list_result.success:
            trip_ids = [t.get("trip_id") for t in list_result.data.get("trips", [])]
            results["trip_in_list"] = trip_id in trip_ids
        else:
            results["trip_in_list"] = False

    finally:
        # Cleanup trip
        if trip_id:
            f = io.StringIO()
            with redirect_stdout(f):
                await adapter.call_tool("delete_trip", {"trip_id": trip_id})

        # Cleanup checkpoints
        for cp_id in checkpoint_ids:
            f = io.StringIO()
            with redirect_stdout(f):
                await adapter.call_tool("delete_checkpoint", {"checkpoint_id": cp_id})

        # Cleanup vehicle
        f = io.StringIO()
        with redirect_stdout(f):
            await adapter.call_tool("delete_vehicle", {"vehicle_id": vehicle_id})

        results["cleanup_done"] = True

    print(json.dumps(results))

asyncio.run(test())
'''
        result = run_in_container(code)
        assert result["returncode"] == 0, f"Script failed: {result['stderr']}"

        lines = result["stdout"].strip().split('\n')
        json_line = lines[-1] if lines else ""
        data = json.loads(json_line)

        # Verify workflow
        assert data.get("vehicle_created") == True, f"Vehicle creation failed: {data}"
        assert data.get("cp1_created") == True, f"CP1 creation failed: {data}"
        assert data.get("cp2_created") == True, f"CP2 creation failed: {data}"
        assert data.get("trip_created") == True, f"Trip creation failed: {data}"
        assert data.get("trip_id") is not None, f"No trip_id: {data}"
        assert data.get("trip_in_list") == True, f"Trip not in list: {data}"
        assert data.get("cleanup_done") == True, f"Cleanup failed: {data}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
