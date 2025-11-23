# Checkpoint from Receipt MCP Tools Reference

## ekasa-api.scan_qr_code

**Purpose:** Scan QR code from receipt image with multi-scale detection

**Request:**
```json
{
  "image_path": "/path/to/receipt.jpg",
  "image_data": "base64_encoded_image"
}
```

**Response (Success):**
```json
{
  "success": true,
  "receipt_id": "O-123456789ABC",
  "detection_scale": 2.0,
  "confidence": 0.98
}
```

**Response (Not Found):**
```json
{
  "success": false,
  "error": {
    "code": "QR_NOT_FOUND",
    "message": "QR code not detected at any scale",
    "details": "Tried scales: 1.0x, 2.0x, 3.0x"
  }
}
```

**Implementation Details:**
- **Multi-scale detection:** Tries 1x, 2x, 3x scales
- **Stops on first success:** Doesn't process all scales
- **Works with:** JPG, PNG, PDF files
- **PDF handling:** Checks first page only by default

---

## ekasa-api.fetch_receipt_data

**Purpose:** Fetch receipt from Slovak e-Kasa API (5-30s typically, 60s timeout)

**Endpoint:** `https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/{receipt_id}`

**Request:**
```json
{
  "receipt_id": "O-123456789ABC"
}
```

**Response (Success):**
```json
{
  "success": true,
  "receipt": {
    "receipt_id": "O-123456789ABC",
    "vendor_name": "OMV Tankstelle",
    "vendor_address": "Hlavná 45, 81101 Bratislava",
    "items": [
      {
        "name": "Diesel",
        "quantity": 52.3,
        "unit": "L",
        "price_per_unit": 1.45,
        "total_excl_vat": 63.64,
        "total_incl_vat": 75.84,
        "vat_rate": 0.20
      }
    ],
    "total_excl_vat": 63.64,
    "total_incl_vat": 75.84,
    "timestamp": "2025-11-01T14:30:00Z",
    "payment_method": "card"
  }
}
```

**Response (Timeout):**
```json
{
  "success": false,
  "error": {
    "code": "TIMEOUT",
    "message": "e-Kasa API timeout after 60s",
    "details": "Retry or enter data manually"
  }
}
```

