# MCP Server Architecture v2

**Version:** 2.0
**Date:** 2025-11-17
**Status:** Draft - Architecture Refinement
**Supersedes:** 06-mcp-architecture.md v1

---

## Overview

This document specifies the **Model Context Protocol (MCP) server architecture** for Car Log with key architectural refinements:

1. **Separated trip-reconstructor** - Independent stateless service
2. **GPS as source of truth** - Addresses are optional enhancements
3. **Hybrid matching** - GPS (70%) + address similarity (30%)
4. **Optional geocoding** - User decides when to calculate coordinates
5. **Ambiguity handling** - Show alternatives for unclear addresses

---

## Architecture Principles

### Design Philosophy

**Separation of Concerns:**
```
car-log-core:        Pure CRUD operations (data in/out)
trip-reconstructor:  Stateless matching algorithm (receives all data as input)
geo-routing:         Geographic calculations (geocoding + routing)
ekasa-api:          External API integration
filesystem:          File operations + EXIF extraction
sqlite:              Data persistence
```

**Key Architectural Decisions:**

| Decision | Rationale |
|----------|-----------|
| **trip-reconstructor is separate** | Complex algorithm deserves dedicated service; enables independent scaling and testing |
| **Stateless reconstruction** | All data passed as parameters; no database queries; pure function behavior |
| **GPS = source of truth** | Coordinates are precise and reliable; addresses are human-readable labels |
| **Optional geocoding** | User chooses when to calculate GPS from addresses; works offline |
| **Hybrid matching** | Combines GPS precision (70%) with address context (30%) for best results |

---

## MCP Server Landscape

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERFACES                            │
│  • Claude Desktop (Skills)  • Gradio App (DSPy)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    Orchestration Layer
         (Skills/DSPy coordinate multiple MCP calls)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MCP SERVER LAYER                             │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ car-log-core     │  │ trip-reconstructor│  (P0 - Required)  │
│  │ CRUD Operations  │  │ Stateless Matcher │                   │
│  └──────────────────┘  └──────────────────┘                   │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ geo-routing      │  │ ekasa-api        │  (P0 - Required)  │
│  │ Geocode + Routes │  │ Receipt Data     │                   │
│  └──────────────────┘  └──────────────────┘                   │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ filesystem       │  │ sqlite           │  (P0 - Required)  │
│  │ Photos + EXIF    │  │ Data Store       │                   │
│  └──────────────────┘  └──────────────────┘                   │
│                                                                 │
│  ┌──────────────────┐                                          │
│  │ report-generator │                        (P1 - Optional)   │
│  │ PDF/CSV Export   │                                          │
│  └──────────────────┘                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Orchestration Pattern

**Key Insight:** Skills/DSPy orchestrate; MCP servers don't call each other.

```
┌─────────────────────────────────────────────────────┐
│ Claude Skill: "Reconstruct trips from Nov 1-8"     │
└─────────────────────────────────────────────────────┘
                      ↓
        Step 1: Get gap data
                      ↓
┌─────────────────────────────────────────────────────┐
│ car-log-core.analyze_gap(cp1_id, cp2_id)           │
│ → Returns: {distance: 530km, start: {...}, end}    │
└─────────────────────────────────────────────────────┘
                      ↓
        Step 2: Get user's templates
                      ↓
┌─────────────────────────────────────────────────────┐
│ car-log-core.list_templates(user_id)               │
│ → Returns: [{id, name, from_coords, to_coords...}] │
└─────────────────────────────────────────────────────┘
                      ↓
        Step 3: Calculate routes (if GPS available)
                      ↓
┌─────────────────────────────────────────────────────┐
│ geo-routing.calculate_route(start_gps, end_gps)    │
│ → Returns: [{distance: 410km, via: "E50"}]         │
└─────────────────────────────────────────────────────┘
                      ↓
        Step 4: Run matching algorithm
                      ↓
┌─────────────────────────────────────────────────────┐
│ trip-reconstructor.match_templates({               │
│   gap_data: <from step 1>,                          │
│   templates: <from step 2>,                         │
│   geo_routes: <from step 3>                         │
│ })                                                  │
│ → Returns: {matched_templates, proposal, confidence}│
└─────────────────────────────────────────────────────┘
                      ↓
        Step 5: Present to user & get approval
                      ↓
        Step 6: Create trips
                      ↓
┌─────────────────────────────────────────────────────┐
│ FOR EACH approved trip:                             │
│   car-log-core.create_trip(trip_data)              │
└─────────────────────────────────────────────────────┘
```

---

## Server 1: car-log-core (Custom - Pure CRUD)

