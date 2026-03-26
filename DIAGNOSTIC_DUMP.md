# Complete Diagnostic Dump - Dashboard 500 Error

## CRITICAL BUG FOUND

**Location:** `app/reports/service.py` line 39
**Error:** `column ay.label does not exist`
**Fix Required:** Change `ay.label` to `ay.name`

```python
# BEFORE (line 39):
SELECT ay.label, c.semester_id

# AFTER:
SELECT ay.name, c.semester_id
```

The `academic_year` table has a `name` column, not a `label` column.

---

## Dashboard API Calls

The dashboard makes these API calls on load:

1. **GET `/api/reports/department-summary`** - Returns aggregate stats (FAILS with 500)
2. **GET `/api/auth/me`** - Returns current user info (WORKS)
3. **GET `/api/reports/faculty-workload`** - Returns workload data (LIKELY FAILS - same bug)

---

## Error Stack Trace

```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn) column ay.label does not exist
LINE 2:             SELECT ay.label, c.semester_id
                           ^

[SQL:
            SELECT ay.label, c.semester_id
            FROM cycle c
            JOIN academic_year ay ON ay.id = c.academic_year_id
            WHERE c.status = 'OPEN'
            LIMIT 1
        ]
```

**Function:** `_resolve_active_cycle()` in `app/reports/service.py`
**Called by:**
- `get_faculty_workload()` (line 62)
- `get_subject_summary()` (line 132)
- `get_department_summary()` (line 176)
- `generate_excel_report()` (line 255)
- `generate_pdf_report()` (line 430)

---

## 1. Frontend Dashboard Page

**File:** `frontend/src/pages/DashboardPage.tsx`

**API Calls Made:**
```typescript
// Line 42-47: Load department summary
getDepartmentSummary()
    .then((r) => setData(r.data))
    .catch((err: any) => {
        const detail = err.response?.data?.detail || 'Failed to load dashboard data';
        setError(detail);
    })

// Line 52-60: Load user's assigned subjects
Promise.all([
    getCurrentUser(),      // GET /api/auth/me
    getFacultyWorkload(),  // GET /api/reports/faculty-workload
])
```

**Expected Response from `/api/reports/department-summary`:**
```typescript
interface DeptSummary {
    total_subject_offerings: number;
    allocated_subjects: number;
    unallocated_subjects: number;
    total_faculty: number;
    average_workload: number;
    faculty_overloaded: number;
    faculty_underloaded: number;
    faculty_balanced: number;
}
```

---

## 2. Frontend API Client

**File:** `frontend/src/api/client.ts`

**Base URL:** `/api` (proxied to `http://localhost:8000` by Vite)

**Relevant Functions:**
```typescript
export const getDepartmentSummary = () => api.get('/reports/department-summary');
export const getFacultyWorkload = () => api.get('/reports/faculty-workload');
export const getCurrentUser = () => api.get('/auth/me');
```

**Auth:** JWT Bearer token from localStorage (`jwt_token`)

---

## 3. App Directory Structure

```
app/
├── admin/
│   ├── cycle_router.py
│   ├── cycle_service_new.py
│   ├── router.py
│   ├── service.py
│   ├── staff_router.py
│   └── staff_service.py
├── allocation/
│   ├── router.py
│   ├── schemas.py
│   └── service.py
├── auth/
│   ├── dependencies.py
│   ├── google_oauth.py
│   ├── jwt_utils.py
│   ├── router.py
│   ├── schemas.py
│   └── session_manager.py
├── coordinator/
│   ├── router.py
│   ├── semester_state_router.py
│   ├── semester_state_service.py
│   ├── window_router.py
│   └── window_transactions.py
├── core/
│   ├── config.py
│   ├── correlation_middleware.py
│   └── logging_config.py
├── db/
│   ├── pool.py
│   └── session.py
├── health/
│   └── router.py
├── preference/
│   ├── router.py
│   ├── service.py
│   ├── window_router.py
│   └── window_service.py
├── reports/
│   ├── cycle_guard.py
│   ├── master_workload_excel.py
│   ├── pdf_generator.py
│   ├── router.py          ← Defines /api/reports/* endpoints
│   ├── service.py          ← BUG IS HERE (line 39)
│   ├── schemas.py
│   └── snapshot_service.py
├── selection/
│   ├── router.py
│   └── transactions.py
├── utils/
│   ├── error_mapper.py
│   └── rate_limiter.py
├── main.py                 ← App entry point
└── startup_check.py
```

---

## 4. Main.py - Included Routers

**File:** `app/main.py`

**All Routers:**
```python
app.include_router(health_router.router)           # /health
app.include_router(auth_router.router)             # /api/auth/*
app.include_router(selection_router.router)        # /api/selection/*
app.include_router(coordinator_router.router)      # /api/coordinator/*
app.include_router(window_router.router, prefix="/api")  # /api/window/*
app.include_router(semester_state_router.router)   # /api/semester-state/*
app.include_router(preference_router.router)       # /api/preferences/*
app.include_router(pref_window_router.router)      # /api/pref-window/*
app.include_router(allocation_router.router)       # /api/allocation/*
app.include_router(admin_router.router)            # /api/admin/*
app.include_router(cycle_router.router)            # /api/cycles/*
app.include_router(staff_router.router)            # /api/admin/staff/*
app.include_router(reports_router.router)          # /api/reports/*  ← DASHBOARD USES THIS
```

