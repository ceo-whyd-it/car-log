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
2. **car-log-core.list_trips** - Query trips with filters (date range, purpose, vehicle)
3. **report-generator.generate_csv** - CSV for accounting software
4. **report-generator.generate_pdf** - PDF for human-readable archive (P1)
5. **validation.validate_compliance** - Verify Slovak VAT Act requirements

---

## Orchestration Pattern (Detailed)

### Pattern: Select → Filter → Generate → Verify → Present

```typescript
// 1. List vehicles (if user has multiple)
const vehicles = await car_log_core.list_vehicles({
  user_id: current_user
});

// 2. Collect filter parameters
// - Vehicle ID (from list or single vehicle)
// - Date range (start_date, end_date)
// - Purpose filter: "business" | "personal" | "all"

// 3. Fetch trips with filters
const trips = await car_log_core.list_trips({
  vehicle_id: selected_vehicle.vehicle_id,
  start_date: "2025-11-01",
  end_date: "2025-11-30",
  purpose: "business"  // For tax deduction
});

// 4. Calculate summary statistics
const summary = {
  total_distance_km: trips.reduce((sum, t) => sum + t.distance_km, 0),
  total_fuel_liters: trips.reduce((sum, t) => sum + (t.fuel_consumption_liters || 0), 0),
  avg_efficiency: total_fuel_liters / total_distance_km * 100,
  total_cost_excl_vat: trips.reduce((sum, t) => sum + (t.fuel_cost_excl_vat || 0), 0),
  total_cost_incl_vat: trips.reduce((sum, t) => sum + (t.fuel_cost_incl_vat || 0), 0),
  total_vat: total_cost_incl_vat - total_cost_excl_vat,
  trip_count: trips.length
};

// 5. Verify Slovak compliance
const compliance = await validation.validate_compliance({
  trips: trips,
  vehicle: selected_vehicle
});

// 6. Generate CSV report
const csv_report = await report_generator.generate_csv({
  trips: trips,
  vehicle: selected_vehicle,
  summary: summary,
  output_path: "~/Documents/MileageLog/reports/ford-transit-nov-2025.csv"
});

// 7. Optional: Generate PDF (P1 feature)
const pdf_report = await report_generator.generate_pdf({
  trips: trips,
  vehicle: selected_vehicle,
  summary: summary,
  output_path: "~/Documents/MileageLog/reports/ford-transit-nov-2025.pdf"
});

// 8. Present summary and compliance status to user
```

---

## File Location Guidance

**Default report location:**
```
~/Documents/MileageLog/reports/
├── {vehicle_license}-{month}-{year}.csv
├── {vehicle_license}-{month}-{year}.pdf
└── index.json (report metadata)
```

**Example paths:**
- `~/Documents/MileageLog/reports/BA-789XY-nov-2025.csv`
- `~/Documents/MileageLog/reports/BA-789XY-nov-2025.pdf`

**User communication:**
```
"Reports saved to:
• ~/Documents/MileageLog/reports/BA-789XY-nov-2025.csv
• ~/Documents/MileageLog/reports/BA-789XY-nov-2025.pdf

You can open these files directly or share with your accountant."
```

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

## Slovak VAT Act 2025 Compliance Verification

### Compliance Checklist (Automatic)

After generating report, Claude should verify:

```
🇸🇰 Slovak VAT Act 2025 Compliance Check:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Vehicle VIN: WVWZZZ3CZDP123456 (17 chars, valid format)
✅ Driver names: Present in all 12 trips
✅ Trip timing: Start/End separated from refuel timing
✅ Locations: Start/End locations present in all trips
✅ Fuel efficiency: L/100km format (European standard)
✅ Business descriptions: Present for all 12 business trips
✅ Mandatory fields: 100% complete

Report is READY for tax deduction submission.
```

### Compliance Warnings

If any issues found:

```
⚠️ Compliance Issues Found:

1. Trip #3 missing driver name (MANDATORY for VAT Act 2025)
2. Trip #7 fuel efficiency in km/L format (must be L/100km)
3. Trip #9 missing business description (required for business trips)

Fix these issues before submitting to tax authority.
Would you like to edit these trips now? (yes/no)
```

### Mandatory vs. Optional Fields

**MANDATORY (Block submission if missing):**
- VIN (17 chars, no I/O/Q)
- Driver name
- Trip start datetime
- Trip end datetime
- Trip start location
- Trip end location
- Distance (km)
- Purpose (Business/Personal)
- Business description (if Business)

**RECOMMENDED (Warn if missing):**
- Fuel consumption (L)
- Fuel efficiency (L/100km)
- Refuel datetime
- Refuel timing

**OPTIONAL (No warning):**
- Template ID
- Confidence score
- Route alternatives

---

## Example Reports

### CSV Report Example

