# e-Kasa API Implementation Guide

**Version:** 1.0
**Date:** 2025-11-18
**Status:** Based on blockovac-next repository analysis

---

## Overview

This guide provides detailed implementation instructions for integrating the Slovak e-Kasa receipt API into the car-log MCP server.

**Key Findings:**
- Public endpoint (no API key required)
- Response time: 5-30 seconds typically
- No rate limiting observed
- Extended timeout required: 60 seconds
- QR code detection requires multi-scale approach for PDFs

---

## e-Kasa API Endpoint

### Base URL
```
https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/{receipt_id}
```

### Authentication
**None required** - Public endpoint provided by Financial Administration of Slovak Republic

### Request Format

**HTTP Method:** GET

**Headers:**
```
Accept: application/json
```

**Parameters:**
- `{receipt_id}`: e-Kasa receipt identifier from QR code

### Response Time
- **Typical:** 5-30 seconds
- **Maximum observed:** 45 seconds
- **Recommended timeout:** 60 seconds

---

## Example Request/Response

### Request
```bash
curl -X GET \
  "https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/O-E182401234567890123456789" \
  -H "Accept: application/json"
```

### Response (Success - 200 OK)
```json
{
  "receiptId": "O-E182401234567890123456789",
  "createDate": "2025-11-18T14:30:00Z",
  "amount": 65.50,
  "organization": {
    "organizationName": "Shell Slovakia s.r.o.",
    "ico": "12345678",
    "dic": "SK1234567890",
    "icDph": "SK1234567890",
    "address": {
      "street": "Hlavná",
      "buildingNumber": "45",
      "city": "Bratislava",
      "postalCode": "811 01",
      "country": "SK"
    }
  },
  "items": [
    {
      "type": "goods",
      "name": "Diesel",
      "quantity": 45.5,
      "unit": "l",
      "unitPrice": 1.44,
      "totalPrice": 65.52,
      "vatRate": 20,
      "priceWithoutVat": 54.60,
      "vatAmount": 10.92
    }
  ],
  "totalPrice": 65.50,
  "totalPriceWithoutVat": 54.58,
  "totalVat": 10.92
}
```

### Response (Error - 404 Not Found)
```json
{
  "error": "Receipt not found",
  "errorCode": "RECEIPT_NOT_FOUND",
  "receiptId": "invalid-id"
}
```

### Response (Error - 500 Server Error)
```json
{
  "error": "Internal server error",
  "errorCode": "INTERNAL_ERROR"
}
```

---

## Fuel Item Detection

### Detection Strategy

The e-Kasa API doesn't explicitly mark fuel items. Detection must be done by item name matching.

**Common Slovak Fuel Names:**
- Diesel: "Diesel", "Nafta", "Motorová nafta"
- Gasoline 95: "Natural 95", "BA 95", "Benzín 95"
- Gasoline 98: "Natural 98", "BA 98", "Benzín 98"
- LPG: "LPG", "Autoplyn"
- CNG: "CNG", "Zemný plyn"

### Implementation Pattern

```python
import re
from typing import Optional

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
    Detect fuel type from item name.

    Args:
        item_name: Item description from receipt

    Returns:
        Fuel type or None if not fuel
    """
    for fuel_type, patterns in FUEL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, item_name):
                return fuel_type
    return None

def extract_fuel_data(receipt_data: dict) -> dict:
    """
    Extract fuel purchase data from e-Kasa receipt.

    Returns:
        {
            'fuel_type': str,
            'quantity_liters': float,
            'price_per_liter': float,
            'total_price': float,
            'vat_amount': float,
            'vat_rate': float
        }
    """
    for item in receipt_data.get('items', []):
        fuel_type = detect_fuel_type(item.get('name', ''))
        if fuel_type:
            return {
                'fuel_type': fuel_type,
                'quantity_liters': float(item.get('quantity', 0)),
                'price_per_liter': float(item.get('unitPrice', 0)),
                'total_price': float(item.get('totalPrice', 0)),
                'vat_amount': float(item.get('vatAmount', 0)),
                'vat_rate': float(item.get('vatRate', 0))
            }

    raise ValueError('No fuel items found in receipt')
```

---

## QR Code Extraction

### Library Comparison

#### Option 1: pyzbar (Python - Current Plan)

**Pros:**
- Native Python
- Direct integration with PIL/Pillow
- Works well with images

**Cons:**
- Requires system dependencies (libzbar)
- PDF support requires pdf2image conversion
- More complex setup

