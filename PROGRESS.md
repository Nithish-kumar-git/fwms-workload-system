# ALLOCATION SERVICE semester_type BUG DIAGNOSIS

## Problem Summary
The allocation service references `semester_type` column which doesn't exist in the new schema. The system has migrated from ODD/EVEN semester_type to semester_id (1-6 for I-VI).

## STEP 1: All occurrences of "semester_type" in app/

Found in `app/allocation/service.py`:
- Line 57: Function parameter `semester_type: str`
- Line 421: Function parameter `semester_type: str | None = None`
- Line 436: Comment mentions `academic_year + semester_type`
- Line 492-493: Validation check `active_cycle["semester_type"]`
- Line 496: Error message includes `semester_type`
- Line 505: Assignment `semester_type = active_cycle["semester_type"]`
- Line 626: Function call parameter `semester_type=semester_type`
- Line 729: INSERT INTO workload_summary column `semester_type`
- Line 733: ON CONFLICT clause `(staff_id, academic_year, semester_type)`
- Line 746: Parameter binding `"st": semester_type`

Found in `app/reports/service.py`:
- Line 217-218: Comment and conversion logic `semester_type = "EVEN" if semester_id in (2, 4, 6) else "ODD"`
- Line 224, 226, 232, 235, 241, 244: WHERE clauses using `semester_type`

Found in `app/coordinator/semester_state_service.py`:
- Line 148-150: Comment about workload_summary using `(academic_year, semester_type)`

## STEP 2: app/allocation/service.py Analysis

The service has these issues:
1. Function `_run_allocation_for_semester()` accepts `semester_type` parameter (line 57)
2. Function `run_allocation()` accepts `semester_type` parameter (line 421)
3. References `active_cycle["semester_type"]` which doesn't exist in new cycle schema
4. Tries to INSERT INTO workload_summary with `semester_type` column
5. Uses ON CONFLICT with `(staff_id, academic_year, semester_type)` constraint

## STEP 3: app/allocation/router.py Analysis

The router:
- Line 22: Removed `semester_type` from AllocationScope (good!)
- Line 47: Comment mentions "semester_type" but doesn't use it
- Line 130: Passes `semester_type=None` to service (needs fixing)

## STEP 4: Database Schema Analysis

### allocation table
- Has `cycle_id` column (FK to cycle.id) ✅
- Has `old_academic_cycle_id` column (legacy) ✅
- NO `semester_type` column ✅

### workload_summary table
- Has `semester_type` column (VARCHAR(10), NOT NULL) ❌
- Has CHECK constraint: `semester_type IN ('ODD', 'EVEN')` ❌
- Has UNIQUE constraint: `(staff_id, academic_year, semester_type)` ❌
- Has `cycle_id` column (nullable FK to cycle.id) ✅
- Has `old_academic_cycle_id` column (NOT NULL, legacy) ❌

### subject_offering table
- Has `semester_id` column (FK to semester.id) ✅
- Has `academic_year` column (VARCHAR) ✅
- Has `academic_year_id` column (FK to academic_year.id) ✅
- NO `semester_type` column ✅

## Root Cause

The `workload_summary` table still uses the OLD schema with `semester_type` (ODD/EVEN), but the rest of the system has migrated to `semester_id` (1-6). The allocation service tries to write to this table using `semester_type`, which causes a mismatch.

The `active_cycle` object from `get_active_cycle()` returns:
```python
{
    "id": int,
    "academic_year": str,
    "semester_id": int,  # NEW: 1-6
    "semester_name": str,  # NEW: "I", "II", etc.
    "status": str,
    "is_active": bool,
    ...
}
```

But the allocation service expects:
```python
{
    "academic_year": str,
    "semester_type": str,  # OLD: "ODD" or "EVEN"
    ...
}
```

## Solution Strategy

We have two options:

### Option 1: Convert semester_id to semester_type (Quick Fix)
- Keep workload_summary table as-is
- Convert semester_id to ODD/EVEN in allocation service
- Mapping: I, III, V → ODD; II, IV, VI → EVEN

### Option 2: Migrate workload_summary table (Proper Fix)
- Drop semester_type column
- Add semester_id column
- Update constraints
- Requires migration script

**Decision: Use Option 1 (Quick Fix)** since it's less risky and doesn't require schema migration.

## Files to Fix

1. `app/allocation/service.py`:
   - Keep `semester_type` parameter but derive it from `semester_id`
   - Convert `semester_id` to `semester_type` using: `"ODD" if semester_id in (1, 3, 5) else "EVEN"`
   - Remove references to `active_cycle["semester_type"]`

2. `app/allocation/router.py`:
   - Already correct (passes `semester_type=None`)

## Next Steps

1. Fix `app/allocation/service.py` to convert semester_id → semester_type
2. Test allocation endpoint
3. Commit changes
