# MCP API Specifications: Car Log

**Version:** 1.0
**Date:** 2025-11-17
**Status:** Complete - Production-Ready Tool Definitions

---

## Overview

This document provides **complete, production-ready MCP tool definitions** with full input/output schemas, validation rules, and error responses for all 7 MCP servers.

**Total Tools:** 24 documented (23 implemented, 4-6 trip tools missing)

**Implementation Status:**
- ✅ 23 tools implemented and tested
- ❌ 4-6 trip CRUD tools documented but NOT implemented (critical blocker)

**Architecture:** Headless MCP servers that power both Claude Desktop (P0) and Gradio UI (P1)

---

## MCP Server Summary

| Server | Purpose | Priority | Tools Count | Status |
|--------|---------|----------|-------------|--------|
| `car-log-core` | CRUD operations (file-based storage) | P0 | 10 implemented, 4-6 trip tools missing | ⚠️ PARTIAL |
| `trip-reconstructor` | Stateless template matching | P0 | 2 | ✅ COMPLETE |
| `geo-routing` | Geocoding + routing (OpenStreetMap) | P0 | 3 | ✅ COMPLETE |
| `ekasa-api` | Receipt processing (e-Kasa Slovakia) | P0 | 2 | ✅ COMPLETE |
| `dashboard-ocr` | Photo OCR + EXIF extraction | P0/P1 | 1 (P0), 2 (P1) | ✅ P0 COMPLETE |
| `validation` | Data validation algorithms | P0 | 4 | ✅ COMPLETE |
| `report-generator` | PDF/CSV generation | P0/P1 | 1 (P0), 1 (P1) | ✅ P0 COMPLETE |

**Critical Gap:** Trip CRUD tools (create_trip, create_trips_batch, list_trips, get_trip) are documented in this specification but NOT implemented. This blocks the end-to-end workflow.

---

## Server 1: car-log-core (10 implemented + 4-6 missing)

**Purpose:** CRUD operations for vehicles, checkpoints, trips, templates
**Storage:** JSON file-based in `~/Documents/MileageLog/data/`
**Language:** Python

---

### Tool 1.1: `create_vehicle`

Create new vehicle with Slovak tax compliance (VIN required).

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 50,
      "description": "Human-readable vehicle name",
      "examples": ["Ford Transit Delivery Van"]
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

**Example Request:**
```json
{
  "name": "Ford Transit Delivery Van",
  "license_plate": "BA-456CD",
  "vin": "WBAXX01234ABC5678",
  "make": "Ford",
  "model": "Transit",
  "year": 2022,
  "fuel_type": "Diesel",
  "initial_odometer_km": 15000
}
```

**Example Response:**
```json
{
  "success": true,
  "vehicle_id": "550e8400-e29b-41d4-a716-446655440000",
  "vehicle": {
    "vehicle_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Ford Transit Delivery Van",
    "license_plate": "BA-456CD",
    "vin": "WBAXX01234ABC5678",
    "make": "Ford",
    "model": "Transit",
    "year": 2022,
    "fuel_type": "Diesel",
    "initial_odometer_km": 15000,
    "current_odometer_km": 15000,
    "average_efficiency_l_per_100km": null,
    "active": true,
    "created_at": "2025-11-17T10:00:00Z",
    "updated_at": "2025-11-17T10:00:00Z"
  },
  "message": "Vehicle created successfully"
}
```

---

### Tool 1.2: `get_vehicle`

Retrieve vehicle by ID.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "vehicle_id": {
      "type": "string",
      "format": "uuid"
    }
  },
  "required": ["vehicle_id"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "vehicle": { "type": "object" }
  }
}
```

---

### Tool 1.3: `list_vehicles`

List all vehicles (with optional filters).

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "active_only": {
      "type": "boolean",
      "default": true,
      "description": "Only return active vehicles"
    },
    "fuel_type": {
      "type": "string",
      "enum": ["Diesel", "Gasoline", "LPG", "Hybrid", "Electric"],
      "description": "Filter by fuel type"
    }
  }
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "vehicles": {
      "type": "array",
      "items": { "type": "object" }
    },
    "count": { "type": "integer" }
  }
}
```

---

### Tool 1.4: `update_vehicle`

