# FWMS Recruiter-Demo — Handoff Checkpoint

**Created:** 2026-10-15
**Branch:** `feature/recruiter-demo`
**Checkpoint commit (code):** `5680f73` — `fix: add safe demo startup diagnostics`
**Status:** Feature development paused. Demo is live. Institutional production is untouched.

## 22 October 2026 security-containment and rollout-readiness review

This bounded review supersedes the 21 October Git, credential and Render status
below. It did not query application tables, test credentials, change provider
settings, deploy, restart a service, alter a schema, push, or rewrite history.

### Current Git state

| Item | Verified value |
|---|---|
| Active branch | `feature/recruiter-demo` |
| Review base HEAD (before this documentation commit) | `f4adc2925510f7ea4bf999fec088716d7bbd3ff4` |
| Upstream | `origin/feature/recruiter-demo` at `15fdeb3f42a86e662609c9aa960df87599af3ebf` |
| Ahead / behind after fetch at review start | 3 ahead / 0 behind |
| Tracked worktree | Clean before this documentation update |
| Untracked worktree | The same 20 migration/security notes and helper files listed in section 3; all preserved and excluded from this commit |

The unpublished sequence is `f6b61d3` (administrative containment and atomic
allocation), `cb9f324` (shared-workload serialization and programme finalization),
then `f4adc29` (documentation reconciliation). No remote branch contains either
repair commit.

### Redacted credential-containment findings

No credential was tested or used, and no value is recorded here. Classification
is based only on file shape, host class and placeholder markers.

| Location | Finding | Current containment |
|---|---|---|
| Feature-tip `.env.example` | Placeholder-only database, OAuth and signing settings | Safe template at local HEAD and `origin/feature/recruiter-demo` |
| Feature-tip `run_migrations.bat` | No credential; refuses automatic replay and points to the reviewed procedure | Contained in unpublished `f6b61d3` |
| Public `main` and history: `run_migrations.bat` | Embedded Railway PostgreSQL connection credential candidate | Still present on `origin/main` and in public history; activity was not tested |
| Public `main`: `.env.example` | Explicit signing/OAuth placeholders plus a local/Compose database credential literal | Not evidence of a remote secret; rotate anywhere it was reused outside disposable local development |
| Public `main` and history: `verify_dev_auth.py` | Local/test database, OAuth and signing literals | Removed from the feature branch by `cd3b220`; an ignored untracked local copy remains preserved |

The Railway connection material has the structure of a real remote credential,
but whether it is still active cannot be established safely without testing it,
which is prohibited. The named Google values are placeholders/test-like, not
evidence of a real Google client secret. The signing literals are usable values;
whether either was copied into Render or another deployed environment remains
**UNVERIFIED** and requires a private equality/reuse assessment by the application
owner. If a deployed signing key matches, rotation invalidates existing JWTs and
cookies and must be treated as a planned session-invalidation event. Institutional
and recruiter-demo signing keys must remain independent.

Containment checklist requiring owner approval:

1. Railway/PostgreSQL owner: identify the credential by repository location,
   rotate or revoke it without testing the old value, and review database access
   logs from the exposure window.
2. Render/institutional service owner: determine privately whether the exposed
   Railway credential is the service's database credential. Do not introduce a
   replacement while the deployed `8780324` startup can print it; first approve a
   guarded-launcher rollout or an equivalent no-log maintenance path.
3. Application security owner: compare deployed signing-key fingerprints or values
   privately against historical/local candidates. If reused or uncertain, rotate
   the affected key and explicitly invalidate sessions/JWTs; do not copy values
   into tickets, commits or logs.
4. Google/SMTP owners: confirm the template/test-looking values were never reused.
   Rotate only an actual matching provider credential; repository evidence alone
   does not establish one.
5. GitHub owner: after provider containment, decide whether to rewrite public
   history and coordinate clones, forks, caches and deployment references. History
   rewriting is not a substitute for rotation and was not attempted here.

### Current Render rollout evidence

Read-only Render metadata was retrieved from the user-confirmed workspace on
2026-10-22. Environment variables and logs were not requested.

| Service | Branch / automatic deployment | Current live deploy | Runtime configuration |
|---|---|---|---|
| `fwms-workload-system-1` | `feature/recruiter-demo`; **On Commit enabled** | `15fdeb3`; Render status `live` | Docker, context `.`, `demo/Dockerfile`, no command override |
| `fwms-workload-system` | `main`; **On Commit enabled** | `8780324`; Render status `live` | Docker, context `.`, `./Dockerfile`, no command override |

