# Trip Reconstruction - MCP Tool Reference

Complete reference for all MCP tools used in trip reconstruction workflow.

---

## 1. car-log-core.analyze_gap

**Purpose:** Analyze the gap between two checkpoints to prepare for trip reconstruction.

**Request:**
```json
{
  "checkpoint1_id": "chk-456-abc-789",
  "checkpoint2_id": "chk-789-xyz-012"
}
```

**Response:**
```json
{
  "success": true,
  "gap": {
    "start_checkpoint": {
      "checkpoint_id": "chk-456-abc-789",
      "datetime": "2025-11-01T08:00:00Z",
      "odometer_km": 45000,
      "location": {
        "coords": {"latitude": 48.1486, "longitude": 17.1077},
        "address": "OMV Station, Bratislava"
      }
    },
    "end_checkpoint": {
      "checkpoint_id": "chk-789-xyz-012",
      "datetime": "2025-11-08T14:25:00Z",
      "odometer_km": 45820,
      "location": {
        "coords": {"latitude": 48.7164, "longitude": 21.2611},
        "address": "Shell Station, Košice"
      }
    },
    "distance_km": 820,
    "duration_days": 7,
    "vehicle_id": "abc-123-def-456"
  }
}
```

**Key Fields:**
- `distance_km`: Odometer delta (end - start)
- `duration_days`: Time elapsed between checkpoints
- `location.coords`: GPS coordinates (REQUIRED for high-confidence matching)
- `location.address`: Human-readable label (optional, 30% matching weight)

---

## 2. car-log-core.list_templates

**Purpose:** Fetch all saved route templates for a vehicle to match against gap data.

**Request:**
```json
{
  "vehicle_id": "abc-123-def-456"
}
```

**Response:**
```json
{
  "success": true,
  "templates": [
    {
      "template_id": "tpl-123-warehouse",
      "name": "Warehouse Run",
      "from_coords": {"lat": 48.1486, "lng": 17.1077},
      "from_address": "Bratislava Office",
      "from_label": "Bratislava",
      "to_coords": {"lat": 48.7164, "lng": 21.2611},
      "to_address": "Košice Warehouse",
      "to_label": "Košice",
      "distance_km": 410,
      "is_round_trip": true,
      "typical_days": ["Monday", "Thursday"],
      "purpose": "business",
      "business_description": "Weekly warehouse pickup and delivery"
    },
    {
      "template_id": "tpl-456-commute",
      "name": "Daily Commute",
      "from_coords": {"lat": 48.1500, "lng": 17.1100},
      "to_coords": {"lat": 48.1600, "lng": 17.1200},
      "distance_km": 25,
      "is_round_trip": false,
      "typical_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "purpose": "business"
    }
  ],
  "count": 2
}
```

**Key Fields:**
- `from_coords` / `to_coords`: GPS coordinates (MANDATORY for 70% matching weight)
- `from_address` / `to_address`: Optional labels (30% matching weight)
- `typical_days`: Day-of-week patterns (+5% confidence bonus if matched)
- `is_round_trip`: If true, creates two trips (outbound + return)
- `purpose`: "business" or "personal" (inherited by matched trips)

---

## 3. trip-reconstructor.match_templates

**Purpose:** Run GPS-first hybrid matching algorithm against templates. This is a STATELESS operation - all data must be provided in request.

**Request:**
```json
{
  "gap_data": {
    "start_coords": {"latitude": 48.1486, "longitude": 17.1077},
    "end_coords": {"latitude": 48.7164, "longitude": 21.2611},
    "start_address": "Bratislava",
    "end_address": "Košice",
    "distance_km": 820,
    "start_datetime": "2025-11-01T08:00:00Z",
    "end_datetime": "2025-11-08T14:25:00Z"
  },
  "templates": [
    {
      "template_id": "tpl-123-warehouse",
      "name": "Warehouse Run",
      "from_coords": {"lat": 48.1486, "lng": 17.1077},
      "to_coords": {"lat": 48.7164, "lng": 21.2611},
      "from_address": "Bratislava Office",
      "to_address": "Košice Warehouse",
      "distance_km": 410,
      "is_round_trip": true,
      "typical_days": ["Monday", "Thursday"],
      "purpose": "business",
      "business_description": "Warehouse pickup"
    }
  ],
  "gps_weight": 0.7,
  "address_weight": 0.3,
  "min_confidence": 0.7
}
```

