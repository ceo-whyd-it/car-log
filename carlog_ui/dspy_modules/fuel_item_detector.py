"""
DSPy module for fuel item detection in receipts.

Identifies fuel items from Slovak e-Kasa receipt line items,
distinguishing fuel from other purchases (snacks, car wash, etc.).
"""

from typing import List
from dataclasses import dataclass

import dspy


@dataclass
class FuelItem:
    """A detected fuel item from a receipt."""
    item_name: str
    fuel_type: str  # Diesel, Gasoline_95, Gasoline_98, LPG, CNG
    quantity_liters: float
    price_per_liter: float
    total_price: float
    confidence: float


@dataclass
class FuelDetectionResult:
    """Result of fuel item detection."""
    fuel_items: List[FuelItem]
    non_fuel_items: List[str]
    reasoning: str


class FuelDetectionSignature(dspy.Signature):
    """Identify fuel items from receipt line items."""

    receipt_items: str = dspy.InputField(
        desc="JSON array of receipt line items: [{name, quantity, unit, price, total}]"
    )
    vendor_name: str = dspy.InputField(
        desc="Name of the vendor (gas station)"
    )

    fuel_items: str = dspy.OutputField(
        desc="JSON array of fuel items: [{item_name, fuel_type, quantity_liters, price_per_liter, total_price, confidence}]"
    )
    non_fuel_items: str = dspy.OutputField(
        desc="Comma-separated list of non-fuel item names"
    )
    reasoning: str = dspy.OutputField(
        desc="Explanation of how fuel items were identified"
    )


class FuelItemDetector(dspy.Module):
    """
    DSPy module for detecting fuel items in receipts.

    Uses knowledge of Slovak fuel naming conventions:
    - Diesel: "nafta", "motorová nafta", "diesel"
    - Gasoline 95: "natural 95", "BA 95", "benzín 95"
    - Gasoline 98: "natural 98", "BA 98", "benzín 98"
    - LPG: "lpg", "autoplyn"
    - CNG: "cng", "zemný plyn"
    """

    def __init__(self):
        """Initialize the detector with chain-of-thought reasoning."""
        super().__init__()
        self.detector = dspy.ChainOfThought(FuelDetectionSignature)

    def forward(
        self,
        receipt_items: str,
        vendor_name: str = "",
    ) -> FuelDetectionResult:
        """
        Detect fuel items from receipt line items.

        Args:
            receipt_items: JSON string of receipt line items
            vendor_name: Name of the gas station vendor

        Returns:
            FuelDetectionResult with fuel items, non-fuel items, and reasoning
        """
        import json

        # Call the DSPy chain-of-thought predictor
        result = self.detector(
            receipt_items=receipt_items,
            vendor_name=vendor_name or "Unknown",
        )

        # Parse fuel items from JSON string
        try:
            fuel_data = json.loads(result.fuel_items)
            fuel_items = [
                FuelItem(
                    item_name=f.get("item_name", ""),
                    fuel_type=f.get("fuel_type", "Unknown"),
                    quantity_liters=float(f.get("quantity_liters", 0)),
                    price_per_liter=float(f.get("price_per_liter", 0)),
                    total_price=float(f.get("total_price", 0)),
                    confidence=float(f.get("confidence", 0.5)),
                )
                for f in fuel_data
            ]
        except (json.JSONDecodeError, TypeError):
            fuel_items = []

        # Parse non-fuel items
        non_fuel_items = [
            item.strip()
            for item in result.non_fuel_items.split(",")
            if item.strip()
        ]

        return FuelDetectionResult(
            fuel_items=fuel_items,
            non_fuel_items=non_fuel_items,
            reasoning=result.reasoning,
        )

    def detect_sync(
        self,
        receipt_items: str,
        vendor_name: str = "",
    ) -> FuelDetectionResult:
        """Synchronous wrapper for detection."""
        return self.forward(receipt_items, vendor_name)
