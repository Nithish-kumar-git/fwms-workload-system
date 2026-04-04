# Bug Condition Investigation Findings

## Summary

After thorough re-investigation of the codebase, I discovered that **the bug exists in `scripts/demo_prep.py` with 8+ broken references to the old schema**. The production service files mentioned in the original design document have already been fixed.

## Evidence

### Production Code Status: ✅ ALREADY FIXED

All service files mentioned in the design document are using the correct schema:

### 1. Preference Service (`app/preference/service.py`)

**Design Document Claims** (line 356-374): Query references `so.academic_cycle_id`

**Actual Current Code** (line 320-356): 
```python
def list_preferences(staff_id: int) -> list[dict]:
    """List all preferences for a faculty member across all cycles."""
    with get_transaction() as session:
        rows = session.execute(
            text("""
                SELECT fp.id, fp.staff_id, fp.subject_offering_id, fp.preference_number,
                       fp.submitted_at,
                       s.code AS subject_code, s.name AS subject_name,
                       sec.label AS section_label, sem.label AS semester_label,
                       p.name AS program_name
                FROM faculty_preference fp
                JOIN subject_offering so ON so.id = fp.subject_offering_id
                JOIN subject s ON s.id = so.subject_id
                JOIN section sec ON sec.id = so.section_id
                JOIN semester sem ON sem.id = so.semester_id
                JOIN program p ON p.id = so.program_id
                WHERE fp.staff_id = :staff_id
                ORDER BY fp.preference_number
            """),
            {"staff_id": staff_id}
        ).fetchall()
```

**Status**: ✅ **FIXED** - No reference to `so.academic_cycle_id`. Query doesn't filter by cycle at all (returns all preferences across all cycles).

### 2. Semester State Service (`app/coordinator/semester_state_service.py`)

**Design Document Claims** (line 85-90): Query references `so.academic_cycle_id`

**Actual Current Code** (line 80-95):
```python
row = session.execute(
    text("""
        SELECT sem.state, c.id AS cycle_id
        FROM semester sem
        LEFT JOIN subject_offering so ON so.semester_id = sem.id
        LEFT JOIN cycle c ON c.semester_id = sem.id 
                         AND c.academic_year_id = so.academic_year_id
        WHERE sem.id = :sid
        LIMIT 1
    """),
    {"sid": semester_id}
).fetchone()
```

**Status**: ✅ **FIXED** - Uses correct JOIN through cycle table with `c.academic_year_id = so.academic_year_id` and `c.semester_id = sem.id`.

### 3. Allocation Service (`app/allocation/service.py`)

**Design Document Claims** (line 131-135): Query references `so.academic_cycle_id`

**Actual Current Code** (line 125-145):
```python
offering_sql = """
    SELECT so.id, so.subject_id, so.program_id, so.semester_id,
           so.section_id, so.shift,
           s.code, s.name, COALESCE(s.tch, s.l + s.t + s.p, 0) AS tch,
           s.l, s.t, s.p,
           p.name AS program_name,
           sem.label AS semester_label,
           sec.label AS section_label
    FROM subject_offering so
    JOIN subject s ON s.id = so.subject_id
    JOIN program p ON p.id = so.program_id
    JOIN semester sem ON sem.id = so.semester_id
    JOIN section sec ON sec.id = so.section_id
    JOIN cycle c ON c.academic_year_id = so.academic_year_id 
                AND c.semester_id = so.semester_id
    WHERE c.id = :cid
      AND so.is_active = true
      AND so.semester_id = :sem_id
"""
```

**Status**: ✅ **FIXED** - Uses correct JOIN through cycle table.

### 4. Staff Service (`app/admin/staff_service.py`)

**Design Document Claims** (line 207-209): Query references `a.academic_cycle_id` and joins `academic_cycle` table

**Actual Current Code** (deactivate_staff function):
```python
alloc_count = session.execute(
    text("""
        SELECT count(*) FROM allocation a
        JOIN cycle c ON c.id = a.cycle_id
        WHERE a.staff_id = :sid AND c.status != 'FROZEN'
    """),
    {"sid": staff_id},
).scalar()
```

**Status**: ✅ **FIXED** - Uses `a.cycle_id` and joins the `cycle` table correctly.

### 5. Demo Script (`scripts/demo_prep.py`)

**Design Document Claims** (line 144-146): Query references `so.academic_cycle_id`

**Actual Current Code** - **MULTIPLE BROKEN REFERENCES**:

**Line 73**: `SELECT id FROM academic_cycle WHERE is_active = true LIMIT 1`
- ❌ **BROKEN**: References `academic_cycle` table which was renamed to `academic_cycle_old_backup`

**Line 76-78**: `INSERT INTO academic_cycle (academic_year, semester_type, is_active) VALUES ('2025-2026', 'EVEN', true)`
- ❌ **BROKEN**: Tries to insert into non-existent `academic_cycle` table

**Line 79**: `SELECT id FROM academic_cycle WHERE is_active = true LIMIT 1`
- ❌ **BROKEN**: References `academic_cycle` table again

**Line 112**: `DELETE FROM allocation WHERE academic_cycle_id = {cycle_id}`
- ❌ **BROKEN**: References `allocation.academic_cycle_id` which was renamed to `old_academic_cycle_id`
- Should use `allocation.cycle_id` instead