**Response:**
```json
{
  "success": true,
  "proposals": [
    {
      "template_id": "tpl-123-warehouse",
      "template_name": "Warehouse Run",
      "confidence": 92,
      "matching_mode": "MODE_B_HYBRID",
      "gps_score": 98,
      "address_score": 75,
      "bonuses": {
        "day_match": 5,
        "distance_match": 5
      },
      "trips": [
        {
          "trip_start_location": "Bratislava",
          "trip_end_location": "Košice",
          "distance_km": 410,
          "trip_start_datetime": "2025-11-01T08:00:00Z",
          "trip_end_datetime": "2025-11-01T12:30:00Z",
          "purpose": "business",
          "business_description": "Warehouse pickup"
        },
        {
          "trip_start_location": "Košice",
          "trip_end_location": "Bratislava",
          "distance_km": 410,
          "trip_start_datetime": "2025-11-06T14:00:00Z",
          "trip_end_datetime": "2025-11-06T18:30:00Z",
          "purpose": "business",
          "business_description": "Return from warehouse"
        }
      ],
      "coverage_km": 820,
      "coverage_percent": 100
    }
  ],
  "best_confidence": 92,
  "match_count": 1
}
```

**Key Fields:**
- `confidence`: Final confidence score (0-100, requires ≥70 for proposals)
- `matching_mode`: "MODE_A_GPS_ONLY", "MODE_B_HYBRID", or "MODE_C_ADDRESS_ONLY"
- `gps_score`: GPS matching score (0-100) based on distance thresholds
- `address_score`: Address similarity score (0-100)
- `bonuses`: Additional confidence points (day_match, distance_match)
- `coverage_percent`: How much of the gap is covered by proposed trips

**GPS Scoring Thresholds:**
- < 100m → 100
- 100-500m → 90
- 500m-2km → 70
- 2-5km → 40
- > 5km → 0

---

## 4. car-log-core.create_trips_batch

**Purpose:** Create multiple trips in a single atomic operation with Slovak compliance validation.

**Request:**
```json
{
  "trips": [
    {
      "vehicle_id": "abc-123-def-456",
      "start_checkpoint_id": "chk-456-abc-789",
      "end_checkpoint_id": "chk-789-xyz-012",
      "driver_name": "Ján Novák",
      "trip_start_datetime": "2025-11-01T08:00:00Z",
      "trip_end_datetime": "2025-11-01T12:30:00Z",
      "trip_start_location": "Bratislava",
      "trip_end_location": "Košice",
      "distance_km": 410,
      "purpose": "Business",
      "business_description": "Warehouse pickup",
      "reconstruction_method": "template",
      "template_id": "tpl-123-warehouse",
      "confidence_score": 92
    },
    {
      "vehicle_id": "abc-123-def-456",
      "start_checkpoint_id": "chk-456-abc-789",
      "end_checkpoint_id": "chk-789-xyz-012",
      "driver_name": "Ján Novák",
      "trip_start_datetime": "2025-11-06T14:00:00Z",
      "trip_end_datetime": "2025-11-06T18:30:00Z",
      "trip_start_location": "Košice",
      "trip_end_location": "Bratislava",
      "distance_km": 410,
      "purpose": "Business",
      "business_description": "Return from warehouse",
      "reconstruction_method": "template",
      "template_id": "tpl-123-warehouse",
      "confidence_score": 92
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "trips_created": 2,
  "trips": [
    {
      "trip_id": "trip-001-abc",
      "vehicle_id": "abc-123-def-456",
      "distance_km": 410,
      "confidence_score": 92,
      "created_at": "2025-11-20T10:30:00Z"
    },
    {
      "trip_id": "trip-002-def",
      "vehicle_id": "abc-123-def-456",
      "distance_km": 410,
      "confidence_score": 92,
      "created_at": "2025-11-20T10:30:00Z"
    }
  ]
}
```

**Required Slovak Compliance Fields:**
- `driver_name`: Full name (MANDATORY for Slovak VAT Act 2025)
- `trip_start_datetime` / `trip_end_datetime`: ISO 8601 format
- `trip_start_location` / `trip_end_location`: Addresses/labels
- `purpose`: "Business" or "Personal"
- `business_description`: Required if purpose is "Business"

