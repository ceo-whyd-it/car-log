# Product Overview: Car Log

**Version:** 2.0
**Date:** 2025-11-17
**Status:** Draft - In Discussion
**Previous Version:** FR_for_review.md (archived)

---

## Executive Summary

Car Log is an AI-assisted mileage and fuel expense tracking application designed for small businesses in Europe. The system enables users to reconstruct complete trip logs from minimal checkpoint data (odometer photos + fuel receipts), significantly reducing manual data entry while maintaining tax compliance.

### Key Innovation

**Trip Reconstruction from Checkpoints**: Instead of logging every trip manually, users create checkpoints (odometer readings + optional receipts) and the system intelligently reconstructs individual trips using:
- User-specified trip memories
- Recurring trip templates
- Geo-routing analysis (when GPS data available)

---

## Problem Statement

Small business owners with company vehicles face:

1. **Time-consuming manual logging** - Recording every trip is tedious
2. **Incomplete records** - Drivers forget to log trips, causing gaps
3. **Tax compliance burden** - Authorities require detailed mileage logs
4. **Receipt management** - Paper receipts get lost or damaged
5. **Multi-country complexity** - European businesses operate across borders

---

## Solution

### Primary Interface (P0)
**Claude Desktop** - Conversational AI interface
- Natural language interaction for all operations
- User pastes photos (dashboard, receipts) directly into conversation
- AI guides reconstruction process interactively
- No forms, no complex UI

### Core Capabilities (P0)
1. **Checkpoint Creation** - Capture vehicle state at fuel stops
2. **Receipt Processing** - Extract data from e-Kasa QR codes (Slovakia)
3. **Trip Reconstruction** - Fill gaps intelligently using templates + geo-routing
4. **Trip Templates** - Define recurring routes for quick reconstruction
5. **Report Generation** - Export CSV/PDF for tax purposes

### Optional Enhancements (P1)
- Gradio web UI for visual dashboards
- Claude Vision OCR for automatic odometer reading extraction
- PDF report generation
- Multi-vehicle fleet management

---

## Target Users

### Primary: Small Business Owners
- **Size:** 1-5 company vehicles
- **Geography:** European Union (starting with Slovakia)
- **Tech literacy:** Medium (comfortable with smartphones)
- **Main goal:** Tax compliance with minimal effort

### Secondary: Drivers
- Log checkpoints at fuel stops
- Minimal training required
- Works offline (processes when online)

### Tertiary: Accountants
- Receive structured reports (CSV/PDF)
- Tax-compliant data format
- Easy reconciliation with bank statements

---

## Core Principles

1. **Simplicity First** - Reduce data entry to absolute minimum
2. **Reconstruction over Logging** - Fill gaps intelligently, don't force manual entry
3. **Evidence-Based** - All trips backed by checkpoint photos/receipts
4. **European-Friendly** - Metric units, EUR, multi-country support
5. **Tax-Compliant** - Meet Slovak/EU tax authority requirements
6. **Conversational UX** - AI guides users through complex workflows
7. **Privacy-Conscious** - Local-first data, optional cloud sync

---

## Scope

### In Scope (P0 - MVP)

**Geographic:**
- ✅ Universal (all European countries)
- ✅ Slovak e-Kasa integration (country-specific)

**Features:**
- ✅ Checkpoint creation (manual + photo)
- ✅ Receipt processing (QR extraction for Slovakia)
- ✅ Trip reconstruction (manual + template-based)
- ✅ Trip templates (user-defined recurring routes)
- ✅ Geo-routing (OpenStreetMap integration)
- ✅ EXIF extraction (timestamp + GPS from photos)
- ✅ Basic reports (CSV export)
- ✅ 1-3 vehicles per user

**Interface:**
- ✅ Claude Desktop (conversational)
- ✅ MCP server architecture

### In Scope (P1 - Nice to Have)

- ⏳ Claude Vision OCR (automatic odometer reading)
- ⏳ PDF report generation
- ⏳ Gradio web UI
- ⏳ Multi-vehicle dashboard
- ⏳ Template auto-suggestion from history

### Out of Scope (P2 - Future)

