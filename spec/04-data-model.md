# Data Model: Car Log

**Version:** 1.0
**Date:** 2025-11-17
**Status:** Complete - File-Based Storage Architecture

---

## Overview

This document defines the **complete data model** for Car Log using **JSON file-based storage**. No database is required for MVP.

**Storage Decision:** Use JSON files instead of database for:
- Human-readable data
- Git-friendly version control
- Complete portability (copy folder = backup)
- No setup required
- User transparency and control

---

## File Structure

```
~/Documents/MileageLog/
├── data/
│   ├── config.json                    # App configuration
│   ├── vehicles/
│   │   └── {vehicle-id}.json          # One file per vehicle
│   ├── checkpoints/
│   │   └── {YYYY-MM}/
│   │       └── {checkpoint-id}.json   # Month-based folders
│   ├── trips/
│   │   └── {YYYY-MM}/
│   │       ├── {trip-id}.json         # Month-based folders
│   │       └── index.json             # Optional: Monthly index for performance
│   └── typical-destinations.json      # Saved trip templates
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

---

## Entity 1: Vehicle

**File Location:** `data/vehicles/{vehicle-id}.json`

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["vehicle_id", "name", "license_plate", "vin", "fuel_type", "initial_odometer_km"],
  "properties": {
    "vehicle_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier"
    },
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 50,
      "description": "Human-readable vehicle name",
      "examples": ["Ford Transit Delivery Van", "Company Car 1"]
    },
    "license_plate": {
      "type": "string",
      "pattern": "^[A-Z]{2}-[0-9]{3}[A-Z]{2}$",
      "description": "Slovak license plate format",
      "examples": ["BA-456CD", "KE-123AB"]
    },
    "vin": {
      "type": "string",
      "pattern": "^[A-HJ-NPR-Z0-9]{17}$",
      "description": "Vehicle Identification Number (17 characters, no I/O/Q)",
      "examples": ["WBAXX01234ABC5678"]
    },
    "make": {
      "type": "string",
      "maxLength": 30,
      "description": "Vehicle manufacturer",
      "examples": ["Ford", "Škoda", "Volkswagen"]
    },
    "model": {
      "type": "string",
      "maxLength": 30,
      "description": "Vehicle model",
      "examples": ["Transit", "Octavia", "Caddy"]
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
    },
    "current_odometer_km": {
      "type": "integer",
      "minimum": 0,
      "maximum": 999999,
      "description": "Latest odometer reading (updated automatically)"
    },
    "average_efficiency_l_per_100km": {
      "type": "number",
      "minimum": 3.0,
      "maximum": 25.0,
      "description": "Average fuel efficiency in L/100km (European standard)"
    },
    "active": {
      "type": "boolean",
      "default": true,
      "description": "Whether vehicle is actively tracked"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "When vehicle was added to system"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "Last modification timestamp"
    }
  }
}
```

### Example File

**File:** `data/vehicles/550e8400-e29b-41d4-a716-446655440000.json`

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

---

## Entity 2: Checkpoint

