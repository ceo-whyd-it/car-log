# Claude Skills Troubleshooting Guide

**Project:** Car Log - Slovak Tax-Compliant Mileage Logger
**Last Updated:** November 20, 2025

---

## Quick Diagnostics

Before troubleshooting specific issues, run these quick checks:

```bash
# Check MCP servers are running
docker-compose ps
# OR (if running locally)
ps aux | grep -E "(car_log_core|ekasa_api|geo_routing|trip_reconstructor|validation|dashboard_ocr|report_generator)"

# Check data directory exists
ls -la ~/Documents/MileageLog/data/

# Check Claude Desktop logs
tail -f ~/Library/Logs/Claude/mcp*.log   # macOS
tail -f ~/.config/Claude/logs/mcp*.log   # Linux
```

**Quick Status:**
- ✅ MCP servers running
- ✅ Data directory accessible
- ✅ Skills loaded in Claude Desktop
- ⏳ Issue details below

---

## Common Issues

### 1. Skill Not Triggering

**Symptom:** User types trigger words but skill doesn't activate.

**Possible Causes:**
1. Skill not loaded in Claude Desktop
2. Trigger words don't match user input
3. Another skill matches first
4. Skill file syntax error

**Solutions:**

#### Check Skill is Loaded
```
Claude Desktop → Settings → Skills → Verify skill appears in list
```

If missing:
1. Click "New Skill"
2. Copy content from `claude_skills/01-vehicle-setup.md`
3. Save as "Vehicle Setup"
4. Repeat for skills 02-06

#### Verify Trigger Words
Open skill file and check trigger section:
```markdown
**Trigger words:** "add vehicle", "new car", "register vehicle", license plate patterns (XX-123XX)
```

Try exact trigger phrase:
```
❌ "I want to add a vehicle"          (too vague)
✅ "Add vehicle BA-456CD"              (exact trigger)
```

#### Check Skill Priority
If multiple skills have overlapping triggers, Claude picks the best match. Add more specific triggers:
```markdown
**Trigger words:** "add vehicle", "new vehicle", "register vehicle"
```

#### Validate Skill File Syntax
Common syntax errors:
- Missing frontmatter (YAML header)
- Broken markdown formatting
- Invalid JSON in examples

Test by copying skill content to a markdown validator.

**Debug Commands:**
```
User: "List my active skills"
Claude: [Shows which skills are loaded]

User: "Show me the Vehicle Setup skill"
Claude: [Displays skill content if loaded]
```

---

### 2. MCP Tool Call Fails

**Symptom:** Skill triggers but tool returns error.

**Error Messages:**
```
Error: Tool 'car-log-core.create_vehicle' not found
Error: Connection refused (server not running)
Error: Tool execution timeout
```

**Solutions:**

#### Server Not Running
```bash
# Docker deployment
cd docker
docker-compose ps
# If not running:
docker-compose up -d

# Local deployment
python -m mcp_servers.car_log_core
# Should output: Server running on stdio...
```

#### Server Not Configured in Claude Desktop
Check `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "car-log-core": {
      "command": "python",
      "args": ["-m", "mcp_servers.car_log_core"],
      "env": {
        "DATA_PATH": "~/Documents/MileageLog/data"
      }
    }
  }
}
```

Verify path:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

After editing, restart Claude Desktop.

#### Tool Name Mismatch
Tool names are `{server}.{tool}`:
```
✅ car-log-core.create_vehicle
✅ ekasa-api.scan_qr_code
❌ create_vehicle               (missing server prefix)
❌ car_log_core.create_vehicle  (underscore instead of hyphen)
```

Check tool registration in server's `__main__.py`:
```python
server.add_tool(create_vehicle)  # Tool name: car-log-core.create_vehicle
```

#### Tool Execution Timeout
Some tools take time (e-Kasa API: 5-30s). Increase timeout in config:
```json
{
  "mcpServers": {
    "ekasa-api": {
      "env": {
        "MCP_TIMEOUT_SECONDS": "60"
      }
    }
  }
}
```

**Debug Commands:**
```bash
# Test tool directly (if MCP CLI available)
mcp call car-log-core.list_vehicles '{"user_id": "test"}'

# Check server logs
docker-compose logs -f car-log-core
```

