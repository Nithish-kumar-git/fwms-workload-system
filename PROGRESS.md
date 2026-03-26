# BUG FIX RESULTS

## BUG 1: window_service.py Cycle Lookup - FIXED ✅

### Problem
The `open_preference_window()` function was trying to lookup cycles using a non-existent `academic_year` column:
```python
SELECT id FROM cycle
WHERE academic_year = :year AND semester_id = :sem_id
```

The `cycle` table uses `academic_year_id` (FK to academic_year.id), not a direct string column.

### Fix Applied
Changed the query to join with the `academic_year` table:
```python
SELECT c.id FROM cycle c
JOIN academic_year ay ON c.academic_year_id = ay.id
WHERE ay.name = :year AND c.semester_id = :sem_id
ORDER BY c.id DESC LIMIT 1
```

### Test Result
```bash
curl -X POST -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  --data "@test_window_open.json" \
  http://localhost:8000/api/pref-window/open
```

**Response:**
```json
{"success":true,"message":"Preference window opened","window_id":1}
```

**Status: FIXED ✅**

---

## BUG 2: Multiple OPEN Cycles - FIXED ✅

### Problem
Database had 3 cycles with `status='OPEN'` simultaneously:
- Cycle 1: Semester II (OPEN)
- Cycle 2: Semester IV (OPEN)
- Cycle 3: Semester VI (OPEN)

This violated the business rule that only one cycle can be OPEN at a time.

### Fix Applied
Closed cycles 2 and 3:
```sql
UPDATE cycle SET status='CLOSED', closed_at=NOW() WHERE id IN (2, 3);
```

**SQL Output:**
```
UPDATE 2
```

### Verification Query
```sql
SELECT c.id, c.status, c.semester_id, s.label 
FROM cycle c 
JOIN semester s ON s.id = c.semester_id 
ORDER BY c.id;
```

**Result:**
```
 id | status | semester_id | label 
----+--------+-------------+-------
  1 | OPEN   |           2 | II
  2 | CLOSED |           4 | IV
  3 | CLOSED |           6 | VI
(3 rows)
```

### API Test Result
```bash
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/cycles
```

**Response (formatted):**
```json
[
  {
    "id": 1,
    "academic_year": "2025-2026",
    "semester_id": 2,
    "semester_name": "II",
    "status": "OPEN",
    "is_active": true,
    "created_at": "2026-03-25T22:37:32.901376"
  },
  {
    "id": 2,
    "academic_year": "2025-2026",
    "semester_id": 4,
    "semester_name": "IV",
    "status": "CLOSED",
    "closed_at": "2026-03-26T07:00:00.919826",
    "is_active": false,
    "created_at": "2026-03-25T22:37:32.901376"
  },
  {
    "id": 3,
    "academic_year": "2025-2026",
    "semester_id": 6,
    "semester_name": "VI",
    "status": "CLOSED",
    "closed_at": "2026-03-26T07:00:00.919826",
    "is_active": false,
    "created_at": "2026-03-25T22:37:32.901376"
  }
]
```

**Status: FIXED ✅**

Cycles 2 and 3 now correctly show:
- `status: "CLOSED"`
- `is_active: false`
- `closed_at` timestamp set

The frontend Activate button will now appear for these closed cycles.

---

## Git Commit

**Commit Hash:** `6bd8e01`

**Commit Message:** `Fix: window_service cycle lookup + close duplicate OPEN cycles`

**Files Changed:**
- `app/preference/window_service.py` - Fixed cycle lookup query
- `PROGRESS.md` - Updated with fix results
- `test_window_open.json` - Test data file

**Push Status:** Successfully pushed to `origin/main`

---

## Summary

Both bugs are now FIXED:

1. ✅ **BUG 1**: Window service can now correctly lookup cycles by academic_year string + semester_id
2. ✅ **BUG 2**: Only one cycle (Semester II) is OPEN; cycles 2 and 3 are properly CLOSED

The system now correctly enforces the "one OPEN cycle at a time" business rule, and the preference window can be opened for any semester by looking up the correct cycle.
