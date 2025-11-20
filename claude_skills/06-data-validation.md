# Skill 6: Data Validation Assistant (Proactive)

**Purpose:** Automatically validate data and warn users about potential issues

**Priority:** P0

---

## Trigger Words

- Automatic after checkpoint/trip creation
- "check my data", "validate trips"
- "are there any errors?"

---

## Workflow (Proactive)

### Automatic Validation
```
[After creating checkpoint/trip]

Claude: "Running validation checks...

[Calls: validation.validate_checkpoint_pair]
[Calls: validation.validate_trip]
[Calls: validation.check_efficiency]
[Calls: validation.check_deviation_from_average]

✅ All validation checks passed!

1️⃣ Distance Sum: 820km ✓
   Odometer delta: 820km
   Trips total: 820km (0% variance, within ±10%)

2️⃣ Fuel Consumption: 72.8L ✓
   Expected: 69.7L (8.5 L/100km average)
   Variance: +4.4% (within ±15%)

3️⃣ Efficiency: 8.9 L/100km ✓
   Range: 5-15 L/100km (Diesel)
   Status: Normal for commercial vans

4️⃣ Deviation: +4.7% ✓
   Vehicle average: 8.5 L/100km
   Trip: 8.9 L/100km (under 20% threshold)"
```

### Warning Example
```
Claude: "⚠️ Validation Warnings:

Trip efficiency 15.2 L/100km is 38% above your average (11.0 L/100km).

Possible causes:
• Heavy load or trailer
• City driving (more idling)
• Cold weather (increased consumption)
• Data entry error

Recommendation: Double-check fuel quantity (52.3L) and distance (344km).

Continue anyway? (yes/no)"
```

### Error Example
```
Claude: "❌ Validation Error:

Distance sum mismatch:
• Odometer delta: 820km
• Trips total: 650km
• Variance: -20.7% (exceeds ±10% tolerance)

You're missing 170km of trips. Options:
1. Add missing trips manually
2. Adjust existing trip distances
3. Skip validation (not recommended for tax)"
```

---

## MCP Tools Used (4 Algorithms)

1. **validation.validate_checkpoint_pair** - Distance sum ±10%
2. **validation.validate_trip** - Fuel consumption ±15%
3. **validation.check_efficiency** - Range check (5-15 L/100km Diesel, 6-20 L/100km Gasoline)
4. **validation.check_deviation_from_average** - ±20% from vehicle avg

---

## Orchestration Pattern (Detailed)

### Pattern: Automatic Validation After Data Entry

```typescript
// Triggered automatically after:
// - checkpoint creation
// - trip creation
// - trip update

// 1. Validate checkpoint pair (distance sum)
const distanceCheck = await validation.validate_checkpoint_pair({
  checkpoint1_id: start_checkpoint_id,
  checkpoint2_id: end_checkpoint_id
});
// Returns: { valid: true/false, variance: 2.3, threshold: 10, message: "..." }

// 2. Validate trip (fuel consumption)
const fuelCheck = await validation.validate_trip({
  trip_id: trip_id
});
// Returns: { valid: true/false, expected_fuel: 69.7, actual_fuel: 72.8, variance: 4.4, threshold: 15, message: "..." }

// 3. Check efficiency range
const efficiencyCheck = await validation.check_efficiency({
  trip_id: trip_id
});
// Returns: { valid: true/false, efficiency: 8.9, fuel_type: "Diesel", range: [5, 15], message: "..." }

// 4. Check deviation from average
const deviationCheck = await validation.check_deviation_from_average({
  trip_id: trip_id,
  vehicle_id: vehicle_id
});
// Returns: { valid: true/false, trip_efficiency: 8.9, vehicle_avg: 8.5, deviation: 4.7, threshold: 20, message: "..." }

// 5. Present results to user
if (all_valid) {
  show_success_message();
} else if (has_errors) {
  show_errors_and_block();
} else if (has_warnings) {
  show_warnings_and_ask_confirmation();
}
```

---

## Validation Thresholds

```
Algorithm              Threshold          Action         Fuel Type
═══════════════════════════════════════════════════════════════════
Distance Sum           ±10%               Error          All
Fuel Consumption       ±15%               Warning        All
Efficiency Range       5-15 L/100km       Error          Diesel
                       6-20 L/100km       Error          Gasoline
                       4-12 L/100km       Error          LPG
                       4-10 L/100km       Error          CNG
Deviation from Avg     ±20%               Warning        All
```

### Algorithm Explanations

#### 1. Distance Sum (±10% Error Threshold)

