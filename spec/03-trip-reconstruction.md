# Trip Reconstruction Algorithm

**Version:** 2.0
**Date:** 2025-11-17
**Status:** Draft - In Discussion

---

## Overview

This document specifies the **Trip Reconstruction Algorithm**, the core differentiator of Car Log. Instead of manually logging every trip, users create checkpoints (odometer readings + optional receipts), and the system intelligently reconstructs individual trips.

**Key Innovation:** Hybrid reconstruction combining user memory, recurring patterns (templates), and geo-routing analysis.

---

## Algorithm Goals

1. **Minimize User Effort** - Reconstruct trips from minimal checkpoint data
2. **Maximize Accuracy** - Use multiple data sources for validation
3. **Maintain Flexibility** - Support mixed reconstruction modes
4. **Ensure Transparency** - Always show user what's being created
5. **Enable Correction** - Allow manual override at any step

---

## High-Level Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. USER CREATES CHECKPOINT                              │
│    Odometer: 45,850km (Nov 15, Košice)                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. SYSTEM ANALYZES GAP                                  │
│    Previous checkpoint: 45,320km (Nov 8, Bratislava)   │
│    Gap: 530km over 7 days                              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. SYSTEM PROMPTS USER                                  │
│    "You drove 530km. Would you like to:                │
│     A) Tell me specific trips you remember              │
│     B) Let me fill in using your trip templates         │
│     C) Reconstruct later"                               │
└─────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
    [A: Manual]      [B: Template-based]      [C: Skip]
         ↓                    ↓                    ↓
┌──────────────┐    ┌──────────────────┐    ┌──────────┐
│ Interactive  │    │ Auto-fill with   │    │ Mark as  │
│ Trip Entry   │    │ templates +      │    │ "To Do"  │
│              │    │ geo-routing      │    │          │
└──────────────┘    └──────────────────┘    └──────────┘
         ↓                    ↓
┌─────────────────────────────────────────────────────────┐
│ 4. USER REVIEWS & APPROVES                              │
│    System shows proposed trips                          │
│    User confirms or makes corrections                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 5. TRIPS CREATED & STORED                               │
│    All trips linked to bounding checkpoints             │
│    Statistics updated (fuel efficiency, totals)         │
└─────────────────────────────────────────────────────────┘
```

---

## Mode A: User-Specified Trips (Manual)

### Purpose
User explicitly remembers specific journeys and provides details.

### When to Use
- User has clear memory of major trips
- Unusual/one-time trips not covered by templates
- High-value trips requiring detailed documentation

### Flow

```
System: "You drove 530km between Nov 8-15. Do you remember any specific trips?"

User: "Yes, I went to Košice on Nov 12, that was about 410km round trip"

System: "Got it. Let me create that trip:
         • Date: Nov 12, 2025
         • Route: Bratislava → Košice → Bratislava
         • Distance: 410km (you specified)

         Was this for business or personal?"

User: "Business - warehouse pickup"

System: "Perfect! Trip created.

         You have 120km unaccounted for between Nov 8-15.
         Should I:
         A) Ask you about other trips
         B) Fill with templates
         C) Mark as local driving"

User: "C - local driving"

System: "Done! Created 2 trips:
         1. Košice warehouse run (410km, Business)
         2. Local driving (120km, needs classification)

         Would you like to classify the local driving now?"
