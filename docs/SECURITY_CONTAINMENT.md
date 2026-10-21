# FWMS containment and bounded repairs

Prepared on `feature/recruiter-demo`, starting at `15fdeb3`. No remote fetch,
deployment, provider change, credential rotation or database connection is part
of this change. Local `main` and cached `origin/main` both point to `8780324`;
these references do not establish the current remote or deployed state.

## Administrative serving policy

The existing application roles remain faculty, TT coordinator and HOD.
Normal curriculum, offering, cycle, window and allocation mutations retain
coordinator access (which includes HOD). Staff/role management, semester freeze
and workload approval retain HOD access. Staff diagnostics now require HOD.

The historical reports maintenance router is **not mounted** by `app.main` in
either institutional or demo mode. Its routes are absent from ordinary OpenAPI
and return 404, including to HOD. It also has a HOD dependency as defense in depth;
do not mount it as a substitute for a reviewed provisioning procedure.
The removed mutation paths under `/api/reports/admin/` are:

- `fix-duplicate-programs`
- `seed-mca-odd`
- `fix-shift2-offerings`
- `fix-shift-from-program`
- `create-shift2-offerings` (both historical registrations)
- `create-secb-offerings`

The associated one-off report diagnostics are unmounted too. Normal reports,
exports and HOD approval remain served. The recruiter demo's restricted database,
signing-key/issuer boundary, synthetic login and Google prohibition are preserved.

## Allocation transaction and scope

Empty requests fail before allocation opens a transaction. Semester, year, OPEN
cycle, program, offerings and preferences are validated before any cleanup.
Cycle and semester rows are locked in the same transaction used for calculation,
replacement, workload updates, audit and status changes. Existing service state
guards remain: an ALLOCATED semester must be reopened before another run, and a
FROZEN semester cannot be allocated. There is no global reset to bypass them.

Replacement is restricted to the selected cycle, semester and optional program;
other programs retain their allocations and their capacity/course constraints.
Preference order and progressive fallback passes are unchanged. Preferences from
another cycle are excluded. Because the existing workload summary key is
`(staff, academic_year, ODD/EVEN)`, its shared bucket is recomputed from all matching
persisted allocations, retaining other semesters' contributions. Other years and
parities are not rewritten. Only the selected semester/cycle statuses change.

`run-all` validates every selected OPEN cycle before writing, then commits once.
A failure in any semester, summary, audit, status update or commit rolls back the
whole request. It no longer returns success after a partially failed batch.

## Serving and explicit provisioning

Institutional serving from the repository root:

```text
sh startup.sh
```

Native Python equivalent:

```text
python -B -m app.start_backend
```

The launcher binds `0.0.0.0` to `PORT` (default 8000), rejects demo mode, sanitizes
startup failures and redacts credentials from formatted server/application logs.
Ordinary startup, Docker and development Compose no longer replay SQL.
Production Compose also no longer mounts SQL into automatic database initialization. The runtime
image no longer copies migrations. The institutional health path is `/api/health`.
Keep institutional database, signing and Google variables configured privately:
`DATABASE_URL`, `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`,
`GOOGLE_REDIRECT_URI`, and the appropriate frontend origin (`FRONTEND_URL`).
Keep `DEV_AUTH_BYPASS=false` for publication. No secret values belong in commands,
documentation or frontend `VITE_*` settings.

The separate demo continues to use `python -B demo/start_backend.py` with only its
dedicated demo variables; see `demo/README.md`. Do not use institutional migrations
or credentials for demo initialization.

Initial institutional provisioning is a separate owner-operated maintenance
operation, never part of serving:

1. Confirm the approved target host/database/owner privately. For initial setup,
   verify the database is new and empty, with no concurrent application or schema
   writers. Refuse either demo database and any unconfirmed target. For an existing
   installation, take a verified backup and use a separately reviewed migration
   procedure instead of initial provisioning.
2. Review the exact SQL file and its prerequisites against that target. Do not
   replay the legacy seed/cleanup list or infer ordering from filenames. The old
   `run_migrations.bat` and `make migrate` now refuse automatic replay; its stale filenames and
   embedded connection credential are removed.
3. Run **one explicitly reviewed file** using non-secret target parameters and
   an interactive password prompt, stop on the first failure, and verify the result
   before selecting another file. Example structure (substitute only non-secret
   parameters and the reviewed file path):

   ```text
   psql --host=APPROVED_HOST --username=APPROVED_OWNER --dbname=APPROVED_DATABASE --password --no-psqlrc --set=ON_ERROR_STOP=on --single-transaction --file=REVIEWED_FILE.sql
   ```

No SQL was executed to prepare this repair. Existing untracked migration helpers
were preserved; they have not been certified or incorporated into startup.

## Redacted credential assessment

Scope: tracked files at local `main`/cached `origin/main`, the development branch,
and the specifically named local configuration/helper files. No credentials were
tested against providers, so none should be assumed inactive.

| File | Main (`8780324`) | Development branch before this repair | Containment |
|---|---|---|---|
| `.env.example` | Literal signing-key candidate and password-bearing database URL; Google values appear template-like | Placeholder-only template | Publish reviewed cleanup; assess and rotate exposed real credentials privately |
| `verify_dev_auth.py` | Literal signing-key candidate and local/test database credentials; Google values appear test-like | Untracked/ignored local copy; removed from tracked branch by `cd3b220` | Preserve local file; determine whether signing material was reused and rotate if exposed |
| `run_migrations.bat` | Embedded remote database credential | Same embedded credential | Removed from this branch tip by this repair; rotate/revoke privately and address main |
| Local `.env`, `.env.local`, `.env.production`, frontend environment files | Untracked/ignored locally; no contents published here | Preserved | Keep private; review copies when rotating |

