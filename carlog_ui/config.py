"""
Configuration for Gradio Car Log application.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AppConfig:
    """Application configuration."""

    # Data storage
    data_path: str = os.getenv("DATA_PATH", "/data")

    # OpenAI / DSPy
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")

    # MLflow
    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    mlflow_tracking_mode: str = os.getenv("MLFLOW_TRACKING_MODE", "summary")

    # geo-routing
    geo_routing_url: str = os.getenv("GEO_ROUTING_URL", "http://geo-routing:8002")

    # Gradio server
    server_host: str = os.getenv("GRADIO_HOST", "0.0.0.0")
    server_port: int = int(os.getenv("GRADIO_PORT", "7860"))
    share: bool = os.getenv("GRADIO_SHARE", "false").lower() == "true"

    def validate(self) -> list[str]:
        """
        Validate configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY environment variable is required")

        if not os.path.exists(self.data_path):
            errors.append(f"Data path does not exist: {self.data_path}")

        return errors


def get_config() -> AppConfig:
    """Get application configuration."""
    return AppConfig()
