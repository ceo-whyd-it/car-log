# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Car Log is a **Slovak tax-compliant company vehicle mileage logger** built for the MCP 1st Birthday Hackathon. The key innovation is using **MCP servers as the actual backend architecture** (not just connectors), enabling conversational trip logging through Claude Desktop with automatic gap-based reconstruction.

**Target Market:** Slovak/European small businesses facing VAT Act 2025 compliance requirements.

**Project Status:** Specification-ready, implementation in progress (Hackathon deadline: Nov 30, 2025)

## Architecture

### MCP-First Design

This project uses **7 headless MCP servers** as the core backend:

```
┌─────────────────────────────────────────┐
│   USER INTERFACES                       │
│   • Claude Desktop (Skills) - P0        │
│   • Gradio Web UI (DSPy) - P1          │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   7 MCP SERVERS (Headless Backend)     │
│                                         │
│   P0 (Required for MVP):                │
│   • car-log-core (CRUD)                │
│   • trip-reconstructor (Matching)      │
│   • geo-routing (Geocoding/Routing)    │
│   • ekasa-api (Slovak Receipts)        │
│   • dashboard-ocr (EXIF + OCR)         │
│   • validation (4 Algorithms)          │
│                                         │
│   P1 (Optional):                        │
│   • report-generator (PDF/CSV)         │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   DATA STORAGE (File-Based)            │
│   JSON files in monthly folders        │
│   ~/Documents/MileageLog/data/         │
└─────────────────────────────────────────┘
```

**Key Principles:**
- **Stateless servers**: Each MCP server is independent, no shared state
- **Orchestration at UI layer**: Skills/DSPy coordinate multiple MCP calls
- **GPS-first**: Coordinates are source of truth (70% weight), addresses are labels (30% weight)
- **File-based storage**: JSON files with atomic write pattern (no database required for MVP)

## Data Storage Architecture

### File Structure

```
~/Documents/MileageLog/data/
├── vehicles/
│   └── {vehicle_id}.json
├── checkpoints/
│   ├── 2025-11/
│   │   ├── {checkpoint_id}.json
│   │   └── index.json (optional, for performance)
│   └── 2025-12/
├── trips/
│   ├── 2025-11/
│   │   ├── {trip_id}.json
│   │   └── index.json
│   └── 2025-12/
├── templates/
│   └── {template_id}.json
└── typical-destinations.json
```

### Atomic Write Pattern (CRITICAL)

**Always use this pattern to prevent file corruption:**

```python
import os
import json
import tempfile

def atomic_write_json(file_path, data):
    """Write JSON file atomically (crash-safe)"""
    # 1. Write to temporary file
    dir_path = os.path.dirname(file_path)
    fd, temp_path = tempfile.mkstemp(dir=dir_path, suffix='.tmp')

    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # 2. Atomic rename (POSIX guarantees atomicity)
        os.replace(temp_path, file_path)
    except:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
```

**Why this matters:** If the process crashes during write, the original file remains intact.

## Slovak Tax Compliance (MANDATORY)

### Required Fields for Tax Deduction

**Vehicle:**
- `vin`: 17-character VIN (no I/O/Q characters) - **MANDATORY for Slovak VAT Act 2025**
- `license_plate`: Format `XX-123XX` (e.g., "BA-456CD")

**Trip:**
- `driver_name`: Full name of driver - **MANDATORY**
- `trip_start_datetime`: When trip started (ISO 8601)
- `trip_end_datetime`: When trip ended
- `trip_start_location`: Trip origin (separate from fuel station)
- `trip_end_location`: Trip destination
- `refuel_datetime`: When refuel occurred (separate from trip timing)
- `refuel_timing`: "before" | "during" | "after"

**Fuel Efficiency:**
- **Always use L/100km** (European standard), never km/L
- Format: `8.5 L/100km` (not `11.8 km/L`)

### Validation Thresholds

```
Distance sum:     ±10% (odometer delta vs. sum of trip distances)
Fuel consumption: ±15% (expected vs. actual fuel)
Efficiency range:
  - Diesel: 5-15 L/100km (reasonable range)
  - Gasoline: 6-20 L/100km
Deviation from average: 20% warning threshold
```

## Trip Reconstruction Algorithm

### Core Algorithm: Hybrid GPS (70%) + Address (30%)

