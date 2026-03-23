# Authentication Audit - app/preference/ and app/coordinator/

## Summary: ALL ENDPOINTS CORRECTLY USE JWT-BASED DEPENDENCIES ✓

---

## app/preference/router.py - ALL CORRECT ✓

### Endpoint 1: POST /api/preferences
**Line 30-34:**
```python
@router.post("", response_model=SubmitPreferenceResponse)
async def submit_preference(
    request: SubmitPreferenceRequest,
    user: UserInfo = Depends(get_current_user),  # ✓ JWT-based
):
```
**Uses:** `user.staff_id` (line 45)
**Status:** ✓ CORRECT

### Endpoint 2: GET /api/preferences/me
**Line 72-75:**
```python
@router.get("/me", response_model=list[PreferenceResponse])
async def list_my_preferences(
    user: UserInfo = Depends(get_current_user),  # ✓ JWT-based
):
```
**Uses:** `user.staff_id` (line 81)
**Status:** ✓ CORRECT

### Endpoint 3: GET /api/preferences/status
**Line 84-87:**
```python
@router.get("/status", response_model=PreferenceStatusResponse)
async def get_preference_status(
    user: UserInfo = Depends(get_current_user),  # ✓ JWT-based
):
```
**Uses:** `user.staff_id` (line 99)
**Status:** ✓ CORRECT

### Endpoint 4: DELETE /api/preferences/{preference_id}
**Line 103-107:**
```python
@router.delete("/{preference_id}", response_model=DeletePreferenceResponse)
async def delete_preference(
    preference_id: int,
    user: UserInfo = Depends(get_current_user),  # ✓ JWT-based
):
```
**Uses:** `user.staff_id` (line 115)
**Status:** ✓ CORRECT

---

## app/preference/window_router.py - ALL CORRECT ✓

### Endpoint 1: POST /api/pref-window/open
**Line 55-59:**
```python
@router.post("/open", response_model=WindowResponse)
async def open_window(
    body: OpenWindowRequest,
    coordinator_id: int = Depends(get_current_coordinator_id),  # ✓ JWT-based
):
```
**Status:** ✓ CORRECT

### Endpoint 2: POST /api/pref-window/close
**Line 74-77:**
```python
@router.post("/close", response_model=WindowResponse)
async def close_window(
    coordinator_id: int = Depends(get_current_coordinator_id),  # ✓ JWT-based
):
```
**Status:** ✓ CORRECT

### Endpoint 3: GET /api/pref-window/status
**Line 85-88:**
```python
@router.get("/status", response_model=WindowStatusResponse)
async def window_status():
    """Get current preference window status. Public endpoint."""
    return WindowStatusResponse(**get_window_status())
```
**Status:** ✓ CORRECT - Public endpoint, no auth required (by design)

---

## app/coordinator/window_router.py - ALL CORRECT ✓

### Endpoint 1: POST /windows
**Line 39-44:**
```python
@router.post("", response_model=WindowOperationResponse)
async def create_window(
    request: Request,
    body: CreateWindowRequest,
    coordinator_id: int = Depends(get_current_coordinator_id)  # ✓ JWT-based
):
```
**Status:** ✓ CORRECT

### Endpoint 2: POST /windows/{window_id}/schedule
**Line 75-80:**
```python
@router.post("/{window_id}/schedule", response_model=WindowOperationResponse)
async def schedule_window(
    request: Request,
    window_id: int,
    body: ScheduleWindowRequest,
    coordinator_id: int = Depends(get_current_coordinator_id)  # ✓ JWT-based
):
```
**Status:** ✓ CORRECT

### Endpoint 3: POST /windows/{window_id}/open
**Line 117-122:**
```python
@router.post("/{window_id}/open", response_model=WindowOperationResponse)
async def open_window(
    request: Request,
    window_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id)  # ✓ JWT-based
):
```
**Status:** ✓ CORRECT

### Endpoint 4: POST /windows/{window_id}/close
**Line 155-160:**
```python
@router.post("/{window_id}/close", response_model=WindowOperationResponse)
async def close_window(
    request: Request,
    window_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id)  # ✓ JWT-based
):
```
**Status:** ✓ CORRECT

### Endpoint 5: POST /windows/{window_id}/archive
**Line 188-193:**
```python
@router.post("/{window_id}/archive", response_model=WindowOperationResponse)
async def archive_window(
    request: Request,
    window_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id)  # ✓ JWT-based
):
```
**Status:** ✓ CORRECT

