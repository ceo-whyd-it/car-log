"""
Code Executor for Car Log Agent

Executes model-generated Python code IN-PROCESS with real MCP adapters.
This fixes the subprocess limitation where MCP calls couldn't return real results.

Key features:
- In-process execution with real adapters (no subprocess isolation)
- Timeout protection via asyncio.wait_for
- stdout/stderr capture via StringIO
- 3-retry logic with error context
- Direct MCP adapter access

Pattern inspired by: https://www.anthropic.com/engineering/code-execution-with-mcp
"""

import os
import sys
import json
import asyncio
import traceback
import time
from io import StringIO
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Awaitable
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr


@dataclass
class ExecutionResult:
    """Result from code execution."""
    success: bool
    stdout: str
    stderr: str
    execution_time: float
    return_value: Optional[Any] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    attempt: int = 1


@dataclass
class ExecutionStatus:
    """Status update for UI display."""
    state: str  # "starting", "running", "completed", "failed", "retrying"
    message: str
    code_preview: Optional[str] = None
    progress: float = 0.0
    attempt: int = 1
    max_attempts: int = 3


class AdapterWrapper:
    """
    Wrapper that provides attribute-style access to adapter tools.

    Allows: await car_log_core.list_vehicles()
    Instead of: await adapter.call_tool("list_vehicles", {})
    """

    def __init__(self, adapter: Any, name: str):
        self._adapter = adapter
        self._name = name

    def __getattr__(self, tool_name: str):
        """Return async function for tool calls."""
        async def call_tool(**kwargs):
            result = await self._adapter.call_tool(tool_name, kwargs)
            # Return the data directly for easier use
            if hasattr(result, 'success'):
                if result.success:
                    return result.data
                else:
                    raise Exception(f"MCP Error: {result.error}")
            return result
        return call_tool