**Mode Selection:**
- **Mode A (GPS-only)**: Both gap checkpoints have GPS → Use GPS matching (100%)
- **Mode B (Hybrid)**: Both have GPS + addresses → GPS (70%) + Address (30%)
- **Mode C (Fallback)**: No GPS → Address matching only (not recommended)

**GPS Matching Thresholds:**
```
Distance from template    Score
< 100m                    100
100m - 500m               90
500m - 2000m              70
2000m - 5000m             40
> 5000m                   0
```

**Template Matching Flow:**
1. Get gap data: `car-log-core.analyze_gap(checkpoint1_id, checkpoint2_id)`
2. Get templates: `car-log-core.list_templates(user_id)`
3. Calculate routes (optional): `geo-routing.calculate_route(start, end)`
4. Run matching: `trip-reconstructor.match_templates({gap_data, templates})`
5. Present proposals to user (confidence >= 70%)
6. Create trips: `car-log-core.create_trips_batch(approved_trips)`

## MCP Server Implementation

### Server Configuration

MCP servers are configured in `claude_desktop_config.json` (macOS) or equivalent:

```json
{
  "mcpServers": {
    "car-log-core": {
      "command": "python",
      "args": ["-m", "mcp_servers.car_log_core"],
      "env": {
        "DATA_PATH": "~/Documents/MileageLog/data",
        "USE_ATOMIC_WRITES": "true"
      }
    },
    "trip-reconstructor": {
      "command": "python",
      "args": ["-m", "mcp_servers.trip_reconstructor"],
      "env": {
        "GPS_WEIGHT": "0.7",
        "ADDRESS_WEIGHT": "0.3"
      }
    }
  }
}
```

### Tool Naming Convention

**Pattern:** `{server_name}.{action}_{entity}` or `{server_name}.{action}`

Examples:
- `car-log-core.create_vehicle`
- `car-log-core.analyze_gap`
- `trip-reconstructor.match_templates`
- `geo-routing.geocode_address`
- `validation.validate_trip`

### Error Handling

**Standard error response format:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable error",
    "field": "vin",
    "details": "Additional context"
  }
}
```

**Common error codes:**
- `VALIDATION_ERROR`: Invalid input data
- `NOT_FOUND`: Resource doesn't exist
- `GPS_REQUIRED`: Operation needs GPS coordinates
- `AMBIGUOUS_ADDRESS`: Multiple geocoding matches (return alternatives)
- `EXTERNAL_API_ERROR`: Third-party service failed

## Development Workflow

### Parallel Development Tracks

The implementation plan uses 4 parallel tracks:

**Track A: Data Foundation (Days 1-3)**
- `car-log-core` - CRUD operations
- Blocks: trip-reconstructor, validation, report-generator

**Track B: External Integrations (Days 1-4)**
- `ekasa-api` - Receipt processing
- `geo-routing` - Geocoding/routing
- No dependencies, fully parallel

**Track C: Intelligence & Validation (Days 3-6)**
- `trip-reconstructor` - Template matching
- `validation` - 4 validation algorithms
- Requires: car-log-core data structures

**Track D: Integration (Days 7-11)**
- Claude Desktop integration
- End-to-end workflows
- Requires: All P0 servers functional

### Critical Checkpoints

**Day 2:** Vehicle + Checkpoint CRUD functional
**Day 4:** All external APIs working
**Day 6:** Trip reconstruction + validation complete
**Day 7:** Integration checkpoint (ALL servers discoverable)
**Day 10:** Full integration complete
**Day 13:** Hackathon submission

### Testing Strategy

**Unit Tests:**
- Pure function testing for `trip-reconstructor`
- CRUD operations for `car-log-core`
- Atomic write crash safety
- GPS matching at various distances (10m, 100m, 1km, 10km)

**Integration Tests:**
- Receipt → Checkpoint workflow
- Gap detection → Template matching → Trip creation
- Geocoding ambiguity handling

**Performance Tests:**
- Template matching with 100+ templates (must complete < 2 seconds)
- File-based storage with 1000+ trips (read < 5 seconds with index)

## External APIs

### e-Kasa API (Slovak Receipt System)
- **Purpose:** Fetch receipt data for VAT compliance
- **Endpoint:** `https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/{receipt_id}`
- **Authentication:** None required (public endpoint)
- **Response Time:** 5-30 seconds typically
- **Timeout:** 60 seconds (MCP server configuration)
- **See:** spec/EKASA_IMPLEMENTATION_GUIDE.md for complete details

### OpenStreetMap (OSRM + Nominatim)
- **OSRM:** Route calculation (https://router.project-osrm.org)
- **Nominatim:** Geocoding (https://nominatim.openstreetmap.org)
- **No API key required** (respect rate limits)
- **Cache TTL:** 24 hours

### Claude Vision (Anthropic)
- **Purpose:** Dashboard OCR (odometer reading)
- **Priority:** P1 (can fallback to manual entry)
- **API Key:** Set in `ANTHROPIC_API_KEY` env var

---

## e-Kasa API Implementation Pattern

**Complete reference:** See spec/EKASA_IMPLEMENTATION_GUIDE.md

### Endpoint Details
- **URL:** `https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/{receipt_id}`
- **Authentication:** None required (public endpoint)
- **Response Time:** 5-30 seconds typically
- **Timeout:** 60 seconds (MCP server configuration)
- **Reference:** blockovac-next repository implementation

### Implementation Pattern

```python
import requests
from typing import Optional, Dict