### Purpose
Data persistence and retrieval for all entities. **No business logic**, just database operations.

**Storage Architecture:** JSON file-based (no database required for MVP)

### Priority
**P0** - Required for MVP

### Implementation
Python or TypeScript

### Storage Approach

**File-Based Storage (MVP):**
- All data stored as JSON files in `~/Documents/MileageLog/data/`
- Monthly folders for trips and checkpoints
- Atomic write pattern (temp file + rename) to prevent corruption
- Optional monthly index files for performance
- Human-readable, Git-friendly, portable

**Advantages:**
- ✅ Human-readable: Users can inspect/edit data in text editor
- ✅ Git-friendly: Version control for business records
- ✅ Portable: Copy folder = complete backup
- ✅ No setup: No database installation or configuration
- ✅ Transparent: Users see exactly what data is stored
- ✅ Privacy: Data stays local, user controls

**Trade-offs:**
- ⚠️ Performance: Slower for 1000+ trips (acceptable for MVP)
- ⚠️ Querying: No SQL (use file system + JSON parsing)
- ⚠️ Concurrency: File locking needed (single-user app, not critical)

### Configuration
```json
{
  "mcpServers": {
    "car-log-core": {
      "command": "python",
      "args": ["-m", "mcp_servers.car_log_core"],
      "env": {
        "DATA_PATH": "./data",
        "USE_ATOMIC_WRITES": "true",
        "GENERATE_MONTHLY_INDEX": "true"
      }
    }
  }
}
```

---

## Tool 1.1: create_checkpoint

### Description
Create new checkpoint with GPS and optional address.

**Note on Data Storage:** API input uses flat structure (`coords`, `address`, `receipt_id`, etc.) for simplicity. The server transforms these into nested `location` and `receipt` objects when storing to JSON files (see 04-data-model.md for storage schema).

### Input Schema
```typescript
{
  vehicle_id: string,
  odometer_reading: number,
  timestamp: string,  // ISO 8601

  // Location (GPS is mandatory if provided)
  coords?: {
    latitude: number,   // -90 to 90
    longitude: number   // -180 to 180
  },
  address?: string,     // Optional human-readable address
  location_source?: "exif" | "user" | "geocoded",  // How coords were obtained

  // Receipt & fuel
  receipt_id?: string,
  fuel_data?: {
    quantity_liters: number,
    price_incl_vat: number,
    price_excl_vat: number,
    vat_rate: number,
    fuel_type: "diesel" | "petrol_95" | "petrol_98" | "lpg" | "cng"
  },

  // Supporting data
  photo_paths?: string[],
  notes?: string
}
```

### Output Schema
```typescript
{
  success: boolean,
  checkpoint_id: string,
  distance_since_last?: number,
  previous_checkpoint?: {
    id: string,
    odometer_reading: number,
    timestamp: string
  },
  warnings?: string[]
}
```

---

## Tool 1.2: analyze_gap

### Description
Analyze distance/time gap between checkpoints. **Pure data retrieval** - no matching logic.

### Input Schema
```typescript
{
  start_checkpoint_id: string,
  end_checkpoint_id: string
}
```

### Output Schema
```typescript
{
  distance_km: number,
  days: number,
  hours: number,
  start_checkpoint: {
    id: string,
    odometer_reading: number,
    timestamp: string,
    coords?: {lat: number, lng: number},
    address?: string,
    fuel_data?: object
  },
  end_checkpoint: {
    // Same structure
  },
  has_gps: boolean,  // True if BOTH checkpoints have coordinates
  avg_km_per_day: number
}
```

---

## Tool 1.3: list_templates

### Description
Retrieve user's trip templates. **No filtering or matching** - returns all templates.

### Input Schema
```typescript
{
  user_id: string,
  vehicle_id?: string  // Optional filter
}
```

### Output Schema
```typescript
{
  templates: Array<{
    id: string,
    name: string,

    // FROM endpoint (GPS is mandatory)
    from_coords: {lat: number, lng: number},
    from_address?: string,
    from_label?: string,  // Short label like "Bratislava"

    // TO endpoint (GPS is mandatory)
    to_coords: {lat: number, lng: number},
    to_address?: string,
    to_label?: string,

    // Optional enhancement fields
    distance_km?: number,
    is_round_trip?: boolean,
    typical_days?: string[],  // ["Monday", "Thursday"]
    purpose?: "business" | "personal",
    business_description?: string,
    notes?: string,

    // Metadata
    usage_count: number,
    last_used_at?: string,
    created_at: string
  }>
}
```

---

## Tool 1.4: create_template

### Description
Create new trip template with GPS coordinates.

