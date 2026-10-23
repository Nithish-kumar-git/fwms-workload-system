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

As of the recorded release checks, the dedicated synthetic-demo backend exposed
`/docs` and `/openapi.json` publicly without authentication. This is recorded
for owner follow-up; this documentation-only change does not alter API routes,
access control, CORS, credentials, databases, or deployment configuration.
