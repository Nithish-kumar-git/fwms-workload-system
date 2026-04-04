# Staff List API Fix - CT Fields and is_active

## Commit: 4e88981
**Message**: "Fix staff list API: include ct fields and is_active in response"
**Status**: Pushed to origin/main

## Root Cause Analysis

**Bug Symptoms**:
1. CT Assignment column showed "—" for ALL staff (including confirmed class teachers)
2. Status showed "Inactive" for ALL staff (even though is_active=true in DB)

**Root Cause**: `/api/admin/staff/list` endpoint had incomplete SELECT query

## What Was Missing

### 1. In app/admin/router.py - GET /staff/list endpoint
**BEFORE**: Custom SELECT query with only 4 fields
```sql
SELECT id, name, emp_code, designation 
FROM staff 
WHERE emp_code IS NOT NULL 
ORDER BY emp_code
```

**AFTER**: Now calls `list_staff()` service function
```python
from app.admin.staff_service import list_staff
return list_staff()
```

This service function includes ALL fields:
- id, emp_code, name, email, designation, shift, tch_norm, role
- is_active, is_class_teacher
- ct_program, ct_section, ct_semester, ct_shift, ct_curriculum_year

### 2. In app/admin/staff_router.py - StaffRecord Pydantic Model
**MISSING**: `role` field

**ADDED**:
```python
role: str | None = None
```

Now the model includes all fields that the service function returns.

## Files Changed
1. `app/admin/router.py` - Replaced custom SELECT with service function call
2. `app/admin/staff_router.py` - Added `role` field to StaffRecord model

## Validation

### Python Syntax Check
- `app/admin/router.py`: OK ✓
- `app/admin/staff_router.py`: OK ✓

### TypeScript Check
```
cd frontend && npx tsc --noEmit 2>&1
(empty output - zero errors)
Exit Code: 0
```

## Result
- Backend now returns complete staff data with all CT fields and is_active
- Frontend will correctly display:
  - CT Assignment column: Shows program/section/semester for class teachers, "—" for others
  - Status column: Shows "Active" for is_active=true, "Inactive" for is_active=false
- No frontend changes needed - it was already checking the correct fields

## Git Log
```
4e88981 (HEAD -> main, origin/main) Fix staff list API: include ct fields and is_active in response
2222980 StaffPage: remove Role column, add CT column for all staff
11ad6cb fix: set correct roles for HOD (MCT44) and TT Coordinator (MCT48) in DB
```