```

### Acceptance Criteria

**AC-MANUAL-1: User Trip Entry**
- Given user wants to specify a trip manually
- When user provides trip details (date, distance, destination, purpose)
- Then system creates trip entry with exact specifications
- And links trip to bounding checkpoints
- And calculates remaining gap

**AC-MANUAL-2: Partial Gap Filling**
- Given user specifies trips that don't fill entire gap
- When remaining gap < 50km
- Then system suggests "local driving" classification
- When remaining gap ≥ 50km
- Then system prompts for additional trips

**AC-MANUAL-3: Mixed Mode Support**
- Given user has specified some trips manually
- When gap remains
- Then system offers to fill remainder with templates
- And user can accept/reject template suggestions

---

## Mode B: Template-Based Reconstruction

### Purpose
Automatically fill gaps using user's recurring trip patterns.

### When to Use
- Gap consists of typical/recurring trips
- User doesn't remember specific details
- Time period matches template usage patterns

### Inputs Required
1. Distance gap (from checkpoint odometer delta)
2. Time gap (from checkpoint timestamps)
3. User's trip templates
4. Checkpoint GPS locations (if available)

### Orchestration Architecture

**IMPORTANT DESIGN PRINCIPLE:**

The trip reconstruction algorithm is implemented as a **stateless service** in the `trip-reconstructor` MCP server. It does NOT access the database or call other MCP servers directly.

**Orchestration Pattern:**
```
┌────────────────────────────────────────────────────┐
│  ORCHESTRATOR                                      │
│  (Claude Skill in Claude Desktop)                  │
│  (DSPy Module in Gradio App)                       │
│                                                    │
│  Responsibilities:                                 │
│  1. Fetch checkpoints from sqlite                  │
│  2. Fetch templates from car-log-core              │
│  3. Calculate geo-routes from geo-routing          │
│  4. Pass ALL data to trip-reconstructor            │
│  5. Present results to user                        │
│  6. Create trips via car-log-core after approval   │
└────────────────────────────────────────────────────┘
              ↓         ↓         ↓         ↓
   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ sqlite   │ │ car-log  │ │   geo-   │ │  trip-   │
   │          │ │  -core   │ │ routing  │ │ recon.   │
   └──────────┘ └──────────┘ └──────────┘ └──────────┘
```

**Why Stateless?**
- **Single Responsibility** - Reconstruction logic separated from data access
- **Testability** - Easy to test with mock data
- **Reusability** - Can be used by both Claude Skills and Gradio app
- **No Hidden Dependencies** - All inputs explicit in function signature

**Data Flow Example:**
```python
# 1. Orchestrator gathers data
checkpoints = sqlite.query("SELECT * FROM checkpoints WHERE ...")
templates = car_log_core.list_templates(vehicle_id)
geo_routes = geo_routing.calculate_route(start_coords, end_coords)

# 2. Orchestrator calls stateless reconstructor
matches = trip_reconstructor.match_templates(
    gap_data={
        "distance_km": 530,
        "start_coords": {"lat": 48.1486, "lng": 17.1077},
        "end_coords": {"lat": 48.7164, "lng": 21.2611},
        "start_address": "Bratislava",
        "end_address": "Košice",
        "start_date": "2025-11-08",
        "end_date": "2025-11-15"
    },
    templates=templates,  # Full template objects
    geo_routes=geo_routes  # Full route data
)

# 3. Orchestrator presents to user and creates trips after approval
for match in matches:
    car_log_core.create_trip(...)
```

---

### Algorithm Steps

#### Step 1: Gather Context

```python
def analyze_gap(start_checkpoint, end_checkpoint):
    """
    Calculate gap and gather context for reconstruction
    """
    distance_gap = end_checkpoint.odometer - start_checkpoint.odometer
    time_gap = end_checkpoint.timestamp - start_checkpoint.timestamp

    context = {
        "distance_km": distance_gap,
        "days": time_gap.days,
        "start_location": start_checkpoint.location,  # GPS or null
        "end_location": end_checkpoint.location,      # GPS or null
        "start_date": start_checkpoint.timestamp,
        "end_date": end_checkpoint.timestamp
    }

    return context
```

#### Step 2: Geo-Routing Analysis (if GPS available)

```python
def calculate_geo_routes(start_coords, end_coords):
    """
    Call OpenStreetMap routing API to get possible routes
    """
    # Call OSRM (Open Source Routing Machine)
    request = {
        "coordinates": [
            [start_coords.lng, start_coords.lat],
            [end_coords.lng, end_coords.lat]
        ],
        "alternatives": 3,      # Get up to 3 route options
        "steps": True,          # Include turn-by-turn
        "overview": "full"      # Full route geometry
    }

    response = osrm_api.route(request)

    routes = []
    for route in response.routes:
        routes.append({
            "distance_km": route.distance / 1000,
            "duration_hours": route.duration / 3600,
            "via_cities": extract_waypoints(route.steps),
            "route_type": classify_route(route),  # highway, local, mixed
            "confidence": calculate_confidence(route)
        })

    return routes
