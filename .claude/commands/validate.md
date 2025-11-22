---
description: Execute the project-specific 5-phase validation workflow.
---

# Validation Protocol

**Context:** Validating `Car Log` (Slovak Tax-Compliant Mileage Logger) using `Python 3.11, Node.js 22, MCP Servers, Pytest`

This validation workflow was automatically generated based on your project's detected configuration.

**Detected Stack:**
- **Languages:** Python 3.11.9, Node.js 22.14.0
- **Frameworks:** MCP SDK, asyncio
- **Testing:** Pytest (70+ tests, 98.6% success rate)
- **Architecture:** 7 headless MCP servers (6 Python, 1 Node.js)

---

## Phase 1: Static Analysis (Linting)

**Purpose:** Catch syntax errors, code quality issues, and enforce coding standards.

**Status:** ⚠️ Linting tools available but currently commented out in requirements.txt

**Recommended Commands:**

```bash
# Option 1: Using Ruff (fast, recommended)
pip install ruff
ruff check mcp-servers/ tests/

# Option 2: Using Flake8 (traditional)
pip install flake8
flake8 mcp-servers/ tests/ --max-line-length=120 --exclude=node_modules,__pycache__
```

**What to check:**
- No syntax errors or undefined variables
- No unused imports
- Code follows Python best practices (PEP 8)
- No common anti-patterns

**Action Required:**
Currently, linting tools (black, mypy, ruff) are commented out in requirements.txt.
Consider uncommenting them for production use:
```bash
pip install black mypy ruff
```

---

## Phase 2: Type Safety (Type Checking)

**Purpose:** Ensure type correctness and catch type-related bugs before runtime.

**Status:** ⚠️ MyPy available but not currently installed

**Command:**
```bash
# Install MyPy
pip install mypy

# Run type checking on MCP servers
mypy mcp-servers/ --ignore-missing-imports
```

**What to check:**
- No type errors in function signatures
- Proper type annotations for critical functions
- No unsafe `Any` types without justification

**Note:** Type checking is optional for MVP but recommended for production deployment.

---

## Phase 3: Code Style (Formatting)

**Purpose:** Ensure consistent code formatting across the codebase.

**Status:** ⚠️ Black formatter available but not currently installed

**Command:**
```bash
# Install Black
pip install black

# Check formatting (dry run)
black --check mcp-servers/ tests/

# Auto-fix formatting
black mcp-servers/ tests/
```

**What to check:**
- All Python files follow consistent formatting
- Line length within reasonable limits (88 chars for Black, 120 for Flake8)
- No trailing whitespace or inconsistent indentation

---

## Phase 4: Unit Tests (Logic Verification) - CRITICAL

**Purpose:** Verify that individual units of code work as expected.

**Command:**
```bash
# Run all pytest tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=mcp-servers --cov-report=term-missing
```

**What to check:**
- ✅ All unit tests pass (currently 70+ tests, 98.6% success rate)
- Test coverage for critical modules:
  - `car-log-core`: Vehicle, Checkpoint, Template CRUD
  - `trip-reconstructor`: Template matching (GPS 70% + Address 30%)
  - `validation`: 4 validation algorithms
  - `ekasa-api`: Receipt fetching, QR scanning
  - `geo-routing`: Geocoding, route calculation
  - `dashboard-ocr`: EXIF extraction
  - `report-generator`: CSV generation

**Known Issues:**
- ⚠️ Trip CRUD tools not implemented (4 tools missing - see TASKS.md A6)
- Tests depending on trip storage will fail until implemented

---

## Phase 5: End-to-End Tests (E2E) - CRITICAL

**Purpose:** Verify that the entire application works correctly from a user perspective.

**Status:** ⚠️ No dedicated E2E framework detected, but integration tests exist

**Current Integration Tests:**
```bash
# Run integration checkpoint test (Day 7 milestone)
python tests/integration_checkpoint_day7.py

# Run specific integration test suites
pytest tests/ekasa_api/test_integration.py -v
```

**What to check:**
- Receipt → Checkpoint workflow (E-Kasa API integration)
- Gap detection → Template matching flow
- Geocoding with ambiguity handling
- Slovak compliance validation (VIN format, L/100km fuel efficiency)

**⚠️ MISSING E2E COVERAGE:**

This project does not have full end-to-end testing for:
1. **Claude Desktop Skills integration** (manual testing required)
2. **Complete workflow:** Receipt → Checkpoint → Gap → Template Matching → **Trip Creation** → Report
3. **Cross-server orchestration** (all 7 MCP servers working together)

**Recommended Manual Testing:**

1. **Receipt Processing:**
   - Upload fuel receipt with QR code
   - Verify e-Kasa API fetch (60s timeout)
   - Check checkpoint creation with GPS coordinates

2. **Template Matching:**
   - Create templates with GPS coordinates
   - Detect gaps between checkpoints
   - Verify hybrid matching (GPS 70% + Address 30%)
   - Confirm confidence scores >= 70%

3. **Trip Reconstruction (BLOCKED):**
   - ❌ Cannot save reconstruction proposals as trips
   - ❌ Missing: `create_trip`, `create_trips_batch`, `list_trips`, `get_trip`
   - See TASKS.md section A6 for implementation tasks