---

### 3. GPS Extraction Fails

**Symptom:** "No GPS data found in photo"

**Possible Causes:**
1. Photo is a screenshot (no EXIF)
2. Photo taken with location disabled
3. EXIF data stripped by social media
4. Photo format doesn't support EXIF (BMP, WebP)

**Solutions:**

#### Verify Photo Has EXIF
```bash
# macOS
mdls dashboard.jpg | grep -i gps

# Linux
exiftool dashboard.jpg | grep -i gps
```

Expected output:
```
GPS Latitude: 48 deg 8' 55.00" N
GPS Longitude: 17 deg 6' 27.72" E
```

If no output → Photo has no GPS data.

#### Take Photo with Location Enabled
1. Open phone Camera app
2. Settings → Location → Always Allow
3. Take new photo
4. Verify EXIF: GPS should appear in photo metadata

#### Use Phone Camera App (Not Screenshot)
```
❌ Screenshot from Maps app     → No EXIF
❌ Downloaded image              → EXIF often stripped
✅ Photo from Camera app         → EXIF preserved
```

#### Fallback: Enter GPS Manually
If GPS extraction fails:
```
Claude: "No GPS found. Please enter coordinates manually:"
User: "48.1486, 17.1077"
Claude: "GPS saved: 48.1486°N, 17.1077°E"
```

Or use address geocoding:
```
User: "Hlavná 45, Bratislava"
Claude: "Geocoding... Found: 48.1486°N, 17.1077°E"
```

**Debug Commands:**
```python
# Test EXIF extraction directly
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

img = Image.open('dashboard.jpg')
exif = img._getexif()
print(exif)  # Should show GPS data
```

---

### 4. e-Kasa API Timeout

**Symptom:** "e-Kasa API timeout after 60s"

**Possible Causes:**
1. API is slow (5-30s normal, 60s+ timeout)
2. Invalid receipt ID
3. Internet connection issue
4. API rate limiting

**Solutions:**

#### Wait and Retry
e-Kasa API can be slow. First timeout is not fatal:
```
Claude: "e-Kasa API timeout. Retry?"
User: "Yes"
Claude: [Retries with same receipt ID]
```

#### Verify Receipt ID Format
e-Kasa receipt IDs are long alphanumeric strings:
```
✅ "O-1234567890ABCDEF1234567890ABCDEF"
❌ "1234"                                  (too short)
❌ "INVALID-ID"                            (wrong format)
```

QR code should contain full URL:
```
https://ekasa.financnasprava.sk/receipt/{receipt_id}
```

#### Check Internet Connection
```bash
# Test API endpoint
curl -I "https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/test"

# Should return 200 or 404 (not connection error)
```

#### Fallback: Manual Entry
If API consistently times out:
```
Claude: "e-Kasa API unavailable. Enter receipt data manually?"
User: "52.3L Diesel at €1.47/L, total €76.85"
Claude: "Receipt saved manually."
```

**Debug Commands:**
```bash
# Test e-Kasa API directly
curl "https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/{receipt_id}"

# Check ekasa-api server logs
docker-compose logs -f ekasa-api
```

---

### 5. QR Code Not Detected

**Symptom:** "QR code not found in photo"

**Possible Causes:**
1. QR code too small or blurry
2. PDF rendering issue (low DPI)
3. QR code damaged or partial
4. Wrong image format

**Solutions:**

#### Improve Photo Quality
```
❌ Zoomed out (QR code tiny)      → Take closer photo
❌ Blurry/out of focus            → Hold phone steady
❌ Poor lighting                  → Use flash or bright light
✅ Close-up, sharp, well-lit      → QR code fills 1/4 of frame
```

#### PDF Multi-Scale Detection
For PDF receipts, multi-scale detection runs automatically:
```
1x scale → No QR found
2x scale → Trying...
3x scale → QR code found!
```

If all scales fail, try:
1. Open PDF in viewer
2. Zoom to 200%
3. Screenshot QR code area
4. Paste screenshot

#### Manual Receipt ID Entry
If QR scan fails consistently:
```
Claude: "QR code not detected. Enter receipt ID manually?"
User: "O-1234567890ABCDEF1234567890ABCDEF"
Claude: "Receipt ID entered. Fetching from e-Kasa..."
```

