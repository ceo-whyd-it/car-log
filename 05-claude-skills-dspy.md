# Claude Skills & DSPy Integration

**Version:** 2.0
**Date:** 2025-11-17
**Status:** Draft - In Discussion

---

## Overview

This document specifies the **AI orchestration layer** for both interfaces:

- **Claude Skills** (Claude Desktop - P0): Workflow orchestration using natural language
- **DSPy** (Gradio App - P1): Programmatic LLM prompting with optimization

Both layers call the same MCP server backend for consistency.

---

## Architecture Comparison

| Aspect | Claude Desktop (Skills) | Gradio App (DSPy) |
|--------|------------------------|-------------------|
| **AI Framework** | Claude Skills (markdown-based) | DSPy (Python library) |
| **Interaction** | Conversational, contextual | Triggered by UI actions |
| **Prompt Management** | Embedded in Skill.md | DSPy signatures + modules |
| **Optimization** | Manual iteration | Automatic (BootstrapFewShot) |
| **Tool Calling** | MCP protocol (native) | MCP via HTTP/gRPC bridge |
| **State Management** | Claude conversation history | Gradio session state |

---

# Part 1: Claude Skills (P0)

## Overview

Claude Skills are **workflow orchestrators** that guide users through multi-step processes using natural language. Each skill encapsulates:
- When to activate (trigger conditions)
- What steps to perform (workflow logic)
- How to call MCP tools
- Error handling and user guidance

---

## Skill 1: checkpoint-manager

### File Structure
```
.claude/skills/checkpoint-manager/
├── Skill.md           # Main skill definition
└── resources/
    └── examples.md    # Extended examples
```

### Skill.md
```markdown
---
name: "Checkpoint Manager"
description: "Create vehicle checkpoints with automatic data extraction from photos"
version: "1.0.0"
---

# Checkpoint Manager

## Purpose
Guide users through checkpoint creation by extracting data from photos (receipts, dashboard) and validating input.

## When to Activate
- User mentions: "refuel", "fill up", "checkpoint", "log mileage"
- User pastes photo of receipt or dashboard
- User states: "I'm at [X] km"

## MCP Dependencies
- `car-log-core`: validate_checkpoint(), create_checkpoint()
- `ekasa-api`: extract_qr_code(), fetch_receipt()
- `filesystem`: extract_photo_metadata()
- `sqlite`: query and store data

## Workflow

### Step 1: Analyze Input
**If photo provided:**
1. Use Claude Vision to identify type (receipt/dashboard/unknown)
2. Extract visible text (odometer, QR code)
3. Call `filesystem.extract_photo_metadata(photo_path)`
   - Returns: `{timestamp, gps_coords, camera_info}`

**If text only:**
1. Parse for odometer reading (e.g., "45,320 km" or "45320")
2. Parse for vehicle mention (if multiple vehicles)

### Step 2: Extract Receipt Data
**If receipt identified:**
1. Call `ekasa-api.extract_qr_code(photo_path)`
   - Returns: `{receipt_id, confidence_score}`
2. If confidence > 0.8, call `ekasa-api.fetch_receipt(receipt_id)`
   - Returns: Complete receipt JSON with line items
3. Call `car-log-core.detect_fuel_items(receipt_data)`
   - Returns: `{fuel_items[], non_fuel_items[]}`
4. Present fuel item to user: "I found Diesel: 50L @ €1.45/L. Should I use this?"

**Fallback:** If QR extraction fails, offer manual receipt ID entry

### Step 3: Collect Missing Data
**Required fields:**
- vehicle_id (if user has multiple vehicles)
- odometer_reading (if not OCR'd from dashboard photo)
- timestamp (defaults to EXIF or current time)

**Prompt examples:**
- "Which vehicle? Ford Transit (BA-123AB) or Škoda Octavia (BA-456CD)?"
- "What's your current odometer reading in kilometers?"
- "When did this happen? (press Enter for now)"

### Step 4: Validate
1. Call `car-log-core.validate_checkpoint(checkpoint_data)`
   - Returns: `{valid, warnings[], errors[]}`

**Handle warnings:**
- Large distance (>500km in 1 day): "⚠️ That's 520km in 1 day. Is this correct?"
- Unusual fuel efficiency: "⚠️ This suggests 50 L/100km, which is very high. Correct?"

**Handle errors:**
- Odometer backwards: "❌ This reading (45,000km) is less than previous (45,320km). Options:
  1. Fix typo
  2. Mark as odometer reset
  3. Different vehicle"

### Step 5: Create & Confirm
1. Call `car-log-core.create_checkpoint(validated_data)`
   - Returns: `{checkpoint_id, distance_since_last, fuel_efficiency}`

2. Confirm to user with summary:
```
✓ Checkpoint created at 45,320km
• Location: Bratislava (Shell station)
• Fuel: 50L Diesel @ €1.45/L = €72.50
  - VAT (20%): €12.08
  - Excl. VAT: €60.42
