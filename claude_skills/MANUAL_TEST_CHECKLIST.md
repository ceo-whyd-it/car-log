# Claude Skills Manual Test Checklist

**Project:** Car Log - Slovak Tax-Compliant Mileage Logger
**Purpose:** User-friendly checklist for manual testing in Claude Desktop
**Estimated Time:** 2-3 hours for complete testing
**Last Updated:** November 20, 2025

---

## Prerequisites Checklist

Before you start testing, verify all prerequisites are met:

### System Setup
- [ ] **Claude Desktop** installed and running
- [ ] **Docker Desktop** installed (or local Python 3.11+ / Node.js 18+)
- [ ] **Git** installed (for cloning repository)
- [ ] **Disk space:** At least 1 GB free

### Repository Setup
- [ ] Repository cloned: `git clone [repository-url]`
- [ ] In project directory: `cd car-log`
- [ ] Branch checked out: `git status` (should show main or demo branch)

### MCP Servers Setup
- [ ] All 7 servers running: `docker-compose ps` (all "Up")
  - `car-log-core`
  - `ekasa-api`
  - `geo-routing`
  - `trip-reconstructor`
  - `validation`
  - `dashboard-ocr`
  - `report-generator`

- [ ] If not running: `cd docker && docker-compose up -d`
- [ ] Check logs for errors: `docker-compose logs` (no ERROR messages)

### Claude Desktop Configuration
- [ ] Config file exists:
  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
  - Linux: `~/.config/Claude/claude_desktop_config.json`

- [ ] Config file content matches `claude_desktop_config.json` in repository
- [ ] Claude Desktop restarted after config changes

### Data Directory Setup
- [ ] Data directory exists: `~/Documents/MileageLog/data/`
- [ ] Subdirectories created:
  - [ ] `vehicles/`
  - [ ] `checkpoints/2025-11/`
  - [ ] `trips/2025-11/`
  - [ ] `templates/`
  - [ ] `reports/2025-11/`

- [ ] Permissions correct: `chmod -R 755 ~/Documents/MileageLog/data/`

### Skills Loaded
- [ ] Open Claude Desktop → Settings → Skills
- [ ] Load each skill (copy from `claude_skills/` directory):
  - [ ] 01-vehicle-setup.md → "Vehicle Setup"
  - [ ] 02-checkpoint-from-receipt.md → "Checkpoint from Receipt"
  - [ ] 03-trip-reconstruction.md → "Trip Reconstruction"
  - [ ] 04-template-creation.md → "Template Creation"
  - [ ] 05-report-generation.md → "Report Generation"
  - [ ] 06-data-validation.md → "Data Validation"

- [ ] All 6 skills appear in skills list

### Test Data Prepared
- [ ] Sample receipt photo with QR code (`examples/receipt1.jpg`)
- [ ] Sample dashboard photo with GPS EXIF (`examples/dashboard1.jpg`)
- [ ] Second set for gap testing (receipt2.jpg, dashboard2.jpg)
- [ ] Optional: Generate mock data `python scripts/generate_mock_data.py --scenario demo`

**✅ Prerequisites Complete** - Ready to start testing!

---

## Test 1: Skill 1 - Vehicle Setup

**Duration:** 5 minutes
**Goal:** Register a vehicle with Slovak compliance

### Step 1.1: Valid Vehicle Registration
- [ ] Open Claude Desktop
- [ ] Type: "Add vehicle BA-456CD Ford Transit diesel"
- [ ] **Expected:** Claude asks for VIN
- [ ] Respond: "VIN is WBAXX01234ABC5678"
- [ ] **Expected:** Claude asks for odometer reading
- [ ] Respond: "125000 km"
- [ ] **Expected:** Claude asks for average fuel efficiency
- [ ] Respond: "8.5 L per 100km"
- [ ] **Expected:**
  - ✅ Vehicle created successfully
  - Message shows validation passed (VIN 17 chars, no I/O/Q)
  - License plate format validated (BA-456CD)
  - L/100km format used (not km/L)

