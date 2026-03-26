# Preference Academic Cycle Fix - Bugfix Design

## Overview

After migration 021 transitioned from the `academic_cycle` table to the new `cycle` table architecture, several service files continue to reference the non-existent `so.academic_cycle_id` column in `subject_offering`. The migration renamed this column to `old_academic_cycle_id` and introduced a new structure using `academic_year_id` and `semester_id` to reference cycles. This design document outlines the precise SQL query changes needed in each affected file to restore functionality while maintaining backward compatibility and data integrity.

The fix strategy is surgical: replace direct `academic_cycle_id` column references with JOINs through the new `cycle` table structure, using `academic_year_id` and `semester_id` as the linking keys.

## Glossary

- **Bug_Condition (C)**: SQL queries that reference `so.academic_cycle_id` or `a.academic_cycle_id` columns that no longer exist after migration 021
- **Property (P)**: Queries successfully execute by joining through the `cycle` table using `academic_year_id` and `semester_id`
- **Preservation**: All existing functionality (preference submission, allocation, window management) continues to work with identical business logic
- **subject_offering**: Table containing course offerings, now uses `academic_year_id` + `semester_id` instead of `academic_cycle_id`
- **cycle**: New table that controls workflow state for a specific academic year + semester combination
- **academic_year**: New table representing time periods (e.g., "2025-2026"), independent of semester structure
- **migration 021**: Database migration that transitioned from ODD/EVEN semester_type system to semester-specific cycles

## Bug Details

### Bug Condition

The bug manifests when any service attempts to query `subject_offering` or `allocation` tables using the old `academic_cycle_id` column. The migration renamed this column to `old_academic_cycle_id` for backup purposes, but the application code was not updated to use the new schema structure.

**Formal Specification:**
```
FUNCTION isBugCondition(query)
  INPUT: query of type SQLQuery
  OUTPUT: boolean
  
  RETURN (query.references("so.academic_cycle_id") OR 
          query.references("a.academic_cycle_id")) AND
         NOT query.joins("cycle") AND
         NOT query.uses("academic_year_id") AND
         NOT query.uses("semester_id")
END FUNCTION
```

### Examples

- **Example 1**: Faculty calls `/api/preferences/me` → System crashes with "column so.academic_cycle_id does not exist" (line 370 in `app/preference/service.py`)
- **Example 2**: Coordinator calls `/api/pref-window/status` → System crashes with "column so.academic_cycle_id does not exist" (line 85 in `app/coordinator/semester_state_service.py`)
- **Example 3**: Allocation service queries offerings → System crashes with "column so.academic_cycle_id does not exist" (line 131 in `app/allocation/service.py`)
- **Example 4**: Staff deactivation check → System crashes with "column a.academic_cycle_id does not exist" (line 207 in `app/admin/staff_service.py`)
- **Edge case**: Demo script generates preferences → System crashes with "column so.academic_cycle_id does not exist" (line 144 in `scripts/demo_prep.py`)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Faculty preference submission validation rules (PREF-01 through PREF-05, SHIFT-01, CT-01) must continue to work exactly as before
- Preference window lifecycle (DRAFT → SCHEDULED → OPEN → CLOSED) must remain unchanged
- Allocation algorithm logic (Stage 1, Stage 2, Final Pass with progressive relaxation) must remain unchanged
- Workload calculation and summary generation must produce identical results
- Audit logging for all operations must continue to work

**Scope:**
All inputs that do NOT involve querying subject offerings or allocations by cycle should be completely unaffected by this fix. This includes:
- Staff authentication and authorization
- Subject and program management
- Semester state transitions
- Report generation (except where it queries allocations)
- All write operations to `faculty_preference`, `allocation`, and `selection_window` tables (these already use the correct `cycle_id` column)

## Hypothesized Root Cause

Based on the bug description and migration analysis, the root causes are:

1. **Incomplete Migration Update**: Migration 021 successfully updated the database schema and migrated data, but did not include application code updates. The migration script only handled SQL schema changes, leaving Python service files with stale column references.

2. **Column Rename Without Code Scan**: The `academic_cycle_id` column was renamed to `old_academic_cycle_id` in `subject_offering` and `allocation` tables, but no automated scan was performed to identify all code locations referencing these columns.

3. **Missing JOIN Pattern**: The new architecture requires joining through the `cycle` table using `academic_year_id` and `semester_id`, but existing queries attempted direct column access. The migration documentation did not provide clear query migration patterns.

