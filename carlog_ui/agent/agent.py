"""
Car Log Agent - Main Agentic Loop

Implements the "Code Execution with MCP" pattern from Anthropic's engineering article.
The agent uses an LLM to generate Python code that interacts with MCP servers,
achieving 98%+ token reduction through progressive tool discovery.

Pattern: https://www.anthropic.com/engineering/code-execution-with-mcp
"""

import os
import json
import re
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, AsyncGenerator
from datetime import datetime

from openai import AsyncOpenAI
import mlflow

from .system_prompt import get_system_prompt
from .tool_discovery import ToolDiscovery
from .code_executor import CodeExecutor, ExecutionResult, ExecutionStatus
from .code_library import CodeLibrary
from .snippet_manager import SnippetManager


@dataclass
class AgentConfig:
    """Configuration for the Car Log Agent."""
    model: str = "gpt-5-mini"  # Best value: 80% of GPT-5 at 10x cheaper than GPT-4o
    max_iterations: int = 5     # Max code execution rounds per message
    max_tokens: int = 4096      # Max response tokens
    temperature: float = 0.1    # Low temperature for deterministic code
    workspace_path: str = "/app/workspace"
    execution_timeout: int = 60
    max_retries: int = 3
    code_library_path: str = "/app/code_library"  # Path to code snippets


@dataclass
class ConversationMessage:
    """A message in the conversation history."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    code_executed: Optional[str] = None
    execution_result: Optional[ExecutionResult] = None


@dataclass
class AgentResponse:
    """Response from the agent."""
    message: str
    code_blocks: List[str] = field(default_factory=list)
    execution_results: List[ExecutionResult] = field(default_factory=list)
    quick_actions: List[str] = field(default_factory=list)
    error: Optional[str] = None
    iterations: int = 0


class CarLogAgent:
    """
    Car Log Agent implementing code execution pattern.

    The agent:
    1. Receives user message
    2. Sends to LLM with system prompt and tool index
    3. If LLM responds with code block:
       a. Execute code in sandbox
       b. Feed result back to LLM
       c. Repeat until final response
    4. Return final response to user
    """

    def __init__(
        self,
        adapters: Dict[str, Any],
        config: Optional[AgentConfig] = None,
        tracker: Optional[Any] = None,
    ):
        """
        Initialize the Car Log Agent.

        Args:
            adapters: Dictionary of MCP adapters (server_name -> adapter)
            config: Agent configuration
            tracker: MLflow conversation tracker (optional)
        """
        self.adapters = adapters
        self.config = config or AgentConfig()
        self.tracker = tracker

        # Initialize components
        self.tool_discovery = ToolDiscovery()
        self.code_executor = CodeExecutor(
            adapters=adapters,
            workspace_path=self.config.workspace_path,
            timeout=self.config.execution_timeout,
            max_retries=self.config.max_retries,
        )

        # Initialize code library for snippet reuse
        self.code_library = CodeLibrary(self.config.code_library_path)
        self.snippet_manager = SnippetManager()
        self._library_loaded = False

        # Enable OpenAI tracing (MLflow 3.x) BEFORE creating the client
        # Autolog patches the openai library, so it must be called before client creation
        try:
            # Set tracking URI from environment (required for autolog to work)
            tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5050")
            mlflow.set_tracking_uri(tracking_uri)
            print(f"MLflow tracking URI set to: {tracking_uri}")

            # Set or create experiment for traces
            experiment_name = "car-log-agent"
            try:
                mlflow.set_experiment(experiment_name)
                print(f"MLflow experiment set: {experiment_name}")
            except Exception as exp_err:
                print(f"Could not set experiment: {exp_err}")

            # Enable autolog for OpenAI calls (BEFORE client creation!)
            mlflow.openai.autolog()
            print("OpenAI autolog enabled")

        except Exception as e:
            print(f"OpenAI autolog not available: {e}")

        # Initialize OpenAI client (AFTER autolog is enabled)
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        # Conversation state
        self.conversation_history: List[ConversationMessage] = []
        self.current_vehicle_id: Optional[str] = None

        # MLflow trace session tracking
        import uuid
        self.session_id = str(uuid.uuid4())[:8]  # Short session ID
        self.user_id = os.getenv("CARLOG_USER_ID", "default-user")

        # Status callback for UI updates
        self._status_callback = None

    def set_status_callback(self, callback):
        """Set callback for status updates (for Gradio UI)."""
        self._status_callback = callback
        self.code_executor.set_status_callback(callback)

    def load_code_library(self) -> int:
        """
        Load and index the code library.

        Returns:
            Number of snippets loaded
        """
        count = self.code_library.scan()
        self._library_loaded = True
        return count

    def find_matching_snippets(self, user_message: str, top_k: int = 3):
        """
        Find snippets that match the user's intent.

        Args:
            user_message: The user's message/query
            top_k: Maximum number of matches to return

        Returns:
            List of MatchResult objects
        """
        if not self._library_loaded:
            self.load_code_library()

        return self.code_library.match(user_message, top_k=top_k)

    def _format_snippet_suggestions(self, matches) -> str:
        """Format matching snippets for inclusion in prompt."""
        if not matches:
            return ""

        lines = ["\n## Matching Code Snippets"]
        lines.append("These pre-built snippets may help with this task:\n")

        for match in matches:
            snippet = match.snippet
            score_pct = int(match.score * 100)
            lines.append(f"**{snippet.name}** (match: {score_pct}%)")
            lines.append(f"  - Description: {snippet.description}")
            lines.append(f"  - MCP: {snippet.mcp}")
            if snippet.skill:
                lines.append(f"  - Skill: {snippet.skill}")
            lines.append("")

        lines.append("To use a snippet, reference it in your code or use its pattern.")
        return "\n".join(lines)

    async def _notify_status(self, status: ExecutionStatus):
        """Notify UI of status change."""
        if self._status_callback:
            await self._status_callback(status)

    def _build_system_prompt(self, user_message: str = "") -> str:
        """Build the full system prompt with tool index and matching snippets."""
        base_prompt = get_system_prompt()

        # Add compact tool index (500 tokens vs 15,000 for full schemas)
        tool_index = self.tool_discovery.get_index_json()

        # Add workspace state if exists
        workspace_info = self._get_workspace_info()

        # Add code library index
        library_info = self._get_library_info()

        # Find matching snippets for user's message (if provided)
        snippet_suggestions = ""
        if user_message:
            matches = self.find_matching_snippets(user_message, top_k=3)
            snippet_suggestions = self._format_snippet_suggestions(matches)

        full_prompt = f"""{base_prompt}

