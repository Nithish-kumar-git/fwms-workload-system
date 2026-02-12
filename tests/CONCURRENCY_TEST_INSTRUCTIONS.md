# Concurrency Torture Test — Execution Instructions

## Prerequisites

1. **Database Setup**
   - PostgreSQL 15+ running
   - Schema applied: `migrations/schema.sql` (v1.3)
   - Database connection configured in `.env`

2. **Python Dependencies**
   ```bash
   pip install asyncpg python-dotenv
   ```

3. **Environment Variables** (`.env` file)
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=faculty_selection
   DB_USER=postgres
   DB_PASSWORD=your_password
   ```

## Running the Test

### Option 1: Direct Execution
```bash
python tests/concurrency_torture_test.py
```

### Option 2: With Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate
pip install asyncpg python-dotenv
python tests\concurrency_torture_test.py
```

## What the Test Does

### Test 1: Quota Enforcement (10 Parallel Workers)
- **Setup**: 10 workers attempt to select 10 different subjects simultaneously
- **Quota**: 3 subjects per staff per window
- **Expected**: Exactly 3 successes, 7 "Quota exceeded" rejections
- **Validates**: Advisory lock prevents quota race conditions

### Test 2: FCFS Enforcement (5 Parallel Workers)
- **Setup**: 5 workers attempt to select the SAME subject simultaneously
- **Expected**: Exactly 1 success, 4 "Subject already selected" rejections
- **Validates**: Partial unique index `uq_subject_selected` enforces FCFS

### Test 3: Slot Uniqueness Verification
- **Setup**: Query all `staff_slot_number` values from `subject_selection`
- **Expected**: Sequential slots [1, 2, 3] with no duplicates or gaps
- **Validates**: Advisory lock prevents slot collision

## Expected Output

```
================================================================================
CONCURRENCY TORTURE TEST SUMMARY
================================================================================

[TEST 1] QUOTA ENFORCEMENT (10 parallel requests, quota=3)
--------------------------------------------------------------------------------
Total requests: 10
Successful selections: 3
Quota exceeded rejections: 7
Expected: exactly 3 successes, 7 quota exceeded
✅ PASS: Quota enforcement correct

[TEST 2] FCFS ENFORCEMENT (5 parallel requests, same subject)
--------------------------------------------------------------------------------
Total requests: 5
Successful selections: 1
Conflict rejections: 4
Expected: exactly 1 success, 4 conflicts
✅ PASS: FCFS guarantee enforced

[TEST 3] SLOT UNIQUENESS VERIFICATION
--------------------------------------------------------------------------------
Total slots assigned: 3
Unique slots: 3
Slots: [1, 2, 3]
✅ PASS: All slots unique and sequential

✅ No errors encountered

================================================================================
```

## Failure Scenarios

### ❌ Test 1 Fails (Quota Violation)
**Symptom**: More than 3 successes or fewer than 7 quota rejections  
**Cause**: Advisory lock not acquired or acquired in wrong order  
**Fix**: Verify `pg_advisory_xact_lock` is called at Step 1.75 in `transactions.py`

### ❌ Test 2 Fails (FCFS Violation)
**Symptom**: More than 1 success (multiple workers claim same subject)  
**Cause**: Partial unique index missing or INSERT conflict handling broken  
**Fix**: Verify `uq_subject_selected` index exists and `ON CONFLICT DO NOTHING` is present

### ❌ Test 3 Fails (Slot Collision)
**Symptom**: Duplicate slot numbers or non-sequential slots  
**Cause**: Advisory lock not serializing slot assignment  
**Fix**: Verify advisory lock is acquired BEFORE `MAX(staff_slot_number)` query

## Troubleshooting

### Connection Refused
```
Error: connection refused
```
**Fix**: Ensure PostgreSQL is running and `.env` has correct credentials

### Lock Timeout
```
Error: canceling statement due to lock timeout
```
**Fix**: Expected under high contention. Test will retry. If persistent, increase `lock_timeout` in test.

### Schema Not Found
```
Error: relation "subject_selection" does not exist
```
**Fix**: Apply `migrations/schema.sql` first:
```bash
psql -U postgres -d faculty_selection -f migrations/schema.sql
```

## Verification Checklist

After running the test, verify:

- [ ] All 3 tests show ✅ PASS
- [ ] No ❌ FAIL verdicts
- [ ] No errors in error section
- [ ] Slot numbers are [1, 2, 3] exactly
- [ ] Quota enforcement shows 3/7 split
- [ ] FCFS enforcement shows 1/4 split

## Next Steps

If all tests pass:
1. ✅ Advisory lock implementation is correct
2. ✅ FCFS guarantee is enforced
3. ✅ Quota enforcement is race-safe
4. ✅ Slot assignment is collision-free
5. **Proceed to integration testing with full API stack**

If any test fails:
1. Review failure scenario above
2. Check `app/selection/transactions.py` lock ordering
3. Verify schema.sql has correct indexes and constraints
4. Re-run test after fixes