Update vehicle details.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "vehicle_id": { "type": "string", "format": "uuid" },
    "name": { "type": "string" },
    "average_efficiency_l_per_100km": { "type": "number" },
    "active": { "type": "boolean" }
  },
  "required": ["vehicle_id"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "vehicle": { "type": "object" },
    "message": { "type": "string" }
  }
}
```

---

### Tool 1.5: `create_checkpoint`

Create checkpoint from refuel or manual entry.

**Note on Data Transformation:** API uses flat fields (`location_address`, `location_coords`) for simplicity. The server transforms these into nested `location` object when storing (see 04-data-model.md). Similarly, `receipt_id`, `fuel_liters`, etc. are grouped into `receipt` object in storage.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "vehicle_id": { "type": "string", "format": "uuid" },
    "checkpoint_type": {
      "type": "string",
      "enum": ["refuel", "manual", "month_end"]
    },
    "datetime": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp"
    },
    "odometer_km": {
      "type": "integer",
      "minimum": 0
    },
    "odometer_source": {
      "type": "string",
      "enum": ["photo", "manual", "photo_adjusted"]
    },
    "odometer_photo_path": { "type": "string" },
    "odometer_confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "location_address": { "type": "string" },
    "location_coords": {
      "type": "object",
      "properties": {
        "lat": { "type": "number", "minimum": -90, "maximum": 90 },
        "lng": { "type": "number", "minimum": -180, "maximum": 180 }
      }
    },
    "receipt_id": { "type": "string" },
    "fuel_liters": {
      "type": "number",
      "minimum": 0,
      "maximum": 500
    },
    "fuel_cost_eur": {
      "type": "number",
      "minimum": 0
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

---

### Tool 1.6: `get_checkpoint`

Retrieve checkpoint by ID.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "checkpoint_id": { "type": "string", "format": "uuid" }
  },
  "required": ["checkpoint_id"]
}
```

---

### Tool 1.7: `list_checkpoints`

List checkpoints with filters.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "vehicle_id": { "type": "string", "format": "uuid" },
    "start_date": { "type": "string", "format": "date" },
    "end_date": { "type": "string", "format": "date" },
    "checkpoint_type": {
      "type": "string",
      "enum": ["refuel", "manual", "month_end"]
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 50
    }
  },
  "required": ["vehicle_id"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "checkpoints": { "type": "array" },
    "count": { "type": "integer" }
  }
}
```

---

### Tool 1.8: `detect_gap`

Analyze distance/time between checkpoints.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "start_checkpoint_id": { "type": "string", "format": "uuid" },
    "end_checkpoint_id": { "type": "string", "format": "uuid" }
  },
  "required": ["start_checkpoint_id", "end_checkpoint_id"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "distance_km": { "type": "number" },
    "days": { "type": "number" },
    "hours": { "type": "number" },
    "start_checkpoint": { "type": "object" },
    "end_checkpoint": { "type": "object" },
    "has_gps": { "type": "boolean" },
    "avg_km_per_day": { "type": "number" },
    "reconstruction_recommended": { "type": "boolean" }
  }
}
```

---

## Server 2: trip-reconstructor (2 tools)

**Purpose:** Stateless template matching algorithm
**Language:** Python

---

### Tool 2.1: `match_templates`

Match templates to gap using hybrid GPS + address scoring.

