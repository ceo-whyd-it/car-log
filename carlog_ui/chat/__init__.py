"""
Chat assistant for Car Log.

Handles:
- User message processing
- Command parsing
- DSPy module routing
"""

from .handler import ChatHandler
from .commands import CommandParser

__all__ = ["ChatHandler", "CommandParser"]
