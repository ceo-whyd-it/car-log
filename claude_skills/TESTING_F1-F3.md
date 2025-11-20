# Comprehensive Testing Guide for Claude Desktop Skills F1-F3

This guide provides detailed test scenarios for all three core workflow skills.

## Test Environment Setup

### Prerequisites

1. Claude Desktop with MCP servers configured (see INSTALLATION.md)
2. Test data directory with sample files:
   ```bash
   mkdir -p ~/Documents/MileageLog/test-data/{receipts,dashboards,expected-results}
   ```
3. Sample images:
   - `test-receipt-qr.jpg` - Receipt with visible QR code
   - `test-receipt-no-qr.jpg` - Receipt without QR code
   - `test-dashboard-gps.jpg` - Dashboard photo with EXIF GPS
   - `test-dashboard-no-gps.png` - Screenshot without EXIF
4. Clean data directory for testing:
   ```bash
   rm -rf ~/Documents/MileageLog/data/*
   mkdir -p ~/Documents/MileageLog/data/{vehicles,checkpoints,trips,templates}
   ```

### Test Data Preparation

Create sample data files for testing:

**Sample Vehicle:**
```json
{
  "vehicle_id": "test-vehicle-001",
  "name": "Ford Transit Test Van",
  "license_plate": "BA-789XY",
  "vin": "WVWZZZ3CZDP123456",
  "fuel_type": "Diesel",
  "initial_odometer_km": 45000,
  "current_odometer_km": 45000
}
```

**Sample Template:**
```json
{
  "template_id": "test-template-001",
  "name": "Test Warehouse Run",
  "from_coords": {"latitude": 48.1486, "longitude": 17.1077},
  "from_address": "Bratislava",
  "to_coords": {"latitude": 48.7164, "longitude": 21.2611},
  "to_address": "Košice",
  "distance_km": 410,
  "is_round_trip": true,
  "typical_days": ["Monday", "Thursday"]
}
```

---

## SKILL 1: Vehicle Setup - Test Scenarios

### Test Suite F1.1: Standard Registration (Happy Path)

**Objective:** Verify complete vehicle registration with all fields

**Input:**
```
"Add my Ford Transit BA-789XY diesel 125000km VIN WVWZZZ3CZDP123456"
```

**Expected Behavior:**
1. Parse all fields from one message
2. Validate VIN: 17 chars ✓, no I/O/Q ✓
3. Validate license plate: BA-789XY ✓
4. Show summary for confirmation
5. Call `car-log-core.create_vehicle`
6. Display success message with vehicle ID
7. Prompt for next steps ("Ready to add your first checkpoint?")

**Expected MCP Calls:**
```json
[
  {
    "tool": "car-log-core.list_vehicles",
    "purpose": "Check for duplicates"
  },
  {
    "tool": "car-log-core.create_vehicle",
    "parameters": {
      "name": "Ford Transit",
      "license_plate": "BA-789XY",
      "vin": "WVWZZZ3CZDP123456",
      "fuel_type": "Diesel",
      "initial_odometer_km": 125000
    }
  }
]
```

**Success Criteria:**
- ✅ All fields extracted correctly
- ✅ VIN validation passes
- ✅ License plate formatted with hyphen
- ✅ Vehicle created in data/vehicles/
- ✅ User sees clear next steps
- ✅ Fuel efficiency expectation shown (5-15 L/100km for Diesel)

**Test Duration:** 1-2 minutes

---

### Test Suite F1.2: Guided Registration (Conversational)

**Objective:** Test step-by-step conversational flow

**Input:**
```
User: "I need to add my company car"
```

**Expected Conversation Flow:**
```
Claude: "I'll help! What kind of vehicle?"
User: "BMW 5 series"
Claude: "Great! What's the license plate (format: BA-456CD)?"
User: "BA456CD"
Claude: "License plate should be BA-456CD (with hyphen). Is this correct?"
User: "Yes"
Claude: "✓ BA-456CD. What's the VIN (17 characters)?"
User: "WVWZZZ3CZDP123456"
Claude: "✓ VIN validated. What fuel type?"
User: "Gasoline"
Claude: "✓ Gasoline. Current odometer reading (km)?"
User: "85000"
Claude: "✓ 85,000 km. Summary: [shows all fields]. Create this vehicle?"
User: "Yes"
Claude: "✅ Vehicle registered successfully! [shows details and next steps]"
```

**Success Criteria:**
- ✅ Step-by-step guidance clear
- ✅ Format auto-correction works (BA456CD → BA-456CD)
- ✅ User can review before creation
- ✅ Each field validated immediately
- ✅ Helpful format hints shown

**Test Duration:** 3-5 minutes

---

### Test Suite F1.3: Invalid VIN (Contains I/O/Q)

