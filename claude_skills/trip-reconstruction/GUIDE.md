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

## Detailed GPS-First Hybrid Algorithm

### Matching Mode Selection

The algorithm automatically selects the best mode based on available data:

```javascript
function selectMatchingMode(gapCheckpoint1, gapCheckpoint2, template) {
  const hasGPS1 = gapCheckpoint1.location.coords != null;
  const hasGPS2 = gapCheckpoint2.location.coords != null;
  const hasAddr1 = gapCheckpoint1.location.address != null;
  const hasAddr2 = gapCheckpoint2.location.address != null;

  if (hasGPS1 && hasGPS2) {
    if (hasAddr1 && hasAddr2) {
      return "MODE_B_HYBRID"; // GPS 70% + Address 30%
    } else {
      return "MODE_A_GPS_ONLY"; // GPS 100%
    }
  } else if (hasAddr1 && hasAddr2) {
    return "MODE_C_ADDRESS_ONLY"; // Address 100% (fallback)
  } else {
    return "MODE_INSUFFICIENT_DATA"; // Cannot match
  }
}
```

### GPS Distance Scoring (70% weight)

```javascript
function calculateGPSScore(gapCoords, templateCoords) {
  const distance = haversineDistance(gapCoords, templateCoords);

  if (distance < 100) return 100;        // < 100m: Perfect match
  if (distance < 500) return 90;         // 100-500m: Excellent
  if (distance < 2000) return 70;        // 500m-2km: Good
  if (distance < 5000) return 40;        // 2-5km: Poor
  return 0;                               // > 5km: No match
}

// Calculate for both start and end points
const startScore = calculateGPSScore(gap.start_coords, template.from_coords);
const endScore = calculateGPSScore(gap.end_coords, template.to_coords);
const gpsScore = (startScore + endScore) / 2;
```

### Address Similarity Scoring (30% weight)

```javascript
function calculateAddressScore(gapAddress, templateAddress) {
  // Normalize addresses (lowercase, remove special chars)
  const norm1 = normalize(gapAddress);
  const norm2 = normalize(templateAddress);

  // Check for exact match
  if (norm1 === norm2) return 100;

  // Check for substring match
  if (norm1.includes(norm2) || norm2.includes(norm1)) return 80;

  // Check for city match (e.g., both contain "Bratislava")
  const city1 = extractCity(norm1);
  const city2 = extractCity(norm2);
  if (city1 === city2) return 60;

  // Calculate Levenshtein distance
  const levenshtein = levenshteinDistance(norm1, norm2);
  const similarity = 1 - (levenshtein / Math.max(norm1.length, norm2.length));

  return Math.round(similarity * 100);
}
```

### Final Confidence Score Calculation

```javascript
function calculateConfidenceScore(gapData, template, mode) {
  let confidence = 0;

  if (mode === "MODE_A_GPS_ONLY") {
    // GPS 100%
    confidence = gpsScore;
  } else if (mode === "MODE_B_HYBRID") {
    // GPS 70% + Address 30%
    const gpsWeight = 0.7;
    const addressWeight = 0.3;
    confidence = (gpsScore * gpsWeight) + (addressScore * addressWeight);
  } else if (mode === "MODE_C_ADDRESS_ONLY") {
    // Address 100% (fallback)
    confidence = addressScore;
  }

  // Apply bonus factors
  if (template.typical_days && matchesTypicalDay(gapData, template)) {
    confidence += 5; // +5% for day-of-week match
  }

  if (Math.abs(gapData.distance_km - template.distance_km) < 10) {
    confidence += 5; // +5% for distance match within 10km
  }

  return Math.min(Math.round(confidence), 100); // Cap at 100
}
```

---

## Confidence Tiers & User Presentation

### High Confidence (90-100%)
```
Claude: "📊 Reconstruction Proposal (92% confidence):

✓ Exact GPS match (within 50m)
✓ Day-of-week matches template
✓ Distance matches expected route

Proposal:
2× Warehouse Run (Bratislava ↔ Košice)
• Nov 1-2: Bratislava → Košice (410km)
• Nov 6-7: Košice → Bratislava (410km)

Coverage: 820km / 820km (100%) ✓

This looks very reliable. Accept?"
```

