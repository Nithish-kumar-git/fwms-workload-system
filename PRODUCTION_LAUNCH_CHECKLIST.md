# PRODUCTION LAUNCH CHECKLIST

## Quick Reference for Production Deployment

This is a condensed checklist for launching the Faculty Subject Allocation System to production.

---

## PRE-LAUNCH CRITICAL ACTIONS

### 1. Environment Configuration ⚠️ CRITICAL

```bash
# .env.production file
DEV_AUTH_BYPASS=False  # ⚠️ MUST BE FALSE
GOOGLE_CLIENT_ID=<production-client-id>
GOOGLE_CLIENT_SECRET=<production-secret>
GOOGLE_REDIRECT_URI=<production-redirect-uri>
DATABASE_URL=postgresql://user:pass@prod-host:5432/dbname
LOG_LEVEL=INFO
```

**Verification**:
```bash
# Check DEV_AUTH_BYPASS is disabled
grep DEV_AUTH_BYPASS .env.production
# Expected: DEV_AUTH_BYPASS=False
```

---

### 2. Database Setup

**Run Migrations**:
```bash
psql -d production_db -f migrations/001_initial_schema.sql
psql -d production_db -f migrations/002_window_lifecycle.sql
psql -d production_db -f migrations/003_seed_minimal.sql
# ... continue through all migrations
psql -d production_db -f migrations/014_semester_state_management.sql
```

**Verify Schema**:
```sql
-- Check semester.state column exists
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'semester' AND column_name = 'state';
-- Expected: state | character varying
```

**Create Indexes**:
```sql
CREATE INDEX IF NOT EXISTS idx_allocation_staff ON allocation(staff_id);
CREATE INDEX IF NOT EXISTS idx_allocation_cycle ON allocation(academic_cycle_id);
CREATE INDEX IF NOT EXISTS idx_allocation_offering ON allocation(subject_offering_id);
CREATE INDEX IF NOT EXISTS idx_preference_staff ON faculty_preference(staff_id);
CREATE INDEX IF NOT EXISTS idx_preference_offering ON faculty_preference(subject_offering_id);
CREATE INDEX IF NOT EXISTS idx_workload_cycle ON workload_summary(academic_cycle_id);
```

**Backup Database**:
```bash
pg_dump production_db > backup_pre_launch_$(date +%Y%m%d_%H%M%S).sql
```

---

### 3. Initial Data Setup

**Create Academic Cycle**:
```sql
INSERT INTO academic_cycle (academic_year, semester_type, is_active)
VALUES ('2025-2026', 'EVEN', true);
```

**Create Semesters**:
```sql
INSERT INTO semester (label, state) VALUES
('Semester I', 'CLOSED'),
('Semester II', 'CLOSED'),
('Semester III', 'CLOSED');
```

**Import Faculty and Subjects**:
- Use existing import scripts
- Verify all required fields populated

---

### 4. Security Checklist

- [ ] DEV_AUTH_BYPASS=False in production
- [ ] Google OAuth production credentials configured
- [ ] Database credentials not in version control
- [ ] HTTPS enabled
- [ ] CORS configured for production domain
- [ ] Firewall rules configured
- [ ] Database access restricted

---

### 5. Monitoring Setup

- [ ] Application logs configured (`logs/app.log`)
- [ ] Log rotation enabled
- [ ] Database connection monitoring
- [ ] Error tracking (Sentry or similar)
- [ ] Audit log review process established

---

## POST-LAUNCH SMOKE TESTS

### Test 1: Authentication
```bash
# Test login endpoint
curl -X POST https://your-domain.com/api/auth/login
# Expected: Redirect to Google OAuth
```

### Test 2: Semester State
```bash
# Get semester state (requires auth token)
curl -H "Authorization: Bearer <token>" \
  https://your-domain.com/api/semester/1/state
# Expected: {"id": 1, "label": "Semester I", "state": "CLOSED", ...}
```

### Test 3: Open Semester
```bash
# Open semester (coordinator only)
curl -X POST -H "Authorization: Bearer <coordinator-token>" \
  https://your-domain.com/api/semester/1/open
# Expected: {"success": true, "message": "Semester 1 opened..."}
```

### Test 4: Submit Preference
```bash
# Submit preference (faculty)
curl -X POST -H "Authorization: Bearer <faculty-token>" \
  -H "Content-Type: application/json" \
  -d '{"subject_offering_id": 1, "preference_number": 1}' \
  https://your-domain.com/api/preferences
# Expected: {"success": true, "preference_id": X}
```

---

## CRITICAL VALIDATION QUERIES

### Check System Health