• Distance since last: 200km (7 days ago)
• Fuel efficiency: 25 L/100km

You have a 200km gap to reconstruct.
Would you like to reconstruct trips now?
```

## Error Handling

**Photo analysis fails:**
```
"I couldn't extract data from this photo. You can:
1. Upload a clearer photo
2. Enter data manually
3. Try a different photo angle"
```

**e-Kasa API unavailable:**
```
"e-Kasa API is temporarily unavailable.
I've saved your receipt photo (ID: ABC123).
I'll fetch the data automatically when the API is back online.

For now, would you like to enter fuel data manually?"
```

**Duplicate checkpoint:**
```
"⚠️ You already have a checkpoint at 45,320km on Nov 15.
Options:
1. View existing checkpoint
2. Edit existing checkpoint
3. Cancel this entry"
```

## Examples

See [examples.md](resources/examples.md) for detailed conversational flows.
```

---

## Skill 2: trip-reconstructor

### Skill.md
```markdown
---
name: "Trip Reconstructor"
description: "Reconstruct trips between checkpoints using templates and geo-routing"
version: "1.0.0"
---

# Trip Reconstructor

## Purpose
Fill checkpoint gaps intelligently using:
- User memory (manual trip entry)
- Trip templates (recurring patterns)
- Geo-routing (OpenStreetMap)

## When to Activate
- After checkpoint creation, user wants to reconstruct
- User requests: "reconstruct trips from [date range]"
- User says: "fill in my trips"

## MCP Dependencies
- `sqlite`: Query checkpoints and templates
- `car-log-core`: Get templates, create trips (CRUD only)
- `geo-routing`: calculate_route(), geocode_address()
- `trip-reconstructor`: match_templates() (STATELESS service)

**IMPORTANT - Orchestration Pattern:**
The Skill acts as the ORCHESTRATOR. It:
1. Fetches data from multiple MCP servers (sqlite, car-log-core)
2. Prepares complete gap_data object with all checkpoints, templates, routes
3. Calls trip-reconstructor with ALL data as parameters (stateless)
4. Presents results to user
5. Creates trips via car-log-core after user approval

## Workflow

### Step 1: Gather Gap Data
**The Skill orchestrates multiple MCP calls:**

```python
# 1. Fetch checkpoints from sqlite
start_checkpoint = sqlite.query("SELECT * FROM checkpoints WHERE id = ?", [start_id])
end_checkpoint = sqlite.query("SELECT * FROM checkpoints WHERE id = ?", [end_id])

# 2. Calculate gap
gap_data = {
    "distance_km": end_checkpoint.odometer - start_checkpoint.odometer,
    "days": (end_checkpoint.timestamp - start_checkpoint.timestamp).days,
    "start_coords": start_checkpoint.coords,  # GPS coordinates (mandatory)
    "end_coords": end_checkpoint.coords,      # GPS coordinates (mandatory)
    "start_address": start_checkpoint.address,  # Optional human label
    "end_address": end_checkpoint.address,      # Optional human label
    "start_date": start_checkpoint.timestamp,
    "end_date": end_checkpoint.timestamp
}
```

Result presented to user:
```json
{
  "distance_km": 530,
  "days": 7,
  "start": {
    "odometer": 45320,
    "location": {"lat": 48.1486, "lng": 17.1077, "name": "Bratislava"},
    "timestamp": "2025-11-08T14:32:00Z"
  },
  "end": {
    "odometer": 45850,
    "location": {"lat": 48.7164, "lng": 21.2611, "name": "Košice"},
    "timestamp": "2025-11-15T10:15:00Z"
  }
}
```

### Step 2: Choose Reconstruction Mode
Present options:
```
"You drove 530km from Bratislava to Košice (Nov 8-15).

How would you like to reconstruct these trips?