### Medium Confidence (70-89%)
```
Claude: "📊 Reconstruction Proposal (75% confidence):

⚠️ GPS match is approximate (within 1.5km)
✓ City names match (Bratislava, Košice)
⚠️ Days don't match typical pattern

Proposal:
2× Warehouse Run (820km total)

This is likely correct, but please verify:
1. Did you drive to Košice on Nov 1?
2. Did you return to Bratislava on Nov 6?

Accept, modify, or reject?"
```

### Low Confidence (<70%)
```
Claude: "📊 No High-Confidence Match Found

I found potential matches, but none are above 70% confidence:
• Warehouse Run (58%) - Distance matches, but GPS is 8km off
• Client Visit (42%) - Wrong direction

Options:
1. Manually describe the trips
2. Create a new template for this route
3. Skip reconstruction for now

What would you like to do?"
```

---

## Multiple Proposal Handling

### Scenario: Multiple Templates Match

```javascript
function handleMultipleMatches(matches) {
  // Filter high-confidence matches (>= 70%)
  const highConfidence = matches.filter(m => m.confidence >= 70);

  if (highConfidence.length === 0) {
    return showNoMatchMessage();
  } else if (highConfidence.length === 1) {
    return showSingleProposal(highConfidence[0]);
  } else {
    // Multiple high-confidence matches
    return showMultipleProposals(highConfidence);
  }
}
```

### User Presentation for Multiple Matches

```
Claude: "📊 Multiple High-Confidence Matches Found:

Option 1: Warehouse Run (92%)
• 2× trips (820km total)
• GPS match: 98% (within 50m)
• Typical route: Mon/Thu ✓

Option 2: Client Visit Route (78%)
• 4× trips (800km total, 20km uncovered)
• GPS match: 85% (within 400m)
• Mixed purposes (2 business, 2 personal)

Option 3: Custom combination
• 1× Warehouse + 2× Daily Commute
• Coverage: 820km / 820km (100%)

Which option best matches your actual trips?"
```

---

## Batch Trip Creation Workflow

### Step 1: User Approval
```javascript
async function requestApproval(proposals) {
  showProposal(proposals);

  const response = await ask("Accept (yes), modify (edit), or reject (no)?");

  if (response === 'yes') {
    return createTripsFromProposals(proposals);
  } else if (response === 'edit') {
    return modifyProposals(proposals);
  } else {
    return cancelReconstruction();
  }
}
```

### Step 2: Create Trips Batch
```javascript
async function createTripsFromProposals(proposals) {
  const trips = proposals.map(p => ({
    vehicle_id: p.vehicle_id,
    start_checkpoint_id: p.start_checkpoint_id,
    end_checkpoint_id: p.end_checkpoint_id,
    driver_name: await askDriverName(), // Slovak compliance
    trip_start_datetime: p.start_datetime,
    trip_end_datetime: p.end_datetime,
    trip_start_location: p.start_location,
    trip_end_location: p.end_location,
    distance_km: p.distance_km,
    purpose: p.purpose, // "Business" or "Personal"
    business_description: p.business_description,
    reconstruction_method: "template",
    template_id: p.template_id,
    confidence_score: p.confidence
  }));

  const result = await mcp.call("car-log-core.create_trips_batch", {
    trips: trips
  });

  return result;
}
```

### Step 3: Automatic Validation
```javascript
async function validateCreatedTrips(trips, gap) {
  // Validation 1: Distance Sum
  const distanceValidation = await mcp.call("validation.validate_checkpoint_pair", {
    checkpoint1_id: gap.start_checkpoint_id,
    checkpoint2_id: gap.end_checkpoint_id,
    trips: trips
  });

  // Validation 2: Fuel Consumption
  const fuelValidation = await mcp.call("validation.validate_fuel_consumption", {
    checkpoint1_id: gap.start_checkpoint_id,
    checkpoint2_id: gap.end_checkpoint_id
  });

  // Validation 3: Individual Trip Efficiency
  for (const trip of trips) {
    await mcp.call("validation.validate_trip", {
      trip_id: trip.trip_id
    });
  }

  return {
    distance: distanceValidation,
    fuel: fuelValidation
  };
}
```

---

## Complete Orchestration Flow

