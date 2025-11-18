# Key Enhancements from Milestone-Based Specification

**Date:** 2025-11-17
**Purpose:** Document all valuable content from `company-vehicle-mileage-log` folder to integrate into `car-log` specification
**Status:** Review Complete - Ready for Integration

---

## Executive Summary

The `company-vehicle-mileage-log` folder contains a comprehensive, production-ready specification for a Slovak tax-compliant mileage tracking application. While using "Milestone" terminology instead of "Checkpoint," the core concepts are **identical** to our car-log approach.

**Key Discovery:** Both specifications use the same fundamental architecture - point-in-time vehicle state markers (Checkpoints/Milestones) for gap-based trip reconstruction.

**Critical Enhancements to Integrate:**
1. Slovak VAT Act compliance fields (VIN, driver name, trip times/locations)
2. L/100km fuel efficiency format (European standard)
3. Validation algorithms with specific thresholds
4. File-based storage architecture (no database for MVP)
5. Complete MCP API tool signatures
6. 17-day implementation timeline with daily checkpoints
7. Hackathon presentation strategy

---

## Part 1: Slovak Tax Compliance (CRITICAL - P0)

### From: `04-slovak-tax-compliance.md`

**Legal Context:**
- **Income Tax Act:** zákon č. 595/2003 Z. z.
- **VAT Act:** Effective 1 January 2025 (stricter rules from 1 January 2026)
- **Requirement:** 100% VAT deduction requires ride-by-ride records

### Required Fields (Practice-Based from Accountants)

**Vehicle:**
```json
{
  "vin": "WBAXX01234ABC5678",           // NEW: 17-char alphanumeric, MANDATORY
  "vin_verified": true                   // NEW: Verification status
}
```
- **Validation:** `^[A-HJ-NPR-Z0-9]{17}$` (no I, O, Q)
- **Why Critical:** VIN is required for VAT deduction under 2025 rules

**Trip Entry - Add These Fields:**
```json
{
  // TIMING FIELDS (separate refuel time from trip time!)
  "trip_start_datetime": "2025-11-15T09:00:00Z",  // NEW: When trip started
  "trip_end_datetime": "2025-11-15T13:00:00Z",    // NEW: When trip ended
  "refuel_datetime": "2025-11-15T08:45:00Z",      // Existing: When refueled
  "refuel_timing": "before",                       // NEW: before/during/after trip

  // LOCATION FIELDS (separate trip locations from fuel station!)
  "trip_start_location": "Bratislava Office, Hlavná 12",  // NEW: Trip origin
  "trip_end_location": "Client ABC, Košice",              // NEW: Trip destination
  "vendor_location": "Shell Bratislava West",             // Existing: Fuel station

  // DRIVER FIELDS (required for multi-driver vehicles)
  "driver_name": "Ján Novák",                      // NEW: MANDATORY
  "driver_id": "uuid-or-null",                     // NEW: Optional link to Driver entity
  "driver_is_owner": true                          // NEW: Flag for quick filtering
}
```

**Why This Matters:**
- Slovak tax inspectors require **separate trip timing from refuel timing**
- Example: Refuel Monday 8am → Trip Monday 9am-5pm (different times!)
- GPS coordinates remain OPTIONAL (not legally required, but strongly recommended)

### Implementation in car-log

**Action Items:**
1. Update `04-data-model.md` Vehicle entity with VIN field
2. Update `04-data-model.md` Trip entity with timing/location/driver fields
3. Add validation rules for VIN format
4. Update all example data to include these fields
5. Ensure PDF report generator includes all required fields

**Priority:** P0 (Must have for tax compliance)

---

## Part 2: Fuel Efficiency Format - L/100km (CRITICAL - P0)

### From: `09-mvp-decisions.md`, `03-european-localization-fixes.md`

**Decision:** Use L/100km (liters per 100 kilometers) ONLY for MVP

**Current car-log spec:** Uses km/L format
**Required change:** Switch to L/100km as PRIMARY format

### Why L/100km?

**European Standard:**
- Used by all car manufacturers in EU
- Shown on all fuel economy labels in Slovakia/Europe
- Users think in "how many liters to drive 100km?"
- Lower number = more efficient (intuitive for Europeans)

**Conversion Formula:**
```javascript
// From km/L to L/100km:
L_per_100km = 100 / km_per_liter

// From L/100km to km/L:
km_per_liter = 100 / L_per_100km

// Direct calculation from trip data:
L_per_100km = (fuel_liters / distance_km) * 100

// Example:
// 50.5L fuel, 200km distance
// L/100km = (50.5 / 200) * 100 = 25.25 L/100km
// km/L = 100 / 25.25 = 3.96 km/L
```