def fetch_ekasa_receipt(receipt_id: str, timeout: int = 60) -> Dict:
    """
    Fetch receipt from e-Kasa API.

    Args:
        receipt_id: e-Kasa receipt identifier
        timeout: Request timeout in seconds (default 60)

    Returns:
        Receipt data dictionary

    Raises:
        TimeoutError: If request exceeds timeout
        ValueError: If receipt_id invalid
    """
    url = f"https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/{receipt_id}"

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        raise TimeoutError(f"e-Kasa API timeout after {timeout}s")
    except requests.RequestException as e:
        raise ValueError(f"e-Kasa API error: {e}")
```

### User Experience Considerations
- Show progress indicator during 5-30s wait
- Inform user that receipt lookup may take up to 60 seconds
- Cache successful responses to avoid repeated API calls
- Provide manual entry fallback if timeout occurs

### Fuel Detection Pattern

The e-Kasa API doesn't explicitly mark fuel items. Use Slovak name pattern matching:

```python
import re

FUEL_PATTERNS = {
    'Diesel': [r'(?i)diesel', r'(?i)nafta', r'(?i)motorová\s+nafta'],
    'Gasoline_95': [r'(?i)natural\s*95', r'(?i)ba\s*95', r'(?i)benzín\s*95'],
    'Gasoline_98': [r'(?i)natural\s*98', r'(?i)ba\s*98', r'(?i)benzín\s*98'],
    'LPG': [r'(?i)lpg', r'(?i)autoplyn'],
    'CNG': [r'(?i)cng', r'(?i)zemný\s+plyn']
}

def detect_fuel_type(item_name: str) -> Optional[str]:
    """Detect fuel type from Slovak item name."""
    for fuel_type, patterns in FUEL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, item_name):
                return fuel_type
    return None
```

---

## Extended Timeout Best Practices

**MCP Server Configuration:**
Claude Desktop supports extended timeouts for MCP servers. Configure in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ekasa-api": {
      "command": "python",
      "args": ["-m", "mcp_servers.ekasa_api"],
      "env": {
        "MCP_TIMEOUT_SECONDS": "60"
      }
    }
  }
}
```

### When to Use Extended Timeouts

✅ **Use extended timeouts for:**
- External API calls (e-Kasa: 5-30s)
- PDF processing with multi-scale QR detection
- Large file operations

❌ **Do NOT use extended timeouts for:**
- Simple CRUD operations (keep < 5s)
- Local calculations (keep < 1s)

### Timeout Hierarchy

1. **Operation timeout** (e.g., `requests.get(timeout=60)`)
2. **MCP tool timeout** (configured in server)
3. **Claude Desktop timeout** (60s max)

### User Experience During Long Operations

Claude Desktop shows a "thinking" indicator while MCP tools execute. For operations that may take 30-60 seconds:

```python
# Good: User sees "thinking" indicator for 15-30s
result = await fetch_receipt_data(receipt_id)  # Typical: 15s

# Acceptable: User sees "thinking" for up to 60s
result = await fetch_receipt_data(receipt_id)  # Slow case: 45s

# Bad: User has no idea what's happening
# Don't use async queues/polling for operations < 60s
```

---

## Multi-Scale PDF QR Detection Pattern

**Problem:** QR codes in PDFs may be too small or low-resolution for direct detection.