**Objective:** Test VIN validation and error messaging

**Test Cases:**

**Case A: VIN with O (letter O instead of 0)**
```
Input: "VIN: WVOZZZ3CZDP123456"
Expected Error: "VIN contains invalid character 'O'. Slovak VINs cannot contain I, O, or Q. It might be number 0 (zero) instead of letter O. Please double-check:"
```

**Case B: VIN with I (letter I instead of 1)**
```
Input: "VIN: WVIZZZ3CZDP123456"
Expected Error: "VIN contains invalid character 'I'. It might be number 1 instead of letter I."
```

**Case C: VIN too short**
```
Input: "VIN: WVWZZZ3CZ"
Expected Error: "VIN must be exactly 17 characters. Slovak tax law requires a complete VIN for VAT deduction. Please provide the full 17-character VIN:"
```

**Success Criteria:**
- ✅ VIN rejected immediately
- ✅ Clear error message
- ✅ Helpful suggestion (0 vs O, 1 vs I)
- ✅ Re-prompt for correct VIN
- ✅ Explain Slovak compliance requirement

**Test Duration:** 2-3 minutes per case

---

### Test Suite F1.4: License Plate Format Variations

**Objective:** Test license plate auto-correction

**Test Cases:**

| Input | Expected Output | Auto-Correct |
|-------|----------------|--------------|
| BA789XY | BA-789XY | Yes |
| BA 789 XY | BA-789XY | Yes |
| ba-789xy | BA-789XY | Yes (uppercase) |
| B-789XY | B-789XY | Yes (1 letter valid) |
| BA-789X | ERROR | No (invalid format) |
| 123-456AB | ERROR | No (starts with digits) |

**Expected Behavior:**
- Auto-correct valid variations
- Show corrected format and ask confirmation
- Reject invalid formats with clear error

**Success Criteria:**
- ✅ All valid variations auto-corrected
- ✅ User confirmation requested
- ✅ Invalid formats rejected with helpful message
- ✅ Slovak format explained (XX-123XX)

**Test Duration:** 5 minutes

---

### Test Suite F1.5: Duplicate License Plate Detection

**Objective:** Test duplicate prevention

**Setup:**
1. Create vehicle with BA-789XY
2. Attempt to create another with BA-789XY

**Expected Behavior:**
```
Claude: "⚠️ Vehicle with license plate BA-789XY already exists:

Ford Transit Delivery Van
• VIN: WVWZZZ3CZDP123456
• Current odometer: 125,000 km
• Fuel: Diesel

Did you mean to:
1. Add a different vehicle (different plate)
2. View existing vehicle details
3. Update odometer reading

What would you like to do?"
```

**Success Criteria:**
- ✅ Duplicate detected via list_vehicles call
- ✅ Existing vehicle details shown
- ✅ Clear options provided
- ✅ No duplicate vehicle created
- ✅ User can choose next action

**Test Duration:** 2 minutes

---

### Test Suite F1.6: Unrealistic Odometer Validation

**Objective:** Test odometer reasonableness checks

**Test Cases:**

| Input | Expected Behavior |
|-------|-------------------|
| 5000000 km | ⚠️ "Seems high (5M km = 125× around Earth!)" |
| -1000 km | ⚠️ "Odometer cannot be negative" |
| 0 km | ✅ Accept (new vehicle) |
| 300000 km | ✅ Accept (high but reasonable) |

**Success Criteria:**
- ✅ Validation triggers on >1,000,000 km
- ✅ Negative values rejected
- ✅ Helpful context provided
- ✅ User can confirm unusual values
- ✅ Zero accepted for new vehicles

**Test Duration:** 3 minutes

---

### Test Suite F1.7: Fuel Efficiency Expectations

**Objective:** Test L/100km format and ranges

**Test Cases:**

| Fuel Type | Expected Range | Example Message |
|-----------|----------------|-----------------|
| Diesel | 5-15 L/100km | "Expected: 8.5 L/100km for commercial vans" |
| Gasoline | 6-20 L/100km | "Expected: 10.5 L/100km for sedans" |
| LPG | 7-18 L/100km | "Expected: 12 L/100km" |
| Hybrid | 3-8 L/100km | "Expected: 5.5 L/100km combined" |
| Electric | N/A | "Electric: kWh/100km (not L/100km)" |

**Success Criteria:**
- ✅ L/100km format used (NEVER km/L)
- ✅ Reasonable range provided for fuel type
- ✅ Context for vehicle type (van vs sedan)
- ✅ Electric vehicles handled differently
- ✅ User sees expectations immediately

**Test Duration:** 2 minutes

---

### Test Suite F1.8: Multi-Vehicle User

**Objective:** Test adding second/third vehicle

**Setup:**
1. Create first vehicle (BA-789XY)
2. Add second vehicle (KE-456AB)

