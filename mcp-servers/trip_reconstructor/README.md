# trip-reconstructor MCP Server

**Intelligent template-based trip reconstruction using hybrid GPS + address matching.**

## Overview

The trip-reconstructor server is the core intelligence layer for the Car Log application. It uses a sophisticated hybrid scoring algorithm to match gap periods between checkpoints to predefined trip templates, enabling automatic reconstruction of missing trip data.

## Architecture

### Hybrid Scoring Algorithm

**GPS Matching (70% weight):**
- Primary matching method using Haversine distance
- Thresholds:
  - < 100m → 100 points
  - 100-500m → 90 points
  - 500-2000m → 70 points
  - 2000-5000m → 40 points
  - > 5000m → 0 points

**Address Matching (30% weight):**
- Component-based matching (city, street, full address)
- Slovak character normalization (á→a, č→c, etc.)
- Levenshtein distance for similarity

**Bonuses (up to +20 points):**
- Distance bonus: +10 points if template distance within 10% of gap
- Day bonus: +10 points if gap day matches template typical_days

**Confidence Threshold:** 70 points (configurable)

## MCP Tools

### 1. match_templates

Match templates to a gap between checkpoints.

**Input:**
```json
{
  "gap_data": {
    "distance_km": 820,
    "start_checkpoint": { /* checkpoint data */ },
    "end_checkpoint": { /* checkpoint data */ }
  },
  "templates": [ /* array of template objects */ ],
  "confidence_threshold": 70
}
```

**Output:**
```json
{
  "success": true,
  "gap_distance_km": 820,
  "templates_evaluated": 5,
  "templates_matched": 2,
  "matched_templates": [
    {
      "template_id": "tmpl-1",
      "template_name": "Warehouse Run",
      "confidence_score": 90.6,
      "start_match": {
        "score": 95.6,
        "distance_meters": 0,
        "gps_score": 100,
        "address_score": 52
      },
      "end_match": {
        "score": 85.6,
        "distance_meters": 0,
        "gps_score": 100,
        "address_score": 52
      }
    }
  ],
  "reconstruction_proposal": {
    "has_proposal": true,
    "proposed_trips": [
      {
        "template_id": "tmpl-1",
        "template_name": "Warehouse Run",
        "confidence_score": 90.6,
        "num_trips": 1,
        "distance_km": 410,
        "is_round_trip": true,
        "total_distance_km": 820
      }
    ],
    "gap_distance_km": 820,
    "reconstructed_km": 820,
    "remaining_km": 0,
    "coverage_percent": 100,
    "reconstruction_quality": "excellent"
  }
}
```

### 2. calculate_template_completeness

Analyze template completeness and provide improvement suggestions.

**Input:**
```json
{
  "template": { /* template object */ }
}
```

**Output:**
```json
{
  "success": true,
  "is_valid": true,
  "completeness_percent": 100,
  "quality": "excellent",
  "mandatory_fields": {
    "total": 3,
    "present": 3,
    "missing": 0
  },
  "optional_fields": {
    "total": 9,
    "present": 9,
    "missing": 0,
    "present_list": ["from_address", "to_address", ...],
    "missing_list": []
  },
  "suggestions": [],
  "breakdown": {
    "has_gps": true,
    "has_addresses": true,
    "has_distance": true,
    "has_typical_days": true,
    "has_purpose": true
  }
}
```

## Configuration

Set environment variables in Claude Desktop config:

```json
{
  "mcpServers": {
    "trip-reconstructor": {
      "command": "python",
      "args": ["-m", "mcp_servers.trip_reconstructor"],
      "env": {
        "GPS_WEIGHT": "0.7",
        "ADDRESS_WEIGHT": "0.3",
        "CONFIDENCE_THRESHOLD": "70"
      }
    }
  }
}
```

## Installation

```bash
cd mcp-servers/trip_reconstructor
pip install -r requirements.txt
```

## Running as MCP Server

```bash
python -m mcp_servers.trip_reconstructor
```

## Testing

```bash
# Core matching tests
python examples/test_simple_matching.py

# Demo scenario (820 km gap with Warehouse Run)
python examples/test_demo_scenario.py

# Confidence score examples
python examples/demo_confidence_scores.py
```

## Demo Scenario Results

**Gap:** 820 km (Nov 4-8, Bratislava → Bratislava)
**Template:** Warehouse Run (410 km, round trip)

**Results:**
- Average confidence: **90.6%** (✓ above 70% threshold)
- Coverage: **100%** (1× round trip = 820 km)
- Quality: **EXCELLENT**

## File Structure

```
trip_reconstructor/
├── __init__.py               # Package metadata
├── __main__.py              # MCP server entry point (88 lines)
├── matching.py              # Core algorithms (368 lines)
├── requirements.txt         # Dependencies
├── tools/
│   ├── __init__.py
│   ├── match_templates.py                    # Template matching (288 lines)
│   └── calculate_template_completeness.py    # Completeness analysis (242 lines)
└── README.md                # This file

Total: ~1000 lines of production code
```

## Key Features

✅ **Stateless Design:** All data passed as parameters
✅ **GPS-First:** 70% weight on GPS coordinates
✅ **Slovak Support:** Proper character normalization
✅ **Confidence Scores:** Clear scoring breakdown
✅ **Smart Proposals:** Automatic trip reconstruction
✅ **Quality Analysis:** Template completeness feedback

## Dependencies

- `mcp>=0.1.0` - Model Context Protocol SDK
- Python 3.8+ standard library (math, unicodedata, re)

## Implementation Status

**Track C (C1-C6): COMPLETE** ✓

- [x] C1: Project setup (1 hour)
- [x] C2: GPS matching (3 hours)
- [x] C3: Address matching (2 hours)
- [x] C4: Hybrid scoring (2 hours)
- [x] C5: Proposal generation (2 hours)
- [x] C6: Completeness calculator (2 hours)

**Total:** 12 hours estimated → Completed

## Example Usage

```python
# Match templates to a gap
result = await match_templates({
    "gap_data": {
        "distance_km": 820,
        "start_checkpoint": {...},
        "end_checkpoint": {...}
    },
    "templates": [warehouse_template],
    "confidence_threshold": 70
})

if result['success']:
    for match in result['matched_templates']:
        print(f"{match['template_name']}: {match['confidence_score']}%")
```

## Performance

- Template matching: < 100ms per template
- Supports 100+ templates: < 2 seconds total
- Memory: Stateless, no caching required

## Error Handling

Standard error response format:

```json
{
  "success": false,
  "error": {
    "code": "GPS_REQUIRED",
    "message": "Both checkpoints must have GPS coordinates"
  }
}
```

**Error codes:**
- `VALIDATION_ERROR` - Invalid input
- `GPS_REQUIRED` - Missing GPS coordinates
- `EXECUTION_ERROR` - Runtime error

## Testing Results

```
✓ Haversine distance (Bratislava-Košice: ~313km)
✓ GPS scoring thresholds (5 levels)
✓ Slovak address normalization
✓ Address matching (Levenshtein)
✓ Hybrid scoring (70/30 split)
✓ Distance and day bonuses
✓ Demo scenario (100% coverage)
```

## License

Part of the Car Log project (MCP 1st Birthday Hackathon)
