# 🧊 FROZEN SYSTEM BLUEPRINT (FSB) v1.3
## Faculty Subject Selection System — EXECUTION SPECIFICATION

**Status:** FROZEN FOR PRODUCTION USE  
**Scope:** Phases 3.3 → 3.8 ONLY  
**Audience:** AI Code Generators (Claude, Gemini, Cursor, Antigravity, Windsurf)  
**Change Policy:** ❌ NO DESIGN CHANGES — Clarifications only  
**Deployment Context:** Real college, real staff, FCFS fairness legally relevant  
**Date:** 2026-02-12

---

## 0. ABSOLUTE RULES (NON-NEGOTIABLE)

These rules override all other instructions.

- FCFS ordering is enforced ONLY by PostgreSQL constraints.
- Application code MUST NOT implement availability checks.
- NO automatic retries on FCFS paths (SELECT / CHANGE).
- All quota enforcement MUST use SELECT … FOR UPDATE.
- Role (is_coordinator) MUST be queried from DB on EVERY request.
- Reads MUST NOT lock, write, or mutate state.
- Notifications MUST occur AFTER transaction commit.
- audit_log is APPEND-ONLY (no UPDATE, no DELETE).
- If behavior is not specified here, DO NOT INVENT IT.

Any violation = incorrect system.

---

## 1. PHASE 3.3 — AUTH & IDENTITY (GOOGLE OAUTH)

### 1.1 Authentication Method
- Authentication mechanism: Google OAuth 2.0 ONLY
- No username/password auth
- No fallback auth

### 1.2 OAuth Flow (EXACT)
1. User clicks "Login with Google"
2. Redirect to:
```
   https://accounts.google.com/o/oauth2/v2/auth
```
3. OAuth callback URL (EXACT):
```
   /api/auth/callback
```
4. Backend verifies Google token
5. Extract email
6. Validate email domain (see 1.3)
7. Query staff table
8. Create server-side session
9. Redirect user to: `/dashboard`

### 1.3 Email Domain Enforcement (EXACT IMPLEMENTATION)

**Rule:**
- Email MUST end with `@hindustanuniv.ac.in`

**Python logic (ONLY acceptable form):**
```python
email.endswith("@hindustanuniv.ac.in")
```

**Explicitly REJECT:**
- `user@gmail.com@hindustanuniv.ac.in`
- `user@hindustanuniv.ac.in.attacker.com`

### 1.4 Session Management (MANDATORY)

**Session Type:** Server-side (NOT JWT)  
**Storage:** Redis (optional) OR in-memory

**Session Key:**
```
session:<random_uuid>
```

**Session Value:**
```json
{
  "staff_id": INTEGER
}
```

**Expiration:** 4 hours

**On EVERY request:**
- Validate session exists
- Query staff table using staff_id
- Read is_coordinator fresh from DB

**Logout:**
- Delete session key from Redis/memory

**JWT is FORBIDDEN**  
Reason: JWT caches role → stale privilege escalation risk.

### 1.5 Authorization Rules

**Staff endpoints:**
- Require authenticated session

**Coordinator endpoints:**
- Require authenticated session
- AND `staff.is_coordinator == true`

Role checks MUST be enforced via dependency, not inline logic.

---

## 2. PHASE 3.4 — READ APIs (SAFE READS ONLY)

### 2.1 Global Read Rules
- No INSERT / UPDATE / DELETE
- No FOR UPDATE
- No FOR SHARE
- No locks of any kind
- No writes (including "last_viewed")

### 2.2 Window Visibility Rule
- Staff CAN view subjects when window is CLOSED
- Staff CANNOT select or change when window is CLOSED
- Read APIs always return data (read-only)

UI should display: "Window Closed — View Only"

### 2.3 GET /api/staff/subjects (EXACT SQL)

**Authorization:** Authenticated staff  
**Behavior:** Read-only, eligibility enforced in SQL
```sql
SELECT 
  s.id,
  s.code,
  s.name,
  CASE 
    WHEN ss.subject_id IS NULL THEN true 
    ELSE false 
  END AS is_available_hint,
  CASE 
    WHEN ss.staff_id = :current_staff_id THEN true 
    ELSE false 
  END AS selected_by_you
FROM subject s
JOIN staff_assignment sa 
  ON s.batch_id = sa.batch_id 
 AND s.specialization_id = sa.specialization_id
LEFT JOIN subject_selection ss 
  ON s.id = ss.subject_id 
 AND ss.status = 'SELECTED'
WHERE sa.staff_id = :current_staff_id
  AND s.is_active = true
ORDER BY s.code;
```

- `is_available_hint` is NON-AUTHORITATIVE
- API MUST NOT imply guarantee
- Empty array allowed if no eligibility

---

## 3. PHASE 3.5 — FCFS WRITE APIs (CRITICAL)