**Response (Invalid Receipt ID):**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Receipt not found in e-Kasa system",
    "details": "Verify receipt ID or check if receipt is registered"
  }
}
```

**Timing:**
- **Typical:** 5-30 seconds
- **Maximum:** 60 seconds (timeout)
- **Progress updates:** Show at 15s, 30s, 45s

**Fuel Detection Patterns (Slovak):**
```
Diesel:      "diesel", "nafta", "motorová nafta"
Gasoline 95: "natural 95", "ba 95", "benzín 95"
Gasoline 98: "natural 98", "ba 98", "benzín 98"
LPG:         "lpg", "autoplyn"
CNG:         "cng", "zemný plyn"
```

---

## dashboard-ocr.extract_metadata

**Purpose:** Extract GPS and odometer from dashboard photo

**Request:**
```json
{
  "image_path": "/path/to/dashboard.jpg",
  "image_data": "base64_encoded_image"
}
```

**Response (Success - with GPS):**
```json
{
  "success": true,
  "gps": {
    "latitude": 48.1486,
    "longitude": 17.1077,
    "source": "exif",
    "accuracy_meters": 10
  },
  "timestamp": "2025-11-01T14:35:00Z",
  "odometer_reading": 125340,
  "odometer_confidence": 0.92
}
```

**Response (Success - no GPS):**
```json
{
  "success": true,
  "gps": null,
  "timestamp": "2025-11-01T14:35:00Z",
  "odometer_reading": 125340,
  "odometer_confidence": 0.92,
  "warning": "No GPS data in EXIF. Enable location services."
}
```

**Response (Low OCR Confidence):**
```json
{
  "success": true,
  "gps": {
    "latitude": 48.1486,
    "longitude": 17.1077,
    "source": "exif"
  },
  "timestamp": "2025-11-01T14:35:00Z",
  "odometer_reading": null,
  "odometer_confidence": 0.45,
  "warning": "OCR confidence too low. Manual entry recommended."
}
```

**EXIF Data Sources:**
- GPS: Standard EXIF GPS tags
- Timestamp: EXIF DateTimeOriginal
- Camera: Make, Model (for debugging)

**OCR Confidence Thresholds:**
- **> 80%:** Auto-accept with confirmation
- **50-80%:** Show value, ask for verification
- **< 50%:** Skip OCR, ask for manual entry

---

## car-log-core.create_checkpoint

**Purpose:** Create checkpoint with receipt + GPS data

**Request:**
```json
{
  "vehicle_id": "uuid-1234",
  "checkpoint_type": "refuel",
  "datetime": "2025-11-01T14:30:00Z",
  "odometer_km": 125340,
  "location": {
    "coords": {
      "latitude": 48.1486,
      "longitude": 17.1077
    },
    "address": "OMV Station, Hlavná 45, Bratislava",
    "source": "exif"
  },
  "receipt": {
    "receipt_id": "O-123456789ABC",
    "vendor_name": "OMV Tankstelle",
    "fuel_type": "Diesel",
    "fuel_liters": 52.3,
    "price_excl_vat": 63.64,
    "price_incl_vat": 75.84,
    "vat_rate": 0.20
  },
  "driver_name": "Ján Novák"
}
```

**Response (Success):**
```json
{
  "success": true,
  "checkpoint": {
    "checkpoint_id": "uuid-5678",
    "vehicle_id": "uuid-1234",
    "checkpoint_type": "refuel",
    "datetime": "2025-11-01T14:30:00Z",
    "odometer_km": 125340,
    "created_at": "2025-11-20T10:45:00Z"
  }
}
```

**Response (Validation Error):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Odometer reading decreased",
    "field": "odometer_km",
    "details": "Previous: 125500 km, Current: 125340 km"
  }
}
```

---

## car-log-core.update_checkpoint

**Purpose:** Update checkpoint to fix mistakes (odometer, GPS, driver name, fuel amount)

**Request:**
```json
{
  "checkpoint_id": "uuid-5678",
  "updates": {
    "odometer_km": 125500,
    "location_coords": {
      "lat": 48.1500,
      "lng": 17.1100
    },
    "fuel_liters": 53.0
  }
}
```

**Response (Success):**
```json
{
  "success": true,
  "checkpoint_id": "uuid-5678",
  "checkpoint": {
    "checkpoint_id": "uuid-5678",
    "vehicle_id": "uuid-1234",
    "checkpoint_type": "refuel",
    "datetime": "2025-11-01T14:30:00Z",
    "odometer_km": 125500,
    "updated_at": "2025-11-23T15:00:00Z"
  },
  "updated_fields": ["odometer_km", "location.coords", "receipt.fuel_liters"],
  "message": "Checkpoint updated successfully"
}
```