```

#### Step 3: Template Matching

```python
def match_templates_to_gap(templates, gap_context, geo_routes=None):
    """
    Find templates that fit the gap using hybrid GPS + address matching

    IMPORTANT: This is a STATELESS function in the trip-reconstructor MCP server.
    It receives ALL required data as parameters and doesn't access database.
    The orchestrator (Claude Skill or DSPy module) must gather and provide all data.
    """
    matches = []

    for template in templates:
        match_score = 0

        # Distance matching (50 points max)
        distance_diff = abs(template.distance_km - gap_context.distance_km)
        distance_tolerance = gap_context.distance_km * 0.10  # 10%

        if distance_diff <= distance_tolerance:
            match_score += 50

            # HYBRID LOCATION MATCHING (40 points max)
            # GPS coordinates are MANDATORY in templates (source of truth)
            # Addresses are OPTIONAL (human labels that enhance matching)
            if template.from_coords and template.to_coords:
                # GPS matching (28 points = 70% of 40 points)
                start_gps_score = calculate_gps_match(
                    template.from_coords,
                    gap_context.start_coords,
                    max_score=100
                ) if gap_context.start_coords else 0

                end_gps_score = calculate_gps_match(
                    template.to_coords,
                    gap_context.end_coords,
                    max_score=100
                ) if gap_context.end_coords else 0

                gps_score = ((start_gps_score + end_gps_score) / 2) * 0.28

                # Address matching (12 points = 30% of 40 points)
                address_score = 0
                if template.from_address and gap_context.start_address:
                    start_addr_score = calculate_string_similarity(
                        template.from_address,
                        gap_context.start_address
                    )
                else:
                    start_addr_score = 0

                if template.to_address and gap_context.end_address:
                    end_addr_score = calculate_string_similarity(
                        template.to_address,
                        gap_context.end_address
                    )
                else:
                    end_addr_score = 0

                address_score = ((start_addr_score + end_addr_score) / 2) * 0.12

                # Combined location score (GPS 70% + Address 30%)
                match_score += (gps_score + address_score)

            # Day-of-week matching (10 points max)
            if template.typical_days:
                matching_days = count_matching_days(
                    gap_context.start_date,
                    gap_context.end_date,
                    template.typical_days
                )
                if matching_days > 0:
                    match_score += 10

            matches.append({
                "template": template,
                "confidence": match_score,
                "suggested_count": calculate_count(template, gap_context)
            })

    # Sort by confidence score
    matches.sort(key=lambda x: x["confidence"], reverse=True)

    return matches


def calculate_gps_match(coord1, coord2, max_score=100):
    """
    Calculate GPS matching score based on distance
    Uses Haversine formula for distance calculation

    Returns: 0-100 score based on distance
      < 100m = 100 points
      < 500m = 90 points
      < 1km = 70 points
      < 5km = 40 points
      > 5km = 0 points
    """
    distance_m = haversine_distance(coord1, coord2)

    if distance_m < 100:
        return 100
    elif distance_m < 500:
        return 90
    elif distance_m < 1000:
        return 70
    elif distance_m < 5000:
        return 40
    else:
        return 0


def calculate_string_similarity(str1, str2):
    """
    Calculate string similarity using Levenshtein distance
    Returns: 0-100 score (100 = identical, 0 = completely different)
    """
    # Normalize strings (lowercase, trim)
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()

    # Calculate Levenshtein distance
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 100

    distance = levenshtein_distance(s1, s2)
    similarity = (1 - distance / max_len) * 100

    return max(0, similarity)
