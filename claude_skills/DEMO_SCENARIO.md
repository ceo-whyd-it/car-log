# Car Log Demo Scenario Script

**Project:** Slovak Tax-Compliant Mileage Logger
**Demo Duration:** 5 minutes
**Audience:** MCP 1st Birthday Hackathon judges
**Last Updated:** November 20, 2025

---

## Demo Overview

**Value Proposition:** 10x faster mileage tracking with conversational AI + Slovak tax compliance

**Demo Structure:**
1. **Problem Statement** (30 seconds)
2. **Architecture Overview** (60 seconds)
3. **Live Workflow Demo** (180 seconds)
4. **Slovak Compliance Highlight** (30 seconds)
5. **Results & Next Steps** (30 seconds)

**Key Messages:**
- MCP servers as backend architecture (not just connectors)
- GPS-first reconstruction (70/30 algorithm)
- Slovak VAT Act 2025 compliance
- 10x productivity improvement

---

## Part 1: Problem Statement (30 seconds)

**Script:**

> "Small businesses in Slovakia face a challenge: the Slovak VAT Act 2025 requires companies to track vehicle mileage with strict documentation - VIN numbers, driver names, precise trip timing, and fuel efficiency in L/100km format.
>
> Traditional mileage apps require 5-10 minutes per refuel for manual data entry. For a company vehicle refueling twice a week, that's **40+ hours per year wasted on paperwork**.
>
> Car Log solves this with conversational AI that turns photos into tax-compliant trip logs in under 30 seconds."

**Slides:**
- Slide 1: Problem
  - Slovak VAT Act 2025 requirements
  - Manual entry: 40+ hours/year
  - Error-prone compliance

---

## Part 2: Architecture Overview (60 seconds)

**Script:**

> "Car Log uses a unique architecture: **7 headless MCP servers as the actual backend**, not just API connectors.
>
> [Show architecture diagram]
>
> - **car-log-core**: CRUD operations for vehicles, checkpoints, trips, templates
> - **ekasa-api**: Slovak e-Kasa receipt system integration
> - **geo-routing**: OpenStreetMap geocoding and routing
> - **trip-reconstructor**: GPS-first matching algorithm (70% GPS, 30% address)
> - **validation**: 4 validation algorithms for tax compliance
> - **dashboard-ocr**: EXIF GPS extraction from photos
> - **report-generator**: Slovak VAT-compliant CSV reports
>
> All orchestrated through **6 Claude Desktop skills** that guide users conversationally.
>
> The innovation: MCP servers ARE the backend. No separate API layer, no database. Just stateless tools and file-based storage."

**Slides:**
- Slide 2: Architecture
  - 7 MCP servers diagram
  - Skills orchestration pattern
  - Key: MCP servers = backend

---

## Part 3: Live Workflow Demo (180 seconds)

### Demo Preparation

**Before Demo:**
1. Claude Desktop open with Car Log skills loaded
2. Sample receipt photos ready:
   - `receipt1_nov1.jpg` (QR code visible, 52.3L Diesel)
   - `dashboard1_nov1.jpg` (EXIF GPS: Bratislava)
   - `receipt2_nov8.jpg` (QR code visible, 20.5L Diesel)
   - `dashboard2_nov8.jpg` (EXIF GPS: Košice)
3. Data directory clean or mock data loaded
4. All MCP servers running (verify with `docker-compose ps`)

**Demo Data:**
- Vehicle: Ford Transit, BA-456CD, VIN: WBAXX01234ABC5678
- Checkpoint 1: Nov 1, 2025, 45000 km, Bratislava (48.1486°N, 17.1077°E)
- Checkpoint 2: Nov 8, 2025, 45820 km, Košice (48.7164°N, 21.2611°E)
- Gap: 820 km, 7 days
- Template: "Warehouse Run" (Bratislava ↔ Košice, 410 km, round trip)

### Demo Script

#### Step 1: Vehicle Setup (20 seconds)

**User:** "Add vehicle BA-456CD Ford Transit diesel VIN WBAXX01234ABC5678 with 125000 km odometer and 8.5 L per 100km average fuel efficiency"

**Claude:**
```
I'll register your vehicle. Let me validate the details...

✓ VIN validated (17 characters, no I/O/Q)
✓ License plate: BA-456CD (Slovak format)
✓ Fuel type: Diesel
✓ Average efficiency: 8.5 L/100km

Vehicle registered successfully!
```

**Voiceover:**
> "First, I register my company vehicle. Car Log validates the VIN format - no I, O, or Q characters allowed per Slovak VAT requirements. Notice it uses L/100km, the European standard, not km/L."

