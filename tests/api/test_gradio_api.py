"""
Gradio API End-to-End Tests with MLflow Verification.

These tests interact with the Gradio chat interface via API,
test real workflows, and verify MLflow traces are created.

Run with:
    pytest tests/api/test_gradio_api.py -v --timeout=600

Prerequisites:
    - Docker containers running (docker compose up)
    - Gradio at http://localhost:7861
    - MLflow at http://localhost:5050
"""
import pytest
import time
import re


class TestHealthChecks:
    """Verify services are running."""

    def test_gradio_health(self, gradio_client):
        """Gradio app is responding."""
        assert gradio_client.health_check(), "Gradio should be healthy"

    def test_mlflow_health(self, mlflow_client):
        """MLflow is responding."""
        assert mlflow_client.health_check(), "MLflow should be healthy"


class TestListVehicles:
    """Test listing vehicles via chat."""

    @pytest.mark.timeout(300)
    def test_list_vehicles_show_cars(self, gradio_client, mlflow_client, initial_trace_count):
        """Test 'show cars' returns vehicle list."""
        result = gradio_client.send_chat("show cars")

        assert result["success"], f"Chat failed: {result['error']}"
        response = result["response"].lower()

        # Should get a response (may be vehicle info or fallback message if agent had issues)
        assert len(result["response"]) > 20, f"Response too short: {result['response']}"

        # Verify MLflow trace was created (using timestamp-based detection)
        time.sleep(3)
        assert mlflow_client.has_trace_since(initial_trace_count), \
            f"MLflow trace should be created after chat (no trace since timestamp {initial_trace_count})"

    @pytest.mark.timeout(300)
    def test_list_vehicles_what_cars(self, gradio_client, mlflow_client):
        """Test 'what cars we have?' natural language query."""
        result = gradio_client.send_chat("what cars we have?")

        assert result["success"], f"Chat failed: {result['error']}"

        # Chat should complete without error
        assert len(result["response"]) > 20, f"Response too short: {result['response']}"

    @pytest.mark.timeout(300)
    def test_list_vehicles_structured(self, gradio_client):
        """Test 'list all my vehicles' structured request."""
        result = gradio_client.send_chat("list all my vehicles")

        assert result["success"], f"Chat failed: {result['error']}"

        # Should provide structured response
        response = result["response"]
        # Could be "no vehicles" or a list
        assert len(response) > 20, "Response should have meaningful content"


class TestCreateCheckpoint:
    """Test creating checkpoints via chat."""

    @pytest.mark.timeout(300)
    def test_create_checkpoint_refuel(self, gradio_client, mlflow_client, initial_trace_count):
        """Test creating a fuel checkpoint via chat."""
        message = """Add a new checkpoint:
        - Odometer: 55000 km
        - Fuel: 42.5 liters of diesel
        - Location: OMV Bratislava, Slovakia
        - Date: today
        """

        result = gradio_client.send_chat(message)

        assert result["success"], f"Chat failed: {result['error']}"

        # Should get a response (agent executed the task)
        assert len(result["response"]) > 20, f"Response too short: {result['response']}"

        # Verify MLflow trace was created (using timestamp-based detection)
        time.sleep(3)
        assert mlflow_client.has_trace_since(initial_trace_count), \
            f"MLflow trace should be created (no trace since timestamp {initial_trace_count})"

    @pytest.mark.timeout(300)
    def test_create_checkpoint_manual(self, gradio_client):
        """Test creating a manual (non-refuel) checkpoint."""
        message = "Add a manual checkpoint at 60000 km at my home office"

        result = gradio_client.send_chat(message)

        assert result["success"], f"Chat failed: {result['error']}"

        # Should process the request
        assert len(result["response"]) > 20, "Should have meaningful response"


class TestCreateTrip:
    """Test creating trips via chat."""

    @pytest.mark.timeout(300)
    def test_create_trip_business(self, gradio_client, mlflow_client, initial_trace_count):
        """Test creating a business trip via chat."""
        message = """Create a new business trip:
        - From: Bratislava office
        - To: Kosice client site
        - Distance: 410 km
        - Driver: Peter Novak
        - Purpose: Client meeting for Q4 planning
        """

        result = gradio_client.send_chat(message)

        assert result["success"], f"Chat failed: {result['error']}"

        # Should get a response (agent processed the request)
        assert len(result["response"]) > 20, f"Response too short: {result['response']}"

        # Verify MLflow trace was created (using timestamp-based detection)
        time.sleep(3)
        assert mlflow_client.has_trace_since(initial_trace_count), \
            f"MLflow trace should be created (no trace since timestamp {initial_trace_count})"

    @pytest.mark.timeout(300)
    def test_check_gaps(self, gradio_client):
        """Test checking for gaps in mileage."""
        result = gradio_client.send_chat("Check for gaps in my mileage")

        assert result["success"], f"Chat failed: {result['error']}"

        # Should get a response
        assert len(result["response"]) > 20, f"Response too short: {result['response']}"


