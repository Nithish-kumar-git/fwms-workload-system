# PHASE 2 Hardening - Manual Test Script

## Prerequisites
- Database running with migration 014 applied
- API server running
- Authentication configured (or DEV_AUTH_BYPASS=True)

---

## Test 1: Reopening Clears ALL Data

### Setup
```bash
# Get a semester ID (e.g., semester 1)
SEMESTER_ID=1
```

### Steps
1. **Open semester**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/open
   ```
   Expected: `{"success": true, "message": "Semester 1 opened for preferences (all previous data cleared)"}`

2. **Submit some preferences** (use actual staff_id and offering_id from your DB)
   ```bash
   curl -X POST http://localhost:8000/api/preferences \
     -H "Content-Type: application/json" \
     -d '{"subject_offering_id": 1, "preference_number": 1}'
   ```
   Expected: Success

3. **Close semester**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/close
   ```
   Expected: Success with preference count

4. **Run allocation**
   ```bash
   curl -X POST http://localhost:8000/api/allocation/run \
     -H "Content-Type: application/json" \
     -d '{"semester_id": 1}'
   ```
   Expected: Allocation completes, semester state → ALLOCATED

5. **Check database - should have data**
   ```sql
   SELECT COUNT(*) FROM allocation WHERE subject_offering_id IN (SELECT id FROM subject_offering WHERE semester_id = 1);
   SELECT COUNT(*) FROM workload_summary;
   SELECT COUNT(*) FROM faculty_preference WHERE subject_offering_id IN (SELECT id FROM subject_offering WHERE semester_id = 1);
   ```
   Expected: Non-zero counts

6. **Reopen semester**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/open
   ```
   Expected: Success message about clearing data

7. **Check database - ALL data should be cleared**
   ```sql
   SELECT COUNT(*) FROM allocation WHERE subject_offering_id IN (SELECT id FROM subject_offering WHERE semester_id = 1);
   SELECT COUNT(*) FROM workload_summary;
   SELECT COUNT(*) FROM faculty_preference WHERE subject_offering_id IN (SELECT id FROM subject_offering WHERE semester_id = 1);
   ```
   Expected: **ALL ZERO** (allocations, workload, preferences cleared)

8. **Check semester state**
   ```bash
   curl http://localhost:8000/api/semester/1/state
   ```
   Expected: `state: "OPEN"`, `allocated_at: null`

### ✅ Pass Criteria
- All allocations cleared
- All workload summaries cleared
- **All preferences cleared** (this is the key hardening)
- Semester state = OPEN
- allocated_at timestamp cleared

---

## Test 2: Strict Preference Lifecycle

### Test 2A: Cannot Submit When CLOSED
1. **Close semester** (if not already closed)
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/close
   ```

2. **Try to submit preference**
   ```bash
   curl -X POST http://localhost:8000/api/preferences \
     -H "Content-Type: application/json" \
     -d '{"subject_offering_id": 1, "preference_number": 1}'
   ```
   Expected: **ERROR** - "Preferences can ONLY be submitted when semester is OPEN (currently CLOSED)"

### Test 2B: Cannot Submit When ALLOCATED
1. **Run allocation** (if not already allocated)
   ```bash
   curl -X POST http://localhost:8000/api/allocation/run \
     -H "Content-Type: application/json" \
     -d '{"semester_id": 1}'
   ```

2. **Try to submit preference**
   ```bash
   curl -X POST http://localhost:8000/api/preferences \
     -H "Content-Type: application/json" \
     -d '{"subject_offering_id": 1, "preference_number": 1}'
   ```
   Expected: **ERROR** - "Preferences can ONLY be submitted when semester is OPEN (currently ALLOCATED)"