### Validation Range

**Realistic range for cars/vans:**
- **Minimum:** 4.0 L/100km (very efficient hybrid)
- **Maximum:** 20.0 L/100km (large van, heavy load)
- **Typical passenger car:** 6-10 L/100km
- **Typical van (like Ford Transit):** 8-12 L/100km

**From `09-mvp-decisions.md`:**
```json
{
  "efficiency_min_l_per_100km": 4.0,
  "efficiency_max_l_per_100km": 20.0,
  "efficiency_warning_threshold_percent": 20  // Warn if >20% deviation from average
}
```

### Implementation in car-log

**Action Items:**
1. Update all efficiency calculations in `03-trip-reconstruction.md`
2. Change data model field: `fuel_efficiency_l_per_100km` (rename from km/L)
3. Update validation rules in domain model
4. Update all example data (convert existing km/L values)
5. Update report templates to show L/100km
6. Add formula documentation in technical sections

**Display Options:**
- **Primary (MVP):** Show L/100km only
- **Optional (P1):** Show both: "7.5 L/100km (13.3 km/L)" for users familiar with km/L

**Priority:** P0 (User-facing format change)

---

## Part 3: Validation Algorithms with Thresholds (IMPORTANT - P0)

### From: `05-milestone-trip-reconstruction.md`, `13-data-models.md`

The milestone spec has **4 specific validation algorithms** with **concrete thresholds** that we should adopt.

### Algorithm 1: Distance Sum Validation

**Purpose:** Verify that reconstructed trip distances match the odometer delta

```javascript
function validate_distance_sum(trips, actual_odometer_delta) {
  const total_trip_distance = trips.reduce((sum, trip) => sum + trip.distance, 0);
  const variance_percent = Math.abs(total_trip_distance - actual_odometer_delta) / actual_odometer_delta * 100;

  const THRESHOLD = 10; // 10% tolerance

  if (variance_percent <= THRESHOLD) {
    return { status: "ok", variance: variance_percent };
  } else {
    return {
      status: "warning",
      variance: variance_percent,
      message: `Trip distances total ${total_trip_distance}km, but odometer shows ${actual_odometer_delta}km. Difference: ${variance_percent.toFixed(1)}%`,
      suggestion: "Add missing trips or check odometer readings"
    };
  }
}
```

**Threshold:** ±10% acceptable variance
**Rationale:** Accounts for rounding, short local trips, odometer accuracy

### Algorithm 2: Fuel Consumption Validation

**Purpose:** Verify that calculated fuel consumption matches actual fuel purchased

```javascript
function validate_fuel_consumption(trips, actual_fuel_liters, vehicle_avg_efficiency_l_per_100km) {
  const total_distance = trips.reduce((sum, trip) => sum + trip.distance, 0);
  const expected_fuel_liters = (total_distance / 100) * vehicle_avg_efficiency_l_per_100km;
  const variance_percent = Math.abs(expected_fuel_liters - actual_fuel_liters) / actual_fuel_liters * 100;

  const THRESHOLD = 15; // 15% tolerance

  if (variance_percent <= THRESHOLD) {
    return { status: "ok", variance: variance_percent };
  } else {
    return {
      status: "warning",
      variance: variance_percent,
      expected_fuel: expected_fuel_liters,
      actual_fuel: actual_fuel_liters,
      message: `Expected ${expected_fuel_liters.toFixed(1)}L based on distance, but you refueled ${actual_fuel_liters}L. Difference: ${variance_percent.toFixed(1)}%`,
      suggestion: "Vehicle efficiency may have changed (weather, driving style, load)"
    };
  }
}
```

**Threshold:** ±15% acceptable variance
**Rationale:** Fuel efficiency varies with driving conditions, load, weather

### Algorithm 3: Efficiency Reasonability Check

**Purpose:** Ensure fuel efficiency is within realistic bounds

```javascript
function check_efficiency_reasonability(efficiency_l_per_100km, fuel_type) {
  const ranges = {
    "Diesel": { min: 5.0, max: 15.0 },
    "Gasoline": { min: 6.0, max: 20.0 },
    "LPG": { min: 8.0, max: 25.0 },
    "Hybrid": { min: 3.0, max: 8.0 },
    "Electric": { min: 12.0, max: 25.0 }  // kWh/100km
  };

  const range = ranges[fuel_type] || { min: 4.0, max: 20.0 };

  if (efficiency_l_per_100km < range.min) {
    return {
      status: "error",
      message: `Efficiency ${efficiency_l_per_100km} L/100km is unrealistically LOW for ${fuel_type}. Check distance or fuel quantity.`,
      expected_range: range
    };
  } else if (efficiency_l_per_100km > range.max) {
    return {
      status: "error",
      message: `Efficiency ${efficiency_l_per_100km} L/100km is unrealistically HIGH for ${fuel_type}. Check distance or fuel quantity.`,
      expected_range: range
    };
  } else {
    return { status: "ok", efficiency: efficiency_l_per_100km };
  }
}
```

