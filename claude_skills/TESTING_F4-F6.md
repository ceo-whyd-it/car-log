# Claude Desktop Skills - Testing Guide (F4-F6)

**Purpose:** Comprehensive test cases for Template Creation, Report Generation, and Data Validation skills

---

## Table of Contents

1. [F4: Template Creation Tests](#f4-template-creation-tests)
2. [F5: Report Generation Tests](#f5-report-generation-tests)
3. [F6: Data Validation Tests](#f6-data-validation-tests)
4. [Slovak Compliance Verification](#slovak-compliance-verification)
5. [Edge Cases and Error Scenarios](#edge-cases-and-error-scenarios)
6. [Integration Test Scenarios](#integration-test-scenarios)

---

## F4: Template Creation Tests

### Test 1: Happy Path - Complete Template with GPS

**Input:**
```
User: "Create template called 'Daily Commute'"
Claude: "Where does it start?"
User: "Hlavná 45, Bratislava"
Claude: [Geocodes, finds GPS: 48.1486, 17.1077]
User: [Confirms location]
User: "Mlynská 12, Košice" (end location)
User: "No" (not round trip)
User: "Monday, Friday" (typical days)
User: "Business" (purpose)
User: "Client meetings in Košice office" (description)
```

**Expected MCP Calls:**
1. `geo-routing.geocode_address` → { address: "Hlavná 45, Bratislava", country_hint: "SK" }
2. `geo-routing.geocode_address` → { address: "Mlynská 12, Košice", country_hint: "SK" }
3. `geo-routing.calculate_route` → { start_coords: [48.1486, 17.1077], end_coords: [48.7164, 21.2611] }
4. `car-log-core.create_template` → { name: "Daily Commute", from_coords, to_coords, distance_km: 410, ... }
5. `trip-reconstructor.calculate_template_completeness` → { template_id }

**Expected Output:**
```
✅ Template created!

'Daily Commute'
• From: Hlavná 45, Bratislava (48.1486°N, 17.1077°E)
• To: Mlynská 12, Košice (48.7164°N, 21.2611°E)
• Distance: 410km (one-way)
• Days: Monday, Friday
• Purpose: Business - Client meetings in Košice office
• GPS coordinates saved ← I can match trips within 100m!
• Completeness: 95% (excellent)

I'll recognize this route with 90%+ confidence on future trips!
```

**Verification:**
- ✅ GPS coordinates mandatory (both from/to)
- ✅ Address stored as optional labels
- ✅ Route distance calculated
- ✅ Optional fields collected (days, purpose, description)
- ✅ Completeness score calculated
- ✅ User messaging clear and helpful

---

### Test 2: Ambiguous Address Resolution

**Input:**
```
User: "Create template for trips to Košice"
Claude: "Where does it start?"
User: "Bratislava"
```

**Expected Behavior:**
1. Geocode "Bratislava" → Returns 3+ alternatives
2. Show alternatives with context:
   ```
   ⚠️ Multiple locations found:

   1. Bratislava City Center (48.1486°N, 17.1077°E)
      - Capital city center
      - Confidence: 75%

   2. Bratislava-Petržalka (48.1234°N, 17.1100°E)
      - Residential district
      - Confidence: 60%

   3. Bratislava Airport (48.1702°N, 17.2127°E)
      - M. R. Štefánik Airport
      - Confidence: 55%

   Which location? (1/2/3) or provide more specific address:
   ```
3. Wait for user selection
4. Use selected GPS coordinates
5. Continue with end location

**MCP Calls:**
1. `geo-routing.geocode_address` → { alternatives: [3 options] }
2. [User selects option 1]
3. Continue with selected coordinates

**Verification:**
- ✅ Alternatives shown with context (type, confidence)
- ✅ User can select by number
- ✅ User can provide more specific address instead
- ✅ GPS coordinates from selected option used

---

### Test 3: GPS-Only Template (Fallback)

**Input:**
```
User: "Create template with GPS only"
Claude: "Where does it start?"
User: "GPS: 48.2000, 17.3000"
Claude: "Where does it end?"
User: "GPS: 48.8500, 21.4000"
```

**Expected Behavior:**
1. Parse GPS coordinates directly (no geocoding needed)
2. Optionally reverse-geocode for friendly labels
3. Calculate route using GPS
4. Create template with GPS, addresses optional
5. Confirm GPS-only template works

**Expected Output:**
```
✓ GPS coordinates received: 48.2000°N, 17.3000°E
Location: Near Svätý Jur, Slovakia

✓ GPS coordinates received: 48.8500°N, 21.4000°E
Location: Near Prešov, Slovakia

Note: GPS-only templates work perfectly! I'll match based on
coordinates (70% weight) without needing address matching.

[Continues with route and optional fields...]
```

**MCP Calls:**
1. `geo-routing.reverse_geocode` (optional, for labels)
2. `geo-routing.calculate_route` (using GPS directly)
3. `car-log-core.create_template` (GPS mandatory, addresses optional)

**Verification:**
- ✅ GPS coordinates accepted directly
- ✅ Addresses optional (reverse-geocoded for labels)
- ✅ User informed GPS-only works (70% matching weight)

---

### Test 4: Minimal Template (GPS Only, No Enhancements)

**Input:**
```
User: "Quick template: Bratislava to Košice, skip details"
[Geocodes to GPS]
User: "Skip" (route alternatives)
User: "Skip" (round trip)
User: "Skip" (typical days)
User: "Skip" (purpose)
```

**Expected Behavior:**
1. Create template with minimal data (name + GPS)
2. Calculate completeness score (~60%)
3. Recommend adding optional fields for better matching

**Expected Output:**
```
✅ Template created!

'Quick Template'
• From: 48.1486°N, 17.1077°E
• To: 48.7164°N, 21.2611°E
• Completeness: 60% (basic)

⚠️ Recommendation: Add optional fields for better matching:
• Typical days (improves matching by 15%)
• Purpose (helps filter business/personal)
• Round trip flag (doubles distance calculation)

Would you like to enhance this template now? (yes/no)
```

**Verification:**
- ✅ Minimal template accepted
- ✅ Low completeness score shown
- ✅ Recommendations provided
- ✅ Option to enhance offered

---

### Test 5: Route Alternatives

**Input:**
```
User: "Create template, show route options"
[After geocoding]
```

**Expected Behavior:**
1. Calculate 3 route alternatives
2. Show distance, time, tolls for each
3. Let user select typical route
4. Use selected route distance

**Expected Output:**
```
Calculating routes...

3 routes found:
1. D1 highway: 395km (4.2 hrs) €12 tolls ← Fastest
2. E50: 410km (4.5 hrs) €8 tolls ← Most common
3. Local roads: 385km (5.8 hrs) No tolls ← Cheapest

Which route do you typically take? (1/2/3)
```

**MCP Calls:**
1. `geo-routing.calculate_route` → { alternatives: true }

**Verification:**
- ✅ Multiple routes shown
- ✅ Distance, time, tolls displayed
- ✅ Recommendation provided (fastest/most common)
- ✅ User can select typical route

---

## F5: Report Generation Tests

### Test 6: Happy Path - Monthly Business Report

**Input:**
```
User: "Generate November report"
[System has 1 vehicle, 12 business trips in November]
User: "Business only" (filter)
User: "Both" (CSV + PDF)
```

**Expected MCP Calls:**
1. `car-log-core.list_vehicles` → [Ford Transit]
2. `car-log-core.list_trips` → { vehicle_id, start_date: "2025-11-01", end_date: "2025-11-30", purpose: "business" }
3. `validation.validate_compliance` → { trips, vehicle }
4. `report-generator.generate_csv` → { trips, vehicle, summary, output_path }
5. `report-generator.generate_pdf` → { trips, vehicle, summary, output_path }

**Expected Output:**
```
✅ Reports generated!

November 2025 Business Trips Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Totals:
• Distance: 1,850 km
• Fuel consumed: 164.5 L
• Avg efficiency: 8.9 L/100km
• Fuel cost: €330.00 (incl. VAT)
• VAT deductible: €55.00
• Trips: 12

🇸🇰 Slovak VAT Act 2025 Compliance:
✅ VIN included (WVWZZZ3CZDP123456)
✅ Driver names present (all trips)
✅ Trip timing separated from refuel
✅ L/100km format (European standard)
✅ Business descriptions complete
✅ All mandatory fields: 100%

📄 Files saved to:
• ~/Documents/MileageLog/reports/BA-789XY-nov-2025.csv
• ~/Documents/MileageLog/reports/BA-789XY-nov-2025.pdf

Report is ready for tax deduction submission!
```

**Verification:**
- ✅ All Slovak VAT Act 2025 fields present
- ✅ L/100km format (not km/L)
- ✅ Summary statistics accurate
- ✅ Compliance checklist displayed
- ✅ File paths provided
- ✅ CSV and PDF both generated

---

### Test 7: Custom Date Range, Multiple Vehicles

**Input:**
```
User: "Generate report for BMW from Nov 15 to Nov 30"
[System has 2 vehicles]
```

**Expected Behavior:**
1. Recognize "BMW" → select BMW vehicle
2. Parse date range: Nov 15-30, 2025
3. Fetch trips in range
4. Ask about filter (business/personal/all)
5. Generate report

**Expected Output:**
```
Generating custom date range report...

Found 2 vehicles:
1. Ford Transit (BA-789XY)
2. BMW 5 Series (BA-123CD)

Confirmed: BMW 5 Series (BA-123CD)
Date range: Nov 15-30, 2025

Filter by purpose?
1. Business only
2. Personal only
3. All trips
```

**MCP Calls:**
1. `car-log-core.list_vehicles`
2. `car-log-core.list_trips` → { vehicle_id: BMW, start_date: "2025-11-15", end_date: "2025-11-30" }

**Verification:**
- ✅ Vehicle identified from natural language
- ✅ Date range parsed correctly
- ✅ Custom filters applied

---

### Test 8: Compliance Issues Found

**Input:**
```
User: "Generate October report"
[System has 10 trips, 3 with missing mandatory fields]
```

**Expected Behavior:**
1. Fetch trips
2. Validate compliance
3. Find 3 issues (missing driver, missing description, wrong format)
4. Show errors with details
5. Offer to fix issues
6. Guide through corrections
7. Regenerate report

**Expected Output:**
```
⚠️ Compliance Issues Found:

October 2025 Report - 10 trips
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issues:
1. Trip #3 (Oct 8) - Missing driver name [MANDATORY]
2. Trip #5 (Oct 12) - Missing business description [MANDATORY]
3. Trip #7 (Oct 19) - Fuel efficiency in km/L format (must be L/100km)

Slovak VAT Act 2025 requires these fields for tax deduction.

Options:
1. Fix issues now (edit trips)
2. Generate report anyway (with warnings)
3. Cancel report generation

Recommendation: Fix issues first to ensure tax compliance.
```

**MCP Calls:**
1. `car-log-core.list_trips`
2. `validation.validate_compliance` → { errors: [3 issues] }
3. `car-log-core.update_trip` (for each fix)
4. Re-validate
5. Generate report

**Verification:**
- ✅ Missing fields detected
- ✅ Clear error messages
- ✅ Offer to fix vs. continue
- ✅ Guide through corrections
- ✅ Re-validate after fixes

---

### Test 9: No Trips Found

**Input:**
```
User: "Generate December report"
[December 2025 is future/empty]
```

**Expected Behavior:**
1. Query trips for December
2. Find zero trips
3. Show friendly message
4. Suggest alternatives

**Expected Output:**
```
No trips found for December 2025.

Suggestions:
• Check if trips were logged for this period
• Try a different date range
• Verify vehicle selection

Would you like to try a different period?
```

**Verification:**
- ✅ Empty result handled gracefully
- ✅ Helpful suggestions provided
- ✅ No error/crash

---

### Test 10: Large Report (100+ Trips)

**Input:**
```
User: "Generate full year 2025 report"
[System has 120 trips across 12 months]
```

**Expected Behavior:**
1. Fetch all trips (may be slow)
2. Show progress if >50 trips
3. Generate CSV efficiently
4. Generate PDF (multi-page)
5. Show annual summary

**Expected Output:**
```
Fetching trips... (120 trips found)
Calculating summary...
Generating CSV... ✓ (2.1 seconds)
Generating PDF... ✓ (6.8 seconds)

✅ 2025 Annual Report Complete

📊 Annual Summary:
• Total Distance: 24,600 km
• Total Fuel: 2,091 L
• Avg Efficiency: 8.5 L/100km
• Total Cost: €4,280 (incl. VAT)
• VAT Deductible: €713
• Trips: 120

Files saved to:
• ~/Documents/MileageLog/reports/BA-789XY-2025-annual.csv
• ~/Documents/MileageLog/reports/BA-789XY-2025-annual.pdf (18 pages)
```

**Performance Requirements:**
- CSV generation: <3 seconds for 120 trips
- PDF generation: <10 seconds for 120 trips
- Total: <15 seconds

**Verification:**
- ✅ Large dataset handled efficiently
- ✅ Progress indicator shown
- ✅ Multi-page PDF generated
- ✅ Annual totals accurate

---

## F6: Data Validation Tests

### Test 11: Happy Path - All Checks Pass

**Input:**
```
[User creates trip]
- Odometer: 50,000 → 50,820 (820km)
- Trip distance: 410 + 410 = 820km
- Fuel: 34.85 + 36.90 = 71.75L
- Vehicle avg: 8.5 L/100km
- Trip efficiency: 8.75 L/100km
```

**Expected MCP Calls:**
1. `validation.validate_checkpoint_pair` → { valid: true, variance: 0.0 }
2. `validation.validate_trip` → { valid: true, variance: 2.9 }
3. `validation.check_efficiency` → { valid: true, efficiency: 8.75 }
4. `validation.check_deviation_from_average` → { valid: true, deviation: 2.9 }

**Expected Output:**
```
✅ All validation checks passed!

1️⃣ Distance Sum: 820km ✓
   Odometer delta: 820km
   Trips total: 820km (0% variance, within ±10%)

2️⃣ Fuel Consumption: 71.75L ✓
   Expected: 69.7L (8.5 L/100km average)
   Variance: +2.9% (within ±15%)

3️⃣ Efficiency: 8.75 L/100km ✓
   Range: 5-15 L/100km (Diesel)
   Status: Normal for commercial vans

4️⃣ Deviation: +2.9% ✓
   Vehicle average: 8.5 L/100km
   Trip: 8.75 L/100km (under 20% threshold)

Trip saved successfully!
```

**Verification:**
- ✅ All 4 algorithms run
- ✅ All pass with green checkmarks
- ✅ Detailed breakdown shown
- ✅ Visual indicators (✅ ✓ 1️⃣)

---

### Test 12: Warning - Deviation 21%

**Input:**
```
- Trip efficiency: 10.3 L/100km
- Vehicle avg: 8.5 L/100km
- Deviation: +21.2%
```

**Expected MCP Calls:**
1. `validation.check_deviation_from_average` → { valid: false, deviation: 21.2, threshold: 20 }

**Expected Output:**
```
⚠️ Validation Warning:

4️⃣ Deviation from Average: +21.2%
   Vehicle avg: 8.5 L/100km
   This trip: 10.3 L/100km

This is 21% above your average, which is unusual.

Common causes:
• Heavy load or trailer (adds 20-40% fuel use)
• City driving vs. highway (30-50% more fuel)
• Cold weather (10-25% increase)
• Data entry error

Was there something different about this trip?
(heavy load / city driving / correct as-is / fix data)
```

**Verification:**
- ✅ Warning shown (not error)
- ✅ User can override
- ✅ Contextual suggestions provided
- ✅ Multiple options offered

---

### Test 13: Error - Distance Mismatch 12%

**Input:**
```
- Odometer delta: 820km
- Trips total: 650km
- Variance: -20.7%
```

**Expected MCP Calls:**
1. `validation.validate_checkpoint_pair` → { valid: false, variance: -20.7, threshold: 10 }

**Expected Output:**
```
❌ Validation Error:

1️⃣ Distance Sum Mismatch: -20.7%
   Odometer: 50,000 → 50,820 (820km)
   Trips recorded: 650km
   Missing: 170km

You're missing 170km worth of trips between Nov 1 and Nov 5.

This gap is too large for Slovak tax compliance (max ±10%).

Options:
1. Add missing trips - Were there trips you forgot to log?
2. Check odometer - Could the reading be wrong?
3. Adjust trips - Should existing trips be longer?

What would you like to do?
```

**Verification:**
- ✅ Error shown (blocking)
- ✅ Clear explanation (missing 170km)
- ✅ Options provided
- ✅ Cannot proceed until fixed

---

### Test 14: Error - Efficiency Out of Range

**Input:**
```
- Efficiency: 22.5 L/100km
- Fuel type: Diesel
- Range: 5-15 L/100km
```

**Expected MCP Calls:**
1. `validation.check_efficiency` → { valid: false, efficiency: 22.5, range: [5, 15] }

**Expected Output:**
```
❌ Validation Error:

3️⃣ Efficiency Out of Range: 22.5 L/100km
   Expected range: 5-15 L/100km (Diesel)

This is outside the reasonable range for diesel vehicles.

Possible issues:
• Incorrect fuel quantity entered
• Incorrect distance entered
• Wrong fuel type selected

Please review and correct the data.
```

**Verification:**
- ✅ Out of range detected
- ✅ Range context shown
- ✅ Likely causes suggested
- ✅ Blocking error (must fix)

---

### Test 15: Multiple Warnings (Allow with Confirmation)

**Input:**
```
- Fuel consumption: +18% (warning)
- Deviation: +25% (warning)
```

**Expected Behavior:**
1. Show both warnings
2. Provide context for each
3. Ask for single confirmation
4. Allow save if confirmed
5. Log override

**Expected Output:**
```
⚠️ Validation Warnings (2):

2️⃣ Fuel Consumption: +18%
   Expected: 69.7L, Actual: 82.2L
   Variance: +18% (exceeds ±15% threshold)

4️⃣ Deviation from Average: +25%
   Vehicle avg: 8.5 L/100km
   This trip: 10.6 L/100km

Both warnings suggest this trip had unusual conditions
(heavy load, city driving, weather, etc.)

Continue anyway? (yes/no)
```

**Verification:**
- ✅ Multiple warnings shown together
- ✅ Single confirmation asked
- ✅ User can override both
- ✅ Override logged for audit

---

## Slovak Compliance Verification

### Compliance Test 1: VIN Validation

**Valid VINs:**
```
✅ WVWZZZ3CZDP123456 (17 chars, valid format)
✅ 1HGBH41JXMN109186 (17 chars)
✅ JH4KA7561PC000000 (17 chars)
```

**Invalid VINs:**
```
❌ WVWZZZ3CZDP12345 (16 chars, too short)
❌ WVWZZZ3CZDP1234567 (18 chars, too long)
❌ WVWZZZ3CZDPI23456 (contains 'I', invalid)
❌ WVWZZZ3CZDPO23456 (contains 'O', invalid)
❌ WVWZZZ3CZDPQ23456 (contains 'Q', invalid)
```

**Error Message:**
```
❌ Invalid VIN: WVWZZZ3CZDPI23456

VIN must be:
• Exactly 17 characters
• No I, O, or Q characters (easily confused with 1/0)
• Uppercase letters and digits only

Slovak VAT Act 2025 requires valid VIN for tax deduction.
```

---

### Compliance Test 2: Driver Name Mandatory

**Valid:**
```
✅ "John Doe"
✅ "Ján Novák"
✅ "Maria Schmidt-Weiss"
```

**Invalid:**
```
❌ "" (empty)
❌ null
❌ "Unknown"
❌ "-"
```

**Error Message:**
```
❌ Missing driver name

Slovak VAT Act 2025 requires driver name for all trips.

Who was driving this trip?
```

---

### Compliance Test 3: L/100km Format

**Valid:**
```
✅ 8.5 L/100km
✅ 12.3 L/100km
✅ 5.0 L/100km
```

**Invalid (Auto-convert with warning):**
```
⚠️ 11.8 km/L → Converted to 8.5 L/100km
⚠️ 9.5 km/L → Converted to 10.5 L/100km

Slovak VAT Act 2025 requires L/100km format (European standard).
I've converted your entry automatically.
```

---

### Compliance Test 4: Business Description Mandatory

**Valid (if purpose = Business):**
```
✅ "Client meeting in Košice"
✅ "Warehouse pickup"
✅ "Delivery to customer"
```

**Invalid (if purpose = Business):**
```
❌ "" (empty)
❌ null
❌ "Business trip" (too vague)
```

**Error Message:**
```
❌ Missing business description

For business trips, Slovak VAT Act 2025 requires a
specific description of the business purpose.

Examples:
• "Client meeting in Košice"
• "Warehouse pickup"
• "Delivery to customer XYZ"

What was the business purpose of this trip?
```

---

## Edge Cases and Error Scenarios

### Edge Case 1: Geocoding Returns No Results

**Input:**
```
User: "xyzabc123notarealplace"
```

**Expected Behavior:**
```
⚠️ Location not found: "xyzabc123notarealplace"

I couldn't find this location. Options:
1. Provide more specific address
2. Enter GPS coordinates manually (lat, lng)
3. Skip geocoding (add address later)

What would you like to do?
```

---

### Edge Case 2: e-Kasa API Timeout

**Input:**
```
User: "/o12345..."
[e-Kasa API takes >60 seconds]
```

**Expected Behavior:**
```
⚠️ e-Kasa API timeout (60 seconds exceeded)

Slovak e-Kasa servers are busy right now.

Options:
1. Retry (may take another 60s)
2. Enter receipt data manually
3. Save receipt ID for later lookup

Recommendation: Enter manually now, I'll fetch details
later when servers are less busy.

Do you have the fuel quantity and price?
```

---

### Edge Case 3: Route Calculation Fails

**Input:**
```
[GPS coordinates in different countries, no route]
```

**Expected Behavior:**
```
⚠️ Route calculation failed

I couldn't calculate a route between these locations
(possibly different countries or isolated areas).

Options:
1. Enter distance manually
2. Skip route calculation (use straight-line distance)
3. Check GPS coordinates

What would you like to do?
```

---

### Edge Case 4: Negative Distance (Odometer Rollback)

**Input:**
```
- Checkpoint 1: 99,950 km
- Checkpoint 2: 100 km (odometer rollback)
```

**Expected Behavior:**
```
⚠️ Odometer rollback detected

Previous: 99,950 km
Current: 100 km
Delta: -99,850 km (negative)

This suggests:
1. Odometer rollback/reset (rare, 999,999 → 0)
2. Data entry error (typo)
3. Different vehicle (wrong selection)

Please review these readings. Is this correct?
```

---

### Edge Case 5: Future Date

**Input:**
```
User: "Create checkpoint for tomorrow"
```

**Expected Behavior:**
```
⚠️ Future date detected: 2025-11-21

You're trying to create a checkpoint for tomorrow.
This is unusual - checkpoints are typically logged
as they happen.

Options:
1. Use today's date (2025-11-20)
2. Continue with future date
3. Specify different date

What would you like to do?
```

---

## Integration Test Scenarios

### Integration Test 1: End-to-End Monthly Workflow

**Scenario:**
```
1. User scans 4 receipts (F1) throughout November
2. System auto-detects 3 gaps (F2)
3. User reconstructs 6 trips from templates (F3)
4. User creates 1 new template (F4)
5. User generates November report (F5)
6. System validates all data (F6) - all pass
```

**Success Criteria:**
- ✅ All 4 receipts processed
- ✅ All 3 gaps detected
- ✅ All 6 trips reconstructed
- ✅ Template created successfully
- ✅ Report generated (CSV + PDF)
- ✅ 100% Slovak compliance
- ✅ Total time: <10 minutes

---

### Integration Test 2: Error Recovery Flow

**Scenario:**
```
1. User creates trips with missing driver names
2. Validation fails (F6)
3. User attempts report generation (F5)
4. System blocks report, shows errors
5. User fixes all issues
6. Re-validation passes
7. Report generated successfully
```

**Success Criteria:**
- ✅ Errors detected before report
- ✅ Clear error messages shown
- ✅ User guided through fixes
- ✅ Re-validation automatic
- ✅ Report generation unblocked

---

### Integration Test 3: Template → Reconstruction → Validation

**Scenario:**
```
1. User creates template "Warehouse Run" (F4)
2. User scans 2 receipts with 820km gap (F1)
3. Gap detection triggers (F2)
4. Trip reconstruction matches template 95% (F3)
5. User approves, trips created
6. Validation auto-runs (F6) - all pass
```

**Success Criteria:**
- ✅ Template completeness >90%
- ✅ Gap detected automatically
- ✅ High-confidence match (>90%)
- ✅ Trips created with template metadata
- ✅ Validation passes all checks

---

## Test Execution Checklist

### Before Testing
- [ ] Claude Desktop configured with all 7 MCP servers
- [ ] Test data directory created: ~/Documents/MileageLog/data/
- [ ] Sample vehicle created (VIN, license plate)
- [ ] Sample checkpoints created (at least 2)
- [ ] Sample templates created (at least 2)

### During Testing
- [ ] Record all MCP calls made
- [ ] Verify response times (<5s for most operations)
- [ ] Check error messages are clear and actionable
- [ ] Confirm Slovak compliance enforced
- [ ] Validate all file paths are correct

### After Testing
- [ ] Clean up test data
- [ ] Document any issues found
- [ ] Verify all success criteria met
- [ ] Create bug reports for failures
- [ ] Update test cases as needed

---

## Summary

**Total Test Cases:** 15 core tests + 5 edge cases + 3 integration tests = 23 tests

**Coverage:**
- F4 (Template Creation): 5 tests
- F5 (Report Generation): 5 tests
- F6 (Data Validation): 5 tests
- Slovak Compliance: 4 tests
- Edge Cases: 5 tests
- Integration: 3 tests

**Success Metrics:**
- ✅ All 23 tests pass
- ✅ 100% Slovak VAT Act 2025 compliance
- ✅ Error messages clear and actionable
- ✅ Average operation time <5 seconds
- ✅ User experience smooth and intuitive

---

**Last Updated:** 2025-11-20
**Version:** 1.0