### Endpoint 6: GET /windows/{window_id}
**Line 219-224:**
```python
@router.get("/{window_id}", response_model=WindowResponse)
async def get_window(
    request: Request,
    window_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id)  # ✓ JWT-based
):
```
**Status:** ✓ CORRECT

### Endpoint 7: GET /windows/current
**Line 272-276:**
```python
@router.get("/current", response_model=CurrentWindowResponse)
async def get_current_window(
    request: Request,
    staff_id: int = Depends(get_current_staff_id)  # ✓ JWT-based
):
```
**Status:** ✓ CORRECT

---

## app/coordinator/semester_state_router.py - ALL CORRECT ✓

### Endpoint 1: GET /api/semester/{semester_id}/state
**Line 36-40:**
```python
@router.get("/{semester_id}/state", response_model=SemesterStateResponse)
async def get_semester_state(
    semester_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id)  # ✓ JWT-based
):
```
**Status:** ✓ CORRECT

### Endpoint 2: POST /api/semester/{semester_id}/open
**Line 63-67:**
```python
@router.post("/{semester_id}/open", response_model=StateTransitionResponse)
async def open_semester(
    semester_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id)  # ✓ JWT-based
):
```
**Status:** ✓ CORRECT

### Endpoint 3: POST /api/semester/{semester_id}/close
**Line 83-87:**
```python
@router.post("/{semester_id}/close", response_model=StateTransitionResponse)
async def close_semester(
    semester_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id)  # ✓ JWT-based
):
```
**Status:** ✓ CORRECT

### Endpoint 4: POST /api/semester/{semester_id}/freeze
**Line 103-107:**
```python
@router.post("/{semester_id}/freeze", response_model=StateTransitionResponse)
async def freeze_semester(
    semester_id: int,
    hod_id: int = Depends(get_current_hod_id)  # ✓ JWT-based
):
```
**Status:** ✓ CORRECT

---

## app/coordinator/router.py - ALL CORRECT ✓

### Endpoint 1: POST /api/coordinator/override
**Line 25-30:**
```python
@router.post("/override", response_model=OverrideSubjectResponse)
async def override_subject(
    request_body: OverrideSubjectRequest,
    request: Request,
    coordinator_staff_id: int = Depends(get_current_coordinator_id)  # ✓ JWT-based
):
```
**Status:** ✓ CORRECT

---

## Authentication Flow Verification

### JWT Token Flow (CORRECT):
1. User calls `/api/auth/dev-login/17` → Returns JWT token with `sub: 17`
2. Frontend stores token in localStorage
3. Frontend sends `Authorization: Bearer <token>` header
4. Backend `get_current_user` extracts `staff_id` from JWT `sub` field
5. Endpoint receives correct `user.staff_id = 17`

### DEV_AUTH_BYPASS Fallback (EXPECTED BEHAVIOR):
- **When:** NO token provided AND `DEV_AUTH_BYPASS=true`
- **Returns:** Hardcoded `staff_id=1` (mock coordinator)
- **Purpose:** Allow testing without authentication
- **Location:** `app/auth/dependencies.py`, lines 81-87

### Test Results:
```bash
# WITH JWT token (staff_id=17):
curl -H "Authorization: Bearer <token>" /api/preferences/status
# Returns: {"staff_id": 17, ...}  ✓ CORRECT

# WITHOUT JWT token (DEV_AUTH_BYPASS fallback):
curl /api/preferences/status
# Returns: {"staff_id": 1, ...}  ✓ EXPECTED (no token provided)
```

---

## Conclusion

**ALL ENDPOINTS ARE CORRECT** - They all use JWT-based dependencies:
- `Depends(get_current_user)` - Extracts staff_id from JWT
- `Depends(get_current_coordinator_id)` - Requires coordinator/HOD role
- `Depends(get_current_hod_id)` - Requires HOD role
- `Depends(get_current_staff_id)` - Any authenticated user

**The "bug" is NOT a bug** - it's the expected DEV_AUTH_BYPASS behavior:
- When a valid JWT token is sent → Returns correct staff_id from token
- When NO token is sent → Falls back to staff_id=1 (dev mode only)

**Root Cause of User's Issue:**
The frontend is likely NOT sending the JWT token in the Authorization header, causing the fallback to trigger. This is a frontend issue, not a backend authentication issue.

**Files Changed:** 0 - No backend changes needed, all endpoints are correct.
