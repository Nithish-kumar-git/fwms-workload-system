# TECHNICAL SNAPSHOT: Faculty Subject Selection System

**Generated**: 2026-03-28  
**Purpose**: Complete system documentation for external AI analysis  
**Source**: Extracted from actual codebase, configs, and deployment files

---

## SECTION 1: BACKEND ARCHITECTURE

### 1.1 FastAPI Entry Point

**File**: `app/main.py`

**Application Structure**:
```python
def create_app() -> FastAPI:
    app = FastAPI(
        title="Faculty Subject Selection System",
        description="Production-critical FCFS-based subject allocation system",
        version="1.0.0"
    )
```

**Middleware Stack** (order: last added = first executed):
1. `CorrelationIDMiddleware` - Request tracking
2. `CORSMiddleware` - Frontend access control

**CORS Configuration**:
```python
frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
allow_origins=[
    'http://localhost:5173',
    'http://localhost:5174',
    'http://localhost:5175',
    'http://localhost:5176',
    'http://localhost:3000',
    frontend_url
]
allow_credentials=True
allow_methods=['*']
allow_headers=['*']
```

### 1.2 Registered Routers

**Order of registration** (from `app/main.py` lines 65-78):

1. `health_router` - Health checks
2. `auth_router` - Authentication (`/api/auth/*`)
3. `selection_router` - Subject selection
4. `coordinator_router` - Coordinator operations
5. `window_router` - Window management (`/api/*`)
6. `semester_state_router` - Semester state
7. `preference_router` - Preferences (`/api/preferences/*`)
8. `pref_window_router` - Preference window
9. `allocation_router` - Allocation (`/api/allocation/*`)
10. `admin_router` - Admin operations (`/api/admin/*`)
11. `cycle_router` - Cycle management (`/api/cycles/*`)
12. `staff_router` - Staff management (`/api/admin/staff/*`)
13. `reports_router` - Reports (`/api/reports/*`)
14. `debug_router` - Debug diagnostics (`/api/debug/*`)

### 1.3 Critical Endpoint: `/api/reports/subject-summary`

**File**: `app/reports/router.py` (lines 52-59)

```python
@router.get("/subject-summary", response_model=SubjectSummaryResponse)
async def subject_summary(
    staff_id: int = Depends(get_current_staff_id),
):
    """Subject-wise report showing assigned faculty per offering. Accessible by all authenticated users."""
    data = report_service.get_subject_summary()
    data["records"] = [SubjectSummaryRecord(**r) for r in data["records"]]
    return SubjectSummaryResponse(**data)
```

**Service Implementation**: `app/reports/service.py` (lines 126-165)

```python
def get_subject_summary(
    academic_year: Optional[str] = None, semester_id: Optional[int] = None
) -> dict:
    """Per-subject-offering report showing assigned faculty."""
    with get_transaction() as session:
        if academic_year is None or semester_id is None:
            academic_year, semester_id = _resolve_active_cycle(session)
        
        logger.info(f"[get_subject_summary] Using academic_year={academic_year}, semester_id={semester_id}")
        
        rows = session.execute(
            text("""
                SELECT so.id, sub.code, sub.name, p.name AS program,
                       sem.label AS semester, sec.label AS section,
                       s.name AS faculty_name, s.emp_code,
                       COALESCE(sub.tch, 0) AS tch,
                       CASE WHEN a.id IS NOT NULL THEN true ELSE false END AS allocated
                FROM subject_offering so
                JOIN subject sub ON sub.id = so.subject_id
                JOIN program p ON p.id = so.program_id
                JOIN semester sem ON sem.id = so.semester_id
                JOIN section sec ON sec.id = so.section_id
                LEFT JOIN allocation a ON a.subject_offering_id = so.id
                LEFT JOIN staff s ON s.id = a.staff_id
                WHERE so.academic_year = :year AND so.semester_id = :sem_id
                ORDER BY p.name, sem.label, sec.label, sub.code
            """),
            {"year": academic_year, "sem_id": semester_id}
        ).fetchall()

    logger.info(f"[get_subject_summary] Query returned {len(rows)} rows")

    records = [
        {
            "subject_offering_id": r[0],
            "course_code": r[1], "course_name": r[2], "program": r[3],
            "semester": r[4], "section": r[5],
            "faculty_name": r[6], "faculty_emp_code": r[7],
            "tch": r[8], "allocated": r[9],
        }
        for r in rows
    ]
    return {"total": len(records), "records": records}
```

**Key Query Filters**:
- `WHERE so.academic_year = :year` - Uses STRING academic_year column
- `AND so.semester_id = :sem_id` - Uses INTEGER semester_id column

### 1.4 Active Cycle Resolution

**File**: `app/reports/service.py` (lines 26-48)

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

**Returns**:
- `row[0]` = `ay.name` (STRING) - e.g., "2025-2026"
- `row[1]` = `c.semester_id` (INTEGER) - e.g., 2

---

## SECTION 2: DATABASE SCHEMA

### 2.1 Current Schema (Migration 021)