### Input Schema
```typescript
{
  name: string,

  // FROM endpoint (coordinates MANDATORY)
  from_coords: {lat: number, lng: number},
  from_address?: string,
  from_label?: string,

  // TO endpoint (coordinates MANDATORY)
  to_coords: {lat: number, lng: number},
  to_address?: string,
  to_label?: string,

  // Optional fields
  distance_km?: number,
  is_round_trip?: boolean,
  typical_days?: string[],
  purpose?: "business" | "personal",
  business_description?: string,
  notes?: string
}
```

### Output Schema
```typescript
{
  success: boolean,
  template_id: string,
  completeness_percentage: number  // 0-100 based on optional fields filled
}
```

---

## Tool 1.5: create_trip

### Description
Create single trip record with Slovak tax compliance fields.

### Input Schema
```typescript
{
  vehicle_id: string,
  start_checkpoint_id: string,
  end_checkpoint_id: string,
  template_id?: string,

  // SLOVAK COMPLIANCE: Separate trip timing from refuel timing
  trip_start_datetime: string,  // ISO 8601 - When trip started
  trip_end_datetime: string,    // ISO 8601 - When trip ended

  // SLOVAK COMPLIANCE: Separate trip locations from fuel station
  trip_start_location: string,  // Trip origin
  trip_end_location: string,    // Trip destination
  trip_start_coords?: {lat: number, lng: number},
  trip_end_coords?: {lat: number, lng: number},

  // SLOVAK COMPLIANCE: Driver information (MANDATORY)
  driver_name: string,          // Full name of driver
  driver_id?: string,           // Optional: UUID of driver entity
  driver_is_owner?: boolean,    // Whether driver is vehicle owner

  // Trip metrics
  distance_km: number,
  fuel_consumption_liters?: number,
  fuel_efficiency_l_per_100km?: number,  // L/100km (European standard)
  fuel_cost_eur?: number,

  // Purpose classification
  purpose: "Business" | "Personal",
  business_description?: string,  // Required if purpose is Business

  // Refuel metadata (if applicable)
  refuel_datetime?: string,  // ISO 8601 - When refuel occurred
  refuel_timing?: "before" | "during" | "after",

  // Reconstruction metadata
  reconstruction_method?: "manual" | "template" | "geo_assisted" | "user_specified",
  template_used?: string,
  confidence_score?: number,  // 0-1

  notes?: string
}
```

### Output Schema
```typescript
{
  success: boolean,
  trip_id: string,
  validation: {
    status: "validated" | "has_warnings" | "has_errors",
    distance_check: "ok" | "warning" | "error",
    efficiency_check: "ok" | "warning" | "error",
    warnings: string[],
    errors: string[]
  }
}
```

---

## Tool 1.6: create_trips_batch

### Description
Create multiple trips in a single transaction (atomic).

### Input Schema
```typescript
{
  trips: Array<{
    vehicle_id: string,
    start_checkpoint_id: string,
    end_checkpoint_id?: string,
    template_id?: string,
    date: string,
    distance_km: number,
    purpose: "business" | "personal",
    business_description?: string,
    notes?: string
  }>
}
```

### Output Schema
```typescript
{
  success: boolean,
  created_trip_ids: string[],
  failed_count: number,
  total_distance_km: number
}
```

---

## Server 2: trip-reconstructor (Custom - Stateless Algorithm)

### Purpose
**Pure matching algorithm** - receives gap data and templates, returns scored matches. **No database access**, **no external API calls** (except via parameters).

### Priority
**P0** - Required for MVP

### Implementation
Python (algorithm-focused)

