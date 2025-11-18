# Claude Desktop Setup Guide

This guide explains how to configure Car Log's 6 MCP servers in Claude Desktop.

## Prerequisites

1. **Python 3.11+** installed
2. **Node.js 18+** installed (for geo-routing server)
3. **Claude Desktop** installed
4. **Anthropic API Key** (optional - only needed for dashboard OCR P1 feature)

## Installation Steps

### 1. Install Python Dependencies

```bash
# From project root
cd mcp-servers/car_log_core && pip install -r requirements.txt
cd ../trip_reconstructor && pip install -r requirements.txt
cd ../validation && pip install -r requirements.txt
cd ../ekasa_api && pip install -r requirements.txt
cd ../dashboard_ocr && pip install -r requirements.txt
```

### 2. Install Node.js Dependencies

```bash
# From project root
cd mcp-servers/geo-routing
npm install
```

### 3. Create Data Directories

```bash
mkdir -p ~/Documents/MileageLog/data/{vehicles,checkpoints,trips,templates,reports}
```

### 4. Configure Claude Desktop

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

Copy the contents of `claude_desktop_config.json` from this repository to your Claude Desktop config file.

**Important:** Update the paths to match your system:
- Change `python` to absolute path if needed (e.g., `/usr/bin/python3.11`)
- Change `node` to absolute path if needed
- Update `mcp-servers/` paths to absolute paths (e.g., `/home/user/car-log/mcp-servers/...`)

### 5. Set Environment Variables (Optional)

If you want to use dashboard OCR (P1 feature), set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Or update the `claude_desktop_config.json` to use the actual key instead of `${ANTHROPIC_API_KEY}`.

### 6. Restart Claude Desktop

After updating the config file, restart Claude Desktop to load the MCP servers.

## Verification

After restarting Claude Desktop, you should see all 6 servers loaded:

1. **car-log-core** - Vehicle, checkpoint, template CRUD operations
2. **trip-reconstructor** - Template matching and trip reconstruction
3. **validation** - Data validation with Slovak compliance
4. **ekasa-api** - Slovak receipt processing (QR scanning, API fetching)
5. **geo-routing** - OpenStreetMap geocoding and routing
6. **dashboard-ocr** - EXIF extraction (+ OCR with API key)

### Check Server Status

In Claude Desktop, ask Claude:
> "What MCP tools do you have available?"

You should see approximately 21 P0 tools listed:

**car-log-core (8 tools):**
- create_vehicle, get_vehicle, list_vehicles, update_vehicle
- create_checkpoint, get_checkpoint, list_checkpoints
- detect_gap

**trip-reconstructor (2 tools):**
- match_templates
- calculate_template_completeness

**validation (4 tools):**
- validate_checkpoint_pair
- validate_trip
- check_efficiency
- check_deviation_from_average

**ekasa-api (2 tools):**
- scan_qr_code
- fetch_receipt_data

**geo-routing (3 tools):**
- geocode_address
- reverse_geocode
- calculate_route

**dashboard-ocr (2 tools):**
- extract_metadata
- read_odometer (P1 - requires API key)

## Troubleshooting

### Server Not Loading

1. **Check logs:** Claude Desktop → Settings → Developer → View Logs
2. **Verify paths:** Ensure all paths in config are absolute and correct
3. **Check dependencies:** Ensure all Python/Node packages are installed
4. **Restart:** Fully quit and restart Claude Desktop

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Ensure you're in the project root
cd /path/to/car-log

# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/car-log/mcp-servers"
```

Or update the config to use absolute paths:

```json
{
  "command": "python",
  "args": ["-m", "car_log_core"],
  "cwd": "/absolute/path/to/car-log/mcp-servers"
}
```

### Node Server Not Starting

```bash
# Test geo-routing server manually
cd mcp-servers/geo-routing
node index.js --version
```

If it fails, check `npm install` completed successfully.

### Timeout Errors (e-Kasa API)

The e-Kasa API can take 5-30 seconds to respond. The server is configured with a 60-second timeout. If you see timeout errors:

1. Check your internet connection
2. Verify the receipt ID is valid
3. The Slovak government API may be temporarily slow - retry after a few minutes

## Usage Examples

### Create a Vehicle

```
Create a new vehicle:
- Name: Ford Transit
- License Plate: BA-456CD
- VIN: WBAXX01234ABC5678 (17 characters, no I/O/Q)
- Fuel Type: Diesel
- Initial Odometer: 45000 km
```

### Process a Receipt

```
I have a fuel receipt. Let me paste the QR code or receipt ID.
[Receipt ID]: abc123xyz

Please fetch the receipt data and create a checkpoint.
```

### Detect Gap and Reconstruct

```
Detect gaps between my checkpoints and suggest templates to fill them.
```

## Configuration Options

### car-log-core

- `DATA_PATH`: Where to store JSON files (default: `~/Documents/MileageLog/data`)
- `USE_ATOMIC_WRITES`: Enable crash-safe writes (default: `true`)

### trip-reconstructor

- `GPS_WEIGHT`: Weight for GPS matching (default: `0.7` = 70%)
- `ADDRESS_WEIGHT`: Weight for address matching (default: `0.3` = 30%)
- `CONFIDENCE_THRESHOLD`: Minimum confidence to suggest template (default: `70`)

### validation

- `DISTANCE_VARIANCE_PERCENT`: Allowed variance for distance sum (default: `10` = ±10%)
- `CONSUMPTION_VARIANCE_PERCENT`: Allowed variance for fuel consumption (default: `15` = ±15%)
- `DEVIATION_THRESHOLD_PERCENT`: Threshold for deviation warning (default: `20` = ±20%)
- `DIESEL_MIN_L_PER_100KM`: Minimum reasonable diesel efficiency (default: `5`)
- `DIESEL_MAX_L_PER_100KM`: Maximum reasonable diesel efficiency (default: `15`)
- `GASOLINE_MIN_L_PER_100KM`: Minimum reasonable gasoline efficiency (default: `6`)
- `GASOLINE_MAX_L_PER_100KM`: Maximum reasonable gasoline efficiency (default: `20`)
- `LPG_MIN_L_PER_100KM`: Minimum reasonable LPG efficiency (default: `8`)
- `LPG_MAX_L_PER_100KM`: Maximum reasonable LPG efficiency (default: `25`)

### ekasa-api

- `EKASA_API_URL`: Slovak e-Kasa API endpoint (default: `https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt`)
- `MCP_TIMEOUT_SECONDS`: Request timeout (default: `60`)

### geo-routing

- `OSRM_BASE_URL`: OpenStreetMap routing service (default: `https://router.project-osrm.org`)
- `NOMINATIM_BASE_URL`: OpenStreetMap geocoding service (default: `https://nominatim.openstreetmap.org`)
- `CACHE_TTL_HOURS`: Cache duration for geocoding results (default: `24`)

### dashboard-ocr

- `ANTHROPIC_API_KEY`: API key for Claude Vision OCR (required for P1 OCR feature)

## Next Steps

Once all servers are loaded successfully:

1. Test the complete workflow (see `spec/09-hackathon-presentation.md`)
2. Create your first vehicle and checkpoints
3. Set up templates for your common routes
4. Start logging trips!

## Support

For issues or questions:
1. Check CLAUDE.md for implementation details
2. Review TASKS.md for known issues
3. Run integration tests: `python tests/integration_checkpoint_day7.py`
