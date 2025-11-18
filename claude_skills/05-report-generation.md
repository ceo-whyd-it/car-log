# Skill 5: Report Generation (Slovak VAT Act 2025 Compliant)

**Purpose:** Generate tax-compliant CSV/PDF reports with all required fields

**Priority:** P0

---

## Trigger Words

- "generate report", "export to CSV"
- "report for November", "I need tax report"
- "send to accountant"

---

## Workflow

### Step 1: Collect Parameters
```
User: "Generate November report"

Claude: "Creating November 2025 report.

Which vehicle?
• Ford Transit (BA-789XY)
• BMW 5 Series (BA-123CD)
[Calls: car-log-core.list_vehicles if multiple]"

User: "Ford Transit"

Claude: "Filter by purpose?
1. Business trips only (for tax deduction)
2. Personal trips only
3. All trips"

User: "Business only"

Claude: "Format?
• CSV (for accounting software)
• PDF (human-readable)
• Both"

User: "Both"
```

### Step 2: Generate Reports
```
Claude: "Generating reports...

[Calls: car-log-core.list_trips with filters]
[Calls: report-generator.generate_csv]
[Calls: report-generator.generate_pdf]

✅ Reports generated!

November 2025 Business Trips Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Totals:
• Distance: 1,850 km
• Fuel consumed: 164.5 L
• Avg efficiency: 8.9 L/100km
• Fuel cost: €325.80
• VAT: €54.30 (20%)
• Trips: 12

🇸🇰 Slovak VAT Act 2025 Compliance:
✅ VIN included (WVWZZZ3CZDP123456)
✅ Driver names included
✅ Trip start/end times separated from refuel
✅ L/100km format (European standard)
✅ All mandatory fields present

📄 Files ready:
• ford-transit-nov-2025.csv (12 KB)
• ford-transit-nov-2025.pdf (245 KB)

[Download buttons]"
```

---

## MCP Tools Used

1. **car-log-core.list_vehicles** - Select vehicle
2. **car-log-core.list_trips** - Query trips with filters
3. **report-generator.generate_csv** - CSV for accounting
4. **report-generator.generate_pdf** - PDF for archive

---

## Slovak Compliance Fields (Mandatory)

**Per Trip:**
- VIN (17 chars)
- Driver name
- Trip start datetime
- Trip end datetime
- Trip start location
- Trip end location
- Distance (km)
- Fuel consumption (L)
- Fuel efficiency (L/100km) ← European format
- Refuel datetime (separate from trip)
- Refuel timing ("before"/"during"/"after")
- Purpose (Business/Personal)
- Business description (if Business)

**Summary:**
- Total distance
- Total fuel consumed
- Total cost (excl VAT, incl VAT, VAT amount)
- Average efficiency (L/100km)

---

## CSV Format Example

```csv
VIN,Driver,TripStart,TripEnd,StartLocation,EndLocation,DistanceKm,FuelL,EfficiencyL100km,Purpose
WVWZZZ3CZDP123456,John Doe,2025-11-01 08:00,2025-11-01 12:30,Bratislava,Košice,410,34.85,8.5,Business
...
```

---

## Success Criteria

- ✅ All Slovak VAT Act 2025 fields included
- ✅ L/100km format (not km/L)
- ✅ CSV compatible with accounting software
- ✅ PDF human-readable
- ✅ Business trip filtering
- ✅ Summary statistics accurate

---

**Implementation:** 📋 Spec ready | **Effort:** 2 hours