**Expected Behavior:**
```
Claude: "You have 1 vehicle registered:
• Ford Transit (BA-789XY) - 125,000 km

What's the new vehicle?"
```

**Success Criteria:**
- ✅ Existing vehicles displayed
- ✅ Clear distinction from new vehicle
- ✅ Each vehicle has unique license plate
- ✅ Each vehicle has unique VIN
- ✅ User can manage multiple vehicles

**Test Duration:** 3 minutes

---

## SKILL 2: Checkpoint from Receipt Photo - Test Scenarios

### Test Suite F2.1: Happy Path (Both Photos Complete)

**Objective:** Test full automatic workflow with good data

**Setup:**
- Receipt photo with QR code (test-receipt-qr.jpg)
- Dashboard photo with GPS + odometer (test-dashboard-gps.jpg)
- Vehicle already created

**Input:**
```
User: [pastes receipt photo]
```

**Expected Flow:**
```
Claude: "📸 Receipt photo detected. Scanning QR code...
⏳ Trying scale 1x... ✓ QR code found!

Receipt ID: o2a9s3d8f7g6h5j4

Fetching receipt from e-Kasa API (may take 30s)...
[15 seconds]
✓ Receipt loaded!
• Vendor: OMV Station Bratislava
• Date: 2025-11-18 14:23
• Fuel: 52.3L Diesel @ €1.45/L
• Total: €75.84 (€63.20 excl VAT)

Is this correct?"

User: "Yes"

Claude: "Great! Now I need your dashboard photo to get GPS coordinates and odometer reading. Paste dashboard photo:"

User: [pastes dashboard photo]

Claude: "📸 Dashboard photo received. Analyzing...
✓ GPS: 48.1486°N, 17.1077°E (Bratislava)
✓ Timestamp: 2025-11-18 14:25 (2 min after receipt ✓)
✓ Odometer: 45,820 km (confidence: 95%)

Creating checkpoint...

✅ Checkpoint created!

Refuel Stop - OMV Bratislava
• Time: 2025-11-18 14:25
• Location: 48.1486°N, 17.1077°E
• Odometer: 45,820 km
• Fuel: 52.3L Diesel (€75.84)

Checking for gaps...

⚠️ Gap detected: 820 km since last checkpoint (7 days ago)

Would you like me to reconstruct trips for this gap?"
```

**Expected MCP Calls:**
```json
[
  {"tool": "ekasa-api.scan_qr_code", "result": "o2a9s3d8f7g6h5j4"},
  {"tool": "ekasa-api.fetch_receipt_data", "timeout": 60},
  {"tool": "dashboard-ocr.extract_metadata"},
  {"tool": "car-log-core.create_checkpoint"},
  {"tool": "car-log-core.detect_gap"}
]
```

**Success Criteria:**
- ✅ Entire workflow < 30 seconds
- ✅ All data extracted automatically
- ✅ Progress indicators shown
- ✅ Timestamps validated (within 10 min)
- ✅ Gap detection triggers
- ✅ User prompted for reconstruction

**Test Duration:** 2 minutes

---

### Test Suite F2.2: Low-Quality Receipt PDF (Multi-Scale)

**Objective:** Test multi-scale QR detection

**Setup:**
- PDF receipt with small QR code (test-receipt-small-qr.pdf)

**Expected Flow:**
```
Claude: "📸 Receipt detected. Scanning QR code...
⏳ Trying scale 1x... not found
⏳ Trying scale 2x... not found
⏳ Trying scale 3x... ✓ QR code found!

Receipt ID: o2a9s3d8f7g6h5j4
[continues normal flow]"
```

**Success Criteria:**
- ✅ All 3 scales attempted
- ✅ User sees progress for each scale
- ✅ QR found at 3x scale
- ✅ Detection scale logged in metadata
- ✅ Workflow continues normally

**Test Duration:** 1 minute

---

### Test Suite F2.3: e-Kasa API Timeout

**Objective:** Test timeout handling and fallback

**Setup:**
- Valid QR code, but simulate slow e-Kasa API

**Expected Flow (if timeout):**
```
Claude: "Fetching receipt from e-Kasa API...
⏳ Please wait, this may take up to 60 seconds.

Slovak tax system can be slow during peak hours.

[15 seconds]
⏳ Still waiting... (30s max)

[30 seconds]
⏳ Still processing... (30s elapsed)

[60 seconds]
❌ Timeout after 60 seconds.

The e-Kasa system is not responding. Let's enter details manually:

1. Fuel quantity (liters): _____
2. Price per liter (€): _____
3. Total amount (€): _____
4. Vendor name: _____"
```