```typescript
async function performTripReconstruction(gap) {
  // Step 1: Get gap data
  showProgress("Analyzing gap...");
  const gapData = await mcp.call("car-log-core.analyze_gap", {
    checkpoint1_id: gap.start_checkpoint_id,
    checkpoint2_id: gap.end_checkpoint_id
  });

  // Step 2: Fetch templates
  showProgress("Fetching your templates...");
  const templates = await mcp.call("car-log-core.list_templates", {
    vehicle_id: gapData.vehicle_id
  });

  if (templates.length === 0) {
    return suggestManualEntry(gapData);
  }

  // Step 3: Calculate routes (optional enhancement)
  showProgress("Calculating optimal routes...");
  for (const template of templates) {
    if (!template.distance_km) {
      const route = await mcp.call("geo-routing.calculate_route", {
        start: template.from_coords,
        end: template.to_coords
      });
      template.distance_km = route.distance_km;
    }
  }

  // Step 4: Run stateless matching
  showProgress("Running GPS-first matching (70% GPS, 30% address)...");
  const matchResult = await mcp.call("trip-reconstructor.match_templates", {
    gap_data: gapData,
    templates: templates,
    gps_weight: 0.7,
    address_weight: 0.3,
    min_confidence: 0.7
  });

  // Step 5: Present proposals
  const approved = await presentProposals(matchResult.proposals);

  if (!approved) {
    return handleRejection();
  }

  // Step 6: Create trips batch
  showProgress("Creating trips...");
  const trips = await mcp.call("car-log-core.create_trips_batch", {
    trips: approved.trips
  });

  // Step 7: Automatic validation
  showProgress("Running validation checks...");
  const validation = await validateCreatedTrips(trips, gap);

  // Step 8: Show results
  showResults(trips, validation);
}
```

---

## Testing Scenarios

### Test 1: High Confidence Single Match (Happy Path)
```
Input:
- Gap: Bratislava → Košice (820km, 7 days)
- Template: Warehouse Run (Bratislava ↔ Košice, 410km round trip)
- GPS: Within 50m of template endpoints

Expected Flow:
1. Analyze gap → 820km, Mon to Thu
2. Fetch templates → 1 match
3. Calculate match → 92% confidence
4. Present: "2× Warehouse Run"
5. User accepts
6. Create 2 trips
7. Validate → Pass all checks
8. Confirm success

Expected Tools Called:
- car-log-core.analyze_gap
- car-log-core.list_templates
- trip-reconstructor.match_templates
- car-log-core.create_trips_batch
- validation.validate_checkpoint_pair
- validation.validate_trip (2x)

Success Criteria:
✓ 92% confidence displayed
✓ Clear proposal presentation
✓ 2 trips created
✓ Validation passes
✓ User sees success message
```

### Test 2: Medium Confidence (Requires Confirmation)
```
Input:
- Gap: Similar to Warehouse Run, but GPS is 1.2km off
- Confidence: 75%

Expected Flow:
1. Match templates → 75% confidence
2. Present with warning:
   "⚠️ GPS match is approximate (within 1.2km)"
3. Ask: "Is this correct?"
4. User confirms
5. Create trips
6. Validate

Expected Behavior:
- Clear warning shown
- User confirmation required
- Explanation of uncertainty
- Option to modify

Success Criteria:
✓ Confidence 70-89% triggers warning
✓ User can confirm or reject
✓ Explanation is clear
```

### Test 3: No High-Confidence Match
```
Input:
- Gap: 820km
- Templates: Best match is 58% confidence

Expected Flow:
1. Match templates → Best: 58%
2. Show: "No high-confidence match (threshold: 70%)"
3. Options:
   a) Manually describe trips
   b) Create new template
   c) Skip reconstruction
4. User chooses option

Expected Behavior:
- Explain why confidence is low
- Show best match for reference
- Clear options
- No automatic trip creation

Success Criteria:
✓ 70% threshold enforced
✓ Low confidence explained
✓ Options presented
✓ No unwanted trips created
```

### Test 4: Multiple High-Confidence Matches
```
Input:
- Gap: 820km
- Templates:
  - Warehouse Run: 92%
  - Client Circuit: 88%
  - Mixed Route: 78%

Expected Flow:
1. Match templates → 3 matches >= 70%
2. Present all options:
   "Option 1: Warehouse Run (92%)"
   "Option 2: Client Circuit (88%)"
   "Option 3: Mixed Route (78%)"
3. Ask user to select
4. Create trips from selected

Expected Behavior:
- All options shown with confidence
- User can choose best match
- Can reject all options

Success Criteria:
✓ All matches >= 70% shown
✓ Sorted by confidence (descending)
✓ User can choose any option
✓ Clear differentiation
```