4. **Test Coverage Gap**: The affected endpoints were not covered by integration tests that would have caught these schema mismatches immediately after migration.

## Correctness Properties

Property 1: Bug Condition - Schema-Compliant Queries

_For any_ SQL query that previously referenced `so.academic_cycle_id` or `a.academic_cycle_id`, the fixed query SHALL successfully execute by joining through the `cycle` table using `academic_year_id` and `semester_id`, returning the same logical result set as before the migration.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - Business Logic Unchanged

_For any_ operation that does NOT involve querying subject offerings or allocations by cycle (preference validation, window management, state transitions), the fixed code SHALL produce exactly the same behavior as the original code, preserving all business rules and validation logic.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

The fix involves updating SQL queries in 5 files to use the new schema structure. Each fix follows the same pattern: replace direct `academic_cycle_id` column access with a JOIN through the `cycle` table.

**File 1**: `app/preference/service.py`

**Function**: `list_preferences` (line 356-374)

**Current Query** (BROKEN):
```sql
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
  AND so.academic_cycle_id = :cid  -- BROKEN: column does not exist
ORDER BY fp.preference_number
```

**Fixed Query**:
```sql
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
JOIN cycle c ON c.academic_year_id = so.academic_year_id 
            AND c.semester_id = so.semester_id
WHERE fp.staff_id = :staff_id
  AND c.id = :cid
ORDER BY fp.preference_number
```

**Rationale**: Join through `cycle` table using the composite key (`academic_year_id`, `semester_id`) to resolve the cycle ID.

---

**File 2**: `app/coordinator/semester_state_service.py`

**Function**: `open_semester` (line 85-90)

**Current Query** (BROKEN):
```sql
SELECT sem.state, so.academic_cycle_id
FROM semester sem
LEFT JOIN subject_offering so ON so.semester_id = sem.id
WHERE sem.id = :sid
LIMIT 1
```

**Fixed Query**:
```sql
SELECT sem.state, c.id AS cycle_id
FROM semester sem
LEFT JOIN subject_offering so ON so.semester_id = sem.id
LEFT JOIN cycle c ON c.semester_id = sem.id 
                 AND c.academic_year_id = so.academic_year_id
WHERE sem.id = :sid
LIMIT 1
```

**Rationale**: The function needs to retrieve the cycle_id for clearing preferences/allocations. Join through `cycle` table to get the correct cycle ID.

---

**File 3**: `app/allocation/service.py`

**Function**: `_run_allocation_for_semester` (line 131-135)

**Current Query** (BROKEN):
```sql
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
WHERE so.academic_cycle_id = :cid  -- BROKEN: column does not exist
  AND so.is_active = true
  AND so.semester_id = :sem_id
```

**Fixed Query**:
```sql
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
```

**Rationale**: Filter offerings by cycle using the new JOIN pattern. The `semester_id` filter is redundant but kept for clarity.

---

**File 4**: `app/allocation/service.py`

**Function**: `run_allocation` - workload summary calculation (line 689-692)

**Current Query** (BROKEN):
```sql
SELECT 
    s.id, s.emp_code, s.name,
    COALESCE(NULLIF(TRIM(s.designation), ''), 'Assistant Professor') AS designation,
    COALESCE(s.tch_norm, 40) AS tch_norm,
    COALESCE(SUM(sub.tch), 0) AS tch_assigned
FROM staff s
LEFT JOIN allocation a ON a.staff_id = s.id AND a.academic_cycle_id = :cid  -- BROKEN
LEFT JOIN subject_offering so ON so.id = a.subject_offering_id
LEFT JOIN subject sub ON sub.id = so.subject_id
WHERE s.is_active = true AND s.emp_code IS NOT NULL
GROUP BY s.id, s.emp_code, s.name, s.designation, s.tch_norm
ORDER BY s.id
```

**Fixed Query**:
```sql
SELECT 
    s.id, s.emp_code, s.name,
    COALESCE(NULLIF(TRIM(s.designation), ''), 'Assistant Professor') AS designation,
    COALESCE(s.tch_norm, 40) AS tch_norm,
    COALESCE(SUM(sub.tch), 0) AS tch_assigned
FROM staff s
LEFT JOIN allocation a ON a.staff_id = s.id
LEFT JOIN subject_offering so ON so.id = a.subject_offering_id
LEFT JOIN subject sub ON sub.id = so.subject_id
LEFT JOIN cycle c ON c.academic_year_id = so.academic_year_id 
                 AND c.semester_id = so.semester_id
WHERE s.is_active = true 
  AND s.emp_code IS NOT NULL
  AND (a.id IS NULL OR c.id = :cid)
GROUP BY s.id, s.emp_code, s.name, s.designation, s.tch_norm
ORDER BY s.id
```