---

## 5. validation.validate_checkpoint_pair

**Purpose:** Validate that trip distances sum correctly between two checkpoints (±10% threshold).

**Request:**
```json
{
  "checkpoint1_id": "chk-456-abc-789",
  "checkpoint2_id": "chk-789-xyz-012"
}
```

**Response:**
```json
{
  "success": true,
  "validation": {
    "distance_sum_valid": true,
    "distance_variance_percent": 0,
    "expected_distance_km": 820,
    "actual_distance_km": 820,
    "fuel_consumption_valid": true,
    "fuel_variance_percent": 4.4,
    "expected_fuel_liters": 69.7,
    "actual_fuel_liters": 72.8,
    "efficiency_l_per_100km": 8.9,
    "efficiency_within_range": true,
    "warnings": []
  }
}
```

**Key Fields:**
- `distance_sum_valid`: True if variance ≤ 10%
- `distance_variance_percent`: Percentage difference (expected vs actual)
- `fuel_consumption_valid`: True if variance ≤ 15%
- `efficiency_l_per_100km`: Average fuel efficiency (L/100km format, European standard)
- `warnings`: Array of warning messages if thresholds exceeded

**Validation Thresholds:**
- Distance sum: ±10%
- Fuel consumption: ±15%
- Diesel efficiency: 5-15 L/100km
- Gasoline efficiency: 6-20 L/100km

---

## 6. validation.validate_trip

**Purpose:** Validate a single trip's fuel efficiency and distance reasonableness.

**Request:**
```json
{
  "trip_id": "trip-001-abc"
}
```

**Response:**
```json
{
  "success": true,
  "validation": {
    "trip_id": "trip-001-abc",
    "distance_km": 410,
    "fuel_efficiency_l_per_100km": 8.9,
    "efficiency_valid": true,
    "efficiency_range": {
      "min": 5,
      "max": 15,
      "fuel_type": "Diesel"
    },
    "warnings": []
  }
}
```

**Key Fields:**
- `efficiency_valid`: True if within expected range for fuel type
- `efficiency_range`: Min/max expected efficiency for vehicle's fuel type
- `warnings`: Array of warnings (e.g., "Efficiency 20% above average")

---

## Tool Call Sequence (Happy Path)

```
1. car-log-core.analyze_gap
   ↓ (gap_data)
2. car-log-core.list_templates
   ↓ (templates[])
3. trip-reconstructor.match_templates
   ↓ (proposals[])
4. [User approval]
   ↓
5. car-log-core.create_trips_batch
   ↓ (trip_ids[])
6. validation.validate_checkpoint_pair
   ↓ (validation result)
7. validation.validate_trip (for each trip)
   ↓ (individual validations)
```

**Total MCP Calls:** 6+ (3 data fetch, 1 matching, 1 batch create, 1+ validation)

---

## Error Handling

**Common Error Codes:**
- `GAP_NOT_FOUND`: Checkpoint IDs invalid or no gap exists
- `NO_TEMPLATES`: No templates available for matching
- `GPS_REQUIRED`: Template missing mandatory GPS coordinates
- `VALIDATION_ERROR`: Slovak compliance fields missing (e.g., driver_name)
- `CONFIDENCE_TOO_LOW`: Best match below 70% threshold

**Error Response Format:**
```json
{
  "success": false,
  "error": {
    "code": "GPS_REQUIRED",
    "message": "Template 'tpl-123' missing GPS coordinates",
    "field": "from_coords",
    "details": "GPS coordinates are mandatory for template matching"
  }
}
```

---

## Performance Considerations

**Template Matching:**
- Must complete in <2 seconds with 100+ templates
- Algorithm complexity: O(n * m) where n=templates, m=gap segments
- GPS distance calculation (Haversine): O(1) per comparison

**Batch Trip Creation:**
- Atomic operation (all succeed or all fail)
- File-based storage uses atomic write pattern
- Each trip written to monthly folder: `~/Documents/MileageLog/data/trips/2025-11/`

**Validation:**
- Runs automatically after trip creation (background acceptable)
- Should complete in <1 second for checkpoint pair validation
- Individual trip validation: <100ms per trip