### Test 5: Partial Coverage (Gap Not Fully Covered)
```
Input:
- Gap: 820km
- Best match: 2× Warehouse Run = 800km
- Uncovered: 20km

Expected Flow:
1. Match templates → 800km covered
2. Present:
   "Partial coverage: 800km / 820km (98%)
    20km uncovered"
3. Options:
   a) Accept partial (create 800km trips)
   b) Add manual trip for 20km
   c) Try different combination

Expected Behavior:
- Clearly show coverage gap
- Explain uncovered distance
- Offer to add manual trip
- Show percentage coverage

Success Criteria:
✓ Coverage percentage shown
✓ Uncovered distance highlighted
✓ Options for handling gap
```

### Test 6: Round Trip Detection
```
Input:
- Gap: Bratislava → Košice → Bratislava
- Template: Warehouse Run (round trip enabled)

Expected Flow:
1. Detect gap endpoints match (both Bratislava)
2. Match round trip template
3. Present: "1× Warehouse Run (round trip)"
4. Create 2 trips (outbound + return)

Expected Behavior:
- Detect same start/end location
- Match round trip templates
- Create both directions
- Show as single "round trip"

Success Criteria:
✓ Round trip detected
✓ Both directions created
✓ Presented as one unit
```

### Test 7: Day-of-Week Bonus
```
Input:
- Gap: Monday & Thursday
- Template: Warehouse Run (typical days: Mon/Thu)

Expected Flow:
1. Base GPS match: 87%
2. Apply day bonus: +5%
3. Final confidence: 92%
4. Show: "✓ Day-of-week matches template"

Expected Behavior:
- Bonus applied for day match
- Shown in confidence breakdown
- Explained to user

Success Criteria:
✓ Day match bonus applied
✓ Shown in UI
✓ Confidence increased
```

### Test 8: Distance Variance Check
```
Input:
- Gap: 820km
- Template: 410km × 2 = 820km (exact match)

Expected Flow:
1. Calculate expected: 820km
2. Actual gap: 820km
3. Variance: 0%
4. Show: "✓ Distance matches exactly"
5. Apply distance bonus: +5%

Expected Behavior:
- Distance compared
- Variance calculated
- Bonus for close match (<10km)

Success Criteria:
✓ Distance variance shown
✓ Bonus applied if <10km
✓ Explained to user
```

### Test 9: Validation Failure After Creation
```
Input:
- Trips created successfully
- Validation: Fuel consumption +25% (exceeds 15% threshold)

Expected Flow:
1. Create trips → Success
2. Validate fuel → Warning (25% over expected)
3. Show:
   "⚠️ Fuel consumption higher than expected
    Expected: 69.7L
    Actual: 87.1L (+25%)

    Possible causes:
    - Heavy traffic
    - AC usage
    - Vehicle load

    Keep trips or review?"

Expected Behavior:
- Trips created but flagged
- Validation warnings shown
- Explanation provided
- User can review/adjust

Success Criteria:
✓ Validation runs automatically
✓ Warnings don't block creation
✓ Clear explanation
✓ User can review
```

### Test 10: No Templates (First-Time User)
```
Input:
- Gap detected
- No templates exist

Expected Flow:
1. Fetch templates → Empty list
2. Show:
   "No templates found. Let's create one!

    This gap:
    • From: Bratislava (48.14°N, 17.10°E)
    • To: Košice (48.71°N, 21.26°E)
    • Distance: 410km

    Create template for this route?"
3. If yes: Create template from gap
4. If no: Manual entry

Expected Behavior:
- Suggest template creation
- Use gap data as template
- Offer manual alternative

Success Criteria:
✓ Empty template list handled
✓ Template creation suggested
✓ Gap data used for template
✓ Manual option available
```

---

## MCP Tool Call Examples

