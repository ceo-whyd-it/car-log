# Docker Deployment - Manual Testing Guide

**For:** Car Log MCP Servers (Track E - Docker Deployment)
**Purpose:** Step-by-step manual testing with Docker Desktop
**Time Required:** 2-3 hours
**Prerequisites:** Docker Desktop installed and running

---

## Overview

This guide walks you through manually testing the Docker deployment of all 7 MCP servers. Follow each step carefully and check off items as you complete them.

**What We're Testing:**
- ✅ Container builds complete successfully
- ✅ All 7 MCP servers start without errors
- ✅ Data persistence works (volume mounts)
- ✅ QR scanning dependencies installed
- ✅ PDF processing dependencies installed
- ✅ Resource usage acceptable
- ✅ Error handling works correctly

---

## Setup Instructions

### Step 1: Navigate to Docker Directory

```bash
cd /home/user/car-log/docker
```

**Verify you're in the right place:**
```bash
ls -la
# Should see: docker-compose.yml, Dockerfile.python, Dockerfile.nodejs, etc.
```

---

### Step 2: Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# (Optional) Edit .env if you have an Anthropic API key for OCR testing
nano .env
```

**What to know:**
- ANTHROPIC_API_KEY is only needed for dashboard OCR (P1 feature)
- All other variables have sensible defaults
- You can test without any API keys

**Checkpoint:** `.env` file exists in `/home/user/car-log/docker/.env`

---

## Part 1: Building Docker Images (10-15 minutes)

### Step 3: Build Python Container

```bash
docker-compose build car-log-python
```

**What to expect:**
- Build takes 5-10 minutes (downloads Python 3.11, installs packages)
- You'll see output like:
  ```
  [+] Building 45.2s (15/15) FINISHED
  => [internal] load build definition
  => [internal] load .dockerignore
  => [1/7] FROM docker.io/library/python:3.11-slim
  => [2/7] RUN apt-get update && apt-get install -y libzbar0 poppler-utils
  => [3/7] WORKDIR /app
  => [4/7] COPY docker/requirements.txt .
  => [5/7] RUN pip install --no-cache-dir -r requirements.txt
  => [6/7] COPY mcp-servers/ /app/mcp-servers/
  => [7/7] COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
  => exporting to image
  ```

**Success criteria:**
- [ ] Build completes without errors
- [ ] Final line shows: `=> exporting to image`
- [ ] Image tagged as `docker-car-log-python`

**If build fails:**
- Check internet connection (needs to download packages)
- Check Docker Desktop has enough disk space (needs ~500MB)
- Try rebuilding without cache: `docker-compose build --no-cache car-log-python`

---

### Step 4: Build Node.js Container

```bash
docker-compose build geo-routing
```

**What to expect:**
- Build takes 2-3 minutes (faster than Python)
- You'll see output like:
  ```
  [+] Building 12.5s (10/10) FINISHED
  => [internal] load build definition
  => [1/4] FROM docker.io/library/node:18-slim
  => [2/4] WORKDIR /app
  => [3/4] COPY package*.json ./
  => [4/4] RUN npm ci --only=production
  => exporting to image
  ```

**Success criteria:**
- [ ] Build completes without errors
- [ ] Image tagged as `docker-car-log-geo-routing`

**Checkpoint:** Both Docker images built successfully

---

## Part 2: Starting Containers (5-10 minutes)

### Step 5: Start All Containers

```bash
docker-compose up -d
```

**What to expect:**
```
[+] Running 3/3
 ✔ Network docker_car-log-net        Created    0.1s
 ✔ Container car-log-python          Started    1.2s
 ✔ Container car-log-geo-routing     Started    0.8s