**IMPORTANT:** This is a **stateless** function. All data must be passed as input parameters.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "gap_data": {
      "type": "object",
      "properties": {
        "distance_km": { "type": "number" },
        "days": { "type": "number" },
        "hours": { "type": "number" },
        "start_checkpoint": {
          "type": "object",
          "properties": {
            "odometer_reading": { "type": "number" },
            "timestamp": { "type": "string", "format": "date-time" },
            "coords": {
              "type": "object",
              "properties": {
                "lat": { "type": "number" },
                "lng": { "type": "number" }
              }
            },
            "address": { "type": "string" }
          },
          "required": ["odometer_reading", "timestamp"]
        },
        "end_checkpoint": {
          "type": "object",
          "description": "Same structure as start_checkpoint"
        },
        "has_gps": { "type": "boolean" }
      },
      "required": ["distance_km", "days", "hours", "start_checkpoint", "end_checkpoint", "has_gps"]
    },
    "templates": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string", "format": "uuid" },
          "name": { "type": "string" },
          "from_coords": {
            "type": "object",
            "properties": {
              "lat": { "type": "number" },
              "lng": { "type": "number" }
            },
            "required": ["lat", "lng"],
            "description": "MANDATORY - Source of truth for matching"
          },
          "to_coords": {
            "type": "object",
            "properties": {
              "lat": { "type": "number" },
              "lng": { "type": "number" }
            },
            "required": ["lat", "lng"],
            "description": "MANDATORY - Source of truth for matching"
          },
          "from_address": { "type": "string", "description": "OPTIONAL" },
          "to_address": { "type": "string", "description": "OPTIONAL" },
          "distance_km": { "type": "number" },
          "typical_days": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            }
          },
          "is_round_trip": { "type": "boolean" }
        },
        "required": ["id", "name", "from_coords", "to_coords"]
      }
    },
    "geo_routes": {
      "type": "array",
      "description": "OPTIONAL: Pre-calculated routes from geo-routing server",
      "items": {
        "type": "object",
        "properties": {
          "distance_km": { "type": "number" },
          "duration_hours": { "type": "number" },
          "via": { "type": "string" }
        }
      }
    }
  },
  "required": ["gap_data", "templates"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "matched_templates": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "template_id": { "type": "string", "format": "uuid" },
          "template_name": { "type": "string" },
          "confidence_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "description": "Overall confidence (0-100)"
          },
          "confidence_breakdown": {
            "type": "object",
            "properties": {
              "gps_match": {
                "type": "object",
                "properties": {
                  "start_distance_meters": { "type": "number" },
                  "end_distance_meters": { "type": "number" },
                  "start_score": { "type": "number", "minimum": 0, "maximum": 100 },
                  "end_score": { "type": "number", "minimum": 0, "maximum": 100 },
                  "combined_score": { "type": "number", "minimum": 0, "maximum": 100 },
                  "weight": { "type": "number", "enum": [0.7] }
                }
              },
              "address_match": {
                "type": "object",
                "properties": {
                  "start_similarity": { "type": "number", "minimum": 0, "maximum": 1 },
                  "end_similarity": { "type": "number", "minimum": 0, "maximum": 1 },
                  "start_score": { "type": "number", "minimum": 0, "maximum": 100 },
                  "end_score": { "type": "number", "minimum": 0, "maximum": 100 },
                  "combined_score": { "type": "number", "minimum": 0, "maximum": 100 },
                  "weight": { "type": "number", "enum": [0.3] }
                }
              },
              "distance_match": {
                "type": "object",
                "properties": {
                  "template_distance_km": { "type": "number" },
                  "gap_distance_km": { "type": "number" },
                  "difference_km": { "type": "number" },
                  "difference_percentage": { "type": "number" },
                  "score": { "type": "number", "minimum": 0, "maximum": 100 }
                }
              },
              "day_match": {
                "type": "object",
                "properties": {
                  "template_days": { "type": "array" },
                  "gap_day": { "type": "string" },
                  "matches": { "type": "boolean" },
                  "score": { "type": "number", "enum": [0, 50, 100] }
                }
              }
            }
          },
          "suggested_count": { "type": "integer", "minimum": 0 },
          "total_km": { "type": "number" },
          "missing_optional_fields": { "type": "array", "items": { "type": "string" } },
          "completeness_percentage": { "type": "number", "minimum": 0, "maximum": 100 }
        }
      }
    },
    "reconstruction_proposal": {
      "type": "object",
      "properties": {
        "proposed_trips": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "template_id": { "type": "string", "format": "uuid" },
              "template_name": { "type": "string" },
              "count": { "type": "integer", "minimum": 1 },
              "distance_km_per_trip": { "type": "number" },
              "total_km": { "type": "number" }
            }
          }
        },
        "remainder_km": { "type": "number" },
        "remainder_percentage": { "type": "number" },
        "total_confidence": { "type": "number", "minimum": 0, "maximum": 100 },
        "coverage_percentage": { "type": "number", "minimum": 0, "maximum": 100 }
      }
    },
    "suggestions": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Human-readable improvement tips"
    }
  }
}
```

---

### Tool 2.2: `calculate_template_completeness`

Calculate how complete a template is (useful for UI display).

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "template": {
      "type": "object",
      "properties": {
        "id": { "type": "string", "format": "uuid" },
        "name": { "type": "string" },
        "from_coords": { "type": "object" },
        "to_coords": { "type": "object" },
        "from_address": { "type": "string" },
        "to_address": { "type": "string" },
        "distance_km": { "type": "number" },
        "typical_days": { "type": "array" },
        "is_round_trip": { "type": "boolean" },
        "purpose": { "type": "string" },
        "business_description": { "type": "string" }
      },
      "required": ["id", "name", "from_coords", "to_coords"]
    }
  },
  "required": ["template"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "completeness_percentage": { "type": "number", "minimum": 0, "maximum": 100 },
    "mandatory_fields": {
      "type": "object",
      "properties": {
        "filled": { "type": "array", "items": { "type": "string" } },
        "missing": { "type": "array", "items": { "type": "string" } }
      }
    },
    "optional_fields": {
      "type": "object",
      "properties": {
        "filled": { "type": "array", "items": { "type": "string" } },
        "missing": { "type": "array", "items": { "type": "string" } },
        "impact_on_matching": {
          "type": "object",
          "additionalProperties": {
            "type": "string",
            "enum": ["HIGH", "MEDIUM", "LOW"]
          }
        }
      }
    },
    "suggestions": { "type": "array", "items": { "type": "string" } }
  }
}
```