A) Tell me specific trips you remember
B) Let me fill in using your trip templates
C) I'll do it later"
```

### Step 3a: Manual Mode
**User chooses A:**
1. Interactive trip entry:
```
"What trip do you remember?"
User: "I went to Košice on Nov 12, that was 410km"

"Got it. Was this for business or personal?"
User: "Business - warehouse pickup"

"Perfect! That accounts for 410km out of 530km.
Remaining: 120km. Should I:
1. Ask about more trips
2. Fill remainder with templates
3. Mark as local driving"
```

2. Create user-specified trips
3. Handle remainder

### Step 3b: Template Mode
**User chooses B:**

1. **Fetch User Templates**:
```python
# Skill orchestrates: Get templates from car-log-core
templates = car_log_core.list_templates(vehicle_id)
# Returns array of template objects with GPS coords (mandatory) and addresses (optional)
```

2. **Calculate Geo-Routes** (if checkpoints have GPS):
```python
# Skill orchestrates: Call geo-routing MCP
routes = geo_routing.calculate_route(
  from_coords=gap_data.start_coords,  # (48.1486, 17.1077)
  to_coords=gap_data.end_coords,      # (48.7164, 21.2611)
  alternatives=3
)

# Returns:
[
  {"distance_km": 395, "via": "D1 highway", "duration_hours": 4.2},
  {"distance_km": 410, "via": "E50", "duration_hours": 4.5},
  {"distance_km": 385, "via": "local roads", "duration_hours": 5.8}
]
```

3. **Call Stateless Reconstructor**:
```python
# Skill orchestrates: Pass ALL data to trip-reconstructor (stateless)
matches = trip_reconstructor.match_templates(
  gap_data={
    "distance_km": 530,
    "start_coords": {"lat": 48.1486, "lng": 17.1077},
    "end_coords": {"lat": 48.7164, "lng": 21.2611},
    "start_address": "Bratislava",  # Optional
    "end_address": "Košice",        # Optional
    "start_date": "2025-11-08",
    "end_date": "2025-11-15"
  },
  templates=templates,     # Full template objects from step 1
  geo_routes=routes        # Full route data from step 2
)

# Returns:
[
  {
    "template": {
      "id": "uuid-1",
      "name": "Warehouse Run",
      "distance_km": 410,
      "from": "Bratislava",
      "to": "Košice"
    },
    "confidence": 0.95,  # GPS + distance match
    "suggested_count": 1,
    "total_km": 410,
    "matching_route": routes[1]  # E50, 410km
  },
  {
    "template": {
      "id": "uuid-2",
      "name": "Daily Commute",
      "distance_km": 25
    },
    "confidence": 0.70,  # Usage pattern match
    "suggested_count": 4,
    "total_km": 100
  }
]
```

4. **Present Proposal**:
```
"Here's my reconstruction estimate:

✓ 1× Warehouse Run (410km)
  ↳ High confidence (95%) - GPS match + distance + day-of-week
  ↳ GPS: Both locations within 100m of template coordinates
  ↳ Route: Bratislava → Košice via E50

✓ 4× Daily Commute (100km total)
  ↳ Medium confidence (70%) - 4 work days in period
  ↳ GPS: Start location 3.5km from template (same area)

⚠️ Remainder: 20km
  ↳ Suggested: Local driving

Total: 530km ✓

Does this match your memory?"
```

5. **User Confirms/Adjusts**:
```
User: "Yes but only 3 commutes, not 4"

"Got it, adjusting:
• 1× Warehouse Run (410km)
• 3× Daily Commute (75km)
• Remainder: 45km local driving

Total: 530km ✓

Should I create these trips?"
```

6. **Create Trips** (Skill orchestrates final creation):
```python
# Skill orchestrates: Call car-log-core to create trips after user approval
result = car_log_core.create_trips_batch([
  {
    "start_checkpoint_id": "uuid-start",
    "end_checkpoint_id": "uuid-end",
    "template_id": "uuid-1",
    "date": "2025-11-12",
    "distance_km": 410,
    "purpose": "business",
    "business_description": "Warehouse pickup"
  },
  # ... 3x commute trips
  # ... 1x local driving
])

# NOTE: car-log-core is CRUD only - it stores the trips
# The reconstruction logic happened in trip-reconstructor (stateless)
```

### Step 4: Confirm Creation
```
"✓ 5 trips created:
• 1× Warehouse Run (410km, Business)
• 3× Daily Commute (75km total, Business)
• 1× Local driving (45km, needs classification)