Both services have a blank provider HTTP health-check path, so Render does not
currently use `/api/health` as an application-level readiness check. A `live`
deploy status is provider metadata, not a fresh endpoint or browser verification;
no hosted request was made during this review.

The live recruiter image uses `demo/Dockerfile`, the fail-closed
`demo/start_backend.py` launcher and its loopback `demo/healthcheck.py`. It does
not copy or replay migration/fixture files. A push of local HEAD would immediately
roll out all three unpublished commits unless auto-deploy is disabled first.

The live institutional image is materially different. Commit `8780324` uses the
old root `startup.sh`, prints the configured database URL, and automatically
replays the legacy migration/seed/cleanup list before starting Uvicorn. Its Docker
health probe targets the historical `/health` path. The local `f6b61d3` repair
removes migration files from the image, routes startup through `app.start_backend`,
suppresses credential logging and probes `/api/health`, but that repair is neither
on `main` nor deployed. Do not restart or redeploy the institutional service as a
containment shortcut without an approved plan.

### Schema, provisioning and verification boundary

The two repair commits add no schema migration. They rely on the already-provisioned
contract documented in `docs/SECURITY_CONTAINMENT.md`: cycle/year linkage, the
unique `(staff_id, academic_year, semester_type)` workload-summary key, audit-log
support and immutable workload snapshots. The demo additionally requires its
separately initialized `fwms_demo` schema, synthetic marker and restricted
`fwms_demo_runtime` role. Disposable PostgreSQL 18.1 tests exercised that contract,
but neither the deployed institutional schema nor the Neon demo schema was queried
in this review, so current compatibility remains **UNVERIFIED**.

No test suite was rerun because application code did not change. Evidence reviewed:
the previously recorded 24 focused offline tests, 12 demo launcher/deployment tests
and 10 disposable-PostgreSQL checks passed at `cb9f324`; Python syntax, Compose
parsing, shell syntax and whitespace were also recorded as passing. Docker/Compose,
hosted endpoints, browser workflows, live RBAC and deployed-schema checks remain
unverified.

**Single next action:** obtain a jointly approved containment window from the
Railway/PostgreSQL credential owner and the institutional Render owner. The plan
must prevent the live `8780324` startup from logging the replacement credential,
rotate/revoke the exposed Railway credential, review provider logs, and decide
session invalidation before any feature-branch push or rollout.

### Approved credential-containment window — operator checklist

This is a preparation runbook, not authorization to make the changes. Do not put
credential values, connection strings, key fingerprints, deploy hooks or log
exports in the ticket, Git history or this document. Record only the operator,
time window, service/commit identifiers and a redacted result.

1. **Name the approving owners before the window.** The Railway/PostgreSQL owner
   owns database credential generation, revocation and database audit-log access.
   The institutional Render owner owns the institutional service configuration and
   deployment controls; the recruiter-demo Render owner owns the demo service.
   The database/schema owner owns compatibility and backup/restore decisions; the
   application-security owner owns signing-key reuse and session invalidation; the
   release owner owns the final go/no-go and rollback call. Every state-changing
   step below requires the relevant owner's explicit approval.

2. **Freeze automatic deployment deliberately.** Before any branch push, capture
   the live commits and an available rollback artifact for both services, confirm
   that no deploy is running, and obtain release-owner approval to turn off
   On-Commit deployment for both `fwms-workload-system-1` and
   `fwms-workload-system`. This prevents an ordinary push from deploying an
   unreviewed image. Re-enable it only after the release owner closes the window.

3. **Remove the unsafe institutional startup path first.** Do not restart,
   redeploy or apply a configuration-only change to the currently live
   institutional `8780324` image: its `startup.sh` can print the configured
   database URL and replay legacy migration/seed/cleanup SQL. Before a replacement
   database credential is introduced, the institutional Render owner must approve
   and deploy a reviewed `main` commit that uses the guarded `app.start_backend`
   launcher, excludes migration files from the image, emits no database setting,
   and has an approved `/api/health` readiness configuration. Confirm the Docker
   command has no provider override. This safe image, not `8780324`, becomes the
   only acceptable post-rotation rollback target.

4. **Rotate the database credential in a tight, owner-run sequence.** First
   prepare the replacement in Railway using the provider's private workflow,
   without testing or copying the exposed value. Once the safe institutional image
   is live and its startup behaviour is verified from redacted provider logs,
   rotate according to the provider's semantics, securely update the institutional
   Render secret, and perform a normal deployment of that safe image (not a
   restart). Verify readiness and redacted logs, then revoke the old credential if
   the provider did not revoke it atomically. If Railway can only rotate
   immediately, pre-stage the safe image and execute the credential update and
   safe-image deployment as one approved, monitored change with a planned limited
   outage. Do not use the former credential as a verification probe.