**Success Criteria:**
- ✅ Progress shown every 15s
- ✅ Clear timeout message after 60s
- ✅ Manual entry form presented
- ✅ Checkpoint still created with manual data
- ✅ User not confused or stuck

**Test Duration:** 2 minutes (or 60s if real timeout)

---

### Test Suite F2.4: No GPS in Dashboard Photo

**Objective:** Test fallback when EXIF GPS missing

**Setup:**
- Dashboard screenshot (no EXIF GPS)

**Expected Flow:**
```
Claude: "📸 Dashboard photo received. Analyzing...
⏳ Extracting EXIF metadata...
❌ No GPS data in EXIF. Photo may be a screenshot.

Options:
1. Retake photo with camera app (not screenshot)
2. Enable location services on phone
3. Enter location manually:
   Where did you refuel? (address or coordinates)"

User: "OMV Station, Hlavná 45, Bratislava"

Claude: "Geocoding address...
[calls geo-routing.geocode_address]

Found: 48.1486°N, 17.1077°E (OMV Station, Bratislava)

Is this correct?"
```

**Success Criteria:**
- ✅ Clear error message
- ✅ Helpful suggestions
- ✅ Manual location entry works
- ✅ Geocoding called for address
- ✅ User confirms location
- ✅ Checkpoint created with geocoded coords

**Test Duration:** 2 minutes

---

### Test Suite F2.5: No QR Code in Receipt

**Objective:** Test fallback when QR missing

**Setup:**
- Receipt photo without QR code

**Expected Flow:**
```
Claude: "📸 Receipt photo detected. Scanning QR code...
⏳ Trying scale 1x... not found
⏳ Trying scale 2x... not found
⏳ Trying scale 3x... not found

❌ QR code not detected.

Options:
1. Try a clearer photo
2. Enter receipt ID manually (format: o2a9s3d8f7g6h5j4)
3. Enter all receipt details manually

What would you like to do?"

User: "Enter manually: o2a9s3d8f7g6h5j4"

Claude: "Fetching receipt o2a9s3d8f7g6h5j4 from e-Kasa...
[continues normal flow]"
```

**Success Criteria:**
- ✅ All scales tried before giving up
- ✅ Clear "no QR found" message
- ✅ Manual ID entry option
- ✅ Full manual entry option
- ✅ Workflow continues after manual ID

**Test Duration:** 2 minutes

---

### Test Suite F2.6: OCR Odometer Low Confidence

**Objective:** Test handling of uncertain OCR results

**Setup:**
- Dashboard photo with blurry odometer

**Expected Flow:**
```
Claude: "📸 Dashboard photo received. Analyzing...
✓ GPS: 48.1486°N, 17.1077°E
✓ Timestamp: 2025-11-18 14:25
⚠️ Odometer reading uncertain: 45,820 km (confidence: 45%)

The odometer display is blurry. I read: 45,820 km

Is this correct, or enter manually?"

User: "Correct"

Claude: "✓ Odometer confirmed: 45,820 km
[continues]"
```

**Success Criteria:**
- ✅ Low confidence flagged (<70%)
- ✅ Extracted value shown for reference
- ✅ User can confirm or correct
- ✅ Manual override option
- ✅ Confidence logged in metadata

**Test Duration:** 1 minute

---

### Test Suite F2.7: Timestamp Mismatch

**Objective:** Test validation of photo timestamps

**Setup:**
- Receipt: 2025-11-18 14:23
- Dashboard: 2025-11-18 16:45 (2h 22m later)

**Expected Flow:**
```
Claude: "⚠️ Dashboard photo timestamp differs from receipt by 2h 22m.

Receipt time: 14:23
Dashboard time: 16:45

This is unusual. Did you:
1. Take photos at different times?
2. Forget to update phone time?
3. Photo timestamp incorrect?

Which timestamp is correct for the refuel?"

User: "Use receipt time 14:23"

Claude: "✓ Using receipt timestamp: 14:23
[continues with warning logged]"
```

**Success Criteria:**
- ✅ Mismatch detected (>10 minutes)
- ✅ User can choose correct timestamp
- ✅ Warning logged in checkpoint metadata
- ✅ Both timestamps preserved
- ✅ Explanation clear

**Test Duration:** 1 minute

---

### Test Suite F2.8: No Gap After Checkpoint

**Objective:** Test when gap detection finds no gap

**Setup:**
- Previous checkpoint 50 km ago (below 100 km threshold)

**Expected Flow:**
```
Claude: "✅ Checkpoint created!

Refuel Stop - OMV Bratislava
• Time: 2025-11-18 14:25
• Location: 48.1486°N, 17.1077°E
• Odometer: 45,050 km
• Fuel: 52.3L Diesel (€75.84)

Checking for gaps... ✓ No gap detected (50 km since last checkpoint)

Ready to add another checkpoint!"
```

