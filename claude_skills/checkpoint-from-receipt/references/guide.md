# Skill 2: Checkpoint from Receipt Photo

**Purpose:** Create checkpoints by processing fuel receipt photos (QR scan + EXIF GPS)

**Priority:** P0 (Core workflow - 30-second checkpoint creation)

---

## Trigger Words

- User pastes image in chat
- "refuel", "fill up", "gas station", "fuel receipt"
- "checkpoint", "add stop"
- After detecting image: "Is this a fuel receipt?"

---

## Workflow (3-Step Process)

### Step 1: Receipt QR Scanning

```
User: [pastes receipt photo]

Claude: "📸 Receipt photo detected. Scanning QR code...

[Calls: ekasa-api.scan_qr_code]

✓ QR code found: o2a9s3d8f7g6h5j4
Fetching receipt from e-Kasa API (may take 30s)...

[Calls: ekasa-api.fetch_receipt_data with 60s timeout]

✓ Receipt loaded:
• Vendor: OMV Station Bratislava
• Date: 2025-11-18 14:23
• Fuel: 52.3L Diesel @ €1.45/L
• Total: €75.84 (€63.20 excl VAT)

Is this correct?"
```

### Step 2: Dashboard Photo for GPS

```
Claude: "Great! Now I need your dashboard photo to get:
• GPS coordinates (70% weight in trip matching)
• Exact timestamp
• Odometer reading (if visible)

Paste dashboard photo:"

User: [pastes dashboard photo]

Claude: "📸 Analyzing dashboard photo...

[Calls: dashboard-ocr.extract_metadata]

✓ GPS: 48.1486°N, 17.1077°E (Bratislava)
✓ Timestamp: 2025-11-18 14:25
✓ Odometer: 45,820 km (OCR confidence: 95%)

Location: OMV Station, Hlavná 45, Bratislava
Matches receipt timestamp ✓"
```

### Step 3: Create Checkpoint

```
Claude: "Creating checkpoint...

[Calls: car-log-core.create_checkpoint]

✅ Checkpoint created!

Refuel Stop - OMV Bratislava
• Time: 2025-11-18 14:25
• Location: 48.1486°N, 17.1077°E
• Odometer: 45,820 km
• Fuel: 52.3L Diesel (€75.84)

[Calls: car-log-core.detect_gap with previous checkpoint]

⚠️ Gap detected: 820 km since last checkpoint (7 days ago)

Would you like me to reconstruct trips for this gap?"
```

---

## MCP Tools Used

1. **ekasa-api.scan_qr_code** - Extract receipt ID from QR code
2. **ekasa-api.fetch_receipt_data** - Get receipt from Slovak e-Kasa API (60s timeout)
3. **dashboard-ocr.extract_metadata** - EXIF GPS, timestamp from photo
4. **car-log-core.create_checkpoint** - Save checkpoint with receipt + GPS
5. **car-log-core.detect_gap** - Check for trip gaps (triggers reconstruction)

---

## Error Handling

### No QR Code Found
```
Claude: "❌ QR code not detected. This might be:
• Photo quality too low (try better lighting)
• Not an e-Kasa receipt (only Slovak receipts supported)
• QR code cropped out

Options:
1. Retry with clearer photo
2. Enter receipt ID manually: o2a9s3..."
```

### e-Kasa API Timeout
```
Claude: "⏱️ e-Kasa API taking longer than usual (30s+)...
Still waiting... (Slovak tax system can be slow)
[after 60s]
❌ Timeout. Let's enter details manually:
• Fuel quantity (liters):
• Price per liter (€):
• Vendor name:"
```

### No GPS in Photo
```
Claude: "⚠️ Photo doesn't contain GPS data (EXIF missing).

Options:
1. Use phone camera app (not screenshot)
2. Enable location services
3. Enter location manually:
   Where did you refuel?"
```

---

## Slovak e-Kasa Integration

### Multi-Scale QR Detection
```python
# Tries 1x, 2x, 3x zoom to find small QR codes in PDFs
scales = [1.0, 2.0, 3.0]
for scale in scales:
    qr_found = scan_at_scale(receipt_pdf, scale)
    if qr_found: break
```

