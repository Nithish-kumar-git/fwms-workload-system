# Separate synthetic demo deployment — prepared, NOT deployed

These files are opt-in. The root `vercel.json` remains institutional-only.
The later containment repair makes root serving SQL-free and rejects demo mode;
see `docs/SECURITY_CONTAINMENT.md`. Keep the dedicated demo entrypoint below.
Do not enable automatic deployment or run a deploy command until separately approved.

## Architecture and boundary

Use a separate frontend project/origin, separate backend service/origin and a
separate PostgreSQL instance containing only synthetic data. Never reuse an
institutional project, database, credentials or project link. The operator must
verify the chosen project IDs and origins; a config file cannot prove hosted isolation.
Public demo visitors share mutable synthetic accounts. This is not per-visitor isolation.

The root institutional config proxies `/api` to the institutional backend; the
demo config has no proxy and rewrites only declared client routes. `/api` paths
are not rewritten to HTML. The demo build requires an explicit backend origin,
rejects the known institutional origins, never loads `.env`, and embeds a CSP
whose `connect-src` allows only that origin. Unknown aliases still require operator
verification. Changes to declared client routes require updating/testing the demo rewrites.

## Frontend — separate Vercel project

Manual settings for a later review:

- Repository root as the working/root directory; Framework Preset: Other.
- Explicit configuration: `demo/vercel.json`, NOT the root `vercel.json`.
- Install command: `npm ci --prefix frontend`.
- Build command: `node demo/build_frontend.mjs`.
- Output directory: `frontend/dist-demo`.
- Node runtime must satisfy the installed Vite requirement: `^20.19.0 || >=22.12.0`.
  Local verification used Node 22.20.0; provider runtime availability was not inspected.
- Build variables: `VITE_FWMS_DEMO_MODE` enabled, `VITE_API_URL` equal to the
  verified dedicated backend origin without `/api`, and `VITE_DEV_MODE` disabled.
- Do not give the frontend database credentials, signing secrets, Google secrets,
  or other sensitive `VITE_*` variables.

Vercel CLI supports `--local-config demo/vercel.json`. This file is NOT automatically
selected by an ordinary Git deployment using the root config. Before any future
CLI deployment, explicitly select the separately approved demo project; do not
reuse `.vercel` metadata or the institutional project ID. No project was selected,
linked or created here. A Git-based deployment must first have an independently
reviewed configuration-selection workflow; dashboard selection is not assumed.

Reference: https://vercel.com/docs/cli/global-options#local-config

The build refuses existing output directories. Use a fresh hosted build workspace.
For safe local verification, use `--out-dir` with a new temporary directory, never
institutional `frontend/dist`. Do not deploy synthetic verification output.

## Backend — separate service

Supported opt-in start command, run from repository root:

```text
python -B demo/start_backend.py
```

For a later Render Docker service review:

- Dockerfile path: `demo/Dockerfile`; build context: repository root (`.`).
- Keep its default command; do not override it with `startup.sh`.
- Health-check path: `/api/health`.
- The image is non-root, copies only application code and the dedicated launcher/
  probe, and excludes migration/seed scripts and secret files. It has not been built
  or run in Docker during this configuration task.
- The launcher binds to the service-supplied `PORT`, validates demo configuration
  before importing the app, and strips ordinary institutional configuration from
  its process environment. Existing app startup then verifies every database
  connection's identity, restricted role and owner-managed synthetic marker.
- Demo log formatters redact configured database URLs/signing secrets, PostgreSQL
  URL patterns and Bearer/JWT tokens, including formatted exceptions/JSON extras.
  This does not excuse placing unrelated secrets in application messages/files.

Required runtime variable NAMES:

- `FWMS_DEMO_MODE`: explicitly enabled; missing/disabled is a startup failure.
- `FWMS_DEMO_DATABASE_URL`: independently provisioned `fwms_demo`, restricted
  SQL-created `fwms_demo_runtime` role. Do not reuse institutional credentials.
- `FWMS_DEMO_SECRET_KEY`: independently generated signing secret, minimum 32 characters.
- `FWMS_DEMO_FRONTEND_URL`: exact HTTPS origin of the separate demo frontend.
- `PORT`: supplied by the host, or the launcher's documented local default.

Do not set ordinary `DATABASE_URL`, `SECRET_KEY`, Google, Redis or bypass variables
on this service. They are not required. Keep admin/schema-owner credentials out of
the running service. Missing demo configuration never falls back to ordinary values.

Database provisioning/schema application is a separate, approval-gated operation.
See `demo/README.md` for owner-reviewed synthetic schema/fixture setup. No database,
schema, role, Docker resource or production setting was created/changed in this task.

For Neon `fwms-synthetic-demo`, keep the existing privileged `fwms_demo_app`
unchanged. Create the **new** `fwms_demo_runtime` using SQL, initially NOLOGIN;
Console/API/CLI role creation grants neon_superuser and is not the runtime path.
Verify no elevated attributes, inheritance, memberships granted to the runtime
role, or object ownership before owner-only schema/fixture initialization. Set
credentials privately and activate LOGIN only after grants/marker verification.
SQL creation requires the acting administrator's CREATEROLE authority; if denied,
stop for provider assistance. No provider-level deletion permission is needed.
Only the hosted pairing changes: `fwms_demo_test` / `fwms_demo_test_app` stays intact.
Local tests mock catalog results; the new hosted guard query remains unverified
against Neon until a separately approved database check. See the README's
restricted-role procedure for the exact proposed SQL and initialization safeguards.

## Verification and release gates

```text
python -B demo/test_deployment.py -v
node --experimental-vm-modules --test demo/test_deployment.mjs demo/test_frontend_config.mjs demo/test_preferences_retry.mjs demo/test_api_docs.mjs demo/test_allocation_filters.mjs
node demo/verify_frontend.mjs
git diff --check
```

Use existing isolated dependencies. Tests mock the server/health transport and
build into fresh temporary directories. No PostgreSQL or external provider call
is needed for these deployment checks. Earlier local PostgreSQL/browser results
are separate evidence, not hosted verification. The older README's historical
verification paragraph is not the current release report.

Before deployment approval: review these artifacts and the complete existing
uncommitted demo implementation; approve distinct provider projects/instance,
confirm domains and secrets privately, validate the Docker image/provider routing,
and repeat hosted login/role/Retry/Docs/filter checks after an approved deployment.
Never add the demo link to the institutional frontend until its updated demo-token
rejection/public-demo guards have been separately approved and verified.