**Thresholds:** Fuel-type specific ranges
**Rationale:** Different fuels have different typical efficiency ranges

### Algorithm 4: Deviation from Vehicle Average

**Purpose:** Detect unusual trips that deviate significantly from vehicle's historical average

```javascript
function check_deviation_from_average(trip_efficiency_l_per_100km, vehicle_avg_efficiency_l_per_100km) {
  const deviation_percent = Math.abs(trip_efficiency_l_per_100km - vehicle_avg_efficiency_l_per_100km) / vehicle_avg_efficiency_l_per_100km * 100;

  const WARNING_THRESHOLD = 20; // 20% deviation

  if (deviation_percent > WARNING_THRESHOLD) {
    return {
      status: "warning",
      deviation: deviation_percent,
      message: `Trip efficiency ${trip_efficiency_l_per_100km} L/100km differs by ${deviation_percent.toFixed(0)}% from your average ${vehicle_avg_efficiency_l_per_100km} L/100km`,
      suggestion: "This could be normal (highway vs city, load, weather) or indicate data entry error"
    };
  } else {
    return { status: "ok", deviation: deviation_percent };
  }
}
```

**Threshold:** 20% deviation triggers warning
**Rationale:** Alerts user to unusual trips while allowing for normal variation

### Validation Configuration

**From `13-data-models.md`:**
```json
{
  "validation_config": {
    "distance_variance_percent": 10,
    "consumption_variance_percent": 15,
    "efficiency_deviation_percent": 20,
    "efficiency_ranges": {
      "Diesel": { "min_l_per_100km": 5.0, "max_l_per_100km": 15.0 },
      "Gasoline": { "min_l_per_100km": 6.0, "max_l_per_100km": 20.0 },
      "LPG": { "min_l_per_100km": 8.0, "max_l_per_100km": 25.0 },
      "Hybrid": { "min_l_per_100km": 3.0, "max_l_per_100km": 8.0 }
    }
  }
}
```

### Implementation in car-log

**Action Items:**
1. Create new section in `03-trip-reconstruction.md`: "Validation Algorithms"
2. Document all 4 algorithms with thresholds
3. Add validation config to data model
4. Update MCP `validation-server` tool specifications
5. Add validation result data structures (ok/warning/error)

**Priority:** P0 (Core credibility feature)

---

## Part 4: File-Based Storage Architecture (ARCHITECTURAL - P0)

### From: `13-data-models.md`, `06-claude-desktop-mcp-architecture.md`

**Key Decision:** Use JSON files instead of database for MVP

### Rationale

**Advantages:**
- ✅ **Human-readable:** Users can inspect/edit data in text editor
- ✅ **Git-friendly:** Version control for business records
- ✅ **Portable:** Copy folder = complete backup
- ✅ **No setup:** No database installation or configuration
- ✅ **Transparent:** Users see exactly what data is stored
- ✅ **Privacy:** Data stays local, user controls

**Trade-offs:**
- ⚠️ Performance: Slower for 1000+ trips (acceptable for MVP)
- ⚠️ Querying: No SQL (use file system + JSON parsing)
- ⚠️ Concurrency: File locking needed (single-user app, not critical)

### File Structure

```
~/Documents/MileageLog/
├── data/
│   ├── config.json                    # App configuration
│   ├── vehicles/
│   │   └── {vehicle-id}.json          # One file per vehicle
│   ├── checkpoints/                   # (or "milestones" in original spec)
│   │   └── {YYYY-MM}/
│   │       └── {checkpoint-id}.json   # Month-based folders
│   ├── trips/
│   │   └── {YYYY-MM}/
│   │       └── {trip-id}.json         # Month-based folders
│   └── typical-destinations.json      # Saved locations
├── receipts/
│   └── {YYYY-MM}/
│       ├── {receipt-id}.json          # Receipt metadata
│       └── {receipt-id}-photo.jpg     # Receipt photo
├── dashboard-photos/
│   └── {YYYY-MM}/
│       └── {checkpoint-id}.jpg        # Dashboard photos
└── reports/
    └── {YYYY-MM}/
        ├── november-2025.pdf
        └── november-2025.csv
```

