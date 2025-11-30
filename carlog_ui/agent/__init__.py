"""
Car Log Agent Module

Implements the "Code Execution with MCP" pattern from Anthropic's engineering article
for efficient LLM-powered tool selection with 98%+ token reduction.

Components:
- system_prompt: Defines the agent's role and capabilities
- tool_discovery: Progressive tool discovery (on-demand loading)
- code_executor: Sandboxed code execution via Docker subprocess
- agent: Main agentic loop with retry logic
- workspace: Session and state management

Article Reference: https://www.anthropic.com/engineering/code-execution-with-mcp
"""

from .system_prompt import SYSTEM_PROMPT, get_system_prompt
from .tool_discovery import ToolDiscovery
from .code_executor import CodeExecutor, ExecutionResult
from .agent import CarLogAgent, AgentConfig
from .workspace import WorkspaceManager

__all__ = [
    "SYSTEM_PROMPT",
    "get_system_prompt",
    "ToolDiscovery",
    "CodeExecutor",
    "ExecutionResult",
    "CarLogAgent",
    "AgentConfig",
    "WorkspaceManager",
]