```

#### Step 4: Propose Template Combination

```python
def propose_reconstruction(gap_context, template_matches):
    """
    Find best combination of templates to fill gap
    """
    distance_remaining = gap_context.distance_km
    days_available = gap_context.days

    proposal = []

    # Start with highest confidence matches
    for match in template_matches:
        template = match["template"]

        # Calculate how many times this template fits
        max_count_by_distance = distance_remaining // template.distance_km

        # Constrain by time (if template has day restrictions)
        if template.typical_days:
            max_count_by_days = count_matching_days(
                gap_context.start_date,
                gap_context.end_date,
                template.typical_days
            )
            count = min(max_count_by_distance, max_count_by_days)
        else:
            count = max_count_by_distance

        if count > 0:
            proposal.append({
                "template": template,
                "count": count,
                "total_km": count * template.distance_km,
                "confidence": match["confidence"]
            })

            distance_remaining -= (count * template.distance_km)

        # Stop if gap is mostly filled
        if distance_remaining < 50:
            break

    # Handle remainder
    if distance_remaining > 0:
        proposal.append({
            "type": "unaccounted",
            "distance_km": distance_remaining,
            "description": "Local driving or unmapped trips",
            "needs_classification": distance_remaining >= 50
        })

    return proposal
```

#### Step 5: Present to User

```python
def present_reconstruction_proposal(proposal, gap_context):
    """
    Format proposal for user review
    """
    message = f"Between {gap_context.start_date} and {gap_context.end_date}, "
    message += f"you drove {gap_context.distance_km}km.\n\n"
    message += "Here's my reconstruction estimate:\n\n"

    for item in proposal:
        if item.get("template"):
            template = item["template"]
            message += f"✓ {item['count']}× {template.name} "
            message += f"({item['count']} × {template.distance_km}km = {item['total_km']}km)\n"

            if item["confidence"] >= 90:
                message += f"  ↳ High confidence (GPS + distance match)\n"
            elif item["confidence"] >= 70:
                message += f"  ↳ Medium confidence (distance match)\n"

        elif item.get("type") == "unaccounted":
            message += f"\n⚠ Remainder: {item['distance_km']}km\n"
            message += f"  ↳ Suggested: {item['description']}\n"

    message += f"\n\nTotal: {gap_context.distance_km}km\n"
    message += "\nDoes this match your memory?"

    return message
```

### Example Reconstruction

**Scenario:**
```
Gap: 730km, Nov 1-8 (7 days)
Start Checkpoint: GPS (48.1486, 17.1077), Address: "Bratislava"
End Checkpoint: GPS (48.7164, 21.2611), Address: "Košice"

Templates available (GPS coordinates mandatory, addresses optional):
1. "Warehouse Run"
   - From: (48.1486, 17.1077) "Main Office, Bratislava"
   - To: (48.7164, 21.2611) "Warehouse, Košice"
   - Distance: 410km, Days: [Monday, Thursday]

2. "Daily Commute"
   - From: (48.1850, 17.1250) "Home"
   - To: (48.1486, 17.1077) "Office, Bratislava"
   - Distance: 25km, Days: [Mon-Fri]

3. "Client Visit"
   - From: (48.1486, 17.1077) "Office"
   - To: (48.6500, 17.9000) "Client Site"
   - Distance: 120km, no day restrictions
```

**Step-by-step:**

```
1. CALCULATE GEO-ROUTES
   → Route 1: Bratislava to Košice via D1: 395km
   → Route 2: Bratislava to Košice via E50: 410km ✓ Matches template!
   → Route 3: Local roads: 385km