Would you like to classify the local driving now?
Options: Business / Personal"
```

## Edge Cases

**No templates available:**
```
"You don't have any trip templates yet.
Options:
1. Create a template for this route (Bratislava → Košice, 410km)
2. Enter trips manually
3. Skip for now"
```

**Templates don't fit:**
```
"Your 'Warehouse Run' template (410km) doesn't fit this 200km gap.
Possible explanations:
• One-way trip only (205km) ✓
• Different route
• Multiple shorter trips

Which makes sense?"
```

**Large remainder:**
```
"After using templates, you have 150km unaccounted (28% of gap).
This is larger than typical local driving.

Would you like to:
1. Tell me about other trips
2. Create a new template for this
3. Mark all as unspecified trips"
```

## Examples

See [reconstruction-examples.md](resources/reconstruction-examples.md) for detailed flows.
```

---

## Skill 3: template-manager

### Skill.md
```markdown
---
name: "Template Manager"
description: "Create, edit, and manage recurring trip templates"
version: "1.0.0"
---

# Template Manager

## Purpose
Help users create and manage trip templates for recurring routes.

## When to Activate
- User wants to create template: "create a trip template"
- After reconstruction, suggest template: "Save this as a template?"
- User asks to edit templates: "show my templates"

## MCP Dependencies
- `car-log-core`: create_template(), list_templates(), suggest_template_from_history()
- `geo-routing`: geocode_address(), calculate_route()

**IMPORTANT - GPS-First Architecture:**
Templates MUST have GPS coordinates to enable reliable geo-matching.
The Skill orchestrates address geocoding before template creation.

## Workflows

### Create Template (Manual)
```
User: "Create a trip template"

1. "What should I call this template?"
   User: "Office to Warehouse"

2. "Where does it start?"
   User: "Main Office, Hlavná 45, Bratislava"

   [Skill orchestrates: Call geo-routing.geocode_address()]

   If ambiguous (confidence < 0.7):
   "I found multiple matches for 'Bratislava':
   1. Bratislava City Center (48.1486, 17.1077)
   2. Bratislava-Petržalka (48.1234, 17.1234)
   3. Bratislava Airport (48.1702, 17.2127)

   Which location? (1/2/3)"
   User: "1"

3. "And the destination?"
   User: "Warehouse, Košice"

   [Skill orchestrates: Call geo-routing.geocode_address()]
   Result: (48.7164, 21.2611) - single match, high confidence

4. "Is this a round trip?"
   User: "Yes"

5. [Skill orchestrates: Call geo-routing.calculate_route() using GPS coordinates]
   "I calculated the route using GPS coordinates:
   • From: (48.1486, 17.1077) 'Main Office, Bratislava'
   • To: (48.7164, 21.2611) 'Warehouse, Košice'

   3 possible routes:
   • D1 highway: 395km (4.2 hrs)
   • E50: 410km (4.5 hrs) ← Recommended
   • Local: 385km (5.8 hrs)

   Which distance for round trip?"
   User: "410km"

6. "On which days do you typically make this trip? (optional)"
   User: "Mondays and Thursdays"

7. "Business or personal? (optional)"
   User: "Business - picking up supplies"

8. [Skill orchestrates: Call car-log-core.create_template() with GPS coordinates]
   "✓ Template 'Office to Warehouse' created:
   • From: (48.1486, 17.1077) 'Main Office, Bratislava'
   • To: (48.7164, 21.2611) 'Warehouse, Košice'
   • Distance: 410km round trip
   • Days: Mondays, Thursdays (optional)
   • Purpose: Business (optional)

   GPS coordinates saved - I'll match this template reliably during reconstruction."
```

### Create from Existing Trip
```
User: "Create a template from my Nov 12 trip"

1. [Look up trip]
   "That was your Bratislava → Košice trip (410km, Business).
   Template name?"
   User: "Warehouse Run"

2. "Should I include the 'typical days' (Wednesday)?"
   User: "No, it varies"

3. [Create template with trip data]
   "✓ Template 'Warehouse Run' created from trip history."
```

### System Suggests Template
```
[After 5+ similar trips detected]

"I notice you've made 6 similar trips:
• Bratislava → Košice (avg 408km)
• Always on Mondays or Thursdays
• All marked as Business

Should I create a template for this route?
Suggested name: 'Bratislava-Košice Run'"

User: "Yes, call it 'Warehouse Run'"