### Step 1.2: Verify Vehicle File Created
- [ ] Open terminal/Finder
- [ ] Navigate to: `~/Documents/MileageLog/data/vehicles/`
- [ ] **Expected:** JSON file exists with vehicle data
- [ ] Open file and verify:
  - [ ] `vin`: "WBAXX01234ABC5678"
  - [ ] `license_plate`: "BA-456CD"
  - [ ] `fuel_type`: "Diesel"
  - [ ] `average_efficiency`: 8.5

### Step 1.3: Test Invalid VIN (Error Handling)
- [ ] Type: "Add vehicle BA-789XY BMW"
- [ ] Respond with invalid VIN: "12345"
- [ ] **Expected:**
  - ❌ Error message: "VIN must be exactly 17 characters"
  - Vehicle NOT created

- [ ] Try VIN with forbidden characters: "12345678901234IOQ"
- [ ] **Expected:**
  - ❌ Error message: "VIN cannot contain I, O, or Q"

### Step 1.4: List Vehicles
- [ ] Type: "List my vehicles"
- [ ] **Expected:**
  - Shows Ford Transit BA-456CD
  - Shows vehicle details (make, model, license plate)

**✅ Test 1 Complete** - Vehicle registration working

---

## Test 2: Skill 2 - Checkpoint from Receipt

**Duration:** 10 minutes
**Goal:** Create checkpoint from receipt photo + GPS

### Step 2.1: Paste Receipt Photo
- [ ] Open Claude Desktop
- [ ] Copy receipt photo: `examples/receipt1.jpg`
- [ ] Paste into Claude Desktop chat (Cmd+V / Ctrl+V)
- [ ] **Expected:**
  - Claude detects image
  - "Scanning QR code..."
  - "Found e-Kasa receipt. Fetching from API (may take 30s)..."

### Step 2.2: Wait for e-Kasa API Response
- [ ] Wait (5-30 seconds normal, 60 seconds max)
- [ ] **Expected:**
  - Receipt details displayed:
    - Vendor name
    - Fuel type (Diesel, Nafta, Natural 95, etc.)
    - Quantity (L)
    - Price per liter
    - Total price (incl. VAT)
  - "Now paste dashboard photo for GPS coordinates"

- [ ] **If timeout occurs:**
  - [ ] Retry: "Retry"
  - [ ] OR enter manually: "52.3L Diesel at €1.47/L"

### Step 2.3: Paste Dashboard Photo
- [ ] Copy dashboard photo: `examples/dashboard1.jpg`
- [ ] Paste into chat
- [ ] **Expected:**
  - "GPS extracted from photo EXIF"
  - Shows coordinates (e.g., 48.1486°N, 17.1077°E)
  - Shows location name (if reverse geocoded)
  - "What was the odometer reading?"

- [ ] **If GPS fails:**
  - [ ] Claude offers fallback: "Enter GPS manually" or "Enter address"
  - [ ] Test manual GPS: "48.1486, 17.1077"

### Step 2.4: Enter Odometer Reading
- [ ] Type: "45000 km"
- [ ] **Expected:**
  - ✅ Checkpoint created!
  - Shows summary:
    - Date/time
    - Location (GPS + address if available)
    - Odometer: 45,000 km
    - Fuel: 52.3 L Diesel
    - Price
  - "No gap detected yet (first checkpoint)"

### Step 2.5: Verify Checkpoint File Created
- [ ] Navigate to: `~/Documents/MileageLog/data/checkpoints/2025-11/`
- [ ] **Expected:** JSON file exists
- [ ] Open file and verify:
  - [ ] `checkpoint_type`: "refuel"
  - [ ] `odometer_km`: 45000
  - [ ] `location.coords`: {"latitude": 48.1486, "longitude": 17.1077}
  - [ ] `receipt.fuel_liters`: 52.3
  - [ ] `receipt.fuel_type`: "Diesel"
  - [ ] `receipt.price_incl_vat`: (price from receipt)

