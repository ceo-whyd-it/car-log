# Vehicle Setup MCP Tools Reference

## car-log-core.create_vehicle

**Purpose:** Create a new vehicle for mileage tracking

**Request:**
```json
{
  "name": "Ford Transit Delivery Van",
  "license_plate": "BA-789XY",
  "vin": "WVWZZZ3CZDP123456",
  "fuel_type": "Diesel",
  "make": "Ford",
  "model": "Transit",
  "year": 2022,
  "initial_odometer_km": 125000
}
```

**Response (Success):**
```json
{
  "success": true,
  "vehicle": {
    "vehicle_id": "uuid-1234",
    "name": "Ford Transit Delivery Van",
    "license_plate": "BA-789XY",
    "vin": "WVWZZZ3CZDP123456",
    "fuel_type": "Diesel",
    "make": "Ford",
    "model": "Transit",
    "year": 2022,
    "initial_odometer_km": 125000,
    "created_at": "2025-11-20T10:30:00Z"
  }
}
```

**Response (Error - Invalid VIN):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "VIN must be exactly 17 characters and cannot contain I, O, or Q",
    "field": "vin",
    "details": "Provided VIN contains forbidden character 'O'"
  }
}
```

**Response (Error - Duplicate License Plate):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "License plate already exists",
    "field": "license_plate",
    "details": "Vehicle with plate BA-789XY already registered"
  }
}
```

**Validation Rules:**
- `vin`: Must match `^[A-HJ-NPR-Z0-9]{17}$` (exactly 17 characters, no I/O/Q)
- `license_plate`: Must match `^[A-Z]{2}-[0-9]{3}[A-Z]{2}$` (Slovak format)
- `fuel_type`: One of: Diesel, Gasoline_95, Gasoline_98, LPG, Hybrid, Electric
- `initial_odometer_km`: Must be > 0 and < 1,000,000
- `year`: Optional, must be > 1900 and <= current year

---

## car-log-core.list_vehicles

**Purpose:** List all registered vehicles

**Request:**
```json
{}
```

**Response:**
```json
{
  "success": true,
  "vehicles": [
    {
      "vehicle_id": "uuid-1234",
      "name": "Ford Transit Delivery Van",
      "license_plate": "BA-789XY",
      "vin": "WVWZZZ3CZDP123456",
      "fuel_type": "Diesel",
      "initial_odometer_km": 125000,
      "created_at": "2025-11-20T10:30:00Z"
    },
    {
      "vehicle_id": "uuid-5678",
      "name": "BMW 320d Sedan",
      "license_plate": "KE-456AB",
      "vin": "WBAUE11090E123456",
      "fuel_type": "Diesel",
      "initial_odometer_km": 85000,
      "created_at": "2025-11-15T14:20:00Z"
    }
  ],
  "total_count": 2
}
```

---

## car-log-core.get_vehicle

**Purpose:** Get details for a specific vehicle

**Request:**
```json
{
  "vehicle_id": "uuid-1234"
}
```

**Response:**
```json
{
  "success": true,
  "vehicle": {
    "vehicle_id": "uuid-1234",
    "name": "Ford Transit Delivery Van",
    "license_plate": "BA-789XY",
    "vin": "WVWZZZ3CZDP123456",
    "fuel_type": "Diesel",
    "make": "Ford",
    "model": "Transit",
    "year": 2022,
    "initial_odometer_km": 125000,
    "created_at": "2025-11-20T10:30:00Z"
  }
}
```

**Response (Not Found):**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Vehicle not found",
    "details": "No vehicle with ID uuid-1234"
  }
}
```

---

## Slovak Compliance Notes

### VIN Validation
- **Mandatory** per Slovak VAT Act 2025 for tax deduction eligibility
- Must be exactly 17 characters
- Cannot contain letters I, O, or Q (easily confused with 1 and 0)
- Standard ISO 3779 format

### License Plate Format
- Slovak format: `XX-123XX`
- 2 uppercase letters (region code)
- Hyphen
- 3 digits
- 2 uppercase letters

### Fuel Efficiency
- Always use **L/100km** format (European standard)
- Never use km/L (American/Asian format)
- Typical ranges:
  - Diesel: 5-15 L/100km
  - Gasoline: 6-20 L/100km
  - Hybrid: 3-8 L/100km

---

**For complete API specification:** See ../../spec/07-mcp-api-specifications.md
**For implementation examples:** See GUIDE.md
