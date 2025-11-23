"""
MCP Server Entry Point for car-log-core.

This server provides CRUD operations for:
- Vehicles
- Checkpoints
- Trips
- Templates
"""

import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from .tools import (
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
    create_trips_batch,
    list_trips,
    get_trip,
    update_trip,
    delete_trip,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("car-log-core")

# Create MCP server instance
app = Server("car-log-core")


@app.list_tools()
async def list_tools():
    """List all available tools."""
    return [
        # Vehicle tools
        Tool(
            name="create_vehicle",
            description="Create new vehicle with Slovak tax compliance (VIN required)",
            inputSchema=create_vehicle.INPUT_SCHEMA,
        ),
        Tool(
            name="get_vehicle",
            description="Retrieve vehicle by ID",
            inputSchema=get_vehicle.INPUT_SCHEMA,
        ),
        Tool(
            name="list_vehicles",
            description="List all vehicles with optional filters",
            inputSchema=list_vehicles.INPUT_SCHEMA,
        ),
        Tool(
            name="update_vehicle",
            description="Update vehicle details",
            inputSchema=update_vehicle.INPUT_SCHEMA,
        ),
        Tool(
            name="delete_vehicle",
            description="Delete vehicle (warns if checkpoints/trips exist)",
            inputSchema=delete_vehicle.INPUT_SCHEMA,
        ),
        # Checkpoint tools
        Tool(
            name="create_checkpoint",
            description="Create checkpoint from refuel or manual entry",
            inputSchema=create_checkpoint.INPUT_SCHEMA,
        ),
        Tool(
            name="get_checkpoint",
            description="Retrieve checkpoint by ID",
            inputSchema=get_checkpoint.INPUT_SCHEMA,
        ),
        Tool(
            name="list_checkpoints",
            description="List checkpoints with filters (vehicle_id, date range)",
            inputSchema=list_checkpoints.INPUT_SCHEMA,
        ),
        Tool(
            name="update_checkpoint",
            description="Update checkpoint to fix mistakes (odometer, GPS, driver name)",
            inputSchema=update_checkpoint.INPUT_SCHEMA,
        ),
        Tool(
            name="delete_checkpoint",
            description="Delete checkpoint (warns if trips reference it)",
            inputSchema=delete_checkpoint.INPUT_SCHEMA,
        ),
        # Gap detection
        Tool(
            name="detect_gap",
            description="Analyze distance/time gap between two checkpoints",
            inputSchema=detect_gap.INPUT_SCHEMA,
        ),
        # Template tools
        Tool(
            name="create_template",
            description="Create trip template (GPS mandatory, addresses optional)",
            inputSchema=create_template.INPUT_SCHEMA,
        ),
        Tool(
            name="get_template",
            description="Get single template by ID",
            inputSchema=get_template.INPUT_SCHEMA,
        ),
        Tool(
            name="list_templates",
            description="List all trip templates",
            inputSchema=list_templates.INPUT_SCHEMA,
        ),
        Tool(
            name="update_template",
            description="Update template (GPS coords, address, name, business description)",
            inputSchema=update_template.INPUT_SCHEMA,
        ),
        Tool(
            name="delete_template",
            description="Delete trip template by ID",
            inputSchema=delete_template.INPUT_SCHEMA,
        ),
        # Trip tools
        Tool(
            name="create_trip",
            description="Create single trip with Slovak compliance (driver_name, L/100km)",
            inputSchema=create_trip.INPUT_SCHEMA,
        ),
        Tool(
            name="create_trips_batch",
            description="Batch create trips from reconstruction proposals",
            inputSchema=create_trips_batch.INPUT_SCHEMA,
        ),
        Tool(
            name="list_trips",
            description="List trips with filters (vehicle, date range, purpose)",
            inputSchema=list_trips.INPUT_SCHEMA,
        ),
        Tool(
            name="get_trip",
            description="Retrieve trip by ID",
            inputSchema=get_trip.INPUT_SCHEMA,
        ),
        Tool(
            name="update_trip",
            description="Update trip to fix data (business description, driver name, etc.)",
            inputSchema=update_trip.INPUT_SCHEMA,
        ),
        Tool(
            name="delete_trip",
            description="Delete trip by ID",
            inputSchema=delete_trip.INPUT_SCHEMA,
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute tool by name."""
    try:
        if name == "create_vehicle":
            return await create_vehicle.execute(arguments)
        elif name == "get_vehicle":
            return await get_vehicle.execute(arguments)
        elif name == "list_vehicles":
            return await list_vehicles.execute(arguments)
        elif name == "update_vehicle":
            return await update_vehicle.execute(arguments)
        elif name == "delete_vehicle":
            return await delete_vehicle.execute(arguments)
        elif name == "create_checkpoint":
            return await create_checkpoint.execute(arguments)
        elif name == "get_checkpoint":
            return await get_checkpoint.execute(arguments)
        elif name == "list_checkpoints":
            return await list_checkpoints.execute(arguments)
        elif name == "update_checkpoint":
            return await update_checkpoint.execute(arguments)
        elif name == "delete_checkpoint":
            return await delete_checkpoint.execute(arguments)
        elif name == "detect_gap":
            return await detect_gap.execute(arguments)
        elif name == "create_template":
            return await create_template.execute(arguments)
        elif name == "get_template":
            return await get_template.execute(arguments)
        elif name == "list_templates":
            return await list_templates.execute(arguments)
        elif name == "update_template":
            return await update_template.execute(arguments)
        elif name == "delete_template":
            return await delete_template.execute(arguments)
        elif name == "create_trip":
            return await create_trip.execute(arguments)
        elif name == "create_trips_batch":
            return await create_trips_batch.execute(arguments)
        elif name == "list_trips":
            return await list_trips.execute(arguments)
        elif name == "get_trip":
            return await get_trip.execute(arguments)
        elif name == "update_trip":
            return await update_trip.execute(arguments)
        elif name == "delete_trip":
            return await delete_trip.execute(arguments)
        else:
            return {
                "success": False,
                "error": {
                    "code": "UNKNOWN_TOOL",
                    "message": f"Unknown tool: {name}",
                },
            }
    except Exception as e:
        logger.error(f"Error executing {name}: {e}", exc_info=True)
        return {
            "success": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        }


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