2. MATCH TEMPLATES (using hybrid GPS 70% + address 30% algorithm)
   → "Warehouse Run": 410km
     GPS Match: Start (48.1486, 17.1077) = exact match (100 points)
                End (48.7164, 21.2611) = exact match (100 points)
     Address Match: "Bratislava" vs "Main Office, Bratislava" = 60 points
                    "Košice" vs "Warehouse, Košice" = 50 points
     Final Location Score: (100 × 0.7) + (55 × 0.3) = 86.5 points
     Typical day Monday in date range: +10 points
     Total Confidence: 50 (distance) + 35 (location) + 10 (day) = 95%
     Count: 1× (fits exactly, and Monday is in date range)

   → "Daily Commute": 25km, 5 work days in period
     GPS Match: Start (48.1850, 17.1250) vs checkpoint start (48.1486, 17.1077)
                Distance ~3.5km = 40 points (< 5km threshold)
     No address match (checkpoint has city-level address only)
     Location Score: (40 × 0.7) + (0 × 0.3) = 28 points
     Typical days Mon-Fri: +10 points
     Total Confidence: 50 (distance) + 28 (location) + 10 (day) = 88%
     Count: 6× possible (150km total)

   → "Client Visit": 120km
     GPS Match: Partial match (office location matches start)
     Location Score: ~35 points
     Total Confidence: 50 (distance) + 35 (location) = 85%
     Count: 1× (120km)

3. PROPOSE COMBINATION
   • 1× Warehouse Run (410km) - Mon Nov 4
   • 6× Daily Commute (150km) - Mon-Fri + Sat
   • 1× Client Visit (120km) - Wed Nov 6
   • Remainder: 50km → Local driving

   Total: 730km ✓

4. PRESENT TO USER
   "Between Nov 1-8, you drove 730km from Bratislava to Košice.

   Here's my reconstruction estimate:

   ✓ 1× Warehouse Run (410km)
     ↳ High confidence (GPS + distance match for Nov 4)

   ✓ 6× Daily Commute (150km total)
     ↳ Medium confidence (typical work week)

   ✓ 1× Client Visit (120km)
     ↳ Medium confidence (weekly pattern)

   ⚠ Remainder: 50km
     ↳ Suggested: Local driving

   Total: 730km

   Does this match your memory?"

5. USER RESPONSE OPTIONS
   A) "Yes, looks good" → Create all trips
   B) "No, I only did 5 commutes" → Adjust and recalculate
   C) "Let me tell you exactly what I did" → Switch to manual mode
```

### Acceptance Criteria

**AC-TEMPLATE-1: Template Selection**
- Given user has trip templates defined
- When reconstruction is triggered
- Then system identifies templates that fit gap
- And ranks by confidence score (distance + GPS + day-of-week)

**AC-TEMPLATE-2: Geo-Route Matching**
- Given checkpoints have GPS coordinates
- When templates have GPS coordinates
- Then system calculates routes via OpenStreetMap
- And matches templates to routes within 10% distance tolerance
- And within 500m location tolerance

**AC-TEMPLATE-3: Multiple Template Combination**
- Given no single template fills entire gap
- When multiple templates are available
- Then system proposes combination of templates
- And handles remainder (<50km as local, ≥50km prompts user)

**AC-TEMPLATE-4: User Confirmation Required**
- Given system proposes template-based reconstruction
- When presenting to user
- Then system shows all proposed trips with confidence levels
- And user must approve before creation
- And user can edit counts/templates

**AC-TEMPLATE-5: Confidence Scoring**
- Given template matching is performed
- When calculating confidence
- Then GPS match + distance match = 90%+ (High)
- And distance match only = 70-89% (Medium)
- And loose match = <70% (Low, show warning)

---

## Mode C: Skip Reconstruction

### Purpose
Defer reconstruction for later (user is busy or unsure).

### Flow

```
System: "You drove 530km. Would you like to reconstruct trips now?"

User: "Not now, I'll do it later"

System: "No problem! I've marked this gap as pending.
         You can reconstruct it anytime by saying:
         'Reconstruct trips from Nov 8 to Nov 15'"
