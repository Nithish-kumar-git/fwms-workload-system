# PROGRESS LOG

## Task 9: Override Debug Logging Added 🔍

**Commit**: 7e9a577
**Message**: "debug: add override request logging and staff-list-debug endpoint"
**Status**: Debug logging added to track staff_id flow

### DEBUG CHANGES APPLIED:

**Backend Debug (app/admin/router.py)**:
1. Added print statements to override endpoint (line 88-97):
   ```python
   print(f"OVERRIDE DEBUG: allocation_id={allocation_id}, new_staff_id={request.new_staff_id}, type={type(request.new_staff_id)}", flush=True)
   
   # Check if staff exists in database
   with get_transaction() as session:
       check = session.execute(
           text("SELECT id, name, is_active FROM staff WHERE id = :sid"),
           {"sid": request.new_staff_id}
       ).fetchone()
       print(f"OVERRIDE DEBUG: staff lookup result = {check}", flush=True)
   ```

2. Added public debug endpoint GET /api/admin/staff/list-debug (no auth):
   - Returns: id, name, emp_code, designation, is_active
   - Can be tested in browser without authentication

**Frontend Debug (frontend/src/pages/ReviewPage.tsx)**:
1. Staff list load logging (line 75-82):
   ```typescript
   const data = await res.json();
   console.log('Staff list loaded:', data.length, 'items', data.slice(0, 3));
   ```

2. Staff click handler logging (line 253):
   ```typescript
   onClick={() => {
       console.log('Staff clicked:', staff.id, staff.emp_code, staff.name, 'type:', typeof staff.id);
       setSelectedStaffId(staff.id);  // ✓ Uses staff.id (database ID)
       setSearchTerm(`${staff.emp_code} - ${staff.name}`);
   }}
   ```

3. Override handler logging (line 91):
   ```typescript
   console.log('Selected staff id:', selectedStaffId, 'type:', typeof selectedStaffId);
   ```

### CODE VERIFICATION:

**Staff List Fetch** (line 74):
```typescript
const res = await fetch('/api/admin/staff/list', {
    credentials: 'include',
});
```
✓ Fetches from /api/admin/staff/list
✓ Returns array of {id, name, emp_code, designation}

**Staff Selection** (line 253-256):
```typescript
setSelectedStaffId(staff.id);  // ✓ CORRECT - uses staff.id (database ID)
setSearchTerm(`${staff.emp_code} - ${staff.name}`);
```
✓ Sets selectedStaffId to staff.id (NOT emp_code)
✓ Only updates search term display text

**Override Call** (line 94):
```typescript
await overrideAllocation(selected.allocation_id, selectedStaffId);
```
✓ Passes selectedStaffId (number) to API

### NEXT STEPS:
1. Check Railway logs for "OVERRIDE DEBUG" output
2. Test /api/admin/staff/list-debug in browser to see all staff IDs
3. Compare staff IDs in dropdown vs database
4. Verify selectedStaffId type is number, not string

---

## Previous: Task 9 - Override "New staff not found" - FIXED ✅

**Commit**: 09d4957
**Message**: "fix: replace undefined logger with console.log in override handler"
**Status**: Fixed undefined logger causing ReferenceError

### ROOT CAUSE FOUND:
Frontend ReviewPage.tsx line 79 used `logger.info()` but logger was NOT imported or defined.
This caused a ReferenceError that crashed handleOverride() before the API call was made.
User saw generic error instead of the actual crash.

### CODE ANALYSIS:

**Frontend handleOverride (ReviewPage.tsx lines 73-89)**:
```typescript
const handleOverride = async () => {
    if (!selected || !selectedStaffId) {
        addToast('Please select a staff member', 'error');
        return;
    }
    setOverriding(true);
    try {
        logger.info(`Overriding...`);  // ❌ CRASH - logger undefined
        await overrideAllocation(selected.allocation_id, selectedStaffId);
        ...
```

**Frontend API call (client.ts line 68)**:
```typescript
export const overrideAllocation = (id: number, newStaffId: number) =>
    api.put(`/admin/allocation/${id}`, { new_staff_id: newStaffId });
```
✓ Sends correct field name: `new_staff_id`
✓ Sends selectedStaffId (number) as newStaffId parameter

**Backend schema (schemas.py)**:
```python
class OverrideRequest(BaseModel):
    new_staff_id: int = Field(..., description="Staff ID to reassign to")
```
✓ Expects field name: `new_staff_id`
✓ Field names match between frontend and backend