**Success Criteria:**
- ✅ Gap detection runs
- ✅ No gap found (< 100 km threshold)
- ✅ No reconstruction prompt
- ✅ Simple confirmation
- ✅ Ready for next checkpoint

**Test Duration:** 1 minute

---

### Test Suite F2.9: Multiple Fuel Items in Receipt

**Objective:** Test handling of receipts with multiple fuel types

**Setup:**
- Receipt with Diesel (50.2L) + AdBlue (10L)

**Expected Flow:**
```
Claude: "✓ Receipt loaded!

⚠️ Multiple fuel items found:
1. Diesel - 50.2L @ €1.45/L (€72.79)
2. AdBlue - 10L @ €0.95/L (€9.50)

Which is the main fuel for mileage calculation?"

User: "Diesel"

Claude: "✓ Main fuel: Diesel (50.2L)

Note: AdBlue logged in receipt metadata but not used for fuel efficiency calculation.

[continues]"
```

**Success Criteria:**
- ✅ Multiple items detected
- ✅ User selects primary fuel
- ✅ Secondary items logged
- ✅ Only primary used for efficiency
- ✅ Clear explanation

**Test Duration:** 1 minute

---

### Test Suite F2.10: Geocoding Receipt Address

**Objective:** Test GPS vs address comparison

**Setup:**
- Dashboard GPS: 48.1486°N, 17.1077°E
- Receipt address: "OMV, Hlavná 45, Bratislava"

**Expected Flow:**
```
Claude: "Comparing locations...

Dashboard GPS: 48.1486°N, 17.1077°E
Receipt address: OMV, Hlavná 45, Bratislava
Geocoded: 48.1490°N, 17.1080°E

Distance: 45m ✓ (within 500m tolerance)

Using dashboard GPS (more accurate).
Address: OMV Station, Bratislava (label)"
```

**Alternative (mismatch):**
```
Claude: "⚠️ Location mismatch detected:

Dashboard GPS: 48.1486°N, 17.1077°E (Bratislava)
Receipt address: OMV Košice
Geocoded: 48.7164°N, 21.2611°E (Košice)

Distance: 410 km!

Which location is correct for this refuel?"
```

**Success Criteria:**
- ✅ Receipt address geocoded
- ✅ GPS vs address compared
- ✅ Within 500m → use GPS
- ✅ > 500m → warn user
- ✅ User can choose correct location

**Test Duration:** 2 minutes

---

## SKILL 3: Trip Reconstruction - Test Scenarios

### Test Suite F3.1: High Confidence Single Match (Happy Path)

**Objective:** Test perfect template match with GPS

**Setup:**
- Gap: Bratislava → Košice (820km, 7 days)
- Template: Warehouse Run (410km round trip)
- GPS: Within 50m of template endpoints

**Input:**
```
User: "Yes, reconstruct trips" [after gap detection]
```

**Expected Flow:**
```
Claude: "📊 Analyzing gap...

Gap details:
• Start: Bratislava (48.14°N, 17.10°E) - Nov 1, 45,000 km
• End: Košice (48.71°N, 21.26°E) - Nov 8, 45,820 km
• Distance: 820 km
• Duration: 7 days

Fetching your templates...

Found 3 templates:
• Warehouse Run (Bratislava ↔ Košice, 410km)
• Daily Commute (25km)
• Client Visit (45km)

Running GPS-first matching (70% GPS, 30% address)...

📊 Reconstruction Proposal (92% confidence):

✓ Exact GPS match (within 50m)
✓ Day-of-week matches template (Mon/Thu)
✓ Distance matches expected route

Proposal:
2× Warehouse Run (Bratislava ↔ Košice)
• Nov 1 08:00-12:30: Bratislava → Košice (410km)
• Nov 6 14:00-18:30: Košice → Bratislava (410km)

Coverage: 820km / 820km (100%) ✓

Confidence breakdown:
• GPS match: 98% (within 50m) → 68.6 points (70% weight)
• Address match: 75% (city names) → 22.5 points (30% weight)
• Day-of-week bonus: +5 points
• Distance match bonus: +5 points
Total: 92%

This looks very reliable. Accept? (yes/edit/no)"

User: "Yes"

Claude: "Creating trips...

[calls car-log-core.create_trips_batch]

✅ 2 trips created!

Running validation...

[calls validation.validate_checkpoint_pair]
[calls validation.validate_trip for each]

✅ Validation Passed:
• Distance: 820km / 820km (0% variance) ✓
• Fuel: 72.8L / 69.7L (+4.4%, within 15% threshold) ✓
• Efficiency: 8.9 L/100km (Diesel range: 5-15) ✓

Your trips are ready for tax reporting!"
```

