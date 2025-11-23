"""
MCP Server Entry Point for trip-reconstructor.

This server provides intelligent template-based trip reconstruction:
- GPS matching (70% weight)
- Address matching (30% weight)
- Hybrid scoring algorithm
- Template completeness analysis
"""

import asyncio
import logging
import os
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from .tools import (
    match_templates,
    calculate_template_completeness,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trip-reconstructor")

# Load environment variables
GPS_WEIGHT = float(os.getenv("GPS_WEIGHT", "0.7"))
ADDRESS_WEIGHT = float(os.getenv("ADDRESS_WEIGHT", "0.3"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "70"))

logger.info(f"trip-reconstructor initialized: GPS={GPS_WEIGHT}, Address={ADDRESS_WEIGHT}, Threshold={CONFIDENCE_THRESHOLD}")

# Create MCP server instance
app = Server("trip-reconstructor")


@app.list_tools()
async def list_tools():
    """List all available tools."""
    return [
        Tool(
            name="match_templates",
            description="Match templates to gap between checkpoints using hybrid GPS + address scoring",
            inputSchema=match_templates.INPUT_SCHEMA,
        ),
        Tool(
            name="calculate_template_completeness",
            description="Calculate template completeness and provide improvement suggestions",
            inputSchema=calculate_template_completeness.INPUT_SCHEMA,
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute tool by name."""
    try:
        if name == "match_templates":
            return await match_templates.execute(arguments)
        elif name == "calculate_template_completeness":
            return await calculate_template_completeness.execute(arguments)
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
