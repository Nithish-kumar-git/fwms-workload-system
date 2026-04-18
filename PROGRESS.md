# Shift 2 Subjects Fix - Progress Report

## Root Cause: CASE A (REVISED)
**ACTUAL ROOT CAUSE**: The `section` table only contains Shift 1 sections. There are NO Shift 2 sections in the database.

## Final Diagnosis Results

### Section Table State
All 8 sections have `shift=1` (integer):
- A: 168 offerings
- B: 186 offerings  
- C: 147 offerings
- D: 139 offerings
- E: 129 offerings
- F: 124 offerings
- A+B: 80 offerings
- A+B+C: 73 offerings
**Total**: 1046 offerings, ALL with shift=1

### Staff Table State
Staff have shift values as strings: 'SHIFT1', 'SHIFT2', 'SHIFT1+SHIFT2'
- SHIFT2 staff exist: MCT54, MCT58, LAT74, MCT71, MCT75, MCP04
- SHIFT1+SHIFT2 staff exist: MCT69, MCT70, MCT78, MCT77, MCT76

### Subject Offering State
- All 1046 offerings have `shift=1`
- This is CORRECT because they inherit from `section.shift`
- The fix endpoint correctly set `subject_offering.shift = section.shift`

### Backend Analysis
- `app/reports/service.py` `get_subject_summary()`: NO shift filter ✓
- Query returns all subjects from OPEN cycles regardless of shift

### Frontend Analysis  
- `frontend/src/pages/PreferencesPage.tsx` `filteredOfferings`: NO shift filter ✓
- Only filters by program, semester, and search text

## Fix Attempt

### Endpoint: POST /admin/fix-shift-from-program
Set `subject_offering.shift` to match `section.shift` for every offering.

### Results
- **Offerings Updated**: 1046
- **Status**: SUCCESS
- **Distribution**: All offerings now have shift=1 (matching their sections)

## Conclusion
The fix cannot be applied at the `subject_offering` level because:
1. Shift 2 sections don't exist in the `section` table
2. `subject_offering.shift` correctly matches `section.shift` (all are 1)
3. The data model requires sections to be created for Shift 2 programs first

**The real issue**: The database schema has sections with integer shift values (1 only), but staff have string shift values ('SHIFT1', 'SHIFT2', 'SHIFT1+SHIFT2'). There's a mismatch in how shift is represented across tables.

## Git Commit
- **Hash**: 80af8c9
- **Message**: fix: set subject_offering.shift from section.shift correctly
- **Files Changed**: app/reports/router.py, call_proper_shift_fix.py

## Next Steps (Requires User Decision)
1. **Option A**: Create Shift 2 sections in the database (e.g., A-S2, B-S2, C-S2, etc.)
2. **Option B**: Confirm this institution only operates Shift 1 programs
3. **Option C**: Investigate if shift should be determined differently (by program or staff)
4. **Option D**: Change section.shift from integer to string to match staff.shift format