---

## Server 3: geo-routing (3 tools)

**Purpose:** Geocoding + route calculation via OpenStreetMap
**Language:** Node.js
**Dependencies:** OSRM, Nominatim

---

### Tool 3.1: `geocode_address`

Convert address text to GPS coordinates with ambiguity handling.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "address": { "type": "string", "minLength": 1 },
    "country_hint": {
      "type": "string",
      "description": "ISO country code (e.g., SK, CZ, DE) - improves accuracy"
    }
  },
  "required": ["address"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "coordinates": {
      "type": "object",
      "properties": {
        "latitude": { "type": "number" },
        "longitude": { "type": "number" }
      }
    },
    "normalized_address": { "type": "string", "description": "Cleaned up version" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "alternatives": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "address": { "type": "string" },
          "coordinates": {
            "type": "object",
            "properties": {
              "lat": { "type": "number" },
              "lng": { "type": "number" }
            }
          },
          "confidence": { "type": "number" },
          "type": { "type": "string", "enum": ["street", "city", "poi", "region", "district"] }
        }
      },
      "description": "Returned when confidence < 0.7 (ambiguous address)"
    },
    "error": { "type": "string" }
  }
}
```

**Example Request (clear address):**
```json
{
  "address": "Hlavná 45, Bratislava",
  "country_hint": "SK"
}
```

**Example Response (clear address):**
```json
{
  "success": true,
  "coordinates": {
    "latitude": 48.1486,
    "longitude": 17.1077
  },
  "normalized_address": "Hlavná 45, 811 01 Bratislava, Slovakia",
  "confidence": 0.98,
  "alternatives": []
}
```

**Example Request (ambiguous address):**
```json
{
  "address": "Košice"
}
```

**Example Response (ambiguous address):**
```json
{
  "success": true,
  "coordinates": {
    "latitude": 48.7164,
    "longitude": 21.2611
  },
  "normalized_address": "Košice, Slovakia",
  "confidence": 0.65,
  "alternatives": [
    {
      "address": "Košice city center",
      "coordinates": { "lat": 48.7178, "lng": 21.2575 },
      "confidence": 0.65,
      "type": "city"
    },
    {
      "address": "Košice-Západ (west district)",
      "coordinates": { "lat": 48.6900, "lng": 21.1900 },
      "confidence": 0.55,
      "type": "district"
    },
    {
      "address": "Košice-Sever (north district)",
      "coordinates": { "lat": 48.7400, "lng": 21.2500 },
      "confidence": 0.50,
      "type": "district"
    }
  ]
}
```

---

### Tool 3.2: `reverse_geocode`

Convert GPS coordinates to human-readable address.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "latitude": { "type": "number", "minimum": -90, "maximum": 90 },
    "longitude": { "type": "number", "minimum": -180, "maximum": 180 }
  },
  "required": ["latitude", "longitude"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "address": {
      "type": "object",
      "properties": {
        "street": { "type": "string" },
        "house_number": { "type": "string" },
        "city": { "type": "string" },
        "postal_code": { "type": "string" },
        "country": { "type": "string" },
        "formatted": { "type": "string" }
      },
      "required": ["city", "country", "formatted"]
    },
    "poi": { "type": "string", "description": "Point of interest (e.g., 'Shell Bratislava West')" }
  }
}
```