- ❌ User authentication / multi-user
- ❌ Cloud synchronization
- ❌ Mobile app (native iOS/Android)
- ❌ Real-time GPS tracking
- ❌ Integration with accounting software (QuickBooks, etc.)
- ❌ Automatic trip classification (ML-based)
- ❌ Fuel price comparison
- ❌ Vehicle maintenance tracking

---

## Success Metrics

### User Success
- **Time savings:** 80% reduction in manual logging time
- **Completeness:** 95%+ of trips reconstructed from checkpoints
- **Accuracy:** Tax-compliant reports accepted by authorities

### Technical Success
- **Reconstruction accuracy:** 90%+ distance matching
- **Receipt processing:** 95%+ QR code extraction success
- **Response time:** <2s for checkpoint creation
- **Geo-routing:** 98%+ route calculation success

### Business Success
- **User retention:** 70%+ monthly active usage
- **Recommendation:** 8+ NPS score
- **Tax audit readiness:** 100% compliant reports

---

## Competitive Positioning

### vs. Manual Spreadsheets
- ✅ 80% faster data entry
- ✅ Automatic distance calculation
- ✅ Receipt photo storage
- ✅ Tax-compliant formatting

### vs. Traditional Mileage Apps (MileIQ, Everlance)
- ✅ **Trip reconstruction** (don't need to log every trip)
- ✅ **Conversational interface** (no forms)
- ✅ **European focus** (e-Kasa, metric, EUR)
- ❌ No GPS tracking (privacy-first)
- ❌ No mobile app (desktop-first)

### vs. Fleet Management Software (Verizon Connect, Samsara)
- ✅ **Much simpler** (for small businesses)
- ✅ **Lower cost** (no hardware required)
- ✅ **Privacy-focused** (no real-time tracking)
- ❌ Not suitable for large fleets (5+ vehicles)
- ❌ No dispatch/routing optimization

---

## Key Terminology

| Term | Definition |
|------|------------|
| **Checkpoint** | Point-in-time capture of vehicle state (odometer + optional receipt) |
| **Trip** | Calculated journey between two checkpoints |
| **Trip Template** | User-defined recurring route (e.g., "Office to Warehouse") |
| **Reconstruction** | Process of filling checkpoint gaps with trip data |
| **e-Kasa** | Slovak electronic cash register system (receipt API) |
| **EXIF** | Photo metadata (timestamp, GPS location) |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ USER INTERFACE                                          │
│ • Claude Desktop (P0 - Conversational)                 │
│ • Gradio UI (P1 - Visual Dashboard)                    │
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│ MCP SERVER LAYER                                        │
│ • car-log-core (business logic + file storage)        │
│ • ekasa-api (receipt processing)                       │
│ • geo-routing (OpenStreetMap)                          │
│ • dashboard-ocr (photo OCR + EXIF)                     │
│ • validation (data integrity checks)                   │
│ • report-generator (PDF/CSV) [P1]                      │
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│ DATA LAYER                                              │
│ • JSON file-based storage (local-first)                │
│ • Photo storage (local filesystem)                     │
│ • Generated reports (CSV/PDF)                          │
│ Note: Database migration planned for P2 (10,000+ trips)│
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│ EXTERNAL INTEGRATIONS                                   │
│ • Slovak e-Kasa API (receipt data)                     │
│ • OpenStreetMap/OSRM (routing)                         │
└─────────────────────────────────────────────────────────┘
```

---

## Related Documents

- [02-domain-model.md](./02-domain-model.md) - Core concepts and terminology
- [03-trip-reconstruction.md](./03-trip-reconstruction.md) - Algorithm specification
- [04-data-model.md](./04-data-model.md) - JSON file schemas
- [05-claude-skills-dspy.md](./05-claude-skills-dspy.md) - Dual interface architecture
- [06-mcp-architecture-v2.md](./06-mcp-architecture-v2.md) - MCP server architecture
- [07-mcp-api-specifications.md](./07-mcp-api-specifications.md) - Complete API tool definitions

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-17 | 2.0 | Complete restructure: Checkpoint-centric model, trip reconstruction focus |
| 2025-11-08 | 1.0 | Initial functional requirements (FR_for_review.md) |