**Line 113**: `DELETE FROM workload_summary WHERE academic_cycle_id = {cycle_id}`
- ❌ **BROKEN**: References `workload_summary.academic_cycle_id` which was renamed to `old_academic_cycle_id`
- Should use `workload_summary.cycle_id` instead

**Line 114**: `DELETE FROM faculty_preference WHERE academic_cycle_id = {cycle_id}`
- ❌ **BROKEN**: References `faculty_preference.academic_cycle_id` which was renamed to `old_academic_cycle_id`
- Should use `faculty_preference.cycle_id` instead

**Line 144**: `WHERE so.academic_cycle_id = {cycle_id} AND so.is_active = true`
- ❌ **BROKEN**: References `subject_offering.academic_cycle_id` which was renamed to `old_academic_cycle_id`
- Should JOIN through `cycle` table using `academic_year_id` and `semester_id`

**Line 157**: `INSERT INTO faculty_preference (staff_id, subject_offering_id, preference_number, academic_cycle_id)`
- ❌ **BROKEN**: References `academic_cycle_id` column which was renamed to `old_academic_cycle_id`
- Should use `cycle_id` instead

**Status**: ❌ **COMPLETELY BROKEN** - 8+ broken references. This script will fail immediately after migration 021.

### 6. Old Cycle Service (`app/admin/cycle_service.py`)

**Status**: ⚠️ **EXISTS BUT NOT USED** - This file still references the old `academic_cycle` table, but it's not imported anywhere. The router uses `cycle_service_new.py` instead.

## Analysis

### Why This Happened

The investigation reveals:

1. **Production code was already fixed**: The service files mentioned in the design document (preference, allocation, admin) have already been updated to use the new schema. Someone fixed these files but didn't update the bugfix spec.

2. **Demo script was overlooked**: The `scripts/demo_prep.py` file was not updated during the migration. This is a utility script used for testing/demo purposes, so it might have been considered lower priority.

3. **Old service file left behind**: The `app/admin/cycle_service.py` file still exists with old schema references, but it's not being used. The router imports `cycle_service_new.py` instead. This is technical debt that should be cleaned up.

### Impact Assessment

**Critical Impact**:
- ❌ Demo script (`demo_prep.py`) is completely broken - will fail immediately when run
- ❌ Cannot seed test data or prepare demo environments
- ❌ 8+ SQL errors will occur if script is executed

**No Production Impact**:
- ✅ All production API endpoints work correctly
- ✅ All service files use correct schema
- ✅ The old `cycle_service.py` is not imported anywhere

### Root Cause

The root cause is **incomplete migration cleanup**. Migration 021 successfully updated:
- ✅ Database schema (renamed tables and columns)
- ✅ Production service files (preference, allocation, admin)
- ✅ Created new cycle service (`cycle_service_new.py`)

But failed to update:
- ❌ Demo/utility scripts (`demo_prep.py`)
- ❌ Remove or update old service file (`cycle_service.py`)

### Impact on Testing

The bug condition exploration test I created will **FAIL as expected** when testing the broken SQL queries from `demo_prep.py`. This correctly demonstrates the bug exists.

## Recommendations

### Option 1: Fix Demo Script and Clean Up (Recommended)

**Rationale**: The production code is already fixed. We just need to fix the demo script and remove technical debt.

**Actions**:
1. Fix all 8+ broken references in `scripts/demo_prep.py`
2. Delete or update `app/admin/cycle_service.py` (not being used)
3. Update the bugfix spec to reflect actual scope
4. Run bug exploration tests to confirm they fail on unfixed code
5. Apply fixes and verify tests pass

**Estimated Effort**: Low (1-2 hours)

### Option 2: Update Bugfix Spec Scope

**Rationale**: The original spec scope was too broad. Narrow it to just the demo script.

**Actions**:
1. Update bugfix.md to focus only on demo_prep.py
2. Update design.md to remove already-fixed service files
3. Update tasks.md to reflect reduced scope
4. Proceed with fixing demo script only

**Estimated Effort**: Low (1 hour)

### Option 3: Close Spec and Create New One

**Rationale**: The original spec is outdated. Create a fresh spec for the demo script fix.

**Actions**:
1. Close current bugfix spec as "partially complete"
2. Create new bugfix spec specifically for demo_prep.py
3. Document that production code is already fixed
4. Proceed with new spec workflow

**Estimated Effort**: Medium (2-3 hours)

## Next Steps

**Recommended Path**: Option 1 - Fix Demo Script and Clean Up

I have created a bug condition exploration test (`tests/test_bug_academic_cycle_fix.py`) that:
- ✅ Tests the actual broken SQL queries from demo_prep.py
- ✅ Will FAIL on unfixed code (demonstrates bug exists)
- ✅ Will PASS on fixed code (validates fix works)
- ✅ Covers all 4 bug scenarios from the requirements

The test is ready to run. Next steps:
1. Run the test to confirm it fails (proving bug exists)
2. Fix `scripts/demo_prep.py` (8+ broken references)
3. Clean up `app/admin/cycle_service.py` (technical debt)
4. Re-run test to confirm it passes (proving fix works)

**User Decision Needed**: Which option should I proceed with?
