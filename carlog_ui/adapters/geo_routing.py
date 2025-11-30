"""
Adapter for geo-routing MCP server (Node.js via HTTP).

Provides geocoding and route calculation via HTTP calls to Node.js server.
"""

import os
from typing import List

from .base import HTTPMCPAdapter, ToolDefinition


class GeoRoutingAdapter(HTTPMCPAdapter):
    """
    Adapter for geo-routing MCP server (Node.js).

    Communicates via HTTP to the geo-routing container.

    Provides:
    - geocode_address: Convert address to coordinates
    - reverse_geocode: Convert coordinates to address
    - calculate_route: Calculate route between two points
    """

    # Tool definitions (since we can't import from Node.js)
    TOOL_DEFINITIONS = [
        ToolDefinition(
            name="geocode_address",
            description="Convert address string to GPS coordinates using Nominatim",
            input_schema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Address to geocode (e.g., 'Hlavná 45, Bratislava')"
                    },
                    "country_hint": {
                        "type": "string",
                        "default": "SK",
                        "description": "Country code hint for disambiguation"
                    }
                },
                "required": ["address"]
            }
        ),
        ToolDefinition(
            name="reverse_geocode",
            description="Convert GPS coordinates to address using Nominatim",
            input_schema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude coordinate"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude coordinate"
                    }
                },
                "required": ["latitude", "longitude"]
            }
        ),
        ToolDefinition(
            name="calculate_route",
            description="Calculate driving route between two points using OSRM",
            input_schema={
                "type": "object",
                "properties": {
                    "start_lat": {"type": "number", "description": "Start latitude"},
                    "start_lng": {"type": "number", "description": "Start longitude"},
                    "end_lat": {"type": "number", "description": "End latitude"},
                    "end_lng": {"type": "number", "description": "End longitude"}
                },
                "required": ["start_lat", "start_lng", "end_lat", "end_lng"]
            }
        ),
    ]

    def __init__(self, base_url: str = None, timeout: float = 30.0):
        """
        Initialize geo-routing adapter.

        Args:
            base_url: Base URL of geo-routing HTTP server.
                     Defaults to GEO_ROUTING_URL env var or http://geo-routing:8002
            timeout: Request timeout in seconds.
        """
        if base_url is None:
            base_url = os.getenv("GEO_ROUTING_URL", "http://geo-routing:8002")

        super().__init__(
            name="geo-routing",
            base_url=base_url,
            timeout=timeout
        )

    async def list_tools(self) -> List[ToolDefinition]:
        """
        Return tool definitions.

        Override to use static definitions (Node.js server may not expose /tools).
        Falls back to HTTP fetch if server supports it.
        """
        if not self._client:
            return self.TOOL_DEFINITIONS

        try:
            # Try to fetch from server
            return await super().list_tools()
        except Exception:
            # Fall back to static definitions
            return self.TOOL_DEFINITIONS


async def get_adapter(base_url: str = None) -> GeoRoutingAdapter:
    """
    Get initialized geo-routing adapter.

    Args:
        base_url: Override base URL (for testing).
    """
    adapter = GeoRoutingAdapter(base_url=base_url)
    await adapter.initialize()
    return adapter
