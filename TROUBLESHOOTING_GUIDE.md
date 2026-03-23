# TROUBLESHOOTING GUIDE

## Quick Reference for Common Issues

---

## Issue 1: Cannot Submit Preferences

### Symptom
Faculty receives error: "Preferences can ONLY be submitted when semester is OPEN"

### Diagnosis
```sql
-- Check semester state
SELECT id, label, state FROM semester WHERE id = ?;
```

### Solution
1. If state = CLOSED: Coordinator must open semester
   ```bash
   POST /api/semester/{id}/open
   ```

2. If state = ALLOCATED: Coordinator must reopen semester (will clear allocations)
   ```bash
   POST /api/semester/{id}/open
   ```

3. If state = FROZEN: Cannot reopen (finalized by HOD)

---

## Issue 2: Cannot Run Allocation

### Symptom
Error: "Semester must be CLOSED (currently OPEN)"

### Diagnosis
```sql
-- Check semester state and preference count
SELECT 
    sem.id, 
    sem.label, 
    sem.state,
    COUNT(fp.id) as preference_count
FROM semester sem
LEFT JOIN subject_offering so ON so.semester_id = sem.id
LEFT JOIN faculty_preference fp ON fp.subject_offering_id = so.id
WHERE sem.id = ?
GROUP BY sem.id, sem.label, sem.state;
```

### Solution
1. Close semester first:
   ```bash
   POST /api/semester/{id}/close
   ```

2. If error "Cannot close with no preferences":
   - Faculty must submit at least 1 preference
   - Then close semester

3. Then run allocation:
   ```bash
   POST /api/allocation/run
   Body: {"semester_id": X}
   ```

---

## Issue 3: Workload Summary Incorrect

### Symptom
Workload_summary.tch_total doesn't match actual allocations

### Diagnosis
```sql
-- Compare workload_summary with actual allocations
SELECT 
    ws.staff_id,
    ws.tch_total AS summary_tch,
    COALESCE(SUM(sub.tch), 0) AS actual_tch,
    ws.tch_total - COALESCE(SUM(sub.tch), 0) AS difference
FROM workload_summary ws
LEFT JOIN allocation a ON a.staff_id = ws.staff_id 
    AND a.academic_cycle_id = ws.academic_cycle_id
LEFT JOIN subject_offering so ON so.id = a.subject_offering_id
LEFT JOIN subject sub ON sub.id = so.subject_id
WHERE ws.academic_cycle_id = ?
GROUP BY ws.staff_id, ws.tch_total
HAVING ws.tch_total != COALESCE(SUM(sub.tch), 0);
```

### Solution
1. Rerun allocation for the semester (will regenerate workload_summary)
2. Or manually trigger workload refresh (if override was done)

---

## Issue 4: Cannot Override Allocation

### Symptom
Error: "Semester must be ALLOCATED (currently CLOSED)"

### Diagnosis
```sql
-- Check semester state for the allocation
SELECT sem.id, sem.label, sem.state
FROM allocation a
JOIN subject_offering so ON so.id = a.subject_offering_id
JOIN semester sem ON sem.id = so.semester_id
WHERE a.id = ?;
```

### Solution
1. If state = CLOSED: Run allocation first
2. If state = OPEN: Close semester, then run allocation
3. If state = FROZEN: Cannot override (finalized)

---

## Issue 5: Override Exceeds 20% Overload

### Symptom
Error: "Would exceed 20% overload limit: X TCH > Y TCH"

### Diagnosis
```sql
-- Check faculty current workload
SELECT 
    s.id,
    s.name,
    s.tch_norm,
    ws.tch_total,
    ws.deviation_hours,
    ROUND((ws.tch_total - s.tch_norm) / s.tch_norm * 100, 1) as overload_pct
FROM staff s
JOIN workload_summary ws ON ws.staff_id = s.id
WHERE s.id = ?;
```

### Solution
1. Choose different faculty with lower workload
2. Or reassign other subjects from target faculty first
3. 20% limit is strict (institutional requirement)

---

## Issue 6: Duplicate Preference Error

### Symptom
Error: "You have already used preference number X"

### Diagnosis
```sql
-- Check faculty's current preferences
SELECT preference_number, subject_offering_id
FROM faculty_preference
WHERE staff_id = ?
ORDER BY preference_number;
```