**File Location:** `data/checkpoints/{YYYY-MM}/{checkpoint-id}.json`

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["checkpoint_id", "vehicle_id", "checkpoint_type", "datetime", "odometer_km"],
  "properties": {
    "checkpoint_id": {
      "type": "string",
      "format": "uuid"
    },
    "vehicle_id": {
      "type": "string",
      "format": "uuid",
      "description": "Reference to vehicle file"
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
      "description": "Relative path to dashboard photo",
      "examples": ["dashboard-photos/2025-11/660e8400-dashboard.jpg"]
    },
    "odometer_confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "OCR confidence score (0-1)"
    },
    "location": {
      "type": "object",
      "properties": {
        "address": {
          "type": "string",
          "description": "Human-readable address"
        },
        "coords": {
          "type": "object",
          "properties": {
            "lat": { "type": "number", "minimum": -90, "maximum": 90 },
            "lng": { "type": "number", "minimum": -180, "maximum": 180 }
          },
          "required": ["lat", "lng"]
        },
        "city": {
          "type": "string",
          "description": "City name for filtering"
        }
      }
    },
    "receipt": {
      "type": "object",
      "description": "Receipt data (if refuel checkpoint)",
      "properties": {
        "receipt_id": {
          "type": "string",
          "description": "e-Kasa receipt ID or custom ID"
        },
        "receipt_photo_path": {
          "type": "string",
          "description": "Path to receipt photo"
        },
        "vendor_name": {
          "type": "string",
          "description": "Fuel station name"
        },
        "fuel_type": {
          "type": "string",
          "enum": ["Diesel", "Gasoline_95", "Gasoline_98", "LPG", "CNG", "Electric"]
        },
        "fuel_liters": {
          "type": "number",
          "minimum": 0,
          "maximum": 500,
          "description": "Fuel quantity in liters (or kWh for electric)"
        },
        "fuel_cost_eur": {
          "type": "number",
          "minimum": 0,
          "description": "Fuel cost in EUR (excluding other items)"
        },
        "price_per_liter": {
          "type": "number",
          "minimum": 0,
          "description": "Price per liter (or per kWh)"
        },
        "total_amount_eur": {
          "type": "number",
          "minimum": 0,
          "description": "Total receipt amount (may include non-fuel items)"
        },
        "vat_amount_eur": {
          "type": "number",
          "minimum": 0,
          "description": "VAT amount for fuel purchase"
        }
      },
      "required": ["receipt_id", "fuel_type", "fuel_liters", "fuel_cost_eur"]
    },
    "previous_checkpoint_id": {
      "type": ["string", "null"],
      "format": "uuid",
      "description": "ID of previous checkpoint for this vehicle"
    },
    "distance_since_previous_km": {
      "type": "integer",
      "minimum": 0,
      "description": "Calculated distance since previous checkpoint"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

### Example File

**File:** `data/checkpoints/2025-11/660e8400-e29b-41d4-a716-446655440001.json`

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
    "coords": {
      "lat": 48.1486,
      "lng": 17.1077
    },
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

---

## Entity 3: Trip

**File Location:** `data/trips/{YYYY-MM}/{trip-id}.json`

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["trip_id", "vehicle_id", "checkpoint_start_id", "checkpoint_end_id", "trip_start_datetime", "trip_end_datetime", "driver_name", "distance_km", "trip_purpose"],
  "properties": {
    "trip_id": {
      "type": "string",
      "format": "uuid"
    },
    "vehicle_id": {
      "type": "string",
      "format": "uuid"
    },
    "checkpoint_start_id": {
      "type": "string",
      "format": "uuid",
      "description": "Reference to start checkpoint"
    },
    "checkpoint_end_id": {
      "type": "string",
      "format": "uuid",
      "description": "Reference to end checkpoint"
    },
    "trip_start_datetime": {
      "type": "string",
      "format": "date-time",
      "description": "SLOVAK COMPLIANCE: When trip started (separate from refuel time)"
    },
    "trip_end_datetime": {
      "type": "string",
      "format": "date-time",
      "description": "SLOVAK COMPLIANCE: When trip ended"
    },
    "trip_duration_hours": {
      "type": "number",
      "minimum": 0,
      "description": "Calculated trip duration in hours"
    },
    "trip_start_location": {
      "type": "string",
      "description": "SLOVAK COMPLIANCE: Trip origin (separate from fuel station)"
    },
    "trip_end_location": {
      "type": "string",
      "description": "SLOVAK COMPLIANCE: Trip destination"
    },
    "trip_start_coords": {
      "type": "object",
      "properties": {
        "lat": { "type": "number", "minimum": -90, "maximum": 90 },
        "lng": { "type": "number", "minimum": -180, "maximum": 180 }
      }
    },
    "trip_end_coords": {
      "type": "object",
      "properties": {
        "lat": { "type": "number", "minimum": -90, "maximum": 90 },
        "lng": { "type": "number", "minimum": -180, "maximum": 180 }
      }
    },
    "driver_name": {
      "type": "string",
      "minLength": 1,
      "description": "SLOVAK COMPLIANCE: Driver full name (MANDATORY)"
    },
    "driver_id": {
      "type": ["string", "null"],
      "format": "uuid",
      "description": "SLOVAK COMPLIANCE: Optional link to Driver entity"
    },
    "driver_is_owner": {
      "type": "boolean",
      "description": "SLOVAK COMPLIANCE: Flag for owner-driver"
    },
    "distance_km": {
      "type": "number",
      "minimum": 0,
      "description": "Trip distance in kilometers"
    },
    "fuel_consumption_liters": {
      "type": "number",
      "minimum": 0,
      "description": "Fuel consumed during trip (calculated or estimated)"
    },
    "fuel_efficiency_l_per_100km": {
      "type": "number",
      "minimum": 3.0,
      "maximum": 25.0,
      "description": "Fuel efficiency in L/100km (European standard)"
    },
    "fuel_cost_eur": {
      "type": "number",
      "minimum": 0,
      "description": "Allocated fuel cost for this trip"
    },
    "trip_purpose": {
      "type": "string",
      "enum": ["Business", "Personal"],
      "description": "Trip classification for tax purposes"
    },
    "business_purpose_description": {
      "type": "string",
      "description": "Required if trip_purpose is Business"
    },
    "refuel_datetime": {
      "type": "string",
      "format": "date-time",
      "description": "SLOVAK COMPLIANCE: When refuel occurred (may differ from trip time)"
    },
    "refuel_timing": {
      "type": "string",
      "enum": ["before", "during", "after"],
      "description": "SLOVAK COMPLIANCE: Refuel timing relative to trip"
    },
    "reconstruction_method": {
      "type": "string",
      "enum": ["manual", "template", "geo_assisted", "user_specified"],
      "description": "How trip was created"
    },
    "template_used": {
      "type": "string",
      "description": "Name of template used (if applicable)"
    },
    "confidence_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Reconstruction confidence (0-1)"
    },
    "validation": {
      "type": "object",
      "description": "Validation results",
      "properties": {
        "status": {
          "type": "string",
          "enum": ["validated", "has_warnings", "has_errors"]
        },
        "distance_check": {
          "type": "string",
          "enum": ["ok", "warning", "error"]
        },
        "efficiency_check": {
          "type": "string",
          "enum": ["ok", "warning", "error"]
        },
        "warnings": {
          "type": "array",
          "items": { "type": "string" }
        },
        "errors": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

### Example File

**File:** `data/trips/2025-11/770e8400-e29b-41d4-a716-446655440002.json`

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
  "trip_start_coords": {
    "lat": 48.1486,
    "lng": 17.1077
  },
  "trip_end_coords": {
    "lat": 48.7164,
    "lng": 21.2611
  },

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

---

## Entity 4: Trip Template (Typical Destination)

**File Location:** `data/typical-destinations.json`

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "templates": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["template_id", "name", "from_coords", "to_coords"],
        "properties": {
          "template_id": {
            "type": "string",
            "format": "uuid"
          },
          "name": {
            "type": "string",
            "minLength": 1,
            "description": "Template name (e.g., 'Warehouse Run')"
          },
          "from_coords": {
            "type": "object",
            "required": ["lat", "lng"],
            "properties": {
              "lat": { "type": "number", "minimum": -90, "maximum": 90 },
              "lng": { "type": "number", "minimum": -180, "maximum": 180 }
            },
            "description": "MANDATORY - Source of truth for matching"
          },
          "to_coords": {
            "type": "object",
            "required": ["lat", "lng"],
            "properties": {
              "lat": { "type": "number", "minimum": -90, "maximum": 90 },
              "lng": { "type": "number", "minimum": -180, "maximum": 180 }
            },
            "description": "MANDATORY - Source of truth for matching"
          },
          "from_address": {
            "type": "string",
            "description": "OPTIONAL - Human-readable label"
          },
          "to_address": {
            "type": "string",
            "description": "OPTIONAL - Human-readable label"
          },
          "distance_km": {
            "type": "number",
            "minimum": 0,
            "description": "OPTIONAL - Typical distance"
          },
          "is_round_trip": {
            "type": "boolean",
            "description": "OPTIONAL - Whether this is a round trip"
          },
          "typical_days": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            },
            "description": "OPTIONAL - Days when this trip typically occurs"
          },
          "purpose": {
            "type": "string",
            "enum": ["business", "personal"]
          },
          "business_description": {
            "type": "string"
          },
          "notes": {
            "type": "string"
          },
          "usage_count": {
            "type": "integer",
            "minimum": 0,
            "description": "How many times this template has been used"
          },
          "last_used_at": {
            "type": "string",
            "format": "date-time"
          },
          "created_at": {
            "type": "string",
            "format": "date-time"
          }
        }
      }
    }
  }
}
```

### Example File

**File:** `data/typical-destinations.json`

```json
{
  "templates": [
    {
      "template_id": "880e8400-e29b-41d4-a716-446655440003",
      "name": "Warehouse Run",
      "from_coords": {
        "lat": 48.1486,
        "lng": 17.1077
      },
      "to_coords": {
        "lat": 48.7164,
        "lng": 21.2611
      },
      "from_address": "Main Office, Hlavná 12, Bratislava",
      "to_address": "Warehouse, Mlynská 45, Košice",
      "distance_km": 410,
      "is_round_trip": true,
      "typical_days": ["Monday", "Thursday"],
      "purpose": "business",
      "business_description": "Picking up supplies from warehouse",
      "notes": "Via E50 highway (faster than D1)",
      "usage_count": 12,
      "last_used_at": "2025-11-15T09:00:00Z",
      "created_at": "2025-01-15T10:00:00Z"
    },
    {
      "template_id": "880e8400-e29b-41d4-a716-446655440004",
      "name": "Daily Commute",
      "from_coords": {
        "lat": 48.1850,
        "lng": 17.1250
      },
      "to_coords": {
        "lat": 48.1486,
        "lng": 17.1077
      },
      "from_address": "Home",
      "to_address": "Office, Bratislava",
      "distance_km": 25,
      "is_round_trip": true,
      "typical_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "purpose": "business",
      "usage_count": 156,
      "last_used_at": "2025-11-15T17:30:00Z",
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

---

## Entity 5: Monthly Index (Optional - Performance Optimization)

**File Location:** `data/trips/{YYYY-MM}/index.json`

### Purpose
Fast monthly summary without reading all trip files.

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "month": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}$",
      "description": "Month in YYYY-MM format"
    },
    "vehicle_id": {
      "type": "string",
      "format": "uuid"
    },
    "trip_count": {
      "type": "integer",
      "minimum": 0
    },
    "total_distance_km": {
      "type": "number",
      "minimum": 0
    },
    "total_fuel_liters": {
      "type": "number",
      "minimum": 0
    },
    "total_cost_eur": {
      "type": "number",
      "minimum": 0
    },
    "business_trip_count": {
      "type": "integer",
      "minimum": 0
    },
    "personal_trip_count": {
      "type": "integer",
      "minimum": 0
    },
    "trip_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      }
    },
    "generated_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