## Tool Index (Progressive Discovery)
{tool_index}

To discover specific tool schemas, use:
- `list_tools_in_category(category)` - List tool names in a category
- `get_tool_schema(tool_name)` - Get full schema for a tool

{library_info}
{snippet_suggestions}
{workspace_info}

## Current Context
- Vehicle: {self.current_vehicle_id or 'None selected'}
- Time: {datetime.now().isoformat()}
"""
        return full_prompt

    def _get_library_info(self) -> str:
        """Get information about the code library."""
        if not self._library_loaded:
            self.load_code_library()

        if not self.code_library._index:
            return ""

        return self.code_library.format_for_prompt(max_snippets=10)

    def _get_workspace_info(self) -> str:
        """Get information about workspace files."""
        workspace = self.config.workspace_path
        if not os.path.exists(workspace):
            return ""

        files = []
        try:
            for f in os.listdir(workspace):
                filepath = os.path.join(workspace, f)
                if os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    files.append(f"- {f} ({size} bytes)")
        except Exception:
            return ""

        if not files:
            return ""

        return f"""## Workspace Files
{chr(10).join(files)}

Use `load_from_workspace(filename)` to load saved data.
"""

    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract Python code blocks from text."""
        # Match ```python ... ``` blocks
        pattern = r"```python\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return matches

    def _format_history_for_api(self) -> List[Dict[str, str]]:
        """Format conversation history for OpenAI API."""
        messages = []

        for msg in self.conversation_history[-10:]:  # Keep last 10 messages
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })

            # Add execution results as assistant context
            if msg.execution_result:
                result_content = f"[Code Execution Result]\nSuccess: {msg.execution_result.success}\nOutput:\n{msg.execution_result.stdout[:2000]}"
                if msg.execution_result.stderr:
                    result_content += f"\nErrors:\n{msg.execution_result.stderr[:500]}"
                messages.append({
                    "role": "assistant",
                    "content": result_content,
                })

        return messages

    async def process_message(
        self,
        message: str,
        history: Optional[List[Tuple[str, str]]] = None,
    ) -> AgentResponse:
        """
        Process a user message through the agentic loop.

        Args:
            message: User input message
            history: Optional chat history from Gradio

        Returns:
            AgentResponse with message and execution details
        """
        # Track user message (legacy tracker)
        if self.tracker:
            self.tracker.log_user_message(message)

        # Add to conversation history
        self.conversation_history.append(ConversationMessage(
            role="user",
            content=message,
        ))

        # Build messages for API with snippet matching
        api_messages = [
            {"role": "system", "content": self._build_system_prompt(message)},
        ]
        api_messages.extend(self._format_history_for_api())

        # Agentic loop
        response = AgentResponse(message="", iterations=0)

        for iteration in range(self.config.max_iterations):
            response.iterations = iteration + 1

            await self._notify_status(ExecutionStatus(
                state="running",
                message=f"Thinking... (iteration {iteration + 1})",
                progress=0.1 + (iteration * 0.15),
            ))

            # Call OpenAI with MLflow tracing
            try:
                # GPT-5 and o1/o3 reasoning models require special parameters
                is_reasoning_model = any(x in self.config.model.lower() for x in ["gpt-5", "o1", "o3"])

                api_params = {
                    "model": self.config.model,
                    "messages": api_messages,
                }

                if is_reasoning_model:
                    # Reasoning models use max_completion_tokens and require temperature=1
                    api_params["max_completion_tokens"] = max(self.config.max_tokens, 16000)
                else:
                    api_params["max_tokens"] = self.config.max_tokens
                    api_params["temperature"] = self.config.temperature

                # Wrap OpenAI call in MLflow span for tracing
                with mlflow.start_span(name="openai_chat_completion") as span:
                    span.set_inputs({"model": api_params["model"], "message_count": len(api_params["messages"])})
                    # Set trace metadata for session grouping
                    try:
                        mlflow.update_current_trace(
                            metadata={
                                "mlflow.trace.user": self.user_id,
                                "mlflow.trace.session": self.session_id,
                                "vehicle_id": self.current_vehicle_id or "none",
                            }
                        )
                    except Exception:
                        pass

                    completion = await self.client.chat.completions.create(**api_params)
                    span.set_outputs({"finish_reason": completion.choices[0].finish_reason})

                assistant_message = completion.choices[0].message.content

            except Exception as e:
                response.error = f"API Error: {str(e)}"
                response.message = f"Sorry, I encountered an error: {str(e)}"
                return response

            # Extract code blocks
            code_blocks = self._extract_code_blocks(assistant_message)

            if not code_blocks:
                # No code to execute - this is the final response
                response.message = assistant_message
                response.quick_actions = self._extract_quick_actions(assistant_message)
                break

            # Execute code blocks
            response.code_blocks.extend(code_blocks)

            for i, code in enumerate(code_blocks):
                await self._notify_status(ExecutionStatus(
                    state="running",
                    message=f"Executing code block {i + 1}/{len(code_blocks)}...",
                    code_preview=code[:100] + "..." if len(code) > 100 else code,
                    progress=0.3 + (iteration * 0.15),
                ))

                # Execute in sandbox
                result = await self.code_executor.execute(code)
                response.execution_results.append(result)

                # Store in conversation
                self.conversation_history.append(ConversationMessage(
                    role="assistant",
                    content=assistant_message,
                    code_executed=code,
                    execution_result=result,
                ))

                # Add execution result to API messages
                api_messages.append({
                    "role": "assistant",
                    "content": assistant_message,
                })

                if result.success:
                    api_messages.append({
                        "role": "user",
                        "content": f"[Code Execution Successful]\nOutput:\n```\n{result.stdout[:3000]}\n```\n\n"
                                   "Now provide your response explaining these results to the user. "
                                   "Respond with plain text - do NOT generate more code blocks.",
                    })
                else:
                    # Use error context for retry
                    error_context = self.code_executor.get_error_context(result, code)
                    api_messages.append({
                        "role": "user",
                        "content": error_context,
                    })

        # Ensure we have a response
        if not response.message:
            response.message = "I completed the task but couldn't generate a summary. Please check the execution results."

        # Log response
        if self.tracker:
            self.tracker.log_assistant_response(response.message)

        # Store final response
        self.conversation_history.append(ConversationMessage(
            role="assistant",
            content=response.message,
        ))

        await self._notify_status(ExecutionStatus(
            state="completed",
            message="Response ready",
            progress=1.0,
        ))

        return response

    async def stream_message(
        self,
        message: str,
        history: Optional[List[Tuple[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream response to user (for Gradio streaming interface).

        Args:
            message: User input message
            history: Optional chat history

        Yields:
            Response chunks for streaming display
        """
        yield "Thinking..."

        response = await self.process_message(message, history)

        if response.error:
            yield f"Error: {response.error}"
            return

        # Stream the final message
        # For now, yield the complete message (can be enhanced for true streaming)
        yield response.message

        # Add execution summary if code was run
        if response.code_blocks:
            yield f"\n\n---\n*Executed {len(response.code_blocks)} code block(s) in {response.iterations} iteration(s)*"

    def _extract_quick_actions(self, message: str) -> List[str]:
        """Extract suggested quick actions from response - returns complete prompts."""
        # Look for suggested actions in the message
        actions = []

        # Pattern: "You can:" followed by list items
        if "you can" in message.lower():
            # Try to extract bullet points
            lines = message.split("\n")
            for line in lines:
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    action = line.strip().lstrip("-*").strip()
                    if len(action) < 80:  # Reasonable action length
                        actions.append(action)

        # Default contextual actions if none found (complete prompts)
        if not actions:
            # Analyze message to provide contextual suggestions
            msg_lower = message.lower()
            if "checkpoint" in msg_lower and "created" in msg_lower:
                actions = [
                    "Check for gaps in my checkpoints",
                    "Show me all checkpoints",
                    "Add another checkpoint"
                ]
            elif "vehicle" in msg_lower and "created" in msg_lower:
                actions = [
                    "Add a checkpoint for this vehicle",
                    "List all my vehicles",
                    "Show vehicle details"
                ]
            elif "gap" in msg_lower:
                actions = [
                    "Reconstruct trips from the gaps",
                    "Add a checkpoint to fill the gap",
                    "Show me the gap details"
                ]
            elif "trip" in msg_lower:
                actions = [
                    "Generate a monthly report",
                    "Show all trips this month",
                    "Check for more gaps"
                ]
            elif "report" in msg_lower:
                actions = [
                    "Show trips included in the report",
                    "Generate report for a different period",
                    "List all my checkpoints"
                ]
            else:
                actions = [
                    "Add a new checkpoint",
                    "Check for gaps in my mileage",
                    "Generate a monthly report"
                ]

        return actions[:3]  # Max 3 actions for the 3 buttons

    def set_vehicle(self, vehicle_id: str):
        """Set current vehicle context."""
        self.current_vehicle_id = vehicle_id

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation."""
        if not self.conversation_history:
            return "No conversation yet."

        user_msgs = sum(1 for m in self.conversation_history if m.role == "user")
        assistant_msgs = sum(1 for m in self.conversation_history if m.role == "assistant")
        code_executions = sum(1 for m in self.conversation_history if m.code_executed)

        return f"Conversation: {user_msgs} user messages, {assistant_msgs} responses, {code_executions} code executions"


# Convenience function for quick agent creation
def create_agent(
    adapters: Dict[str, Any],
    workspace_path: str = "/app/workspace",
    model: str = "gpt-4o-mini",
) -> CarLogAgent:
    """
    Create a Car Log Agent with default settings.

    Args:
        adapters: MCP adapter dictionary
        workspace_path: Path for workspace files
        model: OpenAI model to use

    Returns:
        Configured CarLogAgent instance
    """
    config = AgentConfig(
        model=model,
        workspace_path=workspace_path,
    )
    return CarLogAgent(adapters=adapters, config=config)