**Solution:** Render PDF at multiple scales and attempt detection at each level.

### Python Implementation Pattern

```python
from pdf2image import convert_from_path
from pyzbar.pyzbar import decode
from PIL import Image

def scan_pdf_multi_scale(pdf_path: str) -> dict:
    """
    Scan PDF for QR codes at multiple scales.

    Args:
        pdf_path: Path to PDF file

    Returns:
        {
            'receipt_id': str,
            'detection_scale': float,  # 1.0, 2.0, or 3.0
            'page_number': int
        }

    Raises:
        ValueError: If QR code not found at any scale
    """
    scales = [1.0, 2.0, 3.0]
    images = convert_from_path(pdf_path, dpi=200)

    for page_num, image in enumerate(images, start=1):
        for scale in scales:
            # Resize image to scale
            width, height = image.size
            scaled_img = image.resize(
                (int(width * scale), int(height * scale)),
                Image.LANCZOS
            )

            # Try QR detection
            decoded = decode(scaled_img)
            if decoded:
                return {
                    'receipt_id': decoded[0].data.decode('utf-8'),
                    'detection_scale': scale,
                    'page_number': page_num
                }

    raise ValueError('QR code not found in PDF at any scale')
```

### When to Use Multi-Scale Detection

- ✅ PDF receipts (common for e-Kasa)
- ✅ Low-resolution images
- ✅ Small QR codes
- ✅ Initial detection fails at 1x scale

### Performance Impact

- **3x scale = ~9x pixels to process**
- Limit to 3 scales maximum
- Stop on first successful detection
- Don't process all PDF pages if QR found on page 1

---

## Key Data Models

### Checkpoint
```typescript
{
  checkpoint_id: string (UUID),
  vehicle_id: string (UUID),
  checkpoint_type: "refuel" | "manual",
  datetime: string (ISO 8601),
  odometer_km: number,

  // Location (GPS is source of truth)
  location: {
    coords: {latitude: number, longitude: number},
    address?: string,  // Optional human-readable label
    source: "exif" | "user" | "geocoded"
  },

  // Receipt data (if refuel)
  receipt?: {
    receipt_id: string,
    vendor_name: string,
    fuel_type: string,
    fuel_liters: number,
    price_excl_vat: number,
    price_incl_vat: number,
    vat_rate: number
  }
}
```

### Template
```typescript
{
  template_id: string (UUID),
  name: string,

  // FROM endpoint (GPS MANDATORY)
  from_coords: {lat: number, lng: number},
  from_address?: string,
  from_label?: string,

  // TO endpoint (GPS MANDATORY)
  to_coords: {lat: number, lng: number},
  to_address?: string,
  to_label?: string,

  // Optional enhancement fields
  distance_km?: number,
  is_round_trip?: boolean,
  typical_days?: string[],  // ["Monday", "Thursday"]
  purpose?: "business" | "personal",
  business_description?: string
}
```

### Trip
```typescript
{
  trip_id: string (UUID),
  vehicle_id: string (UUID),
  start_checkpoint_id: string (UUID),
  end_checkpoint_id: string (UUID),

  // Slovak compliance fields
  driver_name: string,  // MANDATORY
  trip_start_datetime: string (ISO 8601),
  trip_end_datetime: string (ISO 8601),
  trip_start_location: string,
  trip_end_location: string,

  // Metrics
  distance_km: number,
  fuel_consumption_liters?: number,
  fuel_efficiency_l_per_100km?: number,  // L/100km format

  // Purpose
  purpose: "Business" | "Personal",
  business_description?: string,  // Required if Business

  // Reconstruction metadata
  reconstruction_method: "manual" | "template" | "geo_assisted",
  template_id?: string,
  confidence_score?: number
}
```

## Common Patterns

### Geocoding with Ambiguity Handling

```typescript
// Step 1: Geocode address
const result = await geo_routing.geocode_address({
  address: "Košice",
  country_hint: "SK"
});

// Step 2: Check for ambiguity
if (result.confidence < 0.7 && result.alternatives.length > 0) {
  // Present alternatives to user
  console.log("Multiple matches found:");
  result.alternatives.forEach((alt, i) => {
    console.log(`${i+1}. ${alt.address} (${alt.type})`);
  });

  // User selects option
  const selected = result.alternatives[userChoice - 1];
  coords = selected.coordinates;
} else {
  coords = result.coordinates;
}
```

