# Claude Desktop Testing Guide for Car Log

**Purpose:** Test all 6 conversational skills with Claude Desktop
**Prerequisites:** All 7 MCP servers running, Claude Desktop installed
**Estimated Time:** 15-20 hours (can be parallelized across testers)
**Priority:** P0 (Required for hackathon demo)

---

## Pre-Testing Setup

### Step 1: Install Prerequisites

**Required:**
- Claude Desktop (latest version)
- Python 3.11+ (for Python MCP servers)
- Node.js 18+ (for geo-routing server)
- All project dependencies installed

**Check:**
```bash
python --version  # Should be 3.11+
node --version    # Should be 18+
```

### Step 2: Configure MCP Servers

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

**Configuration:**
```json
{
  "mcpServers": {
    "car-log-core": {
      "command": "python",
      "args": ["-m", "mcp_servers.car_log_core"],
      "env": {
        "PYTHONPATH": "/path/to/car-log/mcp-servers",
        "DATA_PATH": "~/Documents/MileageLog/data",
        "USE_ATOMIC_WRITES": "true"
      }
    },
    "ekasa-api": {
      "command": "python",
      "args": ["-m", "mcp_servers.ekasa_api"],
      "env": {
        "PYTHONPATH": "/path/to/car-log/mcp-servers",
        "MCP_TIMEOUT_SECONDS": "60"
      }
    },
    "geo-routing": {
      "command": "node",
      "args": ["/path/to/car-log/mcp-servers/geo-routing/index.js"],
      "env": {
        "CACHE_TTL_HOURS": "24"
      }
    },
    "trip-reconstructor": {
      "command": "python",
      "args": ["-m", "mcp_servers.trip_reconstructor"],
      "env": {
        "PYTHONPATH": "/path/to/car-log/mcp-servers",
        "GPS_WEIGHT": "0.7",
        "ADDRESS_WEIGHT": "0.3"
      }
    },
    "validation": {
      "command": "python",
      "args": ["-m", "mcp_servers.validation"],
      "env": {
        "PYTHONPATH": "/path/to/car-log/mcp-servers"
      }
    },
    "dashboard-ocr": {
      "command": "python",
      "args": ["-m", "mcp_servers.dashboard_ocr"],
      "env": {
        "PYTHONPATH": "/path/to/car-log/mcp-servers"
      }
    },
    "report-generator": {
      "command": "python",
      "args": ["-m", "mcp_servers.report_generator"],
      "env": {
        "PYTHONPATH": "/path/to/car-log/mcp-servers"
      }
    }
  }
}
```

**Important:** Replace `/path/to/car-log` with actual project path.

### Step 3: Create Data Directories

```bash
mkdir -p ~/Documents/MileageLog/data/{vehicles,checkpoints,trips,templates,reports}
```

### Step 4: Restart Claude Desktop

Close and reopen Claude Desktop to load MCP server configuration.

### Step 5: Verify Server Discovery

In Claude Desktop, ask:
```
What MCP tools do you have access to?
```

**Expected Response:**
Claude should list all 28 tools from 7 MCP servers.

---

## Testing Workflow

Since skills are conversational patterns (not code), testing involves:

1. **Start conversation** with natural language
2. **Observe tool orchestration** (Claude calls multiple MCP tools)
3. **Verify file creation** (check ~/Documents/MileageLog/data/)
4. **Validate Slovak compliance** (VIN format, L/100km, etc.)
5. **Document issues** (errors, confusing prompts, missing validations)

---

## Skill Testing Scenarios

### Skill 1: Vehicle Setup (2 hours)

**Purpose:** Create and configure company vehicle with Slovak VAT compliance

**Test Scenario 1.1: Happy Path**

```
User: "I need to set up my company vehicle for mileage tracking"

Expected: Claude guides through vehicle setup, asking for:
- Make/model
- License plate (Slovak format: BA-456CD)
- VIN (17 characters, no I/O/Q)
- Fuel type (Diesel/Gasoline/LPG)
- Average fuel consumption (L/100km format)

Validation:
- File created: ~/Documents/MileageLog/data/vehicles/{vehicle_id}.json
- VIN validated (no I/O/Q characters)
- License plate validated (XX-123XX format)
- Fuel efficiency in L/100km (not km/L)
```

**Test Scenario 1.2: VIN Validation Error**

```
User: "VIN is WBAXX0123OABC5678" (contains 'O')

Expected: Claude rejects VIN, explains Slovak VAT Act requirement (no I/O/Q)

Validation:
- Error message clear and helpful
- No file created
- User can retry with correct VIN
```

**Test Scenario 1.3: Duplicate Vehicle**

```
User: "Add another vehicle with license plate BA-456CD"

Expected: Claude detects duplicate, asks if user wants to update existing vehicle

Validation:
- Duplicate detection works
- Offers update vs create new
- No corrupted data
```