[Create template automatically]
```

## Examples
See [template-examples.md](resources/template-examples.md)
```

---

## Skill 4: report-generator

### Skill.md
```markdown
---
name: "Report Generator"
description: "Generate tax-compliant PDF/CSV reports"
version: "1.0.0"
---

# Report Generator

## Purpose
Create exportable reports (CSV/PDF) for tax authorities and accountants.

## When to Activate
- User requests: "generate report"
- User asks: "export to CSV"
- User says: "I need a report for [time period]"

## MCP Dependencies
- `car-log-core`: query_trips(), calculate_totals()
- `report-generator`: generate_csv(), generate_pdf()
- `sqlite`: data queries

## Workflow

### Step 1: Gather Report Parameters
```
User: "Generate a report for November"

1. "Which vehicle(s)?"
   [If single vehicle, skip this step]
   User: "Ford Transit"

2. "What format? CSV or PDF?"
   User: "Both"

3. "Include only business trips or all trips?"
   User: "Business only"
```

### Step 2: Query Data
```python
# Call car-log-core MCP
report_data = query_trips(
  vehicle_id="uuid-ford",
  start_date="2025-11-01",
  end_date="2025-11-30",
  purpose="business"
)

# Returns:
{
  "trips": [
    {
      "date": "2025-11-03",
      "from": "Bratislava",
      "to": "Košice",
      "distance_km": 410,
      "fuel_liters": 50,
      "fuel_cost_eur": 72.50,
      "purpose": "Business - warehouse pickup"
    },
    ...
  ],
  "totals": {
    "total_distance_km": 1850,
    "total_fuel_cost_eur": 325.80,
    "business_trips": 12,
    "avg_fuel_efficiency": 25.4
  }
}
```

### Step 3: Generate Reports
```python
# CSV
csv_path = generate_csv(report_data, template="slovak_tax_2025")

# PDF
pdf_path = generate_pdf(report_data, template="slovak_tax_2025")
```

### Step 4: Deliver to User
```
"✓ Reports generated for November 2025:

📊 Summary:
• Total distance: 1,850 km (business only)
• Fuel cost: €325.80
• Trips: 12
• Avg efficiency: 25.4 L/100km

📄 Files created:
• ford-transit-nov-2025.csv (12 KB)
• ford-transit-nov-2025.pdf (245 KB)

[Downloads ready]

Would you like to:
1. View the PDF
2. Email to accountant
3. Generate another report"
```

## Templates

### Slovak Tax Authority Format
- Company details
- Vehicle registration
- Trip log table (date, from, to, km, purpose)
- Fuel expense summary (VAT breakdown)
- Signature section

## Examples
See [report-examples.md](resources/report-examples.md)
```

---

# Part 2: DSPy Integration (P1)

## Overview

**DSPy** (Declarative Self-improving Python) is used in the Gradio app for:
- Programmatic LLM prompting
- Automatic prompt optimization
- Structured output generation
- Chain-of-thought reasoning

### Why DSPy for Gradio?

| Requirement | DSPy Solution |
|-------------|---------------|
| **Consistent outputs** | Signatures with typed outputs |
| **Prompt optimization** | BootstrapFewShot compiler |
| **Non-conversational** | Direct function calls, not chat |
| **Testable** | Unit tests with assertions |
| **Cost-effective** | Optimized prompts reduce tokens |

---

## DSPy Architecture

```
┌─────────────────────────────────────────────────────┐
│ Gradio UI (User clicks button)                     │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Python Backend (Event handler)                      │
│ • Validate input                                    │
│ • Call DSPy module                                  │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ DSPy Module (e.g., CheckpointValidator)            │
│ • Input: checkpoint_data                            │
│ • Chain-of-thought reasoning                        │
│ • Output: {valid, warnings, errors}                 │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ LLM API (Claude via Anthropic API)                 │
│ • Optimized prompt from DSPy                        │
│ • Structured response                               │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ MCP Server (car-log-core)                          │
│ • create_checkpoint() or other business logic       │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Gradio UI (Display result)                          │
└─────────────────────────────────────────────────────┘
```

---

## DSPy Modules

### Module 1: CheckpointValidator

**Purpose:** Validate checkpoint data before creation