### Example File

**File:** `data/trips/2025-11/index.json`

```json
{
  "month": "2025-11",
  "vehicle_id": "550e8400-e29b-41d4-a716-446655440000",
  "trip_count": 28,
  "total_distance_km": 2300,
  "total_fuel_liters": 195.0,
  "total_cost_eur": 292.50,
  "business_trip_count": 22,
  "personal_trip_count": 6,
  "trip_ids": [
    "770e8400-e29b-41d4-a716-446655440002",
    "770e8400-e29b-41d4-a716-446655440003"
  ],
  "generated_at": "2025-12-01T00:00:00Z"
}
```

---

## Atomic Write Pattern

**CRITICAL:** Never write directly to final file (risk of corruption)

### Implementation

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

### Python Implementation

```python
import json
import os
from pathlib import Path

def save_trip_atomic(trip_data: dict, trip_id: str, month: str):
    """
    Atomically save trip data to JSON file
    """
    # Create directory if needed
    trip_dir = Path(f"data/trips/{month}")
    trip_dir.mkdir(parents=True, exist_ok=True)

    final_path = trip_dir / f"{trip_id}.json"
    temp_path = trip_dir / f"{trip_id}.json.tmp"

    try:
        # Write to temp file
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(trip_data, f, indent=2, ensure_ascii=False)

        # Atomic rename
        temp_path.replace(final_path)

        return True
    except Exception as e:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise e
```

