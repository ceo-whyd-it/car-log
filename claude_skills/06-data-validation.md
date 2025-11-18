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
3. **validation.check_efficiency** - Range check (5-15 L/100km Diesel)
4. **validation.check_deviation_from_average** - ±20% from vehicle avg

---

## Validation Thresholds

```
Algorithm          Threshold    Action
═══════════════════════════════════════
Distance Sum       ±10%         Error if exceeded
Fuel Consumption   ±15%         Warning if exceeded
Efficiency Range   5-15 L/100km Error if outside
Deviation          ±20%         Warning if exceeded
```

---

## Conversational Validation

**Good (actionable):**
```
"⚠️ This efficiency is 38% above average.
Could be heavy load or data error.
Check fuel quantity: 52.3L correct?"
```

**Bad (cryptic):**
```
"ERROR: EFFICIENCY_OUT_OF_RANGE
Code: VAL_001
Threshold exceeded"
```

---

## Success Criteria

- ✅ Automatic validation after data entry
- ✅ Clear warnings vs. blocking errors
- ✅ Contextual suggestions
- ✅ Non-cryptic error messages
- ✅ 4 algorithms (distance, fuel, efficiency, deviation)

---

**Implementation:** 📋 Spec ready | **Effort:** 2 hours
