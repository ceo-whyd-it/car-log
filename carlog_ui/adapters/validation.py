"""
Adapter for validation MCP server.

Provides Slovak tax compliance validation tools.
"""

from typing import Dict, Any

from .base import PythonMCPAdapter

# Import tools from validation
from mcp_servers.validation.tools import (
    validate_checkpoint_pair,
    validate_trip,
    check_efficiency,
    check_deviation_from_average,
)


class ValidationAdapter(PythonMCPAdapter):
    """
    Adapter for validation MCP server.

    Provides:
    - validate_checkpoint_pair: Validate distance/consumption between checkpoints
    - validate_trip: Full trip validation
    - check_efficiency: Fuel efficiency L/100km validation
    - check_deviation_from_average: Compare to vehicle average
    """

    TOOLS: Dict[str, Any] = {
        "validate_checkpoint_pair": validate_checkpoint_pair,
        "validate_trip": validate_trip,
        "check_efficiency": check_efficiency,
        "check_deviation_from_average": check_deviation_from_average,
    }

    def __init__(self):
        """Initialize validation adapter."""
        super().__init__(name="validation")


async def get_adapter() -> ValidationAdapter:
    """Get initialized validation adapter."""
    adapter = ValidationAdapter()
    await adapter.initialize()
    return adapter
