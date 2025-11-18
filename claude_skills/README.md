# Claude Desktop Skills for Car Log

**6 conversational skills** that make mileage tracking 10x faster than traditional apps.

---

## Overview

Claude Skills transform Car Log from a traditional MCP server backend into a **conversational AI assistant** that guides users through tax-compliant mileage tracking.

**Key Innovation:** Skills act as orchestrators, coordinating multiple MCP servers to create seamless workflows.

---

## Skills Summary

| # | Skill | Priority | Workflow | Time Saved |
|---|-------|----------|----------|------------|
| 1 | **Vehicle Setup** | P0 | Slovak VIN validation → compliant registration | 3 min → 30 sec |
| 2 | **Checkpoint from Receipt** | P0 | Photo paste → QR scan → EXIF → checkpoint | 3 min → 30 sec |
| 3 | **Trip Reconstruction** | P0 | GPS-first matching → 92% confidence proposals | 15 min → 2 min |
| 4 | **Template Creation** | P0 | Address → GPS geocoding → route calculation | 5 min → 1 min |
| 5 | **Report Generation** | P0 | Slovak VAT Act 2025 compliant CSV/PDF | 10 min → 1 min |
| 6 | **Data Validation** | P0 | Proactive 4-algorithm validation | Manual → Automatic |

**Total Time Savings:** ~30 minutes per refuel cycle → **10x faster workflow**

---

## Skill Descriptions

### 1. Vehicle Setup (Slovak Compliance)

**What it does:**
- Guides users through tax-compliant vehicle registration
- Validates VIN (17 chars, no I/O/Q - Slovak VAT Act 2025)
- Validates license plate format (BA-456CD)
- Sets L/100km fuel efficiency (European standard)

**Trigger words:** "add vehicle", "new car", license plate patterns

**MCP tools:** `car-log-core.create_vehicle`, `car-log-core.list_vehicles`

**Example:**
```
User: "Add BA-789XY Ford Transit diesel"
Claude: [validates VIN format]
✅ Registered! Ready to track trips.
```

---

### 2. Checkpoint from Receipt Photo

**What it does:**
- Scan QR code from Slovak e-Kasa receipt (multi-scale PDF)
- Fetch receipt from e-Kasa API (60s timeout)
- Extract GPS from dashboard photo EXIF
- Create checkpoint with receipt + GPS
- Automatically detect gaps (triggers reconstruction)

**Trigger words:** User pastes image, "refuel", "checkpoint"

**MCP tools:** `ekasa-api.scan_qr_code`, `ekasa-api.fetch_receipt_data`, `dashboard-ocr.extract_metadata`, `car-log-core.create_checkpoint`, `car-log-core.detect_gap`

**Example:**
```
User: [pastes receipt photo]
Claude: "QR code found... Fetching from e-Kasa (30s)...
✓ 52.3L Diesel @ €1.45/L
Now paste dashboard photo for GPS:"
User: [pastes dashboard]
Claude: "✓ GPS: 48.1486°N, 17.1077°E
✅ Checkpoint created!
⚠️ 820km gap detected. Reconstruct trips?"
```

---

### 3. Trip Reconstruction (GPS-First)

**What it does:**
- Detect gaps between checkpoints
- Match templates using hybrid GPS (70%) + address (30%)
- Present high-confidence proposals (>=70%)
- Create trips in batch
- Run 4 validation algorithms

**Trigger words:** Automatic after gap detection, "reconstruct", "fill trips"

**MCP tools:** `car-log-core.list_templates`, `geo-routing.calculate_route`, `trip-reconstructor.match_templates`, `car-log-core.create_trips_batch`, `validation.*`

**Example:**
```
Claude: "820km gap detected.
Matching templates...
✓ 2× Warehouse Run (92% confidence)
  GPS match: 98% (within 50m)
Accept? ✅ Created + validated!"
```

---

### 4. Template Creation (GPS Mandatory)

**What it does:**
- Geocode addresses to GPS coordinates (handles ambiguity)
- Calculate route alternatives (OSRM)
- Save template with GPS (mandatory for matching)
- Optional: day-of-week patterns, round trip, purpose