```python
import dspy

class CheckpointValidator(dspy.Signature):
    """Validate a vehicle checkpoint for anomalies and errors."""

    # Inputs
    checkpoint_data: dict = dspy.InputField(
        desc="Checkpoint data: {vehicle_id, odometer, timestamp, fuel_data}"
    )
    previous_checkpoint: dict = dspy.InputField(
        desc="Previous checkpoint for sequence validation"
    )

    # Outputs
    valid: bool = dspy.OutputField(desc="True if checkpoint is valid")
    warnings: list[str] = dspy.OutputField(
        desc="Non-blocking warnings (e.g., large distance)"
    )
    errors: list[str] = dspy.OutputField(
        desc="Blocking errors (e.g., odometer backwards)"
    )
    reasoning: str = dspy.OutputField(
        desc="Chain-of-thought explanation"
    )


class ValidateCheckpoint(dspy.Module):
    def __init__(self):
        super().__init__()
        self.validator = dspy.ChainOfThought(CheckpointValidator)

    def forward(self, checkpoint_data, previous_checkpoint):
        result = self.validator(
            checkpoint_data=checkpoint_data,
            previous_checkpoint=previous_checkpoint
        )
        return result


# Usage in Gradio
def create_checkpoint_handler(odometer, fuel_liters, fuel_cost):
    """Gradio button click handler"""

    # Get previous checkpoint
    prev_cp = get_last_checkpoint(vehicle_id)

    # Prepare data
    checkpoint_data = {
        "vehicle_id": vehicle_id,
        "odometer": odometer,
        "timestamp": datetime.now(),
        "fuel_data": {"liters": fuel_liters, "cost": fuel_cost}
    }

    # Validate with DSPy
    validator = ValidateCheckpoint()
    validation = validator(
        checkpoint_data=checkpoint_data,
        previous_checkpoint=prev_cp
    )

    # Handle result
    if not validation.valid:
        return gr.Error(f"❌ Errors: {', '.join(validation.errors)}")

    if validation.warnings:
        show_warning_dialog(validation.warnings)

    # Call MCP to create
    checkpoint_id = mcp_client.create_checkpoint(checkpoint_data)

    return gr.Info(f"✓ Checkpoint {checkpoint_id} created")
```

---

### Module 2: TripReconstructor

**Purpose:** Propose trip reconstruction from gap analysis

```python
class TripReconstructionSignature(dspy.Signature):
    """Reconstruct trips from checkpoint gap using templates."""

    # Inputs
    gap_data: dict = dspy.InputField(
        desc="Gap: {distance_km, days, start_location, end_location}"
    )
    available_templates: list[dict] = dspy.InputField(
        desc="User's trip templates with distances and locations"
    )
    geo_routes: list[dict] = dspy.InputField(
        desc="Calculated routes from OpenStreetMap (if GPS available)"
    )

    # Outputs
    proposed_trips: list[dict] = dspy.OutputField(
        desc="List of trips: {template_id, count, total_km, confidence}"
    )
    remainder_km: int = dspy.OutputField(
        desc="Unaccounted distance after template matching"
    )
    confidence_score: float = dspy.OutputField(
        desc="Overall confidence (0-1) of reconstruction"
    )
    reasoning: str = dspy.OutputField(
        desc="Explanation of how templates were matched"
    )


class ReconstructTrips(dspy.Module):
    def __init__(self):
        super().__init__()
        self.reconstructor = dspy.ChainOfThought(TripReconstructionSignature)

    def forward(self, gap_data, available_templates, geo_routes=None):
        result = self.reconstructor(
            gap_data=gap_data,
            available_templates=available_templates,
            geo_routes=geo_routes or []
        )
        return result


# Usage in Gradio
def reconstruct_gap_handler(start_checkpoint_id, end_checkpoint_id):
    """Gradio button click: Reconstruct trips"""

    # Get gap data from MCP
    gap = mcp_client.analyze_gap(start_checkpoint_id, end_checkpoint_id)

    # Get templates
    templates = mcp_client.list_templates(user_id)

    # Calculate geo routes if GPS available
    geo_routes = None
    if gap["start"]["location"] and gap["end"]["location"]:
        geo_routes = mcp_client.calculate_route(
            gap["start"]["location"],
            gap["end"]["location"]
        )

    # Reconstruct with DSPy
    reconstructor = ReconstructTrips()
    proposal = reconstructor(
        gap_data=gap,
        available_templates=templates,
        geo_routes=geo_routes
    )

    # Display proposal in UI
    return render_reconstruction_proposal(proposal)
```

---

### Module 3: FuelItemDetector

**Purpose:** Identify fuel items from receipt line items

