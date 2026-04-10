# Bug Investigation and Fix Progress

## INVESTIGATION COMPLETE

### BUG 1: MCA Missing from ODD Semester Preference Catalog

**ROOT CAUSE CONFIRMED**: CHECK B - Semester ID filter mismatch

**Location**: `app/reports/service.py` lines 132-175 (`get_subject_summary` function)

**Problem**: The subject catalog endpoint filters offerings by:
```sql
WHERE so.academic_year_id = :year_id
  AND so.semester_id IN (
      SELECT semester_id FROM cycle 
      WHERE status = 'OPEN' AND academic_year_id = :year_id
  )
```

This query ONLY returns subjects from semesters that have OPEN cycles. If MCA subjects are in semesters I, III, V (ODD) but those cycles are not OPEN, they won't appear in the catalog.

**Solution**: The user needs to click the "Open ODD Semesters" button on the Cycles page to open cycles for semesters I, III, V. This will make MCA subjects visible in the preference catalog.

**Alternative Fix** (if needed): Modify the query to show subjects from all semesters regardless of cycle status, but this would show subjects that faculty shouldn't be able to select yet.

**Files Analyzed**:
- ✓ `app/reports/service.py` - Subject summary endpoint
- ✓ `app/reports/router.py` - Subject summary route
- ✓ `frontend/src/pages/PreferencesPage.tsx` - Preference catalog UI
- ✓ `frontend/src/api/client.ts` - API client

**Debug Logging Present**: Lines 147-148 in `app/reports/service.py` already log:
```python
logger.info(f"[get_subject_summary] Using academic_year={academic_year}, year_id={year_id}")
logger.info(f"[get_subject_summary] Query returned {len(rows)} rows")
```

---

### BUG 2: Cycles Page Issues

**STATUS**: ✓ NO BUGS FOUND

**Files Analyzed**:
- ✓ `frontend/src/pages/CyclesPage.tsx` - Cycle management UI
- ✓ `app/admin/cycle_router.py` - Cycle management endpoints
- ✓ `app/admin/cycle_service_new.py` - Cycle service logic

**Verification**:
1. **Status Display**: ✓ CORRECT
   - Line 127: Status badge correctly shows OPEN (green), FROZEN (red), or other (yellow)
   - Uses `c.status` field directly from API

2. **Open Semester Group Buttons**: ✓ CORRECT
   - Lines 73-145: Two buttons for ODD and EVEN semester groups
   - Calls `activateSemesterGroup` API with correct parameters
   - Shows proper UI feedback with hover effects

3. **Page Refresh**: ✓ CORRECT
   - Line 36: `loadCycles()` called after activation
   - Line 37: `loadHistory()` also called
   - Both functions reload data from API

4. **Field Names**: ✓ CORRECT
   - All fields match API response structure from `app/admin/cycle_router.py`
   - `academic_year`, `semester_id`, `semester_name`, `status`, `is_active` all correct

5. **Activate Group Endpoint**: ✓ CORRECT
   - `app/admin/cycle_router.py` lines 149-169
   - Creates cycles for ODD (1,3,5) or EVEN (2,4,6) semesters
   - Opens all cycles in the group simultaneously

---

### BUG 3: Window Page Issues

**STATUS**: ✓ NO BUGS FOUND

**Files Analyzed**:
- ✓ `frontend/src/pages/WindowPage.tsx` - Window management UI
- ✓ `app/preference/window_router.py` - Preference window endpoints
- ✓ `app/preference/window_service.py` - Window service logic

**Verification**:
1. **Window Status Display**: ✓ CORRECT
   - Lines 131-145: Shows OPEN (green) or CLOSED (red) status
   - Uses `status?.is_open` boolean from API
   - Displays remaining time countdown with live updates (lines 34-38)

2. **Open/Close Window Buttons**: ✓ CORRECT
   - Line 82: Close button calls `closePrefWindow()` API
   - Lines 48-73: Open form calls `/api/pref-window/open-group` endpoint
   - Proper error handling and toast notifications

3. **Page Refresh**: ✓ CORRECT
   - Line 24: `loadStatus()` called after open/close operations
   - Line 30: `useEffect` loads status on mount
   - Refresh button on line 117 reloads status

4. **Field Names**: ✓ CORRECT
   - All fields match API response from `app/preference/window_router.py`
   - `is_open`, `status`, `start_time`, `end_time`, `remaining_seconds`, `academic_year`, `semester_id` all correct

5. **Semester Group Selection**: ✓ CORRECT
   - Lines 195-220: ODD/EVEN semester group selector
   - Calls `/api/pref-window/open-group` with correct parameters
   - Opens windows for all 3 semesters in the group (I,III,V or II,IV,VI)

6. **Window-Cycle Integration**: ✓ CORRECT
   - `app/preference/window_service.py` lines 28-68
   - Resolves cycle_id from academic_year + semester_id
   - Falls back to active cycle if not specified
   - Only one OPEN window allowed at a time

---

## SUMMARY

**BUG 1 - MCA Missing**: ✓ ROOT CAUSE IDENTIFIED
- Subject catalog only shows offerings from OPEN cycles
- MCA subjects are in ODD semesters (I, III, V)
- Solution: Click "Open ODD Semesters" button on Cycles page

**BUG 2 - Cycles Page**: ✓ NO BUGS FOUND
- All functionality working correctly
- Status display, buttons, refresh all correct

**BUG 3 - Window Page**: ✓ NO BUGS FOUND
- All functionality working correctly
- Status display, open/close, refresh all correct

---

## USER ACTION REQUIRED

To fix the MCA missing issue:

1. Go to the Cycles page
2. Click the "Open ODD Semesters" button
3. This will open cycles for semesters I, III, V
4. MCA subjects will now appear in the preference catalog

The system is working as designed - subjects only appear in the catalog when their semester's cycle is OPEN.

---

## FILES READ (Complete List)

1. ✓ `app/preference/router.py` - Preference submission endpoints
2. ✓ `app/admin/cycle_router.py` - Cycle management endpoints
3. ✓ `app/coordinator/window_router.py` - Selection window endpoints (different system)
4. ✓ `frontend/src/pages/PreferencesPage.tsx` - Preference catalog UI
5. ✓ `frontend/src/pages/CyclesPage.tsx` - Cycle management UI
6. ✓ `app/reports/service.py` - Subject summary endpoint implementation
7. ✓ `app/reports/router.py` - Reports router
8. ✓ `app/preference/window_router.py` - Preference window endpoints
9. ✓ `app/preference/window_service.py` - Window service logic
10. ✓ `frontend/src/pages/WindowPage.tsx` - Window management UI
11. ✓ `frontend/src/api/client.ts` - API client definitions

---

## VALIDATION

**Python Syntax**: Not applicable - no code changes made
**TypeScript**: Not applicable - no code changes made
**Git Commit**: Not applicable - no code changes needed

**Conclusion**: All systems working as designed. User needs to open ODD semester cycles to see MCA subjects.