**NEW ARCHITECTURE** (from `migrations/021_semester_specific_cycles.sql`):

#### Table: `academic_year`
```sql
CREATE TABLE IF NOT EXISTS academic_year (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(20) NOT NULL UNIQUE,  -- e.g. "2025-2026"
    start_date      DATE,
    end_date        DATE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### Table: `cycle`
```sql
CREATE TABLE IF NOT EXISTS cycle (
    id                  SERIAL PRIMARY KEY,
    academic_year_id    INTEGER NOT NULL,
    semester_id         BIGINT NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'CLOSED',
    opened_at           TIMESTAMP,
    closed_at           TIMESTAMP,
    allocated_at        TIMESTAMP,
    frozen_at           TIMESTAMP,
    frozen_by_staff_id  BIGINT,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_cycle_academic_year FOREIGN KEY (academic_year_id) REFERENCES academic_year(id),
    CONSTRAINT fk_cycle_semester FOREIGN KEY (semester_id) REFERENCES semester(id),
    CONSTRAINT fk_cycle_frozen_by FOREIGN KEY (frozen_by_staff_id) REFERENCES staff(id),
    CONSTRAINT uq_cycle_year_semester UNIQUE (academic_year_id, semester_id),
    CONSTRAINT chk_cycle_status CHECK (status IN ('OPEN', 'CLOSED', 'ALLOCATED', 'FROZEN'))
);
```

**Status Values**:
- `OPEN` - Active cycle, preferences can be submitted
- `CLOSED` - Inactive cycle
- `ALLOCATED` - Allocation has been run
- `FROZEN` - HOD approved, immutable

#### Table: `subject_offering`

**CRITICAL**: This table has BOTH old and new columns:

```sql
-- From migration 021 (lines 151-168):
ALTER TABLE subject_offering
    ADD COLUMN IF NOT EXISTS academic_year_id INTEGER;

UPDATE subject_offering so
SET academic_year_id = ay.id
FROM academic_year ay
WHERE so.academic_year = ay.name;

ALTER TABLE subject_offering
    ALTER COLUMN academic_year_id SET NOT NULL;

ALTER TABLE subject_offering
    ADD CONSTRAINT fk_subject_offering_academic_year 
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(id);
```

**Columns**:
- `academic_year` (VARCHAR) - OLD, kept for backward compatibility
- `academic_year_id` (INTEGER FK) - NEW, references academic_year.id
- `semester_id` (BIGINT FK) - References semester.id
- `old_academic_cycle_id` (INTEGER) - Renamed from academic_cycle_id
- NO `cycle_id` column in subject_offering

#### Table: `faculty_preference`

**From migration 021** (lines 170-192):

```sql
ALTER TABLE faculty_preference
    ADD COLUMN IF NOT EXISTS new_cycle_id INTEGER;

UPDATE faculty_preference fp
SET new_cycle_id = c.id
FROM subject_offering so
JOIN semester s ON so.semester_id = s.id
JOIN academic_year ay ON so.academic_year = ay.name
JOIN cycle c ON c.academic_year_id = ay.id AND c.semester_id = s.id
WHERE fp.subject_offering_id = so.id;

-- Rename academic_cycle_id to old_academic_cycle_id
ALTER TABLE faculty_preference
    RENAME COLUMN academic_cycle_id TO old_academic_cycle_id;

-- Rename new_cycle_id to cycle_id
ALTER TABLE faculty_preference
    RENAME COLUMN new_cycle_id TO cycle_id;

ALTER TABLE faculty_preference
    ALTER COLUMN cycle_id SET NOT NULL;

ALTER TABLE faculty_preference
    ADD CONSTRAINT fk_faculty_preference_cycle 
    FOREIGN KEY (cycle_id) REFERENCES cycle(id);