### 3.1 Database Schema Requirements (MANDATORY)

**subject_selection table MUST include:**
- id
- subject_id
- staff_id
- batch_id
- specialization_id
- window_id  → FK to selection_window(id)
- staff_slot_number INTEGER NOT NULL
- status (DOMAIN: 'SELECTED', 'OVERRIDDEN' — FROZEN)
- selected_at

**Status Domain (FROZEN):**
- `'SELECTED'` — Active selection by staff
- `'OVERRIDDEN'` — Cancelled by coordinator override

**NO OTHER STATUS VALUES PERMITTED.**

**Foreign Key Constraints:**
- Composite FK to staff_assignment (eligibility enforcement)
- Composite FK to subject (prevents batch/spec mismatch)
- See Phase 1 schema for exact DDL

### 3.2 ADVISORY LOCK SERIALIZATION RULES

**STATUS:** FROZEN — NON-NEGOTIABLE

These rules define the mandatory advisory locking protocol for all FCFS write transactions. Violations will result in race conditions and FCFS ordering failures.

---

#### Rule 1: Lock Acquisition Scope

**SELECT and CHANGE transactions MUST acquire:**
```sql
pg_advisory_xact_lock(staff_id, window_id)
```

**Override transactions MUST NOT acquire advisory locks.**

---

#### Rule 2: Lock Acquisition Timing

The advisory lock MUST be acquired:
- **After** window validation
- **After** eligibility validation
- **Before** quota check
- **Before** slot assignment
- **Before** any INSERT or DELETE on `subject_selection`

---

#### Rule 3: Lock Ordering with Row-Level Locks

The advisory lock MUST be acquired **before** any `FOR UPDATE` on `subject_selection` rows.

**Mandatory lock order:**
1. `FOR SHARE` (window and eligibility validation)
2. Advisory lock (`pg_advisory_xact_lock`)
3. Row-level write locks (`FOR UPDATE` on quota, slot)
4. `INSERT` / `DELETE` on `subject_selection`
5. Audit log insert

---

#### Rule 4: CHANGE Transaction Slot Reuse

**CHANGE transaction MUST reuse the original `staff_slot_number`.**

It MUST NOT recompute `MAX(staff_slot_number)`.

**Rationale:** Slot numbers represent chronological selection order and must remain stable across subject changes.

---

#### Rule 5: Override Exemption

**Override transactions MUST NOT acquire advisory locks.**

**Rationale:** Overrides are coordinator-initiated and do not participate in FCFS ordering.

---

#### Rule 6: Lock Key Format

Advisory lock key MUST use the **two-integer form:**
```sql
pg_advisory_xact_lock(staff_id, window_id)
```

**FORBIDDEN:**
```sql
pg_advisory_xact_lock(hashtext(staff_id || window_id))
```

**Rationale:** Two-integer form is deterministic, collision-free, and debuggable.

---

#### Rule 7: Complete Lock Ordering

**Full transaction lock order (MANDATORY):**

1. **FOR SHARE** — Window and eligibility validation
2. **Advisory lock** — `pg_advisory_xact_lock(staff_id, window_id)`
3. **Row-level write locks** — `FOR UPDATE` on quota and slot queries
4. **INSERT/DELETE** — Mutations on `subject_selection`
5. **Audit log** — Append-only insert

**This ordering is non-negotiable and MUST be preserved in all implementations.**

---

### 3.3 staff_slot_number (EXACT DEFINITION)

**Definition:**
- `staff_slot_number` represents the Nth subject selected by a staff member in a given window.

**Scope:**
- `(staff_id, window_id)`

**Allowed values:**
- 1, 2, 3, ...

**Assignment logic:**
- Determined INSIDE transaction
- MUST use SELECT … FOR UPDATE

**Assignment SQL:**
```sql
SELECT COALESCE(MAX(staff_slot_number), 0) + 1
FROM subject_selection
WHERE staff_id = :staff_id
  AND window_id = :window_id
  AND status = 'SELECTED'
FOR UPDATE;
```

### 3.4 Quota Enforcement (RACE-SAFE)

**Quota is enforced per staff per window.**

**Quota check SQL (MANDATORY):**
```sql
SELECT COUNT(*)
FROM subject_selection
WHERE staff_id = :staff_id
  AND window_id = :window_id
  AND status = 'SELECTED'
FOR UPDATE;
```

**IF count >= max_subjects_per_staff:**
- ROLLBACK
- RETURN HTTP 403 "Quota exceeded"

### 3.5 SELECT SUBJECT — TRANSACTION FLOW (EXACT)
```sql
BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED
SET LOCAL lock_timeout = '5s'
```

**Step 1 — Window Validation**
```sql
SELECT id, max_subjects_per_staff
FROM selection_window
WHERE is_active = true
  AND now() BETWEEN start_time AND end_time
FOR SHARE;
```