### Test 2C: Cannot Delete When CLOSED
1. **Open semester, submit preference, close**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/open
   curl -X POST http://localhost:8000/api/preferences \
     -H "Content-Type: application/json" \
     -d '{"subject_offering_id": 1, "preference_number": 1}'
   curl -X POST http://localhost:8000/api/semester/1/close
   ```

2. **Try to delete preference** (use actual preference_id)
   ```bash
   curl -X DELETE http://localhost:8000/api/preferences/1
   ```
   Expected: **ERROR** - "Preferences can ONLY be deleted when semester is OPEN (currently CLOSED)"

### Test 2D: Cannot Delete When FROZEN
1. **Allocate and freeze**
   ```bash
   curl -X POST http://localhost:8000/api/allocation/run \
     -H "Content-Type: application/json" \
     -d '{"semester_id": 1}'
   curl -X POST http://localhost:8000/api/semester/1/freeze
   ```

2. **Try to delete preference**
   ```bash
   curl -X DELETE http://localhost:8000/api/preferences/1
   ```
   Expected: **ERROR** - "Preferences can ONLY be deleted when semester is OPEN (currently FROZEN)"

### ✅ Pass Criteria
- All preference modifications blocked when not OPEN
- Clear error messages indicating current state
- No data corruption possible

---

## Test 3: Allocation Idempotency

### Steps
1. **Open, submit preferences, close**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/open
   # Submit multiple preferences
   curl -X POST http://localhost:8000/api/semester/1/close
   ```

2. **Run allocation first time**
   ```bash
   curl -X POST http://localhost:8000/api/allocation/run \
     -H "Content-Type: application/json" \
     -d '{"semester_id": 1}'
   ```
   Expected: Success, N allocations created

3. **Check allocation count**
   ```sql
   SELECT COUNT(*) FROM allocation WHERE subject_offering_id IN (SELECT id FROM subject_offering WHERE semester_id = 1);
   ```
   Note the count (e.g., 100)

4. **Reopen and close again**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/open
   curl -X POST http://localhost:8000/api/semester/1/close
   ```

5. **Run allocation second time**
   ```bash
   curl -X POST http://localhost:8000/api/allocation/run \
     -H "Content-Type: application/json" \
     -d '{"semester_id": 1}'
   ```
   Expected: Success

6. **Check allocation count again**
   ```sql
   SELECT COUNT(*) FROM allocation WHERE subject_offering_id IN (SELECT id FROM subject_offering WHERE semester_id = 1);
   ```
   Expected: **SAME COUNT** (no duplicates)

### ✅ Pass Criteria
- Allocation count identical after rerun
- No duplicate allocations created
- Workload summaries accurate
- Logs show "Cleared N existing allocations"

---

## Test 4: Complete Workflow

### Full Lifecycle Test
1. **CLOSED → OPEN**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/open
   ```
   Expected: Success, state = OPEN

2. **Submit preferences**
   ```bash
   # Submit multiple preferences from different faculty
   curl -X POST http://localhost:8000/api/preferences \
     -H "Content-Type: application/json" \
     -d '{"subject_offering_id": 1, "preference_number": 1}'
   ```
   Expected: Success

3. **OPEN → CLOSED**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/close
   ```
   Expected: Success, state = CLOSED

4. **CLOSED → ALLOCATED**
   ```bash
   curl -X POST http://localhost:8000/api/allocation/run \
     -H "Content-Type: application/json" \
     -d '{"semester_id": 1}'
   ```
   Expected: Success, state = ALLOCATED

5. **ALLOCATED → OPEN (Reopen)**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/open
   ```
   Expected: Success, ALL data cleared

6. **Verify clean state**
   ```sql
   SELECT COUNT(*) FROM allocation WHERE subject_offering_id IN (SELECT id FROM subject_offering WHERE semester_id = 1);
   SELECT COUNT(*) FROM faculty_preference WHERE subject_offering_id IN (SELECT id FROM subject_offering WHERE semester_id = 1);
   ```
   Expected: Both zero

7. **Submit new preferences, close, allocate**
   ```bash
   # Submit preferences
   curl -X POST http://localhost:8000/api/semester/1/close
   curl -X POST http://localhost:8000/api/allocation/run \
     -H "Content-Type: application/json" \
     -d '{"semester_id": 1}'
   ```
   Expected: Success

8. **ALLOCATED → FROZEN**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/freeze
   ```
   Expected: Success, state = FROZEN

9. **Try to reopen (should fail)**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/open
   ```
   Expected: **ERROR** - "Cannot reopen FROZEN semester"

10. **Try to modify anything (should fail)**
    ```bash
    # Try preference submission
    curl -X POST http://localhost:8000/api/preferences \
      -H "Content-Type: application/json" \
      -d '{"subject_offering_id": 1, "preference_number": 1}'
    ```
    Expected: **ERROR** - semester not OPEN

### ✅ Pass Criteria
- All state transitions work correctly
- Reopening clears ALL data
- FROZEN state blocks all modifications
- Audit log shows all transitions
- Timestamps set correctly

---

## Test 5: Edge Cases

