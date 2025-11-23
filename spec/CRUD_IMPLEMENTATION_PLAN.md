# CRUD Implementation Plan - Complete Update Cascade

**Date:** 2025-11-23
**Status:** Planning
**Scope:** Implement missing CRUD operations + update all impacted files

---

## Executive Summary

**Missing Operations:** 11 total
- Checkpoint: update, delete (2)
- Trip: create, create_batch, get, list, update, delete (6)
- Template: update, delete, get_single (3)

**Impacted Files:** ~35 files across:
- MCP server implementations (7 files)
- MCP tool specifications (1 file)
- Skills documentation (6 skills × 2 files = 12 files)
- Deployment scripts (3 files)
- Testing files (5 files)
- Project documentation (7 files)

**Estimated Effort:** 12-16 hours total

---

## Phase 1: Core Implementation (6-8 hours)

### 1.1 MCP Server: car-log-core Updates

**File:** `mcp-servers/car-log-core/src/tools.py` (or equivalent)

**Implementations needed:**

#### A. Checkpoint Operations (2 hours)

```python
# 1. update_checkpoint
async def update_checkpoint(checkpoint_id: str, updates: dict) -> dict:
    """
    Update checkpoint fields.

    Args:
        checkpoint_id: UUID of checkpoint
        updates: Dict of fields to update

    Returns:
        Updated checkpoint object

    Raises:
        NotFoundError: Checkpoint doesn't exist
        ValidationError: Invalid update data
    """
    pass

# 2. delete_checkpoint
async def delete_checkpoint(checkpoint_id: str, cascade: bool = False) -> dict:
    """
    Delete checkpoint.

    Args:
        checkpoint_id: UUID of checkpoint
        cascade: If true, delete dependent trips

    Returns:
        Success message with warnings

    Raises:
        NotFoundError: Checkpoint doesn't exist
        DependencyError: Trips reference this checkpoint (if cascade=False)
    """
    pass
```

**Files to modify:**
- [ ] `mcp-servers/car-log-core/src/tools.py`
- [ ] `mcp-servers/car-log-core/src/checkpoint_manager.py` (if exists)
- [ ] `mcp-servers/car-log-core/src/validation.py`
- [ ] `mcp-servers/car-log-core/tests/test_checkpoint_crud.py`

#### B. Trip Operations (4 hours)

```python
# 1. create_trip
async def create_trip(trip_data: dict) -> dict:
    """Create single trip manually."""
    pass

# 2. create_trips_batch
async def create_trips_batch(trips: list[dict]) -> dict:
    """Create multiple trips (from reconstruction)."""
    pass

# 3. get_trip
async def get_trip(trip_id: str) -> dict:
    """Get single trip by ID."""
    pass

# 4. list_trips
async def list_trips(vehicle_id: str, filters: dict) -> dict:
    """List trips with filtering (date range, purpose, etc.)."""
    pass

# 5. update_trip
async def update_trip(trip_id: str, updates: dict) -> dict:
    """Update trip fields."""
    pass

# 6. delete_trip
async def delete_trip(trip_id: str) -> dict:
    """Delete trip."""
    pass
```

**Files to modify:**
- [ ] `mcp-servers/car-log-core/src/tools.py`
- [ ] `mcp-servers/car-log-core/src/trip_manager.py` (CREATE NEW)
- [ ] `mcp-servers/car-log-core/src/validation.py`
- [ ] `mcp-servers/car-log-core/tests/test_trip_crud.py` (CREATE NEW)

#### C. Template Operations (1 hour)

```python
# 1. get_template (single)
async def get_template(template_id: str) -> dict:
    """Get single template by ID."""
    pass

# 2. update_template
async def update_template(template_id: str, updates: dict) -> dict:
    """Update template fields."""
    pass

# 3. delete_template
async def delete_template(template_id: str) -> dict:
    """Delete template."""
    pass
```

