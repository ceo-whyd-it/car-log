# Validation MCP Server

**Status:** ✅ Complete (Track C: C7-C11)
**Language:** Python
**Priority:** P0 (Required for MVP)

## Overview

The validation MCP server provides 4 data validation algorithms for the Car Log system:

1. **Distance Sum Validation** (±10%) - Validate odometer delta against trip distances
2. **Fuel Consumption Validation** (±15%) - Check fuel consumption against expected values
3. **Efficiency Reasonability** - Validate fuel efficiency against fuel type ranges
4. **Deviation from Average** (±20%) - Compare trip efficiency to vehicle average

## Tools

### 1. `validate_checkpoint_pair`

Validate gap between two checkpoints by comparing odometer delta against sum of trip distances.

**Input:**
```json
{
  "start_checkpoint_id": "uuid",
  "end_checkpoint_id": "uuid"
}
```

**Output:**
```json
{
  "status": "ok" | "warning" | "error",
  "distance_km": 820,
  "days": 30,
  "km_per_day": 27.33,
  "trip_count": 15,
  "trip_distance_sum": 815.5,
  "variance_percent": 0.55,
  "warnings": [],
  "errors": []
}
```

**Validation Logic:**
- Calculate odometer delta: `end_odometer - start_odometer`
- Sum all trip distances between checkpoints
- Calculate variance: `|odometer_delta - trip_sum| / odometer_delta * 100`
- **Error** if variance > 10%
- **Warning** if variance > 5%
- **OK** otherwise

**Example:**
```python
# OK case
Odometer: 100000 → 100820 (820 km)
Trips: 410 + 405 = 815 km
Variance: 0.61% ✓

# Error case
Odometer: 100000 → 100820 (820 km)
Trips: 410 + 290 = 700 km
Variance: 14.63% ✗
```

---

### 2. `validate_trip`

Comprehensive trip validation combining all 4 algorithms.

**Input:**
```json
{
  "trip": {
    "distance_km": 410,
    "fuel_consumption_liters": 34.85,
    "fuel_efficiency_l_per_100km": 8.5,
    "vehicle_avg_efficiency_l_per_100km": 8.5,
    "fuel_type": "Diesel"
  }
}
```

**Output:**
```json
{
  "status": "validated" | "has_warnings" | "has_errors",
  "distance_check": "ok" | "warning" | "error",
  "efficiency_check": "ok" | "warning" | "error",
  "consumption_check": "ok" | "warning" | "error",
  "deviation_check": "ok" | "warning",
  "warnings": [],
  "errors": []
}
```

**Checks Performed:**
1. **Distance** - Must be > 0, warn if > 2000 km
2. **Efficiency** - Must be within fuel type range
3. **Consumption** - Compare actual vs expected (±15%)
4. **Deviation** - Compare to vehicle average (±20%)

---

### 3. `check_efficiency`

Check if fuel efficiency is within reasonable range for fuel type.

**Input:**
```json
{
  "efficiency_l_per_100km": 8.5,
  "fuel_type": "Diesel"
}
```

**Output:**
```json
{
  "status": "ok" | "warning" | "error",
  "efficiency": 8.5,
  "expected_range": {
    "min": 5.0,
    "max": 15.0
  },
  "message": "Efficiency within normal range: 8.5 L/100km (expected: 5-15 L/100km)"
}
```

**Fuel Type Ranges (L/100km):**

| Fuel Type | Min | Max |
|-----------|-----|-----|
| Diesel    | 5.0 | 15.0 |
| Gasoline  | 6.0 | 20.0 |
| LPG       | 8.0 | 25.0 |
| Hybrid    | 3.0 | 10.0 |
| Electric  | N/A | N/A (uses kWh) |

**Validation Logic:**
- **Error** if efficiency < min or > max
- **Warning** if within 10% of boundary
- **OK** otherwise

---

### 4. `check_deviation_from_average`

Compare trip efficiency to vehicle average efficiency.

**Input:**
```json
{
  "trip_efficiency_l_per_100km": 9.0,
  "vehicle_avg_efficiency_l_per_100km": 8.5
}
```

**Output:**
```json
{
  "status": "ok" | "warning",
  "deviation_percent": 5.88,
  "message": "Trip efficiency 9.0 L/100km is within normal range of vehicle average 8.5 L/100km (5.9% deviation)",
  "suggestion": "Trip efficiency is consistent with vehicle average."
}
```

**Validation Logic:**
- Calculate deviation: `|trip_eff - avg_eff| / avg_eff * 100`
- **Warning** if deviation > 20%
- **OK** otherwise

**Warning Suggestions:**
- **Higher than average:** Check for heavy traffic, AC usage, aggressive driving, cargo load, terrain
- **Lower than average:** Possible highway driving, ideal conditions, light traffic, eco-driving

---

## Configuration

All thresholds are configurable via environment variables:

