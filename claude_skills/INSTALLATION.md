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

### Step 3: Install Skills in Claude Desktop

**Understanding the Structure:**

Each skill folder contains:
- **SKILL.md** - Concise prompt for Claude (~200-600 words) ← **Load this into Claude Desktop**
- **GUIDE.md** - Comprehensive guide for humans (reference documentation)
- **REFERENCE.md** - MCP tool specifications (technical reference)
- **examples/** - Sample data for testing

**Manual Installation Steps:**

#### Option A: Copy Individual Skills (Recommended)

1. Navigate to skill folders:
   ```bash
   cd /home/user/car-log/claude_skills
   ls -d */  # Shows: vehicle-setup/ checkpoint-from-receipt/ etc.
   ```

2. For each skill, open SKILL.md and copy content to Claude Desktop:

   **In Claude Desktop:**
   - Open Settings → Custom Instructions (or Skills, depending on version)
   - Create new skill or add to existing instructions
   - Paste SKILL.md content
   - Save

3. Install all 6 skills in this order:
   ```bash
   # Copy content from each SKILL.md file:
   cat vehicle-setup/SKILL.md
   cat checkpoint-from-receipt/SKILL.md
   cat trip-reconstruction/SKILL.md
   cat template-creation/SKILL.md
   cat report-generation/SKILL.md
   cat data-validation/SKILL.md
   ```

#### Option B: Combined Installation (Faster)

Create a combined skills file in Claude Desktop Custom Instructions:

```bash
# Concatenate all SKILL.md files
cat vehicle-setup/SKILL.md \
    checkpoint-from-receipt/SKILL.md \
    trip-reconstruction/SKILL.md \
    template-creation/SKILL.md \
    report-generation/SKILL.md \
    data-validation/SKILL.md > combined-skills.txt
```

Then paste `combined-skills.txt` into Claude Desktop Custom Instructions.

**Verification:**

Test each skill:
1. "Add vehicle BA-123CD" → Should trigger vehicle-setup skill
2. Paste receipt photo → Should trigger checkpoint-from-receipt skill
3. "Reconstruct trips" → Should trigger trip-reconstruction skill
4. "Create template Warehouse Run" → Should trigger template-creation skill
5. "Generate November report" → Should trigger report-generation skill
6. Validation runs automatically after data entry

### Step 4: Reference Documentation

**For users (comprehensive guides):**
- Read `<skill-folder>/GUIDE.md` for detailed workflows, examples, and testing scenarios

**For developers (MCP tool specs):**
- Read `<skill-folder>/REFERENCE.md` for MCP tool request/response formats

**For testing:**
- Use `<skill-folder>/examples/*.json` as test data
- Follow `MANUAL_TEST_CHECKLIST.md` for comprehensive testing

### Troubleshooting Installation

**Skill not triggering?**
- Check trigger words in SKILL.md match user input
- Verify all 7 MCP servers running (`docker-compose ps`)
- See `TROUBLESHOOTING.md` for common issues

**MCP tool calls failing?**
- Verify MCP server configuration in claude_desktop_config.json
- Check server logs: `docker-compose logs -f`
- Restart servers: `docker-compose restart`

### Step 5: Verify MCP Server Availability

1. Open Claude Desktop
2. Start a new conversation
3. Ask: "What MCP tools do you have access to?"
4. Verify you see all 7 servers:
   - car-log-core (14 tools)
   - ekasa-api (2 tools)
   - dashboard-ocr (1 tool)
   - trip-reconstructor (2 tools)
   - geo-routing (3 tools)
   - validation (4 tools)
   - report-generator (2 tools)

Expected total: **28 tools** (all P0+P1 features implemented).

### Step 6: Test Each Skill Individually

See `TESTING_F1-F3.md` and `TESTING_F4-F6.md` for comprehensive test scenarios.

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