Development Compose/test files also contain explicit local synthetic database
credentials; these are not evidence of a remote secret, and must not be reused in
hosted services. Feature-branch removal does not erase public main or Git history.
Rotation/revocation, session invalidation, provider log review, changes to main,
and any eventual history rewrite require a separately authorized follow-up. Review
past deployment logs because the old startup script printed the database URL.

## Focused verification

Using the existing isolated dependencies, run these independently; do not invoke
the legacy database test/migration scripts:

```text
python -B tests/verify_security_repairs.py -v
python -B demo/verify_offline.py -v
python -B demo/test_deployment.py -v
python -B -m unittest discover -s tests -p test_demo_isolation.py -v
```

The new suite exercises actual FastAPI dependency resolution, JWTs, ranking,
in-memory SQLite persistence and rollback, including every served administrative
mutation's rejection behavior and all unmounted maintenance routes. It explicitly
adapts PostgreSQL row-lock and timestamp syntax for SQLite; this is **not** evidence
of PostgreSQL locking, hosted database behavior or institutional data verification.
No frontend source changes are required. PostgreSQL integration, Docker execution,
hosted OpenAPI/permission checks and browser workflows remain release checks.

Recorded for this repair on 2026-10-21 with existing Python 3.12 dependencies:

- 22 focused security/allocation/startup regressions passed.
- 38 existing offline demo regressions passed, including 18 auth/demo pytest cases.
- 12 existing deployment/launcher regressions passed.
- The isolation unittest wrapper passed (it reruns the offline demo suite).
- Edited Python syntax, both Compose YAML files, `bash -n startup.sh`, and
  `git diff --check` passed. No frontend source was changed, so no frontend build
  was required for this repair.
- Existing dependency deprecation/resource warnings remain. Windows asyncio and
  Git Bash needed execution outside the sandbox to initialize OS loopback/MSYS
  facilities; database, external-network and secret-file blockers remained enabled
  in the offline application tests.

Before deployment, obtain the external review required by the repository's FCFS
comments for any affected critical path, verify the isolated PostgreSQL workflows,
and approve rollout/credential containment separately. No push or deploy is part
of this repair.

## Served administrative mutation inventory

The regression suite checks all 37 routes below for unauthenticated and
faculty rejection; HOD-only routes also reject coordinators.

| Method | Path | Required role |
|---|---|---|
| POST | `/api/coordinator/override` | Coordinator or HOD |
| POST | `/api/windows` | Coordinator or HOD |
| POST | `/api/windows/{window_id}/schedule` | Coordinator or HOD |
| POST | `/api/windows/{window_id}/open` | Coordinator or HOD |
| POST | `/api/windows/{window_id}/close` | Coordinator or HOD |
| POST | `/api/windows/{window_id}/archive` | Coordinator or HOD |
| POST | `/api/semester/{semester_id}/open` | Coordinator or HOD |
| POST | `/api/semester/{semester_id}/close` | Coordinator or HOD |
| POST | `/api/semester/{semester_id}/freeze` | HOD |
| POST | `/api/pref-window/open` | Coordinator or HOD |
| POST | `/api/pref-window/close` | Coordinator or HOD |
| POST | `/api/pref-window/open-group` | Coordinator or HOD |
| POST | `/api/allocation/run` | Coordinator or HOD |
| POST | `/api/allocation/run-all` | Coordinator or HOD |
| PUT | `/api/admin/allocation/{allocation_id}` | Coordinator or HOD |
| POST | `/api/admin/reassign` | Coordinator or HOD |
| POST | `/api/admin/allocation/freeze` | Coordinator or HOD |
| POST | `/api/admin/allocation/unfreeze` | Coordinator or HOD |
| POST | `/api/cycles` | Coordinator or HOD |
| POST | `/api/cycles/activate` | Coordinator or HOD |
| POST | `/api/cycles/archive/{cycle_id}` | Coordinator or HOD |
| POST | `/api/cycles/new-semester` | Coordinator or HOD |
| POST | `/api/cycles/activate-group` | Coordinator or HOD |
| POST | `/api/admin/staff` | HOD |
| PUT | `/api/admin/staff/{staff_id}` | HOD |
| PATCH | `/api/admin/staff/{staff_id}/deactivate` | HOD |
| PATCH | `/api/admin/staff/{staff_id}/email` | HOD |
| PATCH | `/api/admin/staff/{staff_id}/role` | HOD |
| POST | `/api/subjects/offerings` | Coordinator or HOD |
| DELETE | `/api/subjects/offerings/{offering_id}` | Coordinator or HOD |
| POST | `/api/subjects/sections` | Coordinator or HOD |
| POST | `/api/subjects/programs` | Coordinator or HOD |
| DELETE | `/api/subjects/sections/{section_id}` | Coordinator or HOD |
| DELETE | `/api/subjects/programs/{program_id}` | Coordinator or HOD |
| POST | `/api/curriculum/parse` | Coordinator or HOD |
| POST | `/api/curriculum/confirm` | Coordinator or HOD |
| POST | `/api/reports/approve-workload` | HOD |

## Changed-file manifest

Only these files belong to the containment commit. Pre-existing untracked files
are excluded and preserved.

```text
Dockerfile
Makefile
README.md
app/admin/router.py
app/allocation/router.py
app/allocation/service.py
app/core/log_redaction.py
app/core/logging_config.py
app/reports/router.py
app/start_backend.py
demo/DEPLOYMENT.md
demo/README.md
docker-compose.prod.yml
docker-compose.yml
docs/DOCKER.md
docs/SECURITY_CONTAINMENT.md
run_migrations.bat
startup.sh
tests/verify_security_repairs.py
```