**Rationale**: The allocation table still has `cycle_id` column (correctly migrated), but we need to filter by cycle through the subject_offering relationship. The `(a.id IS NULL OR c.id = :cid)` condition ensures staff with no allocations are still included.

**ALTERNATIVE SIMPLER FIX** (RECOMMENDED):
Since `allocation` table already has `cycle_id` column (migrated correctly), we can use it directly:
```sql
SELECT 
    s.id, s.emp_code, s.name,
    COALESCE(NULLIF(TRIM(s.designation), ''), 'Assistant Professor') AS designation,
    COALESCE(s.tch_norm, 40) AS tch_norm,
    COALESCE(SUM(sub.tch), 0) AS tch_assigned
FROM staff s
LEFT JOIN allocation a ON a.staff_id = s.id AND a.cycle_id = :cid
LEFT JOIN subject_offering so ON so.id = a.subject_offering_id
LEFT JOIN subject sub ON sub.id = so.subject_id
WHERE s.is_active = true AND s.emp_code IS NOT NULL
GROUP BY s.id, s.emp_code, s.name, s.designation, s.tch_norm
ORDER BY s.id
```

**Rationale**: Use the correctly migrated `allocation.cycle_id` column directly instead of joining through subject_offering.

---

**File 5**: `app/admin/staff_service.py`

**Function**: `deactivate_staff` (line 207-209)

**Current Query** (BROKEN):
```sql
SELECT count(*) FROM allocation a
JOIN academic_cycle ac ON ac.id = a.academic_cycle_id  -- BROKEN: table renamed
WHERE a.staff_id = :sid AND ac.is_active = true
```

**Fixed Query**:
```sql
SELECT count(*) FROM allocation a
JOIN cycle c ON c.id = a.cycle_id
WHERE a.staff_id = :sid AND c.status != 'FROZEN'
```

**Rationale**: The `allocation` table now uses `cycle_id` (correctly migrated). The `academic_cycle` table was renamed to `academic_cycle_old_backup`. The new `cycle` table uses `status` instead of `is_active`, and we check for non-FROZEN cycles (OPEN, CLOSED, ALLOCATED are all considered "active").

---

**File 6**: `scripts/demo_prep.py` (BONUS FIX)

**Function**: Demo data generation (line 144-146)

**Current Query** (BROKEN):
```python
offerings_raw = psql(
    f"SELECT id FROM subject_offering so "
    f"WHERE so.academic_cycle_id = {cycle_id} AND so.is_active = true "
    f"{shift_sql} ORDER BY RANDOM() LIMIT 5"
)
```

**Fixed Query**:
```python
offerings_raw = psql(
    f"SELECT so.id FROM subject_offering so "
    f"JOIN cycle c ON c.academic_year_id = so.academic_year_id "
    f"             AND c.semester_id = so.semester_id "
    f"WHERE c.id = {cycle_id} AND so.is_active = true "
    f"{shift_sql} ORDER BY RANDOM() LIMIT 5"
)
```

**Rationale**: Demo script needs to generate test preferences. Use the same JOIN pattern to filter offerings by cycle.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, verify that the bug exists on unfixed code by attempting to call the affected endpoints, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm the root cause analysis by observing the exact PostgreSQL error messages.

**Test Plan**: Manually call each affected endpoint with valid parameters and observe the 500 errors with "column does not exist" messages. This confirms which queries are broken and validates our fix targets.

**Test Cases**:
1. **Faculty Preference List Test**: Call `GET /api/preferences/me` as authenticated faculty (will fail with "column so.academic_cycle_id does not exist")
2. **Preference Window Status Test**: Call `GET /api/pref-window/status` as coordinator (will fail with "column so.academic_cycle_id does not exist")
3. **Allocation Run Test**: Call `POST /api/allocation/run` with valid semester_id (will fail with "column so.academic_cycle_id does not exist")
4. **Staff Deactivation Test**: Call `DELETE /api/admin/staff/{id}` for staff with allocations (will fail with "column a.academic_cycle_id does not exist")

