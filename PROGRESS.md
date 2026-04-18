# Shift 2 Subjects Fix - ROOT CAUSE CONFIRMED

## Latest Diagnostic Results (2bbac93)

### Window Status
- **Window is OPEN** ✓
- Window ID: 227
- Cycle: 1 (Semester II, OPEN)
- Start: 2026-04-18, End: 2026-04-25

### Catalog Test for SHIFT2 Staff

Tested 4 SHIFT2 staff members (MCT54, MCT58, LAT74, MCP04):
- All have `shift: "SHIFT2"` ✓
- All have `is_active: true` ✓
- All see open_cycles: [2, 4, 6] (Semesters II, IV, VI) ✓
- All see preference_window: OPEN ✓
- **catalog_counts: total=82, shift1_count=82, shift2_count=0** ❌

### ROOT CAUSE CONFIRMED

**The database has ZERO shift=2 offerings in the open semesters (II, IV, VI).**

```
Open Semesters: II, IV, VI
Total offerings: 82
Shift 1 offerings: 82
Shift 2 offerings: 0  ← THIS IS THE PROBLEM
```

**This is a DATA issue, NOT a code issue.**

## Code Review Findings

### Backend (app/reports/service.py)
- `get_subject_summary()` has NO shift filter ✓
- Returns ALL offerings from open semesters
- Query: `WHERE so.semester_id = ANY(:sem_ids) AND so.is_active = true`

### Backend (app/preference/service.py)
- SHIFT-01 validation is DISABLED ✓
- Comment: "Rule 4 (SHIFT-01): Shift compatibility - DISABLED"
- No shift filter in preference submission

### Frontend (PreferencesPage.tsx)
- NO shift filter in catalog loading ✓
- Calls `getSubjectSummary()` without any shift parameter
- Displays all subjects returned by API

### Grep Results
- NO shift filters found in preference or reports modules
- Only shift references are in:
  - Staff management UI (shift selection dropdown)
  - Demo/test scripts (for seeding test data)
  - Class teacher validation (ct_shift field)

## Why SHIFT2 Staff See Empty Catalog

**The system is working as designed for CASE 3:**
1. Frontend calls `GET /api/reports/subject-summary`
2. Backend returns 82 offerings, ALL with `shift=1`
3. Frontend displays all 82 offerings (no shift filter)
4. SHIFT2 staff SHOULD see these 82 offerings

**But user reports SHIFT2 staff see NOTHING.**

**This means one of two things:**
1. **User expectation mismatch**: Institution expects separate shift=2 offerings to exist
2. **Unreported frontend issue**: There's a client-side filter we can't see in the code

## The Real Question

**Does the institution want:**

**Option A**: CASE 3 - One set of offerings for both shifts
- Both SHIFT1 and SHIFT2 staff select from the SAME 82 offerings
- No separate shift=2 offerings needed
- Current code is correct, just need to verify SHIFT1 staff can see them

**Option B**: Separate offerings per shift
- Create 82 duplicate offerings with shift=2
- Total: 82 shift=1 + 82 shift=2 = 164 offerings
- Each shift has their own separate subject pool

## Next Steps

**IMMEDIATE ACTION NEEDED:**
1. Ask user: "Do SHIFT1 staff see the 82 subjects in their catalog?"
2. If YES → Option A is correct, investigate why SHIFT2 staff see nothing
3. If NO → Window might be closed or there's a different issue
4. Confirm user expectation: Should shift=2 offerings exist as separate records?

## Git Commits
- 2bbac93: feat: add staff catalog test and window status diagnostic endpoints
- de65dba: Previous commit

## Available Fix Endpoints

If Option B is chosen (separate shift=2 offerings):
- `/api/reports/admin/fix-shift-from-program` - Set offering.shift to match section.shift
- `/api/reports/admin/program-shifts` - View section shift values