### Data Model: Vehicle File

**File:** `data/vehicles/{vehicle-id}.json`

```json
{
  "vehicle_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Ford Transit Delivery Van",
  "license_plate": "BA-456CD",
  "vin": "WBAXX01234ABC5678",
  "make": "Ford",
  "model": "Transit",
  "year": 2022,
  "fuel_type": "Diesel",
  "initial_odometer_km": 15000,
  "current_odometer_km": 45550,
  "average_efficiency_l_per_100km": 11.0,
  "active": true,
  "created_at": "2025-01-01T10:00:00Z",
  "updated_at": "2025-11-15T14:30:00Z"
}
```

### Data Model: Checkpoint File

**File:** `data/checkpoints/2025-11/{checkpoint-id}.json`

```json
{
  "checkpoint_id": "660e8400-e29b-41d4-a716-446655440001",
  "vehicle_id": "550e8400-e29b-41d4-a716-446655440000",
  "checkpoint_type": "refuel",
  "datetime": "2025-11-15T08:45:00Z",
  "odometer_km": 45550,
  "odometer_source": "photo",
  "odometer_photo_path": "dashboard-photos/2025-11/660e8400-dashboard.jpg",
  "odometer_confidence": 0.95,
  "location": {
    "address": "Shell Bratislava West, Hlavná 12",
    "coords": { "lat": 48.1486, "lng": 17.1077 },
    "city": "Bratislava"
  },
  "receipt": {
    "receipt_id": "ekasa-abc123xyz",
    "receipt_photo_path": "receipts/2025-11/ekasa-abc123xyz-photo.jpg",
    "vendor_name": "Shell Slovakia",
    "fuel_type": "Diesel",
    "fuel_liters": 50.5,
    "fuel_cost_eur": 72.50,
    "price_per_liter": 1.44,
    "total_amount_eur": 72.50,
    "vat_amount_eur": 12.08
  },
  "previous_checkpoint_id": "660e8400-e29b-41d4-a716-446655440000",
  "distance_since_previous_km": 200,
  "created_at": "2025-11-15T08:50:00Z"
}
```

### Data Model: Trip File

**File:** `data/trips/2025-11/{trip-id}.json`

```json
{
  "trip_id": "770e8400-e29b-41d4-a716-446655440002",
  "vehicle_id": "550e8400-e29b-41d4-a716-446655440000",
  "checkpoint_start_id": "660e8400-e29b-41d4-a716-446655440000",
  "checkpoint_end_id": "660e8400-e29b-41d4-a716-446655440001",

  "trip_start_datetime": "2025-11-15T09:00:00Z",
  "trip_end_datetime": "2025-11-15T13:00:00Z",
  "trip_duration_hours": 4.0,

  "trip_start_location": "Bratislava Office, Hlavná 12",
  "trip_end_location": "Client ABC, Košice, Mlynská 45",
  "trip_start_coords": { "lat": 48.1486, "lng": 17.1077 },
  "trip_end_coords": { "lat": 48.7164, "lng": 21.2611 },

  "driver_name": "Ján Novák",
  "driver_is_owner": true,

  "distance_km": 280,
  "fuel_consumption_liters": 25.0,
  "fuel_efficiency_l_per_100km": 8.93,
  "fuel_cost_eur": 36.25,

  "trip_purpose": "Business",
  "business_purpose_description": "Client meeting - product demonstration",

  "refuel_datetime": "2025-11-15T08:45:00Z",
  "refuel_timing": "before",

  "reconstruction_method": "template",
  "template_used": "Warehouse Run to Košice",
  "confidence_score": 0.92,

  "validation": {
    "status": "validated",
    "distance_check": "ok",
    "efficiency_check": "ok",
    "warnings": []
  },

  "created_at": "2025-11-15T14:00:00Z",
  "updated_at": "2025-11-15T14:00:00Z"
}
```

### Atomic Write Pattern

**Critical:** Never write directly to final file (risk of corruption)

```javascript
// CORRECT: Atomic write pattern
async function saveTrip(trip) {
  const finalPath = `data/trips/${trip.month}/${trip.id}.json`;
  const tempPath = `${finalPath}.tmp`;

  // 1. Write to temp file
  await fs.writeFile(tempPath, JSON.stringify(trip, null, 2), 'utf-8');

  // 2. Atomic rename (OS-level operation, can't be interrupted)
  await fs.rename(tempPath, finalPath);

  // Result: Either complete success or complete failure, never corrupted file
}

// WRONG: Direct write (can be interrupted, corrupts file)
async function saveTripWrong(trip) {
  const path = `data/trips/${trip.month}/${trip.id}.json`;
  await fs.writeFile(path, JSON.stringify(trip, null, 2), 'utf-8');
  // If process crashes during write → corrupted JSON file!
}
```

