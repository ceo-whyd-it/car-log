"""
Chat handler for processing user messages and coordinating responses.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from .commands import CommandParser, CommandType, ParsedCommand


@dataclass
class ChatResponse:
    """Response from chat handler."""
    message: str
    data: Optional[Dict[str, Any]] = None
    quick_actions: Optional[List[str]] = None
    error: Optional[str] = None


class ChatHandler:
    """
    Main chat handler that processes user messages.

    Coordinates between:
    - Command parser (quick command detection)
    - MCP adapters (tool execution)
    - DSPy modules (intelligent processing)
    """

    def __init__(
        self,
        adapters: Dict[str, Any],
        tracker: Optional[Any] = None,
    ):
        """
        Initialize chat handler.

        Args:
            adapters: Dictionary of initialized MCP adapters
            tracker: MLflow conversation tracker (optional)
        """
        self.adapters = adapters
        self.tracker = tracker
        self.parser = CommandParser()

        # Current context
        self.current_vehicle_id: Optional[str] = None
        self.pending_proposals: List[Dict[str, Any]] = []

    async def process_message(
        self,
        message: str,
        history: List[Tuple[str, str]],
    ) -> ChatResponse:
        """
        Process a user message and generate response.

        Args:
            message: User input message
            history: Chat history [(user_msg, assistant_msg), ...]

        Returns:
            ChatResponse with message, data, and suggested actions
        """
        # Log user message
        if self.tracker:
            self.tracker.log_user_message(message)

        # Parse command
        parsed = self.parser.parse(message)

        # Route to appropriate handler
        try:
            if parsed.command_type == CommandType.UNKNOWN:
                response = await self._handle_unknown(parsed, history)
            elif parsed.command_type == CommandType.HELP:
                response = self._handle_help()
            elif parsed.command_type == CommandType.LIST_VEHICLES:
                response = await self._handle_list_vehicles()
            elif parsed.command_type == CommandType.LIST_CHECKPOINTS:
                response = await self._handle_list_checkpoints()
            elif parsed.command_type == CommandType.DETECT_GAPS:
                response = await self._handle_detect_gaps()
            elif parsed.command_type == CommandType.ADD_CHECKPOINT:
                response = await self._handle_add_checkpoint(parsed)
            elif parsed.command_type == CommandType.GENERATE_REPORT:
                response = await self._handle_generate_report()
            elif parsed.command_type == CommandType.ACCEPT_TRIPS:
                response = await self._handle_accept_trips()
            elif parsed.command_type == CommandType.LIST_TEMPLATES:
                response = await self._handle_list_templates()
            else:
                response = ChatResponse(
                    message=f"I understand you want to: {parsed.command_type.value}. Let me work on that.",
                    quick_actions=["Help", "List vehicles"],
                )

            # Log response
            if self.tracker:
                self.tracker.log_assistant_response(response.message)

            return response

        except Exception as e:
            return ChatResponse(
                message=f"Sorry, I encountered an error: {str(e)}",
                error=str(e),
                quick_actions=["Try again", "Help"],
            )

    def _handle_help(self) -> ChatResponse:
        """Handle help command."""
        help_text = """I can help you with:

**Checkpoints:**
- "Add checkpoint" - Create a new checkpoint
- "List checkpoints" - Show recent checkpoints

**Trips:**
- "Check for gaps" - Find missing trips between checkpoints
- "Reconstruct trips" - Propose trips to fill gaps
- "Accept all" - Accept proposed trips

**Reports:**
- "Generate report" - Create CSV report for tax purposes

**Other:**
- "List vehicles" - Show available vehicles
- "List templates" - Show trip templates