4. **Report Generation:**
   - Generate CSV reports
   - Verify Slovak compliance fields (VIN, driver name, L/100km)
   - Check validation algorithm results

**To Add Playwright/Cypress (Future):**
Since this is a conversational interface through Claude Desktop, traditional E2E frameworks are not applicable. Instead, consider:
- MCP Inspector for debugging server communication
- Automated Claude Desktop skill testing (if SDK available)
- Postman/Insomnia for MCP server endpoint testing

---

# Execution Instructions

**Run these phases sequentially:**

1. ✅ **Execute Phase 4 (Unit Tests) - START HERE**
   ```bash
   pytest tests/ -v
   ```
   - This is your **PRIMARY validation** (70+ tests, proven working)
   - If tests fail, STOP and fix the failures

2. 🔧 **Execute Phase 1 (Linting) - OPTIONAL**
   ```bash
   pip install ruff
   ruff check mcp-servers/ tests/
   ```
   - If linting errors found, review and fix
   - Not blocking for MVP

3. 🔧 **Execute Phase 2 (Type Safety) - OPTIONAL**
   ```bash
   pip install mypy
   mypy mcp-servers/ --ignore-missing-imports
   ```
   - If type errors found, review and fix
   - Not blocking for MVP

4. 🔧 **Execute Phase 3 (Code Style) - OPTIONAL**
   ```bash
   pip install black
   black --check mcp-servers/ tests/
   ```
   - If formatting issues found, run `black mcp-servers/ tests/` to auto-fix

5. ✅ **Execute Phase 5 (Integration Tests)**
   ```bash
   python tests/integration_checkpoint_day7.py
   pytest tests/ekasa_api/test_integration.py -v
   ```
   - If integration tests fail, STOP and investigate

6. 🧪 **Manual E2E Testing** (Claude Desktop)
   - Test Receipt → Checkpoint workflow
   - Test Template matching
   - **Note:** Trip creation is currently blocked (see TASKS.md A6)

---

**On Success:**
Report: "✅ All validation phases passed! Unit tests confirm 98.6% functionality. Ready for integration testing."

**On Failure:**
Report the specific phase that failed with:
- The command that was run
- The error output
- Suggested fixes (refer to CLAUDE.md for implementation guidance)

---

# Additional Validation (Project-Specific)

## Slovak Compliance Validation

**Critical checks:**
```bash
# Verify VIN validation (17 chars, no I/O/Q)
pytest tests/test_car_log_core.py::test_vehicle_vin_validation -v

# Verify L/100km fuel efficiency format (not km/L)
pytest tests/test_validation.py -v -k "efficiency"

# Verify Slovak receipt processing
pytest tests/ekasa_api/test_fuel_detector.py -v
```

## MCP Server Health Check

**Verify all 7 servers are discoverable:**
```bash
# Check car-log-core tools
python -c "from mcp_servers.car_log_core import tools; print('✅ car-log-core OK')"

# Check geo-routing (Node.js)
cd mcp-servers/geo-routing && node index.js --help

# Full server list:
# 1. car-log-core (Python) - CRUD operations
# 2. trip-reconstructor (Python) - Template matching
# 3. geo-routing (Node.js) - Geocoding, routing
# 4. ekasa-api (Python) - Slovak receipts
# 5. dashboard-ocr (Python) - EXIF extraction
# 6. validation (Python) - 4 algorithms
# 7. report-generator (Python) - CSV/PDF reports
```

## Data Integrity Validation

**Test atomic write pattern (crash safety):**
```bash
pytest tests/test_car_log_core.py::test_atomic_write_crash_safety -v
```

## Performance Benchmarks

**Template matching performance:**
```bash
# Must complete in < 2 seconds with 100+ templates
pytest tests/ -v -k "performance"
```

---

# Pro Tips

1. **Before Committing:**
   ```bash
   pytest tests/ -v && echo "✅ Tests passed, safe to commit"
   ```

2. **Quick Smoke Test:**
   ```bash
   pytest tests/test_car_log_core.py tests/test_validation.py -v
   ```

3. **Install All Dev Tools:**
   ```bash
   pip install black mypy ruff pytest pytest-asyncio pytest-cov
   ```

4. **Full Validation Pipeline:**
   ```bash
   ruff check mcp-servers/ tests/ && \
   mypy mcp-servers/ --ignore-missing-imports && \
   black --check mcp-servers/ tests/ && \
   pytest tests/ -v --cov=mcp-servers
   ```

---

# Next Steps

1. **Run validation:** `/validate` (this command)
2. **If tests fail:** Check CLAUDE.md for implementation guidance
3. **Missing Trip CRUD:** See TASKS.md section A6 (4-6 hour task)
4. **Commit this file:** `git add .claude/commands/validate.md`

**Recommendation:** Add linting tools to requirements.txt for production:
```txt
# Uncomment these lines in requirements.txt:
black>=23.0.0  # Code formatting
mypy>=1.5.0    # Type checking
ruff>=0.1.0    # Fast linter
```