**Trigger words:** "create template", "save this route", "weekly trip"

**MCP tools:** `geo-routing.geocode_address`, `geo-routing.calculate_route`, `car-log-core.create_template`

**Example:**
```
User: "Save Warehouse Run"
Claude: "Where does it start?"
User: "Bratislava"
Claude: "Found 3 matches: [shows GPS coords]
Which? 1"
✓ GPS saved - 90%+ matching confidence!
```

---

### 5. Report Generation (Slovak VAT)

**What it does:**
- Query trips with filters (vehicle, date, purpose)
- Generate CSV for accounting software
- Generate PDF for archive
- Include all Slovak VAT Act 2025 required fields
- Show compliance checklist

**Trigger words:** "generate report", "export CSV", "November report"

**MCP tools:** `car-log-core.list_trips`, `report-generator.generate_csv`, `report-generator.generate_pdf`

**Example:**
```
User: "Generate November business report"
Claude: "✅ Reports generated!
1,850 km, €325.80, 12 trips
🇸🇰 Slovak compliance: ✅ All fields
📄 CSV + PDF ready"
```

---

### 6. Data Validation (Proactive)

**What it does:**
- Run 4 validation algorithms automatically
- Distance sum ±10%, Fuel ±15%, Efficiency range, Deviation ±20%
- Show warnings vs. blocking errors
- Provide contextual suggestions

**Trigger words:** Automatic after data entry, "check data", "validate"

**MCP tools:** `validation.validate_checkpoint_pair`, `validation.validate_trip`, `validation.check_efficiency`, `validation.check_deviation_from_average`

**Example:**
```
[After creating trip]
Claude: "Running validation...
✅ All checks passed!
• Distance: 820km (0% variance) ✓
• Fuel: 72.8L (+4.4%, within ±15%) ✓
• Efficiency: 8.9 L/100km (Diesel 5-15) ✓
• Deviation: +4.7% (under 20%) ✓"
```

---

## Installation

### Prerequisites

1. **Claude Desktop** installed
2. **MCP servers** running (local or Docker)
3. **Python 3.11+** (for local servers)
4. **Node.js 18+** (for geo-routing)

### Setup

1. **Configure MCP Servers** (see `../CLAUDE_DESKTOP_SETUP.md`)

2. **Create Skills in Claude Desktop**
   - Open Claude Desktop → Settings → Skills
   - For each skill (01-06):
     - Click "New Skill"
     - Copy content from corresponding `.md` file
     - Save

3. **Test Skills**
   ```
   "Add vehicle BA-123CD"           → Skill 1
   [paste receipt photo]            → Skill 2
   "Reconstruct November trips"     → Skill 3
   "Create Warehouse Run template"  → Skill 4
   "Generate report"                → Skill 5
   "Check my data"                  → Skill 6
   ```

---

## Architecture

### Orchestration Pattern

**Skills don't call MCP servers directly.**
Skills describe workflows → Claude interprets → Calls MCP tools → Returns results

```
User ↔ Claude Desktop ↔ Skill (workflow)
                      ↕
                   MCP Tools
                      ↕
             MCP Servers (7 servers)
                      ↕
                 JSON Files (data)
```

### Example: Trip Reconstruction Orchestration

```
Skill describes workflow:
1. Get gap data
2. Fetch templates
3. Calculate routes
4. Match templates
5. Present proposal
6. Create trips
7. Validate

Claude executes:
car-log-core.detect_gap(cp1, cp2)
car-log-core.list_templates()
geo-routing.calculate_route(...)
trip-reconstructor.match_templates(...)
→ Show proposal to user
car-log-core.create_trips_batch(...)
validation.validate_checkpoint_pair(...)
```

---

## Best Practices (from Claude Docs)

### 1. Clear Trigger Words

```
✅ Good: "add vehicle", "create template" (specific)
❌ Bad: "help", "do something" (ambiguous)
```

### 2. Step-by-Step Workflows

```
✅ Good: Collect data → Validate → Call tool → Confirm
❌ Bad: Call tool immediately without validation
```

### 3. Error Handling

```
✅ Good: "QR code not found. Try better lighting or enter manually:"
❌ Bad: "ERROR: QR_SCAN_FAILED"
```