---

#### Step 2: First Checkpoint from Receipt (40 seconds)

**User:** [Paste `receipt1_nov1.jpg`]

**Claude:**
```
Scanning QR code... Found e-Kasa receipt!
Fetching from Slovak Financial Administration API (may take 30s)...

Receipt Details:
• Vendor: OMV Petrol Station
• Fuel: Diesel
• Quantity: 52.3 L
• Price: €76.85 (€1.47/L)
• VAT: 20% (€12.81)

Now paste the dashboard photo for GPS coordinates.
```

**User:** [Paste `dashboard1_nov1.jpg`]

**Claude:**
```
GPS extracted from photo EXIF:
• Location: 48.1486°N, 17.1077°E (Bratislava)
• Timestamp: Nov 1, 2025, 09:15

What was the odometer reading?
```

**User:** "45000 km"

**Claude:**
```
✅ Checkpoint created!
• Date: Nov 1, 2025, 09:15
• Location: Bratislava (GPS: 48.1486°N, 17.1077°E)
• Odometer: 45,000 km
• Fuel: 52.3 L Diesel

No gap detected yet (first checkpoint for this vehicle).
```

**Voiceover:**
> "I paste two photos: the receipt and my dashboard. Car Log scans the QR code, fetches the receipt from Slovakia's e-Kasa system - this is the official government receipt API - extracts GPS from the photo's EXIF data, and creates a checkpoint. Total time: 30 seconds."

---

#### Step 3: Second Checkpoint + Gap Detection (50 seconds)

**User:** [Paste `receipt2_nov8.jpg`]

**Claude:** [QR scan, e-Kasa fetch...]

**User:** [Paste `dashboard2_nov8.jpg`]

**Claude:**
```
GPS extracted: 48.7164°N, 21.2611°E (Košice)

What was the odometer reading?
```

**User:** "45820 km"

**Claude:**
```
✅ Checkpoint created!

⚠️  Gap detected!
• Between: Nov 1 (45,000 km) → Nov 8 (45,820 km)
• Distance: 820 km
• Duration: 7 days
• Both checkpoints have GPS coordinates

Would you like me to reconstruct trips for this gap using template matching?
```

**Voiceover:**
> "One week later, I refuel again. Car Log automatically detects an 820 km gap - that's distance I drove but haven't logged as trips. It offers to reconstruct these trips using my saved templates."

---

#### Step 4: Trip Reconstruction with GPS Matching (50 seconds)

**User:** "Yes, reconstruct trips"

**Claude:**
```
Analyzing 820 km gap between checkpoints...
Fetching templates... Found 3 templates.
Matching using GPS-first algorithm (70% GPS weight, 30% address)...

Match Results:

🎯 High Confidence Matches (≥70%):

1. Warehouse Run (Bratislava ↔ Košice) - 92% confidence
   • Distance: 410 km (round trip)
   • GPS Match: 98% (start within 45m, end within 38m)
   • Address Match: 85%
   • Day Match: ✓ Monday (template typical day)
   • Purpose: Business
   • Suggested: 2× (Mon Nov 1, Thu Nov 4)

Coverage: 100% (820 km / 820 km)

Accept these proposals?
```

**User:** "Yes"

**Claude:**
```
Creating 2 trips... Running validation...

✅ 2 trips created successfully!

Validation Results:
• Distance sum: 820 km (0% variance) ✓
• Fuel consumption: 72.8 L (+4.2% vs expected) ✓
• Efficiency: 8.9 L/100km (Diesel range 5-15) ✓
• Deviation from average: +4.7% (within ±20%) ✓

All Slovak VAT Act 2025 compliance fields populated:
✓ Driver name
✓ Trip start/end datetime (separate from refuel timing)
✓ Trip start/end location
✓ VIN reference
✓ Fuel efficiency (L/100km)
```

**Voiceover:**
> "Here's the magic: Car Log matched my 'Warehouse Run' template with 92% confidence because the GPS coordinates are within 45 meters of the template's start point. GPS matching gets 70% weight - addresses are just labels.
>
> It proposes 2 round trips totaling 820 km, covering the gap perfectly. I approve, and it creates the trips with all Slovak tax compliance fields: driver name, trip timing separate from refuel timing, locations, VIN, and L/100km efficiency.
>
> Four validation algorithms run automatically to catch errors."

---

#### Step 5: Report Generation (20 seconds)

**User:** "Generate November business report"