### Configuration
```json
{
  "mcpServers": {
    "trip-reconstructor": {
      "command": "python",
      "args": ["-m", "mcp_servers.trip_reconstructor"],
      "env": {
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

---

## Tool 2.1: match_templates

### Description
Match templates to gap using hybrid GPS + address scoring. **Stateless** - all data passed as input.

### Input Schema
```typescript
{
  gap_data: {
    distance_km: number,
    days: number,
    hours: number,
    start_checkpoint: {
      odometer_reading: number,
      timestamp: string,
      coords?: {lat: number, lng: number},
      address?: string
    },
    end_checkpoint: {
      odometer_reading: number,
      timestamp: string,
      coords?: {lat: number, lng: number},
      address?: string
    },
    has_gps: boolean
  },
  templates: Array<{
    id: string,
    name: string,
    from_coords: {lat: number, lng: number},  // MANDATORY
    to_coords: {lat: number, lng: number},    // MANDATORY
    from_address?: string,
    to_address?: string,
    distance_km?: number,
    typical_days?: string[],
    is_round_trip?: boolean
  }>,
  geo_routes?: Array<{  // Optional: pre-calculated from geo-routing server
    distance_km: number,
    duration_hours: number,
    via: string
  }>
}
```

### Output Schema
```typescript
{
  matched_templates: Array<{
    template_id: string,
    template_name: string,
    confidence_score: number,  // 0-100 overall confidence

    // Detailed breakdown
    confidence_breakdown: {
      // GPS matching (always calculated if coords available)
      gps_match?: {
        start_distance_meters: number,
        end_distance_meters: number,
        start_score: number,  // 0-100
        end_score: number,    // 0-100
        combined_score: number,  // Average of start/end
        weight: number        // 0.7 (70%)
      },

      // Address matching (only if addresses provided)
      address_match?: {
        start_similarity: number,  // 0-1 string similarity
        end_similarity: number,
        start_score: number,  // 0-100
        end_score: number,
        combined_score: number,
        weight: number        // 0.3 (30%)
      },

      // Distance matching (only if template has distance_km)
      distance_match?: {
        template_distance_km: number,
        gap_distance_km: number,
        difference_km: number,
        difference_percentage: number,
        score: number  // 0-100
      },

      // Day-of-week matching (only if template has typical_days)
      day_match?: {
        template_days: string[],
        gap_day: string,
        matches: boolean,
        score: number  // 100 if matches, 50 if not
      }
    },

    // Reconstruction proposal
    suggested_count: number,  // How many times to use this template
    total_km: number,         // suggested_count × distance

    // Template completeness
    missing_optional_fields: string[],
    completeness_percentage: number  // 0-100
  }>,

  reconstruction_proposal: {
    proposed_trips: Array<{
      template_id: string,
      template_name: string,
      count: number,
      distance_km_per_trip: number,
      total_km: number
    }>,
    remainder_km: number,
    remainder_percentage: number,
    total_confidence: number,  // Weighted average
    coverage_percentage: number  // How much of gap is covered
  },

  suggestions: string[]  // Human-readable improvement tips
}
```

### Matching Algorithm Pseudocode

```python
def match_templates(gap_data, templates, geo_routes=None):
    """
    Stateless template matching with hybrid GPS + address scoring
    """
    results = []

    for template in templates:
        score = calculate_match_score(template, gap_data)
        results.append(score)

    # Sort by confidence descending
    results.sort(key=lambda x: x.confidence_score, reverse=True)

    # Generate reconstruction proposal
    proposal = generate_proposal(results, gap_data.distance_km)

    # Generate improvement suggestions
    suggestions = generate_suggestions(results, gap_data)

    return {
        "matched_templates": results,
        "reconstruction_proposal": proposal,
        "suggestions": suggestions
    }


def calculate_match_score(template, gap_data):
    """
    Hybrid scoring: GPS (70%) + Address (30%) + Distance + Day-of-week
    """
    breakdown = {}
    total_score = 0
    max_score = 0

    # 1. GPS Matching (if both have coordinates)
    if gap_data.has_gps and template.from_coords and template.to_coords:
        gps_result = score_gps_match(
            template.from_coords, template.to_coords,
            gap_data.start_checkpoint.coords, gap_data.end_checkpoint.coords
        )
        breakdown["gps_match"] = gps_result
        total_score += gps_result.combined_score * 0.7  # 70% weight
        max_score += 100 * 0.7

    # 2. Address Matching (if both have addresses)
    if (template.from_address and template.to_address and
        gap_data.start_checkpoint.address and gap_data.end_checkpoint.address):
        address_result = score_address_match(
            template.from_address, template.to_address,
            gap_data.start_checkpoint.address, gap_data.end_checkpoint.address
        )
        breakdown["address_match"] = address_result
        total_score += address_result.combined_score * 0.3  # 30% weight
        max_score += 100 * 0.3

    # 3. Distance Matching (bonus if template has distance)
    if template.distance_km:
        distance_result = score_distance_match(
            template.distance_km, gap_data.distance_km
        )
        breakdown["distance_match"] = distance_result
        # Bonus: Add to confidence if distance matches
        if distance_result.score >= 80:
            total_score += 10  # Confidence boost

    # 4. Day-of-Week Matching (bonus if template has typical_days)
    if template.typical_days:
        day_result = score_day_match(
            template.typical_days, gap_data.start_checkpoint.timestamp
        )
        breakdown["day_match"] = day_result
        if day_result.matches:
            total_score += 5  # Small confidence boost

    # Normalize score to 0-100
    if max_score > 0:
        confidence = min(100, (total_score / max_score) * 100)
    else:
        confidence = 0

    return {
        "template_id": template.id,
        "template_name": template.name,
        "confidence_score": confidence,
        "confidence_breakdown": breakdown,
        "suggested_count": calculate_suggested_count(template, gap_data),
        "total_km": ...,
        "missing_optional_fields": find_missing_fields(template),
        "completeness_percentage": calculate_completeness(template)
    }


