# PROJECT_CONTEXT.md — FWMS (Faculty Workload Management System)

> **Last updated**: 2026-03-16  
> **Source**: Reverse-engineered from repository code. Anything unverified marked **UNKNOWN FROM REPOSITORY**.

---

## 1. System Purpose

Dual-purpose academic system for the Department of Computer Applications (MCA/BCA) at Hindustan University:

1. **FCFS Subject Selection** — Time-windowed first-come-first-served subject selection with advisory-lock concurrency control
2. **Faculty Workload Management** — Preference-driven allocation engine, coordinator overrides, workload reporting

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Backend | **FastAPI** (Python 3.12), raw SQL via `sqlalchemy.text()` |
| Database | **PostgreSQL 15+** (no ORM models) |
| Auth | **Google OAuth 2.0** + **PyJWT** (HS256) + session cookies |
| Sessions | **Redis** (prod) / **in-memory** (dev) |
| Frontend | **React 19** + **Vite 7** + **Tailwind CSS v4** + **axios** + **react-router-dom v7** |
| Container | **Docker** (multi-stage Python 3.12-slim) + **docker-compose** |
| Exports | **openpyxl** (Excel), **reportlab** (PDF) |

---

## 3. Repository Layout

```
app/
├── main.py                    # FastAPI entry, middleware, router inclusion
├── core/config.py             # Pydantic Settings (env validation)
├── core/correlation_middleware.py  # X-Correlation-ID per request
├── db/pool.py                 # SQLAlchemy engine (pool_size=10, max_overflow=20)
├── db/session.py              # get_transaction() context manager (5s lock_timeout)
├── auth/                      # Google OAuth, JWT, sessions, dependencies
├── allocation/                # POST /api/allocation/run — 3-stage engine
├── admin/                     # Review, override, reassign, freeze, staff CRUD, cycles
├── preference/                # Submit/list/delete prefs + window open/close
├── selection/                 # FCFS transactions (advisory locks)
├── coordinator/               # Override transactions
├── reports/                   # Workload/subject/dept reports + Excel/PDF export
├── health/                    # GET /health
└── utils/error_mapper.py      # SQLSTATE → HTTP status mapper
frontend/src/
├── App.tsx                    # 10 routes (login, dashboard, 7 admin pages)
├── api/client.ts              # axios + JWT interceptor + token capture
├── pages/                     # 9 page components
└── components/                # Navbar, Modal, ToastContainer
migrations/                    # 11 SQL files (schema.sql → 011_update_staff_emails.sql)
scripts/                       # demo_prep.py, demo_seed.sql
```

---

## 4. Database Tables (16+)

**Base schema** (`schema.sql`): `staff`, `selection_window`, `batch`, `specialization`, `staff_assignment`, `subject`, `subject_selection`, `audit_log`

**Workload extension** (`005`): `program`, `semester`, `section`, `subject_offering`, `faculty_role`, `faculty_preference`, `allocation`, `workload_summary`

**Cycle support** (`010`): `academic_cycle` (FK linked to offerings, preferences, allocations, summaries, windows)