**What it checks:**
```
Odometer delta = end_odometer - start_odometer
Trips total = sum of all trip distances between checkpoints
Variance = |odometer_delta - trips_total| / odometer_delta * 100
```

**Why it matters:**
- Ensures all trips are recorded (no gaps)
- Catches data entry errors
- Required for Slovak tax compliance

**Example:**
```
✅ PASS:
Odometer: 50,000 → 50,820 (820km)
Trips: 410 + 410 = 820km
Variance: 0% (within ±10%)

❌ FAIL:
Odometer: 50,000 → 50,820 (820km)
Trips: 410 + 300 = 710km
Variance: -13.4% (exceeds ±10%)
Missing: 110km of trips!
```

#### 2. Fuel Consumption (±15% Warning Threshold)

**What it checks:**
```
Expected fuel = distance * vehicle_avg_efficiency / 100
Actual fuel = sum of refuel amounts
Variance = |expected - actual| / expected * 100
```

**Why it matters:**
- Detects fuel theft or leaks
- Catches incorrect refuel quantities
- Validates efficiency calculations

**Example:**
```
✅ PASS:
Distance: 820km
Vehicle avg: 8.5 L/100km
Expected: 69.7L
Actual: 72.8L
Variance: +4.4% (within ±15%)

⚠️ WARNING:
Distance: 820km
Expected: 69.7L
Actual: 85.0L
Variance: +22.0% (exceeds ±15%)
Possible: Heavy load or data error
```

#### 3. Efficiency Range (Fuel-Type Specific)

**What it checks:**
```
Efficiency = fuel_consumed / distance * 100
Check if efficiency is within reasonable range for fuel type
```

**Ranges by fuel type:**
- **Diesel:** 5-15 L/100km
  - Light cars: 5-8 L/100km
  - Vans/trucks: 8-12 L/100km
  - Heavy commercial: 12-15 L/100km
- **Gasoline:** 6-20 L/100km
  - Economy cars: 6-9 L/100km
  - Standard cars: 9-12 L/100km
  - SUVs/trucks: 12-20 L/100km
- **LPG:** 4-12 L/100km
- **CNG:** 4-10 L/100km (measured in kg, converted to L equivalent)

**Example:**
```
✅ PASS:
Efficiency: 8.9 L/100km
Fuel: Diesel
Range: 5-15 L/100km
Status: Normal for commercial van

❌ FAIL:
Efficiency: 22.5 L/100km
Fuel: Diesel
Range: 5-15 L/100km
Status: Outside reasonable range
Likely: Data entry error
```

#### 4. Deviation from Average (±20% Warning)

**What it checks:**
```
Vehicle avg = mean efficiency of all previous trips
Trip efficiency = this trip's efficiency
Deviation = |trip - avg| / avg * 100
```

**Why it matters:**
- Flags unusual trips for review
- Detects gradual efficiency degradation
- Helps identify vehicle issues

**Example:**
```
✅ PASS:
Vehicle avg: 8.5 L/100km
This trip: 8.9 L/100km
Deviation: +4.7% (within ±20%)

⚠️ WARNING:
Vehicle avg: 8.5 L/100km
This trip: 11.5 L/100km
Deviation: +35.3% (exceeds ±20%)
Possible causes:
• Heavy load or trailer
• City driving (more idling)
• Cold weather
• Data entry error
```

---

## Visual Presentation

### All Checks Pass (Success)

```
✅ All validation checks passed!

1️⃣ Distance Sum: 820km ✓
   Odometer delta: 820km
   Trips total: 820km (0% variance, within ±10%)

2️⃣ Fuel Consumption: 72.8L ✓
   Expected: 69.7L (8.5 L/100km average)
   Variance: +4.4% (within ±15%)

3️⃣ Efficiency: 8.9 L/100km ✓
   Range: 5-15 L/100km (Diesel)
   Status: Normal for commercial vans

4️⃣ Deviation: +4.7% ✓
   Vehicle average: 8.5 L/100km
   Trip: 8.9 L/100km (under 20% threshold)
```

### Warnings (User Confirmation Required)

```
⚠️ Validation Warnings:

2️⃣ Fuel Consumption: +22.0%
   Expected: 69.7L
   Actual: 85.0L
   Variance: +22.0% (exceeds ±15% threshold)

   Possible causes:
   • Heavy load or trailer attached
   • Extra refuels not recorded
   • Data entry error in distance

   Recommendation: Double-check fuel quantity and distance.

4️⃣ Deviation from Average: +35.3%
   Vehicle avg: 8.5 L/100km
   This trip: 11.5 L/100km

   This is significantly above your typical efficiency.
   Common reasons: city driving, cold weather, heavy load.

Continue anyway? (yes/no)
```

