# Claude Desktop Skills Installation Guide

This guide explains how to install and configure the Car Log skills for Claude Desktop.

## Prerequisites

- Claude Desktop installed (macOS/Windows/Linux)
- MCP servers deployed via local installation (see main README.md)
- Car Log deployment directory: `~/.car-log-deployment/` (created automatically by install script)

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

### Step 2: Deploy MCP Servers

**IMPORTANT:** MCP servers are deployed using the local installation method. Do NOT configure manually.

**Windows:**
```cmd
cd D:\github_projects\car-log
install.bat
```

**macOS/Linux:**
```bash
cd ~/path/to/car-log
./deployment/scripts/deploy-macos.sh  # or deploy-linux.sh
```

This automatically:
- Creates `~/.car-log-deployment/` directory
- Copies all 7 MCP servers
- Installs Python and Node.js dependencies
- Generates `claude_desktop_config.json` with correct paths
- Creates data directories

**Configuration is automatic.** The deployment script generates the correct config for your platform with proper paths to:
- Windows batch wrappers: `C:\Users\YourName\.car-log-deployment\run-*.bat`
- Data directory: `C:\Users\YourName\.car-log-deployment\data\` (Windows) or `~/.car-log-deployment/data/` (macOS/Linux)

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
- Verify all 7 MCP servers loaded (restart Claude Desktop)
- See `TROUBLESHOOTING.md` for common issues

**MCP tool calls failing?**
- Verify MCP server configuration in `claude_desktop_config.json`
- Check Claude Desktop logs: `%APPDATA%\Claude\logs\` (Windows) or `~/Library/Logs/Claude/` (macOS)
- Re-run deployment script to update servers
- Restart Claude Desktop

### Step 5: Verify MCP Server Availability

1. **Restart Claude Desktop** (important - quit completely and reopen)
2. Start a new conversation
3. Ask: "What MCP tools do you have access to?"
4. Verify you see all 7 servers with **24 tools total**:
   - car-log-core: 14 tools (vehicles, checkpoints, templates, trips)
   - trip-reconstructor: 1 tool
   - validation: 1 tool
   - ekasa-api: 2 tools
   - dashboard-ocr: 2 tools
   - report-generator: 1 tool
   - geo-routing: 3 tools

Expected total: **24 tools** across 7 MCP servers.

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

The deployment script automatically creates the data directory at `~/.car-log-deployment/data/`.

**Windows:** `C:\Users\YourName\.car-log-deployment\data\`
**macOS/Linux:** `~/.car-log-deployment/data/`

Expected structure (created automatically):
```
.car-log-deployment/data/
├── vehicles/
│   └── {vehicle_id}.json
├── checkpoints/
│   ├── 2025-11/
│   │   └── {checkpoint_id}.json
│   └── 2025-12/
├── trips/
│   ├── 2025-11/
│   │   └── {trip_id}.json
│   └── 2025-12/
├── templates/
│   └── {template_id}.json
└── reports/
    └── {report_name}.csv
```

**Note:** Directories are created automatically. No manual setup required.

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
   # Windows (PowerShell)
   Compress-Archive -Path "$env:USERPROFILE\.car-log-deployment\data" -DestinationPath "mileage-backup-$(Get-Date -Format yyyyMMdd).zip"

   # macOS/Linux
   tar -czf mileage-backup-$(date +%Y%m%d).tar.gz ~/.car-log-deployment/data/
   ```

2. **Encrypt backups:**
   ```bash
   # macOS/Linux
   gpg -c mileage-backup-20251123.tar.gz

   # Windows: Use 7-Zip with password or BitLocker
   ```

3. **Use file permissions (macOS/Linux only):**
   ```bash
   chmod 700 ~/.car-log-deployment/data
   chmod 600 ~/.car-log-deployment/data/*/*.json
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