```python
class FuelDetectionSignature(dspy.Signature):
    """Detect fuel purchases from receipt line items."""

    # Input
    receipt_data: dict = dspy.InputField(
        desc="Receipt with line_items: [{description, quantity, unit, price}]"
    )

    # Outputs
    fuel_items: list[dict] = dspy.OutputField(
        desc="Detected fuel items with confidence scores"
    )
    non_fuel_items: list[dict] = dspy.OutputField(
        desc="Non-fuel items (coffee, snacks, etc.)"
    )
    reasoning: str = dspy.OutputField(
        desc="Explanation of detection logic"
    )


class DetectFuelItems(dspy.Module):
    def __init__(self):
        super().__init__()
        self.detector = dspy.ChainOfThought(FuelDetectionSignature)

    def forward(self, receipt_data):
        return self.detector(receipt_data=receipt_data)


# Usage
detector = DetectFuelItems()
result = detector(receipt_data={
    "line_items": [
        {"description": "Diesel", "quantity": 50, "unit": "L", "price": 72.50},
        {"description": "Káva", "quantity": 1, "unit": "ks", "price": 1.00}
    ]
})

print(result.fuel_items)
# [{description: "Diesel", quantity: 50, confidence: 0.98}]
```

---

## DSPy Optimization

### Training Set Creation

```python
# Create training examples from historical data
training_set = [
    dspy.Example(
        gap_data={"distance_km": 410, "days": 1},
        available_templates=[
            {"name": "Warehouse Run", "distance_km": 410, "location_match": True}
        ],
        geo_routes=[{"distance_km": 410, "via": "E50"}],
        proposed_trips=[{"template_id": "uuid-1", "count": 1, "confidence": 0.95}],
        remainder_km=0
    ).with_inputs("gap_data", "available_templates", "geo_routes"),

    # ... more examples
]

# Optimize with BootstrapFewShot
optimizer = dspy.BootstrapFewShot(metric=reconstruction_accuracy)
optimized_reconstructor = optimizer.compile(
    ReconstructTrips(),
    trainset=training_set
)

# Save optimized module
optimized_reconstructor.save("models/trip_reconstructor_v1.json")
```

### Metric Function

```python
def reconstruction_accuracy(example, prediction, trace=None):
    """
    Evaluate reconstruction quality:
    - Proposed trips sum to gap distance (±5%)
    - High-confidence matches prioritized
    - Low remainder (<5% of gap)
    """
    gap_distance = example.gap_data["distance_km"]
    proposed_distance = sum([t["total_km"] for t in prediction.proposed_trips])
    remainder = prediction.remainder_km

    distance_error = abs(gap_distance - (proposed_distance + remainder))
    distance_accuracy = 1.0 - (distance_error / gap_distance)

    confidence_score = prediction.confidence_score

    remainder_penalty = remainder / gap_distance

    score = (
        distance_accuracy * 0.5 +
        confidence_score * 0.3 +
        (1 - remainder_penalty) * 0.2
    )

    return score
```

---

## Integration with MCP Servers

### MCP Client Bridge

```python
import httpx

class MCPClient:
    """Bridge between Gradio/DSPy and MCP servers"""

    def __init__(self, mcp_base_url="http://localhost:8000"):
        self.base_url = mcp_base_url
        self.client = httpx.Client()

    def create_checkpoint(self, checkpoint_data):
        """Call car-log-core MCP server"""
        response = self.client.post(
            f"{self.base_url}/car-log-core/create_checkpoint",
            json=checkpoint_data
        )
        return response.json()

    def analyze_gap(self, start_checkpoint_id, end_checkpoint_id):
        """Call car-log-core MCP server"""
        response = self.client.post(
            f"{self.base_url}/car-log-core/analyze_gap",
            json={
                "start_checkpoint_id": start_checkpoint_id,
                "end_checkpoint_id": end_checkpoint_id
            }
        )
        return response.json()

    def calculate_route(self, from_coords, to_coords):
        """Call geo-routing MCP server"""
        response = self.client.post(
            f"{self.base_url}/geo-routing/calculate_route",
            json={
                "from_coords": from_coords,
                "to_coords": to_coords,
                "alternatives": 3
            }
        )
        return response.json()


# Global MCP client instance
mcp_client = MCPClient()
```

---

## Gradio App Structure