```

**Success criteria:**
- [ ] Network created
- [ ] Both containers started
- [ ] No error messages

---

### Step 6: Check Container Status

```bash
docker-compose ps
```

**What to expect:**
```
NAME                    STATUS              PORTS
car-log-python          Up 15 seconds       (healthy)
car-log-geo-routing     Up 15 seconds       (healthy)
```

**Success criteria:**
- [ ] Both containers show "Up" status
- [ ] Health checks show "(healthy)" after ~40 seconds for Python, ~10 seconds for Node.js
- [ ] No restart loops

**If containers exit immediately:**
```bash
# Check what went wrong
docker-compose logs car-log-python
docker-compose logs geo-routing
```

---

### Step 7: View Startup Logs

```bash
docker-compose logs -f
```

**What to expect in Python container logs:**
```
car-log-python      | =========================================
car-log-python      |   Car Log MCP Servers - Starting...
car-log-python      | =========================================
car-log-python      | [2025-11-20 10:00:00] Starting car-log-core...
car-log-python      | [2025-11-20 10:00:00] ✓ car-log-core started (PID: 8)
car-log-python      | [2025-11-20 10:00:00] Starting trip-reconstructor...
car-log-python      | [2025-11-20 10:00:00] ✓ trip-reconstructor started (PID: 9)
car-log-python      | [2025-11-20 10:00:01] Starting validation...
car-log-python      | [2025-11-20 10:00:01] ✓ validation started (PID: 10)
car-log-python      | [2025-11-20 10:00:01] Starting ekasa-api...
car-log-python      | [2025-11-20 10:00:01] ✓ ekasa-api started (PID: 11)
car-log-python      | [2025-11-20 10:00:02] Starting dashboard-ocr...
car-log-python      | [2025-11-20 10:00:02] ✓ dashboard-ocr started (PID: 12)
car-log-python      | [2025-11-20 10:00:02] Starting report-generator...
car-log-python      | [2025-11-20 10:00:02] ✓ report-generator started (PID: 13)
car-log-python      | =========================================
car-log-python      |   All Python MCP servers started
car-log-python      | =========================================
```

**What to expect in Node.js container logs:**
```
geo-routing         | [INFO] geo-routing server ready
geo-routing         | [INFO] OSRM URL: https://router.project-osrm.org
geo-routing         | [INFO] Nominatim URL: https://nominatim.openstreetmap.org
```

**Success criteria:**
- [ ] All 6 Python MCP servers started (car-log-core, trip-reconstructor, validation, ekasa-api, dashboard-ocr, report-generator)
- [ ] geo-routing server started
- [ ] No Python import errors
- [ ] No "Module not found" errors
- [ ] No permission errors

**Common issues and fixes:**
- **"Module not found"**: Rebuild image with `docker-compose build --no-cache`
- **Permission denied on /data**: Run `chmod 777 /home/user/car-log/data` (dev only)
- **Import errors**: Check PYTHONPATH is set to `/app` in container

Press `Ctrl+C` to stop following logs.

**Checkpoint:** All 7 MCP servers running without errors

---

## Part 3: Data Persistence Testing (10 minutes)

### Step 8: Create Test Data in Container

```bash
docker exec -it car-log-python python -c "
import json
from pathlib import Path

# Create test vehicle
test_vehicle = {
    'vehicle_id': 'test-docker-123',
    'make': 'Ford',
    'model': 'Transit',
    'year': 2020,
    'vin': 'WBAXX01234ABC5678',
    'license_plate': 'BA-456CD'
}

# Write to data directory
vehicle_file = Path('/data/vehicles/test-docker-123.json')
vehicle_file.write_text(json.dumps(test_vehicle, indent=2))
print('✓ Test vehicle created:', vehicle_file)
print('✓ File size:', vehicle_file.stat().st_size, 'bytes')
"
```

**What to expect:**
```
✓ Test vehicle created: /data/vehicles/test-docker-123.json
✓ File size: 185 bytes
```

**Success criteria:**
- [ ] No errors
- [ ] File created message shown
- [ ] File size reasonable (~185 bytes)

---

### Step 9: Verify Data Exists Inside Container

```bash
docker exec -it car-log-python ls -lh /data/vehicles/
```

**What to expect:**
```
total 4.0K
-rw-r--r-- 1 root root 185 Nov 20 10:05 test-docker-123.json
```

**Success criteria:**
- [ ] File exists
- [ ] Size matches (~185 bytes)
- [ ] Timestamp is recent

---

### Step 10: Verify Data Exists on Host

```bash
# Check file exists on host machine
ls -lh /home/user/car-log/data/vehicles/test-docker-123.json

