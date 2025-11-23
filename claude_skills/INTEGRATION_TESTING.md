# Claude Skills Integration Testing Guide

**Project:** Car Log - Slovak Tax-Compliant Mileage Logger
**Component:** Claude Desktop Skills (Track F)
**Created:** November 20, 2025
**Status:** Ready for manual testing

---

## Overview

This guide provides comprehensive integration testing scenarios for the 6 Claude Desktop skills. All backend MCP servers are functional (100% complete), so testing focuses on **user experience validation** through Claude Desktop.

**Prerequisites:**
- ✅ All 7 MCP servers functional (backend complete)
- ✅ 28 tools implemented and tested (100% pass rate)
- ✅ Integration tests passed (20/20)
- ⏳ Claude Desktop configuration complete
- ⏳ Skills loaded into Claude Desktop

---

## Integration Test Scenarios

### Test Scenario 1: Complete Workflow (Happy Path)

**Goal:** Validate end-to-end workflow from vehicle setup to report generation.

**Duration:** ~10-15 minutes

**Test Steps:**

#### 1.1 Vehicle Setup (Skill 1)
```
User: "Add vehicle BA-456CD Ford Transit diesel"
Claude: "I'll help you register a new vehicle. I need a few details..."

Expected:
✅ VIN validation triggered
✅ License plate format validated (BA-456CD)
✅ Fuel type set to Diesel
✅ L/100km efficiency asked (not km/L)
✅ Vehicle created successfully

Validation:
- Check vehicle JSON file exists: data/vehicles/{vehicle_id}.json
- Verify VIN has no I/O/Q characters
- Verify license plate matches SK format: XX-123XX
```

#### 1.2 First Checkpoint (Skill 2)
```
User: [Paste receipt photo with QR code]
Claude: "Scanning QR code... Found e-Kasa receipt. Fetching data (may take 30s)..."

Expected:
✅ QR code detected (multi-scale if PDF)
✅ e-Kasa API called with 60s timeout
✅ Fuel detected from Slovak names (Nafta, Diesel, Natural 95)
✅ "Now paste dashboard photo for GPS coordinates"

User: [Paste dashboard photo with EXIF]
Claude: "GPS extracted: 48.1486°N, 17.1077°E. Creating checkpoint..."

Expected:
✅ EXIF GPS extracted
✅ Checkpoint created with receipt + GPS
✅ Odometer reading requested
✅ Checkpoint saved to data/checkpoints/2025-11/{checkpoint_id}.json
✅ "No gap detected yet (first checkpoint)"

Validation:
- Checkpoint file exists
- GPS coordinates present
- Receipt data embedded (fuel_liters, price, VAT)
```

#### 1.3 Second Checkpoint + Gap Detection (Skill 2 → Skill 3 chain)
```
User: [Paste second receipt, 7 days later]
Claude: [Same QR + EXIF extraction workflow]

Expected:
✅ Second checkpoint created
✅ Gap automatically detected: "820 km gap found between Nov 1 and Nov 8"
✅ Skill 3 triggered: "Would you like me to reconstruct trips for this gap?"

Validation:
- Gap detection works automatically
- Odometer delta calculated correctly (820 km)
- Time gap calculated (7 days)
```

#### 1.4 Trip Reconstruction (Skill 3)
```
User: "Yes, reconstruct trips"
Claude: "Analyzing gap... Matching templates using GPS-first algorithm..."

Expected:
✅ Templates fetched
✅ GPS matching scored (70% weight)
✅ Address matching scored (30% weight)
✅ Confidence scores displayed (>=70% threshold)
✅ Proposals presented:
    "Found 2 matching trips:
    • 2× Warehouse Run (Bratislava → Košice)
      - GPS match: 98% (within 50m)
      - Overall confidence: 92%
      - Distance: 410 km each
      - Coverage: 100% (820/820 km)

    Accept these proposals?"

User: "Yes"
Claude: "Creating trips... Running validation..."

Expected:
✅ 2 trips created via create_trips_batch
✅ Slovak compliance fields filled (driver_name, timing, locations)
✅ L/100km calculated (not km/L)
✅ Validation runs automatically (Skill 6)
✅ Trips saved to data/trips/2025-11/

Validation:
- 2 trip JSON files exist
- All Slovak mandatory fields present
- Fuel efficiency in L/100km format
- Confidence scores stored
```