def score_gps_match(from_coords_template, to_coords_template,
                    from_coords_gap, to_coords_gap):
    """
    Score GPS coordinate matching using Haversine distance
    """
    # Distance from template start to gap start
    start_distance_m = haversine(from_coords_template, from_coords_gap)

    # Distance from template end to gap end
    end_distance_m = haversine(to_coords_template, to_coords_gap)

    # Score based on distance thresholds
    def distance_to_score(meters):
        if meters < 100: return 100
        elif meters < 500: return 90
        elif meters < 2000: return 70
        elif meters < 5000: return 40
        else: return 0

    start_score = distance_to_score(start_distance_m)
    end_score = distance_to_score(end_distance_m)
    combined_score = (start_score + end_score) / 2

    return {
        "start_distance_meters": start_distance_m,
        "end_distance_meters": end_distance_m,
        "start_score": start_score,
        "end_score": end_score,
        "combined_score": combined_score,
        "weight": 0.7
    }


def score_address_match(from_addr_template, to_addr_template,
                        from_addr_gap, to_addr_gap):
    """
    Score address matching using string similarity + component extraction
    """
    # Normalize addresses
    from_template_norm = normalize_address(from_addr_template)
    to_template_norm = normalize_address(to_addr_template)
    from_gap_norm = normalize_address(from_addr_gap)
    to_gap_norm = normalize_address(to_addr_gap)

    # Calculate string similarity
    start_similarity = string_similarity(from_template_norm, from_gap_norm)
    end_similarity = string_similarity(to_template_norm, to_gap_norm)

    # Extract components (street, city, POI)
    from_template_parts = extract_address_parts(from_template_norm)
    to_template_parts = extract_address_parts(to_template_norm)
    from_gap_parts = extract_address_parts(from_gap_norm)
    to_gap_parts = extract_address_parts(to_gap_norm)

    # Score based on similarity and component matching
    def address_to_score(similarity, template_parts, gap_parts):
        if similarity > 0.9:
            return 100
        elif (template_parts["city"] == gap_parts["city"] and
              template_parts["street"] == gap_parts["street"]):
            return 100
        elif (template_parts["city"] == gap_parts["city"] and
              template_parts["poi"] == gap_parts["poi"]):
            return 80
        elif template_parts["city"] == gap_parts["city"]:
            return 50
        elif similarity > 0.6:
            return 40
        else:
            return 0

    start_score = address_to_score(start_similarity, from_template_parts, from_gap_parts)
    end_score = address_to_score(end_similarity, to_template_parts, to_gap_parts)
    combined_score = (start_score + end_score) / 2

    return {
        "start_similarity": start_similarity,
        "end_similarity": end_similarity,
        "start_score": start_score,
        "end_score": end_score,
        "combined_score": combined_score,
        "weight": 0.3
    }


def generate_proposal(scored_templates, gap_distance_km):
    """
    Generate trip reconstruction proposal from scored templates
    """
    proposed_trips = []
    remaining_distance = gap_distance_km

    # Use templates with confidence >= 70%
    viable_templates = [t for t in scored_templates if t.confidence_score >= 70]

    for template in viable_templates:
        if remaining_distance <= 0:
            break

        # Calculate how many times this template fits
        if template.distance_km:
            count = int(remaining_distance / template.distance_km)
        else:
            # Estimate from gap characteristics
            count = 1

        if count > 0:
            proposed_trips.append({
                "template_id": template.template_id,
                "template_name": template.template_name,
                "count": count,
                "distance_km_per_trip": template.distance_km,
                "total_km": count * template.distance_km
            })
            remaining_distance -= (count * template.distance_km)

    coverage = ((gap_distance_km - remaining_distance) / gap_distance_km) * 100

    return {
        "proposed_trips": proposed_trips,
        "remainder_km": remaining_distance,
        "remainder_percentage": (remaining_distance / gap_distance_km) * 100,
        "total_confidence": calculate_weighted_confidence(proposed_trips, scored_templates),
        "coverage_percentage": coverage
    }
