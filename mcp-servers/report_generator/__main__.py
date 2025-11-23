"""
Report Generator MCP Server

Provides tools for generating mileage log reports in various formats.

P0 Tools:
- generate_csv: Generate CSV report with Slovak tax compliance

P1 Tools (optional):
- generate_pdf: Generate PDF report with Slovak VAT template
"""

import asyncio
import sys
from mcp.types import Tool
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import tool implementations
from report_generator.tools.generate_csv import execute as generate_csv_execute, INPUT_SCHEMA as CSV_SCHEMA

# Create MCP server instance
app = Server("report-generator")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available report generation tools"""
    return [
        Tool(
            name="generate_csv",
            description=(
                "Generate CSV mileage log report for Slovak tax compliance. "
                "Filters trips by date range and business purpose, calculates "
                "summary statistics (total distance, fuel consumption, costs). "
                "Output includes all mandatory fields: VIN, driver, trip timing, locations."
            ),
            inputSchema=CSV_SCHEMA,
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute report generation tool"""

    if name == "generate_csv":
        result = await generate_csv_execute(arguments)
        return [TextContent(
            type="text",
            text=str(result) if isinstance(result, dict) else result
        )]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
