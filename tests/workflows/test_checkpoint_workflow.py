"""
End-to-end checkpoint workflow tests.
Tests: Create Vehicle -> Create Checkpoints -> Detect Gap -> Cleanup

Run with: pytest tests/workflows/test_checkpoint_workflow.py -v
"""
import pytest
import subprocess
import json


def run_in_container(code: str, timeout: int = 60) -> dict:
    """Run Python code inside the Gradio container and return result."""
    cmd = ['docker', 'exec', 'car-log-gradio', 'python', '-c', code]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }


class TestCheckpointWorkflow:

    def test_checkpoint_with_gap_detection(self):
        """Create checkpoints and detect gap between them."""
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

    # 1. Create test vehicle
    f = io.StringIO()
    with redirect_stdout(f):
        vehicle_result = await adapter.call_tool("create_vehicle", {
            "name": "Checkpoint Test Car",
            "make": "VW",
            "model": "Passat",
            "year": 2021,
            "vin": "WVWZZZ3CZNE123456",
            "license_plate": "BA-CHP01",
            "fuel_type": "Diesel",
            "fuel_capacity_liters": 66,
            "initial_odometer_km": 50000
        })

    if not vehicle_result.success:
        print(json.dumps({"phase": "vehicle_create", "error": vehicle_result.error}))
        return

    vehicle_id = vehicle_result.data.get("vehicle_id")
    results["vehicle_created"] = True

    checkpoint_ids = []

    try:
        # 2. Create first checkpoint (start)
        now = datetime.now()
        f = io.StringIO()
        with redirect_stdout(f):
            cp1_result = await adapter.call_tool("create_checkpoint", {
                "vehicle_id": vehicle_id,
                "checkpoint_type": "refuel",
                "datetime": (now - timedelta(days=7)).isoformat(),
                "odometer_km": 50000
            })

        if not cp1_result.success:
            print(json.dumps({"phase": "cp1_create", "error": cp1_result.error}))
            return

        checkpoint_ids.append(cp1_result.data.get("checkpoint_id"))
        results["cp1_created"] = True

        # 3. Create second checkpoint (100km gap)
        f = io.StringIO()
        with redirect_stdout(f):
            cp2_result = await adapter.call_tool("create_checkpoint", {
                "vehicle_id": vehicle_id,
                "checkpoint_type": "refuel",
                "datetime": now.isoformat(),
                "odometer_km": 50100  # 100km driven
            })

        if not cp2_result.success:
            print(json.dumps({"phase": "cp2_create", "error": cp2_result.error}))
            return

        checkpoint_ids.append(cp2_result.data.get("checkpoint_id"))
        results["cp2_created"] = True

        # 4. Verify gap detected
        results["gap_detected"] = cp2_result.data.get("gap_detected", False)
        gap_info = cp2_result.data.get("gap_info", {})
        results["gap_distance_km"] = gap_info.get("distance_km", 0)

        # 5. List checkpoints for vehicle
        f = io.StringIO()
        with redirect_stdout(f):
            list_result = await adapter.call_tool("list_checkpoints", {
                "vehicle_id": vehicle_id
            })

        if list_result.success:
            results["checkpoint_count"] = len(list_result.data.get("checkpoints", []))
        else:
            results["checkpoint_count"] = 0

    finally:
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
        assert data.get("gap_detected") == True, f"Gap not detected: {data}"
        assert data.get("gap_distance_km") == 100, f"Wrong gap distance: {data}"
        assert data.get("checkpoint_count") >= 2, f"Not enough checkpoints: {data}"
        assert data.get("cleanup_done") == True, f"Cleanup failed: {data}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
