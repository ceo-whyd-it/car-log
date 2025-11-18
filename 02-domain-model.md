# Domain Model: Car Log

**Version:** 2.0
**Date:** 2025-11-17
**Status:** Draft - In Discussion

---

## Overview

This document defines the core domain concepts and their relationships in the Car Log system. Understanding these concepts is essential for implementing the trip reconstruction algorithm and business logic.

---

## Core Concepts

### 1. Checkpoint

**Definition:** A point-in-time capture of vehicle state, serving as an anchor point for trip reconstruction.

**Purpose:**
- Record odometer reading at a specific moment
- Capture evidence (photos of dashboard, receipts)
- Enable calculation of distance traveled between points
- Provide timestamp and location context

**Key Characteristics:**
- Created at fuel stops (most common) or on-demand
- Contains required data (odometer) + optional evidence (photos)
- Immutable once created (editable with audit trail)
- Forms timeline of vehicle usage

---

### 2. Trip

**Definition:** A calculated journey between two sequential checkpoints.

**Purpose:**
- Represent actual vehicle usage for tax purposes
- Calculate distance, fuel consumption, and efficiency
- Classify as business or personal
- Link expenses to mileage

**Key Characteristics:**
- Always bounded by two checkpoints (start and end)
- Distance calculated automatically from odometer delta
- Can be user-specified or reconstructed from templates
- Tagged with purpose (business/personal) and description
- **Slovak VAT Compliance Fields:**
  - Separate trip timing from refuel timing (trip_start/end_datetime vs refuel_datetime)
  - Separate trip locations from fuel station location
  - Driver information (driver_name, driver_id, driver_is_owner)
- Fuel efficiency calculated in L/100km (European standard)

---

### 3. Trip Template

**Definition:** A user-defined recurring route pattern used for trip reconstruction.

**Purpose:**
- Simplify reconstruction of repeated journeys
- Store typical routes (home-office, office-warehouse)
- Enable batch trip creation from checkpoint gaps
- Learn user's driving patterns over time

**Key Characteristics:**
- Named by user (e.g., "Warehouse Run")
- Includes origin, destination, and typical distance
- Can have GPS coordinates for geo-matching
- Tracks usage frequency for relevance scoring

---

### 4. Receipt

**Definition:** Digital record of a fuel purchase, extracted from e-Kasa API or manually entered.

**Purpose:**
- Document fuel expenses for tax deduction
- Link fuel consumption to mileage
- Provide vendor and location context
- Enable fuel efficiency calculations

**Key Characteristics:**
- Can be from e-Kasa API (Slovakia) or manual entry (universal)
- Contains line items (may include non-fuel items)
- Fuel items detected and extracted automatically
- Includes VAT breakdown for compliance

---

### 5. Vehicle

**Definition:** A company-owned vehicle being tracked.

**Purpose:**
- Separate mileage logs for multiple vehicles
- Track vehicle-specific data (make, model, fuel type)
- Calculate per-vehicle statistics
- Store Slovak tax compliance data (VIN)

**Key Characteristics:**
- Identified by license plate (Slovak format: BA-456CD)
- VIN (Vehicle Identification Number) - MANDATORY for Slovak VAT compliance
- Has initial odometer reading (baseline)
- Linked to all checkpoints and trips
- Can be marked active/inactive
- Tracks average fuel efficiency in L/100km (European standard)

---

## Conceptual Relationships

```
┌──────────────────────────────────────────────────────────────┐
│                         VEHICLE                              │
│  • Ford Transit (BA-123AB)                                  │
│  • Initial odometer: 45,000 km                              │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ has many
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                      CHECKPOINTS                             │
│  CP1: Nov 1, 45,120km, Bratislava, Receipt €50             │
│  CP2: Nov 8, 45,320km, Bratislava, Receipt €45             │
│  CP3: Nov 15, 45,850km, Košice, (no receipt)               │
│  CP4: Nov 22, 46,100km, Bratislava, Receipt €52            │
└──────────────────────────────────────────────────────────────┘
       │                    │                    │
       └──── 200km ─────────┘                    │
              ↓                                   │
       ┌────────────┐                            │
       │  TRIP 1    │                            │
       │  Nov 1-8   │                            │
       │  200km     │                            │
       └────────────┘                            │
                                                 │
                        └──── 530km ─────────────┘
                               ↓
                        ┌────────────┐
                        │  TRIP 2    │
                        │  Nov 8-15  │
                        │  530km     │
                        └────────────┘
                               ↑
                               │ reconstructed using
                               │
                        ┌────────────────────┐
                        │  TRIP TEMPLATES    │
                        │  • Daily Commute   │
                        │  • Warehouse Run   │
                        │  • Client Visit    │
                        └────────────────────┘
```