**Expected Counterexamples**:
- PostgreSQL error: `column so.academic_cycle_id does not exist`
- PostgreSQL error: `column a.academic_cycle_id does not exist`
- PostgreSQL error: `relation "academic_cycle" does not exist`
- Possible causes: migration 021 renamed columns but code was not updated

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (queries referencing old columns), the fixed function produces the expected behavior (successful query execution with correct results).

**Pseudocode:**
```
FOR ALL query WHERE isBugCondition(query) DO
  result := execute_fixed_query(query)
  ASSERT result.success = true
  ASSERT result.data = expected_data_from_new_schema
END FOR
```

**Test Plan**: After applying fixes, call each affected endpoint and verify:
1. No PostgreSQL errors
2. Correct data returned (same logical results as before migration)
3. Response format unchanged (API contract preserved)

**Test Cases**:
1. **Faculty Preference List**: Verify preferences are returned with correct subject details
2. **Preference Window Status**: Verify window status includes correct cycle information
3. **Allocation Run**: Verify allocations are created successfully and workload summaries are correct
4. **Staff Deactivation**: Verify staff with active allocations cannot be deactivated

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (operations not involving cycle queries), the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL operation WHERE NOT involves_cycle_query(operation) DO
  ASSERT fixed_code(operation) = original_code(operation)
END FOR
```

**Testing Approach**: Property-based testing is NOT recommended for this bugfix because:
- The bug is purely a schema mismatch, not a logic error
- The fix does not change any business rules or validation logic
- Manual testing of key workflows is sufficient to verify preservation

**Test Plan**: Manually test key workflows that do NOT involve the fixed queries:

**Test Cases**:
1. **Preference Submission**: Submit a new preference and verify all validation rules (PREF-01 through PREF-05, SHIFT-01, CT-01) still work correctly
2. **Window Lifecycle**: Open and close a preference window, verify state transitions work correctly
3. **Semester State Transitions**: Open, close, and allocate a semester, verify state machine works correctly
4. **Audit Logging**: Verify all operations still generate correct audit log entries

### Unit Tests

- Test each fixed query in isolation with mock data to verify correct JOIN logic
- Test edge cases: offerings with no cycle match, staff with no allocations, empty result sets
- Test that queries return same logical results as before migration (using test data that exists in both old and new schema)

### Property-Based Tests

NOT APPLICABLE for this bugfix. The bug is a schema mismatch, not a logic error. Property-based testing would not provide additional value beyond manual testing.

### Integration Tests

- Test full preference submission flow: faculty submits preferences → coordinator closes window → allocation runs → workload report generated
- Test reopening workflow: coordinator reopens semester → preferences cleared → faculty resubmits → allocation runs again
- Test staff deactivation: verify staff with allocations in active cycle cannot be deactivated
- Test demo script: verify demo data generation works with new schema

## Migration Validation

After applying fixes, validate that the migration was successful:

1. **Schema Verification**: Confirm `subject_offering.old_academic_cycle_id` exists (backup column)
2. **Data Integrity**: Verify all preferences and allocations have valid `cycle_id` references
3. **Cycle Mapping**: Verify all old academic_cycle records have corresponding new cycle records
4. **Backward Compatibility**: Verify `old_academic_cycle_id` column is NOT used by any application code

## Rollback Plan

If the fix causes unexpected issues:

1. **Immediate Rollback**: Revert all 5 file changes using git
2. **Schema Rollback**: Run reverse migration to restore `academic_cycle` table (if needed)
3. **Data Validation**: Verify no data loss occurred during testing
4. **Root Cause Analysis**: Investigate why the fix failed and update design document

## Performance Considerations

The new JOIN pattern adds one additional table join per query. Performance impact analysis:

- **Preference List Query**: +1 JOIN through `cycle` table (negligible impact, cycle table is small)
- **Allocation Query**: +1 JOIN through `cycle` table (negligible impact, query already has 5 JOINs)
- **Workload Summary Query**: Uses existing `allocation.cycle_id` column (no additional JOIN)
- **Staff Deactivation Query**: Uses existing `allocation.cycle_id` column (no additional JOIN)

**Recommendation**: No indexes needed. The `cycle` table is small (<100 rows) and already has indexes on `academic_year_id` and `semester_id` (created by migration 021).