### 4. User Confirmation

```
✅ Good: Show summary → Ask "Create this vehicle?"
❌ Bad: Create without confirmation
```

### 5. Progress Indicators

```
✅ Good: "Fetching from e-Kasa API (may take 30s)..."
❌ Bad: Silent wait for 30 seconds
```

---

## Testing

### Unit Testing (Per Skill)

```bash
# Test Skill 1: Vehicle Setup
Input: "Add BA-123CD Ford Transit diesel 125000"
Expected: Vehicle created with VIN validation

# Test Skill 2: Checkpoint
Input: [paste receipt photo] + [paste dashboard]
Expected: Checkpoint created with GPS + receipt data

# Test Skill 3: Reconstruction
Input: "Reconstruct from Nov 1"
Expected: Template proposals with confidence scores

# Test Skill 4: Template
Input: "Create template Warehouse Run"
Expected: Template with GPS coordinates saved

# Test Skill 5: Report
Input: "Generate November report"
Expected: CSV + PDF with Slovak compliance

# Test Skill 6: Validation
Input: [after creating trip]
Expected: 4 validation checks run automatically
```

### Integration Testing

```bash
# End-to-end workflow
1. Add vehicle (Skill 1)
2. Paste receipt (Skill 2)
3. Detect gap → reconstruct (Skill 3)
4. Create template from trip (Skill 4)
5. Generate report (Skill 5)
6. Validation runs throughout (Skill 6)
```

---

## Troubleshooting

### Skill Not Triggering

**Check:** Trigger words match user input
**Fix:** Add more trigger word variations

### MCP Tool Call Fails

**Check:** MCP servers running (`docker-compose ps`)
**Fix:** Restart servers (`docker-compose restart`)

### GPS Extraction Fails

**Check:** Photo has EXIF data (not screenshot)
**Fix:** Use phone camera app with location enabled

### e-Kasa Timeout

**Check:** Internet connection, API status
**Fix:** Fallback to manual entry

---

## Performance

**Typical Response Times:**

| Action | Time | Bottleneck |
|--------|------|------------|
| Vehicle setup | 1-2s | Validation logic |
| QR scan | 3-5s | Multi-scale detection |
| e-Kasa API | 5-30s | External API |
| GPS extraction | 1-2s | EXIF reading |
| Template matching | 2-4s | Haversine calculations |
| Report generation | 3-5s | File I/O |
| Validation | 1-2s | 4 algorithms |

**Optimization:**
- Cache geocoding results (24h TTL)
- Parallel MCP tool calls when possible
- Preload templates for matching

---

## Future Enhancements (Post-Hackathon)

### P1 Features

- **Skill 7: Dashboard OCR** - Read odometer with Claude Vision
- **Skill 8: Multi-Vehicle Management** - Switch between vehicles
- **Skill 9: Trip Editing** - Modify existing trips
- **Skill 10: Anomaly Detection** - ML-based fraud detection

### Advanced Workflows

- Voice input for hands-free logging
- Photo album batch processing
- Automatic template suggestion
- Predictive trip recommendations

---

## Documentation References

- **Claude Skills Documentation:** https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices
- **Creating Custom Skills:** https://support.claude.com/en/articles/12512198
- **MCP Tool Specifications:** `../spec/07-mcp-api-specifications.md`
- **Claude Desktop Setup:** `../CLAUDE_DESKTOP_SETUP.md`
- **Workflow Diagrams:** `../spec/09-hackathon-presentation.md`

---

## Success Metrics

After implementing these skills:

- ✅ Vehicle registration: 3 min → 30 sec (6x faster)
- ✅ Checkpoint creation: 3 min → 30 sec (6x faster)
- ✅ Trip reconstruction: 15 min → 2 min (7.5x faster)
- ✅ Report generation: 10 min → 1 min (10x faster)
- ✅ Data validation: Manual → Automatic
- ✅ **Overall: 10x productivity improvement**

---

**Last Updated:** November 18, 2025
**Status:** 📋 Specifications complete, implementation pending
**Estimated Implementation:** 15-20 hours total (all 6 skills)
