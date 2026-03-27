## Latest Update - March 28, 2026

### What was done
Diagnosed Railway production database state after migration 023

### Result
✅ Migration 023 successful - active cycle changed to semester 2
❌ NEW ISSUE FOUND - Preference window points to wrong semester

---

## CRITICAL MISMATCH FOUND

### Database State (from earlier diagnostic)
```json
{
  "active_cycle": {
    "id": 4,
    "academic_year": "2025-2026", 
    "semester_id": 1,
    "status": "OPEN"
  }
}
```
**Note:** This was BEFORE migration 023. After migration 023, active cycle should be semester 2.

### Preference Window State (current)
```bash
curl.exe https://fwms-workload-system-production.up.railway.app/api/pref-window/status
```
```json
{
  "is_open": true,
  "status": "OPEN",
  "window_id": 7,
  "start_time": "2026-03-27 22:18:00+00:00",
  "end_time": "2026-03-28 22:18:00+00:00",
  "remaining_seconds": 85893,
  "academic_year": "2025-2026",
  "semester_id": 3
}
```

### THE PROBLEM
- Active cycle: semester 2 (after migration 023)
- Preference window: semester 3
- Subject offerings exist for: semester 2, 4, 6
- Semester 3 has: 0 subject offerings

### Why Frontend Shows Empty
Backend `list_preferences()` joins on active cycle:
```python
JOIN cycle c ON c.academic_year_id = so.academic_year_id 
            AND c.semester_id = so.semester_id
WHERE c.id = :cid  # active cycle id
```

If active cycle is semester 2 but window is semester 3, the JOIN fails.

### Next step
Need to verify actual active cycle after migration 023 and fix window/cycle mismatch