**Files to modify:**
- [ ] `mcp-servers/car-log-core/src/tools.py`
- [ ] `mcp-servers/car-log-core/src/template_manager.py` (if exists)
- [ ] `mcp-servers/car-log-core/tests/test_template_crud.py`

#### D. File Storage Updates (1 hour)

**Atomic write pattern for updates:**

```python
def atomic_update_json(file_path: Path, update_fn: callable):
    """
    Atomically update JSON file.

    Args:
        file_path: Path to JSON file
        update_fn: Function that takes current data and returns updated data
    """
    # 1. Read current
    with open(file_path, 'r') as f:
        current_data = json.load(f)

    # 2. Apply update
    updated_data = update_fn(current_data)

    # 3. Atomic write
    atomic_write_json(file_path, updated_data)
```

**Files to modify:**
- [ ] `mcp-servers/car-log-core/src/storage.py` (or equivalent)

---

## Phase 2: Specifications Update (1 hour)

### 2.1 MCP API Specifications

**File:** `spec/07-mcp-api-specifications.md`

**Add new tool definitions:**

- [ ] Tool 1.8a: `update_checkpoint`
- [ ] Tool 1.8b: `delete_checkpoint`
- [ ] Tool 1.9: `create_trip`
- [ ] Tool 1.10: `create_trips_batch`
- [ ] Tool 1.11: `get_trip`
- [ ] Tool 1.12: `list_trips`
- [ ] Tool 1.13: `update_trip`
- [ ] Tool 1.14: `delete_trip`
- [ ] Tool 1.15: `get_template`
- [ ] Tool 1.16: `update_template`
- [ ] Tool 1.17: `delete_template`

**Update summary table:**
```diff
- | `car-log-core` | CRUD operations | P0 | 10 implemented, 4-6 trip tools missing | ⚠️ PARTIAL |
+ | `car-log-core` | CRUD operations | P0 | 21 tools | ✅ COMPLETE |
```

**Files to modify:**
- [ ] `spec/07-mcp-api-specifications.md`

---

## Phase 3: Skills Documentation (3 hours)

### 3.1 Update All Skills References

**For each skill, update `references/mcp-tools.md`:**

#### Checkpoint-from-Receipt Skill

**File:** `claude_skills/checkpoint-from-receipt/references/mcp-tools.md`

**Add sections:**
```markdown
## car-log-core.update_checkpoint

**Purpose:** Update checkpoint to fix mistakes

**Request:**
```json
{
  "checkpoint_id": "uuid-5678",
  "updates": {
    "odometer_km": 125500,
    "driver_name": "Corrected Name"
  }
}
```

## car-log-core.delete_checkpoint

**Purpose:** Delete erroneous checkpoint

**Request:**
```json
{
  "checkpoint_id": "uuid-5678",
  "cascade": false
}
```
```

**Files to modify:**
- [ ] `claude_skills/checkpoint-from-receipt/references/mcp-tools.md`
- [ ] `claude_skills/checkpoint-from-receipt/references/guide.md` (add error correction workflow)

#### Trip Reconstruction Skill

**File:** `claude_skills/trip-reconstruction/references/mcp-tools.md`

**Add sections:**
```markdown
## car-log-core.create_trips_batch

**Purpose:** Save approved trip reconstruction proposals

**Request:**
```json
{
  "vehicle_id": "uuid-1234",
  "trips": [
    {
      "start_checkpoint_id": "uuid-4567",
      "end_checkpoint_id": "uuid-5678",
      "driver_name": "Ján Novák",
      "trip_start_datetime": "2025-10-25T08:00:00Z",
      "trip_end_datetime": "2025-10-25T12:30:00Z",
      "trip_start_location": "Bratislava",
      "trip_end_location": "Košice",
      "distance_km": 410,
      "purpose": "Business",
      "business_description": "Warehouse pickup",
      "reconstruction_method": "template",
      "template_id": "uuid-tmpl-1",
      "confidence_score": 0.92
    }
  ]
}
```

## car-log-core.update_trip

**Purpose:** Fix trip data errors

## car-log-core.delete_trip

**Purpose:** Remove incorrect trip
```