```

---

## Tool 2.2: calculate_template_completeness

### Description
Calculate how complete a template is (useful for UI display).

### Input Schema
```typescript
{
  template: {
    id: string,
    name: string,
    from_coords: {lat, lng},
    to_coords: {lat, lng},
    from_address?: string,
    to_address?: string,
    distance_km?: number,
    typical_days?: string[],
    is_round_trip?: boolean,
    purpose?: string,
    business_description?: string
  }
}
```

### Output Schema
```typescript
{
  completeness_percentage: number,  // 0-100
  mandatory_fields: {
    filled: string[],  // ["name", "from_coords", "to_coords"]
    missing: string[]  // []
  },
  optional_fields: {
    filled: string[],  // ["distance_km", "typical_days"]
    missing: string[],  // ["from_address", "to_address", ...]
    impact_on_matching: {
      [field: string]: "HIGH" | "MEDIUM" | "LOW"
    }
  },
  suggestions: string[]  // What to add for better matching
}
```

---

## Server 3: geo-routing (Custom - Geographic Services)

### Purpose
Geocoding (address ↔ GPS) and route calculation via OpenStreetMap.

### Priority
**P0** - Required for GPS-based matching

### Implementation
Node.js wrapper around OSRM (Open Source Routing Machine)

### Configuration
```json
{
  "mcpServers": {
    "geo-routing": {
      "command": "node",
      "args": ["./mcp-servers/geo-routing/index.js"],
      "env": {
        "OSRM_BASE_URL": "https://router.project-osrm.org",
        "NOMINATIM_BASE_URL": "https://nominatim.openstreetmap.org",
        "CACHE_TTL_HOURS": "24"
      }
    }
  }
}
```

---

## Tool 3.1: geocode_address

### Description
**NEW TOOL** - Convert address text to GPS coordinates with ambiguity handling.

### Input Schema
```typescript
{
  address: string,
  country_hint?: string  // "SK", "CZ", "DE" - improves accuracy
}
```

### Output Schema
```typescript
{
  success: boolean,
  coordinates?: {
    latitude: number,
    longitude: number
  },
  normalized_address?: string,  // Cleaned up version
  confidence: number,  // 0-1
  alternatives?: Array<{
    address: string,
    coordinates: {lat: number, lng: number},
    confidence: number,
    type: string  // "street", "city", "poi", "region"
  }>,
  error?: string
}
```

### Example Responses

```javascript
// Clear address
geocode_address("Hlavná 45, Bratislava")
→ {
    success: true,
    coordinates: {lat: 48.1486, lng: 17.1077},
    normalized_address: "Hlavná 45, 811 01 Bratislava, Slovakia",
    confidence: 0.98,
    alternatives: []
  }

// Ambiguous address - multiple matches
geocode_address("Košice")
→ {
    success: true,
    coordinates: {lat: 48.7164, lng: 21.2611},  // Best guess
    normalized_address: "Košice, Slovakia",
    confidence: 0.65,
    alternatives: [
      {
        address: "Košice city center",
        coordinates: {lat: 48.7178, lng: 21.2575},
        confidence: 0.65,
        type: "city"
      },
      {
        address: "Košice-Západ (west district)",
        coordinates: {lat: 48.6900, lng: 21.1900},
        confidence: 0.55,
        type: "district"
      },
      {
        address: "Košice-Sever (north district)",
        coordinates: {lat: 48.7400, lng: 21.2500},
        confidence: 0.50,
        type: "district"
      }
    ]
  }

// Invalid address
geocode_address("asdfghjkl")
→ {
    success: false,
    error: "No results found for address"
  }
```

---

## Tool 3.2: reverse_geocode

### Description
Convert GPS coordinates to human-readable address.

### Input Schema
```typescript
{
  latitude: number,
  longitude: number
}
```

### Output Schema
```typescript
{
  address: {
    street?: string,
    house_number?: string,
    city: string,
    postal_code?: string,
    country: string,
    formatted: string
  },
  poi?: string  // Point of interest (e.g., "Shell Bratislava West")
}
```

---

## Tool 3.3: calculate_route

### Description
Calculate route(s) between two GPS coordinates.

### Input Schema
```typescript
{
  from_coords: {lat: number, lng: number},
  to_coords: {lat: number, lng: number},
  alternatives?: number,  // 1-3, default: 1
  vehicle?: "car" | "truck"  // default: "car"
}
```

### Output Schema
```typescript
{
  routes: Array<{
    distance_km: number,
    duration_hours: number,
    via: string,  // Summary: "via D1 highway"
    waypoints: Array<{
      name: string,
      latitude: number,
      longitude: number
    }>,
    route_type: "highway" | "local" | "mixed"
  }>
}
```

---

## Servers 4-7: Supporting Services

### Server 4: ekasa-api (Receipt Processing)
- Tool: `extract_qr_code(image_path)`
- Tool: `fetch_receipt(receipt_id)`
- Tool: `validate_receipt_id(receipt_id)`

### Server 5: filesystem (File Operations + EXIF)
- Tool: `extract_photo_metadata(file_path)`
- Tool: `write_file(path, content)`
- Tool: `read_file(path)`

### Server 6: sqlite (Data Persistence)
- Tool: `execute_query(sql, params)`
- Tool: `read_query(sql, params)`

### Server 7: report-generator (P1 - Reports)
- Tool: `generate_csv(trips, metadata)`
- Tool: `generate_pdf(trips, metadata, template)`

*(Detailed specs unchanged from v1 - refer to sections in original document)*

---

## Complete Workflow Example: Template Creation with Geocoding

```
User: "Create template Warehouse Run"

