"""
ekasa-api MCP Server

Entry point for the e-Kasa receipt processing MCP server.
Provides QR code scanning and receipt data fetching tools.
"""

import asyncio
import logging
import os
import sys
from mcp.server import Server
from mcp.types import Tool, TextContent

from .tools.scan_qr_code import scan_qr_code
from .tools.fetch_receipt_data import fetch_receipt_data

# Configure logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("ekasa-api")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available tools in the e-Kasa API server.
    """
    return [
        Tool(
            name="scan_qr_code",
            description=(
                "Extract QR code from receipt image or PDF. "
                "Supports PNG, JPG, JPEG images and PDF documents with multi-scale detection "
                "for small or low-resolution QR codes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Absolute path to receipt image or PDF file"
                    }
                },
                "required": ["image_path"]
            }
        ),
        Tool(
            name="fetch_receipt_data",
            description=(
                "Fetch receipt data from Slovak e-Kasa API. "
                "Public endpoint, no authentication required. "
                "Automatically detects fuel items using Slovak naming patterns. "
                "May take 5-30 seconds to complete."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "receipt_id": {
                        "type": "string",
                        "description": "e-Kasa receipt identifier from QR code"
                    },
                    "timeout_seconds": {
                        "type": "number",
                        "default": 60,
                        "maximum": 60,
                        "description": "Override default timeout (max 60s)"
                    }
                },
                "required": ["receipt_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle tool execution requests.
    """
    try:
        logger.info(f"Tool called: {name} with arguments: {arguments}")

        if name == "scan_qr_code":
            result = await scan_qr_code(**arguments)
        elif name == "fetch_receipt_data":
            result = await fetch_receipt_data(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        logger.info(f"Tool {name} completed: success={result.get('success')}")

        return [TextContent(type="text", text=str(result))]

    except Exception as e:
        logger.error(f"Tool execution error: {e}", exc_info=True)
        error_result = {
            "success": False,
            "error": f"Tool execution error: {str(e)}"
        }
        return [TextContent(type="text", text=str(error_result))]


async def main():
    """
    Main entry point for the MCP server.
    """
    logger.info("Starting ekasa-api MCP server...")
    logger.info(f"Log level: {LOG_LEVEL}")

    # Import and run the server using stdio transport
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server initialized, waiting for requests...")
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