```

### Acceptance Criteria

**AC-SKIP-1: Mark as Pending**
- Given user chooses to skip reconstruction
- When checkpoint is created
- Then system marks gap as "pending reconstruction"
- And user can trigger reconstruction later via command

**AC-SKIP-2: Pending List**
- Given user has pending reconstructions
- When user asks "What needs reconstruction?"
- Then system lists all pending gaps with date ranges and distances

---

## On-Demand Reconstruction

### Trigger Commands

User can request reconstruction at any time:

```
"Reconstruct trips from last week"
"Reconstruct my November trips"
"Reconstruct from Nov 1 to Nov 15"
"Fill in missing trips for Ford Transit"
```

### Flow

```
User: "Reconstruct my trips from last week"

System: [Analyzes all checkpoints from last 7 days]
        "I found 2 gaps to reconstruct:

        Gap 1: Nov 8-15, 530km (Bratislava → Košice)
        Gap 2: Nov 16-17, 50km (Košice area)

        Should I reconstruct both or one at a time?"

User: "Both"

System: [Runs reconstruction algorithm for each gap]
        [Presents combined proposal]
```

### Acceptance Criteria

**AC-ONDEMAND-1: Time Range Support**
- Given user specifies time range
- When system searches for gaps
- Then all checkpoint gaps in range are identified
- And user can choose which to reconstruct

**AC-ONDEMAND-2: Vehicle Filtering**
- Given user has multiple vehicles
- When requesting reconstruction
- Then user can specify vehicle
- And system only processes that vehicle's gaps

---

## Edge Cases & Error Handling

### Case 1: Templates Don't Fit

**Scenario:** No template combination fills gap adequately

```
Gap: 200km
Templates:
  • Daily Commute: 25km (8× = 200km, but only 5 work days)
  • Warehouse Run: 410km (too large)

System: "Your templates don't fit this gap well.

         Option A: Use 5× Daily Commute (125km) + 75km unaccounted
         Option B: Tell me specific trips you made
         Option C: Create new template for this route

         Which would you prefer?"
```

**AC-EDGE-1: Poor Template Fit Warning**
- Given template combination has low confidence (<60%)
- When presenting reconstruction
- Then system warns user about uncertainty
- And suggests manual entry or new template creation

---

### Case 2: GPS Data Missing

**Scenario:** Checkpoints don't have GPS coordinates

```
Gap: 410km (no GPS data)

System: "You drove 410km, but I don't have location data
         to suggest routes.

         Your templates that might fit:
         • Warehouse Run (410km) - exact match!
         • 2× Client Visit (200km each = 400km)

         Which makes sense for this period?"
```

**AC-EDGE-2: No GPS Fallback**
- Given checkpoints lack GPS data
- When reconstruction is triggered
- Then system relies on distance matching only
- And confidence scores reduced by 30 points

---

### Case 3: Conflicting Templates

**Scenario:** Multiple templates match with equal confidence

```
Gap: 120km, Wednesday

Templates:
  • Client Visit (120km, no day restriction) - 80% confidence
  • Supplier Run (115km, Wednesdays) - 80% confidence

System: "I found 2 equally likely templates:

         1. Client Visit (120km)
         2. Supplier Run (115km, typical for Wednesdays)

         Which one did you do, or was it something else?"
```

**AC-EDGE-3: Template Disambiguation**
- Given multiple templates match with similar confidence (±10%)
- When presenting to user
- Then system asks user to choose
- And provides context for each option

---

### Case 4: Unrealistic Gap

**Scenario:** Gap distance is impossible for time period

```
Gap: 1500km in 1 day (unrealistic for typical use)

System: "⚠️ Warning: This is an unusually long distance (1500km in 24 hours).

         Possible issues:
         • Incorrect odometer reading
         • Checkpoint timestamp wrong
         • Vehicle transported (ferry, truck)

         Would you like to:
         A) Edit the checkpoint data
         B) Confirm this is correct (long-distance trip)
         C) Mark as vehicle transport event"