---

### Skill 2: Checkpoint from Receipt (4 hours)

**Purpose:** Create checkpoint from refuel receipt with automatic GPS and gap detection

**Test Scenario 2.1: Photo with EXIF GPS**

```
User: [Pastes dashboard photo with EXIF GPS]
User: "I refueled today at 45120 km"

Expected: Claude:
1. Extracts GPS from EXIF metadata
2. Asks for receipt (or QR code if visible)
3. Creates checkpoint with GPS location
4. Detects gap if distance > 50 km from previous

Validation:
- GPS extracted from EXIF
- Checkpoint created in monthly folder
- Gap detected if applicable
- Odometer updated on vehicle
```

**Test Scenario 2.2: E-Kasa Receipt QR Code**

```
User: [Pastes e-Kasa receipt PDF/image with QR]
User: "Process this fuel receipt"

Expected: Claude:
1. Scans QR code (multi-scale detection if PDF)
2. Fetches receipt data from e-Kasa API (60s timeout)
3. Detects fuel type from Slovak names (Nafta, Natural 95)
4. Extracts fuel quantity, price, VAT
5. Creates checkpoint with receipt data

Validation:
- QR code scanned successfully
- API call completes (may take 5-30s)
- Fuel type detected correctly
- Receipt data embedded in checkpoint JSON
```

**Test Scenario 2.3: Manual Entry (No GPS/Receipt)**

```
User: "Manual checkpoint at 45300 km on November 15"

Expected: Claude creates checkpoint with:
- Manual odometer
- No GPS (acceptable)
- No receipt data
- Prompts for location (optional)

Validation:
- Manual checkpoint created
- No errors from missing GPS
- User can add location later
```

**Test Scenario 2.4: Gap Detection Trigger**

```
Setup: Previous checkpoint at 45000 km
User: "New checkpoint at 45820 km"

Expected: Claude:
1. Detects 820 km gap
2. Suggests trip reconstruction
3. Offers to match templates

Validation:
- Gap > 50 km detected
- Reconstruction suggested
- Workflow continues to Skill 3
```

---

### Skill 3: Trip Reconstruction (5 hours)

**Purpose:** Match gap to templates, propose trips, create batch trips

**Test Scenario 3.1: Perfect Template Match**

```
Setup: 
- Gap: 820 km (Checkpoint A → Checkpoint B)
- Template: "Warehouse Run" (410 km, Bratislava → Košice)

User: "Reconstruct my trips for this gap"

Expected: Claude:
1. Calls detect_gap to get gap data
2. Calls list_templates to get all templates
3. Calls match_templates with GPS-first scoring (70%)
4. Presents proposal:
   - 2× Warehouse Run (410 km each)
   - Coverage: 100%
   - Confidence: 90%+
5. Asks for approval

Validation:
- GPS matching weighted 70%
- Address matching weighted 30%
- Confidence >= 70% shown
- Coverage calculation correct
```

**Test Scenario 3.2: Batch Trip Creation**

```
User: "Yes, create those trips"

Expected: Claude:
1. Calls create_trips_batch with approved proposals
2. All trips created atomically (all or nothing)
3. Slovak compliance validated:
   - driver_name required
   - trip_start_datetime separate from refuel_datetime
   - L/100km fuel efficiency
   - Business trips have business_description
4. Automatic validation triggered

Validation:
- All trips created in ~/Documents/MileageLog/data/trips/2025-11/
- 25/25 unit tests passing for trip CRUD
- Slovak compliance fields present
- Validation results shown
```

**Test Scenario 3.3: Low Confidence Match**

```
Setup: Templates don't match well (confidence < 70%)

Expected: Claude:
1. Explains low confidence
2. Suggests creating new template
3. Offers manual trip entry

Validation:
- Low confidence communicated clearly
- Alternative workflows offered
- User not stuck
```

---

### Skill 4: Template Creation (3 hours)

**Purpose:** Create reusable trip templates with GPS and route calculation

**Test Scenario 4.1: Simple Template (GPS + Address)**

```
User: "Create template for my warehouse run from Bratislava to Košice"

Expected: Claude:
1. Geocodes "Bratislava" (may have alternatives)
2. Geocodes "Košice" (definitely has alternatives)
3. Presents alternatives for ambiguous addresses
4. Calculates route via OSRM (~410 km)
5. Creates template with:
   - GPS coordinates (mandatory)
   - Addresses (optional labels)
   - Distance from route calculation
   - Business purpose

Validation:
- GPS coordinates mandatory and present
- Addresses optional (can be missing)
- Distance calculated correctly (~410 km)
- Template saved with completeness score
```

**Test Scenario 4.2: Geocoding Ambiguity Handling**