---

## File Organization Best Practices

### Monthly Folders

**Why monthly folders?**
- Typical usage: 20-30 trips per month
- Easy to archive old months
- Performance: Smaller directory listings
- Human-readable organization

**Folder naming:** `YYYY-MM` format (e.g., `2025-11`)

### File Naming

- **Vehicles:** `{uuid}.json`
- **Checkpoints:** `{uuid}.json` (in monthly folder)
- **Trips:** `{uuid}.json` (in monthly folder)
- **Photos:** `{uuid}-{type}.jpg` (e.g., `abc123-dashboard.jpg`)

### JSON Formatting

All JSON files should be:
- **Pretty-printed** with 2-space indentation
- **UTF-8 encoded** (supports Slovak characters: á, č, ď, é, í, ĺ, ľ, ň, ó, ô, ŕ, š, ť, ú, ý, ž)
- **Line endings:** LF (Unix-style) for Git compatibility

---

## Storage Performance

### Read Performance

**Typical operation:** Read all trips for a month
- **Without index:** Read 28 JSON files (~15-20KB each) = ~0.5MB total
- **With index:** Read 1 index file (~2KB) for summary, then specific trip files as needed

**Recommendation:** Generate monthly index at end of month

### Write Performance

**Atomic write overhead:** ~5-10ms per file (acceptable for user-driven actions)