**Installation:**
```bash
# Windows
pip install pyzbar pillow pdf2image

# macOS
brew install zbar
pip install pyzbar pillow pdf2image

# Linux
sudo apt-get install libzbar0
pip install pyzbar pillow pdf2image
```

#### Option 2: jsQR (JavaScript - blockovac-next uses this)

**Pros:**
- Pure JavaScript, no system dependencies
- Excellent PDF support via pdfjs-dist
- Simpler multi-scale implementation
- No external binaries required

**Cons:**
- Requires Node.js runtime
- Async/await complexity
- Separate process if called from Python

**Installation:**
```bash
npm install jsqr canvas pdfjs-dist
```

### Recommendation

**For car-log (Python MCP servers):** Use **pyzbar** for consistency
**If implementing Node.js version:** Use **jsQR** (simpler for PDFs)

---

## Multi-Scale QR Detection Implementation

### Python Version (pyzbar)

```python
from pdf2image import convert_from_path
from pyzbar.pyzbar import decode
from PIL import Image
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

def scan_image_qr(image_path: str) -> Optional[str]:
    """
    Scan single image for QR code.

    Args:
        image_path: Path to image file (PNG, JPG)

    Returns:
        QR code data (receipt ID) or None
    """
    try:
        image = Image.open(image_path)
        decoded = decode(image)

        if decoded:
            return decoded[0].data.decode('utf-8')
        return None
    except Exception as e:
        logger.error(f"Error scanning image: {e}")
        return None

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
        ValueError: If no QR code found at any scale
    """
    scales = [1.0, 2.0, 3.0]

    try:
        # Convert PDF to images (one per page)
        images = convert_from_path(pdf_path, dpi=200)
        logger.info(f"Converted PDF to {len(images)} page(s)")

        for page_num, image in enumerate(images, start=1):
            logger.info(f"Scanning page {page_num}...")

            for scale in scales:
                logger.debug(f"Trying scale {scale}x...")

                # Resize image
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
                        f"id={receipt_id[:20]}..."
                    )

                    return {
                        'receipt_id': receipt_id,
                        'detection_scale': scale,
                        'page_number': page_num,
                        'confidence': 1.0  # pyzbar doesn't provide confidence
                    }

        raise ValueError('QR code not found in PDF at any scale (1x, 2x, 3x)')

    except Exception as e:
        logger.error(f"Error scanning PDF: {e}")
        raise

def scan_qr_universal(file_path: str) -> Dict:
    """
    Universal QR scanner supporting images and PDFs.

    Args:
        file_path: Path to image or PDF file

    Returns:
        QR scan result dictionary
    """
    ext = file_path.lower().split('.')[-1]

    if ext == 'pdf':
        return scan_pdf_qr_multi_scale(file_path)
    elif ext in ['png', 'jpg', 'jpeg']:
        receipt_id = scan_image_qr(file_path)
        if receipt_id:
            return {
                'receipt_id': receipt_id,
                'detection_scale': 1.0,
                'page_number': 1,
                'confidence': 1.0
            }
        raise ValueError(f'QR code not found in image: {file_path}')
    else:
        raise ValueError(f'Unsupported file format: {ext}')
```

---

## Error Handling

### Error Categories

1. **QR Detection Errors**
   - File not found
   - Unsupported format
   - No QR code detected
   - Corrupted image/PDF

2. **API Errors**
   - Network timeout (>60s)
   - Invalid receipt ID
   - Receipt not found (404)
   - Server error (500)
   - Network connectivity issues

3. **Data Parsing Errors**
   - Invalid JSON response
   - Missing required fields
   - No fuel items found

### Implementation Pattern

```python
from typing import Dict, Optional
import requests
import logging

logger = logging.getLogger(__name__)

class EKasaError(Exception):
    """Base exception for e-Kasa API errors"""
    pass

class QRDetectionError(EKasaError):
    """QR code detection failed"""
    pass

class APITimeoutError(EKasaError):
    """API request timed out"""
    pass

class ReceiptNotFoundError(EKasaError):
    """Receipt ID not found in e-Kasa system"""
    pass

def fetch_receipt_with_retry(
    receipt_id: str,
    timeout: int = 60,
    max_retries: int = 1
) -> Dict:
    """
    Fetch receipt from e-Kasa API with error handling.

    Args:
        receipt_id: e-Kasa receipt identifier
        timeout: Request timeout in seconds
        max_retries: Number of retry attempts for transient errors

    Returns:
        Receipt data dictionary

    Raises:
        APITimeoutError: Request exceeded timeout
        ReceiptNotFoundError: Receipt ID not found
        EKasaError: Other API errors
    """
    url = f"https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/{receipt_id}"

    for attempt in range(max_retries + 1):
        try:
            logger.info(
                f"Fetching receipt {receipt_id} "
                f"(attempt {attempt + 1}/{max_retries + 1})"
            )

            response = requests.get(
                url,
                headers={'Accept': 'application/json'},
                timeout=timeout
            )

            # Handle HTTP errors
            if response.status_code == 404:
                raise ReceiptNotFoundError(
                    f"Receipt not found: {receipt_id}"
                )

            response.raise_for_status()

            data = response.json()
            logger.info(f"Receipt fetched successfully: {receipt_id}")
            return data

        except requests.Timeout:
            if attempt < max_retries:
                logger.warning(f"Timeout, retrying ({attempt + 1}/{max_retries})...")
                continue
            raise APITimeoutError(
                f"e-Kasa API timeout after {timeout}s"
            )

        except requests.RequestException as e:
            if attempt < max_retries:
                logger.warning(f"Request error, retrying: {e}")
                continue
            raise EKasaError(f"e-Kasa API error: {e}")

    raise EKasaError("All retry attempts failed")
```