### Test 5A: Reopen from CLOSED (before allocation)
1. **Open and close without allocation**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/open
   # Submit preferences
   curl -X POST http://localhost:8000/api/semester/1/close
   ```

2. **Reopen from CLOSED**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/open
   ```
   Expected: Success, preferences cleared

### Test 5B: Multiple reopens
1. **Open → Close → Open → Close → Open**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/open
   curl -X POST http://localhost:8000/api/semester/1/close
   curl -X POST http://localhost:8000/api/semester/1/open
   curl -X POST http://localhost:8000/api/semester/1/close
   curl -X POST http://localhost:8000/api/semester/1/open
   ```
   Expected: All succeed, no data corruption

### Test 5C: Duplicate preference prevention
1. **Open semester**
   ```bash
   curl -X POST http://localhost:8000/api/semester/1/open
   ```

2. **Submit same preference twice**
   ```bash
   curl -X POST http://localhost:8000/api/preferences \
     -H "Content-Type: application/json" \
     -d '{"subject_offering_id": 1, "preference_number": 1}'
   
   curl -X POST http://localhost:8000/api/preferences \
     -H "Content-Type: application/json" \
     -d '{"subject_offering_id": 1, "preference_number": 1}'
   ```
   Expected: First succeeds, second fails with duplicate error

### ✅ Pass Criteria
- All edge cases handled correctly
- No data corruption
- Clear error messages
- System remains consistent

---

## Database Verification Queries

### Check semester state
```sql
SELECT id, label, state, opened_at, closed_at, allocated_at, frozen_at, frozen_by_staff_id
FROM semester
WHERE id = 1;
```

### Check allocations
```sql
SELECT COUNT(*) as allocation_count
FROM allocation a
JOIN subject_offering so ON so.id = a.subject_offering_id
WHERE so.semester_id = 1;
```

### Check preferences
```sql
SELECT COUNT(*) as preference_count
FROM faculty_preference fp
JOIN subject_offering so ON so.id = fp.subject_offering_id
WHERE so.semester_id = 1;
```

### Check workload summaries
```sql
SELECT COUNT(*) as workload_count
FROM workload_summary;
```

### Check audit log
```sql
SELECT action_type, details, created_at
FROM audit_log
WHERE action_type IN ('SEMESTER_OPENED', 'SEMESTER_REOPENED', 'SEMESTER_CLOSED', 'SEMESTER_FROZEN', 'ALLOCATION_RUN')
ORDER BY created_at DESC
LIMIT 20;
```

---

## Expected Results Summary

| Test | Expected Behavior | Pass/Fail |
|------|------------------|-----------|
| Reopening clears allocations | ✅ Zero allocations after reopen | |
| Reopening clears workload | ✅ Zero workload records after reopen | |
| **Reopening clears preferences** | ✅ Zero preferences after reopen | |
| Submit when CLOSED | ❌ Error: not OPEN | |
| Submit when ALLOCATED | ❌ Error: not OPEN | |
| Submit when FROZEN | ❌ Error: not OPEN | |
| Delete when CLOSED | ❌ Error: not OPEN | |
| Delete when ALLOCATED | ❌ Error: not OPEN | |
| Delete when FROZEN | ❌ Error: not OPEN | |
| Allocation idempotency | ✅ No duplicates on rerun | |
| Full workflow | ✅ All transitions work | |
| FROZEN immutability | ❌ All modifications blocked | |

---

## Troubleshooting

### If preferences not cleared on reopen
- Check logs for "Cleared N preferences (fresh start)"
- Verify DELETE query in `open_semester()` function
- Check database: `SELECT COUNT(*) FROM faculty_preference WHERE subject_offering_id IN (SELECT id FROM subject_offering WHERE semester_id = 1);`

### If can submit when not OPEN
- Check `submit_preference()` state validation
- Verify semester state: `SELECT state FROM semester WHERE id = 1;`
- Check error message in response

### If duplicates after rerun
- Check allocation DELETE query in `run_allocation()`
- Verify logs show "Cleared N existing allocations"
- Check database for duplicate allocations

---

## Success Criteria

All tests must pass with:
- ✅ Complete data cleanup on reopening
- ✅ Strict state enforcement for preferences
- ✅ Idempotent allocation
- ✅ Clear error messages
- ✅ Full audit trail
- ✅ No data corruption

If all tests pass, PHASE 2 hardening is complete and production-ready.
