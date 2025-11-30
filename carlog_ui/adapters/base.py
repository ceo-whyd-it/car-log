"""
Base MCP Adapter class for Gradio integration.

Provides a unified interface for calling MCP server tools from Gradio,
whether the server is Python (direct import) or Node.js (HTTP).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import time


class AdapterError(Exception):
    """Base exception for adapter errors."""
    pass


class ToolNotFoundError(AdapterError):
    """Raised when a requested tool is not found."""
    pass


class ToolExecutionError(AdapterError):
    """Raised when tool execution fails."""
    pass


@dataclass
class ToolResult:
    """Result from executing an MCP tool."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"success": self.success}
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        if self.error_code is not None:
            result["error_code"] = self.error_code
        result["duration_ms"] = self.duration_ms
        return result


@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPAdapter(ABC):
    """
    Abstract base class for MCP server adapters.

    Subclasses implement either:
    - Direct Python import (for Python MCP servers)
    - HTTP client (for Node.js/remote MCP servers)
    """

    def __init__(self, name: str):
        """
        Initialize adapter.

        Args:
            name: Name of the MCP server (e.g., "car-log-core")
        """
        self.name = name
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the adapter (load modules, establish connections).

        Returns:
            True if initialization successful, False otherwise.
        """
        pass

    @abstractmethod
    async def list_tools(self) -> List[ToolDefinition]:
        """
        List all available tools from this MCP server.

        Returns:
            List of tool definitions.
        """
        pass

    @abstractmethod
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute a tool with the given arguments.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Dictionary of arguments to pass to the tool.

        Returns:
            ToolResult with success status and data or error.

        Raises:
            ToolNotFoundError: If tool doesn't exist.
            ToolExecutionError: If tool execution fails.
        """
        pass

    async def call_tool_timed(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute a tool and track execution time.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Dictionary of arguments to pass to the tool.

        Returns:
            ToolResult with duration_ms populated.
        """
        start = time.perf_counter()
        result = await self.call_tool(tool_name, arguments)
        result.duration_ms = (time.perf_counter() - start) * 1000
        return result

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the MCP server is healthy and responding.

        Returns:
            True if healthy, False otherwise.
        """
        pass

    async def close(self) -> None:
        """
        Clean up resources (close connections, etc.).
        Override in subclasses if needed.
        """
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if adapter is initialized."""
        return self._initialized

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, initialized={self._initialized})"


class PythonMCPAdapter(MCPAdapter):
    """
    Base adapter for Python MCP servers using direct imports.

    Subclasses should populate TOOLS dict with tool name -> module mapping.
    """

    # Override in subclass: {"tool_name": tool_module, ...}
    TOOLS: Dict[str, Any] = {}

    async def initialize(self) -> bool:
        """Initialize by verifying all tools are importable."""
        if not self.TOOLS:
            raise AdapterError(f"No tools defined for {self.name}")
        self._initialized = True
        return True

    async def list_tools(self) -> List[ToolDefinition]:
        """List tools from TOOLS dict."""
        definitions = []
        for name, module in self.TOOLS.items():
            # Each tool module should have INPUT_SCHEMA and optionally DESCRIPTION
            schema = getattr(module, "INPUT_SCHEMA", {})
            description = getattr(module, "DESCRIPTION", f"Tool: {name}")
            definitions.append(ToolDefinition(
                name=name,
                description=description,
                input_schema=schema
            ))
        return definitions

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """Execute tool by calling module.execute(arguments)."""
        if tool_name not in self.TOOLS:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found in {self.name}")

        module = self.TOOLS[tool_name]

        try:
            # All tool modules should have async execute(arguments) function
            result = await module.execute(arguments)

            # Handle different result formats
            if isinstance(result, dict):
                if "success" in result:
                    return ToolResult(
                        success=result.get("success", True),
                        data=result.get("data", result),
                        error=result.get("error"),
                        error_code=result.get("error_code")
                    )
                else:
                    return ToolResult(success=True, data=result)
            else:
                return ToolResult(success=True, data={"result": result})

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                error_code="EXECUTION_ERROR"
            )

    async def health_check(self) -> bool:
        """Python adapters are healthy if initialized."""
        return self._initialized


class HTTPMCPAdapter(MCPAdapter):
    """
    Base adapter for MCP servers accessed via HTTP.

    Used for Node.js servers or remote MCP servers.
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        timeout: float = 30.0
    ):
        """
        Initialize HTTP adapter.

        Args:
            name: Name of the MCP server.
            base_url: Base URL of the HTTP server (e.g., "http://geo-routing:8002").
            timeout: Request timeout in seconds.
        """
        super().__init__(name)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = None

    async def initialize(self) -> bool:
        """Initialize HTTP client."""
        try:
            import httpx
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )
            # Verify server is reachable
            if await self.health_check():
                self._initialized = True
                return True
            return False
        except ImportError:
            raise AdapterError("httpx package required for HTTP adapters")
        except Exception as e:
            raise AdapterError(f"Failed to initialize HTTP adapter: {e}")

    async def list_tools(self) -> List[ToolDefinition]:
        """Fetch tool list from /tools endpoint."""
        if not self._client:
            raise AdapterError("Adapter not initialized")

        response = await self._client.get("/tools")
        response.raise_for_status()
        tools_data = response.json()

        return [
            ToolDefinition(
                name=t["name"],
                description=t.get("description", ""),
                input_schema=t.get("inputSchema", {})
            )
            for t in tools_data.get("tools", [])
        ]

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """Execute tool via POST /tools/{name}."""
        if not self._client:
            raise AdapterError("Adapter not initialized")

        try:
            response = await self._client.post(
                f"/tools/{tool_name}",
                json=arguments
            )
            response.raise_for_status()
            data = response.json()

            return ToolResult(
                success=data.get("success", True),
                data=data.get("data", data),
                error=data.get("error"),
                error_code=data.get("error_code")
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                error_code="HTTP_ERROR"
            )

    async def health_check(self) -> bool:
        """Check /health endpoint."""
        if not self._client:
            return False

        try:
            response = await self._client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        await super().close()