---

## MCP Tool Implementation

### Complete scan_qr_code Tool

```python
# mcp_servers/ekasa_api/tools/scan_qr_code.py

from typing import Dict
import logging
from pathlib import Path
from .qr_scanner import scan_qr_universal, QRDetectionError

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
            return {
                "success": False,
                "error": f"File not found: {image_path}"
            }

        # Scan QR code
        result = scan_qr_universal(str(file_path))

        # Determine format
        ext = file_path.suffix.lower()
        file_format = 'pdf' if ext == '.pdf' else 'image'

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
```

### Complete fetch_receipt_data Tool

```python
# mcp_servers/ekasa_api/tools/fetch_receipt_data.py

from typing import Dict
import logging
from .api_client import (
    fetch_receipt_with_retry,
    APITimeoutError,
    ReceiptNotFoundError,
    EKasaError
)
from .fuel_detector import extract_fuel_data

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
        logger.info(f"Fetching receipt: {receipt_id}")
        raw_data = fetch_receipt_with_retry(receipt_id, timeout=timeout_seconds)

        # Parse receipt data
        receipt_data = {
            "receipt_id": raw_data.get('receiptId'),
            "vendor_name": raw_data.get('organization', {}).get('organizationName'),
            "vendor_tax_id": raw_data.get('organization', {}).get('ico'),
            "timestamp": raw_data.get('createDate'),
            "total_amount_eur": float(raw_data.get('totalPrice', 0)),
            "vat_amount_eur": float(raw_data.get('totalVat', 0)),
            "items": raw_data.get('items', [])
        }

        # Extract fuel items
        try:
            fuel_data = extract_fuel_data(raw_data)
            fuel_items = [fuel_data]
        except ValueError:
            # No fuel items found
            fuel_items = []

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
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_ekasa_api.py

import pytest
from mcp_servers.ekasa_api.tools.scan_qr_code import scan_qr_code
from mcp_servers.ekasa_api.tools.fetch_receipt_data import fetch_receipt_data

class TestQRScanning:
    """Test QR code detection"""

    def test_scan_image_success(self):
        """Test successful QR detection from image"""
        result = scan_qr_code("tests/fixtures/receipt_qr.png")
        assert result['success'] is True
        assert result['receipt_id'].startswith('O-E')
        assert result['format'] == 'image'

    def test_scan_pdf_multi_scale(self):
        """Test PDF scanning with multi-scale detection"""
        result = scan_qr_code("tests/fixtures/receipt.pdf")
        assert result['success'] is True
        assert result['format'] == 'pdf'
        assert result['detection_scale'] in [1.0, 2.0, 3.0]

    def test_scan_no_qr_found(self):
        """Test error when no QR code present"""
        result = scan_qr_code("tests/fixtures/no_qr.png")
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

class TestReceiptFetching:
    """Test e-Kasa API integration"""

    @pytest.mark.integration
    def test_fetch_receipt_success(self):
        """Test successful receipt fetch (requires real API)"""
        # Use cached test receipt ID
        result = fetch_receipt_data("O-E182401234567890123456789")
        assert result['success'] is True
        assert result['receipt_data']['vendor_name'] is not None

    def test_fetch_invalid_receipt_id(self):
        """Test error handling for invalid receipt ID"""
        result = fetch_receipt_data("invalid-id")
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    @pytest.mark.slow
    def test_fetch_timeout_handling(self):
        """Test timeout handling (use mock slow API)"""
        result = fetch_receipt_data("test-id", timeout_seconds=1)
        assert result['success'] is False
        assert 'timeout' in result['error'].lower()
```