**✅ Test 2 Complete** - Checkpoint creation working

---

## Test 3: Skill 2 + Skill 3 - Gap Detection & Reconstruction

**Duration:** 15 minutes
**Goal:** Create second checkpoint, detect gap, reconstruct trips

### Step 3.1: Create Second Checkpoint (7 Days Later)
- [ ] Wait or change system date (optional for testing)
- [ ] Paste second receipt photo: `examples/receipt2.jpg`
- [ ] **Expected:** QR scan + e-Kasa fetch
- [ ] Paste second dashboard photo: `examples/dashboard2.jpg`
- [ ] **Expected:** GPS extraction
- [ ] Enter odometer: "45820 km"
- [ ] **Expected:**
  - ✅ Checkpoint created
  - ⚠️ **Gap detected!**
  - "Gap: 820 km between Nov 1 (45,000 km) and Nov 8 (45,820 km)"
  - "Would you like me to reconstruct trips for this gap?"

### Step 3.2: Trigger Trip Reconstruction
- [ ] Type: "Yes, reconstruct trips"
- [ ] **Expected:**
  - "Analyzing 820 km gap..."
  - "Fetching templates..."
  - "Matching using GPS-first algorithm..."

### Step 3.3: Review Template Matching Results
- [ ] **Expected results format:**
  ```
  Match Results:

  🎯 High Confidence Matches (≥70%):

  1. [Template Name] - XX% confidence
     • Distance: XXX km
     • GPS Match: XX% (within XXm)
     • Address Match: XX%
     • Day Match: ✓/✗
     • Purpose: Business/Personal
     • Suggested: [count]×

  Coverage: XX% (XXX km / 820 km)
  ```

- [ ] **If NO templates exist yet:**
  - [ ] **Expected:** "No templates found. Create a template first?"
  - [ ] Skip to Test 4, then return to Test 3

- [ ] **If templates exist but low confidence (<70%):**
  - [ ] **Expected:** "No high-confidence matches. Would you like to:"
    - Create new template
    - Lower threshold
    - Manual entry

### Step 3.4: Accept Proposals
- [ ] Type: "Yes, accept"
- [ ] **Expected:**
  - "Creating [count] trips..."
  - "Running validation..."
  - Progress indicator

### Step 3.5: Review Validation Results
- [ ] **Expected validation output:**
  ```
  Validation complete:
  ✓ Distance sum: [X km] (X% variance) - OK/WARNING
  ✓ Fuel consumption: [X L] (±X%) - OK/WARNING
  ✓ Efficiency: [X L/100km] (Diesel 5-15 range) - OK
  ✓ Deviation: ±X% from average - OK/WARNING
  ```

- [ ] **If warnings shown:**
  - [ ] Warning message explains possible reasons
  - [ ] User can accept or edit data

### Step 3.6: Verify Trips Created
- [ ] Navigate to: `~/Documents/MileageLog/data/trips/2025-11/`
- [ ] **Expected:** 2 (or more) JSON files
- [ ] Open one file and verify:
  - [ ] `driver_name`: (your name)
  - [ ] `trip_start_datetime`: (ISO 8601 format)
  - [ ] `trip_end_datetime`: (ISO 8601 format)
  - [ ] `trip_start_location`: (start address)
  - [ ] `trip_end_location`: (end address)
  - [ ] `distance_km`: (matches template)
  - [ ] `fuel_efficiency_l_per_100km`: (calculated, not km/L!)
  - [ ] `purpose`: "Business" or "Personal"
  - [ ] `reconstruction_method`: "template"
  - [ ] `template_id`: (UUID reference)
  - [ ] `confidence_score`: (e.g., 92)

**✅ Test 3 Complete** - Gap detection and reconstruction working

---

## Test 4: Skill 4 - Template Creation

**Duration:** 10 minutes
**Goal:** Create trip template with GPS geocoding