### Scalability Limits

**MVP target:** 1 vehicle, 30 trips/month, 12 months = ~360 trip files
- **File count:** ~360 trip files + ~60 checkpoint files + 1 vehicle file = ~421 files
- **Total size:** ~10-15 MB (JSON + photos)
- **Performance:** Excellent for MVP scope

**Growth scenario:** 5 vehicles, 50 trips/month/vehicle, 3 years
- **File count:** ~9,000 trip files + ~1,800 checkpoint files = ~10,800 files
- **Total size:** ~250-300 MB
- **Performance:** Still acceptable with monthly indexes

---

## Migration to Database (Future - P2)

If file-based storage becomes inadequate:

### Migration Path

1. **Define SQLite schema** based on JSON schemas
2. **Create migration script** to read all JSON files and insert into database
3. **Update MCP servers** to use SQLite instead of filesystem
4. **Keep file-based option** for backup/export

### When to Migrate

Triggers for migration:
- More than 10,000 trip files
- Complex queries needed (e.g., "all trips to Košice in 2025")
- Multi-user concurrent access required
- Performance degradation

---

## Related Documents

- [02-domain-model.md](./02-domain-model.md) - Core concepts
- [03-trip-reconstruction.md](./03-trip-reconstruction.md) - Algorithms
- [06-mcp-architecture-v2.md](./06-mcp-architecture-v2.md) - MCP servers
- [07-mcp-api-specifications.md](./07-mcp-api-specifications.md) - API details

---

## Appendix: Validation Ranges Summary

```json
{
  "validation": {
    "odometer": {
      "min_km": 0,
      "max_km": 999999,
      "max_daily_distance_km": 1000
    },
    "fuel_efficiency_l_per_100km": {
      "Diesel": { "min": 5.0, "max": 15.0 },
      "Gasoline": { "min": 6.0, "max": 20.0 },
      "LPG": { "min": 8.0, "max": 25.0 },
      "Hybrid": { "min": 3.0, "max": 8.0 },
      "Electric": { "min": 12.0, "max": 25.0 }
    },
    "distance_variance_percent": 10,
    "consumption_variance_percent": 15,
    "efficiency_deviation_percent": 20
  }
}
```

---

**Document Status:** Complete - Ready for Implementation
**Last Updated:** 2025-11-17
**Storage Format:** JSON file-based (no database required)
