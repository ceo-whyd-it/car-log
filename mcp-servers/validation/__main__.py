"""
MCP Server Entry Point for validation.

This server provides data validation algorithms for:
- Checkpoint pair validation (distance sum check)
- Trip validation (comprehensive)
- Efficiency reasonability check
- Deviation from average check
"""

import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from .tools import (
    validate_checkpoint_pair,
    validate_trip,
    check_efficiency,
    check_deviation_from_average,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("validation")

# Create MCP server instance
app = Server("validation")


@app.list_tools()
async def list_tools():
    """List all available tools."""
    return [
        Tool(
            name="validate_checkpoint_pair",
            description="Validate gap between two checkpoints (distance sum ±10%)",
            inputSchema=validate_checkpoint_pair.INPUT_SCHEMA,
        ),
        Tool(
            name="validate_trip",
            description="Comprehensive trip validation (distance, fuel, efficiency, deviation)",
            inputSchema=validate_trip.INPUT_SCHEMA,
        ),
        Tool(
            name="check_efficiency",
            description="Check fuel efficiency reasonability against fuel type ranges",
            inputSchema=check_efficiency.INPUT_SCHEMA,
        ),
        Tool(
            name="check_deviation_from_average",
            description="Compare trip efficiency to vehicle average (±20% warning)",
            inputSchema=check_deviation_from_average.INPUT_SCHEMA,
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute tool by name."""
    logger.info(f"Calling tool: {name}")

    if name == "validate_checkpoint_pair":
        return await validate_checkpoint_pair.execute(arguments)
    elif name == "validate_trip":
        return await validate_trip.execute(arguments)
    elif name == "check_efficiency":
        return await check_efficiency.execute(arguments)
    elif name == "check_deviation_from_average":
        return await check_deviation_from_average.execute(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run MCP server."""
    logger.info("Starting validation MCP server...")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
