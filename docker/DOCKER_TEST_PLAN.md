# Docker Deployment Test Plan

**Status:** ✅ Configuration Complete, ⏳ Testing Pending
**Priority:** P0 (Required for deployment)
**Estimated Time:** 2-3 hours
**Prerequisites:** Docker Desktop or Docker Engine 20.10+

---

## Pre-Test Checklist

### Files Verified ✅
- [x] `docker-compose.yml` - Defines 2 services (Python + Node.js)
- [x] `Dockerfile.python` - All 6 Python MCP servers
- [x] `Dockerfile.nodejs` - geo-routing server
- [x] `docker-entrypoint.sh` - Startup script
- [x] `.env.example` - Environment template
- [x] `requirements.txt` - Python dependencies
- [x] `README.md` - Documentation

### Configuration Review ✅
- [x] Python container includes system dependencies (libzbar0, poppler-utils)
- [x] Node.js container uses production dependencies only
- [x] Shared volume `/data` mounted correctly
- [x] Health checks configured (30s interval)
- [x] All environment variables documented
- [x] Network configuration (bridge)

---

## Test Procedure

### Phase 1: Environment Setup (5 minutes)

**Step 1.1: Set up environment variables**
```bash
cd docker
cp .env.example .env
# Edit .env (optional - only needed for ANTHROPIC_API_KEY)
nano .env
```

**Expected:** `.env` file created

---

### Phase 2: Container Build (10-15 minutes)

**Step 2.1: Build Python container**
```bash
docker-compose build car-log-python
```

**Expected Output:**
```
[+] Building 45.2s (15/15) FINISHED
 => [internal] load build definition
 => [internal] load .dockerignore
 => exporting to image
 => => naming to docker.io/library/docker-car-log-python
```

**Validation:**
- [ ] Build completes without errors
- [ ] All Python dependencies installed
- [ ] System packages (libzbar0, poppler-utils) installed
- [ ] Data directories created (/data/vehicles, /data/checkpoints, etc.)

**Step 2.2: Build Node.js container**
```bash
docker-compose build geo-routing
```

**Expected Output:**
```
[+] Building 12.5s (10/10) FINISHED
 => exporting to image
 => => naming to docker.io/library/docker-car-log-geo-routing
```

**Validation:**
- [ ] Build completes without errors
- [ ] npm dependencies installed
- [ ] Production mode (devDependencies excluded)

---

### Phase 3: Container Startup (5 minutes)

**Step 3.1: Start all containers**
```bash
docker-compose up -d
```

**Expected Output:**
```
[+] Running 3/3
 ✔ Network docker_car-log-net        Created
 ✔ Container car-log-python          Started
 ✔ Container car-log-geo-routing     Started
```

**Step 3.2: Check container status**
```bash
docker-compose ps
```

**Expected Output:**
```
NAME                    STATUS              PORTS
car-log-python          Up 10 seconds       (healthy)
car-log-geo-routing     Up 10 seconds       (healthy)
```

**Validation:**
- [ ] Both containers running
- [ ] Health checks passing (wait 40s for Python, 10s for Node.js)
- [ ] No restart loops

**Step 3.3: View logs**
```bash
docker-compose logs -f
```

**Expected Output:**
```
car-log-python      | Starting MCP servers...
car-log-python      | [INFO] car-log-core listening on stdio
car-log-python      | [INFO] trip-reconstructor listening on stdio
car-log-python      | [INFO] validation listening on stdio
car-log-python      | [INFO] ekasa-api listening on stdio
car-log-python      | [INFO] dashboard-ocr listening on stdio
car-log-python      | [INFO] report-generator listening on stdio
geo-routing         | [INFO] geo-routing server ready
```

**Validation:**
- [ ] All 7 MCP servers start without errors
- [ ] No Python import errors
- [ ] No Node.js module errors
- [ ] No permission errors on /data volume

---

### Phase 4: Data Persistence (10 minutes)

**Step 4.1: Create test data**
```bash
# Execute in Python container
docker exec -it car-log-python python -c "
import json
from pathlib import Path
test_vehicle = {
    'vehicle_id': 'test-123',
    'make': 'Ford',
    'model': 'Transit',
    'year': 2020
}
Path('/data/vehicles/test-123.json').write_text(json.dumps(test_vehicle, indent=2))
print('Test vehicle created')
"
```

**Expected:** "Test vehicle created"

**Step 4.2: Verify data exists in container**
```bash
docker exec -it car-log-python ls -la /data/vehicles/
```

**Expected Output:**
```
-rw-r--r-- 1 root root 120 Nov 18 22:00 test-123.json
```

**Step 4.3: Verify data exists on host**
```bash
ls -la ../data/vehicles/
cat ../data/vehicles/test-123.json
```

