"""
DSPy module for intelligent trip reconstruction.

Given a gap between checkpoints and available templates,
proposes trips to fill the gap using:
- Template matching (GPS distance + address similarity)
- Historical patterns (typical days, purposes)
- Distance optimization (minimize remainder)
"""

from typing import List, Optional
from dataclasses import dataclass

import dspy


@dataclass
class ProposedTrip:
    """A proposed trip to fill part of a gap."""
    template_name: str
    template_id: str
    from_location: str
    to_location: str
    distance_km: float
    purpose: str
    confidence: float


@dataclass
class ReconstructionResult:
    """Result of trip reconstruction."""
    proposed_trips: List[ProposedTrip]
    remainder_km: float
    confidence_score: float
    reasoning: str


class TripReconstructionSignature(dspy.Signature):
    """Propose trips to fill a gap between checkpoints."""

    gap_data: str = dspy.InputField(
        desc="JSON string with gap info: start_checkpoint, end_checkpoint, distance_km, date_range"
    )
    available_templates: str = dspy.InputField(
        desc="JSON array of available trip templates with names, distances, GPS coords"
    )
    matched_templates: str = dspy.InputField(
        desc="JSON array of template matches with GPS/address match scores"
    )

    proposed_trips: str = dspy.OutputField(
        desc="JSON array of proposed trips: [{template_name, template_id, distance_km, purpose, confidence}]"
    )
    remainder_km: float = dspy.OutputField(
        desc="Remaining kilometers not covered by proposed trips"
    )
    confidence_score: float = dspy.OutputField(
        desc="Overall confidence in the reconstruction (0.0 to 1.0)"
    )
    reasoning: str = dspy.OutputField(
        desc="Explanation of why these trips were selected"
    )


class TripReconstructor(dspy.Module):
    """
    DSPy module for trip reconstruction.

    Uses chain-of-thought reasoning to:
    1. Analyze the gap (distance, date range)
    2. Match templates based on GPS proximity and address similarity
    3. Select trips that minimize remainder
    4. Consider historical patterns (typical days)
    """

    def __init__(self):
        """Initialize the reconstructor with chain-of-thought reasoning."""
        super().__init__()
        self.reconstructor = dspy.ChainOfThought(TripReconstructionSignature)

    def forward(
        self,
        gap_data: str,
        available_templates: str,
        matched_templates: str,
    ) -> ReconstructionResult:
        """
        Propose trips to fill a gap.

        Args:
            gap_data: JSON string with gap information
            available_templates: JSON string of available templates
            matched_templates: JSON string of pre-matched templates with scores

        Returns:
            ReconstructionResult with proposed trips and confidence
        """
        import json

        # Call the DSPy chain-of-thought predictor
        result = self.reconstructor(
            gap_data=gap_data,
            available_templates=available_templates,
            matched_templates=matched_templates,
        )

        # Parse proposed trips from JSON string
        try:
            trips_data = json.loads(result.proposed_trips)
            proposed_trips = [
                ProposedTrip(
                    template_name=t.get("template_name", "Unknown"),
                    template_id=t.get("template_id", ""),
                    from_location=t.get("from_location", ""),
                    to_location=t.get("to_location", ""),
                    distance_km=float(t.get("distance_km", 0)),
                    purpose=t.get("purpose", "Business"),
                    confidence=float(t.get("confidence", 0.5)),
                )
                for t in trips_data
            ]
        except (json.JSONDecodeError, TypeError):
            proposed_trips = []

        return ReconstructionResult(
            proposed_trips=proposed_trips,
            remainder_km=float(result.remainder_km),
            confidence_score=float(result.confidence_score),
            reasoning=result.reasoning,
        )

    def reconstruct_sync(
        self,
        gap_data: str,
        available_templates: str,
        matched_templates: str,
    ) -> ReconstructionResult:
        """Synchronous wrapper for reconstruction."""
        return self.forward(gap_data, available_templates, matched_templates)
