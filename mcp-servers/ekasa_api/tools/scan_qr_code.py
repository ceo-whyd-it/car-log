"""
MCP Tool: Extract QR code from receipt image or PDF.
"""

from typing import Dict
import logging
from pathlib import Path

from ..qr_scanner import scan_qr_universal
from ..exceptions import QRDetectionError

logger = logging.getLogger(__name__)


async def scan_qr_code(image_path: str) -> Dict:
    """
    MCP tool: Extract QR code from receipt image or PDF.

    Supports:
    - Image formats: PNG, JPG, JPEG
    - PDF documents (with multi-scale detection)

    Args:
        image_path: Absolute path to receipt file

    Returns:
        {
            "success": bool,
            "receipt_id": str,
            "confidence": float,
            "detection_scale": float,
            "format": str,
            "error": str | None
        }
    """
    try:
        # Validate file exists
        file_path = Path(image_path)
        if not file_path.exists():
            logger.error(f"File not found: {image_path}")
            return {
                "success": False,
                "error": f"File not found: {image_path}"
            }

        # Scan QR code
        logger.info(f"Scanning QR code from: {image_path}")
        result = scan_qr_universal(str(file_path))

        # Determine format
        ext = file_path.suffix.lower()
        file_format = 'pdf' if ext == '.pdf' else 'image'

        logger.info(f"QR scan successful: {result['receipt_id'][:30]}...")

        return {
            "success": True,
            "receipt_id": result['receipt_id'],
            "confidence": result['confidence'],
            "detection_scale": result['detection_scale'],
            "format": file_format,
            "error": None
        }

    except QRDetectionError as e:
        logger.error(f"QR detection failed: {e}")
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