### Errors (Blocking, Must Fix)

```
❌ Validation Errors (must fix before saving):

1️⃣ Distance Sum Mismatch: -13.4%
   Odometer delta: 820km
   Trips total: 710km
   Missing: 110km of trips

   You're missing 110km worth of trips between these checkpoints.

   Options:
   1. Add missing trips manually
   2. Adjust existing trip distances
   3. Check odometer readings for errors

3️⃣ Efficiency Out of Range
   Efficiency: 22.5 L/100km
   Expected range: 5-15 L/100km (Diesel)

   This is outside the reasonable range for diesel vehicles.

   Possible issues:
   • Incorrect fuel quantity entered
   • Incorrect distance entered
   • Wrong fuel type selected

   Please review and correct the data.

Cannot proceed until these errors are fixed.
```

---

## Conversational Validation (Best Practices)

### Good Examples (Actionable, Clear, Helpful)

```
✅ "This efficiency (8.9 L/100km) is normal for your Ford Transit."

⚠️ "Your fuel consumption is 22% higher than expected. This could be
due to heavy load, city driving, or a data entry error. The fuel
quantity (85.0L) seems high for 820km. Can you double-check?"

❌ "Distance mismatch: You're missing 110km of trips between Nov 1
and Nov 3. You recorded 710km but your odometer shows 820km."
```

### Bad Examples (Cryptic, Unhelpful, Technical Jargon)

```
❌ "ERROR: EFFICIENCY_OUT_OF_RANGE
Code: VAL_001
Threshold exceeded
Exit code: -1"

❌ "Variance: -13.4%
Tolerance: ±10.0%
Status: FAILED"

❌ "Invalid trip data. Check logs for details."
```

### Key Principles:
1. **Explain the issue** in plain language
2. **Provide context** (numbers, comparisons)
3. **Suggest causes** (common reasons)
4. **Offer solutions** (actionable steps)
5. **Use visual indicators** (✅ ⚠️ ❌)
6. **Be conversational** (not technical)

---

## Example Validation Outputs

### Example 1: Perfect Data (All Pass)

```
User: [Creates trip: Bratislava → Košice, 410km, 34.85L]

Claude: "Trip created! Running validation checks...

✅ All validation checks passed!

1️⃣ Distance Sum: ✓
   Your odometer readings match trip distances perfectly.

2️⃣ Fuel Consumption: ✓
   34.85L is right on target for 410km at 8.5 L/100km.

3️⃣ Efficiency: 8.5 L/100km ✓
   Perfect for a diesel van on highway driving.

4️⃣ Deviation: 0% ✓
   Exactly matches your vehicle average.

Trip saved successfully!"
```

### Example 2: Warning (Deviation 21%)

```
User: [Creates trip: 410km, 52.3L fuel]

Claude: "Trip created! Running validation checks...

⚠️ Validation Warning:

4️⃣ Deviation from Average: +38%
   Your typical efficiency: 8.5 L/100km
   This trip: 12.8 L/100km

This is 38% above your average, which is unusual.

Common causes:
• Heavy load or trailer (adds 20-40% fuel use)
• City driving vs. highway (30-50% more fuel)
• Cold weather (10-25% increase)
• Data entry error

Was there something different about this trip?
(heavy load / city driving / correct as-is / fix data)"
```

### Example 3: Error (Distance Mismatch 12%)

```
User: [Creates trips totaling 650km between odometer readings 820km apart]

Claude: "Running validation checks...

❌ Validation Error:

1️⃣ Distance Sum Mismatch: -20.7%
   Odometer: 50,000 → 50,820 (820km)
   Trips recorded: 650km
   Missing: 170km

You're missing 170km worth of trips between Nov 1 and Nov 5.

This gap is too large for Slovak tax compliance (max ±10%).

Options:
1. Add missing trips - Were there trips you forgot to log?
2. Check odometer - Could the reading be wrong?
3. Adjust trips - Should existing trips be longer?

What would you like to do?"
```

### Example 4: Multiple Issues

```
User: [Creates problematic trip]

Claude: "Running validation checks...

❌ 2 Errors, ⚠️ 1 Warning

❌ Distance Sum: -12.0%
   Missing 98km of trips between checkpoints.

❌ Efficiency Out of Range: 22.5 L/100km
   Expected range: 5-15 L/100km (Diesel)
   This is unusually high - likely a data entry error.

⚠️ Fuel Consumption: +45%
   Expected: 48.0L
   Actual: 69.6L

Recommendation: Review these fields:
• Distance: Is 308km correct?
• Fuel: Is 69.6L correct? (Seems high)
• Fuel type: Is this really diesel?

Would you like to edit this trip? (yes/no)"
```

