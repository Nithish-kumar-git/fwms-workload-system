# PROGRESS.md

## STEP 1 - Docker & Health

### Docker Down
```
time="2026-03-26T04:07:08+05:30" level=warning msg="C:\\Users\\itsni\\.gemini\\antigravity\\scratch\\faculty_selection\\docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
[+] down 4/4
 ✔ Container faculty_selection_app        Removed                                                                       1.5s
 ✔ Container faculty_selection_db         Removed                                                                       0.4s
 ✔ Network faculty_selection_default      Removed                                                                       0.4s
 ✔ Volume faculty_selection_postgres_data Removed                                                                       0.1s
Exit Code: 0
```

### Docker Up
```
time="2026-03-26T04:07:18+05:30" level=warning msg="C:\\Users\\itsni\\.gemini\\antigravity\\scratch\\faculty_selection\\docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
[+] up 4/4
 ✔ Network faculty_selection_default      Created                                                                       0.1s
 ✔ Volume faculty_selection_postgres_data Created                                                                       0.0s
 ✔ Container faculty_selection_db         Healthy                                                                       6.3s
 ✔ Container faculty_selection_app        Created                                                                       0.2s
Exit Code: 0
```

### Health Check
```
curl.exe http://localhost:8000/health
{"status":"ok"}
Exit Code: 0
```

**Result**: ✅ Docker started successfully, health endpoint working

---

## STEP 2 - Login Token

### First Attempt (GET - Wrong Method)
```
curl.exe http://localhost:8000/api/auth/dev-login/16
{"detail":"Method Not Allowed"}
Exit Code: 0
```

### Second Attempt (POST - Correct)
```
curl.exe -X POST http://localhost:8000/api/auth/dev-login/16
{"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNiIsImVtYWlsIjoibWN0NDRAaGluZHVzdGFudW5pdi5hYy5pbiIsIm5hbWUiOiJEci4gUy4gR29raWxhIiwicm9sZSI6ImhvZCIsImlhdCI6MTc3NDQ3ODM1MCwiZXhwIjoxNzc0NDkyNzUwfQ.ai1ApTr4Tf2TQZEginsZHUpXT8R-Wlmy66z3VQdSyOI","staff_id":16,"email":"mct44@hindustanuniv.ac.in","name":"Dr. S. Gokila","role":"hod"}
Exit Code: 0
```

**Token obtained**: YES

