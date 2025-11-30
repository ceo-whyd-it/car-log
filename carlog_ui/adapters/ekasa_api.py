"""
Adapter for ekasa-api MCP server.

Provides Slovak e-Kasa receipt processing tools.
"""

from typing import Dict, Any

from .base import PythonMCPAdapter

# Import tools from ekasa-api
from mcp_servers.ekasa_api.tools import (
    fetch_receipt_data,
    scan_qr_code,
)


class EkasaApiAdapter(PythonMCPAdapter):
    """
    Adapter for ekasa-api MCP server.

    Provides:
    - fetch_receipt_data: Fetch receipt from Slovak e-Kasa API
    - scan_qr_code: Extract receipt ID from QR code in image/PDF
    """

    TOOLS: Dict[str, Any] = {
        "fetch_receipt_data": fetch_receipt_data,
        "scan_qr_code": scan_qr_code,
    }

    def __init__(self):
        """Initialize ekasa-api adapter."""
        super().__init__(name="ekasa-api")


async def get_adapter() -> EkasaApiAdapter:
    """Get initialized ekasa-api adapter."""
    adapter = EkasaApiAdapter()
    await adapter.initialize()
    return adapter
