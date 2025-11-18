# ekasa-api MCP Server

Slovak e-Kasa receipt processing MCP server with QR code scanning and API integration.

## Features

- **QR Code Scanning**: Extract receipt IDs from images (PNG, JPG) and PDFs
- **Multi-Scale PDF Detection**: Automatically tries 1x, 2x, 3x zoom to find small QR codes
- **e-Kasa API Integration**: Fetch receipt data from Slovak government API
- **Fuel Detection**: Automatically detects fuel items using Slovak naming patterns
- **Extended Timeout**: Supports up to 60-second API calls (e-Kasa typically responds in 5-30s)

## Installation

### System Dependencies

#### macOS
```bash
brew install zbar poppler
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install libzbar0 poppler-utils
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

## MCP Server Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ekasa-api": {
      "command": "python",
      "args": ["-m", "mcp_servers.ekasa_api"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Tools

### 1. scan_qr_code

Extract QR code from receipt image or PDF.

**Input:**
- `image_path` (string): Absolute path to receipt file

**Output:**
```json
{
  "success": true,
  "receipt_id": "O-E182401234567890123456789",
  "confidence": 1.0,
  "detection_scale": 2.0,
  "format": "pdf",
  "error": null
}
```

### 2. fetch_receipt_data

Fetch receipt data from e-Kasa API.

**Input:**
- `receipt_id` (string): e-Kasa receipt identifier
- `timeout_seconds` (number, optional): Request timeout (default: 60s)

**Output:**
```json
{
  "success": true,
  "receipt_data": {
    "receipt_id": "O-E182401234567890123456789",
    "vendor_name": "Shell Slovakia s.r.o.",
    "vendor_tax_id": "12345678",
    "timestamp": "2025-11-18T14:30:00Z",
    "total_amount_eur": 65.50,
    "vat_amount_eur": 10.92,
    "items": [...]
  },
  "fuel_items": [
    {
      "fuel_type": "Diesel",
      "quantity_liters": 45.5,
      "price_per_liter": 1.44,
      "total_price": 65.52,
      "vat_amount": 10.92,
      "vat_rate": 20.0,
      "item_name": "Diesel"
    }
  ],
  "error": null
}
```

## Fuel Detection Patterns

The server automatically detects these fuel types from Slovak names:

- **Diesel**: "diesel", "nafta", "motorová nafta"
- **Gasoline 95**: "natural 95", "BA 95", "benzín 95"
- **Gasoline 98**: "natural 98", "BA 98", "benzín 98"
- **LPG**: "lpg", "autoplyn"
- **CNG**: "cng", "zemný plyn"

## Architecture

```
ekasa_api/
├── __main__.py              # MCP server entry point
├── exceptions.py            # Custom exceptions
├── fuel_detector.py         # Slovak fuel pattern matching
├── qr_scanner.py           # Multi-scale QR detection
├── api_client.py           # e-Kasa API client
├── tools/
│   ├── scan_qr_code.py     # MCP tool: QR scanning
│   └── fetch_receipt_data.py  # MCP tool: Receipt fetching
└── requirements.txt
```

## Error Handling

The server handles these error scenarios:

- **QR Detection Errors**: File not found, unsupported format, no QR detected
- **API Errors**: Network timeout, invalid receipt ID, receipt not found (404)
- **Data Parsing Errors**: Invalid JSON, missing fields, no fuel items

All errors return structured responses with `success: false` and descriptive error messages.

## Performance

- **Image QR scan**: < 1 second
- **PDF QR scan (multi-scale)**: 2-5 seconds
- **e-Kasa API call**: 5-30 seconds (typically 10-15s)
- **Total workflow**: 10-40 seconds

## Development

Run the server directly:

```bash
python -m mcp_servers.ekasa_api
```

Enable debug logging:

```bash
LOG_LEVEL=DEBUG python -m mcp_servers.ekasa_api
```

## License

Part of the car-log project for Slovak tax-compliant mileage logging.