```bash
# Distance validation threshold
export DISTANCE_VARIANCE_PERCENT=10

# Fuel consumption validation threshold
export CONSUMPTION_VARIANCE_PERCENT=15

# Deviation from average warning threshold
export DEVIATION_THRESHOLD_PERCENT=20

# Fuel type efficiency ranges
export DIESEL_MIN_L_PER_100KM=5.0
export DIESEL_MAX_L_PER_100KM=15.0
export GASOLINE_MIN_L_PER_100KM=6.0
export GASOLINE_MAX_L_PER_100KM=20.0
export LPG_MIN_L_PER_100KM=8.0
export LPG_MAX_L_PER_100KM=25.0
export HYBRID_MIN_L_PER_100KM=3.0
export HYBRID_MAX_L_PER_100KM=10.0
```

## Installation

```bash
cd mcp-servers/validation
pip install -r requirements.txt
```

## Usage

### As MCP Server

Add to Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "validation": {
      "command": "python",
      "args": ["-m", "mcp_servers.validation"],
      "env": {
        "DATA_PATH": "~/Documents/MileageLog/data",
        "DISTANCE_VARIANCE_PERCENT": "10",
        "CONSUMPTION_VARIANCE_PERCENT": "15",
        "DEVIATION_THRESHOLD_PERCENT": "20"
      }
    }
  }
}
```

### Run Tests

```bash
python -m pytest tests/test_validation.py -v
```

## Test Coverage

**26 tests, all passing:**

- ✅ 9 tests for `check_efficiency` (all fuel types, boundaries, errors)
- ✅ 5 tests for `check_deviation_from_average` (deviations, edge cases)
- ✅ 5 tests for `validate_trip` (comprehensive validation)
- ✅ 2 tests for validation thresholds
- ✅ 5 tests for edge cases and error handling

## File Structure

```
validation/
├── __init__.py              # Package metadata
├── __main__.py              # MCP server entry point (76 lines)
├── requirements.txt         # Dependencies (1 line)
├── thresholds.py           # Validation constants (64 lines)
└── tools/
    ├── __init__.py         # Tool exports (16 lines)
    ├── validate_checkpoint_pair.py  # Distance sum check (218 lines)
    ├── validate_trip.py    # Comprehensive validation (186 lines)
    ├── check_efficiency.py # Efficiency reasonability (149 lines)
    └── check_deviation_from_average.py  # Deviation check (135 lines)
```

**Total:** ~845 lines of production code + 355 lines of tests

## Error Handling

All tools return consistent error format:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR" | "NOT_FOUND" | "INTERNAL_ERROR",
    "message": "Human-readable error message",
    "field": "field_name",
    "details": "Additional context"
  }
}
```

## Dependencies

- `car-log-core` - For checkpoint and trip data access
- None external (standalone validation logic)

## Slovak Tax Compliance

All validation algorithms use **L/100km** format (European standard), never km/L.

Distance and fuel consumption checks ensure Slovak VAT Act 2025 compliance by:
- Detecting missing trips (odometer gaps)
- Identifying unrealistic fuel consumption
- Flagging data entry errors

## Performance

- **validate_checkpoint_pair:** O(n) where n = trips between checkpoints
- **validate_trip:** O(1) constant time
- **check_efficiency:** O(1) constant time
- **check_deviation_from_average:** O(1) constant time

All validations complete in < 100ms for typical data volumes.

## Examples

### Example 1: Valid Trip (All Checks Pass)

```python
result = await validation.validate_trip({
    "trip": {
        "distance_km": 410,
        "fuel_consumption_liters": 34.85,
        "fuel_efficiency_l_per_100km": 8.5,
        "vehicle_avg_efficiency_l_per_100km": 8.5,
        "fuel_type": "Diesel"
    }
})

# Result:
{
    "status": "validated",
    "distance_check": "ok",
    "efficiency_check": "ok",
    "consumption_check": "ok",
    "deviation_check": "ok",
    "warnings": [],
    "errors": []
}
```

### Example 2: High Fuel Consumption Warning

```python
result = await validation.validate_trip({
    "trip": {
        "distance_km": 410,
        "fuel_consumption_liters": 49.2,  # 12 L/100km
        "fuel_efficiency_l_per_100km": 12.0,
        "vehicle_avg_efficiency_l_per_100km": 8.5,
        "fuel_type": "Diesel"
    }
})

# Result:
{
    "status": "has_warnings",
    "distance_check": "ok",
    "efficiency_check": "ok",
    "consumption_check": "ok",
    "deviation_check": "warning",
    "warnings": [
        "Trip efficiency 12.0 L/100km is 41.2% higher than vehicle average 8.5 L/100km (threshold: 20%)"
    ],
    "errors": []
}
```

### Example 3: Unrealistic Efficiency Error

```python
result = await validation.check_efficiency({
    "efficiency_l_per_100km": 25.0,
    "fuel_type": "Diesel"
})

# Result:
{
    "status": "error",
    "efficiency": 25.0,
    "expected_range": {"min": 5.0, "max": 15.0},
    "message": "Unrealistically high efficiency: 25.0 L/100km. Expected range for Diesel: 5-15 L/100km. Verify measurement or check for data entry error."
}
```

---

**Implementation:** Track C (C7-C11), 10 hours estimated, completed in 8 hours
**Status:** ✅ All tests passing, ready for integration
**Next Step:** Integration with car-log-core and trip-reconstructor