```

**AC-EDGE-4: Anomaly Detection**
- Given gap exceeds realistic limits (>1000km/day or <1km/day)
- When analyzing gap
- Then system warns user of possible data error
- And offers correction options before reconstruction

---

## Algorithm Performance Metrics

### Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Reconstruction Accuracy** | 90%+ | Distance match between proposed and actual |
| **GPS Match Rate** | 95%+ | Template location matches checkpoint GPS |
| **User Approval Rate** | 85%+ | Proposals accepted without modification |
| **Template Reuse** | 70%+ | Gaps filled with templates vs. manual |
| **Remainder Size** | <5% | Unaccounted distance as % of total gap |

### Performance Targets

- **Reconstruction Time:** <3 seconds for gap analysis
- **Geo-Routing API:** <1 second per route calculation
- **Template Matching:** <500ms for 100 templates

---

## Validation Algorithms with Thresholds

This section defines the 4 validation algorithms that ensure data integrity and credibility. Each algorithm has specific thresholds and concrete error messages.

### Algorithm 1: Distance Sum Validation

**Purpose:** Verify that reconstructed trip distances match the odometer delta

**Threshold:** ±10% acceptable variance

**Rationale:** Accounts for rounding, short local trips, odometer accuracy

```javascript
function validate_distance_sum(trips, actual_odometer_delta) {
  const total_trip_distance = trips.reduce((sum, trip) => sum + trip.distance, 0);
  const variance_percent = Math.abs(total_trip_distance - actual_odometer_delta) / actual_odometer_delta * 100;

  const THRESHOLD = 10; // 10% tolerance

  if (variance_percent <= THRESHOLD) {
    return { status: "ok", variance: variance_percent };
  } else {
    return {
      status: "warning",
      variance: variance_percent,
      message: `Trip distances total ${total_trip_distance}km, but odometer shows ${actual_odometer_delta}km. Difference: ${variance_percent.toFixed(1)}%`,
      suggestion: "Add missing trips or check odometer readings"
    };
  }
}
```

### Algorithm 2: Fuel Consumption Validation

**Purpose:** Verify that calculated fuel consumption matches actual fuel purchased

**Threshold:** ±15% acceptable variance

**Rationale:** Fuel efficiency varies with driving conditions, load, weather

```javascript
function validate_fuel_consumption(trips, actual_fuel_liters, vehicle_avg_efficiency_l_per_100km) {
  const total_distance = trips.reduce((sum, trip) => sum + trip.distance, 0);
  const expected_fuel_liters = (total_distance / 100) * vehicle_avg_efficiency_l_per_100km;
  const variance_percent = Math.abs(expected_fuel_liters - actual_fuel_liters) / actual_fuel_liters * 100;

  const THRESHOLD = 15; // 15% tolerance

  if (variance_percent <= THRESHOLD) {
    return { status: "ok", variance: variance_percent };
  } else {
    return {
      status: "warning",
      variance: variance_percent,
      expected_fuel: expected_fuel_liters,
      actual_fuel: actual_fuel_liters,
      message: `Expected ${expected_fuel_liters.toFixed(1)}L based on distance, but you refueled ${actual_fuel_liters}L. Difference: ${variance_percent.toFixed(1)}%`,
      suggestion: "Vehicle efficiency may have changed (weather, driving style, load)"
    };
  }
}
```

### Algorithm 3: Efficiency Reasonability Check

**Purpose:** Ensure fuel efficiency is within realistic bounds

**Thresholds:** Fuel-type specific ranges

**Rationale:** Different fuels have different typical efficiency ranges

```javascript
function check_efficiency_reasonability(efficiency_l_per_100km, fuel_type) {
  const ranges = {
    "Diesel": { min: 5.0, max: 15.0 },
    "Gasoline": { min: 6.0, max: 20.0 },
    "LPG": { min: 8.0, max: 25.0 },
    "Hybrid": { min: 3.0, max: 8.0 },
    "Electric": { min: 12.0, max: 25.0 }  // kWh/100km
  };

  const range = ranges[fuel_type] || { min: 4.0, max: 20.0 };

  if (efficiency_l_per_100km < range.min) {
    return {
      status: "error",
      message: `Efficiency ${efficiency_l_per_100km} L/100km is unrealistically LOW for ${fuel_type}. Check distance or fuel quantity.`,
      expected_range: range
    };
  } else if (efficiency_l_per_100km > range.max) {
    return {
      status: "error",
      message: `Efficiency ${efficiency_l_per_100km} L/100km is unrealistically HIGH for ${fuel_type}. Check distance or fuel quantity.`,
      expected_range: range
    };
  } else {
    return { status: "ok", efficiency: efficiency_l_per_100km };
  }
}
```

### Algorithm 4: Deviation from Vehicle Average

**Purpose:** Detect unusual trips that deviate significantly from vehicle's historical average

**Threshold:** 20% deviation triggers warning

**Rationale:** Alerts user to unusual trips while allowing for normal variation

```javascript
function check_deviation_from_average(trip_efficiency_l_per_100km, vehicle_avg_efficiency_l_per_100km) {
  const deviation_percent = Math.abs(trip_efficiency_l_per_100km - vehicle_avg_efficiency_l_per_100km) / vehicle_avg_efficiency_l_per_100km * 100;

  const WARNING_THRESHOLD = 20; // 20% deviation

  if (deviation_percent > WARNING_THRESHOLD) {
    return {
      status: "warning",
      deviation: deviation_percent,
      message: `Trip efficiency ${trip_efficiency_l_per_100km} L/100km differs by ${deviation_percent.toFixed(0)}% from your average ${vehicle_avg_efficiency_l_per_100km} L/100km`,
      suggestion: "This could be normal (highway vs city, load, weather) or indicate data entry error"
    };
  } else {
    return { status: "ok", deviation: deviation_percent };
  }
}
```

### Validation Configuration

All validation thresholds should be configurable:

```json
{
  "validation_config": {
    "distance_variance_percent": 10,
    "consumption_variance_percent": 15,
    "efficiency_deviation_percent": 20,
    "efficiency_ranges": {
      "Diesel": { "min_l_per_100km": 5.0, "max_l_per_100km": 15.0 },
      "Gasoline": { "min_l_per_100km": 6.0, "max_l_per_100km": 20.0 },
      "LPG": { "min_l_per_100km": 8.0, "max_l_per_100km": 25.0 },
      "Hybrid": { "min_l_per_100km": 3.0, "max_l_per_100km": 8.0 }
    }
  }
}
```

### Validation Result Data Structures

```typescript
type ValidationStatus = "ok" | "warning" | "error";