### Step 4.1: Start Template Creation
- [ ] Type: "Create template for weekly warehouse run"
- [ ] **Expected:** "I'll help create a trip template. Where does this trip start?"

### Step 4.2: Test Ambiguous Address (Multiple Matches)
- [ ] Type: "Košice"
- [ ] **Expected:**
  - "Found [X] locations matching 'Košice':"
  - List of matches with GPS coordinates:
    - 1. Košice, Slovakia (48.7164°N, 21.2611°E) - City
    - 2. [Other matches...]
  - "Which location? (1-[X])"

- [ ] Type: "1"
- [ ] **Expected:** "GPS saved: 48.7164°N, 21.2611°E"

### Step 4.3: Test Single Match Address
- [ ] **Expected:** "Where does it end?"
- [ ] Type: "Hlavná 45, Bratislava"
- [ ] **Expected:**
  - "Found: Bratislava, Slovakia (48.1486°N, 17.1077°E)"
  - No alternatives (confidence > 0.9)
  - "Calculating route..."

### Step 4.4: Route Calculation
- [ ] **Expected:**
  - Route distance displayed (e.g., "~410 km via D1")
  - "This template will have 90%+ matching confidence due to GPS coordinates"
  - "Add optional details? (day-of-week patterns, round trip, purpose)"

### Step 4.5: Add Optional Details
- [ ] Type: "It's every Monday and Thursday, round trip, business"
- [ ] **Expected:**
  - Parses details:
    - typical_days: ["Monday", "Thursday"]
    - is_round_trip: true
    - purpose: "business"
  - "Template created!"
  - "Template completeness: XX%"

### Step 4.6: Verify Template File Created
- [ ] Navigate to: `~/Documents/MileageLog/data/templates/`
- [ ] **Expected:** JSON file exists
- [ ] Open file and verify:
  - [ ] `name`: "Weekly Warehouse Run" (or similar)
  - [ ] `from_coords`: {"lat": 48.7164, "lng": 21.2611}
  - [ ] `to_coords`: {"lat": 48.1486, "lng": 17.1077}
  - [ ] `from_address`: "Košice, Slovakia"
  - [ ] `to_address`: "Hlavná 45, Bratislava, Slovakia"
  - [ ] `distance_km`: 410 (approximate)
  - [ ] `typical_days`: ["Monday", "Thursday"]
  - [ ] `is_round_trip`: true
  - [ ] `purpose`: "business"

### Step 4.7: List Templates
- [ ] Type: "List my templates"
- [ ] **Expected:**
  - Shows created template
  - Shows completeness score
  - Shows last used date (if used)

**✅ Test 4 Complete** - Template creation working

---

## Test 5: Skill 5 - Report Generation

**Duration:** 10 minutes
**Goal:** Generate Slovak VAT-compliant CSV report

### Step 5.1: Generate Report
- [ ] Type: "Generate November business report"
- [ ] **Expected:**
  - "Generating CSV report for November 2025..."
  - "Filtering for Business trips only..."

### Step 5.2: Review Report Summary
- [ ] **Expected summary:**
  ```
  Report: november-2025.csv

  Summary:
  • Total trips: [X]
  • Total distance: [X km]
  • Total fuel: [X L]
  • Average efficiency: [X L/100km]
  • Total fuel cost: €[X]
  • VAT amount: €[X]

  Slovak VAT Act 2025 Compliance: ✅
  All mandatory fields present:
  ✓ VIN
  ✓ Driver name
  ✓ Trip start/end datetime (separate from refuel)
  ✓ Trip start/end location
  ✓ Distance, Fuel, Efficiency (L/100km)
  ✓ Business purpose
  ```

- [ ] Verify Personal trips excluded (if any exist)

