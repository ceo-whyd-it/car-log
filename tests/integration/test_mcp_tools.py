"""
Integration tests for MCP tools via adapters.
Run with: pytest tests/integration/test_mcp_tools.py -v
Requires: Docker containers running

These tests run OUTSIDE the container and call tools that execute INSIDE.
"""
import pytest
import subprocess
import json


def run_in_container(code: str, timeout: int = 30) -> dict:
    """Run Python code inside the Gradio container and return result."""
    cmd = ['docker', 'exec', 'car-log-gradio', 'python', '-c', code]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }


class TestVehicleTools:

    def test_list_vehicles(self):
        """list_vehicles returns vehicle list."""
        code = '''
import asyncio
import sys
import json
import io
from contextlib import redirect_stdout
sys.path.insert(0, "/app")
from carlog_ui.adapters.car_log_core import CarLogCoreAdapter

async def test():
    # Suppress debug prints by temporarily redirecting stdout during call
    adapter = CarLogCoreAdapter()

    # Capture any debug output
    f = io.StringIO()
    with redirect_stdout(f):
        result = await adapter.call_tool("list_vehicles", {})

    # Print only the JSON result to actual stdout
    print(json.dumps(result.to_dict()))

asyncio.run(test())
'''
        result = run_in_container(code)
        assert result["returncode"] == 0, f"Failed: {result['stderr']}"

        # Parse only the last line which should be the JSON
        lines = result["stdout"].strip().split('\n')
        json_line = lines[-1] if lines else ""
        data = json.loads(json_line)
        assert data.get("success") == True, f"Tool failed: {data}"
        # data contains the full result with 'data' key
        assert "data" in data, f"Missing data: {data}"
        assert "vehicles" in data["data"], f"Missing vehicles: {data}"
        assert isinstance(data["data"]["vehicles"], list)

    def test_create_and_delete_vehicle(self):
        """create_vehicle creates new vehicle, delete removes it."""
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

    # Create - ToolResult has .success, .data, .error
    f = io.StringIO()
    with redirect_stdout(f):
        create_result = await adapter.call_tool("create_vehicle", {
            "name": "Integration Test Car",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "vin": "JTDKN3DU5A0123456",
            "license_plate": "BA-INT99",
            "fuel_type": "Gasoline",
            "fuel_capacity_liters": 50,
            "initial_odometer_km": 10000
        })

    if not create_result.success:
        print(json.dumps({"phase": "create", "error": create_result.error}))
        return

    vehicle_id = create_result.data.get("vehicle_id")

    # Delete
    f = io.StringIO()
    with redirect_stdout(f):
        delete_result = await adapter.call_tool("delete_vehicle", {
            "vehicle_id": vehicle_id
        })

    print(json.dumps({
        "create_success": create_result.success,
        "vehicle_id": vehicle_id,
        "delete_success": delete_result.success
    }))

asyncio.run(test())
'''
        result = run_in_container(code, timeout=60)
        assert result["returncode"] == 0, f"Failed: {result['stderr']}"

        lines = result["stdout"].strip().split('\n')
        json_line = lines[-1] if lines else ""
        data = json.loads(json_line)
        assert data.get("create_success") == True, f"Create failed: {data}"
        assert data.get("vehicle_id") is not None, f"No vehicle_id: {data}"
        assert data.get("delete_success") == True, f"Delete failed: {data}"


class TestCheckpointTools:

    def test_list_checkpoints_for_vehicle(self):
        """list_checkpoints returns checkpoint list for a vehicle."""
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

    # First get a vehicle to list checkpoints for
    f = io.StringIO()
    with redirect_stdout(f):
        vehicles_result = await adapter.call_tool("list_vehicles", {})

    if not vehicles_result.success or not vehicles_result.data.get("vehicles"):
        print(json.dumps({"skip": "no_vehicles"}))
        return

    vehicle_id = vehicles_result.data["vehicles"][0]["vehicle_id"]

    # Now list checkpoints for this vehicle
    f = io.StringIO()
    with redirect_stdout(f):
        result = await adapter.call_tool("list_checkpoints", {"vehicle_id": vehicle_id})

    print(json.dumps(result.to_dict()))

asyncio.run(test())
'''
        result = run_in_container(code)
        assert result["returncode"] == 0, f"Failed: {result['stderr']}"

        lines = result["stdout"].strip().split('\n')
        json_line = lines[-1] if lines else ""
        data = json.loads(json_line)

        # Skip if no vehicles
        if data.get("skip") == "no_vehicles":
            pytest.skip("No vehicles available for testing")

        assert data.get("success") == True, f"Tool failed: {data}"
        assert "checkpoints" in data.get("data", {}), f"Missing checkpoints: {data}"

    def test_create_checkpoint_requires_vehicle(self):
        """create_checkpoint fails without valid vehicle."""
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
    f = io.StringIO()
    with redirect_stdout(f):
        result = await adapter.call_tool("create_checkpoint", {
            "vehicle_id": "nonexistent-id-12345",
            "checkpoint_type": "manual",
            "datetime": "2025-11-29T10:00:00Z",
            "odometer_km": 50000
        })
    print(json.dumps(result.to_dict()))

asyncio.run(test())
'''
        result = run_in_container(code)
        assert result["returncode"] == 0, f"Script failed: {result['stderr']}"

        lines = result["stdout"].strip().split('\n')
        json_line = lines[-1] if lines else ""
        data = json.loads(json_line)
        # Should fail because vehicle doesn't exist
        assert data.get("success") == False, f"Should have failed: {data}"


class TestTripTools:

    def test_list_trips(self):
        """list_trips returns trip list."""
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
    f = io.StringIO()
    with redirect_stdout(f):
        result = await adapter.call_tool("list_trips", {})
    print(json.dumps(result.to_dict()))

asyncio.run(test())
'''
        result = run_in_container(code)
        assert result["returncode"] == 0, f"Failed: {result['stderr']}"

        lines = result["stdout"].strip().split('\n')
        json_line = lines[-1] if lines else ""
        data = json.loads(json_line)
        assert data.get("success") == True, f"Tool failed: {data}"
        assert "trips" in data.get("data", {}), f"Missing trips: {data}"


class TestTemplateTools:

    def test_list_templates(self):
        """list_templates returns template list."""
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
    f = io.StringIO()
    with redirect_stdout(f):
        result = await adapter.call_tool("list_templates", {})
    print(json.dumps(result.to_dict()))

asyncio.run(test())
'''
        result = run_in_container(code)
        assert result["returncode"] == 0, f"Failed: {result['stderr']}"

        lines = result["stdout"].strip().split('\n')
        json_line = lines[-1] if lines else ""
        data = json.loads(json_line)
        assert data.get("success") == True, f"Tool failed: {data}"
        assert "templates" in data.get("data", {}), f"Missing templates: {data}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