### Fuel Item Detection (Slovak Names)
```
Patterns matched:
• "Diesel" / "Nafta" / "Motorová nafta"
• "Natural 95" / "BA 95" / "Benzín 95"
• "Natural 98" / "BA 98" / "Benzín 98"
• "LPG" / "Autoplyn"
```

---

## GPS-First Philosophy

**Why GPS is Critical:**
- 70% weight in template matching
- Addresses can be ambiguous ("Košice" has 3 fuel stations)
- GPS enables 100m accuracy matching

**User Message:**
```
"📍 GPS coordinates saved - I'll match your templates with 92% confidence!"
```

---

## Success Criteria

- ✅ QR scan works with low-res PDFs (multi-scale)
- ✅ 60s timeout for e-Kasa API
- ✅ EXIF GPS extraction from photos
- ✅ Automatic gap detection triggers
- ✅ 30-second workflow (paste 2 photos → done)
- ✅ Graceful fallback to manual entry

---

## Detailed Orchestration Flow

### Complete 2-Photo Workflow

```typescript
// Photo 1: Receipt QR Scan
async function processReceiptPhoto(image) {
  // Step 1: Detect image type
  if (!isImage(image)) {
    return askForImage();
  }

  // Step 2: Show progress
  showProgress("Scanning QR code from receipt...");

  // Step 3: Multi-scale QR detection
  const qrResult = await mcp.call("ekasa-api.scan_qr_code", {
    image_path: image.path,
    scales: [1.0, 2.0, 3.0] // Try multiple scales for PDFs
  });

  if (!qrResult.success) {
    return handleNoQR(); // Fallback to manual entry
  }

  // Step 4: Fetch from e-Kasa (with timeout handling)
  showProgress("Fetching receipt from e-Kasa API (may take 30s)...");

  try {
    const receipt = await mcp.call("ekasa-api.fetch_receipt_data", {
      receipt_id: qrResult.receipt_id,
      timeout: 60 // 60 second timeout
    });

    return {
      receipt_id: qrResult.receipt_id,
      vendor: receipt.vendor_name,
      datetime: receipt.datetime,
      fuel_liters: receipt.fuel_liters,
      fuel_type: receipt.fuel_type,
      price_excl_vat: receipt.price_excl_vat,
      price_incl_vat: receipt.price_incl_vat
    };
  } catch (TimeoutError) {
    return handleTimeout(); // Fallback after 60s
  }
}

// Photo 2: Dashboard GPS & Odometer
async function processDashboardPhoto(image, receiptData) {
  showProgress("Extracting GPS and odometer from dashboard photo...");

  const metadata = await mcp.call("dashboard-ocr.extract_metadata", {
    image_path: image.path
  });

  if (!metadata.gps) {
    return handleNoGPS(); // Fallback to manual location
  }

  // Validate timestamp matches receipt (within 10 minutes)
  const timeDiff = Math.abs(metadata.timestamp - receiptData.datetime);
  if (timeDiff > 600) { // 10 minutes
    showWarning("Dashboard photo timestamp differs from receipt by ${timeDiff/60} minutes");
  }

  return {
    coords: metadata.gps,
    timestamp: metadata.timestamp,
    odometer_km: metadata.odometer_reading,
    ocr_confidence: metadata.confidence
  };
}

// Create Checkpoint & Detect Gap
async function createCheckpoint(receipt, dashboard, vehicle_id) {
  const checkpoint = await mcp.call("car-log-core.create_checkpoint", {
    vehicle_id: vehicle_id,
    checkpoint_type: "refuel",
    datetime: dashboard.timestamp,
    odometer_km: dashboard.odometer_km,
    location: {
      coords: dashboard.coords,
      address: await geocodeAddress(dashboard.coords), // Optional
      source: "exif"
    },
    receipt: {
      receipt_id: receipt.receipt_id,
      vendor_name: receipt.vendor,
      fuel_type: receipt.fuel_type,
      fuel_liters: receipt.fuel_liters,
      price_excl_vat: receipt.price_excl_vat,
      price_incl_vat: receipt.price_incl_vat,
      vat_rate: calculateVATRate(receipt)
    }
  });

  // Automatic gap detection
  const gap = await mcp.call("car-log-core.detect_gap", {
    checkpoint_id: checkpoint.checkpoint_id
  });

  if (gap.has_gap) {
    promptTripReconstruction(gap);
  }

  return checkpoint;
}
```