**CORS Origins:**
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

---

## 5. Backend Route Handlers

### A. `/api/reports/department-summary` (FAILS)

**File:** `app/reports/router.py` lines 64-69

```python
@router.get("/department-summary", response_model=DepartmentSummaryResponse)
async def department_summary(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Aggregate department workload statistics."""
    data = report_service.get_department_summary()
    return DepartmentSummaryResponse(**data)
```

**Calls:** `report_service.get_department_summary()` in `app/reports/service.py`

**Bug Location:** `app/reports/service.py` line 176 calls `_resolve_active_cycle()` which has the bug on line 39.

### B. `/api/auth/me` (WORKS)

**File:** `app/auth/router.py` lines 217-222

```python
@router.get("/me", response_model=StaffInfoResponse)
async def get_current_user_info(user: UserInfo = Depends(get_current_user)):
    """Get current user info. Role always fresh from DB."""
    return StaffInfoResponse(
        staff_id=user.staff_id,
        email=user.email,
        name=user.name,
        role=user.role,
    )
```

**Returns:**
```json
{
  "staff_id": 16,
  "email": "mct44@hindustanuniv.ac.in",
  "name": "Dr. S. Gokila",
  "role": "hod"
}
```

### C. `/api/reports/faculty-workload` (LIKELY FAILS)

**File:** `app/reports/router.py` lines 44-52

```python
@router.get("/faculty-workload", response_model=FacultyWorkloadResponse)
async def faculty_workload(
    staff_id: int = Depends(get_current_staff_id),
):
    """Per-faculty workload report with assigned subject details."""
    data = report_service.get_faculty_workload()
    for rec in data["records"]:
        rec["subjects_assigned"] = [SubjectAssignment(**s) for s in rec["subjects_assigned"]]
    data["records"] = [FacultyWorkloadRecord(**r) for r in data["records"]]
    return FacultyWorkloadResponse(**data)
```

**Calls:** `report_service.get_faculty_workload()` which also calls `_resolve_active_cycle()` on line 62.

---

## 6. API Test Results

### Dev Login (WORKS)
```bash
POST http://localhost:8000/api/auth/dev-login/16
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "staff_id": 16,
  "email": "mct44@hindustanuniv.ac.in",
  "name": "Dr. S. Gokila",
  "role": "hod"
}
```

### Department Summary (FAILS - 500)
```bash
GET http://localhost:8000/api/reports/department-summary
Authorization: Bearer <token>
```

**Response:** 500 Internal Server Error

**Error:** `column ay.label does not exist`

---

## 7. Browser Console Error

**Expected Error in Browser:**
```
GET http://localhost:5173/api/reports/department-summary 500 (Internal Server Error)

Failed to load dashboard data
```

**Network Tab:**
- Request URL: `http://localhost:5173/api/reports/department-summary`
- Request Method: GET
- Status Code: 500 Internal Server Error
- Response: `{"detail":"Internal Server Error"}`

---

## 8. No Dashboard-Specific Router

There is NO `dashboard_router.py` or `dashboard_service.py`. The dashboard uses the general `/api/reports/*` endpoints.

---

## 9. Docker Status

**Status:** ✅ Running and healthy

```
NAME                    STATUS
faculty_selection_app   Up 32 minutes (healthy)
faculty_selection_db    Up 33 minutes (healthy)
```

**Recent Error in Logs:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn) column ay.label does not exist
LINE 2:             SELECT ay.label, c.semester_id
                           ^
```

**Source:** `app/reports/service.py` line 39 in `_resolve_active_cycle()`

---

## 10. Dockerfile and startup.sh

### Dockerfile CMD (Line 57)
```dockerfile
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
```

**Issue:** Bypasses `startup.sh` - migrations not running on Railway!

**Should be:**
```dockerfile
CMD ["sh", "startup.sh"]
```

### startup.sh Last Line (Line 45)
```bash
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Correct:** Uses `$PORT` without fallback ✅

---

## THE FIX

**File:** `app/reports/service.py`
**Line:** 39
**Change:** `ay.label` → `ay.name`

```python
# BEFORE:
row = session.execute(
    text("""
        SELECT ay.label, c.semester_id
        FROM cycle c
        JOIN academic_year ay ON ay.id = c.academic_year_id
        WHERE c.status = 'OPEN'
        LIMIT 1
    """)
).fetchone()

# AFTER:
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

---

## Additional Issues Found

1. **Dockerfile CMD bypasses startup.sh** - Railway migrations not running
2. **Migration 020 role** - Already fixed to use `'tt_coordinator'` ✅
3. **CORS** - Already fixed to allow ports 5173-5176 ✅

---

## Next Steps

1. Fix `ay.label` → `ay.name` in `app/reports/service.py` line 39
2. Fix Dockerfile CMD to use `startup.sh`
3. Restart local docker: `docker-compose down -v && docker-compose up -d`
4. Test dashboard: `http://localhost:5173/dashboard`
5. Push to Railway
