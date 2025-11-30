"""
Adapter for trip-reconstructor MCP server.

Provides template matching and trip reconstruction tools.
"""

from typing import Dict, Any

from .base import PythonMCPAdapter

# Import tools from trip-reconstructor
from mcp_servers.trip_reconstructor.tools import (
    match_templates,
    calculate_template_completeness,
)


class TripReconstructorAdapter(PythonMCPAdapter):
    """
    Adapter for trip-reconstructor MCP server.

    Provides:
    - match_templates: Match gap data against templates
    - calculate_template_completeness: Check template coverage
    """

    TOOLS: Dict[str, Any] = {
        "match_templates": match_templates,
        "calculate_template_completeness": calculate_template_completeness,
    }

    def __init__(self):
        """Initialize trip-reconstructor adapter."""
        super().__init__(name="trip-reconstructor")


async def get_adapter() -> TripReconstructorAdapter:
    """Get initialized trip-reconstructor adapter."""
    adapter = TripReconstructorAdapter()
    await adapter.initialize()
    return adapter