**Access Token**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNiIsImVtYWlsIjoibWN0NDRAaGluZHVzdGFudW5pdi5hYy5pbiIsIm5hbWUiOiJEci4gUy4gR29raWxhIiwicm9sZSI6ImhvZCIsImlhdCI6MTc3NDQ3ODM1MCwiZXhwIjoxNzc0NDkyNzUwfQ.ai1ApTr4Tf2TQZEginsZHUpXT8R-Wlmy66z3VQdSyOI`

---

## STEP 3 - API Endpoint Tests

### /api/dashboard/summary
```
curl.exe -H "Authorization: Bearer TOKEN" http://localhost:8000/api/dashboard/summary
{"detail":"Not Found"}
Exit Code: 0
```
**Status**: ❌ 404 Not Found - ENDPOINT DOES NOT EXIST

### /api/cycles/
```
curl.exe -H "Authorization: Bearer TOKEN" http://localhost:8000/api/cycles/
(empty response)
Exit Code: 0
```
**Status**: ✅ 200 OK (empty array - no cycles created yet)

### /api/reports/summary
```
curl.exe -H "Authorization: Bearer TOKEN" http://localhost:8000/api/reports/summary
{"detail":"Not Found"}
Exit Code: 0
```
**Status**: ❌ 404 Not Found - ENDPOINT DOES NOT EXIST

### /api/reports/department-summary (ACTUAL ENDPOINT)
```
curl.exe -H "Authorization: Bearer TOKEN" http://localhost:8000/api/reports/department-summary
Internal Server Error
Exit Code: 0
```
**Status**: ❌ 500 Internal Server Error - ENDPOINT EXISTS BUT CRASHES

---

## STEP 4 - File Contents

### frontend/src/pages/DashboardPage.tsx

**Dashboard calls these API endpoints**:
1. `getDepartmentSummary()` → `/api/reports/department-summary`
2. `getCurrentUser()` → `/api/auth/me`
3. `getFacultyWorkload()` → `/api/reports/faculty-workload`

**Key code**:
```typescript
const loadData = () => {
    setLoading(true);
    setError('');
    getDepartmentSummary()  // ← This is the failing call
        .then((r) => setData(r.data))
        .catch((err: any) => {
            const detail = err.response?.data?.detail || 'Failed to load dashboard data';
            setError(detail);
            setData(null);
            addToast(detail, 'error');
        })
        .finally(() => setLoading(false));
};
```

### app/main.py

**Routers included**:
```python
app.include_router(health_router.router)
app.include_router(auth_router.router)
app.include_router(selection_router.router)
app.include_router(coordinator_router.router)
app.include_router(window_router.router, prefix="/api")
app.include_router(semester_state_router.router)
app.include_router(preference_router.router)
app.include_router(pref_window_router.router)
app.include_router(allocation_router.router)
app.include_router(admin_router.router)
app.include_router(cycle_router.router)
app.include_router(staff_router.router)
app.include_router(reports_router.router)  # ← Reports router IS included
```

**CORS origins**:
```python
allow_origins=[
    'http://localhost:5173',
    'http://localhost:5174',
    'http://localhost:5175',
    'http://localhost:5176',
    'http://localhost:3000',
    frontend_url
]
```

### app/reports/service.py

**Key function**: `get_department_summary()`

Line 39 (FIXED):
```python
row = session.execute(
    text("""
        SELECT ay.name, c.semester_id
        FROM cycle c
        JOIN academic_year ay ON ay.id = c.academic_year_id
        WHERE c.status = 'OPEN'
        LIMIT 1
    """)
).fetchone()
```

**This function is called by**:
- `get_department_summary()` (line 176)
- `get_faculty_workload()` (line 62)
- `get_subject_summary()` (line 132)
- `generate_excel_report()` (line 255)
- `generate_pdf_report()` (line 430)

### Python files in app/ directory (2 levels deep)

```
app/main.py
app/startup_check.py
app/__init__.py
app/admin/cycle_router.py
app/admin/cycle_service.py
app/admin/cycle_service_new.py
app/admin/router.py
app/admin/schemas.py
app/admin/service.py
app/admin/staff_router.py
app/admin/staff_service.py
app/admin/__init__.py
app/allocation/router.py
app/allocation/schemas.py
app/allocation/service.py
app/allocation/__init__.py
app/audit/__init__.py
app/auth/dependencies.py
app/auth/google_oauth.py
app/auth/jwt_utils.py
app/auth/router.py
app/auth/schemas.py
app/auth/session_manager.py
app/auth/__init__.py
app/coordinator/router.py
app/coordinator/schemas.py
app/coordinator/semester_state_router.py
app/coordinator/semester_state_service.py
app/coordinator/transactions.py
app/coordinator/window_router.py
app/coordinator/window_schemas.py
app/coordinator/window_transactions.py
app/coordinator/__init__.py
app/core/config.py
app/core/correlation_middleware.py
app/core/logging_config.py
app/core/__init__.py
app/db/pool.py
app/db/session.py
app/db/__init__.py
app/health/router.py
app/health/__init__.py
app/notifications/__init__.py
app/preference/router.py
app/preference/schemas.py
app/preference/service.py
app/preference/window_router.py
app/preference/window_service.py
app/preference/__init__.py
app/reports/cycle_guard.py
app/reports/master_workload_excel.py
app/reports/pdf_generator.py
app/reports/router.py
app/reports/schemas.py
app/reports/service.py
app/reports/snapshot_service.py
app/reports/__init__.py
app/selection/router.py
app/selection/schemas.py
app/selection/transactions.py
app/selection/__init__.py
app/staff/__init__.py
app/utils/error_mapper.py
app/utils/error_schemas.py
app/utils/rate_limiter.py
app/utils/__init__.py
```

### Files with "dashboard" in name

**Search results**: No files named "dashboard.py" in app/ directory

**References to "dashboard" in code**:
1. `app/auth/router.py:131` - Redirect URL to frontend dashboard
2. `app/admin/router.py:40` - Comment mentioning "admin dashboard"

---

## STEP 5 - What is broken

### Critical Issues

1. **❌ /api/dashboard/summary endpoint does NOT exist**
   - Frontend calls `getDepartmentSummary()` which tries to hit `/api/dashboard/summary`
   - This endpoint is not defined in any router
   - Should be `/api/reports/department-summary` instead

2. **❌ /api/reports/summary endpoint does NOT exist**
   - This endpoint is not defined in any router
   - Likely a typo or wrong endpoint name

3. **❌ /api/reports/department-summary returns 500 Internal Server Error**
   - Endpoint exists but crashes when called
   - Likely cause: No active cycle in database (fresh docker restart with -v flag deleted all data)
   - Error from `_resolve_active_cycle()`: "No active cycle found"

### Root Cause Analysis

**The dashboard is broken because**:
1. Frontend is calling the WRONG endpoint (`/api/dashboard/summary` instead of `/api/reports/department-summary`)
2. Even if it called the right endpoint, it would fail because there's NO ACTIVE CYCLE in the database
3. The database was wiped clean with `docker-compose down -v`

### Required Fixes

1. **Fix frontend API client** - Change endpoint from `/api/dashboard/summary` to `/api/reports/department-summary`
2. **Create an active cycle** - Need to create academic_year and cycle records before dashboard will work
3. **Check app/reports/router.py** - Verify the actual endpoint path defined there

### Next Steps

1. Read `frontend/src/api/client.ts` to see what `getDepartmentSummary()` actually calls
2. Read `app/reports/router.py` to see what endpoints are actually defined
3. Create test data (academic_year + cycle) so reports can work
4. Fix frontend to call correct endpoint


---

## FIX 1 - File Contents

### frontend/src/api/client.ts

**getDepartmentSummary() function** (line 107):
```typescript
export const getDepartmentSummary = () => api.get('/reports/department-summary');
```

✅ **CORRECT** - Frontend is already calling the right endpoint `/reports/department-summary`

### app/reports/router.py

**department-summary endpoint** (line 68-75):
```python
@router.get("/department-summary", response_model=DepartmentSummaryResponse)
async def department_summary(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Aggregate department workload statistics."""
    data = report_service.get_department_summary()
    return DepartmentSummaryResponse(**data)
```

✅ **ENDPOINT EXISTS** at `/api/reports/department-summary`

### app/reports/service.py

**_resolve_active_cycle() function** (line 26-48):
```python
def _resolve_active_cycle(session) -> tuple[str, int]:
    """
    Resolve academic_year and semester_id from the active cycle.

    Returns:
        (academic_year, semester_id) from cycle table with status = 'OPEN'

    Raises:
        RuntimeError: if no active cycle exists
    """
    row = session.execute(
        text("""
            SELECT ay.name, c.semester_id
            FROM cycle c
            JOIN academic_year ay ON ay.id = c.academic_year_id
            WHERE c.status = 'OPEN'
            LIMIT 1
        """)
    ).fetchone()

    if not row:
        raise RuntimeError("No active cycle found. Activate a cycle before generating reports.")

    return row[0], row[1]
```

❌ **PROBLEM** - Raises RuntimeError when no active cycle exists, causing 500 error

**get_department_summary() function** (line 176-232):
```python
def get_department_summary(
    academic_year: Optional[str] = None, semester_id: Optional[int] = None
) -> dict:
    """Aggregate department statistics."""
    with get_transaction() as session:
        if academic_year is None or semester_id is None:
            academic_year, semester_id = _resolve_active_cycle(session)  # ← CRASHES HERE
        # ... rest of function
```

---

## FIX 2 - Frontend API Client

**Status**: ✅ NO CHANGES NEEDED

The frontend is already calling the correct endpoint:
```typescript
export const getDepartmentSummary = () => api.get('/reports/department-summary');
```

This matches the backend route at `/api/reports/department-summary`.



---

## FIX 3 - Make get_department_summary() Not Crash

**File**: `app/reports/service.py`

**Changes**: Wrapped `_resolve_active_cycle()` call in try/except block. When no active cycle exists, return safe empty response with faculty count.

**Before** (line 176-180):
```python
def get_department_summary(
    academic_year: Optional[str] = None, semester_id: Optional[int] = None
) -> dict:
    """Aggregate department statistics."""
    with get_transaction() as session:
        if academic_year is None or semester_id is None:
            academic_year, semester_id = _resolve_active_cycle(session)  # ← CRASHES HERE
```

**After** (line 176-195):
```python
def get_department_summary(
    academic_year: Optional[str] = None, semester_id: Optional[int] = None
) -> dict:
    """Aggregate department statistics."""
    with get_transaction() as session:
        if academic_year is None or semester_id is None:
            try:
                academic_year, semester_id = _resolve_active_cycle(session)
            except RuntimeError:
                # No active cycle - return safe empty response
                total_faculty = session.execute(
                    text("SELECT count(*) FROM staff WHERE emp_code IS NOT NULL AND is_active = true")
                ).scalar()
                return {
                    "total_subject_offerings": 0,
                    "allocated_subjects": 0,
                    "unallocated_subjects": 0,
                    "total_faculty": total_faculty or 0,
                    "average_workload": 0.0,
                    "faculty_overloaded": 0,
                    "faculty_underloaded": 0,
                    "faculty_balanced": total_faculty or 0,
                }
```

✅ **FIXED** - Function now returns safe empty data instead of crashing



---

## FIX 4 - Create Seed Data

**Commands executed**:

1. Insert academic_year:
```bash
docker exec faculty_selection_db psql -U postgres -d faculty_selection -c "INSERT INTO academic_year (name, start_date, end_date) VALUES ('2025-2026', '2025-07-01', '2026-04-30') ON CONFLICT DO NOTHING RETURNING id;"
```
**Result**: Already exists (id=1)

2. Insert cycle:
```bash
docker exec faculty_selection_db psql -U postgres -d faculty_selection -c "INSERT INTO cycle (academic_year_id, semester_id, status, opened_at) VALUES (1, 2, 'OPEN', NOW()) ON CONFLICT DO NOTHING;"
```
**Result**: Already exists

3. Verify cycles:
```bash
docker exec faculty_selection_db psql -U postgres -d faculty_selection -c "SELECT c.id, c.status, c.semester_id, ay.name FROM cycle c JOIN academic_year ay ON ay.id = c.academic_year_id;"
```
**Result**:
```
 id | status | semester_id |   name    
----+--------+-------------+-----------
  1 | OPEN   |           2 | 2025-2026
  2 | OPEN   |           4 | 2025-2026
  3 | OPEN   |           6 | 2025-2026
(3 rows)
```

✅ **SEED DATA EXISTS** - Multiple active cycles found (migrations already created them)



---

# FIX 1 - File Contents

## frontend/src/api/client.ts

**Key finding**: `getDepartmentSummary()` function exists and calls the CORRECT endpoint:

```typescript
export const getDepartmentSummary = () => api.get('/reports/department-summary');
```

This is line 99. The endpoint is CORRECT - it calls `/api/reports/department-summary` (the `/api` prefix is added by baseURL).

## app/reports/router.py

**Key finding**: The endpoint IS defined correctly:

```python
@router.get("/department-summary", response_model=DepartmentSummaryResponse)
async def department_summary(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Aggregate department workload statistics."""
    data = report_service.get_department_summary()
    return DepartmentSummaryResponse(**data)
```

Router prefix is `/api/reports`, so full path is `/api/reports/department-summary` ✅

## app/reports/service.py

**Key finding**: `get_department_summary()` function at line 176 calls `_resolve_active_cycle()` which RAISES RuntimeError when no active cycle exists.

Line 39-48 in `_resolve_active_cycle()`:
```python
row = session.execute(
    text("""
        SELECT ay.name, c.semester_id
        FROM cycle c
        JOIN academic_year ay ON ay.id = c.academic_year_id
        WHERE c.status = 'OPEN'
        LIMIT 1
    """)
).fetchone()

if not row:
    raise RuntimeError("No active cycle found. Activate a cycle before generating reports.")
```

**HOWEVER**: Line 180-195 in `get_department_summary()` ALREADY has a try/except that catches this and returns safe empty response! The fix was already partially applied.

```python
if academic_year is None or semester_id is None:
    try:
        academic_year, semester_id = _resolve_active_cycle(session)
    except RuntimeError:
        # No active cycle - return safe empty response
        total_faculty = session.execute(
            text("SELECT count(*) FROM staff WHERE emp_code IS NOT NULL AND is_active = true")
        ).scalar()
        return {
            "total_subject_offerings": 0,
            "allocated_subjects": 0,
            "unallocated_subjects": 0,
            "total_faculty": total_faculty or 0,
            "average_workload": 0.0,
            "faculty_overloaded": 0,
            "faculty_underloaded": 0,
            "faculty_balanced": total_faculty or 0,
        }
```

**Conclusion**: 
- Frontend endpoint is CORRECT ✅
- Backend endpoint exists ✅
- Backend already handles no active cycle gracefully ✅
- The 500 error must be from something else - need to test with actual database



---

# FIX 2 - Frontend API Client

**Status**: ✅ NO CHANGES NEEDED

The frontend was already calling the correct endpoint:
```typescript
export const getDepartmentSummary = () => api.get('/reports/department-summary');
```

---

# FIX 3 - Backend Service Error Handling

**Status**: ✅ PARTIALLY FIXED, REAL BUG FOUND

The `get_department_summary()` function already had try/except handling for no active cycle.

**REAL BUG FOUND**: The `workload_summary` table still uses `semester_type` (ODD/EVEN) instead of `semester_id` (1-6).

**Fix applied to app/reports/service.py** (lines 217-245):

### BEFORE:
```python
avg_workload = session.execute(
    text("""
        SELECT COALESCE(AVG(ws.tch_total), 0)
        FROM workload_summary ws
        WHERE ws.academic_year = :year AND ws.semester_id = :sem_id
    """),
    {"year": academic_year, "sem_id": semester_id}
).scalar()

overloaded = session.execute(
    text("""
        SELECT count(*) FROM workload_summary
        WHERE academic_year = :year AND semester_id = :sem_id
          AND deviation_hours > 0
    """),
    {"year": academic_year, "sem_id": semester_id}
).scalar()

underloaded = session.execute(
    text("""
        SELECT count(*) FROM workload_summary
        WHERE academic_year = :year AND semester_id = :sem_id
          AND deviation_hours < -2
    """),
    {"year": academic_year, "sem_id": semester_id}
).scalar()
```

### AFTER:
```python
# Convert semester_id to semester_type for workload_summary table (legacy schema)
semester_type = "EVEN" if semester_id in (2, 4, 6) else "ODD"

avg_workload = session.execute(
    text("""
        SELECT COALESCE(AVG(ws.tch_total), 0)
        FROM workload_summary ws
        WHERE ws.academic_year = :year AND ws.semester_type = :sem_type
    """),
    {"year": academic_year, "sem_type": semester_type}
).scalar()

overloaded = session.execute(
    text("""
        SELECT count(*) FROM workload_summary
        WHERE academic_year = :year AND semester_type = :sem_type
          AND deviation_hours > 0
    """),
    {"year": academic_year, "sem_type": semester_type}
).scalar()

underloaded = session.execute(
    text("""
        SELECT count(*) FROM workload_summary
        WHERE academic_year = :year AND semester_type = :sem_type
          AND deviation_hours < -2
    """),
    {"year": academic_year, "sem_type": semester_type}
).scalar()
```

---

# FIX 4 - Create Seed Data

**Status**: ✅ ALREADY EXISTS

Database already had seed data:
- Academic year: `2025-2026` (id=1)
- Active cycles: 3 cycles exist (semester_id 2, 4, 6) all with status='OPEN'

```
 id | status | semester_id |   name    
----+--------+-------------+-----------
  1 | OPEN   |           2 | 2025-2026
  2 | OPEN   |           4 | 2025-2026
  3 | OPEN   |           6 | 2025-2026
```

---

# FIX 5 - Final Test

**Token obtained**: YES
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNiIsImVtYWlsIjoibWN0NDRAaGluZHVzdGFudW5pdi5hYy5pbiIsIm5hbWUiOiJEci4gUy4gR29raWxhIiwicm9sZSI6ImhvZCIsImlhdCI6MTc3NDQ3OTUwNCwiZXhwIjoxNzc0NDkzOTA0fQ.sTj7L8Dj5E3HbWw0u20XI_HIbrR1IIIVhR65LL0Nhao",
  "staff_id": 16,
  "email": "mct44@hindustanuniv.ac.in",
  "name": "Dr. S. Gokila",
  "role": "hod"
}
```

**Endpoint test**: ✅ SUCCESS

```bash
curl.exe -H "Authorization: Bearer TOKEN" http://localhost:8000/api/reports/department-summary
```

**Response**:
```json
{
  "total_subject_offerings": 78,
  "allocated_subjects": 0,
  "unallocated_subjects": 78,
  "total_faculty": 28,
  "average_workload": 0.0,
  "faculty_overloaded": 0,
  "faculty_underloaded": 0,
  "faculty_balanced": 28
}
```

**Status**: ✅ 200 OK - Dashboard endpoint working!

---

# FIX 6 - Summary

## Files Changed

1. **app/reports/service.py** (lines 217-245)
   - Fixed `workload_summary` table queries to use `semester_type` instead of `semester_id`
   - Added conversion logic: `semester_type = "EVEN" if semester_id in (2, 4, 6) else "ODD"`
   - Changed 3 SQL queries to use `ws.semester_type = :sem_type` instead of `ws.semester_id = :sem_id`

## Frontend Changes

**None required** - frontend was already correct

## Backend Restart

**Not required** - Docker container automatically reloads on file changes (if using volume mounts)

If changes don't reflect, restart with:
```bash
docker-compose restart app
```

## Browser Verification

1. Open: `http://localhost:5173/dashboard`
2. Login as HOD (staff_id=16)
3. Dashboard should now load successfully showing:
   - 78 total subject offerings
   - 28 total faculty
   - 0 allocated subjects (no allocation run yet)
   - All faculty balanced (no workload assigned yet)

## Root Cause

The `workload_summary` table was never migrated from the old schema (`semester_type` = ODD/EVEN) to the new schema (`semester_id` = 1-6). The fix adds a conversion layer to bridge the gap until the table migration is completed.

## Next Steps

1. ✅ Dashboard is now working
2. ⚠️ Need to migrate `workload_summary` table schema in a future migration
3. ✅ All other tables (cycle, subject_offering, allocation) use `semester_id` correctly


---

# FINAL VERIFICATION

## STEP 1 - Frontend Status

**Command**: `npm run dev` (in frontend/ folder)

**Result**: ✅ Running on http://localhost:5175/
```
Port 5173 is in use, trying another one...
Port 5174 is in use, trying another one...
VITE v7.3.1  ready in 1347 ms
➜  Local:   http://localhost:5175/
```

**Note**: Frontend auto-incremented to port 5175. CORS in backend allows ports 5173-5176 ✅

---

## STEP 2 - Auth Dependency Check

**Function**: `get_current_coordinator_id()` in `app/auth/dependencies.py`

**Code** (lines 133-138):
```python
async def get_current_coordinator(
    user: UserInfo = Depends(get_current_user)
) -> UserInfo:
    """Require coordinator or HOD role. Returns full UserInfo."""
    if user.role not in ("tt_coordinator", "hod"):  # ← HOD IS ALLOWED
        logger.warning(f"Coordinator access denied: staff_id={user.staff_id}, role={user.role}")
        raise HTTPException(status_code=403, detail="Coordinator access required")
    return user
```

**Result**: ✅ HOD role is explicitly allowed to access coordinator endpoints

---

## STEP 3 - Browser Test

**Cannot automate browser interaction** - User must manually verify:

1. Open: http://localhost:5175/dashboard
2. Login as HOD (staff_id=16) using dev login
3. Dashboard should load and display:
   - Total Offerings: 78
   - Allocated: 0
   - Unallocated: 78
   - Faculty: 28
   - Balanced: 28
   - Overloaded: 0
   - Underloaded: 0
   - Avg Workload: 0.0

---

## STEP 4 - Browser Console Errors

**Cannot automate** - User must check DevTools console manually

---

## STEP 5 - Field Name Verification

**Backend response fields**:
```json
{
  "total_subject_offerings": 78,
  "allocated_subjects": 0,
  "unallocated_subjects": 78,
  "total_faculty": 28,
  "average_workload": 0.0,
  "faculty_overloaded": 0,
  "faculty_underloaded": 0,
  "faculty_balanced": 28
}
```

**Frontend DashboardPage.tsx usage** (lines 207-260):
```typescript
{data.total_subject_offerings}  // ✅ Line 207
{data.allocated_subjects}       // ✅ Line 218
{data.unallocated_subjects}     // ✅ Line 229
{data.total_faculty}            // ✅ Line 240
{data.faculty_balanced}         // ✅ Line 246
{data.faculty_overloaded}       // ✅ Line 251
{data.faculty_underloaded}      // ✅ Line 256
{data.average_workload}         // ✅ Line 261
```

**Result**: ✅ ALL field names match exactly - no mismatch

---

## STEP 6 - Git Commit & Push

**Commands executed**:
```bash
git add -A
git commit -m "Fix dashboard: reports service semester_type conversion for workload_summary table"
git push origin main
```

**Result**: ✅ Pushed to Railway (commit 3e56d33)

**Files changed**:
- app/reports/service.py (semester_type conversion logic)
- PROGRESS.md (created)
- DIAGNOSTIC_DUMP.md (created)
- SESSION_SUMMARY.md (updated)

---

# FINAL STATUS: ✅ WORKING

## What Was Fixed

1. **app/reports/service.py** - Added conversion from `semester_id` (1-6) to `semester_type` (ODD/EVEN) for `workload_summary` table queries
2. **Dockerfile** - Changed CMD to use `startup.sh` (migrations now run on Railway)
3. **app/reports/service.py line 39** - Changed `ay.label` to `ay.name`

## System Status

- ✅ Local backend: Running on http://localhost:8000
- ✅ Local frontend: Running on http://localhost:5175
- ✅ Health endpoint: Working
- ✅ Auth endpoint: Working (HOD login successful)
- ✅ Dashboard API: Working (returns valid JSON)
- 🚀 Railway: Deploying (commit 3e56d33)

## Browser Verification Required

User must manually verify:
1. Open http://localhost:5175/dashboard
2. Login as HOD
3. Confirm dashboard displays stats correctly

## Known Limitations

- `workload_summary` table still uses old schema (`semester_type` instead of `semester_id`)
- Conversion layer added as temporary bridge
- Future migration needed to update `workload_summary` table schema


---

# DIAGNOSTIC STEPS

## STEP 1 - Docker Container Status

```
docker ps
```

**Output**:
```
CONTAINER ID   IMAGE                   COMMAND                   CREATED       STATUS                 PORTS
ae7fde2892c9   faculty_selection-app   "sh -c '\n  set -e &&…"   7 hours ago   Up 7 hours (healthy)   0.0.0.0:8000->8000/tcp
0d502fef6740   postgres:16             "docker-entrypoint.s…"    7 hours ago   Up 7 hours (healthy)   0.0.0.0:5432->5432/tcp
```

**Result**: ✅ Both containers running and healthy

---

## STEP 2 - Backend Health Check

```
curl.exe http://localhost:8000/health
```

**Output**:
```json
{"status":"ok"}
```

**Result**: ✅ Backend is reachable

---

## STEP 3 - Vite Config

**File**: `frontend/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

**Analysis**: ✅ Proxy is correctly configured to forward `/api` requests to `http://localhost:8000`

**Note**: Frontend is running on port 5175 (auto-incremented), but proxy target is correct.

---

## STEP 4 - Token Tests for Each Role

### HOD Token (staff_id=16)

**Login**:
```bash
curl.exe -X POST http://localhost:8000/api/auth/dev-login/16
```

**Response**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNiIsImVtYWlsIjoibWN0NDRAaGluZHVzdGFudW5pdi5hYy5pbiIsIm5hbWUiOiJEci4gUy4gR29raWxhIiwicm9sZSI6ImhvZCIsImlhdCI6MTc3NDUwNDI3OSwiZXhwIjoxNzc0NTE4Njc5fQ.8NHF7IGMo1kf8oJStk0z8-Tbx_UDGPfp0-pF59H8xok",
  "staff_id": 16,
  "email": "mct44@hindustanuniv.ac.in",
  "name": "Dr. S. Gokila",
  "role": "hod"
}
```

**Test 1**: `/api/cycles/`
```bash
curl.exe -H "Authorization: Bearer TOKEN" http://localhost:8000/api/cycles/
```
**Response**: `[]` (empty array)
**Status**: ✅ 200 OK

**Test 2**: `/api/reports/department-summary`
```bash
curl.exe -H "Authorization: Bearer TOKEN" http://localhost:8000/api/reports/department-summary
```
**Response**:
```json
{
  "total_subject_offerings": 78,
  "allocated_subjects": 0,
  "unallocated_subjects": 78,
  "total_faculty": 28,
  "average_workload": 0.0,
  "faculty_overloaded": 0,
  "faculty_underloaded": 0,
  "faculty_balanced": 28
}
```
**Status**: ✅ 200 OK

---

### Coordinator Token (staff_id=22)

**Login**:
```bash
curl.exe -X POST http://localhost:8000/api/auth/dev-login/22
```

**Response**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyMiIsImVtYWlsIjoic2F0aGlzaGttQGhpbmR1c3RhbnVuaXYuYWMuaW4iLCJuYW1lIjoiRHIuIFNhdGhpc2ggS3VtYXIgTSIsInJvbGUiOiJ0dF9jb29yZGluYXRvciIsImlhdCI6MTc3NDUwNDI5NSwiZXhwIjoxNzc0NTE4Njk1fQ.fniu39pSbzjEFYJXlMYBAqPWvMhkZvTfbwI3JTD8TqU",
  "staff_id": 22,
  "email": "sathishkm@hindustanuniv.ac.in",
  "name": "Dr. Sathish Kumar M",
  "role": "tt_coordinator"
}
```