5. **Review provider evidence without exporting secrets.** The Railway owner
   reviews credential/authentication and relevant access logs from the exposure
   period through revocation. The Render owners review build and runtime logs for
   both services over the window, including any database-setting disclosure or
   unexpected migration execution. Record the review source, time range, operator,
   retention location and outcome as `no evidence`, `suspicious`, or
   `inconclusive`; a suspicious or inconclusive result extends containment rather
   than closing it.

6. **Make a private signing-key and session decision.** The application-security
   owner compares deployed signing-key material with historical candidates through
   an approved private channel only. If reuse is found—or cannot be ruled out—the
   owner must schedule key rotation and explicit JWT, cookie and server-session
   invalidation/forced reauthentication. Keep institutional and recruiter-demo
   keys independent. Review OAuth/SMTP candidates separately; rotate only a
   provider credential shown to have been reused.

7. **Clear schema and provisioning gates before any institutional rollout.** The
   database/schema owner must confirm through approved metadata/provisioning
   evidence that cycle/year linkage exists, `workload_summary` has the unique
   `(staff_id, academic_year, semester_type)` key, audit logging supports the
   required actions, workload snapshots are immutable, and the runtime role has
   only the expected permissions. Confirm a tested backup/restore path and that no
   startup migration, seed or cleanup step is needed; the repair commits add no
   schema migration. For the demo, separately confirm its synthetic marker,
   `fwms_demo` schema and restricted runtime role. Any mismatch is a stop: do not
   attempt to repair it through application startup.

8. **Use a staged rollout with safe rollback rules.** After the pre-push gates,
   manually deploy the reviewed target commit to the recruiter-demo service first
   and verify only synthetic authentication, RBAC and health behaviour. Roll back
   demo to its recorded compatible artifact if those gates fail, then re-check
   automatic-deployment state. Roll out institutional Render only after the safe
   launcher, schema gates, credential plan and session decision all pass. Monitor
   its application readiness and redacted logs. Because this window makes no
   schema change, code rollback does not require a database rollback; however,
   Render rollback does not reverse database or environment state. Never roll back
   to `8780324` after the replacement credential exists—it can disclose that
   credential and replay SQL. If the safe target fails post-rotation, keep a safe
   launcher in place and escalate to the institutional Render, Railway and release
   owners rather than returning to the unsafe artifact.

9. **Require written go/no-go gates before a Git push or deployment.** The release
   owner confirms: exact target commit and reviewed diff; clean tracked worktree;
   current upstream synchronization; no secret-bearing files; focused tests and
   Docker/Compose checks with recorded results; both auto-deploy controls held as
   intended; a safe institutional artifact and rollback artifact identified;
   schema/backup evidence accepted; credential, logging and session plans approved;
   no active deploy; and named operators available for monitoring and rollback.
   A push or a provider deployment without all applicable approvals is out of
   scope for this runbook.

## 21 October 2026 documentation and Git closeout

This snapshot supersedes the older checkpoint fields below while preserving the
complete security, isolation and deployment history.

| Item | Verified value |
|---|---|
| Repository | <https://github.com/Nithish-kumar-git/fwms-workload-system> |
| Authoritative local path | `C:\Users\itsni\.gemini\antigravity\scratch\faculty_selection` |
| Default branch | `main`; remote tip `878032465ed052de078b0715fd57049590a9d24c` |
| Active branch | `feature/recruiter-demo` |
| Local HEAD | `cb9f324ffd96f580062cc542c3e46c107e109630` |
| Tracked upstream | `origin/feature/recruiter-demo` at `15fdeb3f42a86e662609c9aa960df87599af3ebf` |
| Synchronization | Local branch is two commits ahead, zero behind |
| Working tree at closeout start | Tracked tree clean; the pre-existing untracked files listed in historical section 3 were present and must be preserved |

The two unpublished repair commits are retained intact:

- `f6b61d3e9ae314e20ec941fb709d8fab8dfddb2b` — administrative containment and atomic allocation repair.
- `cb9f324ffd96f580062cc542c3e46c107e109630` — shared workload concurrency and programme finalization repair.

