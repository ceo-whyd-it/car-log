"""
Slovak fuel item detection from e-Kasa receipt data.

Detects fuel types using Slovak naming patterns.
"""

import re
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Slovak fuel name patterns
FUEL_PATTERNS = {
    'Diesel': [
        r'(?i)diesel',
        r'(?i)nafta',
        r'(?i)motorová\s+nafta'
    ],
    'Gasoline_95': [
        r'(?i)natural\s*95',
        r'(?i)ba\s*95',
        r'(?i)benzín\s*95'
    ],
    'Gasoline_98': [
        r'(?i)natural\s*98',
        r'(?i)ba\s*98',
        r'(?i)benzín\s*98'
    ],
    'LPG': [
        r'(?i)lpg',
        r'(?i)autoplyn'
    ],
    'CNG': [
        r'(?i)cng',
        r'(?i)zemný\s+plyn'
    ]
}


def detect_fuel_type(item_name: str) -> Optional[str]:
    """
    Detect fuel type from Slovak item name.

    Args:
        item_name: Item description from receipt

    Returns:
        Fuel type string or None if not fuel
    """
    for fuel_type, patterns in FUEL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, item_name):
                logger.debug(f"Detected fuel type {fuel_type} from name: {item_name}")
                return fuel_type
    return None


def extract_fuel_data(receipt_data: dict) -> Dict:
    """
    Extract fuel purchase data from e-Kasa receipt.

    Args:
        receipt_data: Raw e-Kasa API response

    Returns:
        Dictionary with fuel data:
        {
            'fuel_type': str,
            'quantity_liters': float,
            'price_per_liter': float,
            'total_price': float,
            'vat_amount': float,
            'vat_rate': float,
            'item_name': str
        }

    Raises:
        ValueError: If no fuel items found
    """
    items = receipt_data.get('items', [])

    for item in items:
        item_name = item.get('name', '')
        fuel_type = detect_fuel_type(item_name)

        if fuel_type:
            logger.info(f"Found fuel item: {fuel_type} - {item_name}")

            return {
                'fuel_type': fuel_type,
                'quantity_liters': float(item.get('quantity', 0)),
                'price_per_liter': float(item.get('unitPrice', 0)),
                'total_price': float(item.get('totalPrice', 0)),
                'vat_amount': float(item.get('vatAmount', 0)),
                'vat_rate': float(item.get('vatRate', 0)),
                'item_name': item_name
            }

    raise ValueError('No fuel items found in receipt')
