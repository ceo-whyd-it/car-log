"""
Fixtures for Gradio API E2E tests.
"""
import pytest
import requests
import time
from typing import Optional
from dataclasses import dataclass


GRADIO_URL = "http://localhost:7861"
MLFLOW_URL = "http://localhost:5050"
CHAT_TIMEOUT = 300  # 5 minutes for LLM responses


@dataclass
class GradioClient:
    """Simple Gradio API client for testing (Gradio 5.x compatible)."""

    base_url: str = GRADIO_URL
    timeout: int = CHAT_TIMEOUT

    def send_chat(self, message: str, history: list = None) -> dict:
        """
        Send a chat message via Gradio API.

        Gradio 5.x uses SSE-based API:
        1. POST /call/{api_name} -> returns event_id
        2. GET /call/{api_name}/{event_id} -> returns SSE stream with result

        Returns dict with:
            - response: str - The assistant's response
            - success: bool - Whether the call succeeded
            - error: Optional[str] - Error message if failed
        """
        history = history or []

        # Gradio 5.x API format - use on_send endpoint with /gradio_api prefix
        api_name = "on_send"
        api_prefix = "/gradio_api"

        try:
            # Step 1: Initiate the call
            init_response = requests.post(
                f"{self.base_url}{api_prefix}/call/{api_name}",
                json={"data": [message, history]},
                timeout=30,
            )

            if init_response.status_code != 200:
                return {
                    "response": "",
                    "success": False,
                    "error": f"Init failed: {init_response.status_code} - {init_response.text[:200]}",
                }

            event_id = init_response.json().get("event_id")
            if not event_id:
                return {
                    "response": "",
                    "success": False,
                    "error": "No event_id in response",
                }

            # Step 2: Get result via SSE stream
            result_response = requests.get(
                f"{self.base_url}{api_prefix}/call/{api_name}/{event_id}",
                stream=True,
                timeout=self.timeout,
            )

            if result_response.status_code != 200:
                return {
                    "response": "",
                    "success": False,
                    "error": f"Result failed: {result_response.status_code}",
                }

            # Parse SSE stream for data
            result_data = None
            for line in result_response.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    import json
                    try:
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        if isinstance(data, list):
                            result_data = data
                    except json.JSONDecodeError:
                        continue

            if result_data is None:
                return {
                    "response": "",
                    "success": False,
                    "error": "No data in SSE response",
                }

            # Extract chat response from result
            # Output format: [msg_input, chatbot, btn1, btn2, btn3, status]
            # chatbot is at index 1, it's a list of [user_msg, assistant_msg] tuples
            if len(result_data) >= 2 and isinstance(result_data[1], list):
                chat_history = result_data[1]
                if chat_history:
                    last_exchange = chat_history[-1]
                    if isinstance(last_exchange, (list, tuple)) and len(last_exchange) >= 2:
                        return {
                            "response": str(last_exchange[1]),
                            "success": True,
                            "error": None,
                        }

            # Fallback: return raw data
            return {
                "response": str(result_data),
                "success": True,
                "error": None,
            }

        except requests.Timeout:
            return {
                "response": "",
                "success": False,
                "error": f"Timeout after {self.timeout}s",
            }
        except Exception as e:
            return {
                "response": "",
                "success": False,
                "error": f"Error: {str(e)}",
            }

    def health_check(self) -> bool:
        """Check if Gradio is healthy."""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            return response.status_code == 200
        except Exception:
            return False