**Debug Commands:**
```python
# Test QR detection directly
from pyzbar.pyzbar import decode
from PIL import Image

img = Image.open('receipt.jpg')
decoded = decode(img)
print(decoded)  # Should show QR data
```

---

### 6. Template Matching Low Confidence

**Symptom:** "No templates matched with sufficient confidence (>=70%)"

**Possible Causes:**
1. Templates don't match gap endpoints
2. GPS coordinates missing in templates
3. Addresses too different
4. Distance mismatch

**Solutions:**

#### Check Template GPS Coordinates
Templates MUST have GPS coordinates for high confidence:
```json
{
  "from_coords": {"lat": 48.1486, "lng": 17.1077},  // MANDATORY
  "to_coords": {"lat": 48.7164, "lng": 21.2611},    // MANDATORY
  "from_address": "Bratislava",                     // Optional
  "to_address": "Košice"                            // Optional
}
```

Without GPS:
```
GPS match: 0% (no GPS) × 70% weight = 0%
Address match: 80% × 30% weight = 24%
Total: 24% (below 70% threshold)
```

With GPS:
```
GPS match: 98% × 70% weight = 68.6%
Address match: 80% × 30% weight = 24%
Total: 92.6% (above 70% threshold)
```

#### Create New Template
If no existing templates match:
```
Claude: "No high-confidence matches. Create new template?"
User: "Yes, create Warehouse Run template"
Claude: [Launches Skill 4: Template Creation]
```

#### Lower Confidence Threshold (Not Recommended)
Adjust threshold in `trip_reconstructor` config:
```json
{
  "env": {
    "CONFIDENCE_THRESHOLD": "60"  // Default: 70
  }
}
```

⚠️ Lower threshold increases false positives.

#### Manual Trip Entry
Fallback to manual logging:
```
User: "Log trip manually"
Claude: "I'll help you create a trip. Where did it start?"
```

**Debug Commands:**
```bash
# Check template completeness
cat ~/Documents/MileageLog/data/templates/{template_id}.json

# Verify GPS coordinates present
jq '.from_coords, .to_coords' template.json
```

---

### 7. Validation Warnings

**Symptom:** "Warning: Fuel consumption 23% higher than expected"

**This is NOT an error!** Validation warnings are informational.

**Common Warnings:**

#### Distance Sum Mismatch (±10% threshold)
```
Warning: Odometer shows 820 km, but trips sum to 750 km (8.5% difference)

Possible reasons:
- Personal trips not logged
- Detours taken
- Odometer calibration

Action: Review trips or accept variance
```

#### Fuel Consumption High (±15% threshold)
```
Warning: Fuel consumption 23% higher than expected

Possible reasons:
- Heavy load (cargo)
- Cold weather
- Stop-and-go traffic
- Air conditioning use

Action: Accept warning or check for leak
```

#### Efficiency Out of Range
```
Warning: 3.2 L/100km is unrealistically low for Diesel

Possible reasons:
- Odometer error
- Fuel calculation error
- Hybrid vehicle misconfigured

Action: Verify odometer reading and fuel quantity
```

#### Deviation from Average (±20% threshold)
```
Warning: 35% deviation from vehicle average (8.5 L/100km)

Possible reasons:
- First few trips (no stable average yet)
- Different driving conditions
- Vehicle issue

Action: Monitor over time
```

**Solutions:**

#### Accept Warning
Warnings don't block operations:
```
Claude: "Warning: Fuel consumption high. Continue?"
User: "Yes"
Claude: "Trip saved with warning flag."
```

#### Adjust Thresholds
Edit `validation/thresholds.py`:
```python
DISTANCE_VARIANCE_PERCENT = 15  # Default: 10
CONSUMPTION_VARIANCE_PERCENT = 20  # Default: 15
DEVIATION_THRESHOLD_PERCENT = 30  # Default: 20
```

Restart validation server after changes.

#### Review Data
Check for data entry errors:
```
- Odometer reading correct?
- Fuel quantity correct?
- Distance calculation reasonable?
```