**Claude:**
```
Generating CSV report for November 2025...
Filtering for Business trips only...

Report: november-2025.csv

Summary:
• Total trips: 2
• Total distance: 820 km
• Total fuel: 72.8 L
• Average efficiency: 8.9 L/100km
• Total fuel cost: €106.56
• VAT amount: €17.76

Slovak VAT Act 2025 Compliance: ✅
All mandatory fields present:
✓ VIN (17 chars, no I/O/Q)
✓ Driver name
✓ Trip start/end datetime (separate from refuel)
✓ Trip start/end location
✓ Distance (km)
✓ Fuel consumption (L)
✓ Fuel efficiency (L/100km)
✓ Business purpose description

Report saved: ~/Documents/MileageLog/data/reports/2025-11/november-2025.csv
```

**Voiceover:**
> "Finally, I generate a CSV report for my accountant. It includes only business trips and has all fields required by Slovak tax law. Ready to submit."

---

## Part 4: Slovak Compliance Highlight (30 seconds)

**Script:**

> "Why does Slovak compliance matter?
>
> [Show compliance checklist]
>
> The Slovak VAT Act 2025 has strict requirements:
> - **VIN validation:** Must be 17 characters, no I, O, or Q (optical recognition prevention)
> - **Separate trip timing:** Trip start/end time is DIFFERENT from refuel time
> - **Driver identification:** Full name mandatory for tax deduction
> - **L/100km format:** European standard, not km/L
>
> Car Log validates all of this automatically. One mistake = rejected tax deduction.
>
> Traditional apps? You're manually checking 12 fields per trip. Car Log? Zero manual compliance checks."

**Slides:**
- Slide 3: Slovak Compliance
  - VAT Act 2025 requirements
  - Automatic validation
  - Zero manual compliance checks

---

## Part 5: Results & Next Steps (30 seconds)

**Script:**

> "Results:
>
> **Time Savings:**
> - Manual entry: 10 minutes per refuel
> - Car Log: 30 seconds per refuel
> - **20x faster** for this workflow
> - **40+ hours saved per year** per vehicle
>
> **Accuracy:**
> - GPS-first matching: 92% confidence
> - 4 validation algorithms catch errors
> - Slovak compliance: 100% automated
>
> **Architecture Innovation:**
> - 7 MCP servers as backend (not connectors)
> - Stateless tools, file-based storage
> - No database, no API layer
> - Claude Desktop orchestrates everything
>
> **Next Steps (Post-Hackathon):**
> - Dashboard OCR with Claude Vision (read odometer from photo)
> - Multi-vehicle fleet management
> - Gradio web UI for non-Claude users
> - ML-based anomaly detection
>
> **Try it:** GitHub repo linked in submission. Docker deployment ready.
>
> Thank you!"

**Slides:**
- Slide 4: Results
  - Time savings: 20x faster
  - Accuracy: 92% confidence
  - Architecture: MCP as backend
- Slide 5: Demo & GitHub
  - QR code to GitHub repo
  - "Try Car Log today"
  - Hackathon submission link

---

## Demo Timing Breakdown

| Section | Duration | Cumulative |
|---------|----------|------------|
| Problem Statement | 30s | 0:30 |
| Architecture Overview | 60s | 1:30 |
| Vehicle Setup | 20s | 1:50 |
| First Checkpoint | 40s | 2:30 |
| Second Checkpoint + Gap | 50s | 3:20 |
| Trip Reconstruction | 50s | 4:10 |
| Report Generation | 20s | 4:30 |
| Slovak Compliance | 30s | 5:00 |
| **Total** | **5:00** | **5:00** |

---

## Demo Preparation Checklist

### 1 Week Before Demo
- [ ] Record practice runs (3-5 times)
- [ ] Create all slides (5 slides)
- [ ] Prepare sample photos (receipt + dashboard with EXIF)
- [ ] Test all MCP servers in Claude Desktop
- [ ] Verify template matching works with sample data

### 1 Day Before Demo
- [ ] Final practice run (timed)
- [ ] Backup sample photos to multiple locations
- [ ] Test Docker deployment (fallback if Claude Desktop fails)
- [ ] Prepare fallback demo video (in case live demo crashes)
- [ ] Update GitHub README with demo instructions

### Day of Demo
- [ ] Start all MCP servers: `docker-compose up -d`
- [ ] Verify Claude Desktop connected to servers
- [ ] Load clean data (or demo dataset)
- [ ] Test photo paste functionality
- [ ] Have screenshot backup in case paste fails
- [ ] Set up screen recording (OBS or similar)

