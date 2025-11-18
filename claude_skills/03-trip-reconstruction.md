# Skill 3: Trip Reconstruction (GPS-First Matching)

**Purpose:** Fill checkpoint gaps using hybrid GPS (70%) + address (30%) template matching

**Priority:** P0 (Core innovation)

---

## Trigger Words

- Automatic after checkpoint with gap: "820km gap detected. Reconstruct?"
- "fill trips", "reconstruct from November 1"
- "what did I drive between checkpoints?"

---

## Workflow (Orchestration Pattern)

### Step 1: Get Gap Data
```
[Triggered after checkpoint creation shows gap]

Claude: "📊 Gap Analysis:
• Start: Bratislava (Nov 1, 45,000 km)
• End: Košice (Nov 8, 45,820 km)
• Distance: 820 km
• Duration: 7 days

How would you like to fill this gap?
1️⃣ Use my templates (automatic matching)
2️⃣ Tell me specific trips
3️⃣ I'll do it later"
```

### Step 2: Template Matching (If Option 1)
```
Claude: "Fetching your templates...

[Calls: car-log-core.list_templates]

Found 3 templates:
• Warehouse Run (Bratislava ↔ Košice, 410km)
• Daily Commute (Home ↔ Office, 25km)
• Client Visit (Office → Trnava, 45km)

Calculating routes...
[Calls: geo-routing.calculate_route for each]

Running GPS-first matching (70% GPS, 30% address)...
[Calls: trip-reconstructor.match_templates with gap_data + templates]

📊 Reconstruction Proposal:

High Confidence (92%):
✓ 2× Warehouse Run (820km total)
  • Nov 1-2: Bratislava → Košice (410km)
  • Nov 6-7: Košice → Bratislava (410km)
  GPS match: 98% (within 50m of template)
  Day match: Monday & Thursday ✓

Coverage: 820km / 820km (100%) ✓

Accept this proposal?"
```

### Step 3: Create Trips
```
User: "Yes"

Claude: "Creating trips...
[Calls: car-log-core.create_trips_batch]

✅ 2 trips created!

Running validation...
[Calls: validation.validate_checkpoint_pair]

✅ Validation passed:
• Distance sum: 820km (0% variance)
• Fuel consumption: 72.8L (expected: 69.7L, +4.4% ✓)
• Efficiency: 8.9 L/100km (within Diesel range 5-15 ✓)

Your trips are ready for reporting!"
```

---

## MCP Tools Used (Orchestration)

1. **car-log-core.detect_gap** - Get gap data
2. **car-log-core.list_templates** - Fetch user templates
3. **geo-routing.calculate_route** - Optional route calculation
4. **trip-reconstructor.match_templates** - Stateless matching (core algorithm)
5. **car-log-core.create_trips_batch** - Save approved trips
6. **validation.validate_checkpoint_pair** - Check distance sum
7. **validation.validate_trip** - Check each trip

---

## GPS-First Scoring

```
GPS Distance    Score    Address Score    Final (70/30)
< 100m          100      High match       100
100m-500m       90       Medium match     88
500m-2km        70       Low match        56
2km-5km         40       No match         28
> 5km           0        -                0
```

---

## Success Criteria

- ✅ GPS matching 70% weight, address 30%
- ✅ Confidence >= 70% shown to user
- ✅ Stateless orchestration (Skill fetches all data)
- ✅ Automatic validation after creation
- ✅ Natural language proposal ("2× Warehouse Run")

---

**Implementation:** 📋 Spec ready | **Effort:** 4-5 hours