@dataclass
class MLflowClient:
    """Simple MLflow API client for trace verification."""

    base_url: str = MLFLOW_URL

    def health_check(self) -> bool:
        """Check if MLflow is healthy."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def _get_experiment_ids(self) -> list:
        """Get all experiment IDs."""
        try:
            exp_response = requests.get(
                f"{self.base_url}/api/2.0/mlflow/experiments/search",
                params={"max_results": 100},
                timeout=10,
            )
            if exp_response.status_code == 200:
                experiments = exp_response.json().get("experiments", [])
                return [e["experiment_id"] for e in experiments]
        except Exception:
            pass
        return []

    def get_run_count(self, experiment_id: str = "1") -> int:
        """Get count of runs in experiment."""
        try:
            response = requests.get(
                f"{self.base_url}/api/2.0/mlflow/runs/search",
                params={"experiment_ids": [experiment_id], "max_results": 100},
                timeout=10,
            )
            if response.status_code == 200:
                return len(response.json().get("runs", []))
        except Exception:
            pass
        return 0

    def get_latest_trace_timestamp(self) -> int:
        """Get timestamp of the most recent trace (milliseconds since epoch)."""
        try:
            experiment_ids = self._get_experiment_ids()
            if not experiment_ids:
                return 0

            response = requests.get(
                f"{self.base_url}/api/2.0/mlflow/traces",
                params={"experiment_ids": experiment_ids, "max_results": 1},
                timeout=10,
            )
            if response.status_code == 200:
                traces = response.json().get("traces", [])
                if traces:
                    return traces[0].get("timestamp_ms", 0)
        except Exception:
            pass
        return 0

    def has_trace_since(self, timestamp_ms: int) -> bool:
        """Check if any trace was created after the given timestamp."""
        try:
            experiment_ids = self._get_experiment_ids()
            if not experiment_ids:
                return False

            response = requests.get(
                f"{self.base_url}/api/2.0/mlflow/traces",
                params={"experiment_ids": experiment_ids, "max_results": 5},
                timeout=10,
            )
            if response.status_code == 200:
                traces = response.json().get("traces", [])
                for trace in traces:
                    if trace.get("timestamp_ms", 0) > timestamp_ms:
                        return True
        except Exception:
            pass
        return False

    def get_trace_count(self) -> int:
        """Get count of traces (capped at 100 by MLflow API)."""
        try:
            experiment_ids = self._get_experiment_ids()
            if not experiment_ids:
                return 0

            response = requests.get(
                f"{self.base_url}/api/2.0/mlflow/traces",
                params={"experiment_ids": experiment_ids, "max_results": 100},
                timeout=10,
            )
            if response.status_code == 200:
                return len(response.json().get("traces", []))
        except Exception:
            pass
        return 0

    def get_latest_traces(self, limit: int = 5) -> list:
        """Get the most recent traces."""
        try:
            experiment_ids = self._get_experiment_ids()
            if not experiment_ids:
                return []

            response = requests.get(
                f"{self.base_url}/api/2.0/mlflow/traces",
                params={"experiment_ids": experiment_ids, "max_results": limit},
                timeout=10,
            )
            if response.status_code == 200:
                return response.json().get("traces", [])
        except Exception:
            pass
        return []

    def wait_for_new_trace(self, initial_timestamp: int, timeout: int = 30) -> bool:
        """Wait for a new trace to appear after the given timestamp."""
        start = time.time()
        while time.time() - start < timeout:
            if self.has_trace_since(initial_timestamp):
                return True
            time.sleep(1)
        return False


@pytest.fixture(scope="session")
def gradio_client():
    """Gradio API client fixture."""
    client = GradioClient()

    # Wait for Gradio to be ready
    for _ in range(30):
        if client.health_check():
            return client
        time.sleep(2)

    pytest.skip("Gradio not available")


@pytest.fixture(scope="session")
def mlflow_client():
    """MLflow API client fixture."""
    client = MLflowClient()

    # Wait for MLflow to be ready
    for _ in range(30):
        if client.health_check():
            return client
        time.sleep(2)

    pytest.skip("MLflow not available")


@pytest.fixture
def initial_trace_count(mlflow_client):
    """Get initial trace timestamp before test (for new trace detection)."""
    return mlflow_client.get_latest_trace_timestamp()


# Test data factories
@pytest.fixture
def test_vehicle_data():
    """Sample vehicle data for testing."""
    return {
        "name": "Test BMW",
        "make": "BMW",
        "model": "330i",
        "year": 2023,
        "license_plate": "BA-123AB",
        "vin": "WBA33010000000001",  # Valid 17-char VIN
        "fuel_type": "gasoline",
    }


@pytest.fixture
def test_checkpoint_data():
    """Sample checkpoint data for testing."""
    return {
        "odometer_km": 50000,
        "fuel_liters": 45.5,
        "fuel_type": "gasoline",
        "location": "Bratislava, Slovakia",
        "notes": "E2E test checkpoint",
    }


@pytest.fixture
def test_trip_data():
    """Sample trip data for testing."""
    return {
        "driver_name": "Test Driver",
        "purpose": "Business",
        "business_description": "Client meeting",
        "from_location": "Bratislava",
        "to_location": "Kosice",
        "distance_km": 410,
    }
