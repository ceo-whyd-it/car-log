# car-log-core MCP Server

CRUD operations for Car Log's file-based storage system.

## Overview

This MCP server provides the foundational data layer for the Car Log project, implementing:
- Vehicle management with Slovak tax compliance
- Checkpoint tracking with automatic gap detection
- Trip template management (GPS-first)
- Atomic file writes for crash safety

## Installation

```bash
cd mcp-servers/car_log_core
pip install -r requirements.txt
```

## Configuration

### Environment Variables

```bash
# Data storage path (default: ~/Documents/MileageLog/data)
export DATA_PATH="~/Documents/MileageLog/data"
```

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "car-log-core": {
      "command": "python",
      "args": ["-m", "car_log_core"],
      "cwd": "/home/user/car-log/mcp-servers",
      "env": {
        "DATA_PATH": "~/Documents/MileageLog/data"
      }
    }
  }
}
```

## Available Tools

### Vehicle Tools

#### `create_vehicle`
Create new vehicle with Slovak VIN validation.

**Required Fields:**
- `name` - Vehicle name
- `license_plate` - Slovak format XX-123XX
- `vin` - 17 characters, no I/O/Q
- `fuel_type` - Diesel, Gasoline, LPG, Hybrid, Electric
- `initial_odometer_km` - Starting odometer reading

**Example:**
```json
{
  "name": "Ford Transit Delivery Van",
  "license_plate": "BA-456CD",
  "vin": "WBAXX01234ABC5678",
  "make": "Ford",
  "model": "Transit",
  "year": 2022,
  "fuel_type": "Diesel",
  "initial_odometer_km": 15000
}
```

#### `get_vehicle`
Retrieve vehicle by ID.

#### `list_vehicles`
List all vehicles with optional filters.

**Filters:**
- `active_only` (default: true)
- `fuel_type`

#### `update_vehicle`
Update vehicle details.

**Updatable Fields:**
- `name`
- `average_efficiency_l_per_100km`
- `active`

### Checkpoint Tools

#### `create_checkpoint`
Create checkpoint from refuel or manual entry.

**Required Fields:**
- `vehicle_id`
- `checkpoint_type` - refuel, manual, month_end
- `datetime` - ISO 8601 format
- `odometer_km`

**Optional Fields:**
- `location_coords` - {lat, lng}
- `location_address`
- `receipt_id`
- `fuel_liters`
- `fuel_cost_eur`

**Example:**
```json
{
  "vehicle_id": "550e8400-e29b-41d4-a716-446655440000",
  "checkpoint_type": "refuel",
  "datetime": "2025-11-15T08:45:00Z",
  "odometer_km": 15200,
  "location_coords": {
    "lat": 48.1486,
    "lng": 17.1077
  },
  "location_address": "Shell Bratislava West",
  "receipt_id": "ekasa-abc123xyz",
  "fuel_liters": 50.5,
  "fuel_cost_eur": 72.50
}
```

**Gap Detection:**
Automatically detects gaps ≥50km and suggests reconstruction for ≥100km.

#### `get_checkpoint`
Retrieve checkpoint by ID.

#### `list_checkpoints`
List checkpoints with filters.

**Required:**
- `vehicle_id`

**Optional Filters:**
- `start_date` (YYYY-MM-DD)
- `end_date` (YYYY-MM-DD)
- `checkpoint_type`
- `limit` (default: 50, max: 100)

### Gap Detection

#### `detect_gap`
Analyze distance/time gap between two checkpoints.

**Returns:**
- Distance (km)
- Time (days, hours)
- GPS availability
- Average km/day
- Reconstruction recommendation

**Example:**
```json
{
  "start_checkpoint_id": "660e8400-...",
  "end_checkpoint_id": "660e8401-..."
}
```

### Template Tools

#### `create_template`
Create trip template (GPS mandatory, addresses optional).

**Required Fields:**
- `name`
- `from_coords` - {lat, lng}
- `to_coords` - {lat, lng}

**Optional Fields:**
- `from_address`
- `to_address`
- `distance_km`
- `is_round_trip`
- `typical_days` - ["Monday", "Thursday"]
- `purpose` - business, personal
- `business_description`
- `notes`

**Example:**
```json
{
  "name": "Warehouse Run",
  "from_coords": {"lat": 48.1486, "lng": 17.1077},
  "to_coords": {"lat": 48.7164, "lng": 21.2611},
  "from_address": "Main Office, Bratislava",
  "to_address": "Warehouse, Košice",
  "distance_km": 410,
  "is_round_trip": true,
  "typical_days": ["Monday", "Thursday"],
  "purpose": "business",
  "business_description": "Warehouse pickup"
}
```

#### `list_templates`
List all templates.

**Optional Filters:**
- `purpose` - business, personal

## Data Storage

### File Structure

```
~/Documents/MileageLog/data/
├── vehicles/
│   └── {vehicle-id}.json
├── checkpoints/
│   └── {YYYY-MM}/
│       └── {checkpoint-id}.json
├── trips/
│   └── {YYYY-MM}/
│       └── {trip-id}.json
└── typical-destinations.json
```

### Atomic Write Pattern

All writes use atomic pattern:
1. Write to temp file
2. Atomic rename (OS-level operation)
3. Result: Either complete success or complete failure

**No partial/corrupted files even if process crashes.**

## Slovak Tax Compliance

### VIN Validation
- Must be exactly 17 characters
- Only A-Z and 0-9 (excluding I, O, Q)
- Pattern: `^[A-HJ-NPR-Z0-9]{17}$`

### License Plate
- Slovak format: XX-123XX
- Example: BA-456CD
- Pattern: `^[A-Z]{2}-[0-9]{3}[A-Z]{2}$`

### Fuel Efficiency
- **Always use L/100km** (European standard)
- Never km/L
- Range: 3.0 - 25.0 L/100km

## Error Codes

- `VALIDATION_ERROR` - Invalid input data
- `NOT_FOUND` - Resource doesn't exist
- `DUPLICATE` - Resource already exists
- `EXECUTION_ERROR` - Server error

## Testing

```bash
# Run unit tests
python tests/test_car_log_core.py
```

**Expected Output:**
```
============================================================
✓ ALL TESTS PASSED!
============================================================
```

## Development

### Adding New Tools

1. Create tool file in `tools/`
2. Define `INPUT_SCHEMA`
3. Implement `async def execute(arguments)`
4. Import in `tools/__init__.py`
5. Register in `__main__.py`

### Code Style
- Type hints for function parameters
- Docstrings for all public functions
- Error messages must be human-readable
- Follow atomic write pattern for all file operations

## Performance

### Expected Performance
- Vehicle operations: ~5-10ms
- Checkpoint operations: ~10-20ms
- List operations: ~50-100ms (for 30 items)

### Scalability
- Optimized for: 1-5 vehicles, 20-50 trips/month
- Monthly folders prevent large directory listings
- No database required for MVP scope

## Dependencies

- `mcp` - MCP server framework
- `python-dateutil` - Date parsing

## License

Part of the Car Log project (MCP 1st Birthday Hackathon).

## Support

For issues or questions, see main project documentation.