### Integration Test

```python
# tests/integration/test_ekasa_workflow.py

import pytest

@pytest.mark.integration
async def test_full_ekasa_workflow():
    """Test complete workflow: Image → QR → API → Fuel data"""

    # Step 1: Scan QR from receipt
    qr_result = await scan_qr_code("tests/fixtures/shell_receipt.pdf")
    assert qr_result['success'] is True
    receipt_id = qr_result['receipt_id']

    # Step 2: Fetch receipt data
    api_result = await fetch_receipt_data(receipt_id)
    assert api_result['success'] is True

    # Step 3: Verify fuel data extracted
    fuel_items = api_result['fuel_items']
    assert len(fuel_items) > 0

    fuel = fuel_items[0]
    assert fuel['fuel_type'] in ['Diesel', 'Gasoline_95', 'Gasoline_98']
    assert fuel['quantity_liters'] > 0
    assert fuel['price_per_liter'] > 0
```

---

## Performance Considerations

### Timeouts
- **Image QR scan:** < 1 second
- **PDF QR scan (multi-scale):** 2-5 seconds
- **e-Kasa API call:** 5-30 seconds (typically 10-15s)
- **Total workflow:** 10-40 seconds

### Optimization Strategies

1. **Cache API responses:**
   ```python
   # Cache successful receipt fetches to avoid re-fetching
   RECEIPT_CACHE = {}  # In-memory for demo, use Redis for production

   def fetch_with_cache(receipt_id: str) -> Dict:
       if receipt_id in RECEIPT_CACHE:
           return RECEIPT_CACHE[receipt_id]

       data = fetch_receipt_with_retry(receipt_id)
       RECEIPT_CACHE[receipt_id] = data
       return data
   ```

2. **Async PDF processing:**
   - Process multiple pages in parallel
   - Use asyncio for concurrent scale detection

3. **Early termination:**
   - Stop multi-scale detection on first success
   - Don't process all PDF pages if QR found on page 1

---

## User Experience Guidelines

### Progress Indicators

Show users what's happening during slow operations:

```
User: "Scan this receipt"
Assistant: "Scanning QR code from PDF..."
[2s later]
Assistant: "QR code detected! Fetching receipt data from e-Kasa..."
[15s later]
Assistant: "Receipt data retrieved successfully. Found 45.5 liters of Diesel for €65.50."
```

### Error Messages

Make errors actionable:

**Bad:**
```
Error: API timeout
```

**Good:**
```
The e-Kasa receipt lookup took longer than expected (>60 seconds).
This sometimes happens with the Slovak government API.
Would you like to try again, or enter the fuel data manually?
```

---

## Configuration

### MCP Server Config

```json
{
  "mcpServers": {
    "ekasa-api": {
      "command": "python",
      "args": ["-m", "mcp_servers.ekasa_api"],
      "env": {
        "MCP_TIMEOUT_SECONDS": "60",
        "EKASA_API_TIMEOUT": "60",
        "LOG_LEVEL": "INFO",
        "ENABLE_CACHE": "true",
        "CACHE_TTL_SECONDS": "3600"
      }
    }
  }
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TIMEOUT_SECONDS` | 60 | MCP tool execution timeout |
| `EKASA_API_TIMEOUT` | 60 | e-Kasa API request timeout |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ENABLE_CACHE` | true | Enable receipt caching |
| `CACHE_TTL_SECONDS` | 3600 | Cache time-to-live (1 hour) |

---

## Troubleshooting

### Common Issues

**Issue:** QR code not detected from PDF
- **Solution:** Try multi-scale detection (2x, 3x zoom)
- **Check:** PDF quality, QR code size

**Issue:** e-Kasa API timeout
- **Solution:** Retry once, then offer manual entry
- **Check:** Network connectivity, API status

**Issue:** No fuel items detected
- **Solution:** Check fuel name patterns, may need to add new patterns
- **Check:** Receipt item descriptions

**Issue:** Slow PDF processing
- **Solution:** Reduce DPI in pdf2image (try 150 instead of 200)
- **Check:** PDF file size, number of pages

---

## References

- **blockovac-next repository:** Implementation reference for multi-scale QR detection
- **e-Kasa API documentation:** Financial Administration of Slovak Republic
- **pyzbar documentation:** https://pypi.org/project/pyzbar/
- **jsQR documentation:** https://github.com/cozmo/jsQR
- **pdfjs-dist documentation:** https://mozilla.github.io/pdf.js/

---

**Last Updated:** 2025-11-18
**Status:** Ready for implementation