```python
import gradio as gr
import dspy

# Configure DSPy
dspy.settings.configure(
    lm=dspy.Claude(model="claude-3-5-sonnet-20241022"),
    rm=None  # No retrieval model needed
)

# Load optimized modules
checkpoint_validator = ValidateCheckpoint()
trip_reconstructor = ReconstructTrips()
fuel_detector = DetectFuelItems()

# Gradio interface
with gr.Blocks(title="Car Log") as app:
    gr.Markdown("# 🚗 Car Log - Mileage Tracker")

    with gr.Tab("Checkpoints"):
        with gr.Row():
            vehicle_dropdown = gr.Dropdown(
                label="Vehicle",
                choices=["Ford Transit (BA-123AB)", "Škoda Octavia (BA-456CD)"]
            )

        with gr.Row():
            odometer_input = gr.Number(label="Odometer (km)", precision=0)
            fuel_liters = gr.Number(label="Fuel (L)", precision=2)
            fuel_cost = gr.Number(label="Cost (€)", precision=2)

        create_btn = gr.Button("Create Checkpoint")
        output = gr.Textbox(label="Result")

        create_btn.click(
            fn=create_checkpoint_handler,
            inputs=[odometer_input, fuel_liters, fuel_cost],
            outputs=[output]
        )

    with gr.Tab("Trip Reconstruction"):
        checkpoint_table = gr.Dataframe(label="Recent Checkpoints")
        reconstruct_btn = gr.Button("Reconstruct Selected Gap")
        proposal_output = gr.JSON(label="Proposed Trips")

        reconstruct_btn.click(
            fn=reconstruct_gap_handler,
            inputs=[],
            outputs=[proposal_output]
        )

app.launch()
```

---

## Testing Strategy

### Unit Tests for DSPy Modules

```python
import pytest

def test_checkpoint_validator_catches_backwards_odometer():
    """Test that validator detects odometer going backwards"""
    validator = ValidateCheckpoint()

    result = validator(
        checkpoint_data={"odometer": 45000},
        previous_checkpoint={"odometer": 45320}
    )

    assert result.valid == False
    assert "odometer" in result.errors[0].lower()


def test_trip_reconstructor_matches_exact_template():
    """Test template matching with exact distance"""
    reconstructor = ReconstructTrips()

    result = reconstructor(
        gap_data={"distance_km": 410, "days": 1},
        available_templates=[
            {"id": "uuid-1", "name": "Warehouse Run", "distance_km": 410}
        ],
        geo_routes=[]
    )

    assert len(result.proposed_trips) == 1
    assert result.proposed_trips[0]["template_id"] == "uuid-1"
    assert result.remainder_km < 50
    assert result.confidence_score > 0.8


def test_fuel_detector_identifies_diesel():
    """Test fuel item detection"""
    detector = DetectFuelItems()

    result = detector(receipt_data={
        "line_items": [
            {"description": "Diesel", "quantity": 50, "unit": "L"},
            {"description": "Káva", "quantity": 1, "unit": "ks"}
        ]
    })

    assert len(result.fuel_items) == 1
    assert result.fuel_items[0]["description"] == "Diesel"
    assert len(result.non_fuel_items) == 1
```

---

## Summary: Skills vs. DSPy

| Aspect | Claude Skills | DSPy |
|--------|---------------|------|
| **Use Case** | Conversational workflows | Programmatic LLM calls |
| **Interface** | Claude Desktop | Gradio web app |
| **Optimization** | Manual iteration | Automatic (BootstrapFewShot) |
| **State** | Conversation history | Session variables |
| **Complexity** | High (multi-turn dialogs) | Low (single function calls) |
| **Testability** | Manual testing | Unit tests |
| **Best For** | Guiding users | Data processing |

Both layers use the same MCP servers, ensuring consistency across interfaces.

---

## Related Documents

- [01-product-overview.md](./01-product-overview.md)
- [03-trip-reconstruction.md](./03-trip-reconstruction.md)
- [06-mcp-architecture.md](./06-mcp-architecture.md) (next)

---

## Next Steps

1. **Implement Claude Skills** (P0)
   - Write Skill.md files for all 4 skills
   - Test in Claude Desktop
   - Iterate based on user feedback

2. **Implement DSPy Modules** (P1)
   - Create signatures for key workflows
   - Build training set from historical data
   - Optimize with BootstrapFewShot

3. **MCP HTTP Bridge** (P1)
   - Expose MCP servers via HTTP API
   - Enable Gradio app to call MCP tools
   - Add authentication if needed
