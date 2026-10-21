# Dedicated synthetic FWMS demo (local implementation, not deployed)

## Boundary and current evidence

Use a **new PostgreSQL instance**, separate backend service and separate frontend
origin. Do not clone, dump or restore the institutional database into it. Never
give the demo backend institutional database credentials. Demo HOD privileges
are meaningful only inside this synthetic database; existing server role guards
remain in use. Demo tokens have a separate signing key and required issuer/audience
and are rejected by the updated institutional backend, even if keys are accidentally
equal. Google login remains unchanged in the institutional environment and is
disabled in the demo. Public demo login on the institutional backend returns 403
before any database operation.

The observed production exception was a `staff_pkey` unique violation during an
INSERT that omitted `id`. The checked-in schema defines `staff.id BIGSERIAL`.
Explicit-ID seed files exist historically, but their deployment/execution and
the actual database default, sequence ownership/value, and triggers are unverified.
No production sequence repair is included. A fresh demo schema uses generated
staff IDs exclusively. Concurrent account creation uses `ON CONFLICT (email)`;
signing and account insertion share one transaction, with rollback on failure.

Every demo pool checkout verifies database name, exact application role, absence
of elevated privileges (including replication), inheritance, role memberships
and object ownership, an owner-managed synthetic marker, and lack of schema/marker
write permissions. Startup must pass this gate. Unknown catalog flags fail closed. Marker
checks are a misconfiguration guard, not proof against an operator who deliberately
imports real data. The new-instance and no-production-credentials requirements are
mandatory. Public visitors share mutable synthetic accounts/data; this is not
per-visitor tenant isolation. Do not upload real faculty documents or data.

## Configuration (names only; configure values privately)

Backend:

- `FWMS_DEMO_MODE`: explicitly true on the separate demo service, false/absent
  on the institutional service. It is read from the process environment, not .env.
- `FWMS_DEMO_DATABASE_URL`: dedicated database `fwms_demo`, login role
  `fwms_demo_runtime`; local tests must instead use `fwms_demo_test` and
  `fwms_demo_test_app`. PostgreSQL URL required. Never reuse production credentials.
- `FWMS_DEMO_SECRET_KEY`: independently generated secret, at least 32 characters.
- `FWMS_DEMO_FRONTEND_URL`: exact separate frontend origin; HTTPS except localhost.

Demo mode ignores normal `DATABASE_URL`, `SECRET_KEY`, Google credentials and
Redis settings; it never reads .env or falls back to normal database configuration.
No Google/Redis credentials are needed. Existing institutional configuration is
unchanged. Use the platform secret manager; never paste secrets into chat or logs.

Frontend builds:

- Dedicated demo: `VITE_FWMS_DEMO_MODE=true`, `VITE_API_URL` set to the dedicated
  backend origin (without /api). Missing API URL is a fatal configuration error.
  Its login health check also requires the backend's synthetic-demo marker.
- Institutional frontend: leave demo mode false/absent; optionally set
  `VITE_FWMS_DEMO_URL` to the separate HTTPS demo login URL. Its Try Demo button
  then navigates to that origin; institutional Google sign-in stays unchanged.
- Keep `VITE_DEV_MODE` false/absent on both published builds.

## Manual setup — requires infrastructure approval first

1. Approve the provider/cost and provision a new, empty PostgreSQL instance.
   There must be no institutional database on that instance. A local development
   instance is suitable for initial verification; Docker Desktop must be running
   if it supplies PostgreSQL. No infrastructure was provisioned by this change.
2. As its administrator, create database `fwms_demo` and a separate SQL-created role
   `fwms_demo_runtime`, initially NOLOGIN, with NOSUPERUSER, NOCREATEDB,
   NOCREATEROLE, NOINHERIT, NOREPLICATION and NOBYPASSRLS, with no memberships
   granted to it. Activate LOGIN only after verifying the role and grants and
   establishing its password privately through a provider-supported secure flow.
   Never put passwords in chat, shell arguments, committed SQL or logs. On Neon,
   do not create the runtime role through Console/API/CLI: these grant
   neon_superuser membership. The administrator, **not** the app
   role, must own the database, schemas, tables and functions. Do not use an
   owner/superuser connection string for the running application.