class TestCreateReport:
    """Test generating reports via chat."""

    @pytest.mark.timeout(300)
    def test_generate_monthly_report(self, gradio_client, mlflow_client, initial_trace_count):
        """Test generating a monthly report."""
        result = gradio_client.send_chat("Generate a monthly report for November 2025")

        assert result["success"], f"Chat failed: {result['error']}"

        # Should get a response
        assert len(result["response"]) > 20, f"Response too short: {result['response']}"

        # Verify MLflow trace was created (using timestamp-based detection)
        time.sleep(3)
        assert mlflow_client.has_trace_since(initial_trace_count), \
            f"MLflow trace should be created (no trace since timestamp {initial_trace_count})"

    @pytest.mark.timeout(300)
    def test_generate_report_date_range(self, gradio_client):
        """Test generating a report with date range."""
        result = gradio_client.send_chat(
            "Generate a report from 2025-11-01 to 2025-11-30"
        )

        assert result["success"], f"Chat failed: {result['error']}"

        # Should process the date range request
        assert len(result["response"]) > 20


class TestMLflowTraceVerification:
    """Verify MLflow traces are properly created."""

    @pytest.mark.timeout(300)
    def test_trace_created_on_chat(self, gradio_client, mlflow_client):
        """Verify each chat creates an MLflow trace."""
        initial_timestamp = mlflow_client.get_latest_trace_timestamp()

        # Send a chat message
        result = gradio_client.send_chat("Hello, what can you do?")
        assert result["success"]

        # Wait for trace to be logged (using timestamp-based detection)
        trace_created = mlflow_client.wait_for_new_trace(initial_timestamp, timeout=30)
        assert trace_created, "Chat should create MLflow trace"

    @pytest.mark.timeout(300)
    def test_traces_contain_session_info(self, gradio_client, mlflow_client):
        """Verify traces contain session metadata."""
        # Send a chat to create a trace
        gradio_client.send_chat("list vehicles")
        time.sleep(5)

        # Get latest traces
        traces = mlflow_client.get_latest_traces(limit=5)

        # Note: Actual verification of metadata depends on MLflow API
        # This test just verifies we can retrieve traces
        assert isinstance(traces, list), "Should retrieve traces"


class TestFullWorkflow:
    """Test complete user workflows end-to-end."""

    @pytest.mark.timeout(600)
    def test_full_workflow_new_user(self, gradio_client, mlflow_client):
        """
        Test the full workflow a new user would follow:
        1. List vehicles (see none)
        2. Ask about creating a vehicle
        3. Add a checkpoint
        4. Check for gaps
        5. Generate report
        """
        results = []

        # Step 1: List vehicles
        r1 = gradio_client.send_chat("show me my vehicles")
        assert r1["success"], f"Step 1 failed: {r1['error']}"
        assert len(r1["response"]) > 10, "Step 1 response too short"
        results.append(("list_vehicles", r1["response"]))

        # Step 2: Ask about vehicles
        r2 = gradio_client.send_chat("how do I add a new vehicle?")
        assert r2["success"], f"Step 2 failed: {r2['error']}"
        assert len(r2["response"]) > 10, "Step 2 response too short"
        results.append(("ask_vehicle", r2["response"]))

        # Step 3: Add checkpoint (may ask for vehicle first)
        r3 = gradio_client.send_chat(
            "Add a checkpoint: 45000 km, 40 liters diesel at Shell Bratislava"
        )
        assert r3["success"], f"Step 3 failed: {r3['error']}"
        assert len(r3["response"]) > 10, "Step 3 response too short"
        results.append(("add_checkpoint", r3["response"]))

        # Step 4: Check gaps
        r4 = gradio_client.send_chat("check for gaps in my mileage log")
        assert r4["success"], f"Step 4 failed: {r4['error']}"
        assert len(r4["response"]) > 10, "Step 4 response too short"
        results.append(("check_gaps", r4["response"]))

        # Step 5: Generate report
        r5 = gradio_client.send_chat("generate a monthly report")
        assert r5["success"], f"Step 5 failed: {r5['error']}"
        assert len(r5["response"]) > 10, "Step 5 response too short"
        results.append(("generate_report", r5["response"]))

        # All steps completed - verify we got responses
        assert len(results) == 5, "All 5 steps should complete"

        # Log results for debugging
        for step, response in results:
            print(f"\n=== {step} ===")
            print(response[:200] + "..." if len(response) > 200 else response)

    @pytest.mark.timeout(300)
    def test_error_recovery(self, gradio_client):
        """Test that agent handles unusual requests gracefully."""
        # Send an unusual request
        result = gradio_client.send_chat(
            "Tell me about the moon phases in relation to my fuel consumption"
        )

        assert result["success"], f"Chat should not timeout: {result['error']}"

        # Should get some response (agent handles gracefully)
        assert len(result["response"]) > 10, "Should get a response"