```csv
VIN,License_Plate,Driver_Name,Trip_Start,Trip_End,Start_Location,End_Location,Distance_Km,Fuel_L,Efficiency_L100km,Fuel_Cost_Excl_VAT,Fuel_Cost_Incl_VAT,VAT_Amount,Purpose,Business_Description,Refuel_DateTime,Refuel_Timing
WVWZZZ3CZDP123456,BA-789XY,John Doe,2025-11-01 08:00,2025-11-01 12:30,"Bratislava, Hlavná 45","Košice, Mlynská 12",410,34.85,8.5,58.20,69.84,11.64,Business,Client meeting - warehouse inspection,2025-11-01 07:45,before
WVWZZZ3CZDP123456,BA-789XY,John Doe,2025-11-01 14:00,2025-11-01 18:30,"Košice, Mlynská 12","Bratislava, Hlavná 45",410,36.90,9.0,61.60,73.92,12.32,Business,Return from warehouse inspection,2025-11-01 14:15,during
WVWZZZ3CZDP123456,BA-789XY,Jane Smith,2025-11-04 09:00,2025-11-04 13:15,"Bratislava, Hlavná 45","Košice, Mlynská 12",410,34.00,8.3,56.80,68.16,11.36,Business,Delivery run,2025-11-04 08:50,before
...

SUMMARY
Total_Distance_Km,Total_Fuel_L,Avg_Efficiency_L100km,Total_Cost_Excl_VAT,Total_Cost_Incl_VAT,Total_VAT,Trip_Count
1850,164.50,8.89,275.00,330.00,55.00,12
```

### PDF Report Example (Visual Layout)

```
╔════════════════════════════════════════════════════════════════╗
║                    MONTHLY MILEAGE REPORT                      ║
║                    Slovak VAT Act 2025 Compliant               ║
╚════════════════════════════════════════════════════════════════╝

Vehicle Information:
────────────────────
• Vehicle: Ford Transit
• License Plate: BA-789XY
• VIN: WVWZZZ3CZDP123456
• Period: November 2025
• Report Type: Business Trips Only

Summary Statistics:
────────────────────
• Total Distance: 1,850 km
• Total Fuel Consumed: 164.5 L
• Average Efficiency: 8.89 L/100km
• Fuel Cost (Excl. VAT): €275.00
• Fuel Cost (Incl. VAT): €330.00
• VAT Amount (20%): €55.00
• Number of Trips: 12

Trip Details:
────────────────────

Trip #1 - Nov 1, 2025
• Driver: John Doe
• Start: 08:00 - Bratislava, Hlavná 45
• End: 12:30 - Košice, Mlynská 12
• Distance: 410 km
• Fuel: 34.85 L (8.5 L/100km)
• Cost: €58.20 + €11.64 VAT = €69.84
• Purpose: Business - Client meeting - warehouse inspection
• Refuel: Nov 1, 07:45 (before trip)

[... additional trips ...]

Compliance Verification:
────────────────────────
✅ All mandatory fields present
✅ VIN format valid (17 characters)
✅ Driver names recorded for all trips
✅ Trip timing separated from refuel timing
✅ L/100km format used (European standard)
✅ Business descriptions provided

This report meets Slovak VAT Act 2025 requirements.

Generated: 2025-11-30 14:35
Report ID: RPT-BA789XY-202511
```

---

## Example Conversations

### Example 1: Single Vehicle, Month Report

```
User: "Generate November report"

Claude: "I'll generate your November 2025 mileage report.

[Calls: car-log-core.list_vehicles]

Found 1 vehicle: Ford Transit (BA-789XY)

Filter by trip purpose?
1. Business trips only (for tax deduction)
2. Personal trips only
3. All trips

(Default: Business only)"

User: "Business only"

Claude: "Format preference?
• CSV (for accounting software)
• PDF (human-readable)
• Both

(Recommended: Both)"

User: "Both"

Claude: "Generating reports...

[Calls: car-log-core.list_trips]
[Calls: validation.validate_compliance]
[Calls: report-generator.generate_csv]
[Calls: report-generator.generate_pdf]

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

Report is ready for tax deduction submission!"
```

### Example 2: Multiple Vehicles, Custom Date Range

```
User: "Generate report for my BMW from Nov 15 to Nov 30"

Claude: "Generating custom date range report...

[Calls: car-log-core.list_vehicles]

Found 2 vehicles:
1. Ford Transit (BA-789XY)
2. BMW 5 Series (BA-123CD)

Confirmed: BMW 5 Series (BA-123CD)

Date range: Nov 15-30, 2025

Filter by purpose?
1. Business only
2. Personal only
3. All trips"

User: "All trips"

Claude: "[Calls: car-log-core.list_trips with date filters]

Found 8 trips (5 business, 3 personal)

⚠️ Note: Personal trips cannot be used for tax deduction.
   Only business trips qualify for VAT deduction.

Generate report with:
1. Business trips only (5 trips, €245 VAT deductible)
2. All trips (8 trips, mixed purposes)
3. Separate reports (business + personal)"

User: "Separate reports"

Claude: "Generating 2 reports...

[Calls: report-generator.generate_csv twice]

✅ Reports generated!

Business Report (Nov 15-30):
• Distance: 1,230 km
• Fuel: 110.7 L (9.0 L/100km)
• VAT deductible: €44.50
• Trips: 5
• Files: BA-123CD-nov15-30-business.csv/pdf

Personal Report (Nov 15-30):
• Distance: 340 km
• Fuel: 27.2 L (8.0 L/100km)
• Trips: 3
• Files: BA-123CD-nov15-30-personal.csv/pdf

All files saved to ~/Documents/MileageLog/reports/"
```

