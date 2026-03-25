# Cycle Schema Migration Fix Summary

## Files Updated: 4

All references to the old `academic_cycle` table with `semester_type` (ODD/EVEN strings) have been updated to use the new `cycle` table with `semester_id` (integers 1-6).

---

## 1. app/admin/service.py

### Changes Made:

**Function: `list_allocations`**
- Parameter changed: `semester_type: str` → `semester_id: int`
- Added JOIN: `JOIN cycle c ON c.id = a.cycle_id`
- WHERE clause: `so.academic_year = :year AND so.semester_type = :sem_type` → `c.academic_year = :year AND c.semester_id = :sem_id`

**Function: `override_allocation`**
- Query updated to join `cycle` and `semester` tables
- Changed: `so.academic_year, so.semester_type` → `c.academic_year, s.label AS semester_name`
- Updated JOIN: `JOIN cycle c ON c.id = a.cycle_id` + `JOIN semester s ON s.id = c.semester_id`
- Updated workload refresh calls to use `semester_name` instead of `semester_type`

**Function: `reassign_subject`**
- Query updated to join `cycle` and `semester` tables
- Changed: `so.academic_year, so.semester_type` → `c.academic_year, s.label AS semester_name`
- Updated JOIN: `JOIN cycle c ON c.id = a.cycle_id` + `JOIN semester s ON s.id = c.semester_id`
- Updated workload refresh calls to use `semester_name` instead of `semester_type`

**Function: `get_workload_summary`**
- Parameter changed: `semester_type: str | None` → `semester_id: int | None`
- Updated workload_summary JOIN: `ws.semester_type = :sem_type` → `ws.semester_id = :sem_id`
- Updated to use `semester_id` from active cycle

**Function: `_refresh_workload_summary_for_cycle`**
- Parameter changed: `semester_type: str` → `semester_name: str`
- Added query to get `semester_id` from cycle: `SELECT semester_id FROM cycle WHERE id = :cid`
- Updated workload_summary upsert to use `semester_id` instead of `semester_type`
- Changed column references: `academic_cycle_id` → `cycle_id`

---

## 2. app/preference/window_router.py

### Changes Made:

**Schema: `OpenWindowRequest`**
- Field changed: `semester_type: str | None` → `semester_id: int | None`
- Updated description: `"EVEN or ODD"` → `"Semester ID (1-6)"`
- Field changed: `academic_cycle_id: int | None` → `cycle_id: int | None`

**Schema: `WindowStatusResponse`**
- Field changed: `semester_type: str | None` → `semester_id: int | None`

**Endpoint: `open_window`**
- Parameter passing updated: `semester_type=body.semester_type` → `semester_id=body.semester_id`
- Parameter passing updated: `academic_cycle_id=body.academic_cycle_id` → `cycle_id=body.cycle_id`

---

## 3. app/preference/window_service.py

### Changes Made:

**Function: `open_preference_window`**
- Parameter changed: `semester_type: str | None` → `semester_id: int | None`
- Parameter changed: `academic_cycle_id: int | None` → `cycle_id: int | None`
- Variable renamed: `cycle_id` → `resolved_cycle_id` (to avoid confusion)
- Table reference: `academic_cycle` → `cycle`
- WHERE clause: `semester_type = :sem` → `semester_id = :sem_id`
- Column reference: `academic_cycle_id` → `cycle_id`
- Window name format: `"Preference Window {academic_year} {semester_type}"` → `"Preference Window {academic_year} Sem-{semester_id}"`
- Audit log: `"semester_type": "{semester_type}"` → `"semester_id": {semester_id}`
- Updated to use `semester_id` from active cycle

**Function: `get_window_status`**
- JOIN updated: `LEFT JOIN academic_cycle ac ON ac.id = sw.academic_cycle_id` → `LEFT JOIN cycle c ON c.id = sw.cycle_id`
- Column reference: `ac.semester_type` → `c.semester_id`
- Return value: `"semester_type": row[5]` → `"semester_id": row[5]`

---

## 4. app/reports/master_workload_excel.py

### Changes Made:

**Function: `_resolve_active_cycle`**
- Return type: `tuple[str, str]` → `tuple[str, int]`
- Table reference: `academic_cycle` → `cycle`
- Column reference: `semester_type` → `semester_id`

**Function: `_fetch_workload_data`**
- Parameter changed: `semester_type: Optional[str]` → `semester_id: Optional[int]`
- Return type: `tuple[list[dict], str, str]` → `tuple[list[dict], str, int]`
- Added JOIN: `JOIN cycle c ON c.id = a.cycle_id`
- WHERE clause: `so.academic_year = :year AND so.semester_type = :sem_type` → `c.academic_year = :year AND c.semester_id = :sem_id`
- Updated workload_summary JOIN: `ws.semester_type = :sem_type` → `ws.semester_id = :sem_id`
- Updated unassigned faculty query: `WHERE so2.academic_year = :year AND so2.semester_type = :sem_type` → `WHERE c2.academic_year = :year AND c2.semester_id = :sem_id`
- Added JOIN in subquery: `JOIN cycle c2 ON c2.id = a2.cycle_id`

**Function: `generate_master_workload_excel`**
- Parameter changed: `semester_type: Optional[str]` → `semester_id: Optional[int]`
- Variable name: `st` → `sid`
- Header text: `f"MASTER WORKLOAD - {'EVEN' if st == 'EVEN' else 'ODD'} SEMESTER {ay}"` → `f"MASTER WORKLOAD - SEMESTER {sid} {ay}"`

**Function: `generate_from_snapshot`**
- Parameter changed: `semester_type: str` → `semester_id: int`
- Docstring updated: `semester_type: "ODD" or "EVEN"` → `semester_id: integer 1-6`
- Header text: `f"MASTER WORKLOAD - {'EVEN' if semester_type == 'EVEN' else 'ODD'} SEMESTER {academic_year}"` → `f"MASTER WORKLOAD - SEMESTER {semester_id} {academic_year}"`

---

## Summary of Changes

### Table References
- `academic_cycle` → `cycle` (everywhere)

### Column References
- `semester_type` (string: "ODD"/"EVEN") → `semester_id` (integer: 1-6)
- `academic_cycle_id` → `cycle_id` (in allocation and related tables)

### Join Pattern
To get semester name from cycle:
```sql
JOIN cycle c ON c.id = a.cycle_id
JOIN semester s ON s.id = c.semester_id
```

### Parameter Types
- All function parameters changed from `semester_type: str` to `semester_id: int`
- All API request schemas updated accordingly

### No ODD/EVEN References
- All hardcoded "ODD" and "EVEN" string values removed
- Replaced with integer semester IDs (1-6)
- Display formatting now uses semester_id directly or joins to get semester.label

---

## Testing Checklist

- [ ] Test `list_allocations` with semester_id parameter
- [ ] Test `override_allocation` with new schema
- [ ] Test `reassign_subject` with new schema
- [ ] Test `get_workload_summary` with semester_id
- [ ] Test preference window opening with semester_id
- [ ] Test preference window status endpoint
- [ ] Test master workload Excel generation
- [ ] Test snapshot-based Excel generation
- [ ] Verify all audit logs use correct field names
- [ ] Verify workload_summary updates use semester_id