```sql
-- 1. Verify semester states
SELECT id, label, state, opened_at, closed_at, allocated_at, frozen_at
FROM semester
ORDER BY id;

-- 2. Verify active cycle
SELECT id, academic_year, semester_type, is_active
FROM academic_cycle
WHERE is_active = true;

-- 3. Check allocation counts
SELECT 
    sem.label,
    COUNT(DISTINCT so.id) as total_offerings,
    COUNT(DISTINCT a.id) as allocated_count,
    COUNT(DISTINCT so.id) - COUNT(DISTINCT a.id) as unallocated_count
FROM semester sem
LEFT JOIN subject_offering so ON so.semester_id = sem.id
LEFT JOIN allocation a ON a.subject_offering_id = so.id
GROUP BY sem.id, sem.label
ORDER BY sem.id;

-- 4. Verify workload accuracy
SELECT 
    s.id,
    s.name,
    s.tch_norm,
    ws.tch_total,
    ws.deviation_hours,
    ROUND((ws.tch_total - s.tch_norm) / s.tch_norm * 100, 1) as overload_pct
FROM staff s
LEFT JOIN workload_summary ws ON ws.staff_id = s.id
WHERE s.is_active = true
ORDER BY overload_pct DESC;

-- 5. Check for data integrity issues
-- No orphaned allocations
SELECT COUNT(*) as orphaned_allocations
FROM allocation a
WHERE NOT EXISTS (SELECT 1 FROM staff s WHERE s.id = a.staff_id)
   OR NOT EXISTS (SELECT 1 FROM subject_offering so WHERE so.id = a.subject_offering_id);
-- Expected: 0

-- No duplicate allocations
SELECT staff_id, subject_offering_id, COUNT(*)
FROM allocation
GROUP BY staff_id, subject_offering_id
HAVING COUNT(*) > 1;
-- Expected: 0 rows

-- 6. Verify audit log
SELECT action_type, COUNT(*) as count
FROM audit_log
GROUP BY action_type
ORDER BY count DESC;
```

---

## ROLLBACK PLAN

If critical issues are discovered post-launch:

### 1. Immediate Actions
```bash
# Stop application
systemctl stop faculty-allocation-api

# Restore database from backup
psql -d production_db < backup_pre_launch_YYYYMMDD_HHMMSS.sql

# Revert code deployment
git checkout <previous-stable-tag>
```

### 2. Investigate
- Check application logs: `tail -f logs/app.log`
- Check database logs
- Review audit_log table
- Identify root cause

### 3. Fix and Redeploy
- Apply fix
- Test in staging
- Redeploy to production

---

## KNOWN ISSUES AND WORKAROUNDS

### Minor Issue 1: Error Response Format Inconsistency
**Impact**: Low (functional, cosmetic issue)
**Description**: Some endpoints return `{"success": false}`, others throw HTTPException
**Workaround**: Frontend should handle both formats
**Fix**: Not required for launch (can be standardized later)

### Minor Issue 2: Workload Summary Hardcoded Parameters
**Impact**: Low (functional limitation)
**Description**: GET `/api/admin/workload-summary` hardcoded to "2025-2026" EVEN
**Workaround**: Modify service code if different cycle needed
**Fix**: Not required for launch (can add query params later)

---

## SUPPORT CONTACTS

**Technical Issues**:
- Check logs: `logs/app.log`
- Check audit log: `SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 50;`
- Review documentation: `PHASE3_HOD_CONTROL_SUMMARY.md`

**Database Issues**:
- Verify migrations applied
- Check connection pool
- Review slow query log

**Authentication Issues**:
- Verify Google OAuth credentials
- Check DEV_AUTH_BYPASS setting
- Review JWT token expiration

---

## FINAL SIGN-OFF

Before launching to production, verify:

- [ ] All migrations applied successfully
- [ ] Database backup created
- [ ] DEV_AUTH_BYPASS=False verified
- [ ] Google OAuth configured and tested
- [ ] Smoke tests passed
- [ ] Monitoring configured
- [ ] Rollback plan documented
- [ ] Support contacts identified

**Signed Off By**: ___________________
**Date**: ___________________
**Time**: ___________________

---

## QUICK REFERENCE: STATE FLOW

```
CLOSED → OPEN → CLOSED → ALLOCATED → FROZEN
         ↑                    ↓
         └────────────────────┘
              (reopen)
```

**State Rules**:
- OPEN: Preferences can be submitted/deleted
- CLOSED: Preferences locked, ready for allocation
- ALLOCATED: Allocation complete, can be edited by HOD
- FROZEN: Finalized, no changes allowed

---

**END OF CHECKLIST**

