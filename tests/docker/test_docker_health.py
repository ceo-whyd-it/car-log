"""
Test Docker container health for all Car Log services.
Run with: pytest tests/docker/test_docker_health.py -v
"""
import pytest
import subprocess
import requests
import time

CONTAINERS = [
    "car-log-gradio",
    "car-log-geo-routing",
    "car-log-mlflow"
]


class TestDockerHealth:

    def test_all_containers_running(self):
        """All required containers must be running."""
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        running = result.stdout.strip().split('\n')
        for container in CONTAINERS:
            assert container in running, f"Container {container} not running. Running containers: {running}"

    def test_gradio_health_endpoint(self):
        """Gradio app must respond to health check."""
        try:
            response = requests.get("http://localhost:7861/", timeout=10)
            assert response.status_code == 200, f"Gradio returned status {response.status_code}"
        except requests.exceptions.ConnectionError as e:
            pytest.fail(f"Cannot connect to Gradio at localhost:7861: {e}")
        except requests.exceptions.Timeout:
            pytest.fail("Gradio request timed out after 10 seconds")

    def test_geo_routing_health(self):
        """Geo-routing server must respond to /health."""
        try:
            response = requests.get("http://localhost:8002/health", timeout=10)
            assert response.status_code == 200, f"Geo-routing returned status {response.status_code}"
        except requests.exceptions.ConnectionError as e:
            pytest.fail(f"Cannot connect to geo-routing at localhost:8002: {e}")
        except requests.exceptions.Timeout:
            pytest.fail("Geo-routing request timed out after 10 seconds")

    def test_mlflow_health(self):
        """MLflow server must respond."""
        try:
            response = requests.get("http://localhost:5050/health", timeout=10)
            # MLflow health endpoint may return different codes, 200 or redirect
            assert response.status_code in [200, 302, 307], f"MLflow returned status {response.status_code}"
        except requests.exceptions.ConnectionError as e:
            pytest.fail(f"Cannot connect to MLflow at localhost:5050: {e}")
        except requests.exceptions.Timeout:
            pytest.fail("MLflow request timed out after 10 seconds")

    def test_container_health_status(self):
        """All containers should report healthy status."""
        for container in CONTAINERS:
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Status}}", container],
                capture_output=True, text=True
            )
            status = result.stdout.strip()
            assert status == "running", f"Container {container} is not running, status: {status}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
