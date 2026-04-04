# Staff Roles Fix - Migration 039

## Latest Commit
- **Hash**: 11ad6cb
- **Message**: "fix: set correct roles for HOD (MCT44) and TT Coordinator (MCT48) in DB"
- **Status**: Pushed to origin/main

## Problem
MCT44 (Dr. S. Gokila) had role='faculty' in database instead of 'hod'
MCT48 (Dr. Sathish Kumar M) needed role='tt_coordinator' confirmed

## Migration 039 Created
**File**: `migrations/039_fix_staff_roles.sql`

**SQL Updates**:
```sql
UPDATE staff SET role = 'hod' WHERE emp_code = 'MCT44';
UPDATE staff SET role = 'tt_coordinator' WHERE emp_code = 'MCT48';
```

## Changes Made

1. **Migration 039**: Created with UPDATE statements for both staff roles
2. **startup.sh**: Added `run_migration 039_fix_staff_roles.sql` after migration 038
3. **Debug Endpoint**: Changed LIMIT from 5 to 30 in `/api/admin/staff/debug-role-ct` to show all staff

## Python Syntax Check
- `app/admin/staff_service.py`: OK ✓
- `app/admin/router.py`: OK ✓

## Verification URLs
- **Debug Endpoint**: https://fwms-workload-system-production.up.railway.app/api/admin/staff/debug-role-ct
- **Expected**: MCT44 shows role='hod', MCT48 shows role='tt_coordinator'
- **Staff Page**: https://fwms-workload-system.vercel.app/hod/staff
- **Expected**: MCT44 shows blue HOD badge, MCT48 shows purple TT Coordinator badge

## Git Log
```
11ad6cb (HEAD -> main, origin/main) fix: set correct roles for HOD (MCT44) and TT Coordinator (MCT48) in DB
bdbb709 fix: CT badge string template, v2 marker to confirm deployment
1e68c50 fix: rewrite list_staff with clean SQL and dict mapping, remove is_coordinator
```

Railway will auto-run migration 039 on next deployment to fix the roles in production database.


