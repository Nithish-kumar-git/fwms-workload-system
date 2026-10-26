# FWMS Recruiter Demo

## Purpose and boundaries

The public recruiter demo is available at
[https://fwms-recruiter-demo.vercel.app/](https://fwms-recruiter-demo.vercel.app/).
Its source repository is
[Nithish-kumar-git/fwms-workload-system](https://github.com/Nithish-kumar-git/fwms-workload-system).

It is an isolated, synthetic-data environment for reviewing FWMS workflows. It
must not be treated as an institutional deployment, connected to institutional
data, or used as evidence of institutional adoption or production readiness.
The institutional application remains separately available at
[https://fwms-workload-system.vercel.app](https://fwms-workload-system.vercel.app).

## Public endpoints and current release

- Recruiter-demo frontend:
  [fwms-recruiter-demo.vercel.app](https://fwms-recruiter-demo.vercel.app/)
- Dedicated synthetic-demo backend health:
  [fwms-workload-system-1.onrender.com/api/health](https://fwms-workload-system-1.onrender.com/api/health)
- Source repository:
  [Nithish-kumar-git/fwms-workload-system](https://github.com/Nithish-kumar-git/fwms-workload-system)

The dedicated backend is currently deployed from
[`dcd403e`](https://github.com/Nithish-kumar-git/fwms-workload-system/commit/dcd403e5607a31b31ba6f8255d3d7eb12319395c)
as Render deployment `dep-dbfn06dg1s2s73ajd4tg`. Read-only release checks
confirmed `/api/health` reports `environment: synthetic-demo` and
`/api/health/deep` reports a healthy database. `/docs`, `/redoc`, and
`/openapi.json` return 404 in this public demo deployment.

The associated startup-resilience change retries only a bounded set of
transient PostgreSQL connection-reset failures during the first connection
attempt. It does not retry authentication, database/role, marker, privilege,
or other isolation failures. Every recovered connection still passes the same
database identity, restricted-runtime-role, privilege, synthetic-marker, and
search-path checkout validation before the application can use it.

## Verified workflow and release evidence

The published demo uses a role-selected synthetic sign-in workflow; no
institutional account is required. A verified HOD demo sign-in reached the
authenticated dashboard, and the subsequent authenticated `/api/auth/me`
request succeeded. Demo credentials are intentionally not recorded here.

The dedicated Vercel deployment
`dpl_13vANc2VC38pVsvUh2A1Zgze82dR` was verified as `READY` on 2026-10-23
from the reviewed static frontend artifact associated with local source commit
`3f50c7a40ce9ccb26939dbcd7b5f1b2dec7cf97b`. The release evidence included:

- 12 of 12 offline deployment-safety tests passing.
- 36 of 36 focused frontend/deployment regression tests passing.
- A production frontend build with zero TypeScript diagnostics.
- An emitted-artifact and live-bundle check confirming the dedicated synthetic
  backend origin and excluding the institutional backend origin.
- A responsive 390 px browser check with no horizontal overflow after sign-in.

The recruiter demo is hosted separately from the institutional Vercel project
and communicates only with the dedicated synthetic-demo backend. The
institutional Vercel and Render deployments were not changed by that release.

## Known limitations and follow-up

The database contains a synthetic-only marker and its checked-in fixtures define
the intended synthetic records. Aggregate verification also matched the expected
synthetic email domains and employee-code prefixes. The schema does **not** have
a reliable per-row provenance field, however, so these checks cannot prove the
origin of every historical row. No live records were reseeded, deleted, or
changed to make that claim. A future provenance mechanism would need a separate,
backward-compatible rollout plan.

The release checks for `dcd403e` covered the three startup retry cases, 19 demo
configuration/isolation checks, six frontend/deployment-boundary checks, and a
backend syntax check. They do not represent a full application-suite, Docker,
or broad browser-regression run.

This documentation does not alter API routes, access control, CORS, credentials,
databases, deployments, or the institutional service.
