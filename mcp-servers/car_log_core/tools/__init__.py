"""
Tool implementations for car-log-core MCP server.
"""

from . import (
    create_vehicle,
    get_vehicle,
    list_vehicles,
    update_vehicle,
    create_checkpoint,
    get_checkpoint,
    list_checkpoints,
    detect_gap,
    create_template,
    list_templates,
    create_trip,
    get_trip,
    list_trips,
    create_trips_batch,
)

__all__ = [
    "create_vehicle",
    "get_vehicle",
    "list_vehicles",
    "update_vehicle",
    "create_checkpoint",
    "get_checkpoint",
    "list_checkpoints",
    "detect_gap",
    "create_template",
    "list_templates",
    "create_trip",
    "get_trip",
    "list_trips",
    "create_trips_batch",
]
