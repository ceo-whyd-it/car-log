# Claude Desktop Skills Installation Guide

This guide explains how to install and configure the Car Log skills for Claude Desktop.

## Prerequisites

- Claude Desktop installed (macOS/Windows/Linux)
- MCP servers configured and running (see main README.md)
- Car Log data directory set up: `~/Documents/MileageLog/data/`

## Installation Steps

### Step 1: Locate Claude Desktop Configuration

**macOS:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```bash
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

### Step 2: Configure MCP Servers

Ensure all required MCP servers are configured in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "car-log-core": {
      "command": "python",
      "args": ["-m", "mcp_servers.car_log_core"],
      "env": {
        "DATA_PATH": "~/Documents/MileageLog/data",
        "USE_ATOMIC_WRITES": "true"
      }
    },
    "ekasa-api": {
      "command": "python",
      "args": ["-m", "mcp_servers.ekasa_api"],
      "env": {
        "MCP_TIMEOUT_SECONDS": "60"
      }
    },
    "dashboard-ocr": {
      "command": "python",
      "args": ["-m", "mcp_servers.dashboard_ocr"],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here"
      }
    },
    "trip-reconstructor": {
      "command": "python",
      "args": ["-m", "mcp_servers.trip_reconstructor"],
      "env": {
        "GPS_WEIGHT": "0.7",
        "ADDRESS_WEIGHT": "0.3"
      }
    },
    "geo-routing": {
      "command": "node",
      "args": ["mcp-servers/geo-routing/index.js"]
    },
    "validation": {
      "command": "python",
      "args": ["-m", "mcp_servers.validation"]
    },
    "report-generator": {
      "command": "python",
      "args": ["-m", "mcp_servers.report_generator"]
    }
  }
}
```

### Step 3: Add Skills to Claude Desktop

**Option A: Custom Instructions (Recommended)**

1. Open Claude Desktop
2. Go to Settings > Custom Instructions
3. Add the following skills configuration:

```markdown
# Car Log Skills

You are an expert at Slovak tax-compliant vehicle mileage logging. You have access to 7 MCP servers that handle:
- Vehicle and checkpoint CRUD (car-log-core)
- Trip reconstruction with GPS-first matching (trip-reconstructor)
- Slovak e-Kasa receipt processing (ekasa-api)
- Dashboard photo OCR with EXIF GPS (dashboard-ocr)
- Geocoding and routing (geo-routing)
- Validation algorithms (validation)
- Report generation (report-generator)

## Skill 1: Vehicle Setup

**Trigger words:** "add vehicle", "register car", "new vehicle", license plate patterns (BA-*), "company car"

**Workflow:**
1. Collect vehicle details conversationally
2. Validate VIN (17 chars, no I/O/Q) - MANDATORY for Slovak VAT Act 2025
3. Validate license plate (XX-123XX format)
4. Use L/100km format (not km/L)
5. Create vehicle via car-log-core.create_vehicle
6. Confirm with next steps

**Error handling:**
- Duplicate license plates → show existing vehicle
- Invalid VIN → explain I/O/Q rule, suggest corrections
- Unrealistic odometer → flag and confirm

## Skill 2: Checkpoint from Receipt Photo

**Trigger words:** User pastes image, "refuel", "fuel receipt", "gas station"

**Workflow:**
1. Detect image paste
2. Scan QR code (multi-scale: 1x, 2x, 3x)
3. Fetch e-Kasa receipt (timeout: 60s, show progress)
4. Request dashboard photo
5. Extract GPS + odometer from EXIF/OCR
6. Create checkpoint via car-log-core.create_checkpoint
7. Automatic gap detection
8. Trigger trip reconstruction if gap > 100km

**Progress indicators:**
- "Scanning QR code... trying 2x scale..."
- "Fetching from e-Kasa API (may take 30s)..."
- "Extracting GPS and odometer..."

**Error handling:**
- No QR → manual receipt ID entry
- Timeout → fallback to manual entry
- No GPS → suggest retake or manual location
- Low OCR confidence → confirm odometer reading

## Skill 3: Trip Reconstruction

**Trigger words:** Automatic after gap detection, "reconstruct trips", "fill gap"

**Workflow:**
1. Analyze gap (car-log-core.analyze_gap)
2. Fetch templates (car-log-core.list_templates)
3. Run GPS-first matching (70% GPS, 30% address)
4. Present high-confidence proposals (>= 70%)
5. User approval
6. Batch trip creation (car-log-core.create_trips_batch)
7. Automatic validation (4 algorithms)
8. Show results with validation status

**Confidence tiers:**
- 90-100%: High confidence, recommend acceptance
- 70-89%: Medium confidence, show warnings
- <70%: No automatic proposal, offer manual entry

**User communication:**
- Always explain confidence breakdown
- Show GPS match distance ("within 50m")
- Explain bonuses (day-of-week, distance match)
- Clear validation results

## Slovak Compliance Rules

**ALWAYS enforce:**
- VIN: 17 characters, no I/O/Q (ISO 3779)
- License plate: XX-123XX format (e.g., BA-456CD)
- Fuel efficiency: L/100km (NEVER km/L)
- Driver name: Required for all trips
- Receipt data: Price excl/incl VAT, VAT rate

**Validation thresholds:**
- Distance sum: ±10%
- Fuel consumption: ±15%
- Efficiency range: Diesel 5-15 L/100km, Gasoline 6-20 L/100km

## GPS-First Philosophy

**Why GPS matters:**
- 70% weight in template matching
- 100m accuracy vs. ambiguous addresses
- Enables high-confidence reconstruction (90%+)

**Always:**
- Extract EXIF GPS from photos
- Store coordinates as source of truth
- Use addresses as labels only
```