class CodeExecutor:
    """
    Executes Python code in-process with real MCP adapters.

    The executor creates wrapper objects for each adapter that the model can call:
        result = await car_log_core.list_vehicles()

    Unlike subprocess execution, this allows real async MCP calls.
    """

    def __init__(
        self,
        adapters: Dict[str, Any],
        workspace_path: str = "/app/workspace",
        timeout: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize code executor.

        Args:
            adapters: Dictionary of MCP adapters (server_name -> adapter)
            workspace_path: Path for temporary files and state
            timeout: Maximum execution time in seconds
            max_retries: Maximum retry attempts on failure
        """
        self.adapters = adapters
        self.workspace_path = Path(workspace_path)
        self.timeout = timeout
        self.max_retries = max_retries

        # Ensure workspace exists
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        # Create adapter wrappers for direct access
        self.adapter_wrappers = {}
        for name, adapter in adapters.items():
            python_name = name.replace("-", "_")
            self.adapter_wrappers[python_name] = AdapterWrapper(adapter, name)

        # Status callback for UI updates
        self._status_callback: Optional[Callable[[ExecutionStatus], Awaitable[None]]] = None

    def set_status_callback(self, callback: Callable[[ExecutionStatus], Awaitable[None]]):
        """Set callback for status updates (for Gradio UI)."""
        self._status_callback = callback

    async def _notify_status(self, status: ExecutionStatus):
        """Notify UI of status change."""
        if self._status_callback:
            await self._status_callback(status)

    def _build_execution_globals(self) -> Dict[str, Any]:
        """
        Build the globals dictionary for exec().

        Includes adapter wrappers, helper functions, and standard imports.
        """
        import re
        import math
        from datetime import datetime, timedelta
        from collections import defaultdict

        workspace_path = str(self.workspace_path)

        def save_to_workspace(filename: str, data: Any):
            """Save data to workspace for later use."""
            filepath = os.path.join(workspace_path, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"Saved to {filepath}")

        def load_from_workspace(filename: str) -> Any:
            """Load data from workspace."""
            filepath = os.path.join(workspace_path, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)

        def list_tool_categories():
            """List available tool categories."""
            return [
                {"name": "vehicle", "description": "Vehicle registration and management"},
                {"name": "checkpoint", "description": "Checkpoint/refuel tracking"},
                {"name": "trip", "description": "Trip storage and management"},
                {"name": "template", "description": "Reusable trip templates"},
                {"name": "gap", "description": "Gap detection between checkpoints"},
                {"name": "matching", "description": "GPS-first template matching"},
                {"name": "validation", "description": "Trip validation algorithms"},
                {"name": "report", "description": "Report generation"},
                {"name": "receipt", "description": "Slovak e-Kasa receipt processing"},
                {"name": "geo", "description": "Geocoding and routing"},
            ]

        def list_tools_in_category(category: str):
            """List tools in a category."""
            tools_map = {
                "vehicle": ["create_vehicle", "get_vehicle", "list_vehicles", "update_vehicle", "delete_vehicle"],
                "checkpoint": ["create_checkpoint", "get_checkpoint", "list_checkpoints", "update_checkpoint", "delete_checkpoint"],
                "trip": ["create_trip", "create_trips_batch", "get_trip", "list_trips", "update_trip", "delete_trip"],
                "template": ["create_template", "get_template", "list_templates", "update_template", "delete_template"],
                "gap": ["detect_gap"],
                "matching": ["match_templates", "calculate_template_completeness"],
                "validation": ["validate_checkpoint_pair", "validate_trip", "check_efficiency", "check_deviation_from_average"],
                "report": ["generate_csv", "generate_pdf"],
                "receipt": ["scan_qr_code", "fetch_receipt_data"],
                "geo": ["geocode_address", "reverse_geocode", "calculate_route"],
            }
            return tools_map.get(category, [])

        # Build globals
        globals_dict = {
            # Standard modules
            "json": json,
            "re": re,
            "math": math,
            "datetime": datetime,
            "timedelta": timedelta,
            "defaultdict": defaultdict,
            "os": os,
            "asyncio": asyncio,
            "print": print,  # Will be redirected

            # Helper functions
            "save_to_workspace": save_to_workspace,
            "load_from_workspace": load_from_workspace,
            "list_tool_categories": list_tool_categories,
            "list_tools_in_category": list_tools_in_category,
        }

        # Add adapter wrappers
        globals_dict.update(self.adapter_wrappers)

        return globals_dict

    async def execute(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute code with retry logic.

        Args:
            code: Python code to execute
            context: Optional context variables to inject

        Returns:
            ExecutionResult with stdout, stderr, and status
        """
        last_result = None

        for attempt in range(1, self.max_retries + 1):
            await self._notify_status(ExecutionStatus(
                state="running" if attempt == 1 else "retrying",
                message=f"Executing code (attempt {attempt}/{self.max_retries})...",
                code_preview=code[:200] + "..." if len(code) > 200 else code,
                progress=0.3,
                attempt=attempt,
                max_attempts=self.max_retries,
            ))

            result = await self._execute_once(code, context)
            result.attempt = attempt

            if result.success:
                await self._notify_status(ExecutionStatus(
                    state="completed",
                    message=f"Code executed successfully in {result.execution_time:.2f}s",
                    progress=1.0,
                    attempt=attempt,
                ))
                return result

            last_result = result

            # If we have more attempts, notify about retry
            if attempt < self.max_retries:
                await self._notify_status(ExecutionStatus(
                    state="retrying",
                    message=f"Attempt {attempt} failed: {result.error_message}. Retrying...",
                    progress=0.3 + (attempt * 0.2),
                    attempt=attempt + 1,
                ))
                await asyncio.sleep(0.5)

        # All attempts failed
        await self._notify_status(ExecutionStatus(
            state="failed",
            message=f"Code execution failed after {self.max_retries} attempts",
            progress=1.0,
            attempt=self.max_retries,
        ))

        return last_result or ExecutionResult(
            success=False,
            stdout="",
            stderr="Max retries exceeded",
            execution_time=0,
            error_type="MaxRetriesExceeded",
            error_message=f"Code execution failed after {self.max_retries} attempts",
        )

    async def _execute_once(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute code once in-process.

        Args:
            code: Python code to execute
            context: Optional context variables

        Returns:
            ExecutionResult
        """
        start_time = time.time()

        # Capture stdout/stderr
        stdout_buffer = StringIO()
        stderr_buffer = StringIO()

        # Build execution environment
        exec_globals = self._build_execution_globals()

        # Add context variables if provided
        if context:
            exec_globals.update(context)

        # Wrap code in async function
        wrapped_code = f"""
async def __user_code__():
{chr(10).join('    ' + line for line in code.split(chr(10)))}

__result__ = asyncio.get_event_loop().run_until_complete(__user_code__())
"""

        try:
            # Execute with timeout
            async def run_code():
                # Redirect stdout/stderr
                old_stdout = sys.stdout
                old_stderr = sys.stderr

                try:
                    sys.stdout = stdout_buffer
                    sys.stderr = stderr_buffer

                    # Compile and execute
                    compiled = compile(wrapped_code, "<agent_code>", "exec")

                    # Create a new event loop for the exec'd code
                    loop = asyncio.new_event_loop()
                    exec_globals['asyncio'] = asyncio

                    # We need to handle async code specially
                    # Parse the original code and wrap it properly
                    async_wrapper = f"""
import asyncio

async def __execute_user_code__():
{chr(10).join('    ' + line for line in code.split(chr(10)))}

# Run and store result
__exec_result__ = None
try:
    __exec_result__ = asyncio.get_event_loop().run_until_complete(__execute_user_code__())
except RuntimeError:
    # Already in async context, just await
    import nest_asyncio
    nest_asyncio.apply()
    __exec_result__ = asyncio.get_event_loop().run_until_complete(__execute_user_code__())
"""
                    # Actually, simpler approach - just exec with await support
                    # by running in current event loop

                    exec_locals = {}

                    # Define async main and run it
                    async_code = f"""
async def __async_main__():
{chr(10).join('    ' + line for line in code.split(chr(10)))}
"""
                    exec(async_code, exec_globals, exec_locals)

                    # Run the async function
                    result = await exec_locals['__async_main__']()
                    return result

                finally:
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr

            # Run with timeout
            try:
                return_value = await asyncio.wait_for(run_code(), timeout=self.timeout)
            except asyncio.TimeoutError:
                return ExecutionResult(
                    success=False,
                    stdout=stdout_buffer.getvalue(),
                    stderr=f"Execution timed out after {self.timeout} seconds",
                    execution_time=self.timeout,
                    error_type="TimeoutError",
                    error_message=f"Code execution exceeded {self.timeout}s timeout",
                )

            execution_time = time.time() - start_time

            return ExecutionResult(
                success=True,
                stdout=stdout_buffer.getvalue(),
                stderr=stderr_buffer.getvalue(),
                execution_time=execution_time,
                return_value=return_value,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_type = type(e).__name__
            error_message = str(e)

            # Get full traceback for stderr
            tb = traceback.format_exc()

            return ExecutionResult(
                success=False,
                stdout=stdout_buffer.getvalue(),
                stderr=stderr_buffer.getvalue() + "\n" + tb,
                execution_time=execution_time,
                error_type=error_type,
                error_message=error_message,
            )

    def get_error_context(self, result: ExecutionResult, original_code: str) -> str:
        """
        Generate error context for model to fix code.

        Args:
            result: Failed execution result
            original_code: Original code that failed

        Returns:
            Error context string for model
        """
        context = f"""
## Code Execution Failed (Attempt {result.attempt}/{self.max_retries})

### Error Type
{result.error_type}

### Error Message
{result.error_message}

### Stderr
```
{result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr}
```

### Original Code
```python
{original_code}
```

### Instructions
Please analyze the error and provide fixed code. Common issues:
1. Syntax errors - check indentation and brackets
2. Missing imports - json, re, math, datetime are available
3. Wrong adapter method - use list_tools_in_category() to check available methods
4. Invalid arguments - check the tool expects keyword arguments

### Available Adapters
{', '.join(self.adapter_wrappers.keys())}

### Example Usage
```python
# List vehicles
vehicles = await car_log_core.list_vehicles()
print(f"Found {{len(vehicles.get('vehicles', []))}} vehicles")

# Create checkpoint
result = await car_log_core.create_checkpoint(
    vehicle_id="...",
    odometer_km=12345,
    checkpoint_type="refuel"
)
```
"""
        return context


# Convenience function for simple code execution
async def execute_code(
    code: str,
    adapters: Dict[str, Any],
    workspace_path: str = "/app/workspace",
) -> ExecutionResult:
    """
    Execute code with default settings.

    Args:
        code: Python code to execute
        adapters: MCP adapters dictionary
        workspace_path: Workspace directory path

    Returns:
        ExecutionResult
    """
    executor = CodeExecutor(adapters=adapters, workspace_path=workspace_path)
    return await executor.execute(code)
