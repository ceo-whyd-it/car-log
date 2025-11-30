"""
MCP Server Adapters for Gradio.

These adapters allow Gradio to call MCP server tools directly via Python imports
(for Python servers) or HTTP (for Node.js servers), bypassing stdio transport.

This enables the same MCP server codebase to work with both:
- Claude Desktop (stdio transport)
- Gradio UI (direct import / HTTP)
"""

from .base import (
    MCPAdapter,
    PythonMCPAdapter,
    HTTPMCPAdapter,
    AdapterError,
    ToolNotFoundError,
    ToolExecutionError,
    ToolResult,
    ToolDefinition,
)
from .car_log_core import CarLogCoreAdapter
from .trip_reconstructor import TripReconstructorAdapter
from .validation import ValidationAdapter
from .ekasa_api import EkasaApiAdapter
from .dashboard_ocr import DashboardOcrAdapter
from .report_generator import ReportGeneratorAdapter
from .geo_routing import GeoRoutingAdapter

__all__ = [
    # Base classes
    "MCPAdapter",
    "PythonMCPAdapter",
    "HTTPMCPAdapter",
    "AdapterError",
    "ToolNotFoundError",
    "ToolExecutionError",
    "ToolResult",
    "ToolDefinition",
    # Concrete adapters
    "CarLogCoreAdapter",
    "TripReconstructorAdapter",
    "ValidationAdapter",
    "EkasaApiAdapter",
    "DashboardOcrAdapter",
    "ReportGeneratorAdapter",
    "GeoRoutingAdapter",
]