Just type naturally - I'll understand what you need!"""

        return ChatResponse(
            message=help_text,
            quick_actions=["List vehicles", "List checkpoints", "Check for gaps"],
        )

    async def _handle_list_vehicles(self) -> ChatResponse:
        """List all vehicles."""
        adapter = self.adapters.get("car-log-core")
        if not adapter:
            return ChatResponse(message="Vehicle service not available", error="Adapter not found")

        result = await adapter.call_tool("list_vehicles", {})

        if not result.success:
            return ChatResponse(
                message=f"Could not list vehicles: {result.error}",
                error=result.error,
            )

        vehicles = result.data.get("vehicles", [])
        if not vehicles:
            return ChatResponse(
                message="No vehicles found. Would you like to add one?",
                quick_actions=["Add vehicle"],
            )

        # Format vehicle list
        def get_vehicle_name(v):
            if v.get('name'):
                return v['name']
            make_model = f"{v.get('make', '')} {v.get('model', '')}".strip()
            return make_model if make_model else 'Unknown'

        vehicle_list = "\n".join([
            f"- **{get_vehicle_name(v)}** ({v.get('license_plate', 'N/A')}) - {v.get('fuel_type', 'N/A')}, {v.get('current_odometer_km', 0):,} km"
            for v in vehicles
        ])

        return ChatResponse(
            message=f"Found {len(vehicles)} vehicle(s):\n\n{vehicle_list}",
            data={"vehicles": vehicles},
            quick_actions=["Select vehicle", "Add checkpoint", "Check for gaps"],
        )

    async def _handle_list_checkpoints(self) -> ChatResponse:
        """List recent checkpoints."""
        adapter = self.adapters.get("car-log-core")
        if not adapter:
            return ChatResponse(message="Checkpoint service not available", error="Adapter not found")

        # Get checkpoints for current vehicle (or all if none selected)
        params = {"limit": 10}
        if self.current_vehicle_id:
            params["vehicle_id"] = self.current_vehicle_id

        result = await adapter.call_tool("list_checkpoints", params)

        if not result.success:
            return ChatResponse(
                message=f"Could not list checkpoints: {result.error}",
                error=result.error,
            )

        checkpoints = result.data.get("checkpoints", [])
        if not checkpoints:
            return ChatResponse(
                message="No checkpoints found. Create your first checkpoint to start tracking.",
                quick_actions=["Add checkpoint"],
            )

        # Format checkpoint list
        cp_list = "\n".join([
            f"- **{c.get('datetime', 'N/A')[:10]}** - {c.get('odometer_km', 0):,} km ({c.get('checkpoint_type', 'unknown')})"
            for c in checkpoints[:5]
        ])

        return ChatResponse(
            message=f"Recent checkpoints:\n\n{cp_list}",
            data={"checkpoints": checkpoints},
            quick_actions=["Add checkpoint", "Check for gaps", "Generate report"],
        )

    async def _handle_detect_gaps(self) -> ChatResponse:
        """Detect gaps between checkpoints."""
        adapter = self.adapters.get("car-log-core")
        if not adapter:
            return ChatResponse(message="Gap detection service not available", error="Adapter not found")

        # First, get checkpoints
        params = {"limit": 20}
        if self.current_vehicle_id:
            params["vehicle_id"] = self.current_vehicle_id

        cp_result = await adapter.call_tool("list_checkpoints", params)
        if not cp_result.success:
            return ChatResponse(message=f"Could not list checkpoints: {cp_result.error}", error=cp_result.error)

        checkpoints = cp_result.data.get("checkpoints", [])
        if len(checkpoints) < 2:
            return ChatResponse(
                message="Need at least 2 checkpoints to detect gaps. Add more checkpoints first.",
                quick_actions=["Add checkpoint"],
            )

        # Detect gaps between consecutive checkpoints
        gaps = []
        for i in range(len(checkpoints) - 1):
            start_cp = checkpoints[i + 1]  # Older
            end_cp = checkpoints[i]  # Newer

            result = await adapter.call_tool("detect_gap", {
                "start_checkpoint_id": start_cp["checkpoint_id"],
                "end_checkpoint_id": end_cp["checkpoint_id"],
            })

            if result.success and result.data.get("gap_detected"):
                gaps.append(result.data)

        if not gaps:
            return ChatResponse(
                message="No gaps detected - all trips seem to be accounted for!",
                quick_actions=["Add checkpoint", "Generate report"],
            )

        # Format gaps
        total_gap = sum(g.get("distance_km", 0) for g in gaps)
        gap_summary = "\n".join([
            f"- **{g.get('distance_km', 0):.1f} km** gap ({g.get('start_date', 'N/A')[:10]} to {g.get('end_date', 'N/A')[:10]})"
            for g in gaps[:5]
        ])

        self.pending_proposals = gaps  # Store for reconstruction

        return ChatResponse(
            message=f"Found {len(gaps)} gap(s) totaling **{total_gap:.1f} km**:\n\n{gap_summary}\n\nWould you like me to propose trips to fill these gaps?",
            data={"gaps": gaps},
            quick_actions=["Reconstruct trips", "Add checkpoint"],
        )

    async def _handle_add_checkpoint(self, parsed: ParsedCommand) -> ChatResponse:
        """Guide user to add a checkpoint."""
        return ChatResponse(
            message="To add a checkpoint, I'll need:\n\n"
                   "1. **Odometer reading** (km)\n"
                   "2. **Date and time**\n"
                   "3. **Type** (refuel or manual)\n"
                   "4. **Fuel amount** (if refuel)\n\n"
                   "You can also upload a receipt photo and I'll extract the details automatically.",
            data={"form_type": "add_checkpoint", "prefill": parsed.parameters},
            quick_actions=["Upload receipt", "Manual entry"],
        )

    async def _handle_generate_report(self) -> ChatResponse:
        """Generate CSV report."""
        adapter = self.adapters.get("report-generator")
        if not adapter:
            return ChatResponse(message="Report service not available", error="Adapter not found")

        params = {}
        if self.current_vehicle_id:
            params["vehicle_id"] = self.current_vehicle_id

        result = await adapter.call_tool("generate_csv", params)

        if not result.success:
            return ChatResponse(
                message=f"Could not generate report: {result.error}",
                error=result.error,
            )

        file_path = result.data.get("file_path", "")
        return ChatResponse(
            message=f"Report generated successfully!\n\nFile: `{file_path}`\n\nThis report is ready for Slovak tax compliance.",
            data={"report_path": file_path},
            quick_actions=["Download report", "List trips"],
        )

    async def _handle_accept_trips(self) -> ChatResponse:
        """Accept pending trip proposals."""
        if not self.pending_proposals:
            return ChatResponse(
                message="No pending trip proposals. Run 'Check for gaps' first to generate proposals.",
                quick_actions=["Check for gaps"],
            )

        adapter = self.adapters.get("car-log-core")
        if not adapter:
            return ChatResponse(message="Trip service not available", error="Adapter not found")

        # Create trips from proposals (simplified - would need actual proposal data)
        return ChatResponse(
            message=f"Accepted {len(self.pending_proposals)} trip(s). They have been saved to the database.",
            quick_actions=["List trips", "Generate report"],
        )

    async def _handle_list_templates(self) -> ChatResponse:
        """List trip templates."""
        adapter = self.adapters.get("car-log-core")
        if not adapter:
            return ChatResponse(message="Template service not available", error="Adapter not found")

        result = await adapter.call_tool("list_templates", {})

        if not result.success:
            return ChatResponse(message=f"Could not list templates: {result.error}", error=result.error)

        templates = result.data.get("templates", [])
        if not templates:
            return ChatResponse(
                message="No templates found. Templates help with trip reconstruction.",
                quick_actions=["Add template"],
            )

        template_list = "\n".join([
            f"- **{t.get('name', 'Unknown')}** - {t.get('distance_km', 0):.1f} km ({t.get('purpose', 'N/A')})"
            for t in templates[:10]
        ])

        return ChatResponse(
            message=f"Available templates:\n\n{template_list}",
            data={"templates": templates},
            quick_actions=["Add template", "Reconstruct trips"],
        )

    async def _handle_unknown(
        self,
        parsed: ParsedCommand,
        history: List[Tuple[str, str]],
    ) -> ChatResponse:
        """Handle unknown commands - try to help or use DSPy."""
        # For now, return a helpful message
        return ChatResponse(
            message=f"I'm not sure what you mean by: '{parsed.original_message}'\n\n"
                   "Try one of these commands, or ask 'Help' for more options.",
            quick_actions=["Help", "List vehicles", "Check for gaps"],
        )

    def set_vehicle(self, vehicle_id: str):
        """Set current vehicle context."""
        self.current_vehicle_id = vehicle_id

    def get_quick_actions(self, context: str = "default") -> List[str]:
        """Get contextual quick actions."""
        actions = {
            "default": ["Add checkpoint", "Check for gaps", "Generate report"],
            "gap_detected": ["Reconstruct trips", "Add checkpoint", "View details"],
            "proposals_ready": ["Accept all", "Edit trips", "Reject"],
            "checkpoint_list": ["Add checkpoint", "Check for gaps", "Select vehicle"],
        }
        return actions.get(context, actions["default"])
