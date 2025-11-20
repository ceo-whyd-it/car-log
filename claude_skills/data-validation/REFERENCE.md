# Data Validation - MCP Tool Reference

## MCP Tools

### 1. validation.validate_checkpoint_pair

**Purpose:** Validate distance sum between two checkpoints (±10% threshold)

**Parameters:**
```json
{
  "checkpoint1_id": "string (UUID)",
  "checkpoint2_id": "string (UUID)",
  "trips": [
    {
      "distance_km": 410
    },
    {
      "distance_km": 410
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "validation": {
    "odometer_delta_km": 820,
    "trips_sum_km": 820,
    "variance_percent": 0,
    "threshold_percent": 10,
    "status": "ok",
    "message": "Distance sum matches odometer delta (0% variance)"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "validation": {
    "odometer_delta_km": 820,
    "trips_sum_km": 920,
    "variance_percent": 12.2,
    "threshold_percent": 10,
    "status": "error",
    "message": "Distance variance too high (+12.2%, exceeds ±10%)",
    "suggestion": "Check for missing trips or incorrect odometer reading"
  }
}
```

### 2. validation.validate_trip

**Purpose:** Validate fuel consumption against expected value (±15% threshold)

**Parameters:**
```json
{
  "distance_km": 820,
  "actual_fuel_liters": 72.8,
  "vehicle_avg_efficiency_l_per_100km": 8.5,
  "fuel_type": "Diesel"
}
```

**Response:**
```json
{
  "success": true,
  "validation": {
    "expected_fuel_liters": 69.7,
    "actual_fuel_liters": 72.8,
    "variance_percent": 4.4,
    "threshold_percent": 15,
    "status": "ok",
    "message": "Fuel consumption within expected range (+4.4%)"
  }
}
```

**Warning Response:**
```json
{
  "success": true,
  "validation": {
    "expected_fuel_liters": 69.7,
    "actual_fuel_liters": 85.0,
    "variance_percent": 22.0,
    "threshold_percent": 15,
    "status": "warning",
    "message": "Fuel consumption higher than expected (+22.0%, exceeds ±15%)",
    "suggestion": "Possible causes: heavy cargo, trailer, traffic, aggressive driving"
  }
}
```

### 3. validation.check_efficiency

**Purpose:** Validate trip efficiency is within fuel-type specific range

**Parameters:**
```json
{
  "efficiency_l_per_100km": 8.9,
  "fuel_type": "Diesel"
}
```

**Response:**
```json
{
  "success": true,
  "validation": {
    "efficiency_l_per_100km": 8.9,
    "fuel_type": "Diesel",
    "min_range": 5,
    "max_range": 15,
    "status": "ok",
    "message": "Efficiency within normal range for Diesel (5-15 L/100km)"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "validation": {
    "efficiency_l_per_100km": 25.0,
    "fuel_type": "Diesel",
    "min_range": 5,
    "max_range": 15,
    "status": "error",
    "message": "Efficiency out of range for Diesel (expected 5-15 L/100km)",
    "suggestion": "Check distance and fuel entries for errors"
  }
}
```

### 4. validation.check_deviation_from_average

**Purpose:** Check if trip efficiency deviates significantly from vehicle average (±20% threshold)

**Parameters:**
```json
{
  "trip_efficiency_l_per_100km": 8.9,
  "vehicle_avg_efficiency_l_per_100km": 8.5,
  "vehicle_id": "string (UUID)"
}
```

**Response:**
```json
{
  "success": true,
  "validation": {
    "trip_efficiency": 8.9,
    "vehicle_average": 8.5,
    "deviation_percent": 4.7,
    "threshold_percent": 20,
    "status": "ok",
    "message": "Trip efficiency within normal deviation (+4.7% from average)"
  }
}
```

**Warning Response:**
```json
{
  "success": true,
  "validation": {
    "trip_efficiency": 10.4,
    "vehicle_average": 8.5,
    "deviation_percent": 22.4,
    "threshold_percent": 20,
    "status": "warning",
    "message": "Trip efficiency deviates significantly from average (+22.4%)",
    "suggestion": "Unusual but acceptable. Add note if known cause (cargo, traffic, etc.)"
  }
}
```