**Option B: Skills Files (Alternative)**

If your Claude Desktop version supports custom skills files:

1. Create a `skills/` directory in Claude Desktop config folder
2. Copy skill files:
   ```bash
   cp claude_skills/01-vehicle-setup.md ~/Library/Application\ Support/Claude/skills/
   cp claude_skills/02-checkpoint-from-receipt.md ~/Library/Application\ Support/Claude/skills/
   cp claude_skills/03-trip-reconstruction.md ~/Library/Application\ Support/Claude/skills/
   ```
3. Restart Claude Desktop

### Step 4: Verify MCP Server Availability

1. Open Claude Desktop
2. Start a new conversation
3. Ask: "What MCP tools do you have access to?"
4. Verify you see all 7 servers:
   - car-log-core (8 tools)
   - ekasa-api (2 tools)
   - dashboard-ocr (1 tool)
   - trip-reconstructor (1 tool)
   - geo-routing (3 tools)
   - validation (4 tools)
   - report-generator (3 tools)

Expected total: **22-28 tools** depending on implementation status.

### Step 5: Test Each Skill Individually

See `TESTING_F1-F3.md` for comprehensive test scenarios.

**Quick smoke tests:**

**Skill 1 (Vehicle Setup):**
```
You: "Add my Ford Transit BA-789XY diesel 125000km VIN WVWZZZ3CZDP123456"
Expected: Vehicle created successfully
```

**Skill 2 (Checkpoint from Receipt):**
```
You: [paste receipt photo]
Expected: QR scan → e-Kasa fetch → request dashboard photo
```

**Skill 3 (Trip Reconstruction):**
```
You: "Reconstruct trips from November 1 to November 8"
Expected: Gap analysis → template matching → proposals
```

## Troubleshooting

### MCP Servers Not Discovered

**Problem:** Claude says "I don't have access to MCP tools"

**Solution:**
1. Check `claude_desktop_config.json` syntax (valid JSON)
2. Restart Claude Desktop
3. Check server logs in `~/Library/Logs/Claude/`
4. Verify Python/Node.js paths are correct

### e-Kasa API Timeouts

**Problem:** Receipt fetching always times out

**Solution:**
1. Increase timeout: `"MCP_TIMEOUT_SECONDS": "90"`
2. Check internet connection
3. Verify e-Kasa API is accessible: https://ekasa.financnasprava.sk
4. Test manually with curl:
   ```bash
   curl "https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/RECEIPT_ID"
   ```

### Dashboard OCR Not Working

**Problem:** No GPS or odometer extracted from photos

**Solution:**
1. Verify `ANTHROPIC_API_KEY` is set
2. Check API key has Claude Vision access
3. Ensure photos are actual camera photos (not screenshots)
4. Verify EXIF data exists:
   ```bash
   exiftool dashboard_photo.jpg | grep GPS
   ```

