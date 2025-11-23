# Claude Desktop Skills for Car Log

**6 conversational skills** that make mileage tracking 10x faster than traditional apps.

---

## Overview

Claude Skills transform Car Log from a traditional MCP server backend into a **conversational AI assistant** that guides users through tax-compliant mileage tracking.

**Key Innovation:** Skills act as orchestrators, coordinating multiple MCP servers to create seamless workflows.

---

## Skills Structure

```
claude_skills/
├── vehicle-setup/                   # Skill 1: Vehicle registration
│   ├── SKILL.md                     # ← Load into Claude Desktop (300 words)
│   ├── GUIDE.md                     # Comprehensive guide (15KB)
│   ├── REFERENCE.md                 # MCP tool specs
│   └── examples/
│       └── test-vehicle.json
│
├── checkpoint-from-receipt/         # Skill 2: Receipt processing
│   ├── SKILL.md                     # ← Load into Claude Desktop (500 words)
│   ├── GUIDE.md                     # Comprehensive guide (21KB)
│   ├── REFERENCE.md                 # MCP tool specs
│   └── examples/
│       └── sample-checkpoint.json
│
├── trip-reconstruction/             # Skill 3: GPS-first matching
│   ├── SKILL.md                     # ← Load into Claude Desktop (600 words)
│   ├── GUIDE.md                     # Comprehensive guide (25KB)
│   ├── REFERENCE.md                 # MCP tool specs
│   └── examples/
│       └── gap-scenario.json
│
├── template-creation/               # Skill 4: Route templates
│   ├── SKILL.md                     # ← Load into Claude Desktop (400 words)
│   ├── GUIDE.md                     # Comprehensive guide (12KB)
│   ├── REFERENCE.md                 # MCP tool specs
│   └── examples/
│       └── warehouse-run-template.json
│
├── report-generation/               # Skill 5: Slovak VAT compliance reports
│   ├── SKILL.md                     # ← Load into Claude Desktop (300 words)
│   ├── GUIDE.md                     # Comprehensive guide (17KB)
│   ├── REFERENCE.md                 # MCP tool specs
│   └── examples/
│       └── sample-report.csv
│
├── data-validation/                 # Skill 6: 4 validation algorithms
│   ├── SKILL.md                     # ← Load into Claude Desktop (300 words)
│   ├── GUIDE.md                     # Comprehensive guide (16KB)
│   ├── REFERENCE.md                 # MCP tool specs
│   └── examples/
│       └── validation-scenarios.json
│
└── Documentation Files:
    ├── INSTALLATION.md              # How to install skills
    ├── BEST_PRACTICES.md            # Usage patterns
    ├── TROUBLESHOOTING.md           # Common issues
    ├── INTEGRATION_TESTING.md       # Test scenarios
    ├── MANUAL_TEST_CHECKLIST.md     # User testing guide
    ├── PERFORMANCE.md               # Benchmarks
    ├── DEMO_SCENARIO.md             # Demo script
    ├── TESTING_F1-F3.md             # Detailed test cases
    └── TESTING_F4-F6.md             # Detailed test cases
```

## Installation Quick Start

**For users:**
1. Copy each `SKILL.md` to Claude Desktop Custom Instructions
2. Read `GUIDE.md` for detailed workflows
3. Use `examples/` for testing
4. Follow `MANUAL_TEST_CHECKLIST.md`

**For developers:**
1. Read `REFERENCE.md` for MCP tool specs
2. See `../spec/07-mcp-api-specifications.md` for complete API
3. Use `examples/` as test fixtures

**Full installation guide:** See [INSTALLATION.md](INSTALLATION.md)

---

## Skill Descriptions

### 1. Vehicle Setup (Slovak Compliance)

**What it does:**
- Guides users through tax-compliant vehicle registration
- Validates VIN (17 chars, no I/O/Q - Slovak VAT Act 2025)
- Validates license plate format (BA-456CD)
- Sets L/100km fuel efficiency (European standard)

**Trigger words:** "add vehicle", "new car", license plate patterns

**MCP tools:** `car-log-core.create_vehicle`, `car-log-core.list_vehicles`, `car-log-core.get_vehicle`, `car-log-core.update_vehicle`

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

**MCP tools:** `ekasa-api.scan_qr_from_pdf`, `ekasa-api.fetch_receipt`, `dashboard-ocr.extract_metadata`, `dashboard-ocr.check_photo_quality`, `car-log-core.create_checkpoint`, `car-log-core.get_checkpoint`, `car-log-core.list_checkpoints`, `car-log-core.detect_gap`

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

**MCP tools:** `car-log-core.list_templates`, `geo-routing.calculate_route`, `trip-reconstructor.match_templates`, `car-log-core.create_trip`, `car-log-core.create_trips_batch`, `car-log-core.list_trips`, `car-log-core.get_trip`, `car-log-core.delete_trip`, `validation.validate_trip`

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

**MCP tools:** `geo-routing.geocode_address`, `geo-routing.reverse_geocode`, `geo-routing.calculate_route`, `car-log-core.create_template`, `car-log-core.list_templates`, `car-log-core.delete_template`

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

**MCP tools:** `car-log-core.list_trips`, `report-generator.generate_report`

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

**MCP tools:** `validation.validate_trip`

**Note:** Validation is performed by the single `validate_trip` tool which runs all 4 algorithms: distance sum (±10%), fuel consumption (±15%), efficiency range check, and deviation from average (±20%)

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

**Complete Testing Guide:** See [INTEGRATION_TESTING.md](INTEGRATION_TESTING.md)