```

**Columns**:
- `cycle_id` (INTEGER FK) - NEW, references cycle.id
- `old_academic_cycle_id` (INTEGER) - OLD, renamed from academic_cycle_id
- `subject_offering_id` (BIGINT FK) - References subject_offering.id
- `staff_id` (BIGINT FK) - References staff.id
- `preference_number` (INTEGER) - 1-5

#### Table: `allocation`

**Same migration pattern as faculty_preference**:
- `cycle_id` (INTEGER FK) - NEW, references cycle.id
- `old_academic_cycle_id` (INTEGER) - OLD
- `subject_offering_id` (BIGINT FK)
- `staff_id` (BIGINT FK)

### 2.2 OLD Schema (Migration 010 - DEPRECATED)

**File**: `migrations/010_academic_cycle_support.sql`

#### Table: `academic_cycle` (RENAMED TO `academic_cycle_old_backup`)

```sql
CREATE TABLE IF NOT EXISTS academic_cycle (
    id              SERIAL PRIMARY KEY,
    academic_year   VARCHAR(20) NOT NULL,       -- e.g. "2025-2026"
    semester_type   VARCHAR(10) NOT NULL,        -- ODD / EVEN
    start_date      DATE,
    end_date        DATE,
    is_active       BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_academic_cycle UNIQUE (academic_year, semester_type),
    CONSTRAINT chk_semester_type CHECK (semester_type IN ('ODD', 'EVEN'))
);
```

**Migration 021 renamed this table** (line 353):
```sql
ALTER TABLE academic_cycle RENAME TO academic_cycle_old_backup;
```

### 2.3 Schema Evolution Summary

**Migration 010 → Migration 021**:

| Aspect | OLD (Migration 010) | NEW (Migration 021) |
|--------|---------------------|---------------------|
| Cycle table | `academic_cycle` | `cycle` |
| Academic year storage | `academic_cycle.academic_year` (STRING) | `academic_year.name` (STRING) + `cycle.academic_year_id` (FK) |
| Semester model | `semester_type` (ODD/EVEN) | `semester_id` (1-6 for I-VI) |
| FK column in preferences | `academic_cycle_id` | `cycle_id` |
| FK column in allocations | `academic_cycle_id` | `cycle_id` |
| subject_offering linkage | `academic_cycle_id` FK | `academic_year` (STRING) + `semester_id` (INTEGER) |

**CRITICAL MISMATCH**:
- `subject_offering` table does NOT have `cycle_id` column
- `subject_offering` uses `academic_year` (STRING) + `semester_id` (INTEGER)
- `faculty_preference` and `allocation` use `cycle_id` (INTEGER FK)

---

## SECTION 3: MIGRATIONS

### 3.1 Migration Files (in order)


1. `schema.sql` - Base schema
2. `002_window_lifecycle.sql`
3. `003_seed_minimal.sql`
4. `004_seed_demo.sql`
5. `005_workload_schema.sql`
6. `006_academic_seed.sql`
7. `007_faculty_seed.sql`
8. `008_admin_override_schema.sql`
9. `009_window_audit_types.sql`
10. **`010_academic_cycle_support.sql`** - Introduced `academic_cycle` table (ODD/EVEN model)
11. `011_update_staff_emails.sql`
12. `011b_workload_snapshot.sql`
13. `012_fix_audit_constraint.sql`
14. `013_single_active_cycle.sql`
15. `014_fix_allocation_pipeline.sql`
16. `015_fix_preference_constraint.sql`
17. `016_semester_state_management.sql`
18. `017_add_role_column.sql`
19. `019_final_fixed.sql`
20. `019_real_subjects_final.sql`
21. `020_real_faculty.sql`
22. **`021_semester_specific_cycles.sql`** - Replaced `academic_cycle` with `cycle` (semester-specific model)

### 3.2 Migration 021 Key Changes

**File**: `migrations/021_semester_specific_cycles.sql`

**What it does**:
1. Creates `academic_year` table (time period only)
2. Creates `cycle` table (workflow controller per academic_year + semester)
3. Migrates data from `academic_cycle` (ODD/EVEN) to `cycle` (semester-specific)
4. Updates `subject_offering` to add `academic_year_id` FK
5. Updates `faculty_preference` to use `cycle_id` instead of `academic_cycle_id`
6. Updates `allocation` to use `cycle_id` instead of `academic_cycle_id`
7. Renames `academic_cycle` to `academic_cycle_old_backup`

**Column Renames**:
```sql
-- In faculty_preference, allocation, workload_summary:
ALTER TABLE faculty_preference
    RENAME COLUMN academic_cycle_id TO old_academic_cycle_id;

ALTER TABLE faculty_preference
    RENAME COLUMN new_cycle_id TO cycle_id;
