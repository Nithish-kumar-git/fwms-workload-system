# FWMS Recruiter-Demo — Handoff Checkpoint

**Created:** 2026-10-15
**Branch:** `feature/recruiter-demo`
**Checkpoint commit (code):** `5680f73` — `fix: add safe demo startup diagnostics`
**Status:** Feature development paused. Demo is live. Institutional production is untouched.

---

## Table of Contents

1. [Project Purpose and Scope](#1-project-purpose-and-scope)
2. [Technology Stack and Architecture](#2-technology-stack-and-architecture)
3. [Repository and Git State](#3-repository-and-git-state)
4. [Which Deployment Is Which?](#4-which-deployment-is-which)
5. [Key Source Files](#5-key-source-files)
6. [Authentication and Authorization Design](#6-authentication-and-authorization-design)
7. [Demo Database Isolation and Synthetic-Data Safeguards](#7-demo-database-isolation-and-synthetic-data-safeguards)
8. [Environment Variables](#8-environment-variables)
9. [Verified Fixes and Changes](#9-verified-fixes-and-changes)
10. [Tests Run and Outcomes](#10-tests-run-and-outcomes)
11. [Live Checks Performed and Results](#11-live-checks-performed-and-results)
12. [Known Limitations](#12-known-limitations)
13. [Outstanding Checks](#13-outstanding-checks)
14. [Safe Commands to Resume Development](#14-safe-commands-to-resume-development)
15. [Next-Session Checklist and Completion Status](#15-next-session-checklist-and-completion-status)

---

## 1. Project Purpose and Scope

**FWMS** (Faculty Workload Management System) is a production system for the
Department of Computer Applications at Hindustan Institute of Technology and
Science. It implements a first-come-first-served (FCFS) subject-preference and
workload-allocation workflow for teaching faculty, coordinated by a timetable
coordinator (TT Coordinator) and the Head of Department (HOD).

**Recruiter-demo scope** (`feature/recruiter-demo`): A fully isolated, synthetic,
read-safe replica of FWMS intended for portfolio/recruiter evaluation. It runs
against a dedicated Neon PostgreSQL database (`fwms_demo`) populated exclusively
with synthetic data. It is completely separate from the institutional production
system — different backend service, different frontend project, different database,
different credentials.

Recruiters can log in as **HOD**, **TT Coordinator**, or **Teacher** without any
Google account and without accessing institutional data.

---

## 2. Technology Stack and Architecture

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy (psycopg2), Uvicorn |
| Frontend | React 18, TypeScript, Vite, Axios |
| Database | PostgreSQL (Neon — hosted) |
| Auth (institutional) | Google OAuth 2.0 + JWT (HS256) + HTTP-only session cookie |
| Auth (demo) | `POST /api/auth/demo-login` — role-selected synthetic JWT only |
| Backend hosting | Render (Docker, free tier) |
| Frontend hosting | Vercel (SPA, static) |
| Demo database | Neon — project `fwms-synthetic-demo`, database `fwms_demo` |

**Architecture overview:**

```
Recruiter browser
    |
    v
Vercel Preview (frontend)           <- CORS allowed only to Render demo backend
    |  VITE_API_URL = https://fwms-workload-system-1.onrender.com
    v
Render service (backend)            <- FWMS_DEMO_MODE=true; no Railway/Google/Redis
    |  FWMS_DEMO_DATABASE_URL = postgresql://fwms_demo_runtime@...
    v
Neon -- fwms_demo (database)        <- role: fwms_demo_runtime (restricted, non-superuser)
    |  fwms_demo_meta schema        <- isolation marker, not accessible to app role
```

Institutional production is a completely separate path; no demo activity affects it.

---

## 3. Repository and Git State

| Item | Value |
|------|-------|
| Local path | `C:\Users\itsni\.gemini\antigravity\scratch\faculty_selection` |
| GitHub remote | `https://github.com/Nithish-kumar-git/fwms-workload-system` |
| Active branch | `feature/recruiter-demo` |
| HEAD commit | `5680f73f5f56763d209f3fe3702488bc9cc691cb` |
| `origin/feature/recruiter-demo` | `5680f73f5f56763d209f3fe3702488bc9cc691cb` |
| HEAD matches remote | **YES — VERIFIED** |
| Staged changes | None |
| Tracked modified files | None (`git diff --check` = clean) |

**Untracked files (not committed, not related to demo — preserve as-is):**

```
DATABASE_SCHEMA.md                MIGRATION_CLEANUP_SUMMARY.md
DEPLOYMENT_MIGRATION_SUMMARY.md  MIGRATION_SYSTEM.md
FINAL_MIGRATION_ARCHITECTURE.md  PREFERENCE_SYSTEM_TRACE.md
GET_DATABASE_SIZE.md              RENDER_DEPLOYMENT.md
SAFE_MIGRATION_SUMMARY.md        RESUME_DATA_ANALYST.md
SECURITY_BREACH_REPORT.md        SYSTEM_AUDIT_REPORT.md
analyze_missing.py                create_secb.py
export_railway_db.py              migrate.sh
repair_scripts/                   schema_migrate.sh
seed.sh                           test_railway_connection.py
```

**Recent commit history:**

```
5680f73  fix: add safe demo startup diagnostics          (HEAD, feature/recruiter-demo)
06f1864  feat: add isolated synthetic recruiter demo
de68b17  docs: correct enforced RBAC role count
2a76d7e  chore: sanitize environment template
cd3b220  chore: untrack local credential helper
```

---

## 4. Which Deployment Is Which?

> **CRITICAL — Read this before touching any environment.**

### A. Institutional Production (DO NOT TOUCH)

| Item | Value |
|------|-------|
| Frontend URL | `https://fwms-workload-system.vercel.app` |
| Vercel project | `fwms-workload-system` (ID: `prj_XDxNJtCAqB576JHQGWrciQNA6Uyl`) |
| Backend URL | `https://fwms-workload-system.onrender.com` |
| `vercel.json` | Repository root `vercel.json` — proxies `/api` to institutional backend |
| Database | Separate institutional PostgreSQL — never the Neon demo |
| Auth | Google OAuth 2.0 (`@hindustanuniv.ac.in`) |
| Branch | `main` |
| **Allowed action** | **READ ONLY. Never deploy, modify, or connect demo to this.** |

### B. Recruiter-Demo Frontend (Vercel Preview)

| Item | Value |
|------|-------|
| Branch | `feature/recruiter-demo` |
| Vercel config | `demo/vercel.json` (NOT root `vercel.json`) |
| Build command | `node demo/build_frontend.mjs` |
| Output directory | `frontend/dist-demo` |
| Build variables | `VITE_FWMS_DEMO_MODE=true`, `VITE_API_URL=<demo-backend-origin>`, `VITE_DEV_MODE=false` |
| Deployed commit | **UNVERIFIED** (dashboard requires login; code HEAD = `5680f73`) |
| Deployment type | Preview (not Production) |
| Last confirmed active | VERIFIED — live health check passed, demo login works |
| **Safety rule** | Never promote to Production. Never link to institutional project. |

The demo frontend has **no `/api` proxy**. All API traffic goes directly to the
Render demo backend via `VITE_API_URL`. The `/api` path is not rewritten to HTML.

### C. Recruiter-Demo Backend (Render)

| Item | Value |
|------|-------|
| Service URL | `https://fwms-workload-system-1.onrender.com` |
| Service name | `fwms-workload-system-1` |
| Start command | `python -B demo/start_backend.py` (via Dockerfile CMD) |
| Dockerfile | `demo/Dockerfile` |
| Deployed commit | **UNVERIFIED** from dashboard (login required); known code = `5680f73` |
| Deployment type | Free tier Docker service |
| Last confirmed live | **VERIFIED** — `GET /api/health` -> `200 {"status":"ok","environment":"synthetic-demo"}` |
| **Safety rule** | Never run startup.sh, fixtures.sql, migrations, or seeds here. |

### D. Neon Demo Database

| Item | Value |
|------|-------|
| Neon project | `fwms-synthetic-demo` |
| Database | `fwms_demo` |
| Runtime role | `fwms_demo_runtime` (LOGIN enabled, non-superuser, no elevated attributes) |
| Schema owner role | `fwms_demo_app` (provisioning only — never in runtime service) |
| Isolation marker | `fwms_demo_meta.environment` — `(purpose='synthetic-only', schema_version=1)` |
| Deep health check | **VERIFIED** — `GET /api/health/deep` -> `200 {"status":"ok","database":"ok"}` |
| **Safety rule** | Never run any DDL, DML, fixture, or migration scripts from this checkpoint. |

---

## 5. Key Source Files

### Backend

| File | Purpose |
|------|---------|
| `demo/start_backend.py` | Fail-closed demo launcher. Validates env, strips institutional vars, wraps logging with a secret-redacting formatter. Never calls `startup.sh` or migrations. |
| `demo/Dockerfile` | Docker image for Render demo service. Non-root user, copies only `app/` and the demo launcher/probe. Excludes fixtures/migrations. |
| `demo/healthcheck.py` | Loopback health probe (`127.0.0.1:{port}/api/health`), verifies `environment=synthetic-demo`. |
| `demo/vercel.json` | Separate Vercel config for the demo frontend. SPA rewrites only. No API proxy. |
| `demo/build_frontend.mjs` | Isolated Vite build. Enforces `VITE_FWMS_DEMO_MODE=true`, validates API origin, strips unrelated `VITE_*` vars, embeds CSP with exact `connect-src`. Rejects institutional origins. |
| `demo/fixtures.sql` | Synthetic seed data. Run once during initial provisioning only. **Do not re-run.** |
| `demo/schema.sql` | Schema definitions for the demo database. Run once. **Do not re-run.** |
| `app/demo/config.py` | Parses `FWMS_DEMO_*` env vars. Returns a Settings override dict that disables Google OAuth, sets domain to `demo.example.com`, hardcodes `DEMO_MODE=True`. |
| `app/demo/isolation.py` | `validate_demo_connection()` — run on every SQLAlchemy connection checkout. Verifies database name, runtime role, privilege flags, synthetic marker, and schema write-privileges. |
| `app/demo/accounts.py` | `ensure_demo_account()` — server-selected synthetic identities. Never accepts a client-supplied staff ID. |
| `app/db/pool.py` | Registers the `validate_demo_connection` checkout hook when `DEMO_MODE=True`. |
| `app/core/config.py` | Main settings class. In demo mode, skips `_check_required_env_vars()` and uses `demo_settings_from_env()` overrides. |
| `app/auth/router.py` | Auth endpoints. `GET /login` and `GET /callback` return HTTP 403 in demo mode. `POST /demo-login?role=` provisions synthetic accounts. |
| `app/auth/google_oauth.py` | Google OAuth client. Not invoked in demo mode (empty credentials supplied by config). |
| `app/main.py` | CORS configured to `allow_origins=[settings.FRONTEND_URL]` in demo mode (single exact origin, no wildcard). |
| `app/health/router.py` | `/api/health` returns `environment: "synthetic-demo"`. `/api/health/deep` executes `SELECT 1`, triggering the isolation checkout guard. |

### Frontend

| File | Purpose |
|------|---------|
| `frontend/src/pages/LoginPage.tsx` | Google button disabled when `VITE_FWMS_DEMO_MODE=true`. Shows role selector (HOD / TT Coordinator / Teacher) and calls `POST /api/auth/demo-login`. Shows wake-up banner on cold start. |
| `frontend/src/api/client.ts` | Axios instance. Validates API origin in demo mode at module load. `demoLogin(role)` -> `POST /api/auth/demo-login`. Intercepts OAuth `?token=` from URL (institutional only). |
| `frontend/src/context/AuthContext.tsx` | Reads JWT from `localStorage`, calls `/api/auth/me`, derives `isHOD`, `isCoordinator`, `isFaculty` from `user.role`. |

---

## 6. Authentication and Authorization Design

### Synthetic Demo Auth Flow

```
1. Recruiter visits /login
2. Selects role from dropdown (HOD / TT Coordinator / Teacher)
3. Clicks "Try Demo -- No login required"
4. Frontend: POST /api/auth/demo-login?role=hod  (or tt_coordinator / faculty)
5. Backend: ensure_demo_account() verifies/creates synthetic staff row
6. Backend: create_jwt(..., iss="fwms-synthetic-demo", aud="fwms-synthetic-demo")
7. Frontend: stores access_token in localStorage as jwt_token
8. AuthContext: calls GET /api/auth/me -> returns role
9. Router: navigates to /hod-dashboard, /dashboard, or /faculty-dashboard
```

### JWT Isolation

- Demo JWTs use `iss="fwms-synthetic-demo"` and `aud="fwms-synthetic-demo"`.
- `accept_token_environment()` in `app/demo/isolation.py` ensures demo tokens are
  rejected by the institutional backend and vice versa.
- Demo session cookie name is `fwms_demo_session` (not `faculty_session`),
  preventing cross-contamination.

### Authorization (RBAC)

Authorization is based solely on `staff.role` (DB column), refreshed from the
database on every `/api/auth/me` call. The `faculty_role` table exists but is
**not** the active authorization mechanism.

| Role | `/api/subjects/programs` | HOD dashboard | Coordinator dashboard | Faculty dashboard |
|------|--------------------------|---------------|-----------------------|-------------------|
| `hod` | 200 VERIFIED | Yes | Yes | -- |
| `tt_coordinator` | 200 VERIFIED | -- | Yes | -- |
| `faculty` | 403 VERIFIED | -- | -- | Yes |

### Google OAuth (Institutional Only — Disabled in Demo)

- `GET /api/auth/login` -> HTTP 403: `"Use synthetic demo login in this environment"`
- `GET /api/auth/callback` -> HTTP 403: `"Google login is not enabled in the synthetic demo"`
- Frontend Google button disabled: label = `"Google sign-in unavailable in synthetic demo"`
- **VERIFIED live** on Render demo service (2026-10-15).

---

## 7. Demo Database Isolation and Synthetic-Data Safeguards

### Connection-Level Isolation Guard

Every SQLAlchemy connection checkout triggers `validate_demo_connection()`, verifying:

1. `current_database() = 'fwms_demo'` and `current_user = 'fwms_demo_runtime'`
2. All privilege flags are false: `rolsuper`, `rolcreatedb`, `rolcreaterole`,
   `rolbypassrls`, `rolreplication`, `rolinherit`
3. No role memberships (`pg_auth_members`) or shared dependencies (`pg_shdepend`)
4. `fwms_demo_meta.environment` contains `(purpose='synthetic-only', schema_version=1)`
   with `singleton=true`
5. `fwms_demo_runtime` cannot `CREATE` in `public` or `fwms_demo_meta`
6. `fwms_demo_runtime` cannot `INSERT/UPDATE/DELETE/TRUNCATE/TRIGGER` on
   `fwms_demo_meta.environment`
7. `SET SESSION search_path TO public` (prevents schema shadowing)

If any check fails, the connection is refused and `GET /api/health/deep` returns
`{"database": "error", "database_error": "Demo database unavailable"}`.

### Synthetic Data Summary

| Table | Rows | Content |
|-------|------|---------|
| `staff` | 2 | `synthetic-alpha@demo.example.com` (id 1), `synthetic-beta@demo.example.com` (id 2) |
| `program` | 1 | Synthetic programme |
| `subject` | 2 | Synthetic subjects |
| `subject_offering` | 2 | Synthetic offerings |
| `faculty_preference` | 1 | One sample preference |
| `allocation` | 1 | One sample allocation |
| `workload_summary` | 1 | One summary row |
| `faculty_role` | 0 | Empty — expected by design |
| `workload_snapshot` | 0 | Empty — expected (no HOD approval yet) |

Demo accounts (provisioned on first login, not in fixtures):

| Role | Email | Name | Emp Code |
|------|-------|------|----------|
| `hod` | `demo@fwms-demo.com` | Demo HOD | DEMO001 |
| `tt_coordinator` | `coordinator@demo.example.com` | Demo Coordinator | DEMO002 |
| `faculty` | `teacher@demo.example.com` | Demo Teacher | DEMO003 |

---

## 8. Environment Variables

### Render Demo Backend (`fwms-workload-system-1`)

| Variable | Purpose | Required |
|----------|---------|----------|
| `FWMS_DEMO_MODE` | Must be `true`. Activates isolation and disables Google OAuth. | YES |
| `FWMS_DEMO_DATABASE_URL` | `postgresql://fwms_demo_runtime@.../fwms_demo`. Must use the restricted runtime role. | YES |
| `FWMS_DEMO_SECRET_KEY` | JWT signing secret, >= 32 characters. Independently generated. | YES |
| `FWMS_DEMO_FRONTEND_URL` | Exact HTTPS origin of the Vercel demo frontend (no trailing slash). Must match Vercel preview URL for CORS. | YES |
| `PORT` | Supplied by Render. Launcher binds to this port. | By host |

**Do NOT set on this service:** `DATABASE_URL`, `SECRET_KEY`, `GOOGLE_CLIENT_ID`,
`GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `REDIS_URL`, `DEV_AUTH_BYPASS`.

### Vercel Demo Frontend (separate Vercel project)

| Variable | Purpose | Required |
|----------|---------|----------|
| `VITE_FWMS_DEMO_MODE` | Must be `true`. Enables demo UI (role selector, disables Google button). | YES |
| `VITE_API_URL` | `https://fwms-workload-system-1.onrender.com`. No `/api` suffix. | YES |
| `VITE_DEV_MODE` | Must be `false`. Hides dev-only login buttons. | YES |

**Do NOT set:** database URLs, signing secrets, or Google OAuth secrets.

### Institutional Backend (`fwms-workload-system.onrender.com`)

Standard institutional environment — untouched and not documented here.

---

## 9. Verified Fixes and Changes

| Commit | Description |
|--------|-------------|
| `5680f73` | **fix: add safe demo startup diagnostics** — `demo/start_backend.py` expanded with `RedactingFormatter`: redacts PostgreSQL URL patterns, Bearer tokens, and JWTs from all log output including tracebacks and JSON extras. Fail-closed error reporting. |
| `06f1864` | **feat: add isolated synthetic recruiter demo** — Core demo infrastructure: `demo/start_backend.py`, `demo/Dockerfile`, `demo/vercel.json`, `demo/build_frontend.mjs`, `demo/healthcheck.py`, `app/demo/` package, `app/db/pool.py` checkout hook, frontend demo login UI, and full test suite. |
| `de68b17` | **docs: correct enforced RBAC role count** |
| `2a76d7e` | **chore: sanitize environment template** |
| `cd3b220` | **chore: untrack local credential helper** |

---

## 10. Tests Run and Outcomes

All tests run locally on `feature/recruiter-demo` at commit `5680f73` (2026-10-15).

### Python Backend Tests

```
python -B demo/test_deployment.py -v
```

**Result: 12/12 PASS — VERIFIED**

All tests pass including: health route contract, secret redaction, fail-closed
launcher validation, log formatter safety, isolation role pairs, missing-variable
fallback prevention, and startup without shell or migrations.

### Node.js Frontend/Integration Tests

```
node --experimental-vm-modules --test \
  demo/test_deployment.mjs \
  demo/test_frontend_config.mjs \
  demo/test_preferences_retry.mjs \
  demo/test_api_docs.mjs \
  demo/test_allocation_filters.mjs
```

**Result: 32/32 PASS — VERIFIED**

Covers: SPA rewrite completeness, API origin isolation, CSP `connect-src` boundary,
demo build isolation (no `.env` reading, no institutional origin fallback),
Retry/stale-state race conditions, Docs link per role, program filter accuracy.

### Frontend Build Verification

```
node demo/verify_frontend.mjs
```

**Result: PASS** — 0 TypeScript diagnostics; Vite builds 1826 modules cleanly.

### Whitespace Check

```
git diff --check
```

**Result: CLEAN** (exit code 0, no output).

---

## 11. Live Checks Performed and Results

All checks against the live hosted demo on 2026-10-15 (IST).

| Check | Endpoint | Expected | Result |
|-------|----------|---------|--------|
| Backend health | `GET /api/health` | `200 {environment: "synthetic-demo"}` | **200 VERIFIED** |
| DB isolation | `GET /api/health/deep` | `200 {database: "ok"}` | **200 VERIFIED** |
| Google login blocked | `GET /api/auth/login` | `403` | **403 VERIFIED** |
| Google callback blocked | `GET /api/auth/callback?code=fake` | `403` | **403 VERIFIED** |
| HOD demo login | `POST /api/auth/demo-login?role=hod` | `200 + JWT` | **VERIFIED** (prior session) |
| `/api/auth/me` | `GET /api/auth/me` with HOD token | `200 {role: "hod"}` | **VERIFIED** |
| RBAC — HOD programs | `GET /api/subjects/programs` as HOD | `200` | **VERIFIED** |
| RBAC — coordinator | `GET /api/subjects/programs` as coordinator | `200` | **VERIFIED** |
| RBAC — faculty | `GET /api/subjects/programs` as faculty | `403` | **VERIFIED** |

---

## 12. Known Limitations

### Google OAuth Intentionally Disabled

Google sign-in is **by design** disabled and blocked in synthetic demo mode:

- `GET /api/auth/login` -> HTTP 403: `"Use synthetic demo login in this environment"`
- `GET /api/auth/callback` -> HTTP 403: `"Google login is not enabled in the synthetic demo"`
- Frontend Google button: disabled, label = `"Google sign-in unavailable in synthetic demo"`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` are all `""` in demo mode

**This is a deliberate isolation feature, not a defect.**

### Other Limitations

- **Cold-start latency:** Render free tier spins down after ~15 min idle. First
  request may take 20-60 seconds. The login page shows a wake-up banner and retries
  every 8 seconds automatically.
- **Preference window closed:** Intentional at startup. TT Coordinator must open it.
- **Shared demo accounts:** All visitors share the same synthetic accounts. Not
  per-visitor isolation. Demo data can be mutated by concurrent visitors.
- **Workload snapshot empty:** Correct initial state. Populated only after HOD approval.
- **`faculty_role` empty:** Expected. `staff.role` is the active authorization source.
- **Stale Railway URL:** Untracked `.env.local` has an old `VITE_API_URL` pointing
  to the decommissioned Railway domain. Not committed; no deployment impact.
- **Render SHA UNVERIFIED:** Dashboard requires authentication; cannot read commit SHA
  programmatically from outside.
- **Vercel Preview SHA UNVERIFIED:** Same limitation. Behaviorally consistent with
  `5680f73` (Vercel `Last-Modified` header is after the commit timestamp).

---

## 13. Outstanding Deployment or Configuration Checks

| Item | Status |
|------|--------|
| Verify exact Render deployed commit SHA | UNVERIFIED — requires dashboard login |
| Verify exact Vercel Preview deployed commit SHA | UNVERIFIED — requires dashboard login |
| Verify `FWMS_DEMO_FRONTEND_URL` on Render matches active Vercel Preview URL | VERIFIED indirectly (CORS passes, credentials succeed) |
| Confirm Vercel Preview not promoted to Production | Not promoted; institutional Production is unmodified |
| Add demo link to README | Pending operator decision — not done |

---

## 14. Safe Commands to Resume Development

### Verify current state

```bash
git branch --show-current
# Expected: feature/recruiter-demo

git rev-parse HEAD
git rev-parse origin/feature/recruiter-demo
# Both must be: 5680f73f5f56763d209f3fe3702488bc9cc691cb

git status --short
# Expected: only untracked ?? lines (no M or A lines)

git diff --check
# Expected: empty output, exit code 0
```

### Run the test suite (no network or DB required)

```bash
python -B demo/test_deployment.py -v

node --experimental-vm-modules --test \
  demo/test_deployment.mjs \
  demo/test_frontend_config.mjs \
  demo/test_preferences_retry.mjs \
  demo/test_api_docs.mjs \
  demo/test_allocation_filters.mjs

node demo/verify_frontend.mjs
```

### Verify live demo backend

```bash
curl https://fwms-workload-system-1.onrender.com/api/health
curl https://fwms-workload-system-1.onrender.com/api/health/deep
```

### Run the demo backend locally

```bash
FWMS_DEMO_MODE=true \
FWMS_DEMO_DATABASE_URL="postgresql://fwms_demo_runtime@.../<fwms_demo>" \
FWMS_DEMO_SECRET_KEY="<32+ char secret>" \
FWMS_DEMO_FRONTEND_URL="http://localhost:5173" \
python -B demo/start_backend.py
```

### Commands that must NEVER be run

```
python startup.sh                             # Institutional startup
psql ... -f demo/fixtures.sql                 # Do not re-seed
psql ... -f demo/schema.sql                   # Do not re-apply schema
run_migrations.bat / migrate.sh               # Institutional/Railway scripts
git push origin feature/recruiter-demo:main   # Never merge to main
vercel --prod                                 # Never promote demo to Production
```

---

## 15. Next-Session Checklist and Completion Status

### Completion Status

| Deliverable | Status |
|-------------|--------|
| `feature/recruiter-demo` branch pushed to GitHub | COMPLETE |
| Render demo backend live and healthy | COMPLETE |
| Database isolation guard verified via deep health | COMPLETE |
| Google OAuth blocked in demo mode | COMPLETE |
| HOD demo login working | COMPLETE |
| RBAC guards verified (HOD/coordinator 200, faculty 403) | COMPLETE |
| Python deployment tests: 12/12 pass | COMPLETE |
| Node.js integration tests: 32/32 pass | COMPLETE |
| Frontend build clean (0 TS errors) | COMPLETE |
| Whitespace check clean | COMPLETE |
| Institutional Production untouched | COMPLETE |
| This handoff document | COMPLETE |

### Next-Session Checklist

Before resuming any development:

- [ ] `git branch --show-current` -> must be `feature/recruiter-demo`
- [ ] `git rev-parse HEAD` and `git rev-parse origin/feature/recruiter-demo` -> must match
- [ ] `git status --short` -> only untracked artefacts, no tracked changes
- [ ] `curl .../api/health` -> must return `environment: "synthetic-demo"`
- [ ] Confirm Vercel Preview for `feature/recruiter-demo` is still a Preview (not promoted)
- [ ] Log into Render dashboard -> note deployed commit SHA for `fwms-workload-system-1`
- [ ] Log into Vercel dashboard -> note deployed commit SHA for the demo Preview
- [ ] If either deployed SHA differs from `5680f73`, determine if intentional before proceeding

**Do not begin new feature work until all checkboxes are confirmed.**

---

*Handoff document created 2026-10-15.*
*All facts are labeled VERIFIED, LAST KNOWN, or UNVERIFIED.*
*No secrets, credentials, database passwords, signing keys, or OAuth tokens appear in this document.*