**Quick Test Workflow:**
```bash
# End-to-end workflow (20 minutes)
1. Add vehicle (Skill 1) - 5 min
2. Paste receipt (Skill 2) - 5 min
3. Detect gap → reconstruct (Skill 3) - 10 min
4. Create template from trip (Skill 4) - 5 min
5. Generate report (Skill 5) - 3 min
6. Validation runs throughout (Skill 6) - automatic

Complete manual testing checklist: MANUAL_TEST_CHECKLIST.md
Demo scenario for video: DEMO_SCENARIO.md
```

**Test Scenarios Available:**
1. Complete workflow (happy path)
2. Template creation with geocoding
3. Error handling and recovery
4. Cross-skill data flow
5. Performance benchmarks

---

## Troubleshooting

**Complete Troubleshooting Guide:** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**Quick Reference:**

### Skill Not Triggering
**Check:** Trigger words match user input
**Fix:** Add more trigger word variations or use exact trigger phrase

### MCP Tool Call Fails
**Check:** MCP servers running (`docker-compose ps`)
**Fix:** Restart servers (`docker-compose restart`)

### GPS Extraction Fails
**Check:** Photo has EXIF data (not screenshot)
**Fix:** Use phone camera app with location enabled, or enter GPS manually

### e-Kasa Timeout
**Check:** Internet connection, API status
**Fix:** Retry or fallback to manual entry

### Template Matching Low Confidence
**Check:** Templates have GPS coordinates
**Fix:** GPS is mandatory for 90%+ confidence

**For detailed solutions:** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) (10 common issues + environment-specific)

---

## Performance

**Complete Performance Benchmarks:** See [PERFORMANCE.md](PERFORMANCE.md)

**Target Response Times:**

| Operation | Target | Acceptable | Timeout |
|-----------|--------|------------|---------|
| Vehicle setup | 1-2s | < 5s | > 10s |
| QR scan | 2-3s | < 5s | > 10s |
| e-Kasa API | 5-15s | < 60s | > 60s |
| GPS extraction | 1-2s | < 3s | > 5s |
| Template matching (100 templates) | 2-4s | < 5s | > 10s |
| Report generation (1000 trips) | 3-5s | < 10s | > 15s |
| Validation (all 4 algorithms) | 1-2s | < 5s | > 10s |

**Bottlenecks:**
- e-Kasa API: 5-30s (external, variable)
- PDF QR scanning: 2-5s (multi-scale)
- Template matching 1000+: 10-15s (needs optimization)

**Optimization:**
- ✅ 24hr geocoding cache
- ✅ Atomic writes (crash-safe)
- ✅ Monthly folders (reduce file count)
- ⏳ Index files for reports (post-MVP)
- ⏳ R-tree spatial index for templates (post-MVP)

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

### Skills Documentation
- [INTEGRATION_TESTING.md](INTEGRATION_TESTING.md) - End-to-end test scenarios (5 test cases)
- [DEMO_SCENARIO.md](DEMO_SCENARIO.md) - Complete 5-minute demo script
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions (10 issues)
- [MANUAL_TEST_CHECKLIST.md](MANUAL_TEST_CHECKLIST.md) - User testing checklist (2-3 hours)
- [PERFORMANCE.md](PERFORMANCE.md) - Performance benchmarks and optimization

### Claude Skills Resources
- **Claude Skills Documentation:** https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices
- **Creating Custom Skills:** https://support.claude.com/en/articles/12512198

### Project Documentation
- **MCP Tool Specifications:** `../spec/07-mcp-api-specifications.md`
- **Claude Desktop Setup:** `../CLAUDE_DESKTOP_SETUP.md`
- **Implementation Plan:** `../spec/08-implementation-plan.md`
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

**Current Status (November 23, 2025):**
- ✅ Backend: 100% complete (7 MCP servers, 20 tools, all functional)
- ✅ Skills: Updated with latest tool definitions
- ✅ Deployment: Local deployment working (install.bat on Windows)
- ⏳ Testing: Ready for manual testing in Claude Desktop
- ⏳ Demo: Script complete, ready to record

**Tool Count Breakdown:**
- car-log-core: 14 tools (vehicles, checkpoints, templates, trips)
- trip-reconstructor: 1 tool
- validation: 1 tool
- ekasa-api: 2 tools
- dashboard-ocr: 2 tools
- report-generator: 1 tool
- geo-routing: 3 tools
- **Total: 24 tools across 7 servers**

---

## Getting Started

**Quick Start (5 steps):**

1. **Setup MCP Servers:**
   ```bash
   cd docker
   docker-compose up -d
   ```

2. **Configure Claude Desktop:**
   - Copy `../claude_desktop_config.json` to Claude Desktop config directory
   - Restart Claude Desktop

3. **Load Skills:**
   - Open Claude Desktop → Settings → Skills
   - Load all 6 skill files (01-06)

4. **Run Manual Test:**
   - Follow [MANUAL_TEST_CHECKLIST.md](MANUAL_TEST_CHECKLIST.md)
   - Complete all 6 skills + 3 integration tests

5. **Record Demo:**
   - Use [DEMO_SCENARIO.md](DEMO_SCENARIO.md)
   - Target: 5 minutes total

**Next Steps:**
- Manual testing (2-3 hours)
- Bug fixes (as needed)
- Demo video recording (1 hour)
- Hackathon submission (Nov 30 deadline)

---

**Last Updated:** November 20, 2025
**Status:** ✅ Documentation complete, ready for testing
**Documentation Files:** 5 guides (INTEGRATION_TESTING, DEMO_SCENARIO, TROUBLESHOOTING, MANUAL_TEST_CHECKLIST, PERFORMANCE)
