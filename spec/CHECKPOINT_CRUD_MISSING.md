# Missing Checkpoint CRUD Operations

**Date:** 2025-11-23
**Issue:** Update and Delete operations missing for checkpoints
**Impact:** Users cannot correct mistakes in checkpoint data

## Current State

**Implemented:**
- ✅ `car-log-core.create_checkpoint` - Create new checkpoint
- ✅ `car-log-core.get_checkpoint` - Read single checkpoint
- ✅ `car-log-core.list_checkpoints` - Read multiple checkpoints

**Missing:**
- ❌ `car-log-core.update_checkpoint` - Update existing checkpoint
- ❌ `car-log-core.delete_checkpoint` - Delete checkpoint

## Use Cases for Update

1. **Fix odometer reading** - User entered wrong value
2. **Correct GPS coordinates** - EXIF data was inaccurate
3. **Update driver name** - Wrong driver initially recorded
4. **Change fuel amount** - Receipt data was misread
5. **Fix timestamp** - Clock was wrong on camera

## Proposed Tool: `update_checkpoint`

### Input Schema

```json
{
  "checkpoint_id": "uuid-5678",
  "updates": {
    "odometer_km": 125500,
    "location": {
      "coords": {
        "latitude": 48.1500,
        "longitude": 17.1100
      },
      "address": "Corrected address"
    },
    "driver_name": "Corrected Name",
    "receipt": {
      "fuel_liters": 53.0
    }
  }
}
```

### Output Schema

```json
{
  "success": true,
  "checkpoint": {
    "checkpoint_id": "uuid-5678",
    "updated_at": "2025-11-23T12:00:00Z",
    "updated_fields": ["odometer_km", "location", "driver_name"]
  },
  "message": "Checkpoint updated successfully"
}
```

### Validation Rules

1. **Checkpoint must exist** - Return error if not found
2. **Odometer validation** - Cannot decrease relative to previous checkpoints
3. **Partial updates** - Only specified fields are updated
4. **Preserve history** - Consider keeping audit log of changes
5. **Cascade validation** - Re-validate dependent trips if checkpoint changes

## Proposed Tool: `delete_checkpoint`

### Input Schema

```json
{
  "checkpoint_id": "uuid-5678",
  "cascade": false
}
```

### Output Schema

```json
{
  "success": true,
  "message": "Checkpoint deleted successfully",
  "warnings": [
    "2 trips reference this checkpoint and may need reconstruction"
  ]
}
```

### Validation Rules

1. **Checkpoint must exist** - Return error if not found
2. **Check dependencies** - Warn if trips reference this checkpoint
3. **Cascade option** - If true, delete dependent trips
4. **File cleanup** - Remove checkpoint file from storage

## Implementation Priority

**Priority:** P0 (Critical for MVP)

**Why:**
- Users WILL make mistakes entering data
- No way to correct errors without update/delete
- Breaks user trust if they can't fix mistakes
- Common operations in any CRUD system

## Recommended Action

1. Add `update_checkpoint` and `delete_checkpoint` to spec/07-mcp-api-specifications.md
2. Implement in `mcp-servers/car-log-core/`
3. Add to checkpoint-from-receipt skill references/mcp-tools.md
4. Create error correction skill or add to existing skills
5. Test with realistic correction scenarios

## Workaround (Current)

**Manual file editing:**
```bash
# Not recommended for end users
cd ~/Documents/MileageLog/data/checkpoints/2025-11/
vim checkpoint-uuid.json
# Edit fields manually
```

This is NOT user-friendly and prone to corruption.

## Related Issues

- Trip CRUD operations also missing (see CLAUDE.md)
- Template CRUD operations incomplete
- No bulk operations for any entity type

---

**Status:** Specification and implementation missing
**Blocks:** User error correction, data quality
**Recommended for:** Immediate addition to backlog
