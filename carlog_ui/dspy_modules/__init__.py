"""
DSPy modules for intelligent trip reconstruction and validation.

Uses OpenAI GPT-4o-mini for:
- Checkpoint validation
- Trip reconstruction from gaps
- Fuel item detection
"""

from .config import configure_dspy, get_lm
from .checkpoint_validator import CheckpointValidator
from .trip_reconstructor import TripReconstructor
from .fuel_item_detector import FuelItemDetector

__all__ = [
    "configure_dspy",
    "get_lm",
    "CheckpointValidator",
    "TripReconstructor",
    "FuelItemDetector",
]