```
User: "Košice"

Expected: Claude presents alternatives:
1. Košice (city, 48.7164, 21.2611)
2. Košice-okolie (district)
3. Košice Region

User selects option 1

Validation:
- Alternatives presented clearly
- User can choose
- Selected coordinates used
```

**Test Scenario 4.3: Template Completeness**

```
User: "Create minimal template with just GPS"

Expected: Claude:
1. Creates template with GPS only
2. Calculates completeness (~30%)
3. Suggests adding:
   - Address labels
   - Typical days (Monday, Thursday)
   - Business description

Validation:
- Template created successfully
- Completeness calculation correct
- Suggestions contextual
```

---

### Skill 5: Report Generation (2 hours)

**Purpose:** Generate Slovak VAT-compliant CSV reports

**Test Scenario 5.1: Monthly Business Report**

```
User: "Generate November 2025 mileage report for business trips"

Expected: Claude:
1. Lists trips for November
2. Filters for Business trips only
3. Calculates summary:
   - Total distance
   - Total fuel consumption
   - Average efficiency (L/100km)
4. Generates CSV with Slovak compliance:
   - VIN
   - Driver name
   - Trip start/end datetimes (separate from refuel)
   - Locations
   - L/100km format
5. Saves to ~/Documents/MileageLog/data/reports/2025-11/

Validation:
- CSV format correct
- All Slovak compliance fields present
- Business trips only (Personal filtered out)
- Summary statistics accurate
- File saved in monthly folder
```

**Test Scenario 5.2: Date Range Report**

```
User: "Report for October 15 to November 15"

Expected: Claude filters trips by date range correctly

Validation:
- Date filtering works
- Cross-month trips included
- Summary accurate
```

---

### Skill 6: Data Validation (2 hours)

**Purpose:** Proactive validation with 4 algorithms

**Test Scenario 6.1: Distance Sum Validation**

```
Setup:
- Checkpoint A: 45000 km
- Checkpoint B: 45820 km (820 km odometer delta)
- Trips sum: 800 km

Expected: Claude runs validate_checkpoint_pair:
- Calculates 20 km difference
- 20 km / 820 km = 2.4% (within ±10% threshold)
- Result: OK

Validation:
- Distance variance <= 10% passes
- Distance variance > 10% fails
- Clear error messages
```

**Test Scenario 6.2: Fuel Consumption Validation**

```
Setup:
- Trip: 410 km
- Vehicle avg: 8.5 L/100km
- Expected fuel: 34.85 L
- Actual refuel: 50 L

Expected: Claude runs validate_trip:
- Calculates 15.15 L difference
- 15.15 / 34.85 = 43% (exceeds ±15% threshold)
- Result: ERROR

Validation:
- Fuel variance <= 15% passes
- Fuel variance > 15% fails
- Suggests checking for errors
```

**Test Scenario 6.3: Efficiency Reasonability**

```
Setup:
- Vehicle: Diesel
- Trip efficiency: 2.0 L/100km (unrealistically low)

Expected: Claude runs check_efficiency:
- Compares to Diesel range (5-15 L/100km)
- 2.0 < 5.0 minimum
- Result: WARNING (unrealistically low)

Validation:
- Diesel: 5-15 L/100km enforced
- Gasoline: 6-20 L/100km enforced
- Warnings for extreme values
```

**Test Scenario 6.4: Deviation from Average**

```
Setup:
- Vehicle avg: 8.5 L/100km
- Trip: 12.0 L/100km

Expected: Claude runs check_deviation_from_average:
- Calculates 3.5 L difference
- 3.5 / 8.5 = 41% deviation (exceeds 20% threshold)
- Result: WARNING

Validation:
- Deviation <= 20% passes
- Deviation > 20% warns
- Contextual suggestions (highway vs city)
```

---

## Integration Testing (2 hours)

**Test End-to-End Workflow:**

```
1. Skill 1: Set up vehicle
   └─ Vehicle created with VIN, license plate

2. Skill 2: Create first checkpoint
   └─ Checkpoint A at 45000 km

3. Skill 2: Create second checkpoint
   └─ Checkpoint B at 45820 km
   └─ Gap detected (820 km)

4. Skill 3: Reconstruct trips
   └─ 2× trips created (410 km each)
   └─ Slovak compliance validated

5. Skill 6: Validate data
   └─ 4 algorithms run
   └─ All validations pass

6. Skill 5: Generate report
   └─ CSV created with all trips
   └─ Slovak VAT compliance verified
```

**Validation:**
- Complete workflow works without manual intervention
- All files created correctly
- Slovak compliance throughout
- Time: < 15 minutes (vs ~90 minutes manual)

---

## Success Criteria

