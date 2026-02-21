# Demo Script — Faculty Subject Selection System

> **Audience:** College administrators, IT committee
> **Duration:** 15–20 minutes
> **Setup:** System running with demo seed data (004_seed_demo.sql)

---

## Pre-Demo Setup

```bash
# Load demo data
docker exec -i faculty_db psql -U faculty_user -d faculty_selection \
  < migrations/004_seed_demo.sql

# Verify data loaded
docker exec faculty_db psql -U faculty_user -d faculty_selection \
  -c "SELECT count(*) AS staff FROM staff; SELECT count(*) AS subjects FROM subject;"
```

Set `DEV_AUTH_BYPASS=true` (development mode only) for demo without Google OAuth.

---

## Act 1: Coordinator Login (2 min)

**Narrator:** "The coordinator logs in using their university Google account."

1. Open browser → `https://YOUR_DOMAIN/api/auth/login`
2. (Dev mode: any request is auto-authenticated as coordinator)
3. Verify: `GET /api/auth/me` → shows coordinator info

**Key point:** "Only `@hindustanuniv.ac.in` accounts can log in."

---

## Act 2: Create a Selection Window (3 min)

**Narrator:** "The coordinator creates a window for CSE 2022 Batch."

```bash
# Create window in DRAFT state
POST /api/windows/
{
  "name": "CSE 2022 - Semester 6 Selection",
  "batch_id": 1,
  "specialization_id": 1,
  "max_subjects_per_staff": 2
}
# Response: window_id (note this for later steps)
```

**Key point:** "Window starts in DRAFT — no times set yet, no one can select."

---

## Act 3: Schedule the Window (2 min)

**Narrator:** "The coordinator sets the time window and locks it."

```bash
# Schedule (set times — they become IMMUTABLE after this)
POST /api/windows/{window_id}/schedule
{
  "start_time": "2026-02-22T10:00:00+05:30",
  "end_time": "2026-02-22T18:00:00+05:30"
}
```

**Key point:** "Once scheduled, the start and end times cannot be changed. This prevents manipulation."

---

## Act 4: Open the Window (1 min)

**Narrator:** "The coordinator opens the window. Faculty can now select subjects."

```bash
# Open window
POST /api/windows/{window_id}/open
```

**Key point:** "Only ONE window can be OPEN per batch+specialization at a time. The database enforces this."

---

## Act 5: Staff Select Subjects — FCFS Demo (5 min)

**Narrator:** "Now let's simulate faculty selecting subjects first-come-first-served."

### Staff 1: Prof. Anand selects Compiler Design
```bash
POST /api/selection/select
{
  "subject_id": 1,
  "batch_id": 1,
  "specialization_id": 1
}
# ✅ Response: success, selection_id=1
```

### Staff 2: Prof. Deepa tries the SAME subject
```bash
POST /api/selection/select
{
  "subject_id": 1,
  "batch_id": 1,
  "specialization_id": 1
}
# ❌ Response: 409 "Subject already selected" — FCFS enforced!
```

**Key point:** "The database guarantees that only one faculty can hold a subject. Even if two people click at the exact same millisecond, one will succeed and the other will get a conflict."

### Staff 2: Prof. Deepa selects a different subject
```bash
POST /api/selection/select
{
  "subject_id": 2,
  "batch_id": 1,
  "specialization_id": 1
}
# ✅ Response: success
```

---

## Act 6: Quota Enforcement (2 min)

**Narrator:** "Each faculty has a maximum number of subjects they can select."

### Prof. Anand tries to select a 3rd subject (max is 2)
```bash
POST /api/selection/select
{
  "subject_id": 4,
  "batch_id": 1,
  "specialization_id": 1
}
# Assuming Anand already selected 2: ❌ Response: 403 "Quota exceeded"
```

**Key point:** "The system automatically enforces quotas — no manual checking needed."

---

## Act 7: Eligibility Check (1 min)

**Narrator:** "Faculty can only select subjects for batches they are assigned to."

### Prof. Mohan (ECE faculty) tries to select a CSE subject
```bash
# Mohan (staff_id=8) is assigned to ECE, not CSE
POST /api/selection/select
{
  "subject_id": 1,
  "batch_id": 1,
  "specialization_id": 1
}
# ❌ Response: 403 "Not eligible for this subject"
```

**Key point:** "Eligibility is enforced by the database via foreign key constraints. It cannot be bypassed."

---

## Act 8: Close the Window (1 min)

**Narrator:** "The coordinator closes the window. No more selections allowed."

```bash
POST /api/windows/{window_id}/close
```

### Staff tries to select after closing
```bash
POST /api/selection/select
{
  "subject_id": 3,
  "batch_id": 1,
  "specialization_id": 1
}
# ❌ Response: 403 "Window closed"
```

**Key point:** "Once closed, no one can make any more selections."

---

## Act 9: Audit Log (2 min)

**Narrator:** "Every action is permanently logged. The audit log cannot be modified or deleted."

```bash
# View audit log (direct DB query for demo)
docker exec faculty_db psql -U faculty_user -d faculty_selection \
  -c "SELECT id, action_type, actor_staff_id, subject_id, created_at FROM audit_log ORDER BY created_at;"
```

**Key points:**
- "Every selection, override, window open/close is logged"
- "The audit log is append-only — even database admins cannot modify it"
- "This provides a complete forensic trail for any disputes"

---

## Closing Statement

> "This system handles **subject allocation only**. It ensures fair, first-come-first-served assignment with database-enforced guarantees.
>
> Timetable generation is a separate concern and is **not part of this system**.
>
> The system is ready for controlled deployment to faculty."