#### 1.5 Data Validation (Skill 6 - Automatic)
```
Claude: "Running 4 validation algorithms..."

Expected:
✅ Distance sum check: ±10% (odometer 820 km vs trips 820 km)
✅ Fuel consumption check: ±15% (expected vs actual)
✅ Efficiency range check: 5-15 L/100km (Diesel)
✅ Deviation check: ±20% from vehicle average
✅ Results displayed:
    "Validation complete:
    ✓ Distance: 0% variance (perfect match)
    ✓ Fuel: +4.2% (within ±15%)
    ✓ Efficiency: 8.7 L/100km (Diesel 5-15 range)
    ✓ Deviation: +2.1% from average (within ±20%)"

Validation:
- All 4 algorithms run
- No blocking errors
- Warnings shown if thresholds exceeded
```

#### 1.6 Report Generation (Skill 5)
```
User: "Generate November business report"
Claude: "Filtering business trips for November 2025..."

Expected:
✅ Trips filtered by date range and purpose (Business)
✅ CSV generated with all Slovak VAT Act fields:
    - VIN (17 chars, no I/O/Q)
    - Driver name
    - Trip start/end datetime
    - Trip start/end location
    - Distance (km)
    - Fuel consumption (L)
    - Fuel efficiency (L/100km)
    - Purpose + business description
✅ Summary statistics shown:
    "Report generated: november-2025.csv
    • Total trips: 2
    • Total distance: 820 km
    • Total fuel: 72.8 L
    • Average efficiency: 8.9 L/100km
    • Total cost: €106.56

    Slovak VAT Act 2025 compliance: ✅ All fields present"

Validation:
- CSV file exists: data/reports/2025-11/november-2025.csv
- All mandatory fields present
- L/100km format used (not km/L)
- Business trips only (Personal trips excluded)
```

**Success Criteria:**
- ✅ All 6 skills triggered in sequence
- ✅ End-to-end workflow completes without errors
- ✅ Data files created correctly
- ✅ Slovak compliance verified throughout
- ✅ Total time < 15 minutes

---

### Test Scenario 2: Template Creation Workflow (Skill 4)

**Goal:** Validate template creation with GPS geocoding and ambiguity handling.

**Duration:** ~5 minutes

**Test Steps:**

#### 2.1 Create Template with Ambiguous Address
```
User: "Create template for weekly warehouse run"
Claude: "I'll help create a trip template. Where does this trip start?"

User: "Košice"
Claude: "Found 3 locations matching 'Košice':
    1. Košice, Slovakia (48.7164°N, 21.2611°E) - City
    2. Košice nad Hornádom, Slovakia (48.6231°N, 20.4197°E) - Municipality
    3. Košice-okolie, Slovakia (48.6500°N, 21.2167°E) - District

    Which location? (1-3)"

Expected:
✅ Geocoding called
✅ Multiple matches detected (confidence < 0.7)
✅ Alternatives presented with GPS coordinates
✅ User can select specific location

User: "1"
Claude: "GPS saved: 48.7164°N, 21.2611°E. Where does it end?"

User: "Bratislava, Hlavná 45"
Claude: "Found: Bratislava, Slovakia (48.1486°N, 17.1077°E). Calculating route..."

Expected:
✅ Single match (confidence > 0.9)
✅ No alternatives shown
✅ Route calculation triggered (OSRM)
✅ Distance calculated: ~410 km
✅ "This trip will have 90%+ matching confidence due to GPS coordinates.
    Add optional details? (day-of-week patterns, round trip, purpose)"

User: "It's every Monday and Thursday, round trip, business"
Claude: "Template created!"

Expected:
✅ Template saved with:
    - GPS coordinates (mandatory)
    - Addresses (optional labels)
    - Distance from route calculation
    - typical_days: ["Monday", "Thursday"]
    - is_round_trip: true
    - purpose: "business"
✅ Completeness score shown: "Template completeness: 85%"

Validation:
- Template JSON exists: data/templates/{template_id}.json
- GPS coordinates mandatory and present
- Addresses stored as labels
- Route distance matches OSRM response (~410 km)
```

#### 2.2 Create Template with GPS Only (No Address)
```
User: "Create template Home to Office"
Claude: "Where does it start?"

User: "48.1234°N, 17.5678°E"
Claude: "GPS coordinates entered directly. Where does it end?"

Expected:
✅ GPS coordinates parsed correctly
✅ No geocoding needed
✅ Template created with GPS only
✅ Address fields empty (optional)
✅ Completeness score lower: "Template completeness: 35%"

Validation:
- Template saved
- GPS present, addresses null
- Can still match templates (GPS is 70% weight)
```

**Success Criteria:**
- ✅ Ambiguity handling works
- ✅ GPS coordinates mandatory and validated
- ✅ Route calculation provides distance
- ✅ Optional fields enhance completeness

---

### Test Scenario 3: Error Handling & Recovery

**Goal:** Validate error handling for common failure scenarios.

**Duration:** ~10 minutes