### Example 5: Gradual Efficiency Drop (Historical Analysis)

```
User: "Check my efficiency trend"

Claude: "[Calls: validation.check_deviation_from_average for last 10 trips]

📊 Efficiency Trend Analysis:

Month      Avg Efficiency   Change
═══════════════════════════════════
Sep 2025   8.3 L/100km      Baseline
Oct 2025   8.7 L/100km      +4.8% ⚠️
Nov 2025   9.2 L/100km      +10.8% ⚠️

⚠️ Your fuel efficiency has decreased by 10.8% over 2 months.

Possible causes:
• Seasonal (winter increases fuel use by 10-15%)
• Vehicle maintenance needed (tire pressure, air filter, oil change)
• Driving habits changed (more city driving, shorter trips)
• Load increased (carrying heavier cargo)

Recommendations:
1. Check tire pressure (low pressure = +5-10% fuel use)
2. Service vehicle (overdue maintenance = +10-20%)
3. Review trip patterns (more city vs. highway)

Would you like to see a detailed breakdown by trip type?"
```

---

## Testing Scenarios

### Scenario 1: Happy Path - All Checks Pass

**Input:**
- Odometer: 50,000 → 50,820 (820km)
- Trips: 410 + 410 = 820km
- Fuel: 34.85 + 36.90 = 71.75L
- Vehicle avg: 8.5 L/100km
- Trip efficiency: 8.75 L/100km

**Expected Behavior:**
1. Run all 4 validation checks
2. All pass with green checkmarks
3. Show detailed breakdown
4. Allow trip to be saved

**MCP Calls:**
1. `validation.validate_checkpoint_pair` → pass
2. `validation.validate_trip` → pass
3. `validation.check_efficiency` → pass
4. `validation.check_deviation_from_average` → pass

### Scenario 2: Warning - Deviation 21%

**Input:**
- Trip efficiency: 10.3 L/100km
- Vehicle avg: 8.5 L/100km
- Deviation: +21.2%

**Expected Behavior:**
1. Distance, fuel, efficiency checks pass
2. Deviation check returns warning
3. Show warning with contextual suggestions
4. Ask user for confirmation
5. Allow save if user confirms

**MCP Calls:**
1. `validation.check_deviation_from_average` → warning (deviation: 21.2%, threshold: 20%)

### Scenario 3: Error - Distance Mismatch

**Input:**
- Odometer: 820km delta
- Trips total: 650km
- Variance: -20.7%

**Expected Behavior:**
1. Distance check fails (exceeds ±10%)
2. Show clear error message
3. Explain the gap (170km missing)
4. Offer solutions
5. Block save until fixed

**MCP Calls:**
1. `validation.validate_checkpoint_pair` → error (variance: -20.7%, threshold: ±10%)

### Scenario 4: Error - Efficiency Out of Range

**Input:**
- Efficiency: 22.5 L/100km
- Fuel type: Diesel
- Range: 5-15 L/100km

**Expected Behavior:**
1. Efficiency range check fails
2. Show error with range context
3. Suggest likely causes (data entry error)
4. Recommend checking fuel quantity and distance
5. Block save until fixed

**MCP Calls:**
1. `validation.check_efficiency` → error (efficiency: 22.5, range: [5, 15])

### Scenario 5: Multiple Warnings (Allow with Confirmation)

**Input:**
- Fuel consumption: +18% (warning)
- Deviation: +25% (warning)

**Expected Behavior:**
1. Show both warnings
2. Provide context for each
3. Ask for single confirmation
4. Allow save if user confirms
5. Log that validation was overridden

**MCP Calls:**
1. `validation.validate_trip` → warning
2. `validation.check_deviation_from_average` → warning

---

## Success Criteria

- ✅ Automatic validation after data entry (checkpoint, trip creation/update)
- ✅ Clear distinction: warnings (user can override) vs. errors (must fix)
- ✅ Contextual suggestions for every issue
- ✅ Non-cryptic, conversational error messages
- ✅ 4 algorithms implemented (distance, fuel, efficiency, deviation)
- ✅ Visual indicators (✅ ⚠️ ❌) for quick scanning
- ✅ Fuel-type specific efficiency ranges
- ✅ Actionable recommendations (what to check, how to fix)
- ✅ Historical trend analysis (efficiency over time)
- ✅ Validation results stored with trip metadata

---

**Implementation:** 📋 Spec ready | **Effort:** 2 hours