## Validation Thresholds

### Distance Sum Validation
```python
DISTANCE_VARIANCE_PERCENT = 10

def validate_distance_sum(odometer_delta, trips_sum):
    variance = abs(odometer_delta - trips_sum) / odometer_delta * 100
    if variance <= DISTANCE_VARIANCE_PERCENT:
        return "ok"
    else:
        return "error"
```

### Fuel Consumption Validation
```python
CONSUMPTION_VARIANCE_PERCENT = 15

def validate_fuel_consumption(expected, actual):
    variance = abs(actual - expected) / expected * 100
    if variance <= CONSUMPTION_VARIANCE_PERCENT:
        return "ok"
    else:
        return "warning"
```

### Efficiency Range Validation
```python
EFFICIENCY_RANGES = {
    "Diesel": {"min": 5, "max": 15},
    "Gasoline": {"min": 6, "max": 20},
    "LPG": {"min": 7, "max": 15},
    "CNG": {"min": 4, "max": 10}
}

def check_efficiency(efficiency, fuel_type):
    range_def = EFFICIENCY_RANGES[fuel_type]
    if range_def["min"] <= efficiency <= range_def["max"]:
        return "ok"
    else:
        return "error"
```

### Deviation from Average Validation
```python
DEVIATION_THRESHOLD_PERCENT = 20

def check_deviation(trip_efficiency, vehicle_avg):
    deviation = abs(trip_efficiency - vehicle_avg) / vehicle_avg * 100
    if deviation <= DEVIATION_THRESHOLD_PERCENT:
        return "ok"
    else:
        return "warning"
```

## Efficiency Ranges by Fuel Type

| Fuel Type | Min (L/100km) | Max (L/100km) | Notes |
|-----------|---------------|---------------|-------|
| Diesel | 5 | 15 | Modern diesel engines |
| Gasoline | 6 | 20 | Standard gasoline engines |
| LPG | 7 | 15 | Converted vehicles |
| CNG | 4 | 10 | kg/100km (compressed gas) |

## Validation Status Codes

### Status Values
- **"ok"**: All checks passed ✅
- **"warning"**: Unusual but acceptable ⚠️
- **"error"**: Data integrity issue ❌

### Visual Indicators
```python
STATUS_SYMBOLS = {
    "ok": "✅",
    "warning": "⚠️",
    "error": "❌"
}
```

## Batch Validation

Validate multiple checkpoints/trips at once:

```json
{
  "operation": "batch_validate",
  "checkpoint_pairs": [
    {
      "checkpoint1_id": "uuid1",
      "checkpoint2_id": "uuid2",
      "trips": [...]
    }
  ],
  "trips": [
    {
      "trip_id": "uuid",
      "distance_km": 410,
      "fuel_consumption_liters": 34.85,
      "fuel_efficiency_l_per_100km": 8.5
    }
  ]
}
```

Response shows summary:
```json
{
  "success": true,
  "summary": {
    "total_validations": 15,
    "passed": 13,
    "warnings": 2,
    "errors": 0
  },
  "details": [...]
}
```

## Contextual Suggestions

### Distance Variance High
```
"Check for missing trips or incorrect odometer reading"
```

### Fuel Consumption High
```
"Possible causes: heavy cargo, trailer, traffic, aggressive driving"
```

### Efficiency Out of Range
```
"Check distance and fuel entries for errors"
```

### Deviation High
```
"Unusual but acceptable. Add note if known cause (cargo, traffic, etc.)"
```

## Pre-Report Validation

Before generating report, validate all trips:

```json
{
  "operation": "pre_report_validation",
  "date_range": {
    "start_date": "2025-11-01",
    "end_date": "2025-11-30"
  },
  "vehicle_id": "uuid"
}
```

Response blocks report if errors found:
```json
{
  "success": false,
  "ready_for_report": false,
  "issues": {
    "errors": 2,
    "warnings": 3,
    "compliance_issues": [
      "VIN missing",
      "Driver name missing (3 trips)",
      "Business description missing (2 trips)"
    ]
  },
  "message": "Fix errors before generating report"
}
```