### Template Creation with GPS

```typescript
// Always store GPS coordinates (mandatory)
// Addresses are optional but improve matching

const template = {
  name: "Warehouse Run",
  from_coords: {lat: 48.1486, lng: 17.1077},  // Required
  from_address: "Hlavná 45, Bratislava",      // Optional
  from_label: "Bratislava",                    // Optional
  to_coords: {lat: 48.7164, lng: 21.2611},
  to_address: "Mlynská 45, Košice",
  to_label: "Košice",
  distance_km: 410,
  is_round_trip: true,
  typical_days: ["Monday", "Thursday"],
  purpose: "business",
  business_description: "Warehouse pickup"
};
```

## Scope Management

### P0 Features (MUST HAVE for MVP)
- ✅ 7 MCP servers functional
- ✅ Claude Desktop integration
- ✅ Receipt → Checkpoint → Trip → Report workflow
- ✅ Slovak compliance (VIN, driver, L/100km)
- ✅ Template matching with GPS (70%) + address (30%)
- ✅ 4 validation algorithms
- ✅ CSV report generation

### P1 Features (NICE TO HAVE)
- ⏳ Gradio web UI
- ⏳ Dashboard OCR with Claude Vision
- ⏳ PDF report generation
- ⏳ Advanced route intelligence

### Cut Priority (If Behind Schedule)
1. **First:** Gradio UI
2. **Second:** Dashboard OCR
3. **Third:** PDF reports
4. **Fourth:** Route calculation

**NEVER CUT:** Receipt processing, trip reconstruction, validation, Slovak compliance

## Documentation References

- **spec/01-product-overview.md**: Product vision, scope, success metrics
- **spec/02-domain-model.md**: Core concepts (Checkpoint, Trip, Template)
- **spec/03-trip-reconstruction.md**: Algorithm details, scoring thresholds
- **spec/04-data-model.md**: JSON schemas, file structure
- **spec/06-mcp-architecture-v2.md**: Server architecture, tool definitions
- **spec/07-mcp-api-specifications.md**: Complete API tool specs (24 tools, queue removed)
- **spec/08-implementation-plan.md**: 13-day parallel development plan
- **spec/09-hackathon-presentation.md**: Demo script, video structure

## Important Notes

### When Writing Code

1. **Always validate VIN format**: 17 characters, no I/O/Q
2. **Always use atomic writes**: See pattern above
3. **Always use L/100km**: Never km/L
4. **GPS is mandatory for templates**: Addresses are optional
5. **Separate trip timing from refuel timing**: Slovak compliance requirement

### When Testing

1. **Test with realistic Slovak data**: Bratislava, Košice, Slovak addresses
2. **Test geocoding ambiguity**: "Košice" returns multiple matches
3. **Test atomic write crash safety**: Simulate crashes during writes
4. **Test with 100+ templates**: Performance requirement

### When Debugging

1. **Check JSON file directly**: Files are human-readable
2. **Check atomic write temp files**: Look for `.tmp` files
3. **Check MCP server logs**: Each server logs independently
4. **Check validation thresholds**: May need adjustment

## Getting Started

1. **Read specifications first**: Start with README.md → spec/01-product-overview.md
2. **Understand MCP architecture**: Read spec/06-mcp-architecture-v2.md
3. **Review API contracts**: Study spec/07-mcp-api-specifications.md
4. **Check implementation plan**: Follow spec/08-implementation-plan.md tracks
5. **Start with car-log-core**: It blocks trip-reconstructor and validation

## Environment Setup

```bash
# Create data directories
mkdir -p ~/Documents/MileageLog/data/{vehicles,checkpoints,trips,templates,reports}

# Set environment variables
export ANTHROPIC_API_KEY="your-key"
export EKASA_API_KEY="your-key"
export DATA_PATH="~/Documents/MileageLog/data"

# Install dependencies (when code exists)
pip install -r requirements.txt
cd mcp-servers/geo-routing && npm install
```

## Success Metrics

**Hackathon MVP (Nov 30):**
- 7 MCP servers functional
- 5-minute demo video completed
- End-to-end workflow: Receipt → Trip → Report
- Slovak compliance verified

**Production-Ready (Post-Hackathon):**
- >80% unit test coverage
- 1000+ trips performance tested
- Multi-vehicle support
- PDF report generation