3. Review `demo/schema.sql`, then apply it as owner only to that empty database.
   It refuses non-demo names and non-empty databases. Then review/apply
   `demo/fixtures.sql` once as owner. Neither artifact has been executed here.
   They contain only synthetic faculty, computing department/program, subjects,
   cycles, preference/allocation and workload data. Login accounts are created
   on demand with generated IDs. No legacy migration/seed chain is involved.
   Example command structure, using non-secret host/user/database parameters and
   an interactive password prompt (substitute only the approved demo host):

   ```text
   psql --host=DEMO_HOST --username=DEMO_OWNER --dbname=fwms_demo --password --set=ON_ERROR_STOP=on --file=demo/schema.sql
   psql --host=DEMO_HOST --username=DEMO_OWNER --dbname=fwms_demo --password --set=ON_ERROR_STOP=on --file=demo/fixtures.sql
   ```

4. Configure the separate backend with the demo variables above. Install the
   existing `requirements.txt` in its environment. Start it directly:

   ```text
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
   ```

   For a separately approved Render **native Python** service, use the same entry
   point with host 0.0.0.0 and the platform PORT. **Do not use the existing Docker
   default or startup.sh:** the institutional launcher now refuses demo mode.
   Its former SQL replay and URL logging were removed in the containment repair;
   see `docs/SECURITY_CONTAINMENT.md`. Keep using the dedicated demo launcher.

5. Configure/build the separate frontend and verify locally before any deployment.
   Use a separate output directory and demo API origin. Set the frontend marker
   only on the demo build. Existing production build settings were not changed.
   Only after PostgreSQL and three-role workflow verification should any deployment
   be approved. The institutional backend's public-demo rejection and cross-token
   protection must be published before linking the public demo from production.

## Neon restricted-role provisioning (NOT EXECUTED; separate approval required)

For the existing empty `fwms-synthetic-demo` project only, select branch
`production`, database `fwms_demo`, and administrator `neondb_owner` in the
Neon SQL Editor. The branch label is not the institutional `fwms-production`
project. Do not connect to that project. Confirm the selected administrator has
CREATEROLE and the new role name is unused before approving this statement:

```sql
CREATE ROLE fwms_demo_runtime
    NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
    NOINHERIT NOREPLICATION NOBYPASSRLS;
```

Leave the existing privileged `fwms_demo_app` unchanged and unused by the demo
runtime. No deletion, membership repair or shared Neon role changes are required.
If SQL creation is denied, stop for Neon permission/support assistance.

Before initialization, verify the new role's elevated attributes and INHERIT are
false, no `pg_auth_members` row has the runtime role as **member**, and no
`pg_shdepend` ownership dependency (`deptype = 'o'`) references it. A grant of the
new role **to its creator** is the reverse direction and does not grant the
runtime role an administrative membership. Keep the runtime role an object owner
of nothing; ordinary ACL grants are not ownership.

After separate approval, apply schema and fixtures as owner with `search_path`
explicitly set to `public`, only to the verified empty demo database. Verify
CONNECT, schema USAGE, marker SELECT, application-table CRUD and sequence
USAGE/SELECT; schema CREATE and marker write privileges must be absent. Then set
credentials privately and activate LOGIN using `ALTER ROLE fwms_demo_runtime LOGIN`.
Configure only `FWMS_DEMO_DATABASE_URL` with that runtime identity. The guard
does not accept the old hosted role, swapped database/role pairs, or an owner login.
No hosted role creation, password setup, schema application or database verification
is claimed by the local tests. Local `fwms_demo_test` / `fwms_demo_test_app` is unchanged.

References: https://neon.com/docs/manage/roles and
https://www.postgresql.org/docs/18/catalog-pg-shdepend.html.