### Example 1: Analyze Gap
```json
// Request
{
  "tool": "car-log-core.analyze_gap",
  "parameters": {
    "checkpoint1_id": "chk-456-abc-789",
    "checkpoint2_id": "chk-789-xyz-012"
  }
}

// Response
{
  "success": true,
  "gap": {
    "start_checkpoint": {
      "checkpoint_id": "chk-456-abc-789",
      "datetime": "2025-11-01T08:00:00Z",
      "odometer_km": 45000,
      "location": {
        "coords": {"latitude": 48.7164, "longitude": 21.2611},
        "address": "OMV Station, Košice"
      }
    },
    "end_checkpoint": {
      "checkpoint_id": "chk-789-xyz-012",
      "datetime": "2025-11-18T14:25:00Z",
      "odometer_km": 45820,
      "location": {
        "coords": {"latitude": 48.1486, "longitude": 17.1077},
        "address": "OMV Station, Bratislava"
      }
    },
    "distance_km": 820,
    "duration_days": 7,
    "vehicle_id": "abc-123-def-456"
  }
}
```

### Example 2: Match Templates
```json
// Request
{
  "tool": "trip-reconstructor.match_templates",
  "parameters": {
    "gap_data": {
      "start_coords": {"latitude": 48.7164, "longitude": 21.2611},
      "end_coords": {"latitude": 48.1486, "longitude": 17.1077},
      "start_address": "Košice",
      "end_address": "Bratislava",
      "distance_km": 820,
      "start_datetime": "2025-11-01T08:00:00Z"
    },
    "templates": [
      {
        "template_id": "tpl-123",
        "name": "Warehouse Run",
        "from_coords": {"latitude": 48.1486, "longitude": 17.1077},
        "to_coords": {"latitude": 48.7164, "longitude": 21.2611},
        "distance_km": 410,
        "is_round_trip": true,
        "typical_days": ["Monday", "Thursday"]
      }
    ],
    "gps_weight": 0.7,
    "address_weight": 0.3,
    "min_confidence": 0.7
  }
}

// Response
{
  "success": true,
  "proposals": [
    {
      "template_id": "tpl-123",
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
          "trip_end_datetime": "2025-11-01T12:30:00Z"
        },
        {
          "trip_start_location": "Košice",
          "trip_end_location": "Bratislava",
          "distance_km": 410,
          "trip_start_datetime": "2025-11-06T14:00:00Z",
          "trip_end_datetime": "2025-11-06T18:30:00Z"
        }
      ],
      "coverage_km": 820,
      "coverage_percent": 100
    }
  ]
}
```

### Example 3: Create Trips Batch
```json
// Request
{
  "tool": "car-log-core.create_trips_batch",
  "parameters": {
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
        "template_id": "tpl-123",
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
        "template_id": "tpl-123",
        "confidence_score": 92
      }
    ]
  }
}

// Response
{
  "success": true,
  "trips_created": 2,
  "trips": [
    {
      "trip_id": "trip-001",
      "vehicle_id": "abc-123-def-456",
      "distance_km": 410,
      "confidence_score": 92
    },
    {
      "trip_id": "trip-002",
      "vehicle_id": "abc-123-def-456",
      "distance_km": 410,
      "confidence_score": 92
    }
  ]
}
```

### Example 4: Validate Checkpoint Pair
```json
// Request
{
  "tool": "validation.validate_checkpoint_pair",
  "parameters": {
    "checkpoint1_id": "chk-456-abc-789",
    "checkpoint2_id": "chk-789-xyz-012"
  }
}

// Response
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

---

## User Communication Patterns

### Pattern 1: Confidence Explanation
```
Always explain confidence score components:

"92% confidence breakdown:
• GPS match: 98% (within 50m) → 68.6 points (70% weight)
• Address match: 75% (city names match) → 22.5 points (30% weight)
• Day-of-week bonus: +5 points
• Distance match bonus: +5 points
Total: 92%"
```

### Pattern 2: Clear Options
```
Always give user clear choices:

"What would you like to do?
1️⃣ Accept proposal (2 trips created)
2️⃣ Modify proposal (adjust trips)
3️⃣ Reject (manual entry instead)

Reply with 1, 2, or 3:"
```

### Pattern 3: Validation Results
```
Always show validation in accessible format:

"✅ Validation Passed:
• Distance: 820km / 820km (0% variance) ✓
• Fuel: 72.8L / 69.7L (+4.4%, within 15% threshold) ✓
• Efficiency: 8.9 L/100km (Diesel range: 5-15) ✓

Your trips are ready for tax reporting!"
```

---

**Implementation:** 📋 Specification ready, implementation pending
**Estimated Effort:** 5 hours
**Dependencies:** car-log-core ✅, trip-reconstructor ✅, geo-routing ✅, validation ✅