#### 3.1 Invalid VIN (Skill 1)
```
User: "Add vehicle BA-123CD with VIN 1234567"
Claude: "VIN must be exactly 17 characters. Please provide a valid VIN."

Expected:
✅ Validation error caught
✅ Clear error message
✅ VIN not saved to database

Test Cases:
- ❌ VIN too short: "1234567"
- ❌ VIN with I/O/Q: "12345678901234IOQ"
- ✅ Valid VIN: "WBAXX01234ABC5678"
```

#### 3.2 Missing GPS in Photo (Skill 2)
```
User: [Paste dashboard photo without EXIF GPS]
Claude: "No GPS data found in photo (screenshot or EXIF stripped).
    Please either:
    1. Use phone camera app with location enabled
    2. Enter GPS coordinates manually
    3. Enter address (will geocode to GPS)"

Expected:
✅ EXIF extraction returns null
✅ Fallback options provided
✅ User can enter GPS manually
✅ Checkpoint created with manual GPS
```

#### 3.3 e-Kasa API Timeout (Skill 2)
```
User: [Paste receipt photo]
Claude: "Scanning QR code... Found receipt ID. Fetching from e-Kasa API (may take up to 60s)..."

[After 60 seconds]
Claude: "e-Kasa API timeout. Would you like to:
    1. Retry (API may be slow)
    2. Enter receipt data manually"

Expected:
✅ Progress indicator shown during wait
✅ Timeout after 60s (not infinite wait)
✅ Fallback to manual entry
✅ User can retry if transient failure
```

#### 3.4 No Templates Match (Skill 3)
```
User: "Reconstruct trips"
Claude: "No templates matched this gap with sufficient confidence (>=70%).
    Would you like to:
    1. Create new template for this route
    2. Manually log trip details
    3. Lower confidence threshold (60%)"

Expected:
✅ Empty proposal handled gracefully
✅ Suggestions for next steps
✅ Can create template from gap
```

#### 3.5 Validation Warnings (Skill 6)
```
Claude: "Running validation...
    ⚠️  Warning: Fuel consumption 23% higher than expected
        Expected: 35 L (based on 8.5 L/100km avg)
        Actual: 43 L (10.5 L/100km for this trip)

        Possible reasons:
        - Heavy load or trailer
        - Stop-and-go traffic
        - Cold weather operation

    This is a warning, not an error. Continue?"

Expected:
✅ Warning shown (not blocking error)
✅ Explanation provided
✅ User can confirm or edit data
✅ Trip saved if user approves
```

**Success Criteria:**
- ✅ All errors caught and handled
- ✅ User-friendly error messages
- ✅ Fallback options provided
- ✅ No crashes or silent failures

---

### Test Scenario 4: Cross-Skill Data Flow

**Goal:** Validate data flow between skills and MCP servers.

**Duration:** ~5 minutes

#### 4.1 Template → Reconstruction Flow
```
Skill 4 (Create template) → data/templates/{id}.json
                          ↓
Skill 3 (Reconstruction) → Reads template → Matches gap → Creates trips
                          ↓
                     data/trips/{id}.json
```

**Test:**
1. Create template in Skill 4
2. Create gap (2 checkpoints)
3. Run Skill 3 reconstruction
4. Verify template used in matching
5. Check trip has template_id reference

**Validation:**
- Template ID in trip JSON
- Reconstruction method: "template"
- Confidence score from template matching

#### 4.2 Trip → Report Flow
```
Skill 3 (Create trips) → data/trips/2025-11/{id}.json
                       ↓
Skill 5 (Report) → Queries trips → Generates CSV
                 ↓
            data/reports/2025-11/report.csv
```

**Test:**
1. Create 5 trips (3 Business, 2 Personal)
2. Generate November business report
3. Verify only 3 trips in CSV
4. Check summary stats match trip data

**Validation:**
- Business trips only in report
- Personal trips excluded
- Summary stats correct (distance, fuel, cost)

#### 4.3 Checkpoint → Gap → Reconstruction Chain
```
Skill 2 (Checkpoint) → Auto-detects gap → Triggers Skill 3
```

**Test:**
1. Create checkpoint at 45000 km
2. Create checkpoint at 45820 km (820 km gap)
3. Verify gap detected automatically
4. Check Skill 3 reconstruction triggered
5. Proposals presented without manual command

**Validation:**
- Gap detection automatic (no user prompt needed)
- Skill chaining works seamlessly
- User can approve/reject proposals

---

### Test Scenario 5: Performance Testing

**Goal:** Validate response times meet performance requirements.

**Duration:** ~10 minutes

#### 5.1 Template Matching Performance
```
Setup: Create 100 templates
Test: Match templates for 820 km gap
Expected: < 2 seconds

Validation:
- GPS matching uses Haversine (fast)
- Address matching uses Levenshtein (fast)
- No database queries (file-based)
- Response time acceptable for UX
```

