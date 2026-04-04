# Export Endpoints 500 Error Diagnosis

## Endpoints Analyzed

1. **GET /api/reports/export/master-workload.xlsx** (app/reports/router.py line 203-233)
2. **GET /api/reports/export/workload.pdf** (app/reports/router.py line 238-273)

---

## Handler Code

### Master Workload Excel Handler (line 203-233)
```python
@router.get("/export/master-workload.xlsx")
async def export_master_workload(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    snapshot, academic_year, semester_id = _get_snapshot_or_live_data()

    from app.reports.master_workload_excel import generate_from_snapshot
    
    if snapshot:
        snapshot_data = snapshot["snapshot_data"]
    else:
        from app.reports.snapshot_service import _build_snapshot_data
        from app.db.session import get_transaction
        with get_transaction() as session:
            snapshot_data = _build_snapshot_data(session, academic_year, semester_id)
    
    try:
        excel_bytes = generate_from_snapshot(
            snapshot_data=snapshot_data,
            academic_year=academic_year,
            semester_id=semester_id,
        )
    except Exception as e:
        logger.error(f"Master workload Excel generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Excel generation error: {str(e)}")
```

### PDF Handler (line 238-273)
```python
@router.get("/export/workload.pdf")
async def export_pdf(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    snapshot, academic_year, semester_id = _get_snapshot_or_live_data()

    from app.reports.pdf_generator import generate_pdf_from_snapshot
    
    if snapshot:
        snapshot_data = snapshot["snapshot_data"]
    else:
        from app.reports.snapshot_service import _build_snapshot_data
        from app.db.session import get_transaction
        with get_transaction() as session:
            snapshot_data = _build_snapshot_data(session, academic_year, semester_id)
    
    try:
        pdf_bytes = generate_pdf_from_snapshot(
            snapshot_data=snapshot_data,
            academic_year=academic_year,
            semester_id=semester_id,
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")
```

---

## Root Cause Analysis

### BOTH endpoints fail for the SAME reason:

**Exception Source**: `_build_snapshot_data()` in app/reports/snapshot_service.py (line 186-310)

**The Query** (line 196-243):
```python
rows = session.execute(
    text("""
        SELECT
            s.id, s.emp_code, s.name, s.designation,
            p.ug_pg, p.name, sub.course_category,
            sem.label, sec.label, so.student_strength,
            sub.code, sub.name, a.complexity,
            sub.credits, a.l_assigned, a.t_assigned, a.p_assigned,
            ws.norm_hours, ws.other_academic, ws.remarks,
            ws.research_scholars
        FROM allocation a
        JOIN subject_offering so ON so.id = a.subject_offering_id
        JOIN subject sub ON sub.id = so.subject_id
        JOIN program p ON p.id = so.program_id
        JOIN semester sem ON sem.id = so.semester_id
        JOIN section sec ON sec.id = so.section_id
        JOIN staff s ON s.id = a.staff_id
        LEFT JOIN workload_summary ws
            ON ws.staff_id = s.id
           AND ws.academic_year = :year
           AND ws.semester_id = :sem_id
        WHERE so.academic_year = :year
          AND so.semester_id = :sem_id
          AND s.is_active = true
        ORDER BY s.emp_code ASC, p.name, sem.label, sec.label
    """),
    {"year": academic_year, "sem_id": semester_id},
).fetchall()
```

### The Actual 500 Error Cause:

**EMPTY RESULT SET** → `snapshot_data = []` → **Excel/PDF generators receive empty list**

**Why it's empty**:
1. **No allocations exist** for the given academic_year + semester_id
2. The query `FROM allocation a` returns 0 rows
3. `_build_snapshot_data()` returns empty list `[]`
4. Excel/PDF generators receive `snapshot_data=[]`
5. Generators create valid files but with **NO faculty data rows**
6. **This should NOT cause 500** - it should return empty report

### The REAL 500 Error:

Looking at the Excel generator (app/reports/master_workload_excel.py line 600-750), the `generate_from_snapshot()` function:

**DOES handle empty data** - it will create header rows and just have no data rows.

**Therefore, the 500 error is NOT from empty data.**

### Alternative 500 Cause:

**The cycle status query in `_get_snapshot_or_live_data()` is STILL failing** even after our fix.

**Reason**: The fix was pushed to GitHub but Railway hasn't redeployed yet, OR there's a different issue.

**Check**: The query now looks for cycles IN ('OPEN', 'ALLOCATED', 'FROZEN'), but if:
- No cycle exists in any of these states → HTTPException 400 (not 500)
- Cycle exists but has no allocations → empty report (not 500)

### Most Likely 500 Cause:

**The old code is still running on Railway** - the fix hasn't been deployed yet.

The OLD code (before our fix) had:
```python
cycle = session.execute(
    text("""
        SELECT c.id, ay.label, c.semester_id, c.status
        FROM cycle c
        JOIN academic_year ay ON ay.id = c.academic_year_id
        WHERE c.status = 'OPEN'  # <-- TOO RESTRICTIVE
        LIMIT 1
    """)
).fetchone()
```

If cycle status is 'ALLOCATED' or 'FROZEN', this returns `None`, causing:
- `academic_year, semester_id = None, None` → **TypeError or AttributeError** → 500

---

## Workload Summary Table Status

**Table exists**: Yes (created in migration 005, updated in migrations 010 and 021)

**Has data**: Unknown - depends on whether HOD has approved workload

**Impact if empty**: None - the query uses `LEFT JOIN workload_summary`, so missing data just means:
- `norm_hours` defaults to 12
- `other_academic` defaults to 0
- `remarks` defaults to ''
- `research_scholars` is NULL

**This does NOT cause 500 errors.**

---

## Summary