**Expected:** File exists on host with same content

**Step 4.4: Test persistence after restart**
```bash
docker-compose restart car-log-python
sleep 10
docker exec -it car-log-python cat /data/vehicles/test-123.json
```

**Expected:** Data persists after restart

**Validation:**
- [ ] Data written from container appears on host
- [ ] Data survives container restart
- [ ] Atomic write pattern works (no .tmp files)

---

### Phase 5: MCP Tool Verification (20 minutes)

**Note:** MCP servers in Docker communicate via stdio. To test MCP tools, you need to configure Claude Desktop to connect to the containers.

**Step 5.1: Update Claude Desktop config**

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "car-log-core": {
      "command": "docker",
      "args": ["exec", "-i", "car-log-python", "python", "-m", "mcp_servers.car_log_core"]
    },
    "geo-routing": {
      "command": "docker",
      "args": ["exec", "-i", "car-log-geo-routing", "node", "/app/index.js"]
    }
    // ... add other servers
  }
}
```

**Step 5.2: Test tool discovery in Claude Desktop**
- [ ] Open Claude Desktop
- [ ] Check MCP servers are discovered
- [ ] Verify all 28 tools are listed

**Step 5.3: Test basic CRUD operations**
- [ ] Create vehicle via Claude Desktop
- [ ] Verify JSON file created in ../data/vehicles/
- [ ] Create checkpoint
- [ ] Verify JSON file created in ../data/checkpoints/YYYY-MM/
- [ ] Create trip
- [ ] Verify JSON file created in ../data/trips/YYYY-MM/

**Validation:**
- [ ] All tools discoverable
- [ ] CRUD operations work through Docker
- [ ] Files created with correct permissions
- [ ] No stdio communication errors

---

### Phase 6: QR Scanning & PDF Processing (15 minutes)

**Step 6.1: Test QR scanning dependencies**
```bash
# Test libzbar0 is installed
docker exec -it car-log-python zbarimg --version
```

**Expected:** zbarimg version info

**Step 6.2: Test PDF processing dependencies**
```bash
# Test poppler-utils is installed
docker exec -it car-log-python pdfinfo --version
```

**Expected:** pdfinfo version info

**Step 6.3: Test QR scanning with sample receipt**
```bash
# Copy test receipt to container
docker cp ../tests/fixtures/sample-receipt.pdf car-log-python:/tmp/

# Run QR scan test
docker exec -it car-log-python python -c "
from mcp_servers.ekasa_api.qr_scanner import scan_pdf_multi_scale
result = scan_pdf_multi_scale('/tmp/sample-receipt.pdf')
print(f'QR detected: {result}')
"
```

**Validation:**
- [ ] QR code detected
- [ ] Multi-scale detection works
- [ ] Receipt ID extracted

---

### Phase 7: Performance & Resource Usage (10 minutes)

**Step 7.1: Check resource usage**
```bash
docker stats --no-stream
```

**Expected Output:**
```
CONTAINER            CPU %    MEM USAGE / LIMIT     NET I/O
car-log-python       2.5%     150MiB / 4GiB        10kB / 5kB
car-log-geo-routing  1.2%     80MiB / 4GiB         5kB / 3kB
```

**Validation:**
- [ ] Python container < 200MB memory
- [ ] Node.js container < 100MB memory
- [ ] CPU usage < 5% when idle
- [ ] No memory leaks (stable over 5 minutes)

**Step 7.2: Test with load**
```bash
# Create 100 test vehicles rapidly
for i in {1..100}; do
  docker exec -it car-log-python python -c "
from pathlib import Path
import json, uuid
vid = str(uuid.uuid4())
Path(f'/data/vehicles/{vid}.json').write_text(json.dumps({'vehicle_id': vid}))
" &
done
wait
```

**Validation:**
- [ ] All 100 files created successfully
- [ ] No file corruption (atomic writes work)
- [ ] No temp files remaining
- [ ] Memory usage remains stable

---

### Phase 8: Error Handling (10 minutes)

**Step 8.1: Test missing environment variable**
```bash
# Remove ANTHROPIC_API_KEY
docker-compose stop
# Edit docker-compose.yml, remove ANTHROPIC_API_KEY line
docker-compose up -d
docker-compose logs dashboard-ocr
```

**Expected:** Warning logged but server starts (OCR is P1)

**Step 8.2: Test invalid data path**
```bash
docker exec -it car-log-python python -c "
import os
os.environ['DATA_PATH'] = '/invalid/path'
# Try to create vehicle - should fail gracefully
"
```

**Expected:** Clear error message, no crash

**Step 8.3: Test crashed server recovery**
```bash
# Kill Python server process
docker exec -it car-log-python pkill -9 python
sleep 5
docker-compose ps
```

**Expected:** Container auto-restarts (restart: unless-stopped)

**Validation:**
- [ ] Graceful error handling
- [ ] Clear error messages
- [ ] Auto-restart on crash
- [ ] No data corruption

---

### Phase 9: Cleanup (2 minutes)

**Step 9.1: Stop containers**
```bash
docker-compose down
```

**Expected Output:**
```
[+] Running 3/3
 ✔ Container car-log-geo-routing  Removed
 ✔ Container car-log-python       Removed
 ✔ Network docker_car-log-net     Removed