```

**IMPORTANT**: `subject_offering` does NOT get a `cycle_id` column. It keeps:
- `academic_year` (STRING) - for backward compatibility
- `academic_year_id` (INTEGER FK) - new foreign key
- `semester_id` (BIGINT FK) - existing column

### 3.3 Code References to OLD Schema

**Files still referencing `old_academic_cycle_id`**:
1. `app/preference/service.py` line 269 - INSERT statement
2. `app/allocation/service.py` line 670 - INSERT statement
3. `app/allocation/service.py` line 737 - INSERT statement
4. `app/admin/service.py` line 687 - INSERT statement

**Pattern**: All INSERT statements populate BOTH `cycle_id` and `old_academic_cycle_id` with the same value for backward compatibility.

---

## SECTION 4: FRONTEND FLOW

### 4.1 Preferences Page

**File**: `frontend/src/pages/PreferencesPage.tsx`

**API Call** (lines 98-107):
```typescript
const loadOfferings = async () => {
    setOfferingsLoading(true);
    try {
        const res = await getSubjectSummary();
        console.log('Subject Summary API Response:', res.data);
        console.log('Records count:', res.data.records?.length || 0);
        setOfferings(res.data.records || []);
    } catch (err) {
        console.error('Failed to load subject offerings:', err);
        // Offerings are supplementary
    } finally {
        setOfferingsLoading(false);
    }
};
```

**State Management**:
- `offerings` state stores `res.data.records` array
- `filteredOfferings` computed from `offerings` with filters applied
- `grouped` computed from `filteredOfferings` for rendering

**Rendering Logic** (lines 234-237):
```typescript
{offeringsLoading ? (
    <p>Loading subject catalog...</p>
) : filteredOfferings.length === 0 ? (
    <p>No subjects match the current filters.</p>
```

**Interface**:
```typescript
interface SubjectOffering {
    subject_offering_id: number;
    course_code: string;
    course_name: string;
    program: string;
    semester: string;
    section: string;
    tch: number;
    allocated: boolean;
    faculty_name: string | null;
}
```

### 4.2 API Client

**File**: `frontend/src/api/client.ts`

**Base URL Construction** (lines 3-5):
```typescript
const baseURL = import.meta.env.VITE_API_URL 
    ? `${import.meta.env.VITE_API_URL}/api`
    : '/api';
```

**API Function** (line 95):
```typescript
export const getSubjectSummary = () => api.get('/reports/subject-summary');
```

**Full URL**: `${baseURL}/reports/subject-summary`

**Authentication** (lines 15-21):
```typescript
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('jwt_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});
```

**Token Capture from OAuth** (lines 24-34):
```typescript
if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (token) {
        localStorage.setItem('jwt_token', token);
        params.delete('token');
        const clean = params.toString();
        const newUrl = window.location.pathname + (clean ? `?${clean}` : '');
        window.history.replaceState({}, '', newUrl);
    }
}
```

---

## SECTION 5: DEPLOYMENT CONFIGURATION

### 5.1 Backend (Railway)

**Dockerfile**:

**Build Stage**:
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc postgresql-client libpq-dev
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
```

**Runtime Stage**:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y postgresql-client libpq5
COPY --from=builder /root/.local /root/.local
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY startup.sh ./startup.sh
RUN chmod +x startup.sh

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["sh", "startup.sh"]
```

**startup.sh** (lines 46-49):
```bash
echo "All migrations done. Starting server..."
# Use PORT from environment, default to 8000 if not set
PORT=${PORT:-8000}
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Migration Execution** (from `startup.sh` lines 11-45):
```bash
run_migration schema.sql
run_migration 002_window_lifecycle.sql
run_migration 003_seed_minimal.sql
run_migration 004_seed_demo.sql
run_migration 005_workload_schema.sql
run_migration 006_academic_seed.sql
run_migration 007_faculty_seed.sql
run_migration 008_admin_override_schema.sql
run_migration 009_window_audit_types.sql
run_migration 010_academic_cycle_support.sql
run_migration 011_update_staff_emails.sql
run_migration 011b_workload_snapshot.sql
run_migration 012_fix_audit_constraint.sql
run_migration 013_single_active_cycle.sql
run_migration 014_fix_allocation_pipeline.sql
run_migration 015_fix_preference_constraint.sql
run_migration 016_semester_state_management.sql
run_migration 017_add_role_column.sql
run_migration 019_final_fixed.sql
run_migration 019_real_subjects_final.sql
run_migration 020_real_faculty.sql
run_migration 021_semester_specific_cycles.sql
```

### 5.2 Frontend (Vercel)

**File**: `vercel.json`

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "installCommand": "echo skip",
  "framework": null,
  "routes": [
    {
      "src": "^/(assets/.*|.*\\.(js|css|png|jpg|jpeg|svg|ico|json))$",
      "dest": "/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

**Routing Strategy**:
1. Static assets (JS, CSS, images) → serve directly
2. All other routes → `index.html` (React Router SPA)

---

## SECTION 6: ENVIRONMENT VARIABLES

### 6.1 Backend Environment Variables

**File**: `app/core/config.py`

**Required Variables** (checked in `_check_required_env_vars()`):


| Variable | Type | Default | Required | Usage |
|----------|------|---------|----------|-------|
| `DATABASE_URL` | str | - | YES | PostgreSQL connection string |
| `SECRET_KEY` | str | - | YES | JWT signing (min 32 chars) |
| `GOOGLE_CLIENT_ID` | str | - | YES | OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | str | - | YES | OAuth client secret |
| `GOOGLE_REDIRECT_URI` | str | - | YES | OAuth callback URL |
| `FRONTEND_URL` | str | `http://localhost:5173` | NO | OAuth redirect target |
| `ENV` | str | `development` | NO | Environment mode |
| `DEV_AUTH_BYPASS` | bool | `false` | NO | Dev-only auth bypass |
| `SESSION_BACKEND` | str | `memory` | NO | Session storage (redis/memory) |
| `REDIS_URL` | str | None | NO | Redis connection string |
| `SESSION_EXPIRATION_HOURS` | int | 4 | NO | Session TTL |
| `LOG_LEVEL` | str | `INFO` | NO | Logging level |
| `ALLOWED_EMAIL_DOMAIN` | str | `hindustanuniv.ac.in` | NO | Email domain restriction |

**Production Validation** (from `config.py` lines 145-172):
- `ENV=production` enforces:
  - `SESSION_COOKIE_SECURE=true`
  - Valid `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
  - `DEV_AUTH_BYPASS=false` (FATAL if true)

### 6.2 Frontend Environment Variables

**File**: `frontend/src/api/client.ts` (lines 3-5)

| Variable | Usage | Default |
|----------|-------|---------|
| `VITE_API_URL` | Backend API base URL | `/api` (relative) |

**Construction**:
```typescript
const baseURL = import.meta.env.VITE_API_URL 
    ? `${import.meta.env.VITE_API_URL}/api`
    : '/api';
```

**Examples**:
- Local: `VITE_API_URL=http://localhost:8000` → `http://localhost:8000/api`
- Production: `VITE_API_URL=https://backend.railway.app` → `https://backend.railway.app/api`
- Not set: Uses relative `/api` (same domain)

---

## SECTION 7: AUTH FLOW

### 7.1 Google OAuth Flow

**File**: `app/auth/router.py`

**Step 1: Login** (`GET /api/auth/login`):
```python
@router.get("/login", response_model=LoginResponse)
async def login():
    """Return Google OAuth authorization URL."""
    url = oauth_client.get_authorization_url()
    return LoginResponse(authorization_url=url)
```

**Step 2: Callback** (`GET /api/auth/callback`):
```python
@router.get("/callback")
async def oauth_callback(code: str = Query(...), state: str = Query(None)):
    # Exchange code for token
    user_info = oauth_client.exchange_code_for_token(code)
    email = user_info["email"]
    
    # Lookup staff by email
    result = db_session.execute(
        text("SELECT id, email, name, role FROM staff WHERE email = :email AND is_active = true"),
        {"email": email}
    ).fetchone()
    
    # DEV bypass: map unknown email to first coordinator
    if result is None and settings.DEV_AUTH_BYPASS:
        result = _lookup_first_coordinator(db_session)
    
    if result is None:
        raise HTTPException(status_code=403, detail="Unauthorized faculty. Email not registered.")
    
    staff_id, staff_email, staff_name, role = result
    
    # Create session + JWT
    auth = _create_auth_tokens(staff_id, staff_email, staff_name, role)
    
    # Redirect to frontend with token
    frontend_url = settings.FRONTEND_URL
    resp = RedirectResponse(url=f"{frontend_url}/dashboard?token={auth['token']}", status_code=302)
    resp.set_cookie(key=settings.SESSION_COOKIE_NAME, value=auth["session_id"], ...)
    return resp
```

**Step 3: Token Creation** (lines 60-64):
```python
def _create_auth_tokens(staff_id: int, email: str, name: str, role: str) -> dict:
    """Create session + JWT. Returns {session_id, token}."""
    session_id = session_manager.create_session(staff_id)
    token = create_jwt(staff_id=staff_id, email=email, name=name, role=role)
    return {"session_id": session_id, "token": token}
```

### 7.2 Frontend Token Handling

**File**: `frontend/src/api/client.ts` (lines 24-34)

**Token Capture from URL**:
```typescript
if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (token) {
        localStorage.setItem('jwt_token', token);
        params.delete('token');
        const clean = params.toString();
        const newUrl = window.location.pathname + (clean ? `?${clean}` : '');
        window.history.replaceState({}, '', newUrl);
    }
}
```

**Token Usage** (lines 15-21):
```typescript
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('jwt_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});
```

---

## SECTION 8: CURRENT KNOWN ISSUES (FROM CODE)

### 8.1 Migration 021 Transaction Errors

**Evidence**: Docker logs show:
```
psql:migrations/021_semester_specific_cycles.sql:151: ERROR: current transaction is aborted, commands ignored until end of transaction block
```

**Location**: Multiple lines in migration 021 after an initial error
**Impact**: Migration may have partially applied, leaving inconsistent schema

### 8.2 Legacy Column References

**Files with `old_academic_cycle_id` INSERT statements**:
1. `app/preference/service.py:269`
2. `app/allocation/service.py:670`
3. `app/allocation/service.py:737`
4. `app/admin/service.py:687`

**Pattern**: Code populates both `cycle_id` (NEW) and `old_academic_cycle_id` (OLD) for compatibility

### 8.3 subject_offering Linkage Mismatch

**Problem**:
- `subject_offering` table uses: `academic_year` (STRING) + `semester_id` (INTEGER)
- `faculty_preference` table uses: `cycle_id` (INTEGER FK to cycle table)
- `allocation` table uses: `cycle_id` (INTEGER FK to cycle table)

**JOIN Complexity**:
To join `faculty_preference` with `subject_offering`, must go through:
```sql
FROM faculty_preference fp
JOIN subject_offering so ON fp.subject_offering_id = so.id
JOIN cycle c ON c.academic_year_id = (SELECT id FROM academic_year WHERE name = so.academic_year)
              AND c.semester_id = so.semester_id
WHERE fp.cycle_id = c.id
```

**Current Code** (`app/preference/service.py` lines 310-324):
```python
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
        JOIN cycle c ON c.academic_year_id = so.academic_year_id 
                    AND c.semester_id = so.semester_id
        WHERE fp.staff_id = :staff_id
          AND c.id = :cid
        ORDER BY fp.preference_number
    """),
    {"staff_id": staff_id, "cid": active_cycle["id"]}
).fetchall()
```

**Note**: Uses `c.academic_year_id = so.academic_year_id` but `subject_offering` has BOTH:
- `academic_year` (STRING)
- `academic_year_id` (INTEGER FK)

---

## SECTION 9: DATA FLOW TRACE

### 9.1 Subject Summary Flow

**Frontend → Backend → Database**:

1. **Frontend initiates** (`PreferencesPage.tsx:98`):
   ```typescript
   const res = await getSubjectSummary();
   ```

2. **API client calls** (`client.ts:95`):
   ```typescript
   api.get('/reports/subject-summary')
   ```
   - Full URL: `${VITE_API_URL}/api/reports/subject-summary`
   - Headers: `Authorization: Bearer ${jwt_token}`

3. **Backend router** (`app/reports/router.py:52`):
   ```python
   @router.get("/subject-summary", response_model=SubjectSummaryResponse)
   async def subject_summary(staff_id: int = Depends(get_current_staff_id)):
       data = report_service.get_subject_summary()
       return SubjectSummaryResponse(**data)
   ```

4. **Service layer** (`app/reports/service.py:126`):
   ```python
   def get_subject_summary(academic_year=None, semester_id=None):
       if academic_year is None or semester_id is None:
           academic_year, semester_id = _resolve_active_cycle(session)
       
       # Query subject_offering with filters
       WHERE so.academic_year = :year AND so.semester_id = :sem_id
   ```

5. **Active cycle resolution** (`app/reports/service.py:26`):
   ```python
   def _resolve_active_cycle(session):
       row = session.execute(text("""
           SELECT ay.name, c.semester_id
           FROM cycle c
           JOIN academic_year ay ON ay.id = c.academic_year_id
           WHERE c.status = 'OPEN'
           LIMIT 1
       """)).fetchone()
       return row[0], row[1]  # (academic_year STRING, semester_id INT)
   ```

6. **Database query**:
   ```sql
   SELECT so.id, sub.code, sub.name, p.name AS program, ...
   FROM subject_offering so
   JOIN subject sub ON sub.id = so.subject_id
   ...
   WHERE so.academic_year = '2025-2026' AND so.semester_id = 2
   ```

7. **Response structure**:
   ```json
   {
     "total": 78,
     "records": [
       {
         "subject_offering_id": 685,
         "course_code": "ACA31001",
         "course_name": "Digital Technological Solutions",
         "program": "BCA(Cyber+MM)",
         "semester": "II",
         "section": "C",
         "faculty_name": "Dr. Nathiya R",
         "faculty_emp_code": "MCT60",
         "tch": 4,
         "allocated": true
       },
       ...
     ]
   }
   ```

8. **Frontend stores** (`PreferencesPage.tsx:105`):
   ```typescript
   setOfferings(res.data.records || []);
   ```

### 9.2 Preference Submission Flow

**Frontend → Backend → Database**:

1. **Frontend submits** (`PreferencesPage.tsx:186`):
   ```typescript
   await submitPreference({
       subject_offering_id: parseInt(offeringId),
       preference_number: parseInt(prefNum),
   });
   ```

2. **API client** (`client.ts:59`):
   ```typescript
   export const submitPreference = (data: {
       subject_offering_id: number;
       preference_number: number;
   }) => api.post('/preferences', data);
   ```

3. **Backend router** (`app/preference/router.py:25`):
   ```python
   @router.post("", response_model=SubmitPreferenceResponse)
   async def submit_preference(
       request: SubmitPreferenceRequest,
       user: UserInfo = Depends(get_current_user),
   ):
       result = preference_service.submit_preference(
           staff_id=user.staff_id,
           subject_offering_id=request.subject_offering_id,
           preference_number=request.preference_number,
       )
   ```

4. **Service layer** (`app/preference/service.py:238`):
   ```python
   def submit_preference(staff_id, subject_offering_id, preference_number):
       # Get active cycle_id
       cycle_row = session.execute(
           text("SELECT id FROM cycle WHERE status = 'OPEN' LIMIT 1")
       ).fetchone()
       active_cycle_id = cycle_row[0]
       
       # Insert preference
       result = session.execute(
           text("""
               INSERT INTO faculty_preference 
                   (staff_id, subject_offering_id, preference_number, cycle_id, old_academic_cycle_id)
               VALUES (:staff_id, :offering_id, :pref_num, :cycle_id, :cycle_id)
               RETURNING id
           """),
           {"staff_id": staff_id, "offering_id": subject_offering_id, 
            "pref_num": preference_number, "cycle_id": active_cycle_id}
       )
   ```

**Database INSERT**:
- Populates `cycle_id` with active cycle ID
- Populates `old_academic_cycle_id` with same value (backward compatibility)

---

## SECTION 10: LOCAL VS PRODUCTION COMPARISON

### 10.1 Local Database State (VERIFIED)

**From debug endpoint** (`http://localhost:8000/api/debug/db-state`):

```json
{
  "subject_offering_total": 194,
  "subject_offering_grouped": [
    {"academic_year": "2025-2026", "semester_id": 2, "count": 78},
    {"academic_year": "2025-2026", "semester_id": 4, "count": 58},
    {"academic_year": "2025-2026", "semester_id": 6, "count": 58}
  ],
  "active_cycle": {
    "id": 1,
    "academic_year": "2025-2026",
    "semester_id": 2,
    "status": "OPEN"
  },
  "all_cycles": [
    {"id": 1, "academic_year": "2025-2026", "semester_id": 2, "status": "OPEN"},
    {"id": 2, "academic_year": "2025-2026", "semester_id": 4, "status": "CLOSED"},
    {"id": 3, "academic_year": "2025-2026", "semester_id": 6, "status": "CLOSED"}
  ],
  "academic_years": [
    {"id": 1, "name": "2025-2026"}
  ]
}
```

**API Response** (`GET /api/reports/subject-summary`):
```json
{
  "total": 78,
  "records": [...]  // 78 subject offerings
}
```

**Backend Logs**:
```
[get_subject_summary] Using academic_year=2025-2026, semester_id=2
[get_subject_summary] Query returned 78 rows
```

### 10.2 Production Database State (SUSPECTED)

**Hypothesis**: Railway database is missing one or more of:
1. `subject_offering` records
2. `academic_year` records
3. `cycle` records with status='OPEN'
4. Proper linkage between tables

**Evidence**:
- Production API returns: `{"total": 0, "records": []}`
- Local API returns: `{"total": 78, "records": [...]}`
- Same codebase, different database

**Verification Needed**:
- Query Railway database using debug endpoint: `https://fwms-workload-system-production.up.railway.app/api/debug/db-state`
- Compare counts and structure with local

---

## SECTION 11: CYCLE MANAGEMENT

### 11.1 Cycle Service

**File**: `app/admin/cycle_service_new.py`

**Get Active Cycle** (lines 165-203):
```python
def get_active_cycle() -> dict | None:
    """
    Get the currently active (OPEN) cycle.
    Joins with academic_year and semester tables.
    
    Returns:
        Cycle dictionary with id, academic_year, semester_id, semester_name, status, is_active
        or None if no active cycle
    """
    with get_transaction() as session:
        row = session.execute(
            text("""
                SELECT 
                    c.id,
                    ay.name as academic_year,
                    c.semester_id,
                    s.label as semester_name,
                    c.status,
                    c.opened_at,
                    c.closed_at,
                    c.allocated_at,
                    c.frozen_at,
                    c.created_at
                FROM cycle c
                JOIN academic_year ay ON c.academic_year_id = ay.id
                JOIN semester s ON c.semester_id = s.id
                WHERE c.status = 'OPEN'
                LIMIT 1
            """)
        ).fetchone()
        
        if not row:
            return None
        
        return {
            "id": row[0],
            "academic_year": row[1],
            "semester_id": row[2],
            "semester_name": row[3],
            "status": row[4],
            "is_active": True,
            ...
        }
```

**Activate Cycle** (lines 88-122):
```python
def activate_cycle(cycle_id: int) -> dict:
    """
    Activate a cycle (set status='OPEN').
    Only one cycle can be OPEN at a time.
    """
    with get_transaction() as session:
        # Check if cycle exists
        cycle = session.execute(
            text("SELECT id, status FROM cycle WHERE id = :id"),
            {"id": cycle_id}
        ).fetchone()
        
        if not cycle:
            return {"success": False, "message": "Cycle not found"}
        
        if cycle[1] == 'FROZEN':
            return {"success": False, "message": "Cannot activate a frozen cycle"}
        
        # Close all other OPEN cycles
        session.execute(
            text("UPDATE cycle SET status = 'CLOSED', closed_at = NOW() WHERE status = 'OPEN'")
        )
        
        # Open this cycle
        session.execute(
            text("UPDATE cycle SET status = 'OPEN', opened_at = NOW() WHERE id = :id"),
            {"id": cycle_id}
        )
        
        session.commit()
        
        return {"success": True, "message": "Cycle activated"}
```

**Safety**: Automatically closes all other OPEN cycles before opening the selected one.

---

## SECTION 12: DIAGNOSTIC ENDPOINT

### 12.1 Debug Router

**File**: `app/debug_router.py` (lines 1-79)

**Endpoint**: `GET /api/debug/db-state`

**Returns**:
```json
{
  "subject_offering_total": <count>,
  "subject_offering_grouped": [
    {"academic_year": "...", "semester_id": N, "count": N}
  ],
  "active_cycle": {
    "id": N,
    "academic_year": "...",
    "semester_id": N,
    "status": "OPEN"
  },
  "all_cycles": [...],
  "academic_years": [...]
}
```

**Queries Executed**:
1. `SELECT COUNT(*) FROM subject_offering`
2. `SELECT academic_year, semester_id, COUNT(*) FROM subject_offering GROUP BY academic_year, semester_id`
3. `SELECT c.id, ay.name, c.semester_id, c.status FROM cycle c JOIN academic_year ay ... WHERE c.status = 'OPEN'`
4. `SELECT c.id, ay.name, c.semester_id, c.status FROM cycle c JOIN academic_year ay ... ORDER BY c.id`
5. `SELECT id, name FROM academic_year ORDER BY id`

---

## SECTION 13: SUMMARY OF FINDINGS

### 13.1 Schema Architecture

**Current State**:
- System uses NEW `cycle` table (migration 021)
- OLD `academic_cycle` table renamed to `academic_cycle_old_backup`
- `subject_offering` has DUAL columns: `academic_year` (STRING) + `academic_year_id` (INTEGER FK)
- `faculty_preference` and `allocation` use `cycle_id` (INTEGER FK)

### 13.2 Active Cycle Query Pattern

**All services use**:
```python
academic_year, semester_id = _resolve_active_cycle(session)
```

**Returns**: `(academic_year STRING, semester_id INTEGER)`

**Used in queries**:
```sql
WHERE so.academic_year = :year AND so.semester_id = :sem_id
```

### 13.3 Local vs Production Discrepancy

**Local (WORKING)**:
- 194 subject offerings total
- 78 for active cycle (2025-2026, Semester II)
- API returns 78 records

**Production (FAILING)**:
- Unknown subject offering count
- API returns 0 records
- Same query logic, different database

### 13.4 Next Steps for Diagnosis

1. **Test Railway debug endpoint**:
   ```bash
   curl https://fwms-workload-system-production.up.railway.app/api/debug/db-state \
     -H "Authorization: Bearer <token>"
   ```

2. **Compare output with local**:
   - subject_offering_total
   - subject_offering_grouped
   - active_cycle
   - academic_years

3. **Identify missing data**:
   - If subject_offering_total = 0 → migrations didn't seed data
   - If active_cycle = null → no OPEN cycle exists
   - If academic_years = [] → academic_year table empty

4. **Fix options**:
   - Option A: Export local DB, import to Railway
   - Option B: Re-run seed migrations on Railway
   - Option C: Manually populate missing tables

---

## APPENDIX A: Migration 021 Complete SQL

**File**: `migrations/021_semester_specific_cycles.sql`

**Key Operations**:
1. Creates `academic_year` table
2. Creates `cycle` table with FK to `academic_year` and `semester`
3. Migrates data from `academic_cycle` to `cycle`
4. Adds `academic_year_id` to `subject_offering`
5. Renames `academic_cycle_id` → `old_academic_cycle_id` in all tables
6. Adds `cycle_id` to `faculty_preference` and `allocation`
7. Renames `academic_cycle` → `academic_cycle_old_backup`

**Transaction**: Wrapped in `BEGIN; ... COMMIT;`

**Validation** (lines 359-380):
```sql
DO $
DECLARE
    cycle_count INTEGER;
    pref_count INTEGER;
    alloc_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO cycle_count FROM cycle;
    SELECT COUNT(*) INTO pref_count FROM faculty_preference WHERE cycle_id IS NOT NULL;
    SELECT COUNT(*) INTO alloc_count FROM allocation WHERE cycle_id IS NOT NULL;
    
    RAISE NOTICE '=== MIGRATION COMPLETE ===';
    RAISE NOTICE 'Created % new semester-specific cycles', cycle_count;
    RAISE NOTICE 'Migrated % preferences', pref_count;
    RAISE NOTICE 'Migrated % allocations', alloc_count;
    RAISE NOTICE 'Old academic_cycle table renamed to academic_cycle_old_backup';
END $;
```

---

## APPENDIX B: Environment Variable Usage Map

| Variable | File | Line(s) | Usage |
|----------|------|---------|-------|
| `DATABASE_URL` | `app/core/config.py` | 73 | Database connection |
| `DATABASE_URL` | `startup.sh` | 4, 7 | Migration execution |
| `SECRET_KEY` | `app/core/config.py` | 107 | JWT signing |
| `GOOGLE_CLIENT_ID` | `app/core/config.py` | 76 | OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | `app/core/config.py` | 77 | OAuth client secret |
| `GOOGLE_REDIRECT_URI` | `app/core/config.py` | 78 | OAuth callback URL |
| `FRONTEND_URL` | `app/core/config.py` | 82 | OAuth redirect target |
| `FRONTEND_URL` | `app/main.py` | 44 | CORS configuration |
| `FRONTEND_URL` | `app/auth/router.py` | 133 | OAuth callback redirect |
| `DEV_AUTH_BYPASS` | `app/core/config.py` | 119 | Dev auth mode |
| `DEV_AUTH_BYPASS` | `app/auth/router.py` | 118, 156 | Auth bypass logic |
| `VITE_API_URL` | `frontend/src/api/client.ts` | 4 | Backend API URL |
| `PORT` | `startup.sh` | 48 | Server port |
| `PYTHONPATH` | `Dockerfile` | 50 | Python module path |

---

**END OF TECHNICAL SNAPSHOT**
