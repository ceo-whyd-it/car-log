"""
Adapter for car-log-core MCP server.

Provides direct Python import access to all 22 CRUD tools for:
- Vehicles
- Checkpoints
- Templates
- Trips
"""

from typing import Dict, Any

from .base import PythonMCPAdapter

# Import all tools from car-log-core
from mcp_servers.car_log_core.tools import (
    create_vehicle,
    get_vehicle,
    list_vehicles,
    update_vehicle,
    delete_vehicle,
    create_checkpoint,
    get_checkpoint,
    list_checkpoints,
    update_checkpoint,
    delete_checkpoint,
    detect_gap,
    create_template,
    get_template,
    list_templates,
    update_template,
    delete_template,
    create_trip,
    get_trip,
    list_trips,
    update_trip,
    delete_trip,
    create_trips_batch,
)


class CarLogCoreAdapter(PythonMCPAdapter):
    """
    Adapter for car-log-core MCP server.

    Provides CRUD operations for:
    - Vehicles (5 tools)
    - Checkpoints (5 tools + gap detection)
    - Templates (5 tools)
    - Trips (6 tools including batch)
    """

    # Map tool names to modules
    TOOLS: Dict[str, Any] = {
        # Vehicle CRUD
        "create_vehicle": create_vehicle,
        "get_vehicle": get_vehicle,
        "list_vehicles": list_vehicles,
        "update_vehicle": update_vehicle,
        "delete_vehicle": delete_vehicle,
        # Checkpoint CRUD
        "create_checkpoint": create_checkpoint,
        "get_checkpoint": get_checkpoint,
        "list_checkpoints": list_checkpoints,
        "update_checkpoint": update_checkpoint,
        "delete_checkpoint": delete_checkpoint,
        # Gap detection
        "detect_gap": detect_gap,
        # Template CRUD
        "create_template": create_template,
        "get_template": get_template,
        "list_templates": list_templates,
        "update_template": update_template,
        "delete_template": delete_template,
        # Trip CRUD
        "create_trip": create_trip,
        "get_trip": get_trip,
        "list_trips": list_trips,
        "update_trip": update_trip,
        "delete_trip": delete_trip,
        "create_trips_batch": create_trips_batch,
    }

    def __init__(self):
        """Initialize car-log-core adapter."""
        super().__init__(name="car-log-core")


# Convenience function for quick access
async def get_adapter() -> CarLogCoreAdapter:
    """Get initialized car-log-core adapter."""
    adapter = CarLogCoreAdapter()
    await adapter.initialize()
    return adapter