### Example 3: Compliance Issues Found

```
User: "Generate October report"

Claude: "[Generating report...]

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

Recommendation: Fix issues first to ensure tax compliance."

User: "Fix now"

Claude: "Let's fix these issues:

Trip #3 (Oct 8, 2025):
• Route: Bratislava → Košice (410 km)
• Current driver: [MISSING]

Who was driving? (required for Slovak compliance)"

User: "John Doe"

Claude: "✓ Driver saved: John Doe

Trip #5 (Oct 12, 2025):
• Route: Bratislava → Prešov (385 km)
• Purpose: Business
• Current description: [MISSING]

What was the business purpose?"

User: "Client presentation"

Claude: "✓ Description saved

Trip #7 (Oct 19, 2025):
• Current efficiency: 11.8 km/L
• Correcting to European format: 8.5 L/100km

✓ Format corrected

[Calls: car-log-core.update_trip three times]

All issues fixed! Regenerating report...

[Generates compliant report]

✅ October 2025 Report Complete
All Slovak VAT Act 2025 requirements met!"
```

---

## Testing Scenarios

### Scenario 1: Happy Path - Monthly Business Report

**Input:**
- Vehicle: Ford Transit (BA-789XY)
- Period: November 2025
- Filter: Business only
- Format: CSV + PDF

**Expected Behavior:**
1. List vehicles (if multiple)
2. Fetch business trips for November
3. Calculate summary statistics
4. Verify Slovak compliance (all pass)
5. Generate CSV and PDF
6. Show summary with compliance checkmarks
7. Provide file paths

**MCP Calls:**
1. `car-log-core.list_vehicles`
2. `car-log-core.list_trips` (filters: vehicle, Nov 2025, business)
3. `validation.validate_compliance`
4. `report-generator.generate_csv`
5. `report-generator.generate_pdf`

### Scenario 2: Custom Date Range

**Input:**
- Vehicle: BMW (BA-123CD)
- Period: Nov 15-30, 2025
- Filter: All trips

**Expected Behavior:**
1. Accept custom date range
2. Fetch all trips in range
3. Warn about mixed purposes (personal not tax deductible)
4. Offer separate reports option
5. Generate requested format(s)

**MCP Calls:**
1. `car-log-core.list_trips` (start_date, end_date)
2. Filter trips by purpose (client-side or server-side)
3. `report-generator.generate_csv` (possibly twice)

### Scenario 3: Compliance Issues

**Input:**
- Period: October 2025
- Some trips missing mandatory fields

**Expected Behavior:**
1. Detect missing fields during validation
2. Show clear error messages
3. Offer to fix issues
4. Guide user through corrections
5. Regenerate report after fixes

**MCP Calls:**
1. `car-log-core.list_trips`
2. `validation.validate_compliance` (returns errors)
3. `car-log-core.update_trip` (for each fix)
4. Regenerate report

### Scenario 4: No Trips Found

**Input:**
- Period: December 2025 (future/empty)

**Expected Behavior:**
1. Query trips
2. Find zero trips
3. Show friendly message
4. Suggest alternatives (different date range, vehicle)

**Output:**
```
No trips found for December 2025.

Suggestions:
• Check if trips were logged for this period
• Try a different date range
• Verify vehicle selection
```

### Scenario 5: Large Report (100+ Trips)

**Input:**
- Period: Full year 2025
- Business trips only

**Expected Behavior:**
1. Fetch all trips (may be slow)
2. Show progress indicator if >50 trips
3. Generate CSV (handles large data well)
4. PDF may be multi-page
5. Summary shows annual totals

**Performance:**
- CSV generation: <2 seconds for 100 trips
- PDF generation: <5 seconds for 100 trips

---

## Success Criteria

- ✅ All Slovak VAT Act 2025 fields included
- ✅ L/100km format (not km/L)
- ✅ CSV compatible with accounting software (UTF-8, comma-separated)
- ✅ PDF human-readable with clear layout
- ✅ Business trip filtering working
- ✅ Custom date ranges supported
- ✅ Summary statistics accurate (totals, averages)
- ✅ Compliance verification automatic
- ✅ Missing field detection and correction flow
- ✅ File paths clearly communicated to user
- ✅ Multiple vehicle support
- ✅ Separate business/personal reports option

---

**Implementation:** 📋 Spec ready | **Effort:** 2 hours
