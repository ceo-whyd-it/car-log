"""
DSPy module for checkpoint validation.

Validates checkpoint data before creation, checking for:
- Logical consistency (odometer increasing)
- Realistic values (fuel amounts, distances)
- Slovak tax compliance (VIN, driver name)
"""

from typing import List, Optional
from dataclasses import dataclass

import dspy


@dataclass
class ValidationResult:
    """Result of checkpoint validation."""
    valid: bool
    warnings: List[str]
    errors: List[str]
    reasoning: str


class CheckpointValidationSignature(dspy.Signature):
    """Validate a vehicle checkpoint for Slovak tax compliance."""

    checkpoint_data: str = dspy.InputField(
        desc="JSON string of the checkpoint being validated"
    )
    previous_checkpoint: str = dspy.InputField(
        desc="JSON string of the previous checkpoint (or 'null' if first)"
    )
    vehicle_info: str = dspy.InputField(
        desc="JSON string of vehicle information (fuel type, average efficiency)"
    )

    valid: bool = dspy.OutputField(
        desc="True if checkpoint passes all critical validations"
    )
    warnings: str = dspy.OutputField(
        desc="Comma-separated list of warnings (non-blocking issues)"
    )
    errors: str = dspy.OutputField(
        desc="Comma-separated list of errors (blocking issues)"
    )
    reasoning: str = dspy.OutputField(
        desc="Brief explanation of the validation logic"
    )


class CheckpointValidator(dspy.Module):
    """
    DSPy module for validating checkpoint data.

    Checks:
    - Odometer must be >= previous checkpoint
    - Distance since last checkpoint must be reasonable (< 2000 km)
    - Fuel amount must be reasonable (1-200 liters)
    - Date must be after previous checkpoint
    - GPS coordinates must be valid if provided
    """

    def __init__(self):
        """Initialize the validator with chain-of-thought reasoning."""
        super().__init__()
        self.validator = dspy.ChainOfThought(CheckpointValidationSignature)

    def forward(
        self,
        checkpoint_data: str,
        previous_checkpoint: Optional[str] = None,
        vehicle_info: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate checkpoint data.

        Args:
            checkpoint_data: JSON string of checkpoint to validate
            previous_checkpoint: JSON string of previous checkpoint (optional)
            vehicle_info: JSON string of vehicle info (optional)

        Returns:
            ValidationResult with valid flag, warnings, errors, and reasoning
        """
        # Call the DSPy chain-of-thought predictor
        result = self.validator(
            checkpoint_data=checkpoint_data,
            previous_checkpoint=previous_checkpoint or "null",
            vehicle_info=vehicle_info or "{}",
        )

        # Parse the outputs
        warnings = [w.strip() for w in result.warnings.split(",") if w.strip()]
        errors = [e.strip() for e in result.errors.split(",") if e.strip()]

        return ValidationResult(
            valid=result.valid,
            warnings=warnings,
            errors=errors,
            reasoning=result.reasoning,
        )

    def validate_sync(
        self,
        checkpoint_data: str,
        previous_checkpoint: Optional[str] = None,
        vehicle_info: Optional[str] = None,
    ) -> ValidationResult:
        """Synchronous wrapper for validation."""
        return self.forward(checkpoint_data, previous_checkpoint, vehicle_info)