#### 5.2 Report Generation Performance
```
Setup: Create 1000 trips over 12 months
Test: Generate November report (80-100 trips)
Expected: < 5 seconds

Validation:
- File reading with monthly index
- Filtering by date range and purpose
- CSV generation fast (no complex formatting)
```

#### 5.3 QR Scanning Performance
```
Test Cases:
1. Image QR (PNG): 1-2 seconds
2. PDF QR at 1x scale: 2-3 seconds
3. PDF QR at 3x scale: 4-5 seconds

Expected:
- Multi-scale detection stops at first success
- Total time < 5 seconds for 90% of receipts
```

**Success Criteria:**
- ✅ All operations < 5 seconds
- ✅ No timeout errors
- ✅ User experience smooth

---

## Testing Checklist

### Pre-Testing Setup
- [ ] All 7 MCP servers running (`Restart Claude Desktop and verify MCP servers loaded` or local processes)
- [ ] Claude Desktop configured with all servers
- [ ] Data directories exist: `~/.car-log-deployment/data/`
- [ ] Test data prepared (sample receipts, dashboard photos)
- [ ] Skills loaded into Claude Desktop (01-06)

### Test Execution
- [ ] Scenario 1: Complete workflow (happy path)
- [ ] Scenario 2: Template creation with geocoding
- [ ] Scenario 3: Error handling and recovery
- [ ] Scenario 4: Cross-skill data flow
- [ ] Scenario 5: Performance testing

### Post-Testing Validation
- [ ] All test JSON files created correctly
- [ ] No file corruption (atomic writes working)
- [ ] Slovak compliance verified in all outputs
- [ ] L/100km format used consistently (not km/L)
- [ ] Demo scenario works end-to-end

---

## Expected Response Times

| Operation | Target | Acceptable | Blocker |
|-----------|--------|------------|---------|
| Vehicle creation | 1-2s | < 5s | > 10s |
| QR scan | 2-3s | < 5s | > 10s |
| e-Kasa API | 5-15s | < 60s | > 60s |
| GPS extraction | 1-2s | < 3s | > 5s |
| Gap detection | 1s | < 2s | > 5s |
| Template matching | 2-3s | < 5s | > 10s |
| Trip creation | 1-2s | < 3s | > 5s |
| Validation | 1-2s | < 3s | > 5s |
| Report generation | 2-3s | < 5s | > 10s |

---

## Integration Test Matrix

| Test Case | Skill 1 | Skill 2 | Skill 3 | Skill 4 | Skill 5 | Skill 6 | Pass/Fail |
|-----------|---------|---------|---------|---------|---------|---------|-----------|
| Complete workflow | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⏳ Pending |
| Template creation | - | - | - | ✅ | - | - | ⏳ Pending |
| Error: Invalid VIN | ✅ | - | - | - | - | - | ⏳ Pending |
| Error: Missing GPS | - | ✅ | - | - | - | - | ⏳ Pending |
| Error: e-Kasa timeout | - | ✅ | - | - | - | - | ⏳ Pending |
| Error: No templates | - | - | ✅ | - | - | - | ⏳ Pending |
| Warning: High fuel | - | - | - | - | - | ✅ | ⏳ Pending |
| Data flow: Template→Trip | - | - | ✅ | ✅ | - | - | ⏳ Pending |
| Data flow: Trip→Report | - | - | ✅ | - | ✅ | - | ⏳ Pending |
| Performance: 100 templates | - | - | ✅ | - | - | - | ⏳ Pending |
| Performance: 1000 trips | - | - | - | - | ✅ | - | ⏳ Pending |

---

## Troubleshooting Common Issues

**See `TROUBLESHOOTING.md` for detailed solutions.**

Quick Reference:
- Skill not triggering → Check trigger words in skill file
- MCP tool fails → Restart MCP servers (`Re-run deployment and restart Claude Desktop`)
- GPS extraction fails → Use phone camera (not screenshot)
- e-Kasa timeout → Retry or manual entry
- Validation warnings → Review thresholds in `validation/thresholds.py`

---

## Next Steps After Integration Testing

1. **Document Results:** Update test matrix with Pass/Fail
2. **Fix Critical Issues:** Any blocking errors must be resolved
3. **Update TASKS.md:** Mark F1-F7 as complete
4. **Prepare Demo:** Use successful test scenario for demo video
5. **Final Polish:** Clean up code, update documentation

---

**Last Updated:** November 20, 2025
**Status:** Ready for manual testing in Claude Desktop
**Estimated Testing Time:** 2-3 hours for all scenarios
