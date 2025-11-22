"""
Dashboard OCR MCP Server

Provides tools for photo metadata extraction (EXIF) and quality validation.
Part of the Car Log MCP-first architecture.

Server: dashboard-ocr
Status: P0 (EXIF extraction only; OCR with Claude Vision is P1)
"""

import json
import logging

from mcp.types import Tool, TextContent
from mcp.server import Server

from tools.extract_metadata import extract_metadata, check_photo_quality

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("dashboard-ocr")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="extract_metadata",
            description="Extract EXIF metadata from photo (GPS, timestamp, camera model)",
            inputSchema={
                "type": "object",
                "properties": {
                    "photo_path": {
                        "type": "string",
                        "description": "Path to photo file",
                    }
                },
                "required": ["photo_path"],
            },
        ),
        Tool(
            name="check_photo_quality",
            description="Validate photo quality for OCR processing",
            inputSchema={
                "type": "object",
                "properties": {
                    "photo_path": {
                        "type": "string",
                        "description": "Path to photo file",
                    }
                },
                "required": ["photo_path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    if name == "extract_metadata":
        photo_path = arguments.get("photo_path")
        if not photo_path:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": "photo_path is required",
                        }
                    ),
                )
            ]

        result = extract_metadata(photo_path)
        return [TextContent(type="text", text=json.dumps(result))]

    elif name == "check_photo_quality":
        photo_path = arguments.get("photo_path")
        if not photo_path:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "is_acceptable": False,
                            "issues": ["photo_path is required"],
                            "suggestions": [],
                        }
                    ),
                )
            ]

        result = check_photo_quality(photo_path)
        return [TextContent(type="text", text=json.dumps(result))]

    else:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": f"Unknown tool: {name}",
                    }
                ),
            )
        ]


async def main():
    """Run the MCP server."""
    async with server:
        logger.info("Dashboard OCR MCP server started")
        await server.wait_for_shutdown()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
