"""
Adapter for dashboard-ocr MCP server.

Provides photo metadata extraction tools.
"""

from typing import Dict, Any

from .base import PythonMCPAdapter

# Import tools from dashboard-ocr
from mcp_servers.dashboard_ocr.tools import (
    extract_metadata,
)


class DashboardOcrAdapter(PythonMCPAdapter):
    """
    Adapter for dashboard-ocr MCP server.

    Provides:
    - extract_metadata: Extract EXIF data (GPS, timestamp) from photos
    """

    TOOLS: Dict[str, Any] = {
        "extract_metadata": extract_metadata,
    }

    def __init__(self):
        """Initialize dashboard-ocr adapter."""
        super().__init__(name="dashboard-ocr")


async def get_adapter() -> DashboardOcrAdapter:
    """Get initialized dashboard-ocr adapter."""
    adapter = DashboardOcrAdapter()
    await adapter.initialize()
    return adapter
