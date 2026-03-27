# Railway Production Diagnosis - Raw Output

## Timestamp
2026-03-28 (Continued from previous session)

---

## COMMAND 1: Health Check
```bash
curl.exe https://fwms-workload-system-production.up.railway.app/health
```

**OUTPUT:**
```json
{"status":"ok"}
```

**STATUS:** ✅ Health endpoint working

---

## COMMAND 2: Debug DB State Endpoint
```bash
curl.exe https://fwms-workload-system-production.up.railway.app/api/debug/db-state
```

**OUTPUT:**
```json
{"detail":"Not authenticated"}
```

**STATUS:** ❌ Requires authentication (endpoint protected)

---

## COMMAND 3: Dev Login (staff_id=16)
```bash
curl.exe -X POST https://fwms-workload-system-production.up.railway.app/api/auth/dev-login/16
```

**OUTPUT:**
```json
{"detail":"Not found"}
```

**STATUS:** ❌ Dev login endpoint returns 404

**REASON:** DEV_AUTH_BYPASS is disabled in production (as it should be for security)

---

## COMMAND 4: Railway Logs (Last 50 Lines)
```bash
railway logs --tail 50
```

**OUTPUT:**
```
COMMENT
psql:migrations/021_semester_specific_cycles.sql:58: NOTICE:  relation "cycle" already exists, skipping
CREATE TABLE
psql:migrations/021_semester_specific_cycles.sql:60: ERROR:  relation "idx_cycle_status" already exists
psql:migrations/021_semester_specific_cycles.sql:61: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:62: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:64: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:74: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:137: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:145: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:151: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:155: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:160: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:168: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:177: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:193: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:201: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:210: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:218: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:221: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:224: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:228: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:231: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:234: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:238: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:241: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:245: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:248: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:253: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:257: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:265: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:269: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:316: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:353: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:359: ERROR:  current transaction is aborted, commands ignored until end of transaction block
psql:migrations/021_semester_specific_cycles.sql:380: ERROR:  current transaction is aborted, commands ignored until end of transaction block
ROLLBACK
OK: 021_semester_specific_cycles.sql
All migrations done. Starting server...
Using in-memory session backend (DEVELOPMENT ONLY)
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     100.64.0.2:14440 - "GET /health HTTP/1.1" 200 OK
INFO:     100.64.0.3:48510 - "GET /health HTTP/1.1" 200 OK
INFO:     100.64.0.4:21600 - "GET /api/debug/db-state HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.6:48188 - "GET /api/debug/db-state HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.8:16546 - "POST /api/auth/dev-login/16 HTTP/1.1" 404 Not Found
```

Exit Code: 0</output>
</result>
</function_calls>

<function_calls>
<invoke name="fsAppend">
<parameter name="path">PROGRESS.md
## 🚨 CRITICAL FINDING: Migration 021 Failed on Railway

### Migration Error Pattern
```
psql:migrations/021_semester_specific_cycles.sql:60: ERROR:  relation "idx_cycle_status" already exists
psql:migrations/021_semester_specific_cycles.sql:61: ERROR:  current transaction is aborted, commands ignored until end of transaction block
[... 30+ more errors ...]
ROLLBACK
OK: 021_semester_specific_cycles.sql
```

### What Happened
1. Migration 021 started executing
2. Line 60: Index `idx_cycle_status` already exists → ERROR
3. PostgreSQL aborted the transaction
4. All subsequent commands in migration 021 were IGNORED
5. Transaction ROLLED BACK
6. Startup script marked it as "OK" and continued

### Impact
- Migration 021 did NOT complete successfully
- Data transformations in migration 021 were NOT applied:
  - `academic_year` table population
  - `cycle` table population with semester-specific cycles
  - `subject_offering` updates
  - Foreign key constraints
  - Data migrations from old `academic_cycle` to new `cycle`
- Railway database is in PARTIAL MIGRATION STATE
- Tables exist but DATA IS MISSING

### Why Local Works But Railway Doesn't
- Local: Migration 021 completed successfully, all data populated
- Railway: Migration 021 rolled back, tables empty or partially populated

---

## Railway Logs - Recent Activity
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     100.64.0.2:14440 - "GET /health HTTP/1.1" 200 OK
INFO:     100.64.0.3:48510 - "GET /health HTTP/1.1" 200 OK
INFO:     100.64.0.4:21600 - "GET /api/debug/db-state HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.6:48188 - "GET /api/debug/db-state HTTP/1.1" 401 Unauthorized
INFO:     100.64.0.8:16546 - "POST /api/auth/dev-login/16 HTTP/1.1" 404 Not Found
```

**Server Status:** Running, health checks passing
**Auth Status:** DEV_AUTH_BYPASS disabled (correct for production)
**Debug Endpoint:** Protected by authentication

---

## Root Cause Analysis

### Problem
Migration 021 failed on Railway due to pre-existing index `idx_cycle_status`

### Why It Failed
- Migration 021 uses `CREATE INDEX` without `IF NOT EXISTS`
- Index already existed from previous deployment attempt
- PostgreSQL aborted entire transaction
- All data population commands were skipped

### Why Startup Script Didn't Catch It
```bash
# startup.sh line ~30
psql "$DATABASE_URL" -f "migrations/021_semester_specific_cycles.sql" || exit 1
echo "OK: 021_semester_specific_cycles.sql"
```

The `|| exit 1` should have caught the error, but the script continued. This suggests:
- psql returned exit code 0 despite ROLLBACK
- OR startup.sh error handling is not working correctly

---

## Next Steps Required

### Option A: Fix Migration 021 (RECOMMENDED)
1. Add `IF NOT EXISTS` to all CREATE INDEX statements
2. Add `IF NOT EXISTS` to all CREATE TABLE statements
3. Wrap data population in conditional checks
4. Make migration idempotent
5. Redeploy to Railway

### Option B: Reset Railway Database
1. Drop all tables in Railway database
2. Re-run all migrations from scratch
3. Seed data

### Option C: Manual Data Population
1. Connect to Railway database directly
2. Manually run data population queries
3. Verify data integrity

---

## Summary for External AI

**ISSUE:** Railway production returns 0 subject offerings, local returns 78

**ROOT CAUSE:** Migration 021 failed on Railway deployment due to pre-existing index, causing transaction rollback. All data population commands were skipped.

**EVIDENCE:**
- Railway logs show: `ERROR: relation "idx_cycle_status" already exists` followed by `ROLLBACK`
- Server started successfully but database is in partial migration state
- Tables exist but critical data (academic_year, cycle, subject_offering) is missing or incomplete

**RECOMMENDATION:** Fix migration 021 to be idempotent (add IF NOT EXISTS clauses) and redeploy.