# View contents
cat /home/user/car-log/data/vehicles/test-docker-123.json
```

**What to expect:**
```json
{
  "vehicle_id": "test-docker-123",
  "make": "Ford",
  "model": "Transit",
  "year": 2020,
  "vin": "WBAXX01234ABC5678",
  "license_plate": "BA-456CD"
}
```

**Success criteria:**
- [ ] File exists on host machine
- [ ] Content matches what was created
- [ ] JSON is properly formatted
- [ ] Volume mount working correctly

---

### Step 11: Test Persistence After Restart

```bash
# Restart Python container
docker-compose restart car-log-python

# Wait for container to start
sleep 10

# Check if data still exists
docker exec -it car-log-python cat /data/vehicles/test-docker-123.json
```

**What to expect:**
- Data should still be there after restart
- Content unchanged

**Success criteria:**
- [ ] Container restarts successfully
- [ ] Data persists after restart
- [ ] No `.tmp` files remaining (atomic writes work)

**Checkpoint:** Data persistence verified ✓

---

## Part 4: Dependency Verification (10 minutes)

### Step 12: Verify QR Scanning Dependencies

```bash
# Check libzbar0 is installed
docker exec -it car-log-python zbarimg --version
```

**What to expect:**
```
zbarimg 0.23
```

**Success criteria:**
- [ ] Command succeeds (no "command not found")
- [ ] Version shown (0.23 or similar)

---

### Step 13: Verify PDF Processing Dependencies

```bash
# Check poppler-utils is installed
docker exec -it car-log-python pdfinfo --version
```

**What to expect:**
```
pdfinfo version 22.02.0
Copyright 2005-2022 The Poppler Developers - http://poppler.freedesktop.org
```

**Success criteria:**
- [ ] Command succeeds
- [ ] Version shown (22.x or similar)

---

### Step 14: Verify Python Environment

```bash
# Check Python version
docker exec -it car-log-python python --version

# Check installed packages
docker exec -it car-log-python pip list
```

**What to expect:**
```
Python 3.11.x
```

And package list including:
```
mcp           1.x.x
Pillow        10.x.x
pyzbar        0.1.9
pdf2image     1.16.3
requests      2.31.0
...
```

**Success criteria:**
- [ ] Python 3.11.x installed
- [ ] All required packages installed
- [ ] No missing dependencies

---

### Step 15: Verify Node.js Environment

```bash
# Check Node.js version
docker exec -it car-log-geo-routing node --version

# Check npm packages
docker exec -it car-log-geo-routing npm list --depth=0
```

**What to expect:**
```
v18.x.x
```

And packages including:
```
@modelcontextprotocol/sdk
axios
node-cache
```

**Success criteria:**
- [ ] Node.js 18.x installed
- [ ] Required npm packages installed

**Checkpoint:** All dependencies verified ✓

---

## Part 5: Resource Usage Testing (10 minutes)

### Step 16: Check Container Resource Usage (Idle)

```bash
docker stats --no-stream
```

**What to expect:**
```
CONTAINER            CPU %    MEM USAGE / LIMIT     NET I/O       BLOCK I/O
car-log-python       2.5%     150MiB / 4GiB        10kB / 5kB    1MB / 0B
car-log-geo-routing  1.2%     80MiB / 4GiB         5kB / 3kB     500kB / 0B
```

**Success criteria:**
- [ ] Python container: < 200MB memory
- [ ] Node.js container: < 100MB memory
- [ ] CPU usage < 5% when idle
- [ ] Total memory < 300MB

**If memory usage too high:**
- This is normal for first startup (caching)
- Monitor for 5 minutes to see if it stabilizes
- Check for memory leaks: `docker stats` (watch for increasing memory)

---

### Step 17: Test with Load

```bash
# Create 50 test vehicles rapidly to test performance
for i in {1..50}; do
  docker exec -i car-log-python python -c "
