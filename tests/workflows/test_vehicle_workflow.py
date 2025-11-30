"""
End-to-end vehicle workflow tests.
Tests: Create -> Get -> Update -> List -> Delete

Run with: pytest tests/workflows/test_vehicle_workflow.py -v
"""
import pytest
import subprocess
import json
import io
from contextlib import redirect_stdout


def run_in_container(code: str, timeout: int = 60) -> dict:
    """Run Python code inside the Gradio container and return result."""
    cmd = ['docker', 'exec', 'car-log-gradio', 'python', '-c', code]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }


class TestVehicleWorkflow:
    """Complete vehicle lifecycle test."""

    def test_full_vehicle_lifecycle(self):
        """Create, read, update, list, delete vehicle."""
        code = '''
import asyncio
import sys
import json
import io
from contextlib import redirect_stdout
sys.path.insert(0, "/app")
from carlog_ui.adapters.car_log_core import CarLogCoreAdapter

async def test():
    adapter = CarLogCoreAdapter()
    results = {}

    # 1. CREATE
    f = io.StringIO()
    with redirect_stdout(f):
        create_result = await adapter.call_tool("create_vehicle", {
            "name": "Workflow Test Car",
            "make": "Skoda",
            "model": "Octavia",
            "year": 2022,
            "vin": "TMBAJ7NE1N0123456",
            "license_plate": "BA-WRK01",
            "fuel_type": "Diesel",
            "fuel_capacity_liters": 55,
            "initial_odometer_km": 25000
        })

    if not create_result.success:
        print(json.dumps({"phase": "create", "error": create_result.error}))
        return

    vehicle_id = create_result.data.get("vehicle_id")
    results["create_success"] = True
    results["vehicle_id"] = vehicle_id

    try:
        # 2. GET - Verify created
        f = io.StringIO()
        with redirect_stdout(f):
            get_result = await adapter.call_tool("get_vehicle", {"vehicle_id": vehicle_id})

        if not get_result.success:
            print(json.dumps({"phase": "get", "error": get_result.error}))
            return

        results["get_success"] = True
        results["get_name"] = get_result.data.get("vehicle", {}).get("name")
        results["get_plate"] = get_result.data.get("vehicle", {}).get("license_plate")

        # 3. UPDATE
        f = io.StringIO()
        with redirect_stdout(f):
            update_result = await adapter.call_tool("update_vehicle", {
                "vehicle_id": vehicle_id,
                "current_odometer_km": 26000
            })

        results["update_success"] = update_result.success

        # 4. LIST - Verify in list
        f = io.StringIO()
        with redirect_stdout(f):
            list_result = await adapter.call_tool("list_vehicles", {})

        if list_result.success:
            vehicle_ids = [v["vehicle_id"] for v in list_result.data.get("vehicles", [])]
            results["in_list"] = vehicle_id in vehicle_ids
        else:
            results["in_list"] = False

    finally:
        # 5. DELETE - Cleanup
        f = io.StringIO()
        with redirect_stdout(f):
            delete_result = await adapter.call_tool("delete_vehicle", {"vehicle_id": vehicle_id})

        results["delete_success"] = delete_result.success

        # Verify deleted
        f = io.StringIO()
        with redirect_stdout(f):
            list_after = await adapter.call_tool("list_vehicles", {})

        if list_after.success:
            vehicle_ids_after = [v["vehicle_id"] for v in list_after.data.get("vehicles", [])]
            results["removed_from_list"] = vehicle_id not in vehicle_ids_after
        else:
            results["removed_from_list"] = False

    print(json.dumps(results))

asyncio.run(test())
'''
        result = run_in_container(code)
        assert result["returncode"] == 0, f"Script failed: {result['stderr']}"

        lines = result["stdout"].strip().split('\n')
        json_line = lines[-1] if lines else ""
        data = json.loads(json_line)

        # Verify all phases
        assert data.get("create_success") == True, f"Create failed: {data}"
        assert data.get("vehicle_id") is not None, f"No vehicle_id: {data}"
        assert data.get("get_success") == True, f"Get failed: {data}"
        assert data.get("get_name") == "Workflow Test Car", f"Wrong name: {data}"
        assert data.get("get_plate") == "BA-WRK01", f"Wrong plate: {data}"
        assert data.get("update_success") == True, f"Update failed: {data}"
        assert data.get("in_list") == True, f"Vehicle not in list: {data}"
        assert data.get("delete_success") == True, f"Delete failed: {data}"
        assert data.get("removed_from_list") == True, f"Vehicle still in list: {data}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