### Solution
1. Delete existing preference with that number:
   ```bash
   DELETE /api/preferences/{id}
   ```

2. Then submit new preference

---

## Issue 7: Shift Incompatibility

### Symptom
Error: "SHIFT2 faculty cannot select SHIFT1 subjects"

### Diagnosis
```sql
-- Check faculty shift and subject shift
SELECT 
    s.id,
    s.name,
    s.shift as faculty_shift,
    so.shift as subject_shift
FROM staff s, subject_offering so
WHERE s.id = ? AND so.id = ?;
```

### Solution
1. Faculty must select subjects matching their shift
2. SHIFT1+SHIFT2 faculty can select any shift
3. Contact coordinator if shift assignment is incorrect

---

## Issue 8: Authentication Failures

### Symptom
HTTP 401 Unauthorized or 403 Forbidden

### Diagnosis
1. Check if DEV_AUTH_BYPASS is enabled:
   ```bash
   grep DEV_AUTH_BYPASS .env
   ```

2. Check token validity:
   ```bash
   # Decode JWT token
   echo "<token>" | cut -d'.' -f2 | base64 -d
   ```

### Solution
1. If DEV_AUTH_BYPASS=True: No token needed (dev only)
2. If production: Ensure valid Google OAuth token
3. Check token expiration
4. Re-authenticate if needed

---

## Issue 9: Frozen Semester Cannot Be Modified

### Symptom
Error: "Semester is FROZEN (finalized by HOD)"

### Diagnosis
```sql
-- Check frozen status
SELECT id, label, state, frozen_at, frozen_by_staff_id
FROM semester
WHERE id = ?;
```

### Solution
1. Frozen semesters CANNOT be reopened (by design)
2. This is intentional (HOD finalization)
3. Contact HOD if changes are absolutely necessary
4. May require database intervention (not recommended)

---

## Issue 10: Allocation Produces Many Unallocated Subjects

### Symptom
Large number of subjects remain unallocated after allocation

### Diagnosis
```sql
-- Check faculty capacity vs subject demand
SELECT 
    'Total Faculty Capacity' as metric,
    SUM(tch_norm * 1.20) as value
FROM staff WHERE is_active = true
UNION ALL
SELECT 
    'Total Subject Demand' as metric,
    SUM(tch) as value
FROM subject s
JOIN subject_offering so ON so.subject_id = s.id
WHERE so.semester_id = ?;
```

### Solution
1. If demand > capacity: Insufficient faculty
   - Hire more faculty
   - Increase tch_norm for existing faculty
   - Reduce subject offerings

2. If capacity sufficient: Check constraints
   - Shift mismatches
   - Preference conflicts
   - Review unallocated reasons in allocation response

---

## Issue 11: Database Connection Errors

### Symptom
Error: "Could not connect to database"

### Diagnosis
```bash
# Test database connection
psql -h <host> -U <user> -d <database> -c "SELECT 1;"
```

### Solution
1. Check DATABASE_URL in .env
2. Verify database server is running
3. Check firewall rules
4. Verify credentials
5. Check connection pool settings

---

## Useful Diagnostic Queries

### Check System State
```sql
-- Overall system status
SELECT 
    'Active Cycle' as component,
    CONCAT(academic_year, ' ', semester_type) as status
FROM academic_cycle WHERE is_active = true
UNION ALL
SELECT 
    CONCAT('Semester: ', label) as component,
    state as status
FROM semester
ORDER BY component;
```

### Check Allocation Progress
```sql
-- Allocation progress by semester
SELECT 
    sem.label,
    COUNT(DISTINCT so.id) as total_offerings,
    COUNT(DISTINCT a.id) as allocated,
    COUNT(DISTINCT so.id) - COUNT(DISTINCT a.id) as unallocated,
    ROUND(COUNT(DISTINCT a.id)::numeric / NULLIF(COUNT(DISTINCT so.id), 0) * 100, 1) as pct_allocated
FROM semester sem
LEFT JOIN subject_offering so ON so.semester_id = sem.id
LEFT JOIN allocation a ON a.subject_offering_id = so.id
GROUP BY sem.id, sem.label
ORDER BY sem.id;
```