---

## Progress Indicators & User Communication

### During QR Scanning (1-5 seconds)
```
User: [pastes receipt photo]

Claude: "📸 Receipt photo detected. Scanning QR code...
⏳ Trying scale 1x... not found
⏳ Trying scale 2x... not found
⏳ Trying scale 3x... ✓ QR code found!

Receipt ID: o2a9s3d8f7g6h5j4"
```

### During e-Kasa API Call (5-30 seconds typical)
```
Claude: "Fetching receipt from e-Kasa API...
⏳ Please wait, this may take up to 30 seconds.

Slovak tax system can be slow during peak hours.

[15 seconds pass]

⏳ Still waiting... (30s max)

[Receipt arrives after 22s]

✓ Receipt loaded!
• Vendor: OMV Station Bratislava
• Date: 2025-11-18 14:23
• Fuel: 52.3L Diesel @ €1.45/L
• Total: €75.84 (€63.20 excl VAT)"
```

### During e-Kasa Timeout (60 seconds)
```
Claude: "Fetching receipt from e-Kasa API...
⏳ Please wait, this may take up to 60 seconds.

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

### During Dashboard OCR (3-8 seconds)
```
User: [pastes dashboard photo]

Claude: "📸 Dashboard photo received. Analyzing...
⏳ Extracting EXIF metadata...
✓ GPS coordinates found: 48.1486°N, 17.1077°E
✓ Photo timestamp: 2025-11-18 14:25
⏳ Running OCR on odometer display...
✓ Odometer reading: 45,820 km (confidence: 95%)

Would you like to adjust the odometer reading?"
```

---

## Testing Scenarios

### Test 1: Happy Path (Both Photos Have All Data)
```
Input:
1. Receipt photo with QR code
2. Dashboard photo with GPS + odometer

Expected Flow:
1. Scan QR → Found
2. Fetch e-Kasa → Success (15s)
3. Extract GPS → Found
4. Extract odometer → 45,820 km (95% confidence)
5. Create checkpoint → Success
6. Detect gap → 820 km gap found
7. Prompt reconstruction

Expected Tools Called:
- ekasa-api.scan_qr_code
- ekasa-api.fetch_receipt_data
- dashboard-ocr.extract_metadata
- car-log-core.create_checkpoint
- car-log-core.detect_gap

Success Criteria:
✓ Entire workflow < 30 seconds
✓ All data extracted automatically
✓ Gap detection triggers
✓ User prompted for next step
```

### Test 2: Low-Quality Receipt PDF (Multi-Scale Needed)
```
Input: PDF receipt with small QR code

Expected Flow:
1. Try 1x scale → QR not found
2. Try 2x scale → QR not found
3. Try 3x scale → QR found! ✓
4. Fetch e-Kasa → Success

Expected Tools Called:
- ekasa-api.scan_qr_code (with scales: [1.0, 2.0, 3.0])

Success Criteria:
✓ Multi-scale detection works
✓ User sees progress ("Trying 2x...")
✓ QR found at 3x scale
```

### Test 3: e-Kasa API Timeout (60s)
```
Input: Valid receipt ID

Expected Flow:
1. Scan QR → Found
2. Fetch e-Kasa → Timeout after 60s
3. Fallback to manual entry
4. Ask for: fuel_liters, price, vendor

Expected Behavior:
- Show progress every 15s
- Clear timeout message after 60s
- Manual entry form presented
- Still create checkpoint with manual data