---

### Tool 3.3: `calculate_route`

Calculate route(s) between two GPS coordinates.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "from_coords": {
      "type": "object",
      "properties": {
        "lat": { "type": "number" },
        "lng": { "type": "number" }
      },
      "required": ["lat", "lng"]
    },
    "to_coords": {
      "type": "object",
      "properties": {
        "lat": { "type": "number" },
        "lng": { "type": "number" }
      },
      "required": ["lat", "lng"]
    },
    "alternatives": {
      "type": "integer",
      "minimum": 1,
      "maximum": 3,
      "default": 1,
      "description": "Number of alternative routes"
    },
    "vehicle": {
      "type": "string",
      "enum": ["car", "truck"],
      "default": "car"
    }
  },
  "required": ["from_coords", "to_coords"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "routes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "distance_km": { "type": "number" },
          "duration_hours": { "type": "number" },
          "via": { "type": "string", "description": "Summary (e.g., 'via D1 highway')" },
          "waypoints": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": { "type": "string" },
                "latitude": { "type": "number" },
                "longitude": { "type": "number" }
              }
            }
          },
          "route_type": {
            "type": "string",
            "enum": ["highway", "local", "mixed"]
          }
        }
      }
    }
  }
}
```

---

## Server 4: ekasa-api (2 tools)

**Purpose:** Receipt processing for Slovak e-Kasa system
**Language:** Python
**Timeout:** 60 seconds (e-Kasa API can take 5-30s)
**Authentication:** None required (public API)

---

### Tool 4.1: `scan_qr_code`

Extract QR code from receipt image or PDF.

**Supports:** PNG, JPG, JPEG images and PDF documents with multi-scale detection.

**Implementation Notes:**
- For PDFs: Uses multi-scale detection (1x, 2x, 3x zoom) to find small or low-resolution QR codes
- Stops on first successful detection
- Returns scale level where QR was detected for debugging

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "image_path": {
      "type": "string",
      "description": "Absolute path to receipt image or PDF file"
    }
  },
  "required": ["image_path"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "receipt_id": { "type": "string", "description": "Extracted e-Kasa receipt ID" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "detection_scale": { "type": "number", "description": "Scale at which QR was detected (1, 2, or 3)" },
    "format": { "type": "string", "enum": ["image", "pdf"], "description": "Source file format" },
    "error": { "type": "string" }
  }
}
```

---

### Tool 4.2: `fetch_receipt_data`

Fetch receipt data from e-Kasa API.