### Check Faculty Workload Distribution
```sql
-- Faculty workload distribution
SELECT 
    CASE 
        WHEN deviation_hours > 0 THEN 'OVERLOADED'
        WHEN deviation_hours < -2 THEN 'UNDERLOADED'
        ELSE 'BALANCED'
    END as status,
    COUNT(*) as faculty_count,
    ROUND(AVG(tch_total), 1) as avg_tch,
    ROUND(AVG(deviation_hours), 1) as avg_deviation
FROM workload_summary
WHERE academic_cycle_id = ?
GROUP BY status
ORDER BY status;
```

### Check Recent Audit Log
```sql
-- Recent actions
SELECT 
    action_type,
    actor_staff_id,
    details,
    created_at
FROM audit_log
ORDER BY created_at DESC
LIMIT 20;
```

### Check for Data Integrity Issues
```sql
-- Comprehensive integrity check
SELECT 'Orphaned Allocations' as issue, COUNT(*) as count
FROM allocation a
WHERE NOT EXISTS (SELECT 1 FROM staff s WHERE s.id = a.staff_id)
   OR NOT EXISTS (SELECT 1 FROM subject_offering so WHERE so.id = a.subject_offering_id)
UNION ALL
SELECT 'Duplicate Allocations', COUNT(*)
FROM (
    SELECT staff_id, subject_offering_id, COUNT(*) as cnt
    FROM allocation
    GROUP BY staff_id, subject_offering_id
    HAVING COUNT(*) > 1
) dup
UNION ALL
SELECT 'Orphaned Preferences', COUNT(*)
FROM faculty_preference fp
WHERE NOT EXISTS (SELECT 1 FROM staff s WHERE s.id = fp.staff_id)
   OR NOT EXISTS (SELECT 1 FROM subject_offering so WHERE so.id = fp.subject_offering_id)
UNION ALL
SELECT 'Workload Mismatches', COUNT(*)
FROM (
    SELECT ws.staff_id
    FROM workload_summary ws
    LEFT JOIN allocation a ON a.staff_id = ws.staff_id AND a.academic_cycle_id = ws.academic_cycle_id
    LEFT JOIN subject_offering so ON so.id = a.subject_offering_id
    LEFT JOIN subject sub ON sub.id = so.subject_id
    GROUP BY ws.staff_id, ws.tch_total
    HAVING ws.tch_total != COALESCE(SUM(sub.tch), 0)
) mismatch;
```

---

## Emergency Procedures

### Rollback Allocation
```sql
-- 1. Reopen semester (clears allocations)
-- Via API: POST /api/semester/{id}/open

-- 2. Or manual rollback
BEGIN;
DELETE FROM allocation WHERE subject_offering_id IN 
    (SELECT id FROM subject_offering WHERE semester_id = ?);
UPDATE semester SET state = 'OPEN', allocated_at = NULL WHERE id = ?;
COMMIT;
```

### Reset Semester to Initial State
```sql
BEGIN;
-- Clear allocations
DELETE FROM allocation WHERE subject_offering_id IN 
    (SELECT id FROM subject_offering WHERE semester_id = ?);

-- Clear preferences
DELETE FROM faculty_preference WHERE subject_offering_id IN 
    (SELECT id FROM subject_offering WHERE semester_id = ?);

-- Reset state
UPDATE semester SET 
    state = 'CLOSED',
    opened_at = NULL,
    closed_at = NULL,
    allocated_at = NULL,
    frozen_at = NULL,
    frozen_by_staff_id = NULL
WHERE id = ?;
COMMIT;
```

### Unfreeze Semester (Emergency Only)
```sql
-- ⚠️ USE WITH CAUTION - Violates workflow
UPDATE semester SET 
    state = 'ALLOCATED',
    frozen_at = NULL,
    frozen_by_staff_id = NULL
WHERE id = ?;
```

---

## Contact and Escalation

**For Technical Issues**:
1. Check logs: `logs/app.log`
2. Check audit log: `SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 50;`
3. Review documentation: `PHASE3_HOD_CONTROL_SUMMARY.md`

**For Data Issues**:
1. Run diagnostic queries above
2. Check data integrity
3. Review recent audit log
4. Restore from backup if needed

**For Workflow Issues**:
1. Check semester state
2. Verify user permissions
3. Review state transition rules
4. Check FINALIZATION_SUMMARY.md

---

**END OF TROUBLESHOOTING GUIDE**

