"""
MLflow conversation tracking for Car Log.

Provides two tracking modes:
- full: Detailed tracing with nested spans, all inputs/outputs
- summary: Aggregate metrics only (counts, durations)
"""

import os
import time
import json
from enum import Enum
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from dataclasses import dataclass, field


class TrackingMode(Enum):
    """Tracking detail level."""
    FULL = "full"
    SUMMARY = "summary"


@dataclass
class ToolCallMetrics:
    """Metrics for a single tool call."""
    tool_name: str
    adapter_name: str
    duration_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class ConversationMetrics:
    """Aggregate metrics for a conversation."""
    total_tool_calls: int = 0
    successful_tool_calls: int = 0
    failed_tool_calls: int = 0
    total_dspy_calls: int = 0
    total_duration_ms: float = 0.0
    tool_calls: List[ToolCallMetrics] = field(default_factory=list)


class ConversationTracker:
    """
    MLflow-based conversation tracker.

    Usage:
        tracker = ConversationTracker()

        with tracker.start_conversation("user-123"):
            result = await adapter.call_tool_timed("create_vehicle", {...})
            tracker.log_tool_call("car-log-core", "create_vehicle", {...}, result)
    """

    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        experiment_name: str = "car-log-conversations",
        mode: Optional[TrackingMode] = None,
    ):
        """
        Initialize tracker.

        Args:
            tracking_uri: MLflow tracking server URI (default: MLFLOW_TRACKING_URI env)
            experiment_name: MLflow experiment name
            mode: Tracking mode (default: MLFLOW_TRACKING_MODE env or SUMMARY)
        """
        self.tracking_uri = tracking_uri or os.getenv(
            "MLFLOW_TRACKING_URI", "http://mlflow:5000"
        )
        self.experiment_name = experiment_name

        # Determine tracking mode
        if mode is None:
            mode_str = os.getenv("MLFLOW_TRACKING_MODE", "summary").lower()
            self.mode = TrackingMode(mode_str) if mode_str in ["full", "summary"] else TrackingMode.SUMMARY
        elif isinstance(mode, str):
            # Handle string input (convert to enum)
            self.mode = TrackingMode(mode.lower()) if mode.lower() in ["full", "summary"] else TrackingMode.SUMMARY
        else:
            self.mode = mode

        self._mlflow = None
        self._current_run = None
        self._metrics = ConversationMetrics()
        self._initialized = False
        self._auto_run_active = False
        self._message_count = 0

    def _ensure_initialized(self):
        """Lazy initialization of MLflow."""
        if self._initialized:
            return

        try:
            import mlflow
            self._mlflow = mlflow

            # Set tracking URI
            mlflow.set_tracking_uri(self.tracking_uri)

            # Create or get experiment
            mlflow.set_experiment(self.experiment_name)

            self._initialized = True
            print(f"MLflow initialized: {self.tracking_uri}, experiment: {self.experiment_name}")
        except ImportError:
            print("Warning: mlflow not installed, tracking disabled")
            self._initialized = False
        except Exception as e:
            print(f"Warning: MLflow initialization failed: {e}")
            self._initialized = False

    def _ensure_run_active(self):
        """Ensure an MLflow run is active (auto-start if needed)."""
        self._ensure_initialized()

        if not self._initialized or self._mlflow is None:
            return False

        # Check if we already have an active run
        if self._current_run is not None:
            return True

        # Auto-start a new run
        try:
            self._current_run = self._mlflow.start_run(run_name=f"auto-conversation-{self._message_count}")
            self._auto_run_active = True
            self._mlflow.log_param("tracking_mode", self.mode.value)
            self._mlflow.log_param("auto_started", "true")
            print(f"MLflow auto-started run: {self._current_run.info.run_id}")
            return True
        except Exception as e:
            print(f"Failed to auto-start MLflow run: {e}")
            return False

    def end_auto_run(self):
        """End auto-started run and log summary metrics."""
        if self._auto_run_active and self._current_run and self._mlflow:
            try:
                self._log_summary_metrics()
                self._mlflow.end_run()
                print(f"MLflow auto-run ended: {self._current_run.info.run_id}")
            except Exception as e:
                print(f"Error ending MLflow run: {e}")
            finally:
                self._current_run = None
                self._auto_run_active = False

    @contextmanager
    def start_conversation(self, user_id: str = "anonymous"):
        """
        Start tracking a conversation.

        Args:
            user_id: User identifier for the conversation

        Yields:
            Self for chaining
        """
        self._ensure_initialized()
        self._metrics = ConversationMetrics()

        if not self._initialized or self._mlflow is None:
            yield self
            return

        try:
            # Start MLflow run
            with self._mlflow.start_run(run_name=f"conversation-{user_id}") as run:
                self._current_run = run

                # Log initial parameters
                self._mlflow.log_param("user_id", user_id)
                self._mlflow.log_param("tracking_mode", self.mode.value)

                yield self

                # Log final metrics
                self._log_summary_metrics()

        except Exception as e:
            print(f"MLflow tracking error: {e}")
            yield self
        finally:
            self._current_run = None

    def log_tool_call(
        self,
        adapter_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any,
        duration_ms: float = 0.0,
    ):
        """
        Log an MCP tool call.

        Args:
            adapter_name: Name of the MCP adapter
            tool_name: Name of the tool called
            arguments: Tool input arguments
            result: Tool result (ToolResult or dict)
            duration_ms: Execution duration in milliseconds
        """
        # Determine success
        if hasattr(result, "success"):
            success = result.success
            error = result.error if hasattr(result, "error") else None
        elif isinstance(result, dict):
            success = result.get("success", True)
            error = result.get("error")
        else:
            success = True
            error = None

        # Track metrics
        metrics = ToolCallMetrics(
            tool_name=tool_name,
            adapter_name=adapter_name,
            duration_ms=duration_ms,
            success=success,
            error=str(error) if error else None,
        )

        self._metrics.total_tool_calls += 1
        self._metrics.total_duration_ms += duration_ms
        if success:
            self._metrics.successful_tool_calls += 1
        else:
            self._metrics.failed_tool_calls += 1
        self._metrics.tool_calls.append(metrics)

        # Log to MLflow in full mode
        if self.mode == TrackingMode.FULL and self._mlflow and self._current_run:
            try:
                # Use MLflow tracing for detailed logging
                with self._mlflow.start_span(name=f"{adapter_name}.{tool_name}") as span:
                    span.set_inputs({"arguments": arguments})
                    span.set_outputs({
                        "success": success,
                        "error": error,
                        "result": self._safe_serialize(result),
                    })
                    span.set_attribute("duration_ms", duration_ms)
            except Exception as e:
                # Fallback to simple logging
                self._mlflow.log_metric(f"tool_call_{tool_name}_ms", duration_ms)

    def log_dspy_call(
        self,
        module_name: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        duration_ms: float = 0.0,
    ):
        """
        Log a DSPy module invocation.

        Args:
            module_name: Name of the DSPy module
            inputs: Module inputs
            outputs: Module outputs
            duration_ms: Execution duration in milliseconds
        """
        self._metrics.total_dspy_calls += 1
        self._metrics.total_duration_ms += duration_ms

        if self.mode == TrackingMode.FULL and self._mlflow and self._current_run:
            try:
                with self._mlflow.start_span(name=f"dspy.{module_name}") as span:
                    span.set_inputs(inputs)
                    span.set_outputs(outputs)
                    span.set_attribute("duration_ms", duration_ms)
            except Exception as e:
                self._mlflow.log_metric(f"dspy_{module_name}_ms", duration_ms)

    def log_user_message(self, message: str):
        """Log a user message (auto-starts run if needed)."""
        self._message_count += 1

        if not self._ensure_run_active():
            return

        if self.mode == TrackingMode.FULL and self._mlflow:
            try:
                # Log as parameter for easy viewing in UI
                param_key = f"user_msg_{self._message_count}"
                self._mlflow.log_param(param_key, message[:500])

                # Also log as span for detailed tracing
                with self._mlflow.start_span(name="user_message") as span:
                    span.set_inputs({"message": message[:500]})
            except Exception as e:
                print(f"Error logging user message: {e}")

    def log_assistant_response(self, response: str):
        """Log an assistant response (auto-starts run if needed)."""
        if not self._ensure_run_active():
            return

        if self.mode == TrackingMode.FULL and self._mlflow:
            try:
                # Log as parameter for easy viewing in UI
                param_key = f"assistant_resp_{self._message_count}"
                self._mlflow.log_param(param_key, response[:500])

                # Also log as span for detailed tracing
                with self._mlflow.start_span(name="assistant_response") as span:
                    span.set_outputs({"response": response[:500]})
            except Exception as e:
                print(f"Error logging assistant response: {e}")

    def _log_summary_metrics(self):
        """Log aggregate metrics at end of conversation."""
        if not self._mlflow or not self._current_run:
            return

        try:
            self._mlflow.log_metrics({
                "total_tool_calls": self._metrics.total_tool_calls,
                "successful_tool_calls": self._metrics.successful_tool_calls,
                "failed_tool_calls": self._metrics.failed_tool_calls,
                "total_dspy_calls": self._metrics.total_dspy_calls,
                "total_duration_ms": self._metrics.total_duration_ms,
            })

            # Log tool call breakdown as artifact
            if self._metrics.tool_calls:
                tool_summary = {}
                for tc in self._metrics.tool_calls:
                    key = f"{tc.adapter_name}.{tc.tool_name}"
                    if key not in tool_summary:
                        tool_summary[key] = {"count": 0, "total_ms": 0, "failures": 0}
                    tool_summary[key]["count"] += 1
                    tool_summary[key]["total_ms"] += tc.duration_ms
                    if not tc.success:
                        tool_summary[key]["failures"] += 1

                self._mlflow.log_dict(tool_summary, "tool_call_summary.json")

        except Exception as e:
            print(f"Error logging summary metrics: {e}")

    def _safe_serialize(self, obj: Any) -> Any:
        """Safely serialize object for logging."""
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif hasattr(obj, "__dict__"):
            return {k: str(v)[:200] for k, v in obj.__dict__.items()}
        elif isinstance(obj, dict):
            return {k: str(v)[:200] for k, v in obj.items()}
        else:
            return str(obj)[:500]

    @property
    def metrics(self) -> ConversationMetrics:
        """Get current conversation metrics."""
        return self._metrics