**Important Implementation Notes:**
- **Endpoint:** `https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/{receipt_id}` (Financial Administration of Slovak Republic)
- **Authentication:** None required (public endpoint)
- **Response Time:** Typically 5-30 seconds, can be slower
- **Timeout:** 60 seconds (configured at MCP server level)
- **Retry Strategy:** Single retry for transient failures (optional)
- **Fuel Detection:** Must detect fuel items by name matching Slovak patterns (Diesel, Nafta, Natural 95, etc.)

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "receipt_id": { "type": "string", "minLength": 1 },
    "timeout_seconds": {
      "type": "number",
      "default": 60,
      "maximum": 60,
      "description": "Override default timeout (max 60s)"
    }
  },
  "required": ["receipt_id"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "receipt_data": {
      "type": "object",
      "properties": {
        "receipt_id": { "type": "string" },
        "vendor_name": { "type": "string" },
        "vendor_tax_id": { "type": "string" },
        "timestamp": { "type": "string", "format": "date-time" },
        "total_amount_eur": { "type": "number" },
        "vat_amount_eur": { "type": "number" },
        "items": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "description": { "type": "string" },
              "quantity": { "type": "number" },
              "unit_price_eur": { "type": "number" },
              "total_price_eur": { "type": "number" },
              "vat_rate": { "type": "number" },
              "is_fuel": { "type": "boolean", "description": "Auto-detected" },
              "fuel_type": { "type": "string", "enum": ["Diesel", "Gasoline_95", "Gasoline_98", "LPG", "CNG"] }
            }
          }
        }
      }
    },
    "fuel_items": {
      "type": "array",
      "description": "Filtered fuel items only",
      "items": { "type": "object" }
    },
    "error": { "type": "string" }
  }
}
```

---

### ~~Tool 4.3 & 4.4: Queue System (DEPRECATED)~~

**Status:** REMOVED in favor of extended MCP server timeout (60s)

**Rationale:**
- The e-Kasa API responds within 5-30 seconds, which is well within the 60-second timeout supported by Claude Desktop MCP servers
- Direct synchronous calls are simpler and more reliable than async queue systems
- No need for job queue, polling, or status tracking
- Simplifies implementation and reduces potential error states

**Original Tools Removed:**
- `queue_receipt` - Add receipt to processing queue
- `get_queue_status` - Check processing queue status

**Migration Path:**
- Use `fetch_receipt_data` directly with 60s timeout
- MCP server handles timeout at the protocol level
- User sees "thinking" indicator while request processes

---

## Server 5: dashboard-ocr (3 tools)

**Purpose:** Dashboard photo OCR + EXIF extraction
**Language:** Python
**Dependencies:** Claude Vision API, PIL/Pillow

---

### Tool 5.1: `read_odometer`

Extract odometer reading from dashboard photo using Claude Vision.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "photo_path": { "type": "string", "description": "Absolute path to dashboard photo" }
  },
  "required": ["photo_path"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "odometer_km": { "type": "integer", "minimum": 0 },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "quality_assessment": {
      "type": "object",
      "properties": {
        "brightness": { "type": "string", "enum": ["too_dark", "too_bright", "ok"] },
        "blur": { "type": "string", "enum": ["blurry", "ok"] },
        "resolution": { "type": "string", "enum": ["too_low", "ok"] }
      }
    },
    "error": { "type": "string" }
  }
}
```

---

### Tool 5.2: `extract_metadata`

Extract EXIF metadata from photo (GPS, timestamp).

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "photo_path": { "type": "string" }
  },
  "required": ["photo_path"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "timestamp": { "type": "string", "format": "date-time" },
    "gps_coords": {
      "type": "object",
      "properties": {
        "lat": { "type": "number" },
        "lng": { "type": "number" }
      }
    },
    "camera_model": { "type": "string" },
    "error": { "type": "string" }
  }
}
```

---

### Tool 5.3: `check_photo_quality`

Validate photo quality before OCR.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "photo_path": { "type": "string" }
  },
  "required": ["photo_path"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "is_acceptable": { "type": "boolean" },
    "issues": {
      "type": "array",
      "items": { "type": "string" }
    },
    "suggestions": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

---

## Server 6: validation (4 tools)

**Purpose:** Data validation algorithms with thresholds
**Language:** Python

---

### Tool 6.1: `validate_checkpoint_pair`

Validate gap between two checkpoints.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "start_checkpoint_id": { "type": "string", "format": "uuid" },
    "end_checkpoint_id": { "type": "string", "format": "uuid" }
  },
  "required": ["start_checkpoint_id", "end_checkpoint_id"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "status": { "type": "string", "enum": ["ok", "warning", "error"] },
    "distance_km": { "type": "number" },
    "days": { "type": "number" },
    "km_per_day": { "type": "number" },
    "warnings": { "type": "array", "items": { "type": "string" } },
    "errors": { "type": "array", "items": { "type": "string" } }
  }
}
```

---

### Tool 6.2: `validate_trip`

Validate single trip entry.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "trip": {
      "type": "object",
      "description": "Complete trip object"
    }
  },
  "required": ["trip"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "status": { "type": "string", "enum": ["validated", "has_warnings", "has_errors"] },
    "distance_check": { "type": "string", "enum": ["ok", "warning", "error"] },
    "efficiency_check": { "type": "string", "enum": ["ok", "warning", "error"] },
    "deviation_check": { "type": "string", "enum": ["ok", "warning", "error"] },
    "warnings": { "type": "array", "items": { "type": "string" } },
    "errors": { "type": "array", "items": { "type": "string" } }
  }
}
```

---

### Tool 6.3: `check_efficiency`

Check fuel efficiency reasonability.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "efficiency_l_per_100km": { "type": "number" },
    "fuel_type": { "type": "string", "enum": ["Diesel", "Gasoline", "LPG", "Hybrid", "Electric"] }
  },
  "required": ["efficiency_l_per_100km", "fuel_type"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "status": { "type": "string", "enum": ["ok", "warning", "error"] },
    "efficiency": { "type": "number" },
    "expected_range": {
      "type": "object",
      "properties": {
        "min": { "type": "number" },
        "max": { "type": "number" }
      }
    },
    "message": { "type": "string" }
  }
}
```