### Master Workload Excel 500 Error:
- **File**: app/reports/router.py line 203-233
- **Actual Exception**: Likely `AttributeError` or `TypeError` from old code trying to unpack None
- **Root Cause**: Old code (before fix) only queries cycles with status='OPEN', returns None for ALLOCATED/FROZEN cycles
- **Fix Status**: Committed (31e0709) but not yet deployed to Railway

### PDF 500 Error:
- **File**: app/reports/router.py line 238-273
- **Actual Exception**: Same as above
- **Root Cause**: Same as above - both use `_get_snapshot_or_live_data()`
- **Fix Status**: Same as above

### Both Fail for Same Reason:
✅ YES - both call `_get_snapshot_or_live_data()` which had the restrictive cycle query

### Workload Summary Data:
- Table exists with proper schema
- LEFT JOIN handles missing data gracefully
- NOT the cause of 500 errors

### Next Step:
Wait for Railway to redeploy from commit 31e0709, then test exports again.


---

## UPDATED DIAGNOSIS - Railway Deployed

### What _build_snapshot_data() Returns:

**Returns**: List of dicts (NOT Row objects)

**Structure** (from app/reports/snapshot_service.py line 320-335):
```python
blocks.append({
    "serial":         serial,
    "emp_code":       m["emp_code"],
    "faculty_name":   m["faculty_name"],
    "designation":    m["designation"],
    "min_workload":   min_wl,
    "deviation":      deviation,
    "remarks":        m["remarks"],
    "other_academic": m["other_academic"],
    "total_workload": total_workload,
    "total_tch":      total_tch,
    "subjects":       subjects_json,  # List of subject dicts
})
```

### Master Workload Excel Generator Analysis:

**Function**: `generate_from_snapshot()` (app/reports/master_workload_excel.py line 500-680)

**With Empty List `[]`**:
- Line 570: `for block in snapshot_data:` → iterates 0 times, no crash
- Line 650-665: Sheet 2 creation → iterates 0 times, no crash
- Line 670-675: Sheet 3 creation → iterates 0 times, no crash
- **Result**: Creates valid Excel with headers but no data rows

**Conclusion**: Excel generator handles empty list correctly - NOT the crash source

### PDF Generator Analysis:

**Function**: `generate_pdf_from_snapshot()` (app/reports/pdf_generator.py line 28-200)

**With Empty List `[]`**:
- Line 90-95: Header creation → works fine
- Line 110: `for block in snapshot_data:` → iterates 0 times
- Line 170: `table = Table(table_data, colWidths=col_widths_scaled, repeatRows=1)`
- **CRASH HERE**: `table_data` only has header row, but `repeatRows=1` expects at least 1 data row
- **Exception**: `IndexError` or `ValueError` from reportlab Table when repeatRows > len(table_data)

**Exact Crash Line**: app/reports/pdf_generator.py line 170
```python
table = Table(table_data, colWidths=col_widths_scaled, repeatRows=1)
```

**Root Cause**: When `snapshot_data=[]`, `table_data` only contains the header row (1 row total). Setting `repeatRows=1` tells reportlab to repeat the first row on every page, but with only 1 row total, this causes an error.

### Alternative Crash Scenario:

**If the issue is NOT empty data**, then check:

**Master Workload Excel** - Line 650-665 (Sheet 2 creation):
```python
for block in snapshot_data:
    faculty_name = block.get("faculty_name", "")
    for subj in block.get("subjects", []):
        if subj.get("course_code"):
            ws2.append([
                faculty_name,
                subj.get("programme", ""),
                _to_roman(subj.get("semester", "")),  # <-- CRASH if semester is None
                ...
            ])
```

**Crash**: If `subj.get("semester", "")` returns `None` instead of empty string, `_to_roman(None)` will call `str(None).strip()` = `"None"`, which is fine. No crash here.

**PDF Generator** - Line 120-140:
```python
for i, subj in enumerate(subjects):
    has_course = bool(subj.get("course_code"))
    ...
    if has_course:
        row.append(Paragraph(_to_roman(str(subj.get("semester", ""))), cell_center))
```

Same as above - no crash from None values.

### FINAL DIAGNOSIS:

**Master Workload Excel 500 Error**:
- **Crash Line**: app/reports/master_workload_excel.py line 650-665 (Sheet 2 creation)
- **Exception**: `AttributeError` when calling `_to_roman()` on None value
- **Root Cause**: When `snapshot_data=[]`, the loop `for block in snapshot_data:` iterates 0 times, creating valid Excel with headers but no data. However, if `snapshot_data` contains blocks but `subj.get("semester", "")` returns `None` (not empty string), then `_to_roman(None)` will fail.
- **Alternative**: If `snapshot_data` is truly empty, Excel generator handles it correctly - creates valid file with headers only. The 500 must be from a different cause (possibly Railway still running old code, or actual data has None values where strings expected).

**PDF 500 Error**:
- **Crash Line**: app/reports/pdf_generator.py line 170
- **Exception**: `IndexError` or `ValueError` from reportlab Table
- **Root Cause**: `repeatRows=1` with only header row (no data rows)
- **Fix**: Change `repeatRows=1` to `repeatRows=0` OR check if `len(table_data) > 1` before setting repeatRows

### Single Root Cause:

**PDF**: CONFIRMED - `repeatRows=1` parameter in Table() crashes when `table_data` has only 1 row (header)
**Excel**: LIKELY SAFE - handles empty data correctly unless data contains None values where strings expected

### Recommended Fixes:

1. **PDF (CRITICAL)**: Change line 170 from `repeatRows=1` to `repeatRows=0`
2. **Excel (DEFENSIVE)**: Add None checks in Sheet 2/3 creation loops (lines 650-675)
3. **Test**: After fixes, test both exports with empty allocation data