### Key Constraints
- `uq_subject_selected` — FCFS guarantee (one SELECTED per subject)
- `uq_faculty_preference_number` — PREF-03 (each faculty uses each pref# once)
- `uq_subject_offering_preference` — PREF-02 (no two faculty same pref# for same offering)
- `audit_log` triggers prevent UPDATE/DELETE (append-only)
- `selection_window` trigger prevents time changes after SCHEDULED state

### Staff Columns (post-migration 005+007)
`id, email, name, is_coordinator, is_active, emp_code, designation, shift, tch_norm, total_workload_norm, is_class_teacher, ct_program, ct_section, ct_semester, ct_shift`

### Seed Data
- **27 faculty** from institutional FACULTY-LIST (migration 007)
- **100+ subjects** from MCA/BCA curriculum (migration 006)
- Subject offerings: subject × program × semester × section (MCA: 3 sections, BCA: 6 sections)

---

## 5. API Endpoints (40+)

| Group | Prefix | Key Endpoints |
|---|---|---|
| Auth | `/api/auth` | `GET /login`, `GET /callback`, `POST /dev-login`, `GET /me`, `POST /logout` |
| Preferences | `/api/preferences` | `POST /`, `GET /me`, `GET /status`, `DELETE /{id}` |
| Pref Window | `/api/pref-window` | `POST /open`, `POST /close`, `GET /status` |
| Allocation | `/api/allocation` | `POST /run` |
| Admin | `/api/admin` | `GET /allocations`, `PUT /allocation/{id}`, `POST /reassign`, `POST /allocation/freeze`, `POST /allocation/unfreeze`, `GET /workload-summary` |
| Staff | `/api/admin/staff` | `GET /`, `POST /`, `PUT /{id}`, `PATCH /{id}/deactivate` |
| Cycles | `/api/cycles` | `POST /`, `POST /activate`, `GET /`, `GET /active` |
| Reports | `/api/reports` | `GET /faculty-workload`, `GET /subject-summary`, `GET /department-summary`, `GET /export/workload.xlsx`, `GET /export/workload.pdf` |
| Selection | `/api/selection` | `POST /select` (FCFS) |
| Coordinator | `/api/coordinator` | `POST /override` |
| Health | `/health` | `GET /` |

---

## 6. Auth System

**Flow**: Browser → Google OAuth → callback → verify ID token → validate `@hindustanuniv.ac.in` → create session + JWT → set `faculty_session` cookie + redirect with `?token=JWT`

**Roles**: `coordinator` (`is_coordinator=true`), `hod` (`designation='HOD'`), `faculty` (default). Role **always** resolved from DB per-request, never trusted from token.

**Dev bypass**: `DEV_AUTH_BYPASS=true` auto-logs in as coordinator. **Blocked at startup in production** via `RuntimeError`.

---

## 7. Allocation Engine

**Location**: `app/allocation/service.py` (517 lines)

**3-Stage Pipeline**:
1. **Pref-1 pass** — allocate each faculty's first-choice (if shift-compatible, under norm)
2. **Pref 2–5 pass** — iterate remaining preferences in order
3. **Final pass** — assign unallocated subjects to lowest-load compatible faculty

**Constraints**: shift compatibility, `tch_norm` workload cap (default 16), multi-section prevention (no same course code twice), active academic cycle required.

**Side effects**: clears existing allocations before re-run, updates `workload_summary`, logs to `audit_log`.

---

## 8. Preference Validation Rules

| Rule | Check |
|---|---|
| PREF-01 | `preference_number` 1–5 |
| PREF-02 | No two faculty same pref# for same offering |
| PREF-03 | Faculty cannot reuse same pref# |
| PREF-04 | Max 5 preferences per faculty |
| PREF-DUP | No duplicate faculty-offering pair |
| SHIFT-01 | Faculty shift matches offering shift |
| CT-01 | Class teacher pref=1 must match their class |

Window guard: only accepted when `selection_window.status = 'OPEN'`.

---

## 9. FCFS Selection (Advisory Lock Model)

**Lock ordering** (FROZEN — do not reorder):
1. `FOR SHARE` → window validation (`status='OPEN'`, batch/spec scoping)
2. `FOR SHARE` → eligibility (staff_assignment check)
3. `pg_advisory_xact_lock(staff_id)` → staff serialization
4. `pg_advisory_xact_lock(staff_id, window_id)` → staff+window serialization
5. `FOR UPDATE` → quota check
6. `FOR UPDATE` → slot assignment
7. `INSERT ... ON CONFLICT DO NOTHING` → FCFS claim
8. `INSERT` → audit log

SQLSTATE error mapping: `40P01` (deadlock) and `55P03` (lock timeout) → 409 "Concurrent change detected".

---

## 10. Environment Variables

| Variable | Default | Notes |
|---|---|---|
| `ENV` | `development` | `development`/`staging`/`production` |
| `DATABASE_URL` | — | Must start with `postgresql://` |
| `GOOGLE_CLIENT_ID/SECRET` | — | Required (validated in prod) |
| `GOOGLE_REDIRECT_URI` | — | OAuth callback URL |
| `SECRET_KEY` | — | ≥32 chars (validated) |
| `ALLOWED_EMAIL_DOMAIN` | `hindustanuniv.ac.in` | Email restriction |
| `SESSION_BACKEND` | `memory` | Must be `redis` in production |
| `SESSION_EXPIRATION_HOURS` | `4` | JWT/session TTL |
| `POOL_SIZE` | `10` | SQLAlchemy pool |
| `DEV_AUTH_BYPASS` | `false` | **Blocked in production** |

---

## 11. Docker

- **docker-compose.yml**: `db` (postgres:15) + `app` (FastAPI). Migrations run on startup via entrypoint.
- **Dockerfile**: Multi-stage (builder + runtime). Python 3.12-slim. Healthcheck on `/health`.
- **Frontend**: Run locally via `cd frontend && npm run dev` (not containerized).

---

## 12. Migration Order

`schema.sql` → `002_window_lifecycle` → `005_workload_schema` → `006_academic_seed` → `007_faculty_seed` → `008_admin_override_schema` → `009_window_audit_types` → `010_academic_cycle_support` → `011_update_staff_emails`

> Migrations 003 and 004 are **UNKNOWN FROM REPOSITORY**.

---

## 13. Known Issues

| Issue | Severity |
|---|---|
| `audit_log` constraint conflict: migration 009 defines types (`SUBJECT_SELECTED`, etc.) that don't match code-emitted values (`SELECT`, `CHANGE`, `OVERRIDE`) | **High** |
| `reports/service.py` hardcodes `ACADEMIC_YEAR="2025-2026"` and `SEMESTER_TYPE="EVEN"` | Medium |
| `InMemorySessionBackend` loses sessions on restart (dev only) | Medium |
| Frontend routes lack role-based guards (backend-only enforcement) | Low |
| `audit_router` inclusion in `main.py` is TODO | Info |

---

## 14. Demo Pipeline

**Python** (`scripts/demo_prep.py`): dev-login → ensure cycle → open window → clear data → seed 5 prefs/faculty → run allocation

**SQL** (`scripts/demo_seed.sql`): same logic, pure SQL, requires manual `POST /api/allocation/run` after.
