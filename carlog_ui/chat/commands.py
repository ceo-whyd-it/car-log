"""
Command parser for chat messages.

Recognizes commands like:
- "add checkpoint" / "create checkpoint"
- "show checkpoints" / "list checkpoints"
- "check for gaps" / "detect gaps"
- "reconstruct trips"
- "generate report"
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any


class CommandType(Enum):
    """Types of recognized commands."""
    # Checkpoint commands
    ADD_CHECKPOINT = "add_checkpoint"
    LIST_CHECKPOINTS = "list_checkpoints"
    SHOW_CHECKPOINT = "show_checkpoint"

    # Gap/Trip commands
    DETECT_GAPS = "detect_gaps"
    RECONSTRUCT_TRIPS = "reconstruct_trips"
    ACCEPT_TRIPS = "accept_trips"
    REJECT_TRIPS = "reject_trips"

    # Template commands
    ADD_TEMPLATE = "add_template"
    LIST_TEMPLATES = "list_templates"

    # Report commands
    GENERATE_REPORT = "generate_report"

    # Vehicle commands
    LIST_VEHICLES = "list_vehicles"
    SELECT_VEHICLE = "select_vehicle"

    # General
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    """Result of parsing a user message."""
    command_type: CommandType
    parameters: Dict[str, Any]
    original_message: str
    confidence: float = 1.0


class CommandParser:
    """
    Parse user messages to identify commands and extract parameters.

    Uses regex patterns for common command phrases.
    Falls back to UNKNOWN for complex queries (let DSPy handle).
    """

    # Command patterns (regex -> CommandType)
    PATTERNS = [
        # Checkpoint commands
        (r"\b(add|create|new)\s+(checkpoint|refuel)\b", CommandType.ADD_CHECKPOINT),
        (r"\b(show|list|display)\s+(checkpoints?|refuels?)\b", CommandType.LIST_CHECKPOINTS),
        (r"\bcheckpoint\s+details?\b", CommandType.SHOW_CHECKPOINT),

        # Gap/Trip commands
        (r"\b(check|detect|find|show)\s+(for\s+)?(gaps?|missing)\b", CommandType.DETECT_GAPS),
        (r"\b(reconstruct|rebuild|fill)\s+(trips?|gaps?)\b", CommandType.RECONSTRUCT_TRIPS),
        (r"\b(accept|approve|confirm)\s+(all\s+)?(trips?|proposals?)\b", CommandType.ACCEPT_TRIPS),
        (r"\b(reject|decline|cancel)\s+(trips?|proposals?)\b", CommandType.REJECT_TRIPS),

        # Template commands
        (r"\b(add|create|new)\s+template\b", CommandType.ADD_TEMPLATE),
        (r"\b(show|list|display)\s+templates?\b", CommandType.LIST_TEMPLATES),

        # Report commands
        (r"\b(generate|create|export)\s+(csv\s+)?report\b", CommandType.GENERATE_REPORT),
        (r"\bexport\s+(to\s+)?csv\b", CommandType.GENERATE_REPORT),

        # Vehicle commands
        (r"\b(show|list|display|check)\s+(vehicles?|existing|cars?)\b", CommandType.LIST_VEHICLES),
        (r"\bexisting\s+(vehicles?|cars?)\b", CommandType.LIST_VEHICLES),
        (r"\b(select|choose|switch|use)\s+vehicle\b", CommandType.SELECT_VEHICLE),

        # Help
        (r"\b(help|what can you do|commands?)\b", CommandType.HELP),
    ]

    def parse(self, message: str) -> ParsedCommand:
        """
        Parse a user message to identify command and parameters.

        Args:
            message: User input message

        Returns:
            ParsedCommand with identified type and extracted parameters
        """
        message_lower = message.lower().strip()

        # Try each pattern
        for pattern, command_type in self.PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                parameters = self._extract_parameters(message, command_type)
                return ParsedCommand(
                    command_type=command_type,
                    parameters=parameters,
                    original_message=message,
                    confidence=0.9,
                )

        # No pattern matched - unknown command
        return ParsedCommand(
            command_type=CommandType.UNKNOWN,
            parameters={},
            original_message=message,
            confidence=0.5,
        )

    def _extract_parameters(
        self,
        message: str,
        command_type: CommandType
    ) -> Dict[str, Any]:
        """
        Extract parameters from message based on command type.

        Args:
            message: Original message
            command_type: Identified command type

        Returns:
            Dictionary of extracted parameters
        """
        params = {}

        # Extract dates
        date_match = re.search(
            r"\b(\d{1,2}[./]\d{1,2}(?:[./]\d{2,4})?|\w+\s+\d{1,2})\b",
            message
        )
        if date_match:
            params["date"] = date_match.group(1)

        # Extract odometer values
        odo_match = re.search(r"\b(\d{1,3}[,.]?\d{3})\s*(?:km)?\b", message)
        if odo_match:
            params["odometer"] = int(odo_match.group(1).replace(",", "").replace(".", ""))

        # Extract fuel amounts
        fuel_match = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:liters?|l)\b", message, re.IGNORECASE)
        if fuel_match:
            params["fuel_liters"] = float(fuel_match.group(1).replace(",", "."))

        # Extract vehicle references
        vehicle_match = re.search(r"\b([A-Z]{2}-\d{3}[A-Z]{2})\b", message)
        if vehicle_match:
            params["vehicle_plate"] = vehicle_match.group(1)

        return params


# Singleton instance
_parser: Optional[CommandParser] = None


def get_parser() -> CommandParser:
    """Get command parser singleton."""
    global _parser
    if _parser is None:
        _parser = CommandParser()
    return _parser
