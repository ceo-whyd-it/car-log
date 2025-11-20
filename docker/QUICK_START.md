# Docker Testing - Quick Start

**Time Required:** 2-3 hours
**Prerequisites:** Docker Desktop installed and running

---

## TL;DR

```bash
# 1. Navigate to docker directory
cd /home/user/car-log/docker

# 2. Create environment file
cp .env.example .env

# 3. Build containers
docker-compose build

# 4. Start containers
docker-compose up -d

# 5. Check status
docker-compose ps
docker-compose logs -f

# 6. Follow full guide
# Open: MANUAL_TEST_GUIDE.md
```

---

## Before You Start

### Install Docker Desktop
- macOS: https://docs.docker.com/desktop/install/mac-install/
- Windows: https://docs.docker.com/desktop/install/windows-install/
- Linux: https://docs.docker.com/desktop/install/linux-install/

### Verify Installation
```bash
docker --version          # Should show: Docker version 20.10+
docker-compose --version  # Should show: Docker Compose version 2.0+
```

### Start Docker Desktop
- Open Docker Desktop application
- Wait for "Docker Desktop is running" status
- Check system tray/menu bar for Docker icon

---

## Testing Process (Overview)

### Phase 1: Build (15 minutes)
```bash
cd /home/user/car-log/docker
docker-compose build
```
**Expected:** Both containers build without errors

### Phase 2: Start (5 minutes)
```bash
docker-compose up -d
docker-compose ps
```
**Expected:** Both containers show "Up" and "(healthy)" status

### Phase 3: Verify (5 minutes)
```bash
docker-compose logs -f
```
**Expected:** All 7 MCP servers start without errors

### Phase 4: Test (60 minutes)
Follow: `MANUAL_TEST_GUIDE.md` Parts 3-6

### Phase 5: Document (30 minutes)
Fill in: `TEST_EXECUTION_RESULTS.md`

### Phase 6: Cleanup (5 minutes)
```bash
docker-compose down
```

---

## What's Being Tested

**7 MCP Servers in 2 Containers:**
- ✅ car-log-core (CRUD operations)
- ✅ trip-reconstructor (Template matching)
- ✅ validation (Data validation)
- ✅ ekasa-api (Slovak receipts)
- ✅ dashboard-ocr (EXIF extraction)
- ✅ report-generator (CSV reports)
- ✅ geo-routing (Geocoding/routing)

**Key Features:**
- Data persistence (volume mounts)
- Health checks
- Auto-restart on crash
- QR scanning (libzbar0)
- PDF processing (poppler-utils)
- Resource usage (< 300MB)

---

## Success Criteria

**You need to verify:**
- [x] Both containers build successfully
- [x] Both containers start and become healthy
- [x] All 7 MCP servers running (check logs)
- [x] Data persists after container restart
- [x] QR scanning dependencies installed
- [x] PDF processing dependencies installed
- [x] Resource usage < 300MB total
- [x] No file corruption (atomic writes work)

**If all ✅ above → PASS → Mark Track E as complete**

---

## Guides Available

**1. MANUAL_TEST_GUIDE.md** ⭐ START HERE
- Step-by-step instructions (7 parts, 22 steps)
- Copy-paste commands
- Expected outputs
- Validation checklists
- Troubleshooting

**2. TEST_EXECUTION_RESULTS.md** 📝 DOCUMENT HERE
- Template for test results
- Pass/fail tracking
- Issue documentation
- Approval workflow

**3. DOCKER_CONFIG_VERIFICATION.md** 📄 REFERENCE
- Configuration verification
- Technical details
- Validation results

**4. TRACK_E_COMPLETION_SUMMARY.md** 📊 OVERVIEW
- What was done
- What you need to do
- Impact on project
- Recommendations

**5. README.md** 📖 DOCUMENTATION
- Architecture overview
- Commands reference
- Troubleshooting
- Production deployment

---

## Quick Troubleshooting

### Build fails
```bash
docker-compose build --no-cache
```

### Container won't start
```bash
docker-compose logs [service-name]
docker-compose restart [service-name]
```

### Permission errors
```bash
chmod -R 777 /home/user/car-log/data
```

### Clean slate
```bash
docker-compose down
docker system prune -a
docker-compose build
docker-compose up -d
```

---

## Time Breakdown

| Phase | Activity | Time |
|-------|----------|------|
| Setup | Install Docker Desktop | 10 min |
| Build | Build containers | 15 min |
| Start | Start containers | 5 min |
| Test | Data persistence | 10 min |
| Test | Dependencies | 10 min |
| Test | Performance | 10 min |
| Test | Error handling | 10 min |
| Document | Fill TEST_EXECUTION_RESULTS.md | 30 min |
| Cleanup | Stop containers | 5 min |
| **Total** | | **~2 hours** |

Add 1 hour buffer for issues = **2-3 hours total**

---

## After Testing

### If All Tests Pass ✅
1. Update TASKS.md Track E2 as ✅ COMPLETE
2. Mark Track E as fully complete
3. Proceed to Track F (Claude Desktop skills)

### If Issues Found ⚠️
1. Document in TEST_EXECUTION_RESULTS.md
2. Fix critical issues
3. Re-test

### Update TASKS.md
```markdown
### E2: Docker Testing (1 hour)

**Status:** ✅ COMPLETE
**Test Date:** [Your date]
**Result:** [PASS/PASS WITH ISSUES/FAIL]
```

---

## Need Help?

**Review these files:**
1. MANUAL_TEST_GUIDE.md - Detailed step-by-step
2. DOCKER_CONFIG_VERIFICATION.md - Configuration details
3. README.md - Troubleshooting section

**Check Docker logs:**
```bash
docker-compose logs -f car-log-python
docker-compose logs -f geo-routing
```

**Docker commands:**
```bash
docker-compose ps          # Container status
docker stats --no-stream   # Resource usage
docker system df           # Disk usage
```

---

## Ready to Start?

**Your path:**
1. ✅ Read this QUICK_START.md (you are here)
2. ⏳ Install Docker Desktop (if needed)
3. ⏳ Open MANUAL_TEST_GUIDE.md
4. ⏳ Follow steps sequentially
5. ⏳ Document in TEST_EXECUTION_RESULTS.md
6. ⏳ Update TASKS.md

**Time commitment:** 2-3 hours

**Current status:** Track E - 90% complete (configuration done, testing pending)

**After completion:** Track E - 100% complete → Ready for Track F

---

**Good luck! 🚀**

---

**Document Version:** 1.0
**Created:** November 20, 2025
**Purpose:** Quick reference for Docker testing
**Full Guide:** See MANUAL_TEST_GUIDE.md
