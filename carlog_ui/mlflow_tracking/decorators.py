"""
Decorators for automatic MLflow tracking.
"""

import time
import functools
from typing import Callable, Optional

from .tracker import ConversationTracker


def track_tool_call(
    tracker: ConversationTracker,
    adapter_name: str,
):
    """
    Decorator to automatically track MCP tool calls.

    Usage:
        @track_tool_call(tracker, "car-log-core")
        async def create_vehicle(arguments):
            return await adapter.call_tool("create_vehicle", arguments)
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(tool_name: str, arguments: dict, *args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(tool_name, arguments, *args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000

                tracker.log_tool_call(
                    adapter_name=adapter_name,
                    tool_name=tool_name,
                    arguments=arguments,
                    result=result,
                    duration_ms=duration_ms,
                )
                return result

            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                tracker.log_tool_call(
                    adapter_name=adapter_name,
                    tool_name=tool_name,
                    arguments=arguments,
                    result={"success": False, "error": str(e)},
                    duration_ms=duration_ms,
                )
                raise

        return wrapper
    return decorator


def track_dspy_call(
    tracker: ConversationTracker,
    module_name: str,
):
    """
    Decorator to automatically track DSPy module calls.

    Usage:
        @track_dspy_call(tracker, "CheckpointValidator")
        def validate_checkpoint(checkpoint_data, previous_checkpoint, vehicle_info):
            return validator.forward(checkpoint_data, previous_checkpoint, vehicle_info)
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()

            # Capture inputs
            inputs = {}
            if args:
                inputs["args"] = [str(a)[:200] for a in args]
            if kwargs:
                inputs["kwargs"] = {k: str(v)[:200] for k, v in kwargs.items()}

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000

                # Capture outputs
                outputs = {}
                if hasattr(result, "__dict__"):
                    outputs = {k: str(v)[:200] for k, v in result.__dict__.items()}
                elif isinstance(result, dict):
                    outputs = {k: str(v)[:200] for k, v in result.items()}
                else:
                    outputs = {"result": str(result)[:500]}

                tracker.log_dspy_call(
                    module_name=module_name,
                    inputs=inputs,
                    outputs=outputs,
                    duration_ms=duration_ms,
                )
                return result

            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                tracker.log_dspy_call(
                    module_name=module_name,
                    inputs=inputs,
                    outputs={"error": str(e)},
                    duration_ms=duration_ms,
                )
                raise

        return wrapper
    return decorator


class TrackedAdapter:
    """
    Wrapper that adds automatic tracking to any MCP adapter.

    Usage:
        adapter = CarLogCoreAdapter()
        tracked = TrackedAdapter(adapter, tracker)
        result = await tracked.call_tool("create_vehicle", {...})
    """

    def __init__(self, adapter, tracker: ConversationTracker):
        """
        Initialize tracked adapter.

        Args:
            adapter: The MCP adapter to wrap
            tracker: The conversation tracker
        """
        self._adapter = adapter
        self._tracker = tracker

    async def call_tool(self, tool_name: str, arguments: dict):
        """Call tool with automatic tracking."""
        start = time.perf_counter()
        try:
            result = await self._adapter.call_tool(tool_name, arguments)
            duration_ms = (time.perf_counter() - start) * 1000

            self._tracker.log_tool_call(
                adapter_name=self._adapter.name,
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                duration_ms=duration_ms,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            self._tracker.log_tool_call(
                adapter_name=self._adapter.name,
                tool_name=tool_name,
                arguments=arguments,
                result={"success": False, "error": str(e)},
                duration_ms=duration_ms,
            )
            raise

    def __getattr__(self, name):
        """Delegate other attributes to wrapped adapter."""
        return getattr(self._adapter, name)