Skill Step 1: Gather name
"Template name?"
User: "Warehouse Run"

Skill Step 2: Get FROM location
"From location? (enter address or GPS)"
User: "Hlavná 45, Bratislava"

Skill Step 3: Geocode FROM
Call geo-routing.geocode_address("Hlavná 45, Bratislava")
→ {
    success: true,
    coordinates: {lat: 48.1486, lng: 17.1077},
    normalized_address: "Hlavná 45, 811 01 Bratislava",
    confidence: 0.98
  }

Skill: "✓ Found: Hlavná 45, Bratislava (GPS: 48.1486, 17.1077)
        Correct?"
User: "Yes"

Skill Step 4: Get TO location
"To location?"
User: "Košice"

Skill Step 5: Geocode TO (ambiguous!)
Call geo-routing.geocode_address("Košice")
→ {
    confidence: 0.65,
    alternatives: [
      {address: "Košice city center", coords: {48.7178, 21.2575}},
      {address: "Košice-Západ", coords: {48.6900, 21.1900}},
      {address: "Košice-Sever", coords: {48.7400, 21.2500}}
    ]
  }

Skill: "I found multiple matches:
        1. Košice city center (48.7178, 21.2575)
        2. Košice-Západ (48.6900, 21.1900)
        3. Košice-Sever (48.7400, 21.2500)
        4. Enter more specific address

        Which location?"
User: "2"

Skill Step 6: Calculate route distance
Call geo-routing.calculate_route(
  from_coords: {48.1486, 17.1077},
  to_coords: {48.6900, 21.1900}
)
→ {routes: [{distance_km: 395, via: "D1"}]}

Skill: "Route calculated: 395 km via D1

        Would you like to add optional details for better matching?

        1. Mark as round trip? [yes/no/skip]"
User: "yes"

Skill: "2. Typical days? [e.g., Monday, Thursday / skip]"
User: "Mondays"

Skill: "3. Purpose? [business/personal/skip]"
User: "Business"

Skill: "4. Business description? [skip if not needed]"
User: "Warehouse pickup"

Skill Step 7: Create template
Call car-log-core.create_template({
  name: "Warehouse Run",
  from_coords: {lat: 48.1486, lng: 17.1077},
  from_address: "Hlavná 45, 811 01 Bratislava, Slovakia",
  from_label: "Bratislava",
  to_coords: {lat: 48.6900, lng: 21.1900},
  to_address: "Košice-Západ, Slovakia",
  to_label: "Košice",
  distance_km: 395,
  is_round_trip: true,
  typical_days: ["Monday"],
  purpose: "business",
  business_description: "Warehouse pickup"
})
→ {success: true, template_id: "uuid-123", completeness_percentage: 100}

Skill: "✓ Template 'Warehouse Run' created!

        Summary:
        • From: Hlavná 45, Bratislava → GPS: 48.1486, 17.1077
        • To: Košice-Západ → GPS: 48.6900, 21.1900
        • Distance: 395 km (round trip via D1)
        • Typical: Mondays
        • Purpose: Business (warehouse pickup)

        Completeness: 100% ✓
        This template is fully optimized for high-confidence matching!"
```

---

## Template Completeness Calculation

```
Mandatory fields (must always be present):
  - name
  - from_coords
  - to_coords

Optional fields (enhance matching):
  HIGH impact on matching:
    - from_address (enables address matching)
    - to_address (enables address matching)
    - distance_km (enables distance matching)

  MEDIUM impact:
    - typical_days (enables day-of-week matching)
    - is_round_trip (helps distance estimation)

  LOW impact (metadata only):
    - from_label
    - to_label
    - purpose
    - business_description
    - notes

Completeness calculation:
  Total optional fields: 10
  Filled optional fields: 7

  Completeness = (7 / 10) * 100 = 70%
