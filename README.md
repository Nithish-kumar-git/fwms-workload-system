# Faculty Workload Management System (FWMS)

> A role-based faculty subject selection platform built for a real college environment, implementing First-Come-First-Served (FCFS) fairness with race-safe database concurrency.

**Live:** [fwms-workload-system.vercel.app](https://fwms-workload-system.vercel.app)  
**Stack:** Python · FastAPI · PostgreSQL · TypeScript · React · Docker · Nginx  
**Auth:** Google OAuth 2.0 (institutional email only — `@hindustanuniv.ac.in`)

---

## What This System Does

University departments face a recurring problem every semester: multiple faculty members want the same subjects, and whoever gets there first should win — fairly, without the system crashing under simultaneous requests.

FWMS solves this with a timed selection window system where faculty submit subject preferences in real time. The system enforces strict FCFS ordering at the database level using PostgreSQL advisory locks, ensuring no two faculty can claim the same subject simultaneously, and no application-layer race conditions can corrupt the result.

---

## Roles & Actors

| Role | Access | Capabilities |
|---|---|---|
| **Faculty (Staff)** | Institutional Google account | View eligible subjects, select up to quota, change selection within window |
| **Coordinator** | Staff + `is_coordinator` flag in DB | Override any active selection, open/close selection windows, view full audit log |

Role is **checked from the database on every request** — never cached in JWT — to prevent privilege escalation from stale tokens.

---

## Core System Rules

These rules were defined during requirements analysis and enforced at the database layer:

### 1. Selection Window
- A coordinator opens a **selection window** with a defined time range and a per-staff subject quota (`max_subjects_per_staff`)
- Faculty can only select or change subjects while the window is open
- Reading subject lists is always allowed, even when the window is closed
- The UI displays "Window Closed — View Only" outside the window

### 2. Eligibility
- Faculty can only select subjects assigned to their batch and specialization
- Eligibility is enforced by a SQL JOIN on `staff_assignment` — no application-level check

### 3. FCFS Fairness (First-Come-First-Served)
- The database, not the application, is the sole arbiter of who gets a subject
- The `ON CONFLICT DO NOTHING` clause on `subject_selection` means only one INSERT succeeds per subject
- If two faculty simultaneously claim the same subject, exactly one gets it; the other receives a 409 response
- This is enforced using `pg_advisory_xact_lock(staff_id, window_id)` to serialize concurrent writes

### 4. Coordinator Override
- A coordinator can cancel any active selection at any time
- Override marks the record as `OVERRIDDEN` (audit preserved) rather than deleting it
- Faculty receive an email notification after override (sent post-commit via background task)

### 5. Audit Log
- Every selection, change, override, and window event is logged
- The audit log is **append-only** — no UPDATE or DELETE is permitted
- Coordinator-only read access

---

## System Architecture

```
┌────────────────────┐     HTTPS      ┌─────────────────────┐
│  React Frontend    │ ────────────── │   Nginx Reverse     │
│  (TypeScript)      │                │   Proxy             │
└────────────────────┘                └──────────┬──────────┘
                                                 │
                                      ┌──────────▼──────────┐
                                      │   FastAPI Backend   │
                                      │   (Python)          │
                                      └──────────┬──────────┘
                                                 │
                              ┌──────────────────▼──────────────────┐
                              │         PostgreSQL Database          │
                              │  subject_selection (FCFS enforced)  │
                              │  staff_assignment (eligibility)      │
                              │  selection_window (time gating)      │
                              │  audit_log (append-only history)     │
                              └─────────────────────────────────────┘
```

---

## Key Database Design Decisions

### Why PostgreSQL advisory locks?
The application layer cannot reliably prevent race conditions. Two API requests can pass application-level checks simultaneously and both proceed to INSERT. PostgreSQL advisory locks serialize these writes at the transaction level — only one proceeds at a time per `(staff_id, window_id)` pair.

### Why server-side sessions instead of JWT?
JWT tokens cache the user's role at issuance time. If a coordinator's role is revoked between token issue and request, the stale JWT still grants access. Server-side sessions query the database on every request — role changes take effect immediately.

### Why `OVERRIDDEN` status instead of DELETE?
Deletions destroy audit trail. Marking records as `OVERRIDDEN` preserves the full history of who had which subject and when it was removed. The audit log provides a legally defensible record for a real college environment.

### The `staff_slot_number`
Every selection carries a sequential slot number per `(staff_id, window_id)`. This represents the chronological order in which a faculty member selected subjects (1st, 2nd, 3rd...). It is assigned inside the transaction using `SELECT FOR UPDATE` and is never recomputed on subject changes — preserving the original selection timestamp fairness.

---

## Edge Cases Identified and Handled

| Scenario | Handling |
|---|---|
| Two faculty select same subject simultaneously | `ON CONFLICT DO NOTHING` + advisory lock → one succeeds, one gets 409 |
| Faculty changes subject (not just adds) | Old subject acquired first, new subject claimed, then old released — deadlock-safe ordering |
| Coordinator overrides during an active faculty change | Override blocks until staff transaction completes; returns 404 if faculty already released |
| Window closes mid-selection | Transaction checks window validity with `FOR SHARE` lock; in-progress transactions complete, new ones rejected |
| Faculty exceeds subject quota | Quota checked with `FOR UPDATE` inside transaction; cannot be bypassed |
| Network timeout during selection | Lock timeout set to 5s; returns 409 — safe to retry |
| Invalid email domain at OAuth login | Server checks `email.endswith("@hindustanuniv.ac.in")` before creating session |
| Coordinator role change takes effect | Role queried from DB on every request — no caching |

---

## API Overview

### Staff Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/staff/subjects` | List eligible subjects with availability hints |
| `POST` | `/api/staff/subjects/select` | FCFS subject claim |
| `POST` | `/api/staff/subjects/change` | Swap current subject (deadlock-safe) |

### Coordinator Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/coordinator/override` | Cancel any active selection |
| `POST` | `/api/windows` | Open a selection window |
| `DELETE` | `/api/windows/:id` | Close a selection window |
| `GET` | `/api/audit` | View full audit log |

### Auth
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/auth/login` | Redirect to Google OAuth |
| `GET` | `/api/auth/callback` | OAuth callback, session creation |
| `POST` | `/api/auth/logout` | Session destruction |

---

## Error Codes

| Condition | HTTP |
|---|---|
| Subject already taken by another faculty | 409 |
| Staff subject quota exceeded | 403 |
| Faculty not eligible for this subject | 403 |
| Selection window is closed | 403 |
| Concurrent change detected (deadlock) | 409 |
| Lock timeout (retry safe) | 409 |

---

## Running Locally

```bash
# Clone the repo
git clone https://github.com/Nithish-kumar-git/fwms-workload-system.git
cd fwms-workload-system

# Copy environment template
cp .env.example .env
# Fill in: DATABASE_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SESSION_SECRET

# Start with Docker Compose
docker-compose up --build
```

Backend: `http://localhost:8000`  
Frontend: `http://localhost:3000`

---

## Requirements Analysis — My Contribution

As the primary analyst and developer on this project, I was responsible for:

- Mapping the end-to-end workflow across Faculty, Coordinator, and System actors
- Defining system rules: workload quotas, window-based locking, role-based access control
- Identifying the core concurrency problem (race conditions on subject selection) and specifying the FCFS enforcement mechanism
- Documenting edge cases: simultaneous selection conflicts, coordinator override during active transaction, deadline states, and duplicate preference attempts
- Specifying the audit log as append-only with no cascade deletes — a requirement driven by the real-world legal context (real college, real staff, fairness legally relevant)
- Writing the Frozen System Blueprint (FSB) — a specification document used to guide implementation across multiple development sessions

---

## Project Context

Built for **Hindustan Institute of Technology and Science**, Chennai, to manage faculty subject preferences across departments each semester. The system handles real staff with real subject assignments — correctness and fairness were non-negotiable requirements.

---

*Developed by Nithish Kumar V · MCA, HITS Chennai · 2025–2026*  
*Contact: its.nithishnk@gmail.com*