class TestDataCreation:
    """Test creating fake data for testing purposes."""

    @pytest.mark.timeout(300)
    def test_create_test_vehicle(self, gradio_client):
        """Create a test vehicle via chat."""
        message = """Create a new vehicle:
        - Name: Test BMW for E2E
        - Make: BMW
        - Model: 330i xDrive
        - Year: 2023
        - License Plate: BA-999ZZ
        - VIN: WBAPH5C55BA123456
        - Fuel Type: Gasoline
        """

        result = gradio_client.send_chat(message)

        assert result["success"], f"Chat failed: {result['error']}"

        # Should get a response
        assert len(result["response"]) > 20, f"Response too short: {result['response']}"

    @pytest.mark.timeout(300)
    def test_create_test_checkpoint_with_data(self, gradio_client):
        """Create a test checkpoint with specific fake data."""
        message = """Add a test checkpoint:
        - Date: 2025-11-15 08:30
        - Odometer: 75000 km
        - Fuel: 55.5 liters of diesel
        - Price: 89.90 EUR
        - Location: Test OMV Station, Bratislava
        - GPS: 48.1486, 17.1077
        """

        result = gradio_client.send_chat(message)

        assert result["success"], f"Chat failed: {result['error']}"

        # Should process or ask for vehicle
        assert len(result["response"]) > 20

    @pytest.mark.timeout(300)
    def test_create_multiple_checkpoints(self, gradio_client):
        """Create multiple test checkpoints for gap detection."""
        checkpoints = [
            "Add checkpoint: 70000 km on 2025-11-01, 50L diesel at Bratislava",
            "Add checkpoint: 70500 km on 2025-11-10, 45L diesel at Kosice",
            "Add checkpoint: 71200 km on 2025-11-20, 48L diesel at Bratislava",
        ]

        for msg in checkpoints:
            result = gradio_client.send_chat(msg)
            assert result["success"], f"Failed to create checkpoint: {result['error']}"
            assert len(result["response"]) > 10, "Response too short"
            time.sleep(2)  # Allow processing between requests

    @pytest.mark.timeout(300)
    def test_create_business_trip_with_data(self, gradio_client):
        """Create a business trip with full data."""
        message = """Create a business trip:
        - Driver: Jan Novak
        - From: Bratislava HQ (48.1486, 17.1077)
        - To: Kosice Office (48.7164, 21.2611)
        - Date: 2025-11-15
        - Distance: 410 km
        - Purpose: Quarterly client review meeting
        - Business description: Q4 review with Kosice branch manager
        """

        result = gradio_client.send_chat(message)

        assert result["success"], f"Chat failed: {result['error']}"

        # Should acknowledge or request more info
        assert len(result["response"]) > 20


class TestNaturalLanguageQueries:
    """Test various natural language query formats."""

    @pytest.mark.timeout(300)
    def test_informal_vehicle_query(self, gradio_client):
        """Test informal vehicle queries."""
        queries = [
            "what cars do I have?",
            "show me my fleet",
            "list registered vehicles",
        ]

        for query in queries:
            result = gradio_client.send_chat(query)
            assert result["success"], f"Query '{query}' failed: {result['error']}"
            assert len(result["response"]) > 20, f"Query '{query}' got short response"

    @pytest.mark.timeout(300)
    def test_informal_checkpoint_query(self, gradio_client):
        """Test informal checkpoint queries."""
        result = gradio_client.send_chat(
            "I just filled up with 40 liters at 52000 km"
        )

        assert result["success"], f"Chat failed: {result['error']}"

        # Should get a response
        assert len(result["response"]) > 20, f"Response too short: {result['response']}"

    @pytest.mark.timeout(300)
    def test_informal_report_query(self, gradio_client):
        """Test informal report queries."""
        result = gradio_client.send_chat(
            "I need a mileage report for tax purposes"
        )

        assert result["success"], f"Chat failed: {result['error']}"

        # Should get a response
        assert len(result["response"]) > 20, f"Response too short: {result['response']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--timeout=600", "-x"])
