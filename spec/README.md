# Specification Documents

This directory contains all specification and design documents for the Car Log project.

## Reading Order

### For Product Overview (Start Here)
1. **01-product-overview.md** - Product vision, target users, success metrics
2. **02-domain-model.md** - Core concepts (Checkpoint, Trip, Template, Vehicle)
3. **09-hackathon-presentation.md** - Demo script and presentation

### For Implementation (Developers)
1. **08-implementation-plan.md** - 13-day parallel development plan (4 tracks)
2. **07-mcp-api-specifications.md** - Complete API specifications for all 24 MCP tools
3. **06-mcp-architecture-v2.md** - MCP server architecture and design
4. **04-data-model.md** - JSON schemas and file structure
5. **IMPLEMENTATION_READY.md** - Quick start guide for developers

### For Understanding Algorithms
1. **03-trip-reconstruction.md** - Template matching algorithm (GPS 70% + Address 30%)
2. **TRIP_RECONSTRUCTOR_IMPLEMENTATION_SUMMARY.md** - Implementation details
3. **EXAMPLE_TEMPLATE_MATCHING.md** - Examples of template matching

### Implementation Guides
- **EKASA_IMPLEMENTATION_GUIDE.md** - Slovak e-Kasa API integration guide
- **IMPLEMENTATION_SUMMARY.md** - Overall implementation summary

### Optional (P1 Features)
- **05-claude-skills-dspy.md** - Dual interface architecture (Claude Skills + DSPy)
- **00-ENHANCEMENTS-FROM-MILESTONE-SPEC.md** - Future enhancements

## Document Status

All documents marked as ✅ Complete are ready for implementation.

## Key Concepts

### MCP-First Architecture
This project uses **MCP servers as the actual backend** (not just connectors). All business logic lives in 7 headless MCP servers that can be orchestrated by Claude Desktop or any MCP client.

### Slovak Tax Compliance
All specifications account for Slovak VAT Act 2025 requirements:
- VIN validation (17 chars, no I/O/Q)
- Driver name mandatory
- L/100km fuel efficiency format
- Separate trip timing from refuel timing

### GPS-First Philosophy
GPS coordinates are the source of truth (70% weight), addresses are optional labels (30% weight). This enables robust template matching even with address variations.

## Navigation

To return to project root documentation:
- [../README.md](../README.md) - Main project README
- [../CLAUDE.md](../CLAUDE.md) - Instructions for Claude Code
- [../TASKS.md](../TASKS.md) - Implementation task tracking
- [../CLAUDE_DESKTOP_SETUP.md](../CLAUDE_DESKTOP_SETUP.md) - Setup guide
