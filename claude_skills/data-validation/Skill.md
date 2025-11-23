---
name: "Data Validation"
description: "Validate trip data quality using 4 algorithms: distance sum, fuel consumption, efficiency range, deviation"
---

# Skill 6: Data Validation

## Purpose
Automatically validate trip data quality using 4 validation algorithms. Runs after every trip creation and can be manually triggered.

## Activation Triggers
- **Automatic:** After trip creation/reconstruction
- **Manual:** "validate", "check data", "run validation"
- **Pre-report:** Before report generation

## 4 Validation Algorithms

### 1. Distance Sum Validation (±10%)

**What it checks:** Odometer delta vs. sum of individual trip distances

**Formula:**
```
variance = |odometer_delta - trips_sum| / odometer_delta
ERROR if variance > 10%
```

**Example:**
```
Odometer delta: 820 km
Trips sum: 820 km
Variance: 0%
✅ Distance check passed
```

**Why it matters:** Ensures no trips are missing or duplicated between checkpoints.

### 2. Fuel Consumption Validation (±15%)

**What it checks:** Expected fuel vs. actual refuel amount

**Formula:**
```
expected_fuel = (trips_sum_km / 100) * vehicle_avg_efficiency
variance = |actual_fuel - expected_fuel| / expected_fuel
WARNING if variance > 15%
```

**Example:**
```
Expected fuel: 69.7L (820km ÷ 100 × 8.5 L/100km)
Actual fuel: 72.8L
Variance: +4.4%
✅ Fuel check passed (within ±15%)
```

**Why it matters:** Detects unusually high/low fuel consumption that may indicate errors.

### 3. Efficiency Range Validation

**What it checks:** Trip efficiency within fuel-type specific range

**Ranges by fuel type:**
- **Diesel:** 5-15 L/100km
- **Gasoline:** 6-20 L/100km
- **LPG:** 7-15 L/100km
- **CNG:** 4-10 kg/100km

**Example:**
```
Trip efficiency: 8.9 L/100km
Fuel type: Diesel
Range: 5-15 L/100km
✅ Efficiency in range
```

**Why it matters:** Catches data entry errors (e.g., 89 L/100km instead of 8.9).

### 4. Deviation from Average (±20%)

**What it checks:** Trip efficiency vs. vehicle's historical average

**Formula:**
```
deviation = |trip_efficiency - vehicle_avg| / vehicle_avg
WARNING if deviation > 20%
```

**Example:**
```
Trip efficiency: 8.9 L/100km
Vehicle average: 8.5 L/100km
Deviation: +4.7%
✅ Deviation acceptable (< 20%)
```

**Why it matters:** Flags unusual trips for review (heavy cargo, traffic, etc.).

## Visual Presentation

### All Checks Passed
```
Running validation...
✅ Distance: 820 km (0% variance)
✅ Fuel: 72.8L (+4.4%, within ±15%)
✅ Efficiency: 8.9 L/100km (Diesel: 5-15)
✅ Deviation: +4.7% from average

All checks passed! ✓
```

### Warning Detected
```
Running validation...
✅ Distance: 820 km (0% variance)
⚠️  Fuel: 85.0L (+22.0%, exceeds ±15%)
✅ Efficiency: 10.4 L/100km (Diesel: 5-15)
⚠️  Deviation: +22.4% from average

Warnings detected. Review recommended.
💡 Possible causes:
   • Heavy cargo or trailer
   • Traffic or route changes
   • Aggressive driving
```

### Error Detected
```
Running validation...
❌ Distance: 920 km (+12.2%, exceeds ±10%)
✅ Fuel: 72.8L (+4.4%)
✅ Efficiency: 7.9 L/100km (Diesel: 5-15)
✅ Deviation: -7.1% from average

ERROR: Distance variance too high!
💡 Possible causes:
   • Missing trip between checkpoints
   • Incorrect odometer reading
   • Trip distance miscalculated
```

## Warning vs. Error Distinction

### Errors (Block Save/Report)
- ❌ **Distance variance > 10%:** Critical data integrity issue
- ❌ **Efficiency out of range:** Likely data entry error
- ❌ **Missing mandatory fields:** Slovak compliance violation

### Warnings (Allow User Override)
- ⚠️  **Fuel variance > 15%:** Unusual but possible
- ⚠️  **Deviation > 20%:** Flag for review
- ⚠️  **Route deviation:** Different path taken

## Contextual Suggestions

**Distance variance high:**
→ "Check for missing trips or incorrect odometer reading"

**Fuel consumption high:**
→ "Was there heavy cargo, trailer, or traffic?"

**Efficiency out of range:**
→ "Verify distance and fuel entries are correct"

**Deviation high but in range:**
→ "Unusual but acceptable. Add note if known cause."

## Automatic Validation Flow

1. **After trip creation:**
   - Run all 4 algorithms
   - Display results
   - Block save if errors
   - Allow override if warnings only

2. **Before report generation:**
   - Validate all trips in range
   - Show summary of issues
   - Prevent report if compliance errors

3. **Manual validation:**
   - Run on specific checkpoint pair
   - Run on specific trip
   - Run on entire vehicle history

## Related Skills

- **Skill 2**: Checkpoint from Receipt (provides data)
- **Skill 3**: Trip Reconstruction (creates trips to validate)
- **Skill 5**: Report Generation (pre-validation required)

## MCP Tools Used

- `validation.validate_checkpoint_pair` (distance sum)
- `validation.validate_trip` (fuel consumption)
- `validation.check_efficiency` (range check)
- `validation.check_deviation_from_average` (historical comparison)