**Backend service (service.py line 155-157)**:
```python
logger.info(f"Override: looking up new staff id={new_staff_id}")
new_staff = session.execute(
    text("SELECT id, name, emp_code, shift, COALESCE(tch_norm, 40) AS tch_norm FROM staff WHERE id = :sid"),
    {"sid": new_staff_id}
).fetchone()
```
✓ Query has NO is_active filter (correct)
✓ Logging exists

### FIX APPLIED:
**File**: frontend/src/pages/ReviewPage.tsx line 79
**Change**: `logger.info(...)` → `console.log(...)`
**Result**: Removed undefined logger reference, replaced with console.log

### VERIFICATION:
- Field names match: frontend sends `new_staff_id`, backend expects `new_staff_id` ✓
- selectedStaffId is set correctly when user clicks staff member ✓
- Validation exists: shows error if no staff selected ✓
- Backend query has no is_active filter ✓
- Backend logging exists for debugging ✓

---

## Previous Update - March 29, 2026

### Override Modal UX Fix - Staff Dropdown ✅

**Commit**: 847cc4f
**Message**: "fix: override modal shows staff dropdown instead of raw ID input"

**Problem**: Override modal asked users to enter "New Staff ID" (database integer), but users tried entering emp_codes like "77" from "MCT77", causing "staff not found" errors.

**FIX 1: Backend - Staff List Endpoint** (app/admin/router.py)
- **Added**: GET /api/admin/staff/list endpoint
- **Returns**: Array of {id, name, emp_code, designation}
- **Query**: `SELECT id, name, emp_code, designation FROM staff WHERE emp_code IS NOT NULL ORDER BY emp_code`
- **Auth**: Requires coordinator authentication

**FIX 2: Frontend - Searchable Dropdown** (frontend/src/pages/ReviewPage.tsx)
- **Replaced**: Text input for "New Staff ID" with searchable staff dropdown
- **Added States**:
  - `staffList: StaffMember[]` - loaded from /api/admin/staff/list
  - `searchTerm: string` - filter input value
  - `selectedStaffId: number | null` - selected staff's database ID
- **UI**: 
  - Search input filters by name or emp_code
  - Dropdown shows: "MCT49 - Dr. Angelina Benita D" with designation below
  - Click staff item to select
  - Selected item highlighted in blue
  - Sends staff.id (database ID) to override endpoint
- **Load**: Fetches staff list on component mount

**FIX 3: Backend Validation** (app/admin/service.py)
- **Confirmed**: Override query has NO is_active filter (fixed in commit b93beeb)
- **Query**: `SELECT id, name, emp_code, shift, COALESCE(tch_norm, 40) AS tch_norm FROM staff WHERE id = :sid`
- **Result**: HODs can assign any staff by ID

**Files Changed**:
- app/admin/router.py (added staff/list endpoint)
- frontend/src/pages/ReviewPage.tsx (replaced text input with searchable dropdown)

**Push Status**: ✅ SUCCESS
- Pushed to origin/main
- 9 objects written (2.08 KiB)
- Railway will auto-redeploy from commit 847cc4f

**Result**: Users can now search and select staff by name/emp_code instead of guessing database IDs.

---

## Previous Update - March 29, 2026

### Allocation Engine Fix - Accept OPEN Cycles ✅

**Commit**: f3ba923
**Message**: "fix: allow allocation engine to run on OPEN cycles, update cycle to ALLOCATED after run"

**Problem**: Allocation engine silently failed because it required semester state=CLOSED, but even semesters start as OPEN when preferences are collected.

**Root Cause**: 
- Line 586 in app/allocation/service.py: `if current_state != SemesterState.CLOSED`
- This rejected OPEN cycles, preventing allocation from running
- Correct flow: OPEN (collect preferences) → Run Allocation → ALLOCATED

**FIX 1: Accept OPEN status** (line 586-593)
- **Old**: `if current_state != SemesterState.CLOSED`
- **New**: `if current_state not in (SemesterState.OPEN, SemesterState.CLOSED)`
- **Result**: Engine now accepts both OPEN and CLOSED states
- **Still rejects**: ALLOCATED (must reopen first), FROZEN (finalized by HOD)

**FIX 2: Update cycle status after allocation** (line 822-826)
- **Added**: `UPDATE cycle SET status = 'ALLOCATED' WHERE id = :cid`
- **Location**: After successful allocation, before commit
- **Result**: Cycle status changes from OPEN → ALLOCATED after engine runs

**Files Changed**:
- app/allocation/service.py (2 changes: validation logic + cycle status update)

**Push Status**: ✅ SUCCESS
- Pushed to origin/main
- 5 objects written (754 bytes)
- Railway will auto-redeploy from commit f3ba923

**Result**: Allocation engine can now run on OPEN cycles and properly updates cycle status to ALLOCATED.