---

## Checkpoint Types

### Type 1: Fuel Checkpoint (Most Common)

**When Created:**
- User refuels vehicle at gas station

**Required Data:**
- Odometer reading
- Timestamp

**Optional Data:**
- Receipt photo (for e-Kasa QR extraction)
- Dashboard photo (for OCR verification)
- GPS coordinates (from photo EXIF or device) - **STRONGLY RECOMMENDED** for geo-matching
- Address (optional human-readable label)

**Example User Flow:**
```
User: [Pastes receipt photo] "Just filled up at 45,320 km"

System:
1. Extracts QR code → Receipt ID: ABC123
2. Calls e-Kasa API → 50L Diesel, €72.50
3. Extracts EXIF → Location: Bratislava, Time: 14:32
4. Creates checkpoint with all data
5. Confirms: "Checkpoint created at 45,320km in Bratislava"
```

---

### Type 2: Mileage-Only Checkpoint

**When Created:**
- User wants to mark current mileage without refueling
- End of month/quarter for reporting

**Required Data:**
- Odometer reading
- Timestamp

**Optional Data:**
- Dashboard photo (for verification)
- GPS coordinates - **STRONGLY RECOMMENDED** for geo-matching
- Address (optional human-readable label)
- Notes

**Example User Flow:**
```
User: [Pastes dashboard photo] "Current mileage"

System:
1. OCR extracts: 46,100 km
2. EXIF extracts: Location + timestamp
3. Prompts: "Create checkpoint at 46,100km?"
4. User confirms
5. System: "Checkpoint created (no fuel data)"
```

---

### Type 3: System-Generated Checkpoint (Future - P2)

**When Created:**
- Automatically at month/quarter end
- After vehicle service events
- Odometer rollover/reset detection

**Required Data:**
- Odometer reading (user-provided)
- Timestamp (system-generated)
- Trigger reason

**Example User Flow:**
```
System: "It's the end of November. Would you like to create
         a checkpoint for your Ford Transit?
         Last checkpoint: Nov 22, 46,100km"

User: "Yes, current reading is 46,850km"

System: "Month-end checkpoint created. You drove 750km in November."
```

---

## Trip Reconstruction Modes

### Mode A: User-Specified Trips

User explicitly remembers specific journeys.