### GPS Coordinates Missing

**Problem:** Checkpoints created without GPS

**Solution:**
1. Use camera app (not screenshot app)
2. Enable location services on phone
3. Check photo metadata:
   ```bash
   exiftool photo.jpg | grep GPS
   ```
4. Manually enter coordinates if needed

### Trip Matching Low Confidence

**Problem:** All template matches below 70%

**Solution:**
1. Check template GPS coordinates are accurate
2. Verify checkpoint GPS coordinates exist
3. Create new template from current gap
4. Use manual trip entry as fallback

## Configuration Tips

### Optimizing for Speed

```json
{
  "ekasa-api": {
    "env": {
      "CACHE_RECEIPTS": "true",
      "CACHE_TTL_HOURS": "24"
    }
  },
  "geo-routing": {
    "env": {
      "CACHE_ROUTES": "true",
      "CACHE_TTL_HOURS": "24"
    }
  }
}
```

### Optimizing for Accuracy

```json
{
  "trip-reconstructor": {
    "env": {
      "GPS_WEIGHT": "0.8",
      "ADDRESS_WEIGHT": "0.2",
      "MIN_CONFIDENCE": "0.75"
    }
  }
}
```

### Development Mode (Verbose Logging)

```json
{
  "mcpServers": {
    "car-log-core": {
      "env": {
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE": "~/car-log-debug.log"
      }
    }
  }
}
```

## Data Directory Structure

Verify the data directory exists and has correct permissions:

```bash
# Create directories
mkdir -p ~/Documents/MileageLog/data/{vehicles,checkpoints,trips,templates,reports}

# Set permissions (macOS/Linux)
chmod 755 ~/Documents/MileageLog
chmod 755 ~/Documents/MileageLog/data

# Verify
ls -la ~/Documents/MileageLog/data/
```

Expected structure:
```
~/Documents/MileageLog/data/
├── vehicles/
│   └── {vehicle_id}.json
├── checkpoints/
│   ├── 2025-11/
│   │   ├── {checkpoint_id}.json
│   │   └── index.json
│   └── 2025-12/
├── trips/
│   ├── 2025-11/
│   │   ├── {trip_id}.json
│   │   └── index.json
│   └── 2025-12/
├── templates/
│   └── {template_id}.json
└── reports/
    └── {report_id}.{csv|pdf}
```

## Security Considerations

### API Keys

Never commit API keys to version control:

```bash
# .gitignore
claude_desktop_config.json
.env
*.key
```

Store API keys securely:
```bash
# macOS Keychain
security add-generic-password -s "Claude Desktop" -a "ANTHROPIC_API_KEY" -w "sk-..."

# Retrieve
security find-generic-password -s "Claude Desktop" -a "ANTHROPIC_API_KEY" -w
```

### Data Privacy

- Receipts contain personal financial data (store locally only)
- GPS coordinates reveal location history (encrypt if cloud sync)
- VIN is personally identifiable (required for Slovak compliance)

### Recommendations

1. **Backup data regularly:**
   ```bash
   tar -czf mileage-backup-$(date +%Y%m%d).tar.gz ~/Documents/MileageLog/data/
   ```

2. **Encrypt backups:**
   ```bash
   gpg -c mileage-backup-20251120.tar.gz
   ```

3. **Use file permissions:**
   ```bash
   chmod 600 ~/Documents/MileageLog/data/*/*.json
   ```

## Next Steps

1. ✅ Install MCP servers
2. ✅ Configure Claude Desktop
3. ✅ Verify tool availability
4. ✅ Run smoke tests
5. 📋 Complete full testing (see TESTING_F1-F3.md)
6. 🚀 Start using Car Log for real trips!

## Support

- Issues: https://github.com/your-repo/car-log/issues
- Documentation: /home/user/car-log/spec/
- MCP Specs: /home/user/car-log/spec/07-mcp-api-specifications.md
- Skills: /home/user/car-log/claude_skills/

---

**Installation Status:** Ready for manual testing in Claude Desktop
**Estimated Setup Time:** 15-30 minutes
**Prerequisites:** Python 3.11+, Node.js 18+, Claude Desktop