### Step 5.3: Verify Report File Created
- [ ] Navigate to: `~/Documents/MileageLog/data/reports/2025-11/`
- [ ] **Expected:** `november-2025.csv` exists
- [ ] Open file in Excel/LibreOffice/text editor
- [ ] **Expected columns:**
  - [ ] Trip ID
  - [ ] Vehicle (VIN)
  - [ ] Driver Name
  - [ ] Trip Start Datetime
  - [ ] Trip End Datetime
  - [ ] Trip Start Location
  - [ ] Trip End Location
  - [ ] Distance (km)
  - [ ] Fuel Consumption (L)
  - [ ] Fuel Efficiency (L/100km) ← **NOT km/L!**
  - [ ] Purpose
  - [ ] Business Description
  - [ ] Refuel Datetime (separate from trip timing)

### Step 5.4: Verify Slovak Compliance
- [ ] Check VIN column: All 17 characters, no I/O/Q
- [ ] Check Efficiency column: Format "8.5 L/100km" (not "11.8 km/L")
- [ ] Check Trip Timing: Separate from refuel datetime
- [ ] Check Driver Name: Full name present

### Step 5.5: Test Date Range Filter (Optional)
- [ ] Type: "Generate report for November 1-15"
- [ ] **Expected:** Only trips in date range included

**✅ Test 5 Complete** - Report generation working

---

## Test 6: Skill 6 - Data Validation (Automatic)

**Duration:** 5 minutes
**Goal:** Verify validation runs automatically

### Step 6.1: Validation After Trip Creation
- [ ] **During Test 3** (trip reconstruction), validation ran automatically
- [ ] Review validation output from Test 3.5
- [ ] Confirm all 4 algorithms ran:
  - [ ] Distance sum check (±10%)
  - [ ] Fuel consumption check (±15%)
  - [ ] Efficiency range check (Diesel 5-15 L/100km)
  - [ ] Deviation from average check (±20%)

### Step 6.2: Test Manual Validation Trigger
- [ ] Type: "Check my November data"
- [ ] **Expected:**
  - Validation runs on all trips
  - Summary of results (ok/warnings/errors)

### Step 6.3: Test Validation Warning
- [ ] Create a trip with unrealistic efficiency:
  - [ ] Type: "Log manual trip"
  - [ ] Enter distance: "100 km"
  - [ ] Enter fuel: "3 L"
  - [ ] **Expected:**
    - Efficiency calculated: 3.0 L/100km
    - ⚠️ Warning: "Unrealistically low efficiency for Diesel (range 5-15)"
    - "Possible reasons: Odometer error, fuel calculation error"
    - "Continue anyway?"

- [ ] Type: "No, cancel"
- [ ] **Expected:** Trip NOT saved

### Step 6.4: Test Validation Pass
- [ ] Verify from Test 3 that normal trips passed validation without warnings

**✅ Test 6 Complete** - Validation working

---

## Integration Tests

### Integration Test 1: Complete End-to-End Workflow
**Duration:** 20 minutes

- [ ] Start fresh (optional: delete data directory and recreate)
- [ ] Test 1: Create vehicle (5 min)
- [ ] Test 2: Create first checkpoint (5 min)
- [ ] Test 4: Create template (5 min)
- [ ] Test 3: Create second checkpoint → gap → reconstruction (10 min)
- [ ] Test 5: Generate report (3 min)
- [ ] **Expected:** Complete workflow succeeds, all data files created

### Integration Test 2: Error Recovery
**Duration:** 15 minutes

- [ ] Test invalid VIN → Error shown, vehicle not created
- [ ] Test photo without GPS → Fallback to manual entry
- [ ] Test e-Kasa timeout → Retry or manual entry
- [ ] Test no template match → Create template or manual entry
- [ ] **Expected:** All errors handled gracefully, no crashes

### Integration Test 3: Cross-Skill Data Flow
**Duration:** 10 minutes

- [ ] Create template in Skill 4
- [ ] Use template in Skill 3 (reconstruction)
- [ ] Verify trip has template_id reference
- [ ] Generate report in Skill 5
- [ ] Verify trip data appears in CSV
- [ ] **Expected:** Data flows correctly between skills

---

## Performance Benchmarks

### Benchmark 1: Response Times
Record actual response times:

- [ ] Vehicle creation: _____ seconds (target < 5s)
- [ ] QR scan: _____ seconds (target < 5s)
- [ ] e-Kasa API: _____ seconds (target 5-30s)
- [ ] GPS extraction: _____ seconds (target < 3s)
- [ ] Template matching: _____ seconds (target < 5s)
- [ ] Validation: _____ seconds (target < 3s)
- [ ] Report generation: _____ seconds (target < 5s)

**Result:** All within acceptable range? YES / NO

### Benchmark 2: Accuracy
- [ ] Template matching confidence: _____ % (target ≥ 85%)
- [ ] GPS matching accuracy: _____ meters (target < 100m)
- [ ] Slovak compliance: All fields present? YES / NO

**Result:** Accuracy acceptable? YES / NO

---

## Screenshots to Capture

For documentation and demo:

- [ ] Screenshot 1: Vehicle creation success message
- [ ] Screenshot 2: Checkpoint created with GPS + receipt data
- [ ] Screenshot 3: Gap detection message
- [ ] Screenshot 4: Template matching results with confidence scores
- [ ] Screenshot 5: Validation results (all ✓)
- [ ] Screenshot 6: Report generation summary
- [ ] Screenshot 7: CSV file open in Excel/LibreOffice
- [ ] Screenshot 8: Template creation with geocoding alternatives

---

## Final Verification

### Data Integrity Check
- [ ] All JSON files valid (no parse errors)
- [ ] No `.tmp` files left over (atomic write completed)
- [ ] All mandatory fields present in trips
- [ ] All file permissions correct

### Slovak Compliance Check
- [ ] All VINs: 17 characters, no I/O/Q
- [ ] All efficiency: L/100km format (not km/L)
- [ ] All trips: Driver name present
- [ ] All trips: Trip timing separate from refuel timing

### Skill Functionality Check
- [ ] ✅ Skill 1: Vehicle setup working
- [ ] ✅ Skill 2: Checkpoint from receipt working
- [ ] ✅ Skill 3: Trip reconstruction working
- [ ] ✅ Skill 4: Template creation working
- [ ] ✅ Skill 5: Report generation working
- [ ] ✅ Skill 6: Data validation working (automatic)

### MCP Servers Check
- [ ] ✅ car-log-core: All 14 tools functional
- [ ] ✅ ekasa-api: QR scan + API fetch working
- [ ] ✅ geo-routing: Geocoding + routing working
- [ ] ✅ trip-reconstructor: Template matching working
- [ ] ✅ validation: All 4 algorithms working
- [ ] ✅ dashboard-ocr: EXIF extraction working
- [ ] ✅ report-generator: CSV generation working

---

## Issues Found During Testing

Document any issues encountered:

### Issue 1
- **Skill:** _____
- **Description:** _____
- **Expected:** _____
- **Actual:** _____
- **Severity:** Critical / High / Medium / Low
- **Status:** Fixed / Open / Won't Fix

### Issue 2
- **Skill:** _____
- **Description:** _____
- **Expected:** _____
- **Actual:** _____
- **Severity:** Critical / High / Medium / Low
- **Status:** Fixed / Open / Won't Fix

_(Add more as needed)_

---

## Testing Summary

**Test Date:** _____________________
**Tester Name:** _____________________
**Duration:** _____ hours

**Results:**
- Total tests: 6 skills + 3 integration tests
- Tests passed: _____ / 9
- Tests failed: _____ / 9
- Critical issues: _____
- High priority issues: _____

**Overall Status:** PASS / FAIL / PARTIAL

**Recommendation:**
- [ ] Ready for demo
- [ ] Needs minor fixes (list above)
- [ ] Needs major fixes (list above)
- [ ] Not ready for demo

**Next Steps:**
1. _____________________
2. _____________________
3. _____________________

---

**Last Updated:** November 20, 2025
**Status:** Ready for user testing
**Estimated Time:** 2-3 hours for complete manual testing