### Index Files for Performance

**Optional optimization:** Create monthly index files

**File:** `data/trips/2025-11/index.json`

```json
{
  "month": "2025-11",
  "vehicle_id": "550e8400-e29b-41d4-a716-446655440000",
  "trip_count": 28,
  "total_distance_km": 2300,
  "total_fuel_liters": 195.0,
  "total_cost_eur": 292.50,
  "trip_ids": [
    "770e8400-e29b-41d4-a716-446655440002",
    "770e8400-e29b-41d4-a716-446655440003",
    ...
  ],
  "generated_at": "2025-12-01T00:00:00Z"
}
```

**Benefits:**
- Fast monthly summary without reading all trip files
- Quick validation of data completeness
- Easy to regenerate if corrupted

### Implementation in car-log

**Action Items:**
1. Update `04-data-model.md` with complete JSON schemas
2. Add file structure diagram
3. Document atomic write pattern
4. Add index file specification (optional)
5. Update MCP server specs to use file-based storage

**Priority:** P0 (Fundamental architectural decision)

---

## Part 5: Complete MCP API Tool Signatures (DETAILED - P0)

### From: `14-mcp-api-specifications.md`, `06-claude-desktop-mcp-architecture.md`

The milestone spec has **complete, production-ready MCP tool definitions** with full input/output schemas.

### Example: Create Vehicle Tool

**Tool Name:** `create_vehicle`
**Server:** `trip-manager-server`

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 50,
      "description": "Human-readable vehicle name"
    },
    "license_plate": {
      "type": "string",
      "pattern": "^[A-Z]{2}-[0-9]{3}[A-Z]{2}$",
      "description": "Slovak license plate format (e.g., BA-456CD)"
    },
    "vin": {
      "type": "string",
      "pattern": "^[A-HJ-NPR-Z0-9]{17}$",
      "description": "Vehicle Identification Number (17 characters, no I/O/Q)"
    },
    "make": {
      "type": "string",
      "maxLength": 30,
      "description": "Vehicle manufacturer (e.g., Ford)"
    },
    "model": {
      "type": "string",
      "maxLength": 30,
      "description": "Vehicle model (e.g., Transit)"
    },
    "year": {
      "type": "integer",
      "minimum": 1900,
      "maximum": 2030,
      "description": "Manufacturing year"
    },
    "fuel_type": {
      "type": "string",
      "enum": ["Diesel", "Gasoline", "LPG", "Hybrid", "Electric"],
      "description": "Primary fuel type"
    },
    "initial_odometer_km": {
      "type": "integer",
      "minimum": 0,
      "maximum": 999999,
      "description": "Odometer reading when vehicle was added to system"
    }
  },
  "required": ["name", "license_plate", "vin", "fuel_type", "initial_odometer_km"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "vehicle_id": { "type": "string", "format": "uuid" },
    "vehicle": {
      "type": "object",
      "description": "Complete vehicle object with all fields"
    },
    "message": { "type": "string" }
  },
  "required": ["success", "vehicle_id", "vehicle"]
}
```

**Error Responses:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid VIN format",
    "field": "vin",
    "details": "VIN must be 17 characters (A-Z, 0-9, excluding I, O, Q)"
  }
}
```

### Example: Create Checkpoint Tool

