# Claude Desktop Skills - Best Practices Guide

**Purpose:** Guidance on when and how to use Car Log skills effectively

---

## Table of Contents

1. [When to Use Each Skill](#when-to-use-each-skill)
2. [Skill Chaining Patterns](#skill-chaining-patterns)
3. [Error Recovery Strategies](#error-recovery-strategies)
4. [Performance Optimization](#performance-optimization)
5. [User Experience Guidelines](#user-experience-guidelines)
6. [Slovak Compliance Checklist](#slovak-compliance-checklist)

---

## When to Use Each Skill

### Skill 1: Receipt to Checkpoint (F1) - ALWAYS FIRST

**Use When:**
- User mentions receipt, e-Kasa, QR code, or refueling
- User says "I just filled up", "scan receipt", "log refuel"
- Starting a new logging session

**Don't Use When:**
- User wants to create manual checkpoint (no receipt)
- User is asking questions (not logging data)
- User wants reports or templates only

**Triggers:**
```
✅ "I scanned a receipt"
✅ "Just filled up at OMV"
✅ "Log my refuel"
✅ "Here's my e-Kasa QR: /o12345..."

❌ "How many trips did I make?"
❌ "Show me my reports"
❌ "What's my average efficiency?"
```

---

### Skill 2: Gap Detection (F2) - AUTOMATIC

**Use When:**
- User has >2 checkpoints
- User asks "any gaps?" or "missing trips?"
- Before generating reports (to ensure completeness)
- After creating checkpoint (proactive check)

**Don't Use When:**
- User has 0-1 checkpoints (not enough data)
- User is still in middle of receipt entry
- User explicitly says "skip gap detection"

**Triggers:**
```
✅ [Automatic after 2nd checkpoint]
✅ "Check for gaps"
✅ "Any missing trips?"
✅ [Before report generation]

❌ [User just created first checkpoint]
❌ [User still entering receipt data]
```

---

### Skill 3: Trip Reconstruction (F3) - AFTER GAP DETECTION

**Use When:**
- Gap detection found gaps
- User has templates defined
- Gap spans 50km+ (worth reconstructing)
- User asks "match templates" or "fill gaps"

**Don't Use When:**
- No gaps found
- Gap <50km (manual entry faster)
- User has no templates
- User wants manual trip entry

**Triggers:**
```
✅ [After gap detection finds gaps]
✅ "Match my templates"
✅ "Reconstruct trips"
✅ "Fill gaps automatically"

❌ "Add trip manually" (use manual entry)
❌ [No templates exist yet]
❌ [Gap is only 15km]
```

---

### Skill 4: Template Creation (F4) - AS NEEDED

**Use When:**
- User mentions "save this route", "create template"
- After manual trip entry: "Save as template?"
- User says "I make this trip regularly"
- After reconstruction: "Save this match as template?"

**Don't Use When:**
- User is doing one-time trip
- Route is highly variable (not recurring)
- User explicitly says "don't save as template"

**Triggers:**
```
✅ "Save warehouse run as template"
✅ "I make this trip every Monday"
✅ "Create template for Bratislava-Košice"

❌ "One-time trip to Vienna"
❌ "Random errand run"
```

---

### Skill 5: Report Generation (F5) - END OF MONTH

**Use When:**
- User asks for "report", "CSV", "PDF", "export"
- End of month (tax submission deadline)
- User mentions "accountant", "tax", "VAT deduction"
- Before audits or compliance checks

**Don't Use When:**
- User is still logging trips (mid-month)
- User wants summary stats only (not full report)
- No trips recorded yet

**Triggers:**
```
✅ "Generate November report"
✅ "Export to CSV for accountant"
✅ "I need tax report"
✅ "Create PDF for records"

❌ "How many km this week?" (use summary query)
❌ "Show my last trip" (use data query)
```

---

### Skill 6: Data Validation (F6) - AUTOMATIC + ON-DEMAND

**Use When:**
- Automatic after checkpoint/trip creation
- User asks "check my data", "validate", "any errors?"
- Before report generation (ensure clean data)
- User suspects data issues

**Don't Use When:**
- User is asking hypothetical questions
- Validation already ran (don't repeat immediately)
- User is still editing trip (wait for completion)

**Triggers:**
```
✅ [Automatic after data entry]
✅ "Check my data for errors"
✅ "Validate my trips"
✅ "Are there any issues?"

❌ "What if I entered wrong fuel?" (hypothetical)
❌ [Validation just ran 10 seconds ago]
```

---

## Skill Chaining Patterns

### Pattern 1: Receipt → Gap → Reconstruction → Validation

**Flow:**
```
1. Skill 1: Receipt to Checkpoint
   ↓
2. Skill 6: Validation (automatic)
   ↓
3. Skill 2: Gap Detection (if >1 checkpoint)
   ↓
4. Skill 3: Trip Reconstruction (if gaps + templates)
   ↓
5. Skill 6: Validation (after reconstruction)
```

**Example Conversation:**
```
User: "I scanned a receipt: /o12345..."

Claude: [F1: Receipt to Checkpoint]
"✅ Checkpoint created from e-Kasa receipt.
Refuel: 45.2L diesel at OMV Bratislava
Odometer: 50,820km

[F6: Validation - automatic]
✅ All validation checks passed!

[F2: Gap Detection - automatic if >1 checkpoint]
⚠️ Gap detected: 820km between Nov 1 and Nov 5

[F3: Trip Reconstruction - if templates exist]
Found 2 matching templates (92% and 88% confidence).
Would you like to review?"

User: "Yes, approve both"

Claude: [Creates trips]

[F6: Validation - automatic after trip creation]
✅ All validation checks passed!
Distance sum: 820km (0% variance)

Gap closed! All trips recorded."
```

---

### Pattern 2: Template Creation → Future Reconstruction

**Flow:**
```
1. User creates manual trip
   ↓
2. Skill 4: "Save as template?" (proactive suggestion)
   ↓
3. Future: Skill 3 uses template for reconstruction
```

**Example:**
```
User: "Add trip: Bratislava to Košice, 410km, business"

Claude: [Creates trip manually]
"✅ Trip created!

I noticed this is a long trip (410km). Do you make this
trip regularly?

If so, I can save it as a template for faster logging
next time. Would you like to create a template?"

User: "Yes, I do this every Monday"

Claude: [F4: Template Creation]
"Creating template...
✅ Template 'Bratislava-Košice' created!

Now when I detect 410km gaps on Mondays, I'll automatically
suggest this template with 90%+ confidence."
```

---

### Pattern 3: Monthly Workflow (End-to-End)

**Flow:**
```
Throughout month:
1. Skill 1: Receipt to Checkpoint (repeated)
2. Skill 6: Validation (automatic)
3. Skill 2: Gap Detection (periodic)
4. Skill 3: Reconstruction (as needed)
5. Skill 4: Template Creation (occasional)

End of month:
6. Skill 2: Final gap check
7. Skill 6: Full validation
8. Skill 5: Report Generation
```

**Example:**
```
[Throughout November]
User: [Multiple receipt scans]
Claude: [F1 + F6 + F2 + F3 loops]

[Nov 30]
User: "Generate November report"

Claude: "Let me first check for any gaps or issues...

[F2: Gap Detection]
✅ No gaps found

[F6: Full Validation]
✅ All 28 trips validated
Distance sum: 0.8% variance ✓
Fuel consumption: All within ±15% ✓

[F5: Report Generation]
✅ November 2025 Business Trips Report
• 28 trips, 11,480km
• 972L fuel (8.5 L/100km avg)
• €389 VAT deductible
• 100% Slovak compliant

Reports saved to ~/Documents/MileageLog/reports/"
```

---

### Pattern 4: Error Recovery (Validation Failure)

**Flow:**
```
1. Skill 6: Validation (finds errors)
   ↓
2. Claude guides correction
   ↓
3. User fixes data
   ↓
4. Skill 6: Re-validation
   ↓
5. Continue workflow
```

**Example:**
```
Claude: [F6: Validation - automatic]
"❌ Validation Error:

Distance Sum Mismatch: -12%
You're missing 98km of trips.

Options:
1. Add missing trips
2. Check odometer readings
3. Adjust trip distances"

User: "I forgot to log a trip to Prešov"

Claude: "Let me help you add that trip.

[Collects trip details]
✅ Trip added: Bratislava → Prešov (98km)

[F6: Re-validation]
✅ All validation checks now pass!
Distance sum: 0% variance

Continue with workflow..."
```

---

## Error Recovery Strategies

### Strategy 1: Graceful Degradation

**Principle:** If a tool fails, offer manual alternative

**Examples:**
```
e-Kasa API timeout (60s):
❌ "e-Kasa API timed out"
✅ "e-Kasa API timed out (busy servers). I can help you
    enter the receipt data manually instead. Do you have
    the fuel quantity and price?"

Geocoding ambiguous:
❌ "Error: Multiple matches"
✅ "Found 3 locations named 'Košice'. Which one?
    1. Košice Center
    2. Košice East
    3. Košice Airport"

Template matching low confidence:
❌ "No match found"
✅ "No high-confidence template match (best: 65%). Would
    you like to enter the trip manually or create a new
    template?"
```

---

### Strategy 2: Progressive Enhancement

**Principle:** Collect minimum required data first, enhance later

**Examples:**
```
Minimum checkpoint:
1. Odometer reading (REQUIRED)
2. DateTime (REQUIRED)
3. GPS/Address (REQUIRED)

Enhancement:
4. Receipt data (optional, fetch later if have ID)
5. Photo/image (optional, P1 feature)
6. Notes (optional)

Minimum trip:
1. Start/End locations (REQUIRED)
2. Distance (REQUIRED)
3. Driver name (REQUIRED for Slovak compliance)
4. Purpose (REQUIRED)

Enhancement:
5. Business description (if business)
6. Template ID (if matched)
7. Route alternatives (optional)
```

---

### Strategy 3: Validation-Driven Correction

**Principle:** Let validation guide fixes, don't assume

**Examples:**
```
❌ Bad: Automatically adjust distance to match odometer
✅ Good: Show mismatch, ask user what to fix

❌ Bad: Silently convert km/L to L/100km
✅ Good: Detect format, ask confirmation

❌ Bad: Fill missing driver name with "Unknown"
✅ Good: Prompt for driver name (mandatory)

❌ Bad: Reject data with errors
✅ Good: Show errors, offer correction flow
```

---

### Strategy 4: Retry with Backoff

**Principle:** External APIs may be slow/flaky, retry intelligently

**Examples:**
```
e-Kasa API:
1st attempt: 60s timeout
2nd attempt: Show "still fetching..." message
Fail: Offer manual entry

Geocoding:
1st attempt: Exact match
2nd attempt: Fuzzy match (show alternatives)
Fail: Ask for manual GPS entry

Route calculation:
1st attempt: 3 alternatives
2nd attempt: Single fastest route
Fail: Ask for manual distance entry
```

---

## Performance Optimization

### Optimization 1: Batch MCP Calls

**Bad (Sequential):**
```typescript
// 5 seconds total (3 × 1s + 2s)
const vehicle = await car_log_core.get_vehicle(id);
const checkpoints = await car_log_core.list_checkpoints(id);
const trips = await car_log_core.list_trips(id);
const templates = await car_log_core.list_templates(user_id);
const validation = await validation.validate_trip(trip_id);
```

**Good (Parallel):**
```typescript
// 2 seconds total (max of all parallel calls)
const [vehicle, checkpoints, trips, templates, validation] = await Promise.all([
  car_log_core.get_vehicle(id),
  car_log_core.list_checkpoints(id),
  car_log_core.list_trips(id),
  car_log_core.list_templates(user_id),
  validation.validate_trip(trip_id)
]);
```

---

### Optimization 2: Cache Common Data

**Cache these:**
- Vehicle list (rarely changes)
- Templates (rarely change)
- Vehicle average efficiency (changes slowly)
- User preferences

**Don't cache these:**
- Checkpoints (always fresh)
- Trips (always fresh)
- Gap detection results (always fresh)
- Validation results (always fresh)

**Example:**
```typescript
// Cache templates for session (10 min)
if (!cached_templates || cache_expired) {
  cached_templates = await car_log_core.list_templates(user_id);
  cache_timestamp = now();
}
use(cached_templates);
```

---

### Optimization 3: Lazy Load Reports

**Principle:** Don't generate PDFs unless requested

**Flow:**
```
User: "Generate November report"

Claude: [Generate CSV first - fast]
"✅ CSV report ready (2 seconds)
• ~/Documents/MileageLog/reports/BA-789XY-nov-2025.csv

Would you also like PDF format? (adds 5 seconds)"

User: "Yes"

Claude: [Generate PDF - slow]
"✅ PDF report ready (5 seconds)
• ~/Documents/MileageLog/reports/BA-789XY-nov-2025.pdf"
```

---

### Optimization 4: Smart Validation Triggers

**Always validate:**
- After checkpoint creation
- After trip creation/update
- Before report generation

**Skip validation:**
- If validation just ran (<30 seconds ago)
- During batch operations (validate once at end)
- For read-only queries

**Example:**
```typescript
if (last_validation_timestamp < 30_seconds_ago) {
  skip_validation("already validated recently");
}

if (batch_operation) {
  defer_validation_until_end();
}
```

---

## User Experience Guidelines

### Guideline 1: Always Confirm Destructive Actions

**Examples:**
```
✅ "I found 3 gap proposals. Approve all? (yes/no/review)"
✅ "Delete template 'Warehouse Run'? (yes/no)"
✅ "Override validation warning? (yes/no)"

❌ [Silently creates 10 trips]
❌ [Deletes template without asking]
❌ [Ignores validation errors]
```

---

### Guideline 2: Progressive Disclosure

**Principle:** Show summary first, details on request

**Examples:**
```
✅ "Gap detected: 820km (Nov 1-5). View details? (yes/no)"
    [User: yes]
    "Gap spans 2 checkpoints:
    • Nov 1: OMV Bratislava (50,000km)
    • Nov 5: Shell Košice (50,820km)
    Missing: ~2 trips (based on typical patterns)"

❌ "Gap detected between checkpoint ABC123 and DEF456.
    Start: 2025-11-01T08:00:00Z, GPS 48.1486,17.1077
    End: 2025-11-05T14:30:00Z, GPS 48.7164,21.2611
    Delta: 820.00km, Fuel: 72.8L..."
```

---

### Guideline 3: Contextual Help

**Examples:**
```
First-time template creation:
"I'll help you create a template. Templates let me automatically
match future trips, saving you time. Let's start with where this
trip usually begins..."

First gap detection:
"I found a gap (820km between checkpoints). This means there are
trips not yet logged. I can help reconstruct them using your
templates or you can add them manually."

First validation warning:
"This efficiency (12.8 L/100km) is 38% above your average. This
could be normal (heavy load, city driving) or a data error. I'm
flagging it for your review."
```

---

### Guideline 4: Clear Next Steps

**Always end with:**
```
✅ Action confirmation + What's next

"✅ Template created!
I'll recognize this route automatically on future trips.
Would you like to create another template?"

"✅ Gap closed with 2 trips!
All trips now recorded. Generate report? (yes/no)"

"✅ Report generated!
Files saved to ~/Documents/MileageLog/reports/
Email to accountant? (P1 feature coming soon)"
```

---

## Slovak Compliance Checklist

### Before Report Generation

```
✅ Vehicle Compliance:
   • VIN: 17 chars, valid format (no I/O/Q)
   • License plate: XX-123XX format

✅ Trip Compliance (per trip):
   • Driver name: Present (not empty)
   • Trip start datetime: ISO 8601 format
   • Trip end datetime: ISO 8601 format
   • Start location: Present (address or GPS)
   • End location: Present (address or GPS)
   • Distance: > 0 km
   • Purpose: "Business" or "Personal"
   • Business description: Present if purpose = Business

✅ Fuel Compliance:
   • Efficiency: L/100km format (not km/L)
   • Refuel datetime: Separate from trip timing
   • Refuel timing: "before" | "during" | "after"

✅ Data Quality:
   • Distance sum: ±10% tolerance
   • Fuel consumption: ±15% tolerance
   • Efficiency: Within range for fuel type
```

---

### Compliance Validation Pattern

```typescript
async function validate_slovak_compliance(trips, vehicle) {
  const errors = [];
  const warnings = [];

  // Vehicle validation
  if (!validate_vin(vehicle.vin)) {
    errors.push("VIN invalid (must be 17 chars, no I/O/Q)");
  }

  // Per-trip validation
  for (const trip of trips) {
    if (!trip.driver_name) {
      errors.push(`Trip ${trip.trip_id}: Missing driver name (MANDATORY)`);
    }
    if (!trip.trip_start_datetime) {
      errors.push(`Trip ${trip.trip_id}: Missing start datetime`);
    }
    if (trip.purpose === "Business" && !trip.business_description) {
      errors.push(`Trip ${trip.trip_id}: Missing business description`);
    }
    if (trip.fuel_efficiency_format !== "L/100km") {
      warnings.push(`Trip ${trip.trip_id}: Use L/100km format (European)`);
    }
  }

  return { errors, warnings };
}
```

---

## Summary

**Key Takeaways:**

1. **Use skills in sequence:** Receipt → Gap → Reconstruction → Template → Report → Validation
2. **Chain skills logically:** Each skill output feeds next skill input
3. **Recover gracefully:** Always offer alternatives when tools fail
4. **Optimize performance:** Batch calls, cache static data, lazy load heavy operations
5. **Prioritize UX:** Confirm actions, progressive disclosure, clear next steps
6. **Enforce compliance:** Slovak VAT Act 2025 requirements are non-negotiable

**Quick Reference:**

| Skill | Priority | Frequency | Trigger |
|-------|----------|-----------|---------|
| F1: Receipt to Checkpoint | P0 | Per refuel | User scans receipt |
| F2: Gap Detection | P0 | Automatic | After 2+ checkpoints |
| F3: Trip Reconstruction | P0 | As needed | Gap + templates exist |
| F4: Template Creation | P0 | Occasional | User saves recurring route |
| F5: Report Generation | P0 | Monthly | End of period |
| F6: Data Validation | P0 | Automatic | After data entry |

---

**Last Updated:** 2025-11-20
**Version:** 1.0
