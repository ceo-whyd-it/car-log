"""
Multi-scale QR code scanner for images and PDFs.

Supports PNG, JPG, JPEG images and PDF documents with automatic multi-scale detection
for small or low-resolution QR codes.
"""

from pdf2image import convert_from_path
from pyzbar.pyzbar import decode
from PIL import Image
from pathlib import Path
from typing import Dict
import logging

from .exceptions import QRDetectionError

logger = logging.getLogger(__name__)


def scan_image_qr(image_path: str) -> str:
    """
    Scan single image for QR code.

    Args:
        image_path: Path to image file (PNG, JPG, JPEG)

    Returns:
        QR code data (receipt ID)

    Raises:
        QRDetectionError: If no QR code found or scan error
    """
    try:
        logger.debug(f"Scanning image: {image_path}")
        image = Image.open(image_path)
        decoded = decode(image)

        if decoded:
            receipt_id = decoded[0].data.decode('utf-8')
            logger.info(f"QR code found in image: {receipt_id[:30]}...")
            return receipt_id

        raise QRDetectionError(f'QR code not found in image: {image_path}')

    except QRDetectionError:
        raise
    except Exception as e:
        logger.error(f"Error scanning image: {e}")
        raise QRDetectionError(f"Error scanning image: {str(e)}")


def scan_pdf_qr_multi_scale(pdf_path: str) -> Dict:
    """
    Scan PDF for QR codes using multi-scale detection.

    Tries scales: 1.0x, 2.0x, 3.0x
    Stops on first successful detection.

    Args:
        pdf_path: Path to PDF file

    Returns:
        {
            'receipt_id': str,
            'detection_scale': float,
            'page_number': int,
            'confidence': float
        }

    Raises:
        QRDetectionError: If no QR code found at any scale
    """
    scales = [1.0, 2.0, 3.0]

    try:
        logger.info(f"Converting PDF to images: {pdf_path}")
        # Convert PDF to images (one per page)
        images = convert_from_path(pdf_path, dpi=200)
        logger.info(f"Converted PDF to {len(images)} page(s)")

        for page_num, image in enumerate(images, start=1):
            logger.debug(f"Scanning page {page_num}...")

            for scale in scales:
                logger.debug(f"Trying scale {scale}x...")

                # Resize image to scale
                width, height = image.size
                scaled_img = image.resize(
                    (int(width * scale), int(height * scale)),
                    Image.LANCZOS
                )

                # Try QR detection
                decoded = decode(scaled_img)

                if decoded:
                    receipt_id = decoded[0].data.decode('utf-8')
                    logger.info(
                        f"QR found: page={page_num}, scale={scale}x, "
                        f"id={receipt_id[:30]}..."
                    )

                    return {
                        'receipt_id': receipt_id,
                        'detection_scale': scale,
                        'page_number': page_num,
                        'confidence': 1.0  # pyzbar doesn't provide confidence
                    }

        raise QRDetectionError('QR code not found in PDF at any scale (1x, 2x, 3x)')

    except QRDetectionError:
        raise
    except Exception as e:
        logger.error(f"Error scanning PDF: {e}")
        raise QRDetectionError(f"Error scanning PDF: {str(e)}")


def scan_qr_universal(file_path: str) -> Dict:
    """
    Universal QR scanner supporting images and PDFs.

    Args:
        file_path: Path to image or PDF file

    Returns:
        {
            'receipt_id': str,
            'detection_scale': float,
            'page_number': int,
            'confidence': float
        }

    Raises:
        QRDetectionError: If QR code not found or unsupported format
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == '.pdf':
        return scan_pdf_qr_multi_scale(file_path)
    elif ext in ['.png', '.jpg', '.jpeg']:
        receipt_id = scan_image_qr(file_path)
        return {
            'receipt_id': receipt_id,
            'detection_scale': 1.0,
            'page_number': 1,
            'confidence': 1.0
        }
    else:
        raise QRDetectionError(f'Unsupported file format: {ext}')