Success Criteria:
✓ Timeout handled gracefully
✓ User not confused
✓ Manual fallback works
```

### Test 4: No GPS in Dashboard Photo
```
Input: Dashboard screenshot (no EXIF data)

Expected Flow:
1. Extract metadata → No GPS found
2. Warn user: "Photo doesn't contain GPS"
3. Options:
   a) Retake with camera app
   b) Enter location manually
   c) Use vendor address from receipt

Expected Tools Called:
- dashboard-ocr.extract_metadata (returns no GPS)
- geo-routing.geocode_address (if manual entry)

Success Criteria:
✓ Clear error message
✓ Helpful suggestions
✓ Manual location entry works
```

### Test 5: No QR Code in Receipt
```
Input: Receipt photo without QR code

Expected Flow:
1. Scan QR → Not found (all scales)
2. Ask for receipt ID manually
3. User enters: "o2a9s3d8f7g6h5j4"
4. Fetch e-Kasa → Success
5. Continue normal flow

Expected Behavior:
- Try all 3 scales before giving up
- Clear "no QR found" message
- Manual ID entry option
- Option to enter all data manually

Success Criteria:
✓ Multi-scale tried before failing
✓ Manual entry fallback
✓ Workflow continues normally
```

### Test 6: OCR Odometer Low Confidence
```
Input: Dashboard photo with blurry odometer

Expected Flow:
1. Extract metadata → GPS ✓, Odometer: 45820 (45% confidence)
2. Warn: "Odometer reading uncertain: 45,820 km"
3. Ask: "Is this correct, or enter manually?"
4. User confirms or corrects

Expected Behavior:
- Flag confidence < 70%
- Show extracted value for reference
- Allow user confirmation
- Manual override option

Success Criteria:
✓ Low confidence detected
✓ User can verify
✓ Manual override works
```

### Test 7: Timestamp Mismatch (Dashboard vs Receipt)
```
Input:
- Receipt: 2025-11-18 14:23
- Dashboard: 2025-11-18 16:45 (2h 22m later)

Expected Behavior:
⚠️ "Dashboard photo timestamp differs from receipt by 2h 22m.
    This is unusual. Did you:
    1. Take photos at different times?
    2. Forget to update phone time?

    Which timestamp is correct?"

Success Criteria:
✓ Mismatch detected (>10 minutes)
✓ User can choose correct timestamp
✓ Warning logged in checkpoint metadata
```

### Test 8: No Gap After Checkpoint
```
Input: Checkpoint created, previous checkpoint was 50 km ago

Expected Flow:
1. Create checkpoint → Success
2. Detect gap → No gap (< 100 km threshold)
3. Confirm: "Checkpoint created! No trip reconstruction needed."

Expected Behavior:
- No gap detection prompt
- Simple confirmation
- Ready for next checkpoint

Success Criteria:
✓ Gap threshold respected (100 km)
✓ No unnecessary prompts
✓ Clean workflow completion
```

### Test 9: Multiple Fuel Items in Receipt
```
Input: Receipt with AdBlue + Diesel

Expected Flow:
1. Fetch e-Kasa → Returns multiple items
2. Detect fuel: "Diesel 50.2L", "AdBlue 10L"
3. Ask: "Multiple fuel items found. Which is the main fuel?"
4. User selects "Diesel"
5. Create checkpoint with Diesel only

Expected Behavior:
- Detect multiple fuel items
- Ask user to select primary
- Log secondary items in metadata

Success Criteria:
✓ Multiple items detected
✓ User can choose primary
✓ Both items logged
```

### Test 10: Geocoding Receipt Address
```
Input: Receipt address: "OMV, Hlavná 45, Bratislava"

Expected Flow:
1. Extract vendor address from receipt
2. Geocode address → Get coordinates
3. Compare with dashboard GPS
4. If within 500m → Use dashboard GPS (more accurate)
5. If > 500m → Warn user about mismatch

Expected Tools Called:
- geo-routing.geocode_address