import json
from pathlib import Path
import uuid

vid = str(uuid.uuid4())
vehicle = {'vehicle_id': vid, 'make': 'TestCar', 'model': 'LoadTest'}
Path(f'/data/vehicles/{vid}.json').write_text(json.dumps(vehicle))
print(f'Created {vid}')
  " &
done

# Wait for all to complete
wait

echo "Load test complete!"
```

**What to expect:**
- 50 vehicles created in parallel
- Each prints "Created [uuid]"
- Completes in < 30 seconds

**Success criteria:**
- [ ] All 50 files created
- [ ] No file corruption (check JSON is valid)
- [ ] No `.tmp` files remaining
- [ ] Memory usage stable during load

---

### Step 18: Verify Load Test Results

```bash
# Count files created
ls /home/user/car-log/data/vehicles/*.json | wc -l

# Check for temp files (should be 0)
ls /home/user/car-log/data/vehicles/*.tmp 2>/dev/null | wc -l

# Verify random file is valid JSON
cat /home/user/car-log/data/vehicles/test-docker-123.json | python -m json.tool
```

**Success criteria:**
- [ ] File count correct (51: 1 original + 50 from load test)
- [ ] No `.tmp` files (atomic writes work)
- [ ] Random file is valid JSON
- [ ] Container still running (no crashes)

**Checkpoint:** Performance verified ✓

---

## Part 6: Error Handling Testing (10 minutes)

### Step 19: Test Invalid Data Path Handling

```bash
docker exec -it car-log-python python -c "
import os

# Try to write to invalid location (should fail gracefully)
try:
    from pathlib import Path
    Path('/invalid/path/test.json').write_text('test')
    print('❌ ERROR: Should have failed!')
except Exception as e:
    print(f'✓ Graceful error handling: {type(e).__name__}')
"
```

**What to expect:**
```
✓ Graceful error handling: FileNotFoundError
```

**Success criteria:**
- [ ] Error caught gracefully
- [ ] No container crash
- [ ] Clear error type shown

---

### Step 20: Test Container Auto-Restart

```bash
# Kill Python process inside container
docker exec -it car-log-python pkill -9 python

# Wait a moment
sleep 5

# Check if container restarted
docker-compose ps
```

**What to expect:**
```
NAME                STATUS              PORTS
car-log-python      Up 3 seconds        (health: starting)
```

**Success criteria:**
- [ ] Container auto-restarts (restart: unless-stopped policy)
- [ ] Status shows recent "Up" time
- [ ] Health check eventually passes
- [ ] No data corruption

---

### Step 21: Test Missing Environment Variable

```bash
# Check if ANTHROPIC_API_KEY is set
docker exec -it car-log-python printenv ANTHROPIC_API_KEY

# If not set, dashboard-ocr should still start (it's P1 feature)
docker-compose logs dashboard-ocr | grep -i "api key"
```

**What to expect:**
- Either API key shown, or empty/warning
- Dashboard-ocr starts anyway (OCR is P1 feature)

**Success criteria:**
- [ ] Missing optional API key doesn't crash server
- [ ] Warning logged (if applicable)
- [ ] Server continues running

**Checkpoint:** Error handling verified ✓

---

## Part 7: Cleanup (5 minutes)

### Step 22: Stop Containers

```bash
docker-compose down
```

**What to expect:**
```
[+] Running 3/3
 ✔ Container car-log-geo-routing  Removed    0.5s
 ✔ Container car-log-python       Removed    0.8s
 ✔ Network docker_car-log-net     Removed    0.2s
```

**Success criteria:**
- [ ] Both containers stopped
- [ ] Network removed
- [ ] No errors

---

### Step 23: Verify Data Persists After Shutdown

```bash
# Data should still exist on host
ls -lh /home/user/car-log/data/vehicles/ | head -5
```

**What to expect:**
- All vehicle files still there
- test-docker-123.json exists
- Load test files exist

**Success criteria:**
- [ ] Data persists after Docker shutdown
- [ ] Volume mount strategy works correctly

---

### Step 24: Clean Up Test Data

```bash
# Remove test files
rm /home/user/car-log/data/vehicles/test-docker-*.json
rm /home/user/car-log/data/vehicles/*LoadTest*.json 2>/dev/null

# Verify cleanup
ls /home/user/car-log/data/vehicles/
```

**Checkpoint:** Cleanup complete ✓

---

## Summary Checklist

### Phase 1: Build (15 minutes)
- [ ] Python container built successfully
- [ ] Node.js container built successfully

### Phase 2: Startup (10 minutes)
- [ ] Both containers start without errors
- [ ] Health checks pass
- [ ] All 7 MCP servers running
- [ ] No import/module errors

### Phase 3: Data Persistence (10 minutes)
- [ ] Data written from container appears on host
- [ ] Data survives container restart
- [ ] Atomic write pattern works (no .tmp files)
- [ ] Volume mount working correctly

### Phase 4: Dependencies (10 minutes)
- [ ] libzbar0 installed (QR scanning)
- [ ] poppler-utils installed (PDF processing)
- [ ] Python 3.11 installed
- [ ] Node.js 18 installed
- [ ] All Python packages installed
- [ ] All npm packages installed

### Phase 5: Performance (10 minutes)
- [ ] Memory usage acceptable (< 300MB total)
- [ ] CPU usage low when idle (< 5%)
- [ ] Load test passes (50 vehicles)
- [ ] No memory leaks
- [ ] No file corruption

### Phase 6: Error Handling (10 minutes)
- [ ] Graceful error handling
- [ ] Auto-restart works
- [ ] Missing optional env vars don't crash servers

### Phase 7: Cleanup (5 minutes)
- [ ] Containers stop cleanly
- [ ] Data persists after shutdown
- [ ] Test data cleaned up

---

## Overall Test Result

**Mark your result:**

- [ ] ✅ **ALL TESTS PASSED** - Ready for production use
- [ ] ⚠️ **PASSED WITH MINOR ISSUES** - Document issues below
- [ ] ❌ **FAILED** - Critical issues found, needs fixes

---

## Issues Found (if any)

**Document any issues here:**

1. _[Issue description]_
   - **Severity:** Critical / High / Medium / Low
   - **Steps to reproduce:** _[steps]_
   - **Expected:** _[what should happen]_
   - **Actual:** _[what happened]_
   - **Workaround:** _[temporary fix]_

2. _[Issue description]_
   ...

---

## Notes and Observations

**Add any additional notes here:**

- Environment: macOS / Windows / Linux
- Docker version: _[version]_
- Time taken: _[X hours Y minutes]_
- Any warnings or unusual behavior: _[notes]_

---

## Next Steps

### If All Tests Passed ✅
1. Update TASKS.md Track E as ✅ COMPLETE
2. Document this successful test in TEST_EXECUTION_RESULTS.md
3. Ready to proceed with Claude Desktop integration (Track F)

### If Issues Found ⚠️
1. Document issues in TEST_EXECUTION_RESULTS.md
2. File GitHub issues (if applicable)
3. Fix critical issues before proceeding
4. Re-test after fixes

### For Hackathon Demo
1. Include Docker deployment in demo video
2. Show container startup and health checks
3. Demonstrate data persistence
4. Highlight 7 MCP servers running in 2 containers

---

## Troubleshooting Quick Reference

### Container won't start
```bash
docker-compose logs [service-name]
docker-compose ps
docker-compose restart [service-name]
```

### Build fails
```bash
docker-compose build --no-cache [service-name]
```

### Permission errors on /data
```bash
# Dev environment only
chmod -R 777 /home/user/car-log/data
```

### Health check fails
- Wait longer (Python needs 40s, Node.js needs 10s)
- Check logs for startup errors
- Increase `start_period` in docker-compose.yml if needed

### Out of disk space
```bash
docker system prune -a
docker volume prune
```

---

**Test Guide Version:** 1.0
**Last Updated:** November 20, 2025
**Estimated Duration:** 2-3 hours
**Status:** Ready for manual testing