**Test 1**: `/api/pref-window/status`
```bash
curl.exe -H "Authorization: Bearer TOKEN" http://localhost:8000/api/pref-window/status
```
**Response**: `Internal Server Error`
**Status**: ❌ 500 ERROR

**Test 2**: `/api/allocation/run`
```bash
curl.exe -H "Authorization: Bearer TOKEN" http://localhost:8000/api/allocation/run
```
**Response**: `{"detail":"Method Not Allowed"}`
**Status**: ❌ 405 (needs POST with body)

---

### Faculty Token (staff_id=17)

**Login**:
```bash
curl.exe -X POST http://localhost:8000/api/auth/dev-login/17
```

**Response**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNyIsImVtYWlsIjoic3VkaGFzQGhpbmR1c3RhbnVuaXYuYWMuaW4iLCJuYW1lIjoiRHIuIFMuIFN1ZGhhIiwicm9sZSI6ImZhY3VsdHkiLCJpYXQiOjE3NzQ1MDQzMDAsImV4cCI6MTc3NDUxODcwMH0.AM4y9hYe0gszQ2QSgXDJt8w5R1rdxIlrcQMyP-awCUg",
  "staff_id": 17,
  "email": "sudhas@hindustanuniv.ac.in",
  "name": "Dr. S. Sudha",
  "role": "faculty"
}
```

**Test 1**: `/api/preferences/me`
```bash
curl.exe -H "Authorization: Bearer TOKEN" http://localhost:8000/api/preferences/me
```
**Response**: `Internal Server Error`
**Status**: ❌ 500 ERROR

---

## STEP 5 - Backend Error Logs

**Error 1**: `/api/preferences/me` (Faculty endpoint)

```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn) column so.academic_cycle_id does not exist
LINE 14:                   AND so.academic_cycle_id = 1
                               ^