### Required (P0)
- [ ] All 7 MCP servers discoverable in Claude Desktop
- [ ] All 28 tools callable via Claude
- [ ] Skill 1: Vehicle setup works (VIN validation)
- [ ] Skill 2: Checkpoint creation works (GPS + receipt)
- [ ] Skill 3: Trip reconstruction works (template matching)
- [ ] Skill 4: Template creation works (geocoding)
- [ ] Skill 5: Report generation works (CSV with Slovak compliance)
- [ ] Skill 6: Validation works (4 algorithms)
- [ ] End-to-end workflow completes successfully
- [ ] Demo video recorded

### Nice-to-Have (P1)
- [ ] Error recovery workflows documented
- [ ] Edge cases handled (missing GPS, API timeouts)
- [ ] Multi-vehicle support tested
- [ ] Performance optimized (< 5s per operation)

---

## Troubleshooting

### Issue: MCP servers not discovered
**Solution:**
1. Check claude_desktop_config.json syntax (valid JSON)
2. Verify PYTHONPATH points to mcp-servers directory
3. Restart Claude Desktop
4. Check server logs

### Issue: Tool calls timeout
**Solution:**
1. Increase MCP_TIMEOUT_SECONDS (ekasa-api: 60s)
2. Check network connection (for external APIs)
3. Verify MCP server is running

### Issue: VIN validation fails
**Solution:**
1. Ensure VIN has no I/O/Q characters
2. Check VIN is exactly 17 characters
3. Use example: WBAXX01234ABC5678

### Issue: Files not created
**Solution:**
1. Check DATA_PATH environment variable
2. Verify directory permissions
3. Check atomic write temp files (.tmp)

### Issue: Geocoding ambiguous
**Solution:**
1. This is expected for cities like "Košice"
2. Select from alternatives
3. Use more specific address

---

## Test Results Template

```markdown
## Claude Desktop Skills Test Results

**Date:** YYYY-MM-DD
**Tester:** [Name]
**Claude Desktop Version:** X.Y.Z

### Skill 1: Vehicle Setup
- [ ] ✅ PASS / ❌ FAIL - VIN validation
- [ ] ✅ PASS / ❌ FAIL - License plate format
- [ ] ✅ PASS / ❌ FAIL - File creation
- **Issues:** [None / List issues]

### Skill 2: Checkpoint from Receipt
- [ ] ✅ PASS / ❌ FAIL - EXIF GPS extraction
- [ ] ✅ PASS / ❌ FAIL - E-Kasa QR scanning
- [ ] ✅ PASS / ❌ FAIL - Gap detection
- **Issues:** [None / List issues]

### Skill 3: Trip Reconstruction
- [ ] ✅ PASS / ❌ FAIL - Template matching
- [ ] ✅ PASS / ❌ FAIL - Batch trip creation
- [ ] ✅ PASS / ❌ FAIL - Slovak compliance
- **Issues:** [None / List issues]

### Skill 4: Template Creation
- [ ] ✅ PASS / ❌ FAIL - Geocoding
- [ ] ✅ PASS / ❌ FAIL - Route calculation
- [ ] ✅ PASS / ❌ FAIL - GPS mandatory
- **Issues:** [None / List issues]

### Skill 5: Report Generation
- [ ] ✅ PASS / ❌ FAIL - CSV generation
- [ ] ✅ PASS / ❌ FAIL - Slovak compliance fields
- [ ] ✅ PASS / ❌ FAIL - Business trip filtering
- **Issues:** [None / List issues]

### Skill 6: Data Validation
- [ ] ✅ PASS / ❌ FAIL - Distance validation
- [ ] ✅ PASS / ❌ FAIL - Fuel validation
- [ ] ✅ PASS / ❌ FAIL - Efficiency check
- [ ] ✅ PASS / ❌ FAIL - Deviation check
- **Issues:** [None / List issues]

### Integration Testing
- [ ] ✅ PASS / ❌ FAIL - End-to-end workflow
- **Time:** [X] minutes (target: < 15 minutes)

### Overall Result
- [ ] ✅ APPROVED FOR DEMO
- [ ] ⚠️ APPROVED WITH ISSUES (list below)
- [ ] ❌ REJECTED (critical issues found)

**Critical Issues:**
1. [Issue description]

**Notes:**
[Additional observations]
```

---

## Next Steps After Testing

1. **If PASS:** Record demo video showcasing conversational workflows
2. **If FAIL:** Fix critical issues, refine skill descriptions, re-test
3. **If APPROVED:** Update TASKS.md Track F as ✅ COMPLETE
4. **Prepare Demo:** Practice 5-minute demo script (see 09-hackathon-presentation.md)

---

**Estimated Total Testing Time:** 15-20 hours
**Can Be Parallelized:** Multiple testers can test different skills simultaneously
**Priority:** P0 (Required for hackathon submission)
**Blocking:** None (all backend servers ready)