**Debug Commands:**
```bash
# Check validation thresholds
cat mcp-servers/validation/thresholds.py

# Test validation directly
python -c "from mcp_servers.validation.tools.validate_trip import validate_trip; print(validate_trip(...))"
```

---

### 8. File Corruption or Missing Data

**Symptom:** "Trip file not found" or "JSON parse error"

**Possible Causes:**
1. Atomic write interrupted
2. Manual file edit
3. Permission issue
4. Disk full

**Solutions:**

#### Check File Exists
```bash
ls -la ~/Documents/MileageLog/data/trips/2025-11/

# Expected output:
{trip_id}.json
```

If missing → File was never created or deleted.

#### Check File Permissions
```bash
ls -l ~/Documents/MileageLog/data/trips/2025-11/{trip_id}.json

# Should be readable/writable by user
chmod 644 {trip_id}.json
```

#### Validate JSON Syntax
```bash
# macOS/Linux
jq . {trip_id}.json

# If parse error → File corrupted
```

#### Check for Temp Files
Atomic write creates temp files:
```bash
ls -la ~/Documents/MileageLog/data/trips/2025-11/*.tmp

# If .tmp files exist → Write was interrupted
# Safe to delete .tmp files
rm *.tmp
```

#### Restore from Backup
If file corrupted and no backup:
```bash
# Check if git tracked
cd ~/Documents/MileageLog
git log -- data/trips/2025-11/{trip_id}.json

# Restore from git
git checkout HEAD -- data/trips/2025-11/{trip_id}.json
```

If not in git → Data lost, recreate trip.

**Prevention:**
- Atomic writes prevent corruption (implemented)
- Regular backups (user responsibility)
- Git track data directory (optional)

**Debug Commands:**
```bash
# Test atomic write
python -c "from mcp_servers.car_log_core.storage import atomic_write_json; atomic_write_json('test.json', {'test': 'data'})"

# Verify file created
cat test.json
```

---

### 9. Skill Chaining Doesn't Work

**Symptom:** Gap detected but reconstruction doesn't trigger automatically.

**Expected Behavior:**
```
Skill 2 (Checkpoint) → Gap detected → "Would you like to reconstruct trips?" → Skill 3 triggered
```

**Possible Causes:**
1. Skill 3 not loaded
2. User prompt not answered
3. Auto-trigger disabled

**Solutions:**

#### Verify Both Skills Loaded
```
Claude Desktop → Settings → Skills → Verify:
- ✅ Checkpoint from Receipt (Skill 2)
- ✅ Trip Reconstruction (Skill 3)
```

#### Explicit Trigger
If auto-trigger fails, manually trigger:
```
User: "Reconstruct trips for November gap"
Claude: [Launches Skill 3]
```

#### Check Skill Dependencies
Skill 3 depends on:
- Gap data from Skill 2
- Templates from Skill 4
- MCP servers: car-log-core, trip-reconstructor, geo-routing

Verify all are functional:
```bash
docker-compose ps
# All services should be "Up"
```

**Debug Commands:**
```
User: "Show gap between Nov 1 and Nov 8"
Claude: [Should display gap data]

User: "List my templates"
Claude: [Should show templates]

User: "Now match templates to this gap"
Claude: [Should trigger reconstruction]
```

---

### 10. Performance Issues

**Symptom:** Operations take > 10 seconds.

**Acceptable Response Times:**
- Vehicle creation: < 5s
- QR scan: < 5s
- e-Kasa API: 5-30s (acceptable), > 60s (timeout)
- GPS extraction: < 3s
- Template matching: < 5s (even with 100 templates)
- Report generation: < 5s (1000 trips)

**Troubleshooting:**

#### Identify Bottleneck
```bash
# Check CPU usage
top
# Look for Python/Node processes at 100%

# Check disk I/O
iostat 1
# Look for high %iowait
```

#### Common Bottlenecks

**Geocoding (Nominatim):**
- Symptom: Template creation takes 10+ seconds
- Solution: Cache enabled (24h TTL), check cache:
  ```bash
  docker-compose logs geo-routing | grep -i cache
  ```

**Template Matching (100+ templates):**
- Symptom: Reconstruction takes 5+ seconds
- Solution: Should still be < 5s. If slower:
  ```bash
  # Check number of templates
  ls -l ~/Documents/MileageLog/data/templates/ | wc -l
  # If > 500 → Consider indexing (post-MVP)
  ```