**Tool Name:** `create_checkpoint`
**Server:** `trip-manager-server`

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "vehicle_id": {
      "type": "string",
      "format": "uuid",
      "description": "ID of the vehicle"
    },
    "checkpoint_type": {
      "type": "string",
      "enum": ["refuel", "manual", "month_end"],
      "description": "Type of checkpoint"
    },
    "datetime": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of checkpoint"
    },
    "odometer_km": {
      "type": "integer",
      "minimum": 0,
      "description": "Odometer reading in kilometers"
    },
    "odometer_source": {
      "type": "string",
      "enum": ["photo", "manual", "photo_adjusted"],
      "description": "How odometer reading was captured"
    },
    "odometer_photo_path": {
      "type": "string",
      "description": "Path to dashboard photo (optional)"
    },
    "location_address": {
      "type": "string",
      "description": "Human-readable address (optional)"
    },
    "location_coords": {
      "type": "object",
      "properties": {
        "lat": { "type": "number", "minimum": -90, "maximum": 90 },
        "lng": { "type": "number", "minimum": -180, "maximum": 180 }
      },
      "description": "GPS coordinates (optional but recommended)"
    },
    "receipt_id": {
      "type": "string",
      "description": "e-Kasa receipt ID (if refuel checkpoint)"
    },
    "fuel_liters": {
      "type": "number",
      "minimum": 0,
      "maximum": 500,
      "description": "Fuel quantity in liters (if refuel)"
    },
    "fuel_cost_eur": {
      "type": "number",
      "minimum": 0,
      "description": "Fuel cost in EUR (if refuel)"
    }
  },
  "required": ["vehicle_id", "checkpoint_type", "datetime", "odometer_km"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "checkpoint_id": { "type": "string", "format": "uuid" },
    "checkpoint": { "type": "object" },
    "gap_detected": { "type": "boolean" },
    "gap_info": {
      "type": "object",
      "properties": {
        "distance_km": { "type": "integer" },
        "time_period_days": { "type": "number" },
        "previous_checkpoint_id": { "type": "string" },
        "reconstruction_suggested": { "type": "boolean" }
      }
    },
    "message": { "type": "string" }
  }
}
```

### All Tool Signatures

**trip-manager-server (Core CRUD):**
1. `create_vehicle` - Create new vehicle
2. `get_vehicle` - Retrieve vehicle by ID
3. `list_vehicles` - List all vehicles (with filters)
4. `update_vehicle` - Update vehicle details
5. `create_checkpoint` - Create checkpoint from refuel/manual entry
6. `get_checkpoint` - Retrieve checkpoint by ID
7. `list_checkpoints` - List checkpoints (filter by vehicle, date range)
8. `detect_gap` - Analyze distance/time between checkpoints
9. `create_trip` - Create single trip entry
10. `create_trips_batch` - Create multiple trips at once
11. `get_trip` - Retrieve trip by ID
12. `list_trips` - List trips (filter by vehicle, date, purpose)
13. `update_trip` - Update trip details
14. `delete_trip` - Delete trip entry
15. `save_typical_destination` - Save location template
16. `get_typical_destinations` - Retrieve all saved locations

**receipt-processor-server:**
1. `scan_qr_code` - Extract QR code from receipt image
2. `fetch_receipt_data` - Call e-Kasa API with receipt ID
3. `queue_receipt` - Add receipt to processing queue
4. `get_queue_status` - Check queue status

**dashboard-ocr-server:**
1. `read_odometer` - Extract odometer reading from dashboard photo
2. `extract_metadata` - Get EXIF data (timestamp, GPS) from photo
3. `check_photo_quality` - Validate photo quality before OCR

**validation-server:**
1. `validate_checkpoint_pair` - Validate gap between two checkpoints
2. `validate_trip` - Validate single trip entry
3. `check_efficiency` - Check fuel efficiency reasonability
4. `check_deviation_from_average` - Compare to vehicle average

**report-generator-server:**
1. `generate_pdf` - Create Slovak VAT-compliant PDF report
2. `generate_csv` - Create CSV export for accounting software
3. `generate_summary` - Calculate monthly statistics

**route-intelligence-server (P1):**
1. `calculate_route` - Use OSRM to calculate distance between coordinates
2. `geocode_address` - Convert address to coordinates (with ambiguity detection)
3. `suggest_trips` - Propose trip combinations to fill gap

### Implementation in car-log

**Action Items:**
1. Create new document: `07-mcp-api-specifications.md`
2. Document all tool signatures with full schemas
3. Add error response patterns
4. Include example requests/responses
5. Update `06-mcp-architecture-v2.md` to reference complete API doc

**Priority:** P0 (Required for implementation)

---

## Part 6: Implementation Timeline with Daily Checkpoints (PLANNING - P0)

### From: `10-implementation-plan.md`, `11-mvp-summary.md`

The milestone spec has a **detailed 17-day implementation plan** with daily checkpoints and decision gates.

### Timeline Structure

**Week 1 (Days 1-7):** Core MCP Server Development
**Week 2 (Days 8-14):** Integration, Testing, Polish
**Week 3 (Days 15-17):** Demo Prep, Documentation, P1 features (conditional)

### Critical Checkpoints

**Day 7 Checkpoint (Week 1):**
- ✅ All P0 MCP servers functional individually
- **Decision:** Pass → Continue | Fail → Cut P1 features

**Day 10 Checkpoint (Mid Week 2):**
- ✅ Claude Desktop integration complete
- **Decision:** Pass → Continue | Fail → Cut ALL P1

**Day 14 Checkpoint (End Week 2) - CRITICAL:**
- ✅ End-to-end demo working flawlessly
- **Decision:** Pass → Proceed to P1 | Fail → Skip P1, fix bugs only

### Flexible Scope Strategy

**Never Cut (Sacred P0):**
1. Receipt processor (core value prop)
2. Trip manager with Slovak compliance (legal requirement)
3. Report generator with PDF (deliverable)
4. Claude Desktop integration (MCP showcase)
5. Validation (credibility)

**Cut in This Order (P1):**
1. First: Gradio UI (Claude Desktop is enough)
2. Second: File watcher (manual paste works)
3. Third: Route intelligence (manual entry acceptable)
4. Last Resort: Dashboard OCR (manual odometer entry fallback)

### Daily Schedule Example

**Day 1: Project Setup + Receipt Processor (Start)**
- Tasks: Repository setup, QR scanning library, basic tool definitions
- Deliverable: Can scan QR code from test image
- Red Flag: QR library not working → Switch library immediately

**Day 2: Receipt Processor (Complete)**
- Tasks: e-Kasa API integration, queue system, validation
- Deliverable: Full receipt processing workflow functional
- Red Flag: API unavailable → Use mock API for demo

**Day 6: Validation Server**
- Tasks: All 4 validation algorithms, thresholds configuration
- Deliverable: Can validate checkpoint pairs and trips
- Red Flag: Validation too strict → Adjust thresholds

### Implementation in car-log

**Action Items:**
1. Create new document: `08-implementation-plan.md`
2. Adapt 17-day timeline to our scope
3. Define checkpoint milestones with pass/fail criteria
4. Document scope cut strategy
5. Add daily task breakdowns

**Priority:** P0 (Project planning and execution)

---

## Part 7: Hackathon Presentation Strategy (DEMO - P0)

### From: `08-hackathon-presentation-draft.md`

The milestone spec has a **complete hackathon presentation strategy** with demo scripts and value proposition framing.

### Elevator Pitch (30 seconds)

"Slovak businesses waste hours manually logging vehicle mileage for tax compliance. We built a **conversational mileage logger** where you paste 2 photos, chat with Claude, and you're done.

The innovation? We didn't build *an app that uses MCP* - we built **MCP servers that ARE the backend**. Same servers power both Claude Desktop and Gradio UI.

Result: 30 seconds to log a trip vs. 3 minutes with traditional apps. Slovak VAT-compliant. Open data. Disposable solution."

### Triple Innovation Framework

1. **Market Innovation:** Slovak/European small businesses facing new 2025 VAT requirements
2. **Technical Innovation:** MCP as architecture (7 headless servers, file-based storage, Checkpoint-based algorithm)
3. **UX Innovation:** Conversational beats forms (30 seconds vs. 3 minutes)

### Demo Video Structure (5 minutes max)

**Video 1: Claude Desktop Demo (2 minutes) - PRIMARY**
- Show complete workflow: Setup → Receipt → Trip → Report
- Emphasize natural conversation, no forms
- Highlight 30-second interaction time

**Video 2: Architecture Deep Dive (1.5 minutes) - TECHNICAL**
- Show 7 MCP servers diagram
- Explain file-based storage
- Demonstrate modularity (same servers, dual UI)

**Video 3: Real-World Impact (1.5 minutes) - OPTIONAL**
- Slovak business owner testimonial (can be staged)
- ROI calculation: €48 VAT deduction/month, €0 cost
- Time savings: 8 hours → 15 minutes per quarter

### Demo Script (P0 Only - 5 minutes)

**Part 1: Setup (1 min)**
```
User: "I need to start logging company vehicle mileage"
Claude: "I'll help set up Slovak tax-compliant tracking. What's your vehicle?"
User: "Ford Transit, BA-456CD, VIN WBAXX01234ABC5678"
Claude: [Creates vehicle] "Saved! What's the current odometer?"
User: [Pastes dashboard photo]
Claude: [Reads 45,000 km] "Got it! You're all set."
```

**Part 2: First Receipt (1.5 min)**
```
User: [Pastes receipt photo]
Claude: [Scans QR, fetches data] "Shell Bratislava, 50.5L Diesel, 72.50 EUR"
User: [Pastes dashboard photo]
Claude: [Reads odometer] "45,000 km. First refuel logged!"
```

**Part 3: Second Receipt + Trip (2 min)**
```
User: [Pastes another receipt photo]
Claude: [Processes] "OMV Bratislava, 45.0L, 65.25 EUR. Odometer?"
User: [Pastes dashboard photo]
Claude: [Reads 45,550 km] "You drove 550 km! Košice trip?"
User: "Yes, client meeting. Left 9am, back 5pm."
Claude: [Creates trips, validates] "Saved! 550 km, 8.5 L/100km efficiency ✓"
```

**Part 4: Report (0.5 min)**
```
User: "Generate November report"
Claude: [Generates PDF] "Report ready! 2 trips, 550 km, VAT deductible: 13.53 EUR"
[Shows PDF with all Slovak compliance fields]
```

### Implementation in car-log

**Action Items:**
1. Create new document: `09-hackathon-presentation.md`
2. Adapt demo script to our feature set
3. Define video structure and key messages
4. Create value proposition framing
5. Prepare architecture diagrams for demo

**Priority:** P0 (Hackathon submission requirement)

---

## Part 8: Additional Valuable Content

### Photo Handling Strategy

**From:** `06-claude-desktop-mcp-architecture.md`, `09-mvp-decisions.md`

**MVP Decision:** Manual paste (not file-watcher)
- User pastes photos directly into Claude Desktop
- No cloud sync dependencies for P0
- File-watcher MCP server is P1 enhancement

**Rationale:**
- Simpler, more reliable
- Faster development
- Clearer demo
- No external dependencies

### OCR Implementation Details

**From:** `02a-odometer-photo-capture.md`, `06-claude-desktop-mcp-architecture.md`

**Use Claude Vision (Sonnet) for OCR:**
- >95% accuracy on clear dashboard photos
- Confidence score returned (threshold: 0.7)
- Fallback to manual entry if OCR fails

**Photo Quality Validation:**
- Check brightness (not too dark/bright)
- Blur detection (focus quality)
- Minimum resolution: 640x480
- Provide feedback: "Photo may be too blurry, try again?"

### EXIF Metadata Extraction

**From:** `02a-odometer-photo-capture.md`

**Extract from photos:**
- Timestamp (photo creation date/time)
- GPS coordinates (if available)
- Camera model (for debugging)

**Use cases:**
- Auto-fill checkpoint timestamp
- Auto-fill checkpoint location
- Detect photo date vs. receipt date conflicts

### Ambiguous Address Handling

**From:** `02-domain-model.md` in car-log (we already have this!)

**When user provides ambiguous address:**
```
"Košice" could mean:
1. Košice City Center (48.7164, 21.2611)
2. Košice-Šaca District (48.6511, 21.2397)
3. Košice Airport (48.6631, 21.2411)