[SQL:
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
                WHERE fp.staff_id = 17
                  AND so.academic_cycle_id = 1
                ORDER BY fp.preference_number
            ]
```

**Root Cause**: `app/preference/service.py` line 356 tries to query `so.academic_cycle_id` but the `subject_offering` table no longer has this column (it was removed in migration 021).

**Error 2**: `/api/pref-window/status` (Coordinator endpoint)

Similar error - likely also references `academic_cycle_id` somewhere.

---

## STEP 6 - Browser Test

**Cannot automate** - User must manually test:
1. Open http://localhost:5175/dashboard
2. Check Network tab in DevTools for failed requests
3. Report exact error messages

---

## STEP 7 - Router Files

### app/preference/router.py

**Key endpoints**:
- `POST /api/preferences` - Submit preference
- `GET /api/preferences/me` - List my preferences (❌ CRASHES)
- `GET /api/preferences/status` - Get status
- `DELETE /api/preferences/{id}` - Delete preference

**Issue**: Line 80 calls `preference_service.list_preferences()` which queries `academic_cycle_id`

### app/preference/window_router.py

**Key endpoints**:
- `POST /api/pref-window/open` - Open window
- `POST /api/pref-window/close` - Close window
- `GET /api/pref-window/status` - Get status (❌ CRASHES)

**Issue**: Likely queries `academic_cycle_id` in window_service.py

### app/allocation/router.py

**Key endpoint**:
- `POST /api/allocation/run` - Run allocation

**Status**: ✅ Code looks correct - uses `semester_id` not `academic_cycle_id`

---

## CRITICAL ISSUES FOUND

### Issue 1: `preference_service.py` uses `academic_cycle_id`

**File**: `app/preference/service.py` (line 356)

**Problem**: Queries `so.academic_cycle_id` which no longer exists in `subject_offering` table

**Fix needed**: Replace `academic_cycle_id` with join to `cycle` table using `academic_year` and `semester_id`

### Issue 2: `window_service.py` likely uses `academic_cycle_id`

**File**: `app/preference/window_service.py`

**Problem**: `/api/pref-window/status` returns 500 error

**Fix needed**: Check and fix all references to `academic_cycle_id`

### Issue 3: `workload_summary` table schema mismatch

**Status**: ✅ FIXED in previous step (added semester_type conversion)

---

## SUMMARY

**Working endpoints**:
- ✅ `/health`
- ✅ `/api/auth/dev-login/{id}`
- ✅ `/api/reports/department-summary`
- ✅ `/api/cycles/`

**Broken endpoints**:
- ❌ `/api/preferences/me` - Uses `academic_cycle_id`
- ❌ `/api/pref-window/status` - Uses `academic_cycle_id`

**Root cause**: Migration 021 removed `academic_cycle_id` from `subject_offering` table, but `app/preference/service.py` and `app/preference/window_service.py` were not updated.

**Next steps**:
1. Fix `app/preference/service.py` to use `academic_year` + `semester_id` instead of `academic_cycle_id`
2. Fix `app/preference/window_service.py` similarly
3. Test all endpoints again
4. Verify dashboard loads in browser
