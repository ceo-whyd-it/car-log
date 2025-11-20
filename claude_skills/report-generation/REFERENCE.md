# Report Generation - MCP Tool Reference

## MCP Tools

### 1. car-log-core.list_trips

**Purpose:** Retrieve trips with filtering for report generation

**Parameters:**
```json
{
  "user_id": "string (UUID)",
  "filters": {
    "date_range": {
      "start_date": "2025-11-01",
      "end_date": "2025-11-30"
    },
    "vehicle_id": "optional string (UUID)",
    "purpose": "Business" | "Personal" | "All"
  }
}
```

**Response:**
```json
{
  "success": true,
  "trips": [
    {
      "trip_id": "uuid",
      "vehicle_id": "uuid",
      "driver_name": "John Smith",
      "trip_start_datetime": "2025-11-01T08:00:00Z",
      "trip_end_datetime": "2025-11-01T14:30:00Z",
      "trip_start_location": "Bratislava",
      "trip_end_location": "Košice",
      "distance_km": 410,
      "fuel_consumption_liters": 34.85,
      "fuel_efficiency_l_per_100km": 8.5,
      "purpose": "Business",
      "business_description": "Warehouse pickup"
    }
  ],
  "total_count": 15
}
```

### 2. report-generator.generate_csv

**Purpose:** Generate Slovak VAT Act 2025 compliant CSV report

**Parameters:**
```json
{
  "trips": [...],
  "vehicle": {
    "license_plate": "BA-789XY",
    "vin": "WVWZZZ3CZDP123456",
    "fuel_type": "Diesel"
  },
  "date_range": {
    "start_date": "2025-11-01",
    "end_date": "2025-11-30"
  },
  "output_path": "~/Documents/MileageLog/reports/"
}
```

**Response:**
```json
{
  "success": true,
  "file_path": "~/Documents/MileageLog/reports/BA-789XY-11-2025.csv",
  "summary": {
    "total_distance_km": 4920,
    "total_fuel_liters": 418.2,
    "total_cost_eur": 627.50,
    "avg_efficiency_l_per_100km": 8.5,
    "trip_count": 15
  },
  "compliance": {
    "vin_present": true,
    "driver_names_complete": true,
    "business_descriptions_complete": true,
    "format_l_per_100km": true,
    "ready_for_tax_deduction": true
  }
}
```

## CSV Format (Slovak VAT Act 2025 Compliant)

### Column Headers

```csv
Date,Vehicle,Trip Start,Trip End,Distance (km),Fuel (L),Efficiency (L/100km),Driver,Purpose,Business Description,VIN
```

### Mandatory Fields

| Field | Slovak Requirement | Validation |
|-------|-------------------|------------|
| VIN | MANDATORY (VAT Act 2025) | 17 chars, no I/O/Q |
| Driver | MANDATORY | Full name |
| Trip Start/End Datetime | MANDATORY | ISO 8601 |
| Trip Start/End Location | MANDATORY | Separate from refuel |
| Business Description | MANDATORY (if Business) | Non-empty |
| Efficiency | MANDATORY | L/100km format |

### Sample Row

```csv
2025-11-01,BA-789XY,Bratislava,Košice,410,34.85,8.5,John Smith,Business,Warehouse pickup,WVWZZZ3CZDP123456
```

## Filter Options

### Date Range Presets

```python
# Month
{
  "start_date": "2025-11-01",
  "end_date": "2025-11-30"
}

# Quarter
{
  "start_date": "2025-10-01",
  "end_date": "2025-12-31"
}

# Year
{
  "start_date": "2025-01-01",
  "end_date": "2025-12-31"
}

# Custom
{
  "start_date": "2025-11-15",
  "end_date": "2025-11-20"
}
```

### Purpose Filters

- **"Business"**: Only business trips (for tax deduction)
- **"Personal"**: Only personal trips (for record-keeping)
- **"All"**: All trips (complete log)

## Compliance Checklist

Before generating report, check:

```python
compliance_checks = {
    "vin_present": vehicle.vin is not None,
    "vin_valid": len(vehicle.vin) == 17 and not any(c in vehicle.vin for c in ['I', 'O', 'Q']),
    "driver_names_complete": all(trip.driver_name for trip in trips),
    "business_descriptions_complete": all(
        trip.business_description if trip.purpose == "Business" else True
        for trip in trips
    ),
    "format_l_per_100km": all(
        "L/100km" in str(trip.fuel_efficiency_l_per_100km)
        for trip in trips
    ),
    "trip_timing_separated": True  # Verified at trip creation
}

ready_for_tax_deduction = all(compliance_checks.values())
```

## Error Handling

### Missing VIN
```json
{
  "success": false,
  "error": {
    "code": "COMPLIANCE_ERROR",
    "message": "VIN required for Slovak VAT Act 2025 compliance",
    "fix": "Use Skill 1 (Vehicle Setup) to add VIN"
  }
}
```

### Incomplete Business Descriptions
```json
{
  "success": false,
  "error": {
    "code": "COMPLIANCE_ERROR",
    "message": "Business descriptions missing for 3 trips",
    "trip_ids": ["uuid1", "uuid2", "uuid3"],
    "fix": "Add business descriptions before generating report"
  }
}
```

## File Location

All reports saved to:
```
~/Documents/MileageLog/reports/
├── BA-789XY-11-2025.csv
├── BA-789XY-12-2025.csv
└── BA-789XY-2025-full.csv
```