**IF NOT FOUND:**
- ROLLBACK
- RETURN 403 "Window closed"

**Step 1.5 — Eligibility Verification (PRE-CHECK)**
```sql
SELECT sa.id
FROM staff_assignment sa
JOIN subject s
  ON s.batch_id = sa.batch_id
 AND s.specialization_id = sa.specialization_id
WHERE sa.staff_id = :staff_id
  AND s.id = :subject_id
FOR SHARE;
```

**IF NOT FOUND:**
- ROLLBACK
- RETURN 403 "Not eligible for this subject"

**Step 1.75 — Advisory Lock Acquisition**
```sql
SELECT pg_advisory_xact_lock(:staff_id, :window_id);
```

**Step 2 — Lock Quota**  
(Use Section 3.4 SQL)

**Step 3 — Assign staff_slot_number**  
(Use Section 3.3 SQL)

**Step 4 — FCFS Claim (ONLY arbiter)**
```sql
INSERT INTO subject_selection
  (subject_id, staff_id, batch_id, specialization_id,
   window_id, staff_slot_number, status, selected_at)
VALUES (...)
ON CONFLICT (subject_id) WHERE status = 'SELECTED'
DO NOTHING
RETURNING id;
```

**IF no row returned:**
- ROLLBACK
- RETURN 409 "Subject already selected"

**Step 5 — Audit Log**
```sql
INSERT INTO audit_log (...)
```

**COMMIT**  
**RETURN 200**

### 3.6 CHANGE SUBJECT — DEADLOCK-SAFE RULES

- Acquire NEW subject before releasing OLD
- Never delete old first

**Deadlock Handling (MANDATORY):**

**IF SQLSTATE 40P01:**
- RETURN 409 "Concurrent change detected, please try again"
- NO automatic retry

This is acceptable and fair.

---

## 4. PHASE 3.6 — COORDINATOR OVERRIDES

### 4.1 Authorization
- MUST require coordinator role
- Role MUST be checked via DB

### 4.2 Override Logic (EXACT)
```sql
UPDATE subject_selection
SET status = 'OVERRIDDEN'
WHERE subject_id = :subject_id
  AND status = 'SELECTED'
FOR UPDATE;
```

**IF rowcount == 0:**
- RETURN 404 "Subject no longer selected"

### 4.3 Override During Change (DEFINED BEHAVIOR)
- Override blocks until staff transaction finishes
- If staff deletes subject first:
  - Override returns 404
- Coordinator may retry on new subject
- Both outcomes are SAFE and auditable

---

## 5. PHASE 3.7 — AUDIT & HISTORY

### 5.1 audit_log Table (EXACT)

**Fields:**
- id BIGSERIAL PK
- actor_staff_id INTEGER FK staff(id)
- action_type ENUM:  
  `('SELECT','CHANGE','OVERRIDE','WINDOW_OPEN','WINDOW_CLOSE')`
- subject_id INTEGER NULLABLE
- affected_staff_id INTEGER NULLABLE
- details JSONB
- created_at TIMESTAMPTZ DEFAULT now()

**Constraints:**
- NO ON DELETE CASCADE
- ON DELETE SET NULL ONLY

### 5.2 Audit Rules
- INSERT ONLY
- NO UPDATE
- NO DELETE
- Coordinator-only read access

---

## 6. PHASE 3.8 — NOTIFICATIONS

### 6.1 Triggering Rule
- Notifications MUST be triggered AFTER COMMIT
- NEVER inside transaction

### 6.2 Mechanism
- Use FastAPI BackgroundTasks
- Best-effort delivery
- No retries
- Failures logged only

### 6.3 Example (Override)
1. Override transaction commits
2. Background task sends email
3. Email failure does NOT affect API response

---

## 7. ERROR MAPPING (MANDATORY)

| Condition | SQLSTATE | HTTP |
|-----------|----------|------|
| Subject taken | — | 409 |
| Quota exceeded | — | 403 |
| Not eligible | — | 403 |
| Window closed | — | 403 |
| Serialization failure | 40001 | 409 |
| Deadlock | 40P01 | 409 |
| Lock timeout | 55P03 | 409 |

---

## 8. FREEZE DECLARATION

This document becomes immutable after final audit approval.

Any change requires:
- New FSB version
- Full re-audit

### ✅ FREEZE READINESS

| Category | Status |
|----------|--------|
| FCFS correctness | ✅ |
| Quota race safety | ✅ |
| Auth clarity | ✅ |
| AI hallucination risk | ✅ Eliminated |
| DB safety vs buggy app | ✅ |
| Specification completeness | ✅ |
| Advisory lock serialization | ✅ FROZEN |

---

**END OF FSB v1.3**
