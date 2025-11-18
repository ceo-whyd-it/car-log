# Examples and Demo Scripts

This directory contains standalone demo scripts and examples for testing individual MCP servers and features.

## Trip Reconstructor Examples

### test_simple_matching.py
Core algorithm tests for the trip reconstruction matching logic. Demonstrates GPS-based template matching with various distance thresholds.

**Run:**
```bash
python examples/test_simple_matching.py
```

### test_demo_scenario.py
Demo scenario test: 820 km gap with Warehouse Run template. This demonstrates the core use case from the specification:
- Gap: 820 km (Nov 4-8, Bratislava to Bratislava)
- Template: Warehouse Run (410 km, round trip)
- Expected: 1× round trip = 820 km (100% coverage)

**Run:**
```bash
python examples/test_demo_scenario.py
```

### demo_confidence_scores.py
Demonstrates confidence score breakdown for template matching, showing how GPS and address scores are calculated and weighted.

**Run:**
```bash
python examples/demo_confidence_scores.py
```

### test_trip_reconstructor.py
Comprehensive tests for the trip reconstructor MCP server functionality.

**Run:**
```bash
python examples/test_trip_reconstructor.py
```

## Other Examples

### extract_exif_demo.py
Demonstrates EXIF metadata extraction from dashboard photos, including GPS coordinates and timestamps.

**Run:**
```bash
python examples/extract_exif_demo.py
```

### validation_demo.py
Demonstrates the 4 validation algorithms used for trip and checkpoint validation.

**Run:**
```bash
python examples/validation_demo.py
```

## Note

These are standalone demonstration scripts. For the complete test suite, use:
```bash
pytest tests/
```

The pytest test suite in `tests/` provides comprehensive unit and integration tests for all MCP servers.