**Files to modify:**
- [ ] `claude_skills/trip-reconstruction/references/mcp-tools.md`
- [ ] `claude_skills/trip-reconstruction/references/guide.md` (add save workflow)
- [ ] `claude_skills/trip-reconstruction/Skill.md` (update step 6 - currently says NOT IMPLEMENTED)

#### Report Generation Skill

**File:** `claude_skills/report-generation/references/mcp-tools.md`

**Add section:**
```markdown
## car-log-core.list_trips

**Purpose:** Get trips for report generation

**Request:**
```json
{
  "vehicle_id": "uuid-1234",
  "filters": {
    "start_date": "2025-11-01",
    "end_date": "2025-11-30",
    "purpose": "Business"
  }
}
```

**Response:**
```json
{
  "success": true,
  "trips": [ /* array of trip objects */ ],
  "total_distance_km": 4920,
  "total_fuel_liters": 418.2
}
```
```

**Files to modify:**
- [ ] `claude_skills/report-generation/references/mcp-tools.md`
- [ ] `claude_skills/report-generation/references/guide.md`

#### Template Creation Skill

**Files to modify:**
- [ ] `claude_skills/template-creation/references/mcp-tools.md` (add update/delete operations)
- [ ] `claude_skills/template-creation/references/guide.md`

#### Data Validation Skill

**Files to modify:**
- [ ] `claude_skills/data-validation/references/mcp-tools.md` (reference trip operations)

#### Vehicle Setup Skill

**Files to modify:**
- [ ] `claude_skills/vehicle-setup/references/mcp-tools.md` (already has update_vehicle, add note about delete)

### 3.2 Repackage All Skills

**After documentation updates:**

```bash
cd claude_skills
python package_skills.py --clean --all
```

**Files to update:**
- [ ] `claude_skills/dist/*.zip` (6 files)

---

## Phase 4: Deployment Scripts (2 hours)

### 4.1 Update MCP Server Deployment

**Files:** `deployment/scripts/deploy-*.sh|bat`

**Changes needed:**
1. Ensure car-log-core deployment includes new trip_manager.py
2. Update dependency requirements if needed
3. Verify file permissions for new modules

**Files to modify:**
- [ ] `deployment/scripts/deploy-windows.bat`
- [ ] `deployment/scripts/deploy-macos.sh`
- [ ] `deployment/scripts/deploy-linux.sh`

### 4.2 Update Verification Script

**File:** `deployment/scripts/verify-deployment.bat`

**Add checks:**
```bash
# Verify new MCP tools are discoverable
echo "Checking car-log-core tools..."
mcp list-tools car-log-core | grep -E "update_checkpoint|delete_checkpoint|create_trip|list_trips"

# Expected: 11 new tools discovered
```