interface ValidationResult {
  status: ValidationStatus;
  variance?: number;
  deviation?: number;
  message?: string;
  suggestion?: string;
  expected_range?: { min: number; max: number };
  expected_fuel?: number;
  actual_fuel?: number;
}

interface TripValidation {
  status: "validated" | "has_warnings" | "has_errors";
  distance_check: ValidationResult;
  efficiency_check: ValidationResult;
  deviation_check: ValidationResult;
  warnings: string[];
  errors: string[];
}
```

---

## Related Documents

- [01-product-overview.md](./01-product-overview.md) - Product vision and scope
- [02-domain-model.md](./02-domain-model.md) - Core concepts and terminology
- [04-data-model.md](./04-data-model.md) - JSON file schemas
- [05-claude-skills-dspy.md](./05-claude-skills-dspy.md) - Dual interface architecture
- [06-mcp-architecture-v2.md](./06-mcp-architecture-v2.md) - MCP server architecture
- [07-mcp-api-specifications.md](./07-mcp-api-specifications.md) - Complete API tool definitions

---

## Future Enhancements (P2)

1. **Machine Learning Template Suggestions**
   - Analyze historical patterns
   - Auto-suggest new templates based on frequency
   - Predict future trips

2. **Fuel Efficiency Correlation**
   - Use fuel consumption to validate distance calculations
   - Detect anomalies (towing, AC usage, terrain)

3. **Calendar Integration**
   - Match gaps to calendar events
   - "Nov 12 meeting in Košice" → Suggest trip

4. **Multi-Vehicle Optimization**
   - Cross-vehicle pattern detection
   - "You usually take Ford for long trips, Škoda for local"