**Expected MCP Calls:**
```json
[
  {"tool": "car-log-core.analyze_gap"},
  {"tool": "car-log-core.list_templates"},
  {"tool": "geo-routing.calculate_route", "optional": true},
  {"tool": "trip-reconstructor.match_templates"},
  {"tool": "car-log-core.create_trips_batch"},
  {"tool": "validation.validate_checkpoint_pair"},
  {"tool": "validation.validate_trip", "count": 2}
]
```

**Success Criteria:**
- ✅ 92% confidence displayed
- ✅ Clear proposal presentation
- ✅ Confidence breakdown shown
- ✅ GPS distance explained ("within 50m")
- ✅ Bonuses explained
- ✅ 2 trips created
- ✅ All validations pass
- ✅ Success message clear

**Test Duration:** 2-3 minutes

---

### Test Suite F3.2: Medium Confidence (Requires Confirmation)

**Objective:** Test 70-89% confidence with warnings

**Setup:**
- Gap: Similar to Warehouse Run
- GPS: 1.2 km off from template

**Expected Flow:**
```
Claude: "📊 Reconstruction Proposal (75% confidence):

⚠️ GPS match is approximate (within 1.2km)
✓ City names match (Bratislava, Košice)
⚠️ Days don't match typical pattern (Wed/Sat vs Mon/Thu)

Proposal:
2× Warehouse Run (820km total)
• Nov 2: Bratislava → Košice (410km)
• Nov 7: Košice → Bratislava (410km)

Coverage: 820km / 820km (100%) ✓

Confidence breakdown:
• GPS match: 75% (within 1.2km) → 52.5 points
• Address match: 85% (cities match) → 25.5 points
• No day bonus (Wed/Sat ≠ Mon/Thu)
• Distance match bonus: +5 points
Total: 75%

This is likely correct, but please verify:
1. Did you drive to Košice on Nov 2 (Wednesday)?
2. Did you return to Bratislava on Nov 7 (Saturday)?

Accept, modify, or reject? (yes/edit/no)"
```

**Success Criteria:**
- ✅ Confidence 70-89% triggers warnings
- ✅ GPS distance shown (1.2km)
- ✅ Day mismatch noted
- ✅ User verification questions
- ✅ Clear options (yes/edit/no)
- ✅ Explanation of uncertainty

**Test Duration:** 2 minutes

---

### Test Suite F3.3: No High-Confidence Match

**Objective:** Test < 70% confidence threshold

**Setup:**
- Gap: 820km
- Best template match: 58% confidence

**Expected Flow:**
```
Claude: "📊 No High-Confidence Match Found

I found potential matches, but none are above 70% confidence:

1. Warehouse Run (58%)
   - Distance matches (410km × 2)
   - GPS is 8km off (too far)
   - Days don't match

2. Client Visit (42%)
   - Wrong direction (Bratislava → Trnava)
   - Distance too short (45km)

Options:
1. Manually describe the trips
2. Create a new template for this route
3. Skip reconstruction for now

What would you like to do?"

User: "Create new template"

Claude: "Great! Let's create a template from this gap:

New Template:
• From: Košice (48.71°N, 21.26°E)
• To: Bratislava (48.14°N, 17.10°E)
• Distance: 410km
• Name: [what should we call this route?]"
```

**Success Criteria:**
- ✅ 70% threshold enforced
- ✅ Low confidence explained
- ✅ Best match shown for reference
- ✅ Why each match failed
- ✅ Options presented
- ✅ No automatic trip creation
- ✅ Template creation offered

**Test Duration:** 2 minutes

---

### Test Suite F3.4: Multiple High-Confidence Matches

**Objective:** Test user selection among multiple options

**Setup:**
- Gap: 820km
- 3 templates above 70%:
  - Warehouse Run: 92%
  - Client Circuit: 88%
  - Mixed Route: 78%

**Expected Flow:**
```
Claude: "📊 Multiple High-Confidence Matches Found:

Option 1: Warehouse Run (92%)
• 2× trips (820km total)
• GPS match: 98% (within 50m)
• Typical route: Mon/Thu ✓
• Coverage: 100%

Option 2: Client Circuit (88%)
• 4× trips (800km total, 20km uncovered)
• GPS match: 92% (within 200m)
• Mixed purposes (2 business, 2 personal)
• Coverage: 98%

Option 3: Mixed Route (78%)
• 1× Warehouse + 2× Daily Commute
• GPS match: 85% (within 500m)
• Coverage: 100%

Which option best matches your actual trips? (1/2/3/none)"

User: "1"

Claude: "✓ Selected: Option 1 (Warehouse Run, 92%)

[continues with trip creation]"
```

**Success Criteria:**
- ✅ All matches >= 70% shown
- ✅ Sorted by confidence (descending)
- ✅ Clear differentiation
- ✅ Coverage shown for each
- ✅ User can choose any option
- ✅ Can reject all options
- ✅ Selected option proceeds