---

### Tool 6.4: `check_deviation_from_average`

Compare trip efficiency to vehicle average.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "trip_efficiency_l_per_100km": { "type": "number" },
    "vehicle_avg_efficiency_l_per_100km": { "type": "number" }
  },
  "required": ["trip_efficiency_l_per_100km", "vehicle_avg_efficiency_l_per_100km"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "status": { "type": "string", "enum": ["ok", "warning"] },
    "deviation_percent": { "type": "number" },
    "message": { "type": "string" },
    "suggestion": { "type": "string" }
  }
}
```

---

## Server 7: report-generator (2 tools - P1)

**Purpose:** PDF/CSV generation for tax reports
**Language:** Python
**Dependencies:** ReportLab (PDF), csv module

---

### Tool 7.1: `generate_pdf`

Create Slovak VAT-compliant PDF report.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "trips": { "type": "array", "items": { "type": "object" } },
    "metadata": {
      "type": "object",
      "properties": {
        "vehicle": { "type": "object" },
        "period_start": { "type": "string", "format": "date" },
        "period_end": { "type": "string", "format": "date" },
        "company_name": { "type": "string" },
        "company_tax_id": { "type": "string" }
      }
    },
    "template": { "type": "string", "enum": ["standard", "detailed"], "default": "standard" }
  },
  "required": ["trips", "metadata"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "pdf_path": { "type": "string" },
    "summary": {
      "type": "object",
      "properties": {
        "total_trips": { "type": "integer" },
        "total_distance_km": { "type": "number" },
        "total_fuel_liters": { "type": "number" },
        "total_cost_eur": { "type": "number" },
        "vat_deductible_eur": { "type": "number" }
      }
    }
  }
}
```

---

### Tool 7.2: `generate_csv`

Create CSV export for accounting software.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "trips": { "type": "array" },
    "metadata": { "type": "object" }
  },
  "required": ["trips"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "csv_path": { "type": "string" },
    "row_count": { "type": "integer" }
  }
}
```

---

## Error Response Patterns

All MCP tools follow consistent error response format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "field": "field_name",
    "details": "Additional context"
  }
}
```

**Common Error Codes:**
- `VALIDATION_ERROR` - Input validation failed
- `NOT_FOUND` - Resource doesn't exist
- `DUPLICATE` - Resource already exists
- `GPS_REQUIRED` - Operation needs GPS coordinates
- `GEOCODING_FAILED` - Address could not be resolved
- `AMBIGUOUS_ADDRESS` - Multiple matches found (return alternatives)
- `RATE_LIMIT` - Too many requests
- `EXTERNAL_API_ERROR` - Third-party service failed (e-Kasa, OSRM)
- `TIMEOUT_ERROR` - Request exceeded 60s timeout (e-Kasa API)
- `QR_DETECTION_FAILED` - QR code not found in image/PDF (try multi-scale)
- `FILE_NOT_FOUND` - File doesn't exist
- `FILE_CORRUPT` - JSON file is corrupted
- `ATOMIC_WRITE_FAILED` - Atomic write operation failed

---

## Related Documents

- [02-domain-model.md](./02-domain-model.md) - Core concepts
- [03-trip-reconstruction.md](./03-trip-reconstruction.md) - Algorithms
- [04-data-model.md](./04-data-model.md) - JSON schemas
- [06-mcp-architecture-v2.md](./06-mcp-architecture-v2.md) - Server architecture
- [08-implementation-plan.md](./08-implementation-plan.md) - Build timeline

---

**Document Status:** Complete - Ready for Implementation
**Last Updated:** 2025-11-18
**Total API Surface:** 24 tools across 7 servers (queue system removed)