**Response (Validation Error - Odometer Decreased):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Odometer cannot decrease (previous: 125500 km, new: 125400 km)",
    "field": "odometer_km"
  }
}
```

**Features:**
- **Partial updates:** Only specified fields are changed
- **Odometer validation:** Cannot decrease relative to previous checkpoint
- **Auto-recalculation:** Updates distance_since_previous_km
- **Vehicle sync:** Updates vehicle's current odometer if this is most recent checkpoint

**Use Cases:**
- Fix typo in odometer reading
- Correct GPS coordinates from bad EXIF data
- Update fuel amount after receipt correction
- Change driver name if initially recorded incorrectly

---

## car-log-core.delete_checkpoint

**Purpose:** Delete checkpoint (remove duplicate or erroneous entry)

**Request:**
```json
{
  "checkpoint_id": "uuid-5678",
  "cascade": false
}
```

**Response (Success):**
```json
{
  "success": true,
  "checkpoint_id": "uuid-5678",
  "message": "Checkpoint deleted successfully"
}
```

**Response (Dependency Error):**
```json
{
  "success": false,
  "error": {
    "code": "DEPENDENCY_ERROR",
    "message": "2 trip(s) reference this checkpoint. Set cascade=true to delete them, or delete trips manually first.",
    "dependent_trips": ["uuid-trip-1", "uuid-trip-2"]
  }
}
```

**Response (Cascade Delete):**
```json
{
  "success": true,
  "checkpoint_id": "uuid-5678",
  "warnings": ["Cascade deleted 2 dependent trip(s)"],
  "message": "Checkpoint deleted successfully"
}
```

**Cascade Behavior:**
- **cascade=false (default):** Blocks deletion if trips reference this checkpoint
- **cascade=true:** Deletes checkpoint and all dependent trips
- **Warnings:** Always shows count of affected trips

**Use Cases:**
- Remove duplicate checkpoint (created twice by mistake)
- Delete checkpoint with wrong date (created in wrong month)
- Clean up test data
- Remove checkpoint after realizing it was entered for wrong vehicle

**Safety Features:**
- Dependency checking before deletion
- Clear warnings about affected data
- Requires explicit cascade=true for force delete

---

## car-log-core.detect_gap

**Purpose:** Detect gaps between checkpoints for trip reconstruction

**Request:**
```json
{
  "vehicle_id": "uuid-1234",
  "checkpoint_id": "uuid-5678"
}
```

**Response (Gap Detected):**
```json
{
  "success": true,
  "gap_detected": true,
  "gap": {
    "start_checkpoint_id": "uuid-4567",
    "end_checkpoint_id": "uuid-5678",
    "distance_km": 820,
    "duration_days": 7,
    "start_odometer": 124520,
    "end_odometer": 125340,
    "start_datetime": "2025-10-25T14:30:00Z",
    "end_datetime": "2025-11-01T14:30:00Z"
  }
}
```

**Response (No Gap):**
```json
{
  "success": true,
  "gap_detected": false,
  "message": "No gap detected. Previous checkpoint within threshold."
}
```

**Gap Detection Thresholds:**
- **Distance:** > 100 km between checkpoints
- **Time:** > 1 day between checkpoints
- **Both conditions:** Must meet distance OR time threshold

---

## geo-routing.geocode_address

**Purpose:** Convert address to GPS coordinates (fallback when no EXIF GPS)

**Request:**
```json
{
  "address": "OMV, Hlavná 45, Bratislava",
  "country_hint": "SK"
}
```

**Response (Success):**
```json
{
  "success": true,
  "coordinates": {
    "latitude": 48.1486,
    "longitude": 17.1077
  },
  "address": "Hlavná 45, 81101 Bratislava, Slovakia",
  "confidence": 0.95,
  "source": "nominatim"
}
```

**Response (Ambiguous):**
```json
{
  "success": true,
  "coordinates": {
    "latitude": 48.7164,
    "longitude": 21.2611
  },
  "address": "Košice, Slovakia",
  "confidence": 0.65,
  "alternatives": [
    {
      "address": "Košice City Center, Slovakia",
      "coordinates": {"latitude": 48.7164, "longitude": 21.2611},
      "type": "city_center"
    },
    {
      "address": "Košice Airport, Slovakia",
      "coordinates": {"latitude": 48.6631, "longitude": 21.2411},
      "type": "airport"
    }
  ]
}
```

---

## Slovak Compliance Notes

### Mandatory Fields
- **driver_name:** Required for tax deduction
- **refuel_datetime:** Separate from trip start/end
- **refuel_location:** May differ from trip endpoints

### Timing Separation
```
Trip Start: 2025-11-01T08:00:00Z (leaving office)
Refuel: 2025-11-01T08:15:00Z (gas station)
Trip End: 2025-11-01T10:30:00Z (arriving warehouse)
```

**Critical:** Store refuel timing separately from trip timing.

### L/100km Format
- Always use European format: **L/100km**
- Never use American format: km/L
- Example: "8.5 L/100km" (not "11.8 km/L")

---

**For complete API specification:** See ../../spec/07-mcp-api-specifications.md
**For implementation examples:** See GUIDE.md
**For e-Kasa implementation details:** See ../../spec/EKASA_IMPLEMENTATION_GUIDE.md
