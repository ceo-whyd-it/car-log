"""
Adapter for report-generator MCP server.

Provides report generation tools.
"""

from typing import Dict, Any

from .base import PythonMCPAdapter

# Import tools from report-generator
from mcp_servers.report_generator.tools import (
    generate_csv,
)


class ReportGeneratorAdapter(PythonMCPAdapter):
    """
    Adapter for report-generator MCP server.

    Provides:
    - generate_csv: Generate Slovak tax-compliant CSV report
    """

    TOOLS: Dict[str, Any] = {
        "generate_csv": generate_csv,
    }

    def __init__(self):
        """Initialize report-generator adapter."""
        super().__init__(name="report-generator")


async def get_adapter() -> ReportGeneratorAdapter:
    """Get initialized report-generator adapter."""
    adapter = ReportGeneratorAdapter()
    await adapter.initialize()
    return adapter