**Test Duration:** 2 minutes

---

### Test Suite F3.5: Partial Coverage

**Objective:** Test handling of incomplete coverage

**Setup:**
- Gap: 820km
- Best match: 800km (20km uncovered)

**Expected Flow:**
```
Claude: "📊 Reconstruction Proposal (85% confidence):

⚠️ Partial coverage: 800km / 820km (98%)
20km uncovered

Proposal:
2× Warehouse Run (800km)

Options:
1. Accept partial (create 800km trips, 20km unaccounted)
2. Add manual trip for missing 20km
3. Try different template combination

What would you like to do?"

User: "Add manual trip"

Claude: "Great! Let's add a 20km trip.

Where was this 20km driven?
From: _____
To: _____"
```

**Success Criteria:**
- ✅ Coverage percentage shown (98%)
- ✅ Uncovered distance highlighted (20km)
- ✅ Options for handling gap
- ✅ Manual trip addition offered
- ✅ User can accept partial
- ✅ Clear explanation

**Test Duration:** 2 minutes

---

### Test Suite F3.6: Round Trip Detection

**Objective:** Test round trip template matching

**Setup:**
- Gap: Bratislava → Košice → Bratislava (same start/end)
- Template: Warehouse Run (round trip enabled)

**Expected Flow:**
```
Claude: "📊 Round trip detected!

Start location: Bratislava (48.14°N, 17.10°E)
End location: Bratislava (48.14°N, 17.10°E)
Total distance: 820km

Matching round trip template: Warehouse Run

Proposal (92% confidence):
1× Warehouse Run (round trip)
• Outbound: Bratislava → Košice (410km)
• Return: Košice → Bratislava (410km)

This will create 2 trips. Accept?"
```

**Success Criteria:**
- ✅ Same start/end location detected
- ✅ Round trip template matched
- ✅ Both directions created
- ✅ Presented as single round trip
- ✅ User sees it as one unit
- ✅ 2 trips actually created

**Test Duration:** 1 minute

---

### Test Suite F3.7: Day-of-Week Bonus

**Objective:** Test day matching bonus

**Setup:**
- Gap: Monday & Thursday
- Template: Typical days Mon/Thu

**Expected Flow:**
```
Claude: "Confidence breakdown:
• GPS match: 87% → 60.9 points
• Address match: 70% → 21.0 points
• Day-of-week bonus: +5 points ✓ (Mon/Thu matches template)
• Distance match: +5 points
Total: 92%

✓ Your trips match your typical Monday & Thursday schedule!"
```

**Success Criteria:**
- ✅ Day bonus applied (+5%)
- ✅ Shown in confidence breakdown
- ✅ Explained to user
- ✅ Confidence increased
- ✅ Typical days displayed

**Test Duration:** 1 minute

---

### Test Suite F3.8: Distance Variance

**Objective:** Test distance bonus

**Test Cases:**

| Gap Distance | Template Distance | Variance | Bonus |
|--------------|-------------------|----------|-------|
| 820 km | 820 km | 0 km | +5% ✓ |
| 820 km | 825 km | 5 km | +5% ✓ |
| 820 km | 835 km | 15 km | 0% (>10km) |

**Success Criteria:**
- ✅ Distance variance calculated
- ✅ Bonus applied if <10km
- ✅ Shown in breakdown
- ✅ Explained to user

**Test Duration:** 1 minute

---

### Test Suite F3.9: Validation Failure After Creation

**Objective:** Test validation warnings

**Setup:**
- Trips created
- Fuel consumption +25% (exceeds 15% threshold)

**Expected Flow:**
```
Claude: "✅ 2 trips created!

Running validation...

⚠️ Validation Warning:

Fuel consumption higher than expected:
• Expected: 69.7L (based on 8.5 L/100km)
• Actual: 87.1L
• Variance: +25% (exceeds 15% threshold)

Possible causes:
- Heavy traffic or city driving
- Air conditioning usage
- Vehicle load (cargo/passengers)
- Aggressive driving

Your trips are saved. Would you like to:
1. Keep trips as-is (flag for review)
2. Adjust fuel efficiency estimate
3. Review trip distances

What would you like to do?"
```

**Success Criteria:**
- ✅ Validation runs automatically
- ✅ Warnings don't block creation
- ✅ Clear explanation
- ✅ Possible causes listed
- ✅ User can review/adjust
- ✅ Trips marked for review

**Test Duration:** 1 minute

---

### Test Suite F3.10: No Templates (First-Time User)

**Objective:** Test template creation suggestion

**Setup:**
- Gap detected
- No templates exist