Success Criteria:
✓ Receipt address geocoded
✓ GPS vs address comparison
✓ Mismatch warning if > 500m
```

---

## Error Recovery Patterns

### Pattern 1: Graceful Degradation
```javascript
// Try automatic → fallback to manual
async function getReceiptData(photo) {
  try {
    // Try QR scan
    const qr = await scanQR(photo);
    const receipt = await fetchEKasa(qr.receipt_id, {timeout: 60});
    return receipt;
  } catch (NoQRError) {
    // Fallback 1: Manual receipt ID
    const id = await askReceiptID();
    return await fetchEKasa(id, {timeout: 60});
  } catch (TimeoutError) {
    // Fallback 2: Manual entry
    return await askManualEntry();
  }
}
```

### Pattern 2: Progress with Timeout
```javascript
async function fetchWithProgress(receiptID) {
  const progressIntervals = [15, 30, 45]; // Show message at these seconds

  let elapsed = 0;
  const timer = setInterval(() => {
    elapsed += 1;
    if (progressIntervals.includes(elapsed)) {
      showProgress(`Still waiting... (${elapsed}s elapsed)`);
    }
  }, 1000);

  try {
    const receipt = await fetch(receiptID, {timeout: 60000});
    clearInterval(timer);
    return receipt;
  } catch (TimeoutError) {
    clearInterval(timer);
    showError("Timeout after 60s. Falling back to manual entry.");
    throw TimeoutError;
  }
}
```

### Pattern 3: Confidence Thresholds
```javascript
function validateOCRResult(result) {
  if (result.confidence >= 0.9) {
    // High confidence: auto-accept
    return {accepted: true, value: result.value};
  } else if (result.confidence >= 0.7) {
    // Medium confidence: show with confirmation
    return {accepted: false, suggested: result.value, needsConfirmation: true};
  } else {
    // Low confidence: ask manual entry
    return {accepted: false, suggested: result.value, askManual: true};
  }
}
```

---

## MCP Tool Call Examples

### Example 1: Scan QR Code (Multi-Scale)
```json
// Request
{
  "tool": "ekasa-api.scan_qr_code",
  "parameters": {
    "image_path": "/tmp/receipt_photo.jpg",
    "scales": [1.0, 2.0, 3.0]
  }
}

// Response (Success)
{
  "success": true,
  "receipt_id": "o2a9s3d8f7g6h5j4",
  "detection_scale": 2.0,
  "confidence": 0.98
}

// Response (Not Found)
{
  "success": false,
  "error": {
    "code": "QR_NOT_FOUND",
    "message": "QR code not detected at any scale",
    "scales_tried": [1.0, 2.0, 3.0]
  }
}
```

### Example 2: Fetch e-Kasa Receipt
```json
// Request
{
  "tool": "ekasa-api.fetch_receipt_data",
  "parameters": {
    "receipt_id": "o2a9s3d8f7g6h5j4",
    "timeout": 60
  }
}

// Response (Success)
{
  "success": true,
  "receipt": {
    "receipt_id": "o2a9s3d8f7g6h5j4",
    "vendor_name": "OMV Station Bratislava",
    "vendor_address": "Hlavná 45, Bratislava",
    "datetime": "2025-11-18T14:23:00Z",
    "items": [
      {
        "name": "Diesel",
        "quantity": 52.3,
        "unit": "L",
        "price_per_unit": 1.45,
        "price_excl_vat": 63.20,
        "price_incl_vat": 75.84,
        "vat_rate": 0.20
      }
    ],
    "fuel_type": "Diesel",
    "fuel_liters": 52.3,
    "price_excl_vat": 63.20,
    "price_incl_vat": 75.84
  },
  "fetch_duration_seconds": 22
}

// Response (Timeout)
{
  "success": false,
  "error": {
    "code": "TIMEOUT",
    "message": "e-Kasa API did not respond within 60 seconds",
    "timeout": 60
  }
}
```

### Example 3: Extract Dashboard Metadata
```json
// Request
{
  "tool": "dashboard-ocr.extract_metadata",
  "parameters": {
    "image_path": "/tmp/dashboard_photo.jpg"
  }
}