**Characteristics:**
- High accuracy (user's memory)
- Complete details (destination, purpose)
- No template required
- Can be partial (doesn't need to fill entire gap)

**Example:**
```
Gap: 200km between checkpoints

User: "I went to Košice on Nov 3, that was 180km round trip"

System: Creates trip:
  • Date: Nov 3
  • Destination: Košice
  • Distance: 180km (user-specified)
  • Remaining gap: 20km (unaccounted)
```

---

### Mode B: Template-Based Reconstruction

System fills gaps using predefined trip templates.

**Characteristics:**
- Automatic gap filling
- Based on recurring patterns
- Requires user confirmation
- Can combine multiple templates

**Example:**
```
Gap: 200km over 7 days
Templates available:
  • Daily Commute (25km)
  • Client Visit (120km)

System proposes:
  • 1× Client Visit (120km)
  • 3× Daily Commute (75km)
  • Remainder: 5km local driving

User confirms → 5 trips created
```

---

### Mode C: Geo-Assisted Reconstruction

Uses checkpoint GPS locations to suggest routes.

**Characteristics:**
- Leverages OpenStreetMap routing
- Matches templates by location
- Provides route alternatives
- High confidence when GPS available

**Example:**
```
Gap: 410km
Start: Bratislava (GPS: 48.1486, 17.1077)
End: Košice (GPS: 48.7164, 21.2611)

System calculates routes:
  1. Via D1 highway: 395km (4.2 hrs)
  2. Via E50: 410km (4.5 hrs) ← Matches gap!
  3. Via local: 385km (5.8 hrs)

System: "Your distance matches route #2 (E50, 410km).
         I found matching template: 'Warehouse Run'

         Create trip from this template?"
```

---

## Trip Template Structure

### Minimal Template (GPS-First Approach)

```
Template: "Daily Commute"
├── Name: "Daily Commute" ← MANDATORY
├── From Coordinates: (48.1850, 17.1250) ← MANDATORY (source of truth)
├── To Coordinates: (48.1486, 17.1077) ← MANDATORY (source of truth)
├── From Address: "Home, Hlavná 45, Bratislava" ← OPTIONAL (human label)
├── To Address: "Office, Priemyselná 12, Bratislava" ← OPTIONAL (human label)
└── [All other fields are optional enhancements]
```

### Fully Enhanced Template

```
Template: "Warehouse Run"
├── Name: "Warehouse Run" ← MANDATORY
├── From Coordinates: (48.1486, 17.1077) ← MANDATORY (source of truth)
├── To Coordinates: (48.7164, 21.2611) ← MANDATORY (source of truth)
├── From Address: "Main Office, Bratislava" ← OPTIONAL (human label)
├── To Address: "Warehouse, Košice" ← OPTIONAL (human label)
├── Distance: 410 km (round trip) ← OPTIONAL (improves matching)
├── Is Round Trip: Yes ← OPTIONAL
├── Typical Days: ["Monday", "Thursday"] ← OPTIONAL
├── Purpose: Business ← OPTIONAL
├── Business Description: "Picking up supplies" ← OPTIONAL
├── Route Notes: "Via E50 (faster than D1)" ← OPTIONAL
├── Usage Count: 12 ← SYSTEM-TRACKED
└── Last Used: 2025-11-15 ← SYSTEM-TRACKED
```

**Design Philosophy:**
- **GPS coordinates are MANDATORY** - They enable reliable geo-matching
- **Addresses are OPTIONAL** - Human-readable labels that enhance UX
- **Progressive enhancement** - Templates work with minimal data, improve with more
- **GPS as source of truth** - Matching algorithm prioritizes coordinates (70% weight)

---

## Checkpoint Lifecycle

```
1. CREATION
   ↓
   User provides data:
   • Odometer reading (required)
   • Photo (optional)
   • Timestamp (auto or manual)

2. ENRICHMENT
   ↓
   System extracts:
   • EXIF data (timestamp, GPS, camera info)
   • QR code from receipt photo
   • Receipt data from e-Kasa API
   • Fuel line items from receipt

3. VALIDATION
   ↓
   System checks:
   • Odometer sequence valid?
   • Distance reasonable? (<500km/day typical)
   • Fuel efficiency in range? (5-50 L/100km)
   • No duplicate checkpoints?

4. CONFIRMATION
   ↓
   System presents to user:
   • "Checkpoint at 45,320km in Bratislava"
   • "Diesel: 50L @ €1.45/L = €72.50"
   • "200km since last checkpoint"

   User approves or corrects

5. STORAGE
   ↓
   Saved to database with:
   • All extracted data
   • Original photo references
   • Validation status

6. RECONSTRUCTION TRIGGER
   ↓
   System asks:
   • "Reconstruct trips from this gap?"
   • User chooses mode (manual/template/skip)
```

---

## Trip States

```
┌─────────────────┐
│  RECONSTRUCTED  │  Initial state after reconstruction
└─────────────────┘
         │
         ↓
┌─────────────────┐
│    CONFIRMED    │  User reviewed and approved
└─────────────────┘
         │
         ↓
┌─────────────────┐
│    REPORTED     │  Included in tax report (immutable)
└─────────────────┘
```

**State Transitions:**
- RECONSTRUCTED → CONFIRMED: User approves reconstruction
- CONFIRMED → REPORTED: Trip included in generated report
- Any state → EDITED: User makes changes (creates new version)

---

## Business Rules

### Checkpoint Rules

1. **Odometer Sequence**
   - Must be ≥ previous checkpoint for same vehicle
   - Exception: Odometer reset event (user confirms)

2. **Timestamp Sequence**
   - Must be ≥ previous checkpoint timestamp
   - Exception: Manual correction with reason

3. **Distance Reasonableness**
   - Max 500km per day for typical usage
   - Max 1000km per day for long trips
   - Warn user if exceeded

4. **Fuel Efficiency**
   - **Format:** L/100km (liters per 100 kilometers) - European standard
   - **Realistic range:** 4.0-20.0 L/100km for cars and vans
   - **Typical values:**
     - Passenger car: 6-10 L/100km
     - Van (e.g., Ford Transit): 8-12 L/100km
     - Very efficient hybrid: 4-5 L/100km
     - Large van with heavy load: 15-20 L/100km
   - Warn if outside range (possible data error)

5. **Duplicate Detection**
   - Same odometer reading within 24 hours → Warn user
   - Same receipt ID → Block creation

---

### Trip Template Rules

1. **Distance Tolerance**
   - Template matches actual distance within 10% tolerance
   - Example: 410km template matches 370-450km actual

2. **Location Matching (Hybrid Algorithm)**
   - **GPS matching (70% weight):** Coordinates within 500m = high score
   - **Address matching (30% weight):** String similarity if both addresses present
   - Final score combines both components
   - Allows for nearby gas stations, parking lots (same general area)

3. **Usage Frequency**
   - Templates used recently ranked higher
   - Templates with >5 uses considered "established"

4. **Day-of-Week Filtering**
   - If template has typical days, only suggest on those days
   - Example: "Weekly Meeting" only on Wednesdays

---

### Reconstruction Rules

1. **Gap Filling**
   - Remainder <50km → Mark as "local driving"
   - Remainder ≥50km → Prompt user for details

2. **Template Combination**
   - Maximum 10 trips from templates in single reconstruction
   - If more needed, prompt user for verification

3. **Confidence Scoring**
   - GPS match + distance match = High confidence (90%+)
   - Distance match only = Medium confidence (70-89%)
   - User-specified = Absolute confidence (100%)

---

## GPS and Address Handling

### Core Principle: GPS as Source of Truth

**Why GPS coordinates are mandatory:**
- **Unambiguous** - Coordinates uniquely identify a location
- **Machine-readable** - Enable automated geo-matching
- **Universal** - Work across all countries and languages
- **Precise** - 500m radius matching is reliable for vehicle tracking

**Why addresses are optional:**
- **Human-friendly** - Easier to read "Bratislava" than "48.1486, 17.1077"
- **Context** - Provide business meaning ("Client Office" vs coordinates)
- **Flexible** - Users can skip if unknown or irrelevant
- **Not authoritative** - Ambiguous addresses are resolved to GPS

### Address Validation and Geocoding

When users provide an address:

1. **Validation:** `geo-routing.geocode_address(address)` returns:
   - Success + coordinates + confidence score
   - OR list of alternatives if ambiguous (confidence < 0.7)

2. **User Resolution:** If ambiguous:
   ```
   "Košice" could mean:
   1. Košice City Center (48.7164, 21.2611)
   2. Košice-Šaca District (48.6511, 21.2397)
   3. Košice Airport (48.6631, 21.2411)

   Which location? (1/2/3)
   ```

3. **Storage:** Both address (label) and coordinates (truth) are saved

### Hybrid Matching Algorithm

When matching templates to checkpoints:

```
GPS Score (70%):
- Calculate haversine distance between coordinates
- < 100m = 100 points
- < 500m = 90 points
- < 1km = 70 points
- < 5km = 40 points
- > 5km = 0 points

Address Score (30%):
- If both checkpoint and template have addresses:
  - Calculate string similarity (Levenshtein)
  - Normalize to 0-100 scale
- If either missing: 0 points (GPS carries full weight)

Final Score = (GPS_Score × 0.7) + (Address_Score × 0.3)
```

**Example:**
```
Template: "Warehouse Run"
- From: (48.1486, 17.1077) "Main Office, Bratislava"
- To: (48.7164, 21.2611) "Warehouse, Košice"

Checkpoint Gap:
- Start: (48.1490, 17.1080) "Bratislava"
- End: (48.7170, 21.2615) "Košice"

Matching:
- GPS distance (start): 50m → 100 points
- GPS distance (end): 60m → 100 points
- Address similarity (start): "Bratislava" vs "Main Office, Bratislava" → 60 points
- Address similarity (end): "Košice" vs "Warehouse, Košice" → 50 points

Final Score:
- Start: (100 × 0.7) + (60 × 0.3) = 70 + 18 = 88/100 ✓
- End: (100 × 0.7) + (50 × 0.3) = 70 + 15 = 85/100 ✓

Template matches with high confidence!
```

---

## Slovak Tax Compliance Requirements

### Legal Context

- **Income Tax Act:** zákon č. 595/2003 Z. z.
- **VAT Act:** Effective 1 January 2025 (stricter rules from 1 January 2026)
- **Requirement:** 100% VAT deduction requires ride-by-ride records

### Required Fields for Tax Compliance

#### Vehicle Entity
```
vin: "WBAXX01234ABC5678"  // 17-character alphanumeric, MANDATORY
vin_verified: true         // Verification status
```

**VIN Validation:**
- Pattern: `^[A-HJ-NPR-Z0-9]{17}$` (no I, O, Q characters)
- Why Critical: VIN is required for VAT deduction under 2025 rules

#### Trip Entity - Slovak-Specific Fields

**Timing Fields (separate refuel time from trip time):**
```
trip_start_datetime: "2025-11-15T09:00:00Z"  // When trip started
trip_end_datetime: "2025-11-15T13:00:00Z"    // When trip ended
refuel_datetime: "2025-11-15T08:45:00Z"      // When refueled
refuel_timing: "before"                       // before/during/after trip
```

**Location Fields (separate trip locations from fuel station):**
```
trip_start_location: "Bratislava Office, Hlavná 12"  // Trip origin
trip_end_location: "Client ABC, Košice"              // Trip destination
vendor_location: "Shell Bratislava West"             // Fuel station
```

**Driver Fields (required for multi-driver vehicles):**
```
driver_name: "Ján Novák"        // MANDATORY
driver_id: "uuid-or-null"       // Optional link to Driver entity
driver_is_owner: true           // Flag for quick filtering
```

**Why This Matters:**
- Slovak tax inspectors require **separate trip timing from refuel timing**
- Example: Refuel Monday 8am → Trip Monday 9am-5pm (different times!)
- GPS coordinates remain OPTIONAL (not legally required, but strongly recommended)

### Fuel Efficiency Format

**European Standard: L/100km**

All fuel efficiency calculations use L/100km (liters per 100 kilometers):

**Conversion Formulas:**
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

**Validation Ranges:**
- **Diesel:** 5.0-15.0 L/100km
- **Gasoline:** 6.0-20.0 L/100km
- **LPG:** 8.0-25.0 L/100km
- **Hybrid:** 3.0-8.0 L/100km
- **Electric:** 12.0-25.0 kWh/100km

---

## Related Documents

- [01-product-overview.md](./01-product-overview.md) - Product vision and scope
- [03-trip-reconstruction.md](./03-trip-reconstruction.md) - Algorithm specification
- [04-data-model.md](./04-data-model.md) - JSON file schemas
- [05-claude-skills-dspy.md](./05-claude-skills-dspy.md) - Dual interface architecture
- [06-mcp-architecture-v2.md](./06-mcp-architecture-v2.md) - MCP server architecture
- [07-mcp-api-specifications.md](./07-mcp-api-specifications.md) - Complete API tool definitions

---

## Glossary

| Term | Definition |
|------|------------|
| **Checkpoint** | Point-in-time vehicle state capture |
| **Trip** | Journey between two checkpoints |
| **Trip Template** | Recurring route pattern |
| **Gap** | Distance/time between checkpoints |
| **Reconstruction** | Process of creating trips from checkpoints |
| **EXIF** | Photo metadata (timestamp, GPS) |
| **e-Kasa** | Slovak electronic receipt system |
| **Odometer** | Vehicle's total distance meter (km) |
| **Geo-routing** | Route calculation via OpenStreetMap |
