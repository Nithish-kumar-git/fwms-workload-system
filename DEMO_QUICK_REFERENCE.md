# Demo Quick Reference

> **Base URL:** `http://localhost:8000` (dev) or `https://YOUR_DOMAIN` (prod)
> **Auth:** `DEV_AUTH_BYPASS=true` auto-authenticates as staff_id=1 (coordinator)
> **Content-Type:** `application/json` for all POST requests

---

## API Call Sequence

### 1. Login (verify auth works)
```
GET /api/auth/me
```
**Expected:**
```json
{"staff_id": 1, "email": "hod.cse@hindustanuniv.ac.in", "name": "Dr. Rajesh Kumar", "is_coordinator": true}
```

### 2. Create Window
```
POST /api/windows/
{"name": "CSE 2022 - Sem 6", "batch_id": 1, "specialization_id": 1, "max_subjects_per_staff": 2}
```
**Expected:**
```json
{"id": 1, "name": "CSE 2022 - Sem 6", "status": "DRAFT", "batch_id": 1, "specialization_id": 1, "max_subjects_per_staff": 2, ...}
```

### 3. Schedule Window
```
POST /api/windows/1/schedule
{"start_time": "2026-02-22T10:00:00+05:30", "end_time": "2026-02-22T23:59:00+05:30"}
```
**Expected:**
```json
{"id": 1, "status": "SCHEDULED", "start_time": "2026-02-22T10:00:00+05:30", ...}
```

### 4. Open Window
```
POST /api/windows/1/open
```
**Expected:**
```json
{"id": 1, "status": "OPEN", ...}
```

### 5. Select Subject (success)
```
POST /api/selection/select
{"subject_id": 1, "batch_id": 1, "specialization_id": 1}
```
**Expected:**
```json
{"success": true, "message": "Subject selected successfully", "selection_id": 1}
```

### 6. Select Same Subject (conflict)
```
POST /api/selection/select
{"subject_id": 1, "batch_id": 1, "specialization_id": 1}
```
**Expected:**
```json
409 {"detail": "Subject already selected"}
```

### 7. Select 3rd Subject (quota exceeded — max is 2)
```
POST /api/selection/select
{"subject_id": 3, "batch_id": 1, "specialization_id": 1}
```
**Expected (after selecting 2 subjects already):**
```json
403 {"detail": "Quota exceeded"}
```

### 8. Close Window
```
POST /api/windows/1/close
```
**Expected:**
```json
{"id": 1, "status": "CLOSED", ...}
```

### 9. Select After Close (rejected)
```
POST /api/selection/select
{"subject_id": 4, "batch_id": 1, "specialization_id": 1}
```
**Expected:**
```json
403 {"detail": "Window closed"}
```

---

## Data Reference

| Entity | IDs | Notes |
|--------|-----|-------|
| Coordinators | 1, 2, 3 | Dr. Rajesh (CSE), Dr. Priya (ECE), Dr. Suresh (MECH) |
| CSE Faculty | 4, 5, 6, 7 | Anand, Deepa, Kartik, Lakshmi |
| ECE Faculty | 8, 9, 10, 11 | Mohan, Nithya, Pradeep, Revathi |
| MECH Faculty | 12, 13, 14, 15 | Senthil, Uma, Vijay, Yamini |
| Batches | 1=2022, 2=2023, 3=2024 | |
| Specs | 1=CSE, 2=ECE, 3=MECH | |
| CSE 2022 subjects | 1–4 | CS601–CS604 |
| CSE 2023 subjects | 5–8 | CS401–CS404 |
| CSE 2024 subjects | 9–12 | CS201–CS204 |

---

## Demo Failure Recovery

| Problem | Cause | Fix |
|---------|-------|-----|
| `401 Unauthorized` | Auth bypass not enabled | Set `DEV_AUTH_BYPASS=true`, restart app |
| `404 Not Found` on window | Wrong window_id | Check `GET /api/windows/{id}` |
| `400` on schedule | start_time in the past | Use future timestamp |
| `409` on open | Another OPEN window exists for same batch/spec | Close the other window first |
| `403 Not eligible` | Staff not assigned to batch/spec | Check `staff_assignment` table |
| `500 Internal Server Error` | DB connection issue | `docker compose restart app` |
| All selections gone | App restarted with fresh DB | Re-run `004_seed_demo.sql`, redo selections |
| Window stuck in DRAFT | Forgot to schedule first | Must schedule before opening |

---

## Faculty Objection Handling

### "Two of us clicked at the same time — who gets it?"

**Answer:** The database uses `SELECT ... FOR UPDATE` row locking with a unique partial index. At the database level, only ONE transaction can commit a `SELECTED` status for any subject. The first transaction to acquire the lock wins. The second gets `409 Subject already selected`.

**Evidence:** Show `uq_subject_selected` unique index in schema. This is the same concurrency guarantee used by airline booking systems.

### "The coordinator forgot to close the window — someone selected late!"

**Answer:** The coordinator can close the window at any time. Once closed, all subsequent selection attempts fail with `403 Window closed`. If a late selection snuck in, the coordinator can use the override endpoint to reassign it. The audit log records exactly when each selection was made.

**Recovery:** `POST /api/windows/{id}/close` → immediately blocks all selections.

### "I need more subjects than the quota allows"

**Answer:** The quota (`max_subjects_per_staff`) is set per window by the coordinator. To change it:
1. If window is in DRAFT: coordinator creates a new window with a higher quota
2. If window is OPEN: coordinator must close the current window, create a new one with adjusted quota, and re-open. Previous selections are preserved in the DB.

**Note:** Quota changes require administrator action — faculty cannot self-serve this.

### "I think the process was unfair — someone got preference"

**Answer:** Pull the audit log:
```sql
SELECT al.created_at, s.name AS staff, sub.code, sub.name AS subject, al.action_type
FROM audit_log al
JOIN staff s ON al.actor_staff_id = s.id
LEFT JOIN subject sub ON al.subject_id = sub.id
WHERE al.action_type IN ('SELECT', 'OVERRIDE')
ORDER BY al.created_at;
```

This shows the **exact timestamp** of every selection. FCFS is provably enforced — the person who selected first has the earlier `created_at`. The audit log is append-only (UPDATE/DELETE triggers prevent tampering).
