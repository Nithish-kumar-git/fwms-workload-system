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

### 22 October 2026 credential-evidence correction

After an authorized remote fetch, `origin/main` remained at `8780324` and
`origin/feature/recruiter-demo` at `15fdeb3`. A redacted structural recheck corrects
the table above: `origin/main:.env.example` contains explicit signing/OAuth
placeholders and a local/Compose database credential literal, not evidence of a
remote signing or Google credential. `origin/main:verify_dev_auth.py` contains
local/test literals; production signing-key reuse remains unknown. The embedded
Railway PostgreSQL credential candidate in `origin/main:run_migrations.bat` and
public history remains the confirmed remote containment concern. Current feature
HEAD removes that value, but neither the remote branch nor public history is
remediated. No value is recorded in this document.

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

## Allocation and production Compose follow-up (2026-10-21)

This bounded follow-up starts at local commit
`f6b61d3e9ae314e20ec941fb709d8fab8dfddb2b`. The 19-file manifest above describes
that original commit; the separate 12-file manifest below describes this follow-up.
The original credential assessment and authorization policy remain unchanged.

### Shared summary transaction contract

`workload_summary` is shared by `(staff_id, academic_year, semester_type)`, not
by semester or cycle. Both writer paths were traced: allocation replacement and
administrative override/reassignment. Readers are the administrative summary,
report/export services and persisted workload snapshots. The administrative
reader now uses the actual parity key, and override/reassignment refresh totals
across the whole year/parity bucket, including retained frozen allocations.
Reassignment also resolves the year through `academic_year_id`, matching the
current cycle schema.

`app/db/workload.py` acquires database-local transaction advisory lock
`(1179995475, 1)` before any application reads, row locks or writes. Single and
batch allocations, both administrative writers, snapshot approval and the
cycle/semester/window lifecycle paths that can invalidate their state use the
same entry point. A whole batch acquires the lock once. Consistent lock-first
ordering prevents competing participating paths from holding row locks while
waiting for each other's workload lock. Existing READ COMMITTED transactions and
five-second lock timeout remain; exceptions roll back allocations, summaries,
statuses and audit rows together. PostgreSQL releases the advisory lock on commit
or rollback. Independent reports read committed data without taking this lock;
approval takes it before constructing a persisted snapshot.

This intentionally serializes infrequent workload operations even across
different year/parity buckets. It trades parallel throughput for a small,
reviewable locking contract. All serving instances must run this version before
the guarantee applies; old instances or direct SQL writers do not cooperate with
advisory locks. Stop/drain old writers for an approved rollout. Reopening retains
its existing behavior of clearing allocations and refreshing summaries on the
next allocation. Window open/close no longer changes a FROZEN semester's state.

See PostgreSQL's [advisory lock documentation](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS).

### Programme completion and serving

A filtered run for a semester containing other active programmes keeps the
semester's existing OPEN/CLOSED state and cycle OPEN. Programme A then programme B
can both run without discarding each other's allocations. An explicit full-semester
run (or run-all) finalizes the cycle; it recalculates the semester using the
existing allocation rules. A filtered run covering the only active programme
still finalizes normally. No implicit progress table or inference from allocation
counts is introduced. Pipeline completion and HOD approval require finalized
allocation status, so a partial result cannot be approved as a complete workload.

Production Compose now runs `sh startup.sh`, which executes only the guarded
institutional launcher. It uses one Uvicorn process, matching that launcher,
instead of the previous direct two-worker override. Ordinary access logs remain
disabled; the health probe uses the configured PORT/default 8000 and `/api/health`.
Serving never replays SQL. Dedicated demo Docker/native startup, its restricted
database role/marker, demo signing boundary and Google prohibition remain intact.

### Verification and rollout prerequisites

Executed with existing dependencies; no packages installed:

- 24 focused offline security/allocation/startup tests passed, including programme
  sequencing, single-programme finalization and production Compose assertions.
  SQLite is used only for offline persistence checks, never as concurrency proof.
- 12 existing demo launcher/deployment tests passed, rerun because the guarded
  production launch path and imported services changed.
- 10 tests passed on PostgreSQL 18.1 in a newly created, loopback-only disposable
  cluster. Actual demo schema/fixtures were applied only there; application
  transactions used restricted `fwms_demo_test_app`, not the schema owner.
  Checks covered different semesters sharing a bucket plus frozen contributions;
  same-semester serialization/revalidation; A then B then explicit full
  finalization; a real database constraint failure rolling back an entire batch;
  both orderings of allocation racing with HOD approval; real lock timeout and
  subsequent recovery; administrative summary refresh/reader; frozen-semester
  preservation on window close; and real native institutional/demo startup,
  shallow/deep health, both configured probes and absence of the synthetic query
  canary/credentials in logs. Competing transactions were observed waiting in
  `pg_locks`. No existing PostgreSQL server, Neon or production data was accessed.
- Docker's engine pipe was unavailable. Container builds and full production
  Compose (including Redis/Nginx) remain unverified. Native probes do not establish
  container networking, hosted browser behavior or provider readiness.
- Python syntax, Compose YAML, guarded shell syntax and whitespace checks passed.
  Previously recorded demo suites above were not rerun without a relevant change.

Reproduce real PostgreSQL checks with existing local binaries and dependencies:
`python -B tests/verify_allocation_postgres.py -v`. The script creates and stops
only its own disposable cluster. `FWMS_PG_BIN` may select an existing Windows
PostgreSQL binary directory. It refuses existing database/provider configuration.

No new application schema migration is introduced. Rollout still requires the
previously reviewed institutional schema/provisioning, including the year FK on
cycle, unique year/parity workload key, audit and immutable snapshot support.
Confirm actual deployed schema privately; removed startup replay cannot provision
an empty database. The demo needs its separately initialized synthetic schema,
marker, fixtures and exact runtime role `fwms_demo_runtime`; neither an owner role
nor institutional credentials are compatible. This task did not initialize Neon.
Critical-path external review, Docker/hosted checks and credential-containment
approval remain deployment prerequisites.

With the user's permission, Render configuration was inspected read-only on
2026-10-21. `fwms-workload-system-1` tracks `feature/recruiter-demo`, uses
`demo/Dockerfile`, and has automatic commit deployment **enabled**. Its provider
health-check path is blank. `fwms-workload-system` tracks `main` and also has
automatic commit deployment enabled. These settings do not prove either service
is healthy. A feature-branch push is therefore **not review-only**; do not push
until the user separately approves disabling automatic deployment or an actual
rollout. Any provider health-check change to `/api/health` also needs approval.
No settings were changed. See [Render deployment controls](https://render.com/docs/deploys).

Follow-up manifest (pre-existing untracked files are excluded and preserved):

```text
app/admin/cycle_service_new.py
app/admin/service.py
app/allocation/router.py
app/allocation/service.py
app/coordinator/semester_state_service.py
app/coordinator/window_transactions.py
app/db/workload.py
app/reports/snapshot_service.py
docker-compose.prod.yml
docs/SECURITY_CONTAINMENT.md
tests/verify_allocation_postgres.py
tests/verify_security_repairs.py
```
