"""
MCP Tool: Fetch receipt data from e-Kasa API.
"""

from typing import Dict
import logging

from ..api_client import fetch_receipt_with_retry
from ..fuel_detector import extract_fuel_data
from ..exceptions import (
    APITimeoutError,
    ReceiptNotFoundError,
    EKasaError
)

logger = logging.getLogger(__name__)


async def fetch_receipt_data(
    receipt_id: str,
    timeout_seconds: int = 60
) -> Dict:
    """
    MCP tool: Fetch receipt data from e-Kasa API.

    Args:
        receipt_id: e-Kasa receipt identifier from QR code
        timeout_seconds: Request timeout (default: 60s, max: 60s)

    Returns:
        {
            "success": bool,
            "receipt_data": {
                "receipt_id": str,
                "vendor_name": str,
                "vendor_tax_id": str,
                "timestamp": str,
                "total_amount_eur": float,
                "vat_amount_eur": float,
                "items": [...]
            },
            "fuel_items": [...],
            "error": str | None
        }
    """
    try:
        # Validate timeout
        if timeout_seconds > 60:
            logger.warning(f"Timeout capped at 60s (requested: {timeout_seconds}s)")
            timeout_seconds = 60

        # Fetch receipt from API
        logger.info(f"Fetching receipt from e-Kasa API: {receipt_id}")
        raw_data = fetch_receipt_with_retry(receipt_id, timeout=timeout_seconds)

        # Parse receipt data
        organization = raw_data.get('organization', {})
        receipt_data = {
            "receipt_id": raw_data.get('receiptId'),
            "vendor_name": organization.get('organizationName'),
            "vendor_tax_id": organization.get('ico'),
            "timestamp": raw_data.get('createDate'),
            "total_amount_eur": float(raw_data.get('totalPrice', 0)),
            "vat_amount_eur": float(raw_data.get('totalVat', 0)),
            "items": raw_data.get('items', [])
        }

        # Extract fuel items
        fuel_items = []
        try:
            fuel_data = extract_fuel_data(raw_data)
            fuel_items = [fuel_data]
            logger.info(f"Fuel item detected: {fuel_data['fuel_type']} - {fuel_data['quantity_liters']}L")
        except ValueError as e:
            # No fuel items found
            logger.warning(f"No fuel items found: {e}")

        return {
            "success": True,
            "receipt_data": receipt_data,
            "fuel_items": fuel_items,
            "error": None
        }

    except ReceiptNotFoundError as e:
        logger.error(f"Receipt not found: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    except APITimeoutError as e:
        logger.error(f"API timeout: {e}")
        return {
            "success": False,
            "error": f"Request timed out after {timeout_seconds}s. e-Kasa API may be slow."
        }
    except EKasaError as e:
        logger.error(f"e-Kasa API error: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Internal error: {str(e)}"
        }