Do **not** push this branch. Render confirms `fwms-workload-system-1` tracks it
with automatic deployment on every commit. Its current live deploy is still
`15fdeb3`; therefore neither repair commit is deployed. The institutional Render
service and Vercel frontend remain at `main` commit `8780324`. Platform metadata
reports both Render deploys as live, but bounded HTTP probes during this closeout
did not return before timeout; current browser/API health is therefore not freshly
verified.

Latest repair evidence, not rerun for this documentation edit: 24 focused offline
security/allocation/startup tests, 12 demo launcher/deployment tests and 10 tests
against a disposable loopback PostgreSQL 18.1 cluster passed. This establishes the
reported PostgreSQL repair checks. Docker's engine was unavailable, and full
Compose plus hosted browser/permission workflows remain unverified.

Environment-variable names only: institutional `DATABASE_URL`, `FRONTEND_URL`,
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `SECRET_KEY`,
`REDIS_URL`, `VITE_API_URL`, `VITE_DEV_MODE`; recruiter demo
`FWMS_DEMO_MODE`, `FWMS_DEMO_DATABASE_URL`, `FWMS_DEMO_SECRET_KEY`,
`FWMS_DEMO_FRONTEND_URL`, `VITE_FWMS_DEMO_MODE`, `VITE_API_URL`,
`VITE_DEV_MODE` and host-supplied `PORT`. Never publish values.

Safe focused commands are documented below and in `docs/SECURITY_CONTAINMENT.md`.
The exact next action is an externally reviewed, explicitly approved rollout plan:
confirm credential containment and deployed schema, stop/drain old writers, verify
Docker/Compose and hosted browser/RBAC paths, then decide whether to disable
automatic deploy before pushing. Credential rotation, provider-log review, database
access, Render/Vercel settings, pushes, deployments and any history rewrite require
explicit approval. The project remains **needs code/security rollout work** and
must not be frozen as production-ready.

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

**FWMS** (Faculty Workload Management System) implements a subject-preference and
workload-allocation workflow for teaching faculty, coordinated by a timetable
coordinator (TT Coordinator) and the Head of Department (HOD). Repository and
hosting evidence do not by themselves establish institutional adoption or
production readiness.

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

## 3. Repository and Git State — historical checkpoint

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
  demo/test_demo_destination.mjs \
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
| HOD demo login | `POST /api/auth/demo-login?role=hod` | `200 + JWT` | **STALE** — the currently observed Vercel build targets the institutional backend; see the 2026-10-23 incident note below. |
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
- **Vercel Preview SHA UNVERIFIED:** The current public bundle was found to target
  the institutional backend, so it must not be presumed to represent the documented
  synthetic-demo build.

### 2026-10-23 — Demo-login routing incident

Read-only public checks confirmed that the observed Vercel frontend bundle embeds
`https://fwms-workload-system.onrender.com`. Its `/api/health` response does **not**
identify itself as `synthetic-demo`. The documented dedicated demo backend,
`https://fwms-workload-system-1.onrender.com`, does identify itself as
`synthetic-demo`; both expose the demo-login route in OpenAPI.

The observed HTTP 500 therefore comes from sending a synthetic demo request to the
institutional backend, not from a bad frontend route path. No production login POST
was replayed during diagnosis, because it can create a session or audit record.
Render logs and the exact exception remain owner-only evidence; current local source
would reject a non-demo request safely rather than expose an internal error.

The frontend now disables the demo action in an institutional build without a valid,
dedicated HTTPS demo destination. This prevents the incorrect backend fallback but
does not make the hosted demo available. An owner must set the intended Vercel build
variables or publish the separately configured demo build, then verify the resulting
bundle and Render deployment before release.

Local verification on 2026-10-23: the 12-test deployment safety suite and 9 Node
frontend configuration/regression tests passed, and the frontend production build
completed. `npm run lint` remains failing on pre-existing codebase-wide findings
(57 errors, 19 warnings); the demo-routing change adds none.

---

## 13. Outstanding Deployment or Configuration Checks

| Item | Status |
|------|--------|
| Verify exact Render deployed commit SHA | UNVERIFIED — requires dashboard login |
| Verify exact Vercel Preview deployed commit SHA | UNVERIFIED — requires dashboard login |
| Verify `FWMS_DEMO_FRONTEND_URL` on Render matches active Vercel Preview URL | REQUIRES OWNER VERIFICATION — the current public bundle targets the institutional backend |
| Confirm Vercel Preview not promoted to Production | Not promoted; institutional Production is unmodified |
| Add demo link to README | Pending operator decision — not done |
| Correct the live frontend's demo build configuration | REQUIRED — current bundle targets the institutional backend, not the documented synthetic backend |

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