**Report Generation (1000+ trips):**
- Symptom: CSV generation takes 10+ seconds
- Solution: Use monthly index:
  ```bash
  # Check if index exists
  ls ~/Documents/MileageLog/data/trips/2025-11/index.json
  # If missing → Create index (optional optimization)
  ```

**e-Kasa API:**
- Symptom: 60s timeout every time
- Solution: API may be overloaded. Fallback to manual entry.

#### Clear Caches
```bash
# Geo-routing cache
docker-compose restart geo-routing

# Or delete cache file
rm ~/Documents/MileageLog/data/.cache/geocoding.cache
```

**Debug Commands:**
```bash
# Profile Python code (if needed)
python -m cProfile -o profile.stats -m mcp_servers.trip_reconstructor

# View results
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('time').print_stats(10)"
```

---

## Environment-Specific Issues

### macOS

#### Claude Desktop Not Finding Config
```bash
# Verify path
ls ~/Library/Application\ Support/Claude/claude_desktop_config.json

# If missing, create
mkdir -p ~/Library/Application\ Support/Claude/
cp claude_desktop_config.json ~/Library/Application\ Support/Claude/
```

#### Python Not Found
```bash
# Verify Python version
python3 --version
# Should be 3.11+

# If not installed
brew install python@3.11
```

### Linux

#### Permission Denied
```bash
# Fix data directory permissions
chmod -R 755 ~/Documents/MileageLog/data/
chown -R $USER:$USER ~/Documents/MileageLog/data/
```

#### Node.js Not Found
```bash
# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Docker

#### Container Won't Start
```bash
# Check logs
docker-compose logs car-log-core

# Common issues:
# - Port conflict: Change port in docker-compose.yml
# - Volume mount error: Verify path in .env
# - Python import error: Rebuild image
docker-compose build --no-cache car-log-core
docker-compose up -d
```

#### Data Not Persisting
```bash
# Verify volume mount
docker-compose exec car-log-core ls /data

# If empty → Volume mount failed
# Fix in docker-compose.yml:
volumes:
  - ./data:/data  # Relative path
  # OR
  - ~/Documents/MileageLog/data:/data  # Absolute path
```

---

## Emergency Fallbacks

If all else fails:

### 1. Manual Data Entry
Skip photo workflows and enter data manually:
```
Vehicle: Create JSON file directly
Checkpoint: Enter odometer, GPS, fuel manually
Trip: Enter start/end, distance manually
Report: Generate manually (open JSON files)
```

### 2. Use Integration Tests
Backend is 100% functional, so bypass Claude Desktop:
```bash
# Test directly with Python
python tests/integration_checkpoint_day7.py

# All 20 tests should pass
```

### 3. Use Mock Data
Generate demo dataset:
```bash
python scripts/generate_mock_data.py --scenario demo

# Creates:
# - 1 vehicle
# - 2 checkpoints
# - 2 templates
# - 820 km gap
```

### 4. Docker Reset
Nuclear option - start fresh:
```bash
docker-compose down -v  # Deletes volumes
rm -rf ~/Documents/MileageLog/data/*  # Deletes data (BACKUP FIRST!)
docker-compose up -d
# Reconfigure Claude Desktop
```

---

## Getting Help

### Resources
1. **INTEGRATION_TESTING.md** - Test scenarios
2. **MANUAL_TEST_CHECKLIST.md** - Step-by-step testing
3. **PERFORMANCE.md** - Performance benchmarks
4. **CLAUDE_DESKTOP_SETUP.md** - Setup guide
5. **GitHub Issues** - Report bugs
6. **spec/** - Architecture documentation

### Debug Information to Collect
When reporting issues, include:
```
1. Claude Desktop version
2. OS version
3. MCP server logs (docker-compose logs)
4. Skill file content
5. Error message (exact text)
6. Steps to reproduce
7. Expected vs actual behavior
```

### Contact
- GitHub: [repository issues]
- Hackathon Submission: [link]
- Documentation: README.md

---

**Last Updated:** November 20, 2025
**Status:** Ready for user testing
**Coverage:** 10 common issues + environment-specific + emergency fallbacks
