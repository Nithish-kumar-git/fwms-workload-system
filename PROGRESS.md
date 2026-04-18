# Shift 2 Subjects Fix - ROOT CAUSE FOUND

## Diagnostic Results

### Window Status
- **Window is OPEN** ✓
- Window ID: 225
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

**This is NOT a filter issue. This is a DATA issue.**

The subjects literally don't exist with shift=2 in the database for the open semesters.

## Why SHIFT2 Staff See Empty Catalog

1. Frontend calls `GET /api/reports/subject-summary`
2. Backend returns 82 offerings, ALL with `shift=1`
3. Frontend has NO shift filter (correct for CASE 3)
4. But SHIFT2 staff expect to see shift=2 offerings
5. Since NO shift=2 offerings exist, they see nothing

## The Misunderstanding

**Previous Analysis Said**: "CASE 3 - One set of offerings for both shifts"

**Reality**: The database SHOULD have one set of offerings, but:
- Only 82 offerings exist for open semesters (II, IV, VI)
- ALL 82 have `shift=1`
- ZERO have `shift=2`

**For CASE 3 to work correctly**, SHIFT2 staff should be able to select from the SAME shift=1 offerings. But the user reports they see NOTHING, which means either:
1. The frontend IS filtering by shift (contradicts our code review)
2. The user expectation is that shift=2 offerings should exist separately
3. There's a mismatch between what the system shows and what users expect

## Next Steps Required

**CRITICAL DECISION NEEDED FROM USER**:

**Option A**: CASE 3 is correct - One set of offerings for both shifts
- SHIFT2 staff SHOULD see the 82 shift=1 offerings
- If they're seeing nothing, there's a frontend bug we haven't found
- Need to verify: Do SHIFT1 staff see the 82 offerings?

**Option B**: Institution needs separate shift=2 offerings
- Create duplicate offerings with shift=2 for the same subjects
- This means 82 shift=1 + 82 shift=2 = 164 total offerings
- Shift differentiation happens at OFFERING level, not just STAFF level

## Git Commits
- 8bdcbbd: feat: add staff catalog test and window status endpoints

## Files to Check Next
1. Verify SHIFT1 staff can see the 82 offerings
2. Check if frontend has hidden shift filter we missed
3. Confirm user expectation: Should shift=2 offerings exist separately?