---

## Contingency Plans

### If e-Kasa API Times Out
**Fallback:**
> "The e-Kasa API is slow today. Let me show you with cached data..."
[Use pre-fetched receipt data]

### If GPS Extraction Fails
**Fallback:**
> "This photo doesn't have GPS EXIF. Car Log can fallback to address geocoding or manual GPS entry..."
[Enter GPS manually: 48.1486, 17.1077]

### If Template Matching Returns Low Confidence
**Fallback:**
> "No high-confidence matches. This is when Car Log would prompt you to create a new template or enter trips manually."
[Show template creation workflow instead]

### If Claude Desktop Crashes
**Fallback:**
> "Let me show you the architecture instead..."
[Switch to slides + architecture explanation + show test results from integration_checkpoint_day7.py]

---

## Slide Deck Outline

### Slide 1: Problem
- Title: "Slovak VAT Act 2025: The Mileage Logging Challenge"
- Content:
  - 40+ hours/year wasted on manual entry
  - Strict compliance requirements (VIN, timing, L/100km)
  - Error-prone manual validation
- Visual: Frustrated user with spreadsheet

### Slide 2: Solution - Architecture
- Title: "7 MCP Servers as Backend"
- Content:
  - car-log-core, ekasa-api, geo-routing, trip-reconstructor, validation, dashboard-ocr, report-generator
  - Skills orchestration pattern
  - Key innovation: MCP = backend (no API layer)
- Visual: Architecture diagram

### Slide 3: Live Demo
- Title: "10x Faster Workflow"
- Content:
  - Photo paste → Checkpoint (30s)
  - Gap detection → Template matching (92% confidence)
  - Report generation (Slovak compliant)
- Visual: Screenshots from demo

### Slide 4: Slovak Compliance
- Title: "Zero Manual Compliance Checks"
- Content:
  - VIN validation (no I/O/Q)
  - Separate trip/refuel timing
  - Driver identification
  - L/100km format
  - 4 validation algorithms
- Visual: Compliance checklist (all ✓)

### Slide 5: Try It
- Title: "Try Car Log Today"
- Content:
  - GitHub repo QR code
  - Docker deployment ready
  - 85% complete (backend done)
  - Post-hackathon: OCR, web UI, multi-vehicle
- Visual: QR code + GitHub logo

---

## Expected Questions & Answers

**Q: Why file-based storage instead of a database?**
A: For MVP, file-based storage is simpler, crash-safe (atomic writes), and human-readable. Post-hackathon, we can add PostgreSQL for multi-user scenarios, but for single-user or small teams, JSON files work great and are easier to debug.

**Q: What if the e-Kasa API is down?**
A: Car Log has fallback to manual entry. You can type in receipt data or use cached responses. For the demo, we use actual API calls to show real integration.

**Q: How accurate is GPS matching?**
A: With GPS coordinates, we achieve 90%+ confidence within 100 meters. Our demo template matches at 98% because the refuel station is 45 meters from the saved template point. Without GPS, accuracy drops to 60-70% (address-only matching).

**Q: Can this work in other countries?**
A: Yes! The MCP architecture is generic. Only the e-Kasa integration is Slovakia-specific. For other countries, swap out ekasa-api with their receipt system (e.g., German Finanzamt, US IRS). The core trip reconstruction algorithm is universal.

**Q: Why 70/30 GPS/address split?**
A: We tested various weights. GPS is more accurate (objective coordinates) while addresses can be ambiguous ("Košice" has 3 matches). 70/30 balances precision and user-friendliness. Users can adjust weights in config if needed.

**Q: How do you handle privacy (GPS tracking)?**
A: All data is stored locally in `~/Documents/MileageLog/data/`. No cloud sync, no external database. User has full control. For companies concerned about employee tracking, the manager can configure write-only access (employees log, manager reviews).

---

## Post-Demo Actions

### Immediately After Demo
- [ ] Upload demo video to YouTube
- [ ] Update GitHub README with video link
- [ ] Tweet demo highlights with hashtag #MCPHackathon
- [ ] Respond to judge questions on submission platform

### Next Steps (Post-Hackathon)
- [ ] Implement P1 features (OCR, web UI)
- [ ] Add PostgreSQL support for multi-user
- [ ] Create Homebrew formula for easy installation
- [ ] Write blog post about MCP architecture
- [ ] Submit to Product Hunt

---

**Last Updated:** November 20, 2025
**Demo Status:** Script complete, ready to record
**Practice Runs:** 0/3 (target: 3 runs before recording)