**Files to modify:**
- [ ] `deployment/scripts/verify-deployment.bat`
- [ ] `deployment/scripts/verify-deployment.sh` (create if doesn't exist)

---

## Phase 5: Testing (3 hours)

### 5.1 Unit Tests

**Create/Update test files:**

```python
# tests/test_checkpoint_update_delete.py
def test_update_checkpoint_odometer():
    """Test updating odometer reading."""
    pass

def test_update_checkpoint_validation():
    """Test update validation (odometer can't decrease)."""
    pass

def test_delete_checkpoint_with_dependencies():
    """Test cascade behavior."""
    pass

# tests/test_trip_crud.py
def test_create_trip():
    """Test single trip creation."""
    pass

def test_create_trips_batch():
    """Test batch creation from reconstruction."""
    pass

def test_list_trips_filtering():
    """Test date range and purpose filters."""
    pass

def test_update_trip():
    """Test trip updates."""
    pass

def test_delete_trip():
    """Test trip deletion."""
    pass
```

**Files to create/modify:**
- [ ] `mcp-servers/car-log-core/tests/test_checkpoint_update_delete.py` (NEW)
- [ ] `mcp-servers/car-log-core/tests/test_trip_crud.py` (NEW)
- [ ] `mcp-servers/car-log-core/tests/test_template_update_delete.py` (NEW)
- [ ] `claude_skills/TESTING_F1-F3.md` (update with new scenarios)
- [ ] `claude_skills/TESTING_F4-F6.md` (update with new scenarios)

### 5.2 Integration Tests

**Update integration test scenarios:**

**File:** `claude_skills/INTEGRATION_TESTING.md`

**Add scenarios:**
1. Receipt → Checkpoint → Fix Odometer → Gap Detection
2. Receipt → Checkpoint → Delete Duplicate → Gap Detection
3. Gap → Template Match → Save Trips → List Trips → Generate Report
4. Template → Update GPS → Match Again
5. Trip → Update Business Description → Regenerate Report

**Files to modify:**
- [ ] `claude_skills/INTEGRATION_TESTING.md`

### 5.3 Manual Test Checklist

**File:** `claude_skills/MANUAL_TEST_CHECKLIST.md`

**Add test cases:**
- [ ] Update checkpoint odometer
- [ ] Update checkpoint driver name
- [ ] Delete checkpoint without dependencies
- [ ] Delete checkpoint with trips (cascade warning)
- [ ] Create trip manually
- [ ] Save trip reconstruction batch
- [ ] List trips for date range
- [ ] Update trip business description
- [ ] Delete trip
- [ ] Update template GPS coordinates
- [ ] Delete unused template

**Files to modify:**
- [ ] `claude_skills/MANUAL_TEST_CHECKLIST.md`

---

## Phase 6: Project Documentation (2 hours)

### 6.1 Main Documentation Files

**Files to update:**

#### CLAUDE.md

**Current issue block:**
```markdown
## ⚠️ CRITICAL STATUS UPDATE

**BLOCKING ISSUE:** Trip CRUD tools are documented in specifications but **NOT IMPLEMENTED**.
```

**After implementation:**
```markdown
## ✅ STATUS UPDATE

**COMPLETE:** All CRUD operations implemented and tested.
- Checkpoint: Create, Read, Update, Delete ✅
- Trip: Create, CreateBatch, Read, List, Update, Delete ✅
- Template: Create, Read, List, Update, Delete ✅
- Vehicle: Create, Read, List, Update ✅
```

**Files to modify:**
- [ ] `CLAUDE.md` (remove BLOCKING ISSUE section)
- [ ] `TASKS.md` (mark A6 as complete)
- [ ] `README.md` (update status)

#### Specifications

**Files to modify:**
- [ ] `spec/01-product-overview.md` (update implementation status)
- [ ] `spec/04-data-model.md` (add update/delete patterns)
- [ ] `spec/06-mcp-architecture-v2.md` (update tool count)
- [ ] `spec/08-implementation-plan.md` (mark tasks complete)
- [ ] `spec/IMPLEMENTATION_READY.md` (update status)
- [ ] `spec/IMPLEMENTATION_SUMMARY.md` (update with new tools)

### 6.2 Skills Documentation

**Files to modify:**
- [ ] `claude_skills/README.md` (update with new capabilities)
- [ ] `claude_skills/BEST_PRACTICES.md` (add error correction patterns)
- [ ] `claude_skills/DEMO_SCENARIO.md` (add error correction demo)
- [ ] `claude_skills/TROUBLESHOOTING.md` (add update/delete troubleshooting)

---

## Phase 7: Packaging & Distribution (1 hour)

### 7.1 Update Packaging Documentation

**Files to modify:**
- [ ] `claude_skills/PACKAGING.md` (note new MCP tool requirements)
- [ ] `claude_skills/DEPLOYMENT.md` (update prerequisites)
- [ ] `claude_skills/INSTALLATION.md` (update installation steps)

### 7.2 Create Migration Guide

**File:** `spec/CRUD_MIGRATION_GUIDE.md` (NEW)

**Content:**
```markdown
# CRUD Implementation Migration Guide

## For Users

**What's new:**
- You can now fix mistakes in checkpoints
- You can now save reconstructed trips
- You can now generate reports

**Breaking changes:**
- None (purely additive)

## For Developers

**New MCP tools available:**
- 11 new car-log-core tools
- See spec/07-mcp-api-specifications.md for schemas

**Updated skills:**
- All 6 skills repackaged with new documentation
- Reinstall from claude_skills/dist/
```

**Files to create:**
- [ ] `spec/CRUD_MIGRATION_GUIDE.md` (NEW)

---

## Implementation Checklist Summary

### MCP Server Implementation (6-8 hours)
- [ ] 2 checkpoint operations
- [ ] 6 trip operations
- [ ] 3 template operations
- [ ] Storage layer updates
- [ ] Validation updates
- [ ] Unit tests (15+ tests)

### Documentation Updates (5-6 hours)
- [ ] 1 specification file (spec/07-mcp-api-specifications.md)
- [ ] 12 skills reference files (6 skills × 2 files)
- [ ] 7 project documentation files
- [ ] 5 testing files
- [ ] 1 migration guide

### Deployment & Scripts (2 hours)
- [ ] 3 deployment scripts
- [ ] 1 verification script
- [ ] 6 skill ZIP packages

### Testing & Validation (3 hours)
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing
- [ ] End-to-end workflow validation

---

## Total Effort Estimate

| Phase | Hours | Priority |
|-------|-------|----------|
| Core Implementation | 6-8 | P0 |
| Specifications | 1 | P0 |
| Skills Docs | 3 | P0 |
| Deployment | 2 | P1 |
| Testing | 3 | P0 |
| Project Docs | 2 | P1 |
| Packaging | 1 | P1 |
| **Total** | **18-20** | - |

---

## Critical Path

**Must complete in order:**

1. ✅ Core implementation (Phase 1)
2. ✅ Specifications update (Phase 2)
3. ✅ Unit tests pass (Phase 5.1)
4. ✅ Skills docs update (Phase 3)
5. ✅ Integration tests pass (Phase 5.2)
6. ✅ Deployment scripts (Phase 4)
7. ✅ Project docs (Phase 6)
8. ✅ Package & distribute (Phase 7)

---

## Risk Assessment

### High Risk
- **File storage atomicity** - Update operations must be crash-safe
- **Cascade deletes** - Must handle dependencies correctly
- **Validation** - Update operations must re-validate constraints

### Medium Risk
- **Documentation drift** - 35+ files to update consistently
- **Testing coverage** - Need comprehensive test suite
- **Backward compatibility** - Ensure old data still works

### Low Risk
- **Breaking changes** - All operations are additive
- **Performance** - File-based storage should handle updates fine

---

## Success Criteria

- [ ] All 11 new MCP tools discoverable
- [ ] All unit tests pass (>90% coverage)
- [ ] Integration tests pass (end-to-end workflow)
- [ ] Skills documentation accurate and complete
- [ ] Deployment scripts updated and tested
- [ ] Manual testing checklist completed
- [ ] All 6 skills repackaged and working in Claude Desktop
- [ ] User can complete full workflow: Receipt → Checkpoint → Fix Error → Gap → Match → Save Trips → Report

---

## Next Steps

1. **Review this plan** with team/stakeholders
2. **Create GitHub issues** for each phase
3. **Assign ownership** for implementation
4. **Set sprint goals** (recommend 2-week sprint)
5. **Begin Phase 1** (Core Implementation)

---

**Status:** Planning complete, ready for implementation
**Document:** CRUD_IMPLEMENTATION_PLAN.md
**Date:** 2025-11-23
**Estimated completion:** 2-3 weeks (part-time) or 3-4 days (full-time)
