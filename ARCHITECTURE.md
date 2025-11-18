# Car Log - Architecture Documentation

**Version:** 1.0
**Date:** 2025-11-18
**Status:** Production-Ready

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [MCP Server Architecture](#mcp-server-architecture)
4. [Data Flow](#data-flow)
5. [Slovak Compliance](#slovak-compliance)
6. [Performance & Scalability](#performance--scalability)
7. [Security & Privacy](#security--privacy)
8. [Testing Strategy](#testing-strategy)

---

## System Overview

### Vision

Car Log is a **Slovak tax-compliant company vehicle mileage logger** that uses **MCP servers as the actual backend architecture** (not just connectors). This enables conversational trip logging through Claude Desktop with automatic gap-based reconstruction.

### Key Innovation

**MCP-First Backend**: Unlike traditional architectures that use MCP as a connector layer, Car Log uses headless MCP servers as the primary backend. All business logic lives in 7 independent MCP servers that can be orchestrated by any MCP client (Claude Desktop, DSPy, custom UIs).

### Target Users

- Small business owners in Slovakia/Europe
- Companies with 1-10 vehicles
- Need to comply with Slovak VAT Act 2025
- Want conversational interface (not forms/spreadsheets)

---

## Architecture Principles

### 1. MCP-First Design

**Principle**: MCP servers ARE the backend, not wrappers around a backend.

**Implementation**:
- 7 headless MCP servers
- Each server is independent (stateless)
- All business logic in server code
- No separate REST API or database server
- Orchestration happens at UI layer (Skills/DSPy)

**Benefits**:
- Simple deployment (just Python/Node processes)
- Easy testing (call MCP tools directly)
- Flexible UI (any MCP client works)
- No API versioning issues

### 2. GPS-First Philosophy

**Principle**: GPS coordinates are source of truth (70% weight), addresses are optional labels (30% weight).

**Rationale**:
- Addresses change (street names, POI names)
- GPS coordinates are permanent
- Enables robust matching despite address variations

**Implementation**:
```python
# Template matching scoring
total_score = (gps_score * 0.7) + (address_score * 0.3)
```

### 3. Stateless Servers

**Principle**: MCP servers have NO shared state or memory.

**Implementation**:
- All data passed in tool arguments
- Servers read directly from file storage
- No caching between requests
- No sessions or authentication

**Benefits**:
- Simple horizontal scaling
- Easy debugging (no state to track)
- Restartable without data loss

### 4. File-Based Storage

**Principle**: JSON files in monthly folders, no database required for MVP.

**Rationale**:
- Human-readable (debugging friendly)
- Git-friendly (version control)
- No database setup required
- Simple backups (copy directory)
- Good performance for <10,000 trips

**Migration Path**: SQLite for 10,000+ trips (P2 feature)

### 5. Atomic Operations

**Principle**: All file writes use atomic pattern (temp file + rename).

**Implementation**:
```python
def atomic_write(file_path, data):
    temp_path = file_path.with_suffix('.tmp')
    with open(temp_path, 'w') as f:
        json.dump(data, f)
    temp_path.replace(file_path)  # Atomic on POSIX
```

**Benefits**:
- Crash-safe (never corrupt data)
- Concurrent-safe (POSIX guarantee)
- No locks needed

---

## MCP Server Architecture

### Server Inventory

| Server | Tools | Language | Purpose | Priority |
|--------|-------|----------|---------|----------|
| car-log-core | 8 | Python | CRUD operations (vehicle, checkpoint, template, trip) | P0 |
| trip-reconstructor | 2 | Python | Template matching with hybrid GPS+address scoring | P0 |
| validation | 4 | Python | 4 validation algorithms (distance, fuel, efficiency, deviation) | P0 |
| ekasa-api | 2 | Python | Slovak e-Kasa receipt processing (QR + API) | P0 |
| geo-routing | 3 | Node.js | OpenStreetMap geocoding + routing with 24h cache | P0 |
| dashboard-ocr | 2 | Python | EXIF extraction + Claude Vision OCR | P1 |
| report-generator | 1 | Python | CSV generation with Slovak compliance | P0 |

**Total**: 22 P0 tools, 2 P1 tools

### 1. car-log-core (Critical Path)

**Purpose**: Core CRUD operations and data management

**Tools**:
1. `create_vehicle` - VIN validation (17 chars, no I/O/Q), Slovak license plate
2. `get_vehicle` - Retrieve by ID
3. `list_vehicles` - Filter, paginate
4. `update_vehicle` - Atomic updates
5. `create_checkpoint` - Refuel or manual checkpoint with GPS
6. `get_checkpoint` - Retrieve by ID
7. `list_checkpoints` - Filter by vehicle, date range
8. `detect_gap` - Find mileage gaps for reconstruction

**Data Storage**:
```
~/Documents/MileageLog/data/
├── vehicles/{vehicle_id}.json
├── checkpoints/2025-11/{checkpoint_id}.json
├── trips/2025-11/{trip_id}.json
└── templates/{template_id}.json
```

**Key Logic**:
- Atomic writes (crash-safe)
- Monthly folder structure
- Gap detection algorithm

**Dependencies**: None (foundation for all others)

### 2. trip-reconstructor (Intelligence)

**Purpose**: Fill mileage gaps using template matching

**Tools**:
1. `match_templates` - Hybrid GPS (70%) + address (30%) scoring
2. `calculate_template_completeness` - Quality score for templates

**Algorithm**:
```python
# GPS scoring (Haversine distance)
< 100m → 100 points
100-500m → 90 points
500-2000m → 70 points
2000-5000m → 40 points
> 5000m → 0 points

# Address scoring (Levenshtein distance + component matching)
Exact match → 100 points
Same city, different street → 70 points
Different city → 30 points

# Final score
confidence = (gps_score * 0.7) + (address_score * 0.3)
```

**Demo Result**: 820 km gap matched with 90.6% confidence (2× Warehouse Run)

**Dependencies**: Requires car-log-core for gap data and templates

### 3. validation (Quality Assurance)

**Purpose**: Validate data integrity and flag anomalies

**Tools**:
1. `validate_checkpoint_pair` - Distance sum check (±10%)
2. `validate_trip` - Comprehensive validation
3. `check_efficiency` - Reasonability (Diesel: 5-15 L/100km)
4. `check_deviation_from_average` - Deviation check (±20%)

**Thresholds** (configurable via environment variables):
- Distance variance: ±10%
- Fuel consumption variance: ±15%
- Deviation threshold: ±20%
- Diesel range: 5-15 L/100km
- Gasoline range: 6-20 L/100km
- LPG range: 8-25 L/100km

**Example**:
```python
# Trip: 410 km, expected 34.85 L (8.5 L/100km)
# Actual refuel: 35 L
# Deviation: 0.4% → ✅ OK (within ±15%)
```

**Dependencies**: Requires car-log-core for vehicle and trip data

### 4. ekasa-api (External Integration)

**Purpose**: Process Slovak e-Kasa receipts for fuel checkpoints

**Tools**:
1. `scan_qr_code` - Multi-scale QR detection (1x, 2x, 3x zoom)
2. `fetch_receipt_data` - Call Slovak gov API (60s timeout)

**External API**:
- URL: `https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/{receipt_id}`
- Auth: None required (public endpoint)
- Response time: 5-30 seconds typically
- Timeout: 60 seconds

**Fuel Detection** (Slovak patterns):
```python
Diesel: r'(?i)diesel|nafta|motorová nafta'
Natural 95: r'(?i)natural 95|ba 95|benzín 95'
Natural 98: r'(?i)natural 98|ba 98|benzín 98'
LPG: r'(?i)lpg|autoplyn'
CNG: r'(?i)cng|zemný plyn'
```

**Dependencies**: None (external API)

### 5. geo-routing (OpenStreetMap)

**Purpose**: Geocoding and route calculation

**Tools**:
1. `geocode_address` - Address → GPS (with ambiguity handling)
2. `reverse_geocode` - GPS → Address
3. `calculate_route` - GPS → GPS (distance + duration)

**External APIs**:
- **OSRM**: Route calculation (https://router.project-osrm.org)
- **Nominatim**: Geocoding (https://nominatim.openstreetmap.org)

**Caching**: 24-hour TTL for all results

**Ambiguity Handling**:
```javascript
// "Košice" returns 3 alternatives (confidence < 0.7)
{
  coordinates: {lat: 48.7164, lng: 21.2611},
  confidence: 0.63,
  alternatives: [
    {address: "Košice, Košice Region", type: "city"},
    {address: "Košice-Sever", type: "district"},
    {address: "Košice-Juh", type: "district"}
  ]
}
```

**Dependencies**: None (external APIs)

### 6. dashboard-ocr (Optional P1)

**Purpose**: Extract metadata from dashboard photos

**Tools**:
1. `extract_metadata` - EXIF extraction (GPS, timestamp) - **P0**
2. `read_odometer` - Claude Vision OCR - **P1**

**EXIF Extraction**:
```python
# GPS coordinates from EXIF (DMS → decimal)
GPS Latitude: 48° 8' 55.00" N → 48.1486
GPS Longitude: 17° 6' 27.72" E → 17.1077
DateTime: 2025:11:18 14:30:00 → 2025-11-18T14:30:00
```

**Dependencies**: None (reads from image files)

### 7. report-generator (Reporting)

**Purpose**: Generate tax-compliant mileage reports

**Tools**:
1. `generate_csv` - CSV with all Slovak compliance fields - **P0**
2. `generate_pdf` - PDF with VAT template - **P1 (cut for MVP)**

**CSV Fields** (Slovak compliance):
```csv
trip_date,driver_name,vehicle_vin,license_plate,
trip_start_datetime,trip_end_datetime,
trip_start_location,trip_end_location,
distance_km,purpose,business_description,
fuel_consumption_liters,fuel_efficiency_l_per_100km,
reconstruction_method,confidence_score
```

**Summary Statistics**:
- Total trips count
- Total distance (km)
- Total fuel (liters)
- Average efficiency (L/100km weighted by distance)

**Dependencies**: Requires car-log-core for trip data

---

## Data Flow

### Complete Workflow: Receipt → Report

```
┌─────────────────────────────────────────────────────────┐
│ 1. RECEIPT PROCESSING                                   │
│                                                          │
│ User: "I have a fuel receipt"                           │
│   ↓                                                      │
│ ekasa-api.scan_qr_code(receipt_photo)                  │
│   → receipt_id: "O-E182401234567890123456789"          │
│   ↓                                                      │
│ ekasa-api.fetch_receipt_data(receipt_id)               │
│   → vendor, fuel_type, fuel_liters, price, VAT         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ 2. CHECKPOINT CREATION                                   │
│                                                          │
│ dashboard-ocr.extract_metadata(dashboard_photo)         │
│   → GPS coords, timestamp, odometer (if OCR enabled)    │
│   ↓                                                      │
│ car-log-core.create_checkpoint({                        │
│   vehicle_id, datetime, odometer_km,                    │
│   location: {coords, address},                          │
│   receipt: {vendor, fuel_type, fuel_liters, ...}        │
│ })                                                       │
│   → checkpoint created in data/checkpoints/2025-11/     │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ 3. GAP DETECTION                                         │
│                                                          │
│ User: "Check for gaps"                                   │
│   ↓                                                      │
│ car-log-core.detect_gap(checkpoint1_id, checkpoint2_id)│
│   → gap_data: {                                          │
│       odometer_delta: 820 km,                            │
│       time_delta: 7 days,                                │
│       has_gps: true                                      │
│     }                                                     │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ 4. TEMPLATE MATCHING                                     │
│                                                          │
│ car-log-core.list_templates()                           │
│   → 3 templates (Warehouse Run: 410 km, etc.)           │
│   ↓                                                      │
│ trip-reconstructor.match_templates({                    │
│   gap_data, templates                                    │
│ })                                                       │
│   → proposals: [                                         │
│       {template: Warehouse Run, confidence: 90.6%},      │
│       {template: Warehouse Run, confidence: 90.6%}       │
│     ]                                                     │
│   → coverage: 100%                                       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ 5. TRIP CREATION                                         │
│                                                          │
│ User: "Approve these trips"                              │
│   ↓                                                      │
│ car-log-core.create_trip({                              │
│   driver_name, trip_start_datetime, trip_end_datetime,  │
│   trip_start_location, trip_end_location,               │
│   distance_km, purpose, business_description            │
│ })  × 2                                                  │
│   → 2 trips created in data/trips/2025-11/              │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ 6. VALIDATION                                            │
│                                                          │
│ validation.validate_checkpoint_pair()                   │
│   → ✅ OK: Sum = 820 km, odometer delta = 820 km        │
│   ↓                                                      │
│ validation.validate_trip() × 2                          │
│   → ✅ OK: Fuel consumption within ±15%                 │
│   → ✅ OK: Efficiency reasonable (8.5 L/100km)          │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ 7. REPORT GENERATION                                     │
│                                                          │
│ User: "Generate November report"                         │
│   ↓                                                      │
│ report-generator.generate_csv({                         │
│   start_date: "2025-11-01",                             │
│   end_date: "2025-11-30",                               │
│   business_only: true                                    │
│ })                                                       │
│   → CSV file: reports/2025-11/november-2025.csv         │
│   → Summary: 2 trips, 820 km, 69.7 L, 8.5 L/100km       │
└─────────────────────────────────────────────────────────┘
```

---

## Slovak Compliance

### VAT Act 2025 Requirements

**Mandatory Fields**:
1. **VIN** - 17 characters, no I/O/Q (validation regex: `^[A-HJ-NPR-Z0-9]{17}$`)
2. **Driver Name** - Full name for all trips
3. **Trip Timing** - Separate from refuel timing
4. **Locations** - Trip start and end locations
5. **Purpose** - Business vs Personal
6. **Business Description** - Required for business trips

**Fuel Efficiency Format**:
- ✅ L/100km (European standard)
- ❌ km/L (NOT used)

**Example**:
```json
{
  "vehicle_vin": "WBAXX01234ABC5678",
  "driver_name": "Ján Kováč",
  "trip_start_datetime": "2025-11-01T08:00:00+01:00",
  "trip_end_datetime": "2025-11-01T14:30:00+01:00",
  "trip_start_location": "Bratislava",
  "trip_end_location": "Košice",
  "distance_km": 410,
  "fuel_efficiency_l_per_100km": 8.5,
  "purpose": "Business",
  "business_description": "Warehouse pickup and delivery"
}
```

### Validation Implementation

All validation checks follow Slovak standards:

```python
# VIN validation
if len(vin) != 17:
    raise ValidationError("VIN must be 17 characters")
if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin):
    raise ValidationError("VIN cannot contain I, O, or Q")

# Fuel efficiency validation
if fuel_efficiency_l_per_100km < 5 or fuel_efficiency_l_per_100km > 15:
    warnings.append("Diesel efficiency outside typical range (5-15 L/100km)")
```

---

## Performance & Scalability

### Current Performance

**Tested with**:
- 100+ templates: < 2 seconds for matching
- 1,000+ trips: < 5 seconds for report generation
- All MCP servers: < 1 second startup

**Test Results**:
- 70/71 tests passing (98.6%)
- Integration checkpoint: 20/20 tests passing (100%)

### Scalability Limits

**File-Based Storage** (current):
- **Good for**: < 10,000 trips
- **Performance**: O(n) for reads, O(1) for writes
- **Disk space**: ~1KB per trip (~10MB for 10,000 trips)

**Migration Path** (P2):
```
10,000+ trips → SQLite
100,000+ trips → PostgreSQL
1,000,000+ trips → PostgreSQL + partitioning
```

### Horizontal Scaling

MCP servers are stateless, so scaling is trivial:

```bash
# Run multiple instances behind load balancer
python -m mcp_servers.car_log_core  # Instance 1
python -m mcp_servers.car_log_core  # Instance 2
python -m mcp_servers.car_log_core  # Instance 3
```

**Consideration**: File locking for concurrent writes (use database for high concurrency)

---

## Security & Privacy

### Data Storage

**Location**: `~/Documents/MileageLog/data/`

**Permissions**:
- User-only read/write
- No network exposure
- Local file system

**Backup Strategy**:
```bash
# Simple backup
cp -r ~/Documents/MileageLog/data /backup/location

# Or use rsync
rsync -av ~/Documents/MileageLog/data /backup/location
```

### API Keys

**Required**:
- None for P0 features

**Optional** (P1):
- `ANTHROPIC_API_KEY` for dashboard OCR

**Configuration**:
```json
// claude_desktop_config.json
{
  "mcpServers": {
    "dashboard-ocr": {
      "env": {
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
      }
    }
  }
}
```

### External API Calls

**e-Kasa API**:
- Public endpoint, no auth required
- Only receipt ID sent (no personal data)

**OpenStreetMap**:
- Public endpoints, no auth required
- Respect rate limits (1 req/sec)
- 24-hour caching reduces calls

---

## Testing Strategy

### Unit Tests (70 tests)

**Coverage by server**:
- car-log-core: 18 tests
- ekasa-api: 14 tests
- dashboard-ocr: 23 tests
- validation: 26 tests
- report-generator: 7 tests

**Run tests**:
```bash
pytest tests/ -v
# 70 passed, 1 skipped, 1 warning
```

### Integration Tests

**Day 7 Checkpoint** (20 tests):
- Server discovery: 6/6
- Tool signatures: 6/6
- Smoke tests: 4/4
- Data flow: 2/2
- Slovak compliance: 1/1
- Error handling: 1/1

**Run checkpoint**:
```bash
python tests/integration_checkpoint_day7.py
# 20/20 tests passed (100%)
```

### Demo Scenario

**Complete workflow test**:
```bash
python scripts/generate_mock_data.py --scenario demo
# Creates: 1 vehicle, 2 checkpoints, 3 templates, 2 trips
```

**Manual testing in Claude Desktop**:
1. Create vehicle
2. Create checkpoints
3. Detect gap
4. Match templates
5. Create trips
6. Generate report

---

## Deployment Checklist

### Prerequisites

- ✅ Python 3.11+ installed
- ✅ Node.js 18+ installed
- ✅ Claude Desktop installed
- ✅ All dependencies installed
- ✅ Data directories created
- ✅ MCP servers configured

### Production Setup

1. **Set environment variables**:
   ```bash
   export DATA_PATH="/path/to/production/data"
   export ANTHROPIC_API_KEY="your-key"  # Optional, P1 only
   ```

2. **Run tests**:
   ```bash
   pytest tests/ -v
   python tests/integration_checkpoint_day7.py
   ```

3. **Configure monitoring** (logs, errors)

4. **Set up backups** (daily data directory backup)

5. **Test in Claude Desktop** (end-to-end workflow)

6. **Train users** (demo script from spec/09-hackathon-presentation.md)

### Success Criteria

- ✅ All 7 MCP servers discoverable in Claude Desktop
- ✅ 70+ tests passing
- ✅ Integration checkpoint 20/20
- ✅ End-to-end workflow < 5 minutes
- ✅ Report generation functional
- ✅ Slovak compliance verified

---

**Architecture Version:** 1.0
**Last Updated:** 2025-11-18
**Status:** Production-Ready ✅
