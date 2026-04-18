# Shift 2 Subjects Fix - Root Cause Found

## Diagnostic Results

### Window Status
- **Window is OPEN** ✓
- Window ID: 224
- Start: 2026-04-18T19:20:12
- End: 2026-04-25T19:20:12
- Cycle: 1 (Semester II, status=OPEN)

### Catalog Test for SHIFT2 Staff (MCT54, MCT58)
- **Staff exists and is_active=true** ✓
- **Open cycles exist**: Semesters 2, 4, 6 ✓
- **Preference window is OPEN** ✓
- **Catalog returns 82 subjects** ✓
  - shift1_count: 82
  - shift2_count: 0
- **Existing preferences**: 0 (none submitted yet)

### Backend Analysis
- `/api/reports/subject-summary` endpoint:
  - Requires authentication: `staff_id: int = Depends(get_current_staff_id)` ✓
  - Does NOT filter by shift ✓
  - Returns all subjects from OPEN cycles ✓
  - Query confirmed working (82 subjects available)

### Frontend Analysis (`PreferencesPage.tsx`)
- Calls `getSubjectSummary()` which hits `/api/reports/subject-summary`
- NO shift filter in `filteredOfferings` ✓
- Only filters by program, semester, and search text ✓
- Console logs show: `res.data.records`

## Root Cause: AUTHENTICATION OR DATA STRUCTURE ISSUE

**The backend IS returning 82 subjects for open semesters.**
**The window IS open.**
**No shift filters exist in backend or frontend.**

**Possible causes**:
1. **Frontend receives empty `records` array** - API returns `{total: 82, records: []}` but records is empty
2. **Authentication issue** - SHIFT2 staff JWT token is invalid or missing staff_id
3. **API response structure mismatch** - Frontend expects different field names

## Next Steps

Need to check:
1. What does `/api/reports/subject-summary` actually return when called by a SHIFT2 staff member?
2. Is the `records` array populated or empty?
3. Are there any errors in the browser console when SHIFT2 staff loads the page?

## Git Commits
- dda6b1f: feat: add staff catalog test and window status endpoints
- 0582f22: fix: correct table name to selection_window in diagnostic endpoints

## Hypothesis

The `get_subject_summary()` function in `app/reports/service.py` filters by `open_sem_ids` which are [2, 4, 6].
But the diagnostic shows only 82 subjects for these semesters, not 1046.

**This means most subjects are NOT in semesters 2, 4, 6!**

Let me check which semesters the 1046 subjects are actually in.