Which location? (1/2/3)
```

**Implementation:** `geo-routing.geocode_address()` returns multiple results with confidence scores

---

## Summary: Priority Matrix

### CRITICAL (P0) - Must Integrate Before Implementation

| Enhancement | Estimated Effort | Impact | Files to Update |
|-------------|-----------------|--------|-----------------|
| Slovak tax compliance fields | 2 hours | High | 04-data-model.md, 06-mcp-architecture-v2.md |
| L/100km fuel efficiency format | 1 hour | High | 02-domain-model.md, 03-trip-reconstruction.md, 04-data-model.md |
| Validation algorithms with thresholds | 3 hours | High | 03-trip-reconstruction.md, NEW: 07-mcp-api-specs.md |
| File-based storage architecture | 2 hours | High | 04-data-model.md, 06-mcp-architecture-v2.md |
| Complete MCP API tool signatures | 4 hours | High | NEW: 07-mcp-api-specifications.md |
| **Total P0 Integration Effort** | **12 hours** | | **5 documents** |

### IMPORTANT (P1) - Should Add After P0 Integration

| Enhancement | Estimated Effort | Impact | Files to Update |
|-------------|-----------------|--------|-----------------|
| Implementation timeline (17-day plan) | 2 hours | Medium | NEW: 08-implementation-plan.md |
| Hackathon presentation strategy | 1 hour | Medium | NEW: 09-hackathon-presentation.md |
| OCR implementation details | 1 hour | Medium | Update 06-mcp-architecture-v2.md |
| Photo handling strategy documentation | 0.5 hours | Low | Update 06-mcp-architecture-v2.md |
| **Total P1 Integration Effort** | **4.5 hours** | | **3 documents** |

---

## Next Steps

1. **Review this document with user** to confirm integration priorities
2. **Update car-log specifications** with P0 content (Slovak compliance, L/100km, validation, file storage, APIs)
3. **Create new documents** (MCP API specs, implementation plan, presentation strategy)
4. **Validate consistency** across all car-log documents
5. **Begin implementation** using updated specifications

---

**Status:** ✅ Review Complete - Ready for User Confirmation
**Total Integration Effort:** ~16.5 hours of specification updates
**Documents to Create:** 3 new documents
**Documents to Update:** 5 existing documents
