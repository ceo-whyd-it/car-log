"""
Test MCP server connectivity from within Gradio container.
Run with: pytest tests/docker/test_mcp_connectivity.py -v
"""
import pytest
import subprocess
import requests


class TestMCPConnectivity:

    def test_car_log_core_responds(self):
        """car-log-core MCP must handle list_vehicles."""
        # Execute inside container - ToolResult is a dataclass with .success, .data
        cmd = ['docker', 'exec', 'car-log-gradio', 'python', '-c', '''
import asyncio
import sys
sys.path.insert(0, '/app')
from carlog_ui.adapters.car_log_core import CarLogCoreAdapter

async def test():
    adapter = CarLogCoreAdapter()
    result = await adapter.call_tool('list_vehicles', {})
    # ToolResult is a dataclass with .success, .data properties
    print('SUCCESS' if result.success else 'FAILED')
    return result.success

asyncio.run(test())
''']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        assert "SUCCESS" in result.stdout, f"MCP list_vehicles failed.\nStdout: {result.stdout}\nStderr: {result.stderr}"

    def test_geo_routing_geocode_responds(self):
        """geo-routing HTTP server must handle geocode."""
        try:
            # Correct endpoint: /tools/geocode_address
            response = requests.post(
                "http://localhost:8002/tools/geocode_address",
                json={"address": "Bratislava, Slovakia"},
                timeout=30
            )
            assert response.status_code == 200, f"Geocode returned status {response.status_code}"
            data = response.json()
            # Check for coordinates in response
            has_coords = "coordinates" in data or "latitude" in data
            assert has_coords, f"Geocode response missing coordinates: {data}"
        except requests.exceptions.ConnectionError as e:
            pytest.fail(f"Cannot connect to geo-routing: {e}")
        except requests.exceptions.Timeout:
            pytest.fail("Geocode request timed out")

    def test_geo_routing_route_responds(self):
        """geo-routing HTTP server must handle route calculation."""
        try:
            # Correct endpoint: /tools/calculate_route with from_coords/to_coords
            response = requests.post(
                "http://localhost:8002/tools/calculate_route",
                json={
                    "from_coords": {"lat": 48.1486, "lng": 17.1077},  # Bratislava
                    "to_coords": {"lat": 48.7164, "lng": 21.2611}     # Kosice
                },
                timeout=30
            )
            assert response.status_code == 200, f"Route returned status {response.status_code}"
            data = response.json()
            # Should have routes in response
            assert "routes" in data or "success" in data, f"Route response: {data}"
        except requests.exceptions.ConnectionError as e:
            pytest.fail(f"Cannot connect to geo-routing: {e}")
        except requests.exceptions.Timeout:
            pytest.fail("Route request timed out")

    def test_car_log_core_create_and_delete_vehicle(self):
        """car-log-core MCP must handle vehicle CRUD operations."""
        # Execute inside container - create and delete test vehicle
        cmd = ['docker', 'exec', 'car-log-gradio', 'python', '-c', '''
import asyncio
import sys
sys.path.insert(0, '/app')
from carlog_ui.adapters.car_log_core import CarLogCoreAdapter

async def test():
    adapter = CarLogCoreAdapter()

    # Create test vehicle - ToolResult has .success, .data
    create_result = await adapter.call_tool('create_vehicle', {
        'name': 'MCP Test Vehicle',
        'make': 'Test',
        'model': 'Connectivity',
        'year': 2024,
        'vin': 'TESTMCP1234567890',
        'license_plate': 'BA-MCP99',
        'fuel_type': 'Diesel',
        'fuel_capacity_liters': 50,
        'initial_odometer_km': 1000
    })

    if not create_result.success:
        print(f'CREATE_FAILED: {create_result.error}')
        return False

    vehicle_id = create_result.data.get('vehicle_id')
    print(f'CREATED: {vehicle_id}')

    # Delete test vehicle
    delete_result = await adapter.call_tool('delete_vehicle', {
        'vehicle_id': vehicle_id
    })

    if delete_result.success:
        print('DELETED: SUCCESS')
        return True
    else:
        print(f'DELETE_FAILED: {delete_result.error}')
        return False

asyncio.run(test())
''']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        assert "CREATED:" in result.stdout, f"Vehicle creation failed.\nStdout: {result.stdout}\nStderr: {result.stderr}"
        assert "DELETED: SUCCESS" in result.stdout, f"Vehicle deletion failed.\nStdout: {result.stdout}\nStderr: {result.stderr}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
