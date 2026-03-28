## Latest Update - March 28, 2026

### BUG 1: "Your Preferences" always empty - FIXED

**Changed in frontend/src/pages/PreferencesPage.tsx** (Line 84):

BEFORE:
```typescript
setPreferences(prefsRes.data.preferences || []);
```

AFTER:
```typescript
setPreferences(Array.isArray(prefsRes.data) ? prefsRes.data : prefsRes.data.preferences || []);
```

Backend returns plain array, not nested object.

---

### STEP 1: Get cycle_id by matching subject's semester - FIXED

**Changed in app/preference/service.py** (Line 241-256):

BEFORE:
```python
# Query active cycle_id
with get_transaction() as session:
    cycle_result = session.execute(
        text("SELECT id FROM cycle WHERE status = 'OPEN' LIMIT 1")
    )
    cycle_row = cycle_result.fetchone()
    if not cycle_row:
        return {"success": False, "message": "No active academic cycle found", 
                "preference_id": None, "rule": "NO-ACTIVE-CYCLE"}
    active_cycle_id = cycle_row[0]
```

AFTER:
```python
# Query cycle_id for this subject's semester
with get_transaction() as session:
    cycle_result = session.execute(
        text("""
            SELECT c.id 
            FROM cycle c
            JOIN subject_offering so ON so.academic_year_id = c.academic_year_id
                                    AND so.semester_id = c.semester_id
            WHERE so.id = :offering_id
            LIMIT 1
        """),
        {"offering_id": subject_offering_id}
    )
    cycle_row = cycle_result.fetchone()
    if not cycle_row:
        return {"success": False, "message": "No cycle found for this subject's semester",
                "preference_id": None, "rule": "CYCLE"}
    active_cycle_id = cycle_row[0]
```

---

### STEP 2: Cycle guard check - NO CHANGE NEEDED

**Found**: `require_cycle_unlocked()` at line 220
- This checks if cycle is FROZEN (after HOD approval)
- Does NOT block CLOSED cycles
- Only blocks FROZEN state
- No change needed - already allows CLOSED cycles

---

### STEP 3: Remove active cycle filter from list_preferences - FIXED

**Changed in app/preference/service.py** (Line 312-343):

BEFORE:
```python
from app.admin.cycle_service_new import get_active_cycle
active_cycle = get_active_cycle()
if not active_cycle:
    return []

WHERE fp.staff_id = :staff_id
  AND fp.cycle_id = :cid
{"staff_id": staff_id, "cid": active_cycle["id"]}
```

AFTER:
```python
WHERE fp.staff_id = :staff_id
ORDER BY fp.preference_number
{"staff_id": staff_id}
```

Removed active_cycle filter - now shows ALL preferences regardless of cycle.

---

### Commit
- Hash: e25b2fd
- Message: "Fix: allow preferences for all semesters not just active cycle"
- Pushed to main