```

---

## Error Handling Strategy

### Error Response Format
```typescript
{
  success: false,
  error: {
    code: string,
    message: string,
    details?: object,
    retry_after?: number  // For rate limiting
  }
}
```

### Common Error Codes
- `INVALID_INPUT`: Validation failed
- `NOT_FOUND`: Resource doesn't exist
- `DUPLICATE`: Resource already exists
- `GPS_REQUIRED`: Operation needs GPS coordinates
- `GEOCODING_FAILED`: Address could not be resolved
- `AMBIGUOUS_ADDRESS`: Multiple matches found (not fatal - return alternatives)
- `RATE_LIMIT`: Too many requests
- `EXTERNAL_API_ERROR`: Third-party service failed

---

## Testing Strategy

### Unit Tests

**car-log-core:**
- CRUD operations with valid/invalid data
- Transaction rollback on errors
- Foreign key constraints

**trip-reconstructor:**
- Pure function testing with mock data
- GPS matching at various distances (10m, 100m, 1km, 10km)
- Address matching with similar/different strings
- Proposal generation with various template combinations
- Edge cases: no templates, no GPS, ambiguous matches

**geo-routing:**
- Geocoding with clear addresses
- Geocoding with ambiguous addresses (multiple results)
- Reverse geocoding accuracy
- Route calculation between various cities
- Error handling for invalid coordinates/addresses

### Integration Tests
- End-to-end reconstruction workflow
- Template creation with geocoding
- Checkpoint creation with EXIF + geocoding
- Multi-template matching scenarios

### Performance Tests
- trip-reconstructor with 100+ templates
- Geocoding response time
- Route calculation response time
- Batch trip creation (50+ trips)

---

## Migration from v1

### Breaking Changes

1. **trip-reconstructor is now separate server**
   - Old: Part of car-log-core
   - New: Dedicated stateless service

2. **Template structure changed**
   - Old: `from_location` was string only
   - New: `from_coords` (mandatory) + `from_address` (optional)

3. **Checkpoint structure changed**
   - Old: `location` was optional GPS
   - New: `coords` (GPS, source of truth) + `address` (optional label)

4. **Matching logic moved**
   - Old: car-log-core.match_templates_to_gap()
   - New: trip-reconstructor.match_templates()

5. **Geocoding added**
   - New tool: geo-routing.geocode_address()
   - Supports ambiguity handling

### Migration Path

**Phase 1:** Add new servers
- Deploy trip-reconstructor server
- Update geo-routing with geocode_address tool

**Phase 2:** Update Skills/DSPy
- Modify orchestration to call trip-reconstructor
- Add geocoding calls for template creation

**Phase 3:** Update database schema
- Add `coords`, `address`, `location_source` to checkpoints table
- Add `from_coords`, `from_address`, `from_label` to templates table

**Phase 4:** Deprecate old tools
- Mark car-log-core matching tools as deprecated
- Migrate existing data to new format

---

## Related Documents

- [01-product-overview.md](./01-product-overview.md) - Product vision and scope
- [02-domain-model.md](./02-domain-model.md) - Core concepts and terminology
- [03-trip-reconstruction.md](./03-trip-reconstruction.md) - Algorithm specification
- [04-data-model.md](./04-data-model.md) - JSON file schemas
- [05-claude-skills-dspy.md](./05-claude-skills-dspy.md) - Dual interface architecture
- [07-mcp-api-specifications.md](./07-mcp-api-specifications.md) - Complete API tool definitions

---

## Next Steps

1. **Implement trip-reconstructor MCP server** (Python)
2. **Add geocode_address tool to geo-routing** (Node.js)
3. **Update car-log-core** with new schemas
4. **Update Skills** for orchestration pattern
5. **Update data model** document with new schemas
6. **Write unit tests** for matching algorithm
7. **Integration testing** with all servers

---

## Appendix: Configuration Example

```json
{
  "mcpServers": {
    "car-log-core": {
      "command": "python",
      "args": ["-m", "mcp_servers.car_log_core"],
      "env": {
        "DB_PATH": "./data/car-log.db"
      }
    },
    "trip-reconstructor": {
      "command": "python",
      "args": ["-m", "mcp_servers.trip_reconstructor"]
    },
    "geo-routing": {
      "command": "node",
      "args": ["./mcp-servers/geo-routing/index.js"],
      "env": {
        "OSRM_BASE_URL": "https://router.project-osrm.org",
        "NOMINATIM_BASE_URL": "https://nominatim.openstreetmap.org"
      }
    },
    "ekasa-api": {
      "command": "python",
      "args": ["-m", "mcp_servers.ekasa_api"],
      "env": {
        "EKASA_API_KEY": "${EKASA_API_KEY}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "./data/photos"
      ]
    },
    "sqlite": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sqlite",
        "./data/car-log.db"
      ]
    }
  }
}
```