// Response (Full Data)
{
  "success": true,
  "metadata": {
    "gps": {
      "latitude": 48.1486,
      "longitude": 17.1077,
      "source": "exif"
    },
    "timestamp": "2025-11-18T14:25:00Z",
    "odometer_reading": 45820,
    "ocr_confidence": 0.95,
    "image_quality": "good"
  }
}

// Response (No GPS)
{
  "success": true,
  "metadata": {
    "gps": null,
    "timestamp": "2025-11-18T14:25:00Z",
    "odometer_reading": 45820,
    "ocr_confidence": 0.87,
    "warning": "No GPS data in EXIF. Photo may be a screenshot."
  }
}
```

### Example 4: Create Checkpoint
```json
// Request
{
  "tool": "car-log-core.create_checkpoint",
  "parameters": {
    "vehicle_id": "abc-123-def-456",
    "checkpoint_type": "refuel",
    "datetime": "2025-11-18T14:25:00Z",
    "odometer_km": 45820,
    "location": {
      "coords": {"latitude": 48.1486, "longitude": 17.1077},
      "address": "OMV Station, Hlavná 45, Bratislava",
      "source": "exif"
    },
    "receipt": {
      "receipt_id": "o2a9s3d8f7g6h5j4",
      "vendor_name": "OMV Station Bratislava",
      "fuel_type": "Diesel",
      "fuel_liters": 52.3,
      "price_excl_vat": 63.20,
      "price_incl_vat": 75.84,
      "vat_rate": 0.20
    }
  }
}

// Response
{
  "success": true,
  "checkpoint_id": "chk-789-xyz-012",
  "checkpoint": {
    "checkpoint_id": "chk-789-xyz-012",
    "vehicle_id": "abc-123-def-456",
    "checkpoint_type": "refuel",
    "datetime": "2025-11-18T14:25:00Z",
    "odometer_km": 45820,
    "location": {...},
    "receipt": {...},
    "created_at": "2025-11-20T15:00:00Z"
  }
}
```

### Example 5: Detect Gap
```json
// Request
{
  "tool": "car-log-core.detect_gap",
  "parameters": {
    "checkpoint_id": "chk-789-xyz-012"
  }
}

// Response (Gap Found)
{
  "success": true,
  "has_gap": true,
  "gap": {
    "start_checkpoint_id": "chk-456-abc-789",
    "end_checkpoint_id": "chk-789-xyz-012",
    "distance_km": 820,
    "duration_days": 7,
    "start_datetime": "2025-11-01T08:00:00Z",
    "end_datetime": "2025-11-18T14:25:00Z",
    "start_location": {"coords": {...}, "address": "Košice"},
    "end_location": {"coords": {...}, "address": "Bratislava"}
  }
}

// Response (No Gap)
{
  "success": true,
  "has_gap": false,
  "previous_checkpoint": {
    "checkpoint_id": "chk-456-abc-789",
    "distance_km": 50,
    "duration_hours": 2
  }
}
```

---

## Integration with Trip Reconstruction

### Automatic Trigger After Gap Detection
```javascript
async function handleCheckpointCreation(checkpoint) {
  // Create checkpoint
  const result = await createCheckpoint(checkpoint);

  // Automatic gap detection
  const gap = await detectGap(result.checkpoint_id);

  if (gap.has_gap && gap.distance_km > 100) {
    // Trigger trip reconstruction skill
    showMessage(`
      ⚠️ Gap detected: ${gap.distance_km} km over ${gap.duration_days} days

      Would you like me to reconstruct trips for this gap?
      I can use your saved templates for automatic matching.
    `);

    const response = await askYesNo();
    if (response === 'yes') {
      // Activate Trip Reconstruction Skill (Skill 3)
      triggerTripReconstruction(gap);
    }
  } else {
    showMessage("✅ Checkpoint created! No trip reconstruction needed.");
  }
}
```

---

**Implementation Status:** 📋 Specification ready, implementation pending
**Estimated Effort:** 4 hours
**Dependencies:** ekasa-api ✅, dashboard-ocr ✅, car-log-core ✅
