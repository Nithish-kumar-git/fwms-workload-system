# StaffPage UI Update - Remove Role Column, Add CT Column

## Commit: 2222980
**Message**: "StaffPage: remove Role column, add CT column for all staff"
**Status**: Pushed to origin/main

## Changes Made

### REMOVED: "Roles" Column
- Removed `<th>Roles</th>` header from table
- Removed entire `<td>` cell that displayed:
  - Role badge (HOD/TT Coordinator/Faculty with colored backgrounds)
  - CT info badge below role badge
  - Complex nested div structure with conditional rendering

### ADDED: "CT Assignment" Column
- Added `<th>CT Assignment</th>` header after Designation column
- New `<td>` cell for EVERY staff row with:
  - **For Class Teachers** (is_class_teacher === true AND ct_program not null/empty):
    - Shows: `{ct_program} · Sec {ct_section} · Sem {ct_semester}`
    - Style: Yellow pill badge (background #fef3c7, color #92400e, border #fde68a)
    - Font size: 11px, padding: 2px 8px, border-radius: 6px
  - **For Non-Class Teachers**:
    - Shows: "—" (em dash)
    - Style: Muted gray color (#9ca3af)
- Column is ALWAYS visible for every staff member (not conditional)

## TypeScript Check
```
cd frontend && npx tsc --noEmit 2>&1
(empty output - zero errors)
Exit Code: 0
```

## Git Status
- All changes committed and pushed
- Branch: main (up to date with origin/main)
- Working tree clean

## Table Structure Now
| Emp Code | Name | Designation | CT Assignment | Status | Actions |
|----------|------|-------------|---------------|--------|---------|

## Result
- Cleaner table layout without role badges
- CT assignments are now prominently displayed in dedicated column
- Easy to scan which staff are class teachers and their assignments
- Non-CT staff show clear "—" indicator instead of empty space



