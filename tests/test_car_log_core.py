"""
Unit tests for car-log-core MCP server.

Tests all CRUD operations and validates Slovak compliance requirements.
"""

import asyncio
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-servers"))

from car_log_core.tools import (
    create_vehicle,
    get_vehicle,
    list_vehicles,
    update_vehicle,
    create_checkpoint,
    get_checkpoint,
    list_checkpoints,
    detect_gap,
    create_template,
    list_templates,
)


class TestCarLogCore:
    """Test suite for car-log-core MCP server."""

    def __init__(self):
        # Create temporary data directory
        self.temp_dir = tempfile.mkdtemp(prefix="car_log_test_")
        os.environ["DATA_PATH"] = self.temp_dir
        print(f"Test data directory: {self.temp_dir}")

    def cleanup(self):
        """Clean up test data directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        print(f"Cleaned up test directory: {self.temp_dir}")

    async def test_vehicle_crud(self):
        """Test vehicle CRUD operations."""
        print("\n=== Testing Vehicle CRUD ===")

        # Test 1: Create vehicle with valid data
        print("\n1. Create vehicle with valid VIN...")
        result = await create_vehicle.execute({
            "name": "Ford Transit Delivery Van",
            "license_plate": "BA-456CD",
            "vin": "WBAXX01234ABC5678",
            "make": "Ford",
            "model": "Transit",
            "year": 2022,
            "fuel_type": "Diesel",
            "initial_odometer_km": 15000,
        })
        assert result["success"], f"Failed: {result.get('error')}"
        vehicle_id = result["vehicle_id"]
        print(f"✓ Vehicle created: {vehicle_id}")

        # Test 2: Create vehicle with invalid VIN (contains I)
        print("\n2. Create vehicle with invalid VIN (contains I)...")
        result = await create_vehicle.execute({
            "name": "Test Vehicle",
            "license_plate": "BA-123CD",
            "vin": "WBAXX01234ABCI678",  # Invalid: contains I
            "fuel_type": "Diesel",
            "initial_odometer_km": 0,
        })
        assert not result["success"], "Should have failed with invalid VIN"
        assert result["error"]["code"] == "VALIDATION_ERROR"
        print(f"✓ Correctly rejected invalid VIN: {result['error']['message']}")

        # Test 3: Create vehicle with invalid license plate
        print("\n3. Create vehicle with invalid license plate...")
        result = await create_vehicle.execute({
            "name": "Test Vehicle",
            "license_plate": "INVALID",
            "vin": "WBAXX01234ABC5678",
            "fuel_type": "Diesel",
            "initial_odometer_km": 0,
        })
        assert not result["success"], "Should have failed with invalid plate"
        print(f"✓ Correctly rejected invalid plate: {result['error']['message']}")

        # Test 4: Get vehicle by ID
        print("\n4. Get vehicle by ID...")
        result = await get_vehicle.execute({"vehicle_id": vehicle_id})
        assert result["success"], f"Failed: {result.get('error')}"
        assert result["vehicle"]["vin"] == "WBAXX01234ABC5678"
        print(f"✓ Retrieved vehicle: {result['vehicle']['name']}")

        # Test 5: List vehicles
        print("\n5. List all vehicles...")
        result = await list_vehicles.execute({})
        assert result["success"], f"Failed: {result.get('error')}"
        assert result["count"] >= 1
        print(f"✓ Found {result['count']} vehicle(s)")

        # Test 6: Update vehicle
        print("\n6. Update vehicle efficiency...")
        result = await update_vehicle.execute({
            "vehicle_id": vehicle_id,
            "average_efficiency_l_per_100km": 8.5,
        })
        assert result["success"], f"Failed: {result.get('error')}"
        assert result["vehicle"]["average_efficiency_l_per_100km"] == 8.5
        print("✓ Updated efficiency to 8.5 L/100km")

        print("\n✓ All vehicle CRUD tests passed!")
        return vehicle_id

    async def test_checkpoint_crud(self, vehicle_id: str):
        """Test checkpoint CRUD operations."""
        print("\n=== Testing Checkpoint CRUD ===")

        # Test 1: Create refuel checkpoint
        print("\n1. Create refuel checkpoint...")
        result = await create_checkpoint.execute({
            "vehicle_id": vehicle_id,
            "checkpoint_type": "refuel",
            "datetime": "2025-11-15T08:45:00Z",
            "odometer_km": 15200,
            "odometer_source": "manual",
            "location_coords": {
                "lat": 48.1486,
                "lng": 17.1077,
            },
            "location_address": "Shell Bratislava West, Hlavná 12",
            "receipt_id": "ekasa-abc123xyz",
            "fuel_liters": 50.5,
            "fuel_cost_eur": 72.50,
        })
        assert result["success"], f"Failed: {result.get('error')}"
        checkpoint1_id = result["checkpoint_id"]
        print(f"✓ Checkpoint 1 created: {checkpoint1_id}")

        # Test 2: Create second checkpoint (should detect gap)
        print("\n2. Create second checkpoint (gap detection)...")
        result = await create_checkpoint.execute({
            "vehicle_id": vehicle_id,
            "checkpoint_type": "refuel",
            "datetime": "2025-11-18T14:30:00Z",
            "odometer_km": 15650,  # 450km gap
            "odometer_source": "manual",
            "location_coords": {
                "lat": 48.7164,
                "lng": 21.2611,
            },
        })
        assert result["success"], f"Failed: {result.get('error')}"
        checkpoint2_id = result["checkpoint_id"]
        assert result["gap_detected"], "Should have detected gap (450km)"
        print(f"✓ Checkpoint 2 created: {checkpoint2_id}")
        print(f"  Gap detected: {result['gap_info']['distance_km']} km over {result['gap_info']['time_period_days']:.1f} days")

        # Test 3: Get checkpoint
        print("\n3. Get checkpoint by ID...")
        result = await get_checkpoint.execute({"checkpoint_id": checkpoint1_id})
        assert result["success"], f"Failed: {result.get('error')}"
        assert result["checkpoint"]["odometer_km"] == 15200
        print(f"✓ Retrieved checkpoint: {result['checkpoint']['odometer_km']} km")

        # Test 4: List checkpoints
        print("\n4. List checkpoints for vehicle...")
        result = await list_checkpoints.execute({"vehicle_id": vehicle_id})
        assert result["success"], f"Failed: {result.get('error')}"
        assert result["count"] >= 2
        print(f"✓ Found {result['count']} checkpoint(s)")

        # Test 5: List checkpoints by date range
        print("\n5. List checkpoints by date range...")
        result = await list_checkpoints.execute({
            "vehicle_id": vehicle_id,
            "start_date": "2025-11-15",
            "end_date": "2025-11-18",
        })
        assert result["success"], f"Failed: {result.get('error')}"
        print(f"✓ Found {result['count']} checkpoint(s) in date range")

        # Test 6: List checkpoints by type
        print("\n6. List refuel checkpoints only...")
        result = await list_checkpoints.execute({
            "vehicle_id": vehicle_id,
            "checkpoint_type": "refuel",
        })
        assert result["success"], f"Failed: {result.get('error')}"
        print(f"✓ Found {result['count']} refuel checkpoint(s)")

        print("\n✓ All checkpoint CRUD tests passed!")
        return checkpoint1_id, checkpoint2_id

    async def test_gap_detection(self, checkpoint1_id: str, checkpoint2_id: str):
        """Test gap detection."""
        print("\n=== Testing Gap Detection ===")

        print("\n1. Detect gap between checkpoints...")
        result = await detect_gap.execute({
            "start_checkpoint_id": checkpoint1_id,
            "end_checkpoint_id": checkpoint2_id,
        })
        assert result["success"], f"Failed: {result.get('error')}"
        assert result["distance_km"] == 450
        assert result["has_gps"] is True
        assert result["reconstruction_recommended"] is True
        print("✓ Gap detected:")
        print(f"  Distance: {result['distance_km']} km")
        print(f"  Time: {result['days']} days ({result['hours']} hours)")
        print(f"  Avg: {result['avg_km_per_day']} km/day")
        print(f"  Has GPS: {result['has_gps']}")
        print(f"  Reconstruction recommended: {result['reconstruction_recommended']}")

        print("\n✓ Gap detection tests passed!")

    async def test_template_crud(self):
        """Test template CRUD operations."""
        print("\n=== Testing Template CRUD ===")

        # Test 1: Create template with GPS (mandatory)
        print("\n1. Create template with GPS coordinates...")
        result = await create_template.execute({
            "name": "Warehouse Run",
            "from_coords": {"lat": 48.1486, "lng": 17.1077},
            "to_coords": {"lat": 48.7164, "lng": 21.2611},
            "from_address": "Main Office, Bratislava",
            "to_address": "Warehouse, Košice",
            "distance_km": 410,
            "is_round_trip": True,
            "typical_days": ["Monday", "Thursday"],
            "purpose": "business",
            "business_description": "Warehouse pickup",
        })
        assert result["success"], f"Failed: {result.get('error')}"
        template_id = result["template_id"]
        print(f"✓ Template created: {template_id}")

        # Test 2: Create template without GPS (should fail)
        print("\n2. Create template without GPS (should fail)...")
        result = await create_template.execute({
            "name": "Invalid Template",
            "from_address": "Bratislava",
            "to_address": "Košice",
        })
        assert not result["success"], "Should have failed without GPS coordinates"
        assert result["error"]["code"] == "VALIDATION_ERROR"
        print(f"✓ Correctly rejected template without GPS: {result['error']['message']}")

        # Test 3: Create template with duplicate name
        print("\n3. Create template with duplicate name...")
        result = await create_template.execute({
            "name": "Warehouse Run",  # Duplicate
            "from_coords": {"lat": 48.0, "lng": 17.0},
            "to_coords": {"lat": 48.5, "lng": 21.0},
        })
        assert not result["success"], "Should have failed with duplicate name"
        assert result["error"]["code"] == "DUPLICATE"
        print("✓ Correctly rejected duplicate template name")

        # Test 4: List all templates
        print("\n4. List all templates...")
        result = await list_templates.execute({})
        assert result["success"], f"Failed: {result.get('error')}"
        assert result["count"] >= 1
        print(f"✓ Found {result['count']} template(s)")

        # Test 5: List business templates only
        print("\n5. List business templates only...")
        result = await list_templates.execute({"purpose": "business"})
        assert result["success"], f"Failed: {result.get('error')}"
        print(f"✓ Found {result['count']} business template(s)")

        print("\n✓ All template CRUD tests passed!")

    async def test_atomic_write(self):
        """Test atomic write pattern."""
        print("\n=== Testing Atomic Write Pattern ===")

        from car_log_core.storage import atomic_write_json, read_json

        print("\n1. Test atomic write...")
        test_file = Path(self.temp_dir) / "test_atomic.json"
        test_data = {"test": "data", "number": 123}

        atomic_write_json(test_file, test_data)
        assert test_file.exists(), "File should exist after atomic write"

        # Verify no .tmp files left behind
        tmp_files = list(Path(self.temp_dir).glob("*.tmp"))
        assert len(tmp_files) == 0, "No temp files should remain"
        print("✓ Atomic write completed, no temp files remain")

        # Verify content
        loaded_data = read_json(test_file)
        assert loaded_data == test_data, "Data should match"
        print("✓ Data written and read correctly")

        print("\n✓ Atomic write tests passed!")

    async def run_all_tests(self):
        """Run all tests."""
        print("=" * 60)
        print("CAR-LOG-CORE MCP SERVER - UNIT TESTS")
        print("=" * 60)

        try:
            # Test atomic write first
            await self.test_atomic_write()

            # Test vehicle CRUD
            vehicle_id = await self.test_vehicle_crud()

            # Test checkpoint CRUD
            checkpoint1_id, checkpoint2_id = await self.test_checkpoint_crud(vehicle_id)

            # Test gap detection
            await self.test_gap_detection(checkpoint1_id, checkpoint2_id)

            # Test template CRUD
            await self.test_template_crud()

            print("\n" + "=" * 60)
            print("✓ ALL TESTS PASSED!")
            print("=" * 60)

        except AssertionError as e:
            print(f"\n✗ TEST FAILED: {e}")
            raise
        except Exception as e:
            print(f"\n✗ UNEXPECTED ERROR: {e}")
            raise
        finally:
            self.cleanup()


async def main():
    """Run test suite."""
    tester = TestCarLogCore()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