**Expected Flow:**
```
Claude: "No templates found. Let's create your first one!

This gap:
• From: Bratislava (48.14°N, 17.10°E)
• To: Košice (48.71°N, 21.26°E)
• Distance: 410km
• When: Nov 1-8

Create template for this route?

If you drive this regularly, I can auto-match it next time with 90%+ confidence!

Template name: [suggest: Bratislava-Košice Route]"

User: "Yes, call it Warehouse Run"

Claude: "✓ Template 'Warehouse Run' created!

Now, was this a round trip (return to Bratislava)?

This will help me match 2× trips next time."

User: "Yes, round trip on Mondays and Thursdays"

Claude: "Perfect! Template created:
• Warehouse Run
• Bratislava ↔ Košice (410km each way)
• Round trip: Yes
• Typical days: Monday, Thursday

Next time you have a similar gap, I'll match this with 90%+ confidence!

For now, let's manually enter the trips:"
```

**Success Criteria:**
- ✅ Empty template list handled
- ✅ Template creation suggested
- ✅ Gap data used for template
- ✅ Round trip question asked
- ✅ Typical days captured
- ✅ Manual entry offered
- ✅ User educated on future matching

**Test Duration:** 2-3 minutes

---

## Integration Test Scenarios

### Integration Test 1: End-to-End Happy Path

**Objective:** Test complete workflow from vehicle to report

**Flow:**
1. Create vehicle (F1)
2. Add checkpoint from receipt photos (F2)
3. Add second checkpoint
4. Reconstruct trips (F3)
5. Generate report

**Duration:** 10 minutes
**Success:** Report generated with all data

---

### Integration Test 2: Error Recovery Path

**Objective:** Test fallbacks across all skills

**Flow:**
1. Create vehicle with VIN error → correct
2. Add checkpoint with timeout → manual entry
3. Add checkpoint with no GPS → manual location
4. Reconstruct with no match → manual trips

**Duration:** 15 minutes
**Success:** All fallbacks work, data created

---

### Integration Test 3: Multi-Vehicle Multi-Trip

**Objective:** Test complex scenario

**Flow:**
1. Create 2 vehicles
2. Add checkpoints to both
3. Create templates for each
4. Reconstruct trips for both
5. Generate separate reports

**Duration:** 20 minutes
**Success:** Vehicles kept separate, reports accurate

---

## Test Reporting Template

```markdown
### Test Result: [Test Suite ID]

**Test:** [Test name]
**Date:** [YYYY-MM-DD]
**Tester:** [Name]
**Status:** ✅ PASS | ❌ FAIL | ⚠️ PARTIAL

**Setup:**
- [Setup steps]

**Execution:**
1. [Step 1 result]
2. [Step 2 result]
...

**Expected MCP Calls:**
- [List of calls]

**Actual MCP Calls:**
- [Actual calls made]

**Issues Found:**
- [Issue 1]
- [Issue 2]

**Recommendations:**
- [Recommendation 1]

**Screenshots/Logs:**
- [Attach if applicable]
```

---

## Test Summary Checklist

### Skill 1 (Vehicle Setup)
- [ ] F1.1: Standard registration
- [ ] F1.2: Guided registration
- [ ] F1.3: Invalid VIN handling
- [ ] F1.4: License plate formats
- [ ] F1.5: Duplicate detection
- [ ] F1.6: Odometer validation
- [ ] F1.7: Fuel efficiency display
- [ ] F1.8: Multi-vehicle support

### Skill 2 (Checkpoint from Receipt)
- [ ] F2.1: Happy path workflow
- [ ] F2.2: Multi-scale QR detection
- [ ] F2.3: Timeout handling
- [ ] F2.4: No GPS fallback
- [ ] F2.5: No QR fallback
- [ ] F2.6: Low OCR confidence
- [ ] F2.7: Timestamp mismatch
- [ ] F2.8: No gap scenario
- [ ] F2.9: Multiple fuel items
- [ ] F2.10: GPS vs address comparison

### Skill 3 (Trip Reconstruction)
- [ ] F3.1: High confidence match
- [ ] F3.2: Medium confidence
- [ ] F3.3: No match (<70%)
- [ ] F3.4: Multiple matches
- [ ] F3.5: Partial coverage
- [ ] F3.6: Round trip detection
- [ ] F3.7: Day-of-week bonus
- [ ] F3.8: Distance variance
- [ ] F3.9: Validation warnings
- [ ] F3.10: No templates

### Integration Tests
- [ ] End-to-end happy path
- [ ] Error recovery path
- [ ] Multi-vehicle scenario

**Total Test Time Estimate:** 4-6 hours
**Required:** 80% pass rate for production release
**Target:** 95% pass rate for MVP

---

**Testing Status:** Ready for manual execution
**Last Updated:** 2025-11-20
**Version:** 1.0
