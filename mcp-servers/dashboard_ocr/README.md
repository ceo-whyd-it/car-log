# Dashboard OCR MCP Server

## Overview

The `dashboard-ocr` MCP server provides tools for photo metadata extraction (EXIF) and quality validation for the Car Log system.

**Priority:** P0 (EXIF extraction only)
**Note:** OCR with Claude Vision is P1 and not included in MVP

## Features

### Tools

#### 1. `extract_metadata`

Extract EXIF metadata from photos including GPS coordinates, timestamp, and camera model.

**Input:**
```json
{
  "photo_path": "/path/to/photo.jpg"
}
```

**Output:**
```json
{
  "success": true,
  "timestamp": "2025-11-18T14:30:45",
  "gps_coords": {
    "lat": 48.1486,
    "lng": 17.1077
  },
  "camera_model": "Canon EOS 5D Mark IV",
  "error": null
}
```

**Behavior:**
- Returns `null` for missing EXIF fields (graceful degradation)
- Returns `error` message if file cannot be read
- Handles missing EXIF data gracefully (returns success=true with null fields)
- GPS coordinates are parsed from EXIF GPS IFD with proper hemisphere correction
- Timestamps are returned in ISO 8601 format

#### 2. `check_photo_quality`

Validate photo quality before processing with OCR.

**Input:**
```json
{
  "photo_path": "/path/to/photo.jpg"
}
```

**Output:**
```json
{
  "is_acceptable": true,
  "issues": [],
  "suggestions": [
    "Use steady hands or tripod",
    "Improve lighting"
  ]
}
```

**Quality Checks:**
- Minimum resolution: 640x480 pixels
- Brightness: 50-200 range (dark and bright extremes flagged)
- Blur detection: Laplacian variance threshold
- File accessibility

## Installation

### Requirements

```bash
pip install Pillow piexif
```

For full quality checks (blur detection):
```bash
pip install numpy opencv-python
```

### Setup

1. Create the server directory structure:
```bash
mkdir -p mcp-servers/dashboard_ocr/tools
```

2. Copy files:
```bash
cp __main__.py mcp-servers/dashboard_ocr/
cp __init__.py mcp-servers/dashboard_ocr/
cp tools/*.py mcp-servers/dashboard_ocr/tools/
```

3. Configure in Claude Desktop (`~/.claude/mcp_config.json`):
```json
{
  "mcpServers": {
    "dashboard-ocr": {
      "command": "python",
      "args": ["-m", "mcp_servers.dashboard_ocr"]
    }
  }
}
```

## Usage Examples

### Extract GPS from Dashboard Photo

```python
from mcp_servers.dashboard_ocr.tools import extract_metadata

result = extract_metadata("/path/to/dashboard_photo.jpg")

if result["success"] and result["gps_coords"]:
    print(f"Location: {result['gps_coords']['lat']}, {result['gps_coords']['lng']}")
    print(f"Timestamp: {result['timestamp']}")
    print(f"Camera: {result['camera_model']}")
```

### Validate Photo Quality Before OCR

```python
from mcp_servers.dashboard_ocr.tools import check_photo_quality

quality = check_photo_quality("/path/to/photo.jpg")

if quality["is_acceptable"]:
    print("Photo is suitable for OCR")
else:
    print(f"Issues: {quality['issues']}")
    print(f"Suggestions: {quality['suggestions']}")
```

## Data Model

### EXIF Extraction

The server extracts the following EXIF tags:

- **Timestamp**: EXIF tag 36867 (DateTimeOriginal) or 306 (DateTime)
  - Format: "YYYY:MM:DD HH:MM:SS"
  - Returned as ISO 8601 string

- **GPS Coordinates**: EXIF tag 34853 (GPS IFD)
  - Format: Degrees/Minutes/Seconds tuples
  - Includes reference (N/S for latitude, E/W for longitude)
  - Converted to decimal degrees with proper sign handling

- **Camera Model**: EXIF tag 271
  - Manufacturer and model name
  - Decoded from UTF-8 bytes

### Quality Metrics

- **Resolution**: Minimum 640x480 pixels recommended
- **Brightness**: 50-200 range (0-255 scale)
- **Blur**: Laplacian variance threshold > 20
- **File Format**: JPEG, PNG supported via PIL

## Testing

Run the test suite:

```bash
pytest tests/test_dashboard_ocr_exif.py -v
```

Test coverage:
- EXIF extraction with and without data
- GPS parsing with different hemispheres
- Datetime extraction and validation
- Camera model extraction with unicode
- Photo quality checks (size, brightness, blur)
- Integration tests
- Error handling (missing files, invalid paths)

## Architecture Notes

### Design Principles

1. **Graceful Degradation**: Missing EXIF fields return `null` instead of errors
2. **File Safety**: No file modifications, read-only operations
3. **Error Handling**: All errors caught and returned in response
4. **Stateless**: No server-side state, pure function behavior

### GPS Handling

GPS coordinates are the authoritative location data for trips:
- **70% weight** in trip reconstruction (GPS is precise)
- **Addresses are labels** (30% weight, for human readability)
- Proper hemisphere handling (N/S, E/W)
- Fallback for missing EXIF GPS

### Quality Validation

Basic quality checks prevent:
- Very small/low-resolution images
- Overexposed (too bright) images
- Underexposed (too dark) images
- Blurry/out-of-focus images

Limitations:
- Requires numpy/opencv for full blur detection
- Basic brightness check sufficient for most cases
- Can be extended with more sophisticated ML-based detection in P2

## Integration with Car Log

### Workflow: Receipt Photo Processing

1. User provides receipt photo (e-Kasa receipt)
2. `extract_metadata` extracts:
   - Timestamp → Links to receipt time
   - GPS coordinates → Links to checkpoint location
   - Camera model → Metadata for audit
3. `check_photo_quality` validates image before OCR (P1)
4. Results feed into trip reconstruction

### Workflow: Dashboard Photo Processing

1. User provides dashboard odometer photo
2. `extract_metadata` extracts GPS + timestamp
3. `check_photo_quality` validates image quality
4. Results used to create checkpoints
5. OCR (P1) extracts odometer reading

## Future Enhancements (P1+)

- [ ] OCR for odometer reading (Claude Vision)
- [ ] Dashboard LCD/LED detection
- [ ] Multi-page receipt handling
- [ ] QR code extraction from receipts
- [ ] Advanced blur detection (ML-based)
- [ ] Orientation auto-correction
- [ ] Metadata caching for performance

## Error Handling

All errors are gracefully handled and returned in the response:

```json
{
  "success": false,
  "error": "File not found: /path/to/photo.jpg",
  "timestamp": null,
  "gps_coords": null,
  "camera_model": null
}
```

Common error scenarios:
- File not found → `error` field populated
- Unreadable image format → `error` field populated
- Missing EXIF data → `success=true`, fields are `null`
- Directory instead of file → `error` field populated

## Performance

- Single image EXIF extraction: ~50-100ms
- Quality check: ~200-300ms (with blur detection)
- Memory footprint: ~5-10MB per image (PIL buffer)
- No caching needed (reads are fast)

## Slovak Compliance

This server supports Car Log's tax compliance requirements by:
- Capturing accurate timestamps from photos
- Extracting GPS coordinates for location verification
- Validating photo quality for audit purposes
- Maintaining metadata for VAT Act 2025 compliance

## License

Part of Car Log project.