```

**Step 9.2: Verify data persists**
```bash
ls -la ../data/vehicles/ | wc -l
```

**Expected:** Files still exist (volume persists)

**Step 9.3: Clean up test data**
```bash
rm -rf ../data/vehicles/test-*.json
```

---

## Success Criteria

### Required (P0)
- [x] Dockerfiles configured correctly ✅
- [ ] Both containers build without errors
- [ ] All 7 MCP servers start successfully
- [ ] Health checks pass
- [ ] Data persistence works (volume mount)
- [ ] MCP tools callable from Claude Desktop
- [ ] QR scanning dependencies installed
- [ ] PDF processing dependencies installed
- [ ] Atomic write pattern works (no corruption)
- [ ] Resource usage acceptable (< 300MB total)

### Optional (P1)
- [ ] Docker Compose profiles (dev/prod)
- [ ] Multi-platform builds (amd64/arm64)
- [ ] CI/CD integration
- [ ] Docker Hub publishing

---

## Troubleshooting

### Issue: Build fails with "package not found"
**Solution:** Check internet connection, retry build

### Issue: Containers exit immediately
**Solution:** Check logs with `docker-compose logs`, fix startup errors

### Issue: Health check fails
**Solution:** Increase `start_period` in docker-compose.yml

### Issue: Permission denied on /data volume
**Solution:** Check volume mount permissions, use `chmod 777 ../data` (dev only)

### Issue: MCP tools not discoverable in Claude Desktop
**Solution:** Verify `docker exec` command works, check stdio communication

---

## Test Results Template

```markdown
## Docker Deployment Test Results

**Date:** YYYY-MM-DD
**Tester:** [Name]
**Environment:** macOS/Windows/Linux
**Docker Version:** X.Y.Z

### Phase 1: Environment Setup
- [ ] ✅ PASS / ❌ FAIL - Environment variables configured

### Phase 2: Container Build
- [ ] ✅ PASS / ❌ FAIL - Python container builds
- [ ] ✅ PASS / ❌ FAIL - Node.js container builds

### Phase 3: Container Startup
- [ ] ✅ PASS / ❌ FAIL - Containers start
- [ ] ✅ PASS / ❌ FAIL - Health checks pass
- [ ] ✅ PASS / ❌ FAIL - All 7 MCP servers running

### Phase 4: Data Persistence
- [ ] ✅ PASS / ❌ FAIL - Volume mount works
- [ ] ✅ PASS / ❌ FAIL - Data survives restart
- [ ] ✅ PASS / ❌ FAIL - No file corruption

### Phase 5: MCP Tool Verification
- [ ] ✅ PASS / ❌ FAIL - Tools discoverable
- [ ] ✅ PASS / ❌ FAIL - CRUD operations work

### Phase 6: QR Scanning & PDF
- [ ] ✅ PASS / ❌ FAIL - libzbar0 installed
- [ ] ✅ PASS / ❌ FAIL - poppler-utils installed
- [ ] ✅ PASS / ❌ FAIL - QR detection works

### Phase 7: Performance
- [ ] ✅ PASS / ❌ FAIL - Memory < 300MB total
- [ ] ✅ PASS / ❌ FAIL - No memory leaks

### Phase 8: Error Handling
- [ ] ✅ PASS / ❌ FAIL - Graceful errors
- [ ] ✅ PASS / ❌ FAIL - Auto-restart works

### Overall Result
- [ ] ✅ APPROVED FOR PRODUCTION
- [ ] ⚠️ APPROVED WITH ISSUES (list below)
- [ ] ❌ REJECTED (critical issues found)

**Issues Found:**
1. [Issue description]
2. [Issue description]

**Notes:**
[Additional observations]
```

---

## Next Steps After Testing

1. **If PASS:** Update TASKS.md Track E as ✅ COMPLETE
2. **If FAIL:** File issues, fix critical bugs, re-test
3. **If APPROVED:** Document deployment guide for production
4. **If using in hackathon:** Include Docker deployment in demo video

---

**Status:** Ready to test (Docker not available in current environment)
**Blocking:** Docker installation required
**Estimated Duration:** 2-3 hours total testing time
