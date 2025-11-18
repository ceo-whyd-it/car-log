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

**Implementation Status:** 📋 Specification ready
**Estimated Effort:** 3-4 hours
**Dependencies:** ekasa-api ✅, dashboard-ocr ✅, car-log-core ✅