## Verification

Offline targeted suite (no .env access, external calls or PostgreSQL connections):

```text
python -B demo/verify_offline.py -v
python -B -m unittest discover -s tests -p test_demo_isolation.py -v
node --experimental-vm-modules --test demo/test_frontend_config.mjs
node demo/verify_frontend.mjs
```

This exercises real FastAPI handlers, PyJWT and SQLAlchemy with in-memory SQLite;
the Google client and PostgreSQL metadata are mocked. Existing demo/auth pytest
files are also run against the isolated database adapter. It is NOT the full
pytest suite, a live Google test, a PostgreSQL sequence test, or a browser test.

Actual PostgreSQL integration is intentionally opt-in. Prepare a second **local**
empty database `fwms_demo_test` with role `fwms_demo_test_app` using steps 2–3.
Configure the demo variables to that localhost database, then explicitly set
`FWMS_DEMO_PG_TEST=true` and run:

```text
python -B demo/verify_postgres.py -v
```

The script refuses remote hosts and other database names/roles. It creates/reuses
synthetic accounts, verifies concurrent login, distinct generated IDs, existing
role guards, unauthenticated rejection and absence of institutional email domains.
It does not apply schema, repair sequences, delete fixtures, or call Google.
Do not run the old full database test suite with institutional credentials.

After that, test the actual demo browser: choose HOD, TT Coordinator and Teacher;
verify their separate dashboards, HOD staff list, coordinator allocation/window
actions, teacher preferences, and reports. Test permission denials, failed startup
with missing/wrong configuration, and that institutional API requests reject demo
tokens. No full workload/browser or production verification is claimed here.
The standalone demo schema is derived from checked-in query requirements but still
requires PostgreSQL/schema and end-to-end workflow verification before publishing.

## Changed-file manifest

Modified existing files (11):

- `app/core/config.py`
- `app/db/pool.py`
- `app/main.py`
- `app/health/router.py`
- `app/auth/router.py`
- `app/auth/jwt_utils.py`
- `app/auth/schemas.py`
- `frontend/src/api/client.ts`
- `frontend/src/context/AuthContext.tsx`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/App.tsx`

Added files (12):

- `app/demo/__init__.py`
- `app/demo/config.py`
- `app/demo/accounts.py`
- `app/demo/isolation.py`
- `demo/schema.sql`
- `demo/fixtures.sql`
- `demo/README.md`
- `demo/verify_offline.py`
- `demo/verify_postgres.py`
- `demo/test_frontend_config.mjs`
- `demo/verify_frontend.mjs`
- `tests/test_demo_isolation.py`

No existing untracked files, institutional seed/migration files, Google provider
implementation, role dependencies or database transaction manager were changed.

## Rollback and production collision investigation

Local verification on 2026-10-14 used Python 3.12 and the existing pinned backend
requirements installed into a temporary test directory (no requirements changes).
The initial system-Python run could not collect because email-validator was missing.
With the pinned test dependencies, 31 offline regressions and 18 existing
auth/demo pytest cases passed. Six frontend configuration tests passed; both
TypeScript configurations had zero diagnostics. A production-mode Vite build
passed using synthetic settings, envFile disabled and a fresh temporary output
directory; existing dist was not overwritten. Dependency deprecation/resource
warnings occurred. Docker's local engine was unavailable, so no PostgreSQL
integration script, schema SQL or fixture SQL was executed. No live Google calls,
production access, commits, pushes or deployments occurred.

No production changes were made. If a later approved demo deployment fails, remove
the institutional frontend's demo link and stop the separate demo service; leave the
institutional Google backend and database intact. Do not re-enable public HOD login
against institutional data, restore real records into demo, or auto-reset databases.
If the institutional primary-key issue needs investigation, a separately authorized
operator must inspect the actual staff ID default, sequence ownership/current state,
table maximum ID and triggers under controlled concurrent-write conditions. Do not
run setval or infer sequence drift solely from the unique violation.
