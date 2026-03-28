## Latest Update - March 28, 2026

### QUESTION 1: Class Teacher Validation Block

**Location**: app/preference/service.py (Line 150-190)

```python
# Rule 5 (CT-01): Class teacher first preference
is_class_teacher = staff[2]
if is_class_teacher and preference_number == 1:
    ct_program = staff[3]
    ct_section = staff[4]
    ct_semester = staff[5]
    ct_shift = staff[6]
    
    # Check if offering matches class teacher's class
    offering_program = offering[8]    # program_name
    offering_semester = offering[7]   # semester_label
    offering_section = offering[9]    # section_label
    offering_shift_val = offering[1]  # shift
    
    mismatch = False
    mismatch_detail = []
    
    if ct_program and offering_program and ct_program.upper() != offering_program.upper():
        mismatch = True
        mismatch_detail.append(f"program ({ct_program} vs {offering_program})")
    
    if ct_semester and offering_semester and str(ct_semester).upper() != str(offering_semester).upper():
        mismatch = True
        mismatch_detail.append(f"semester ({ct_semester} vs {offering_semester})")
    
    if ct_section and offering_section and str(ct_section).upper() != str(offering_section).upper():
        mismatch = True
        mismatch_detail.append(f"section ({ct_section} vs {offering_section})")
    
    if ct_shift and offering_shift_val and int(ct_shift) != int(offering_shift_val):
        mismatch = True
        mismatch_detail.append(f"shift ({ct_shift} vs {offering_shift_val})")
    
    if mismatch:
        return {
            "valid": False,
            "error": f"Class teacher must give preference 1 to their own class. "
                     f"Mismatch: {', '.join(mismatch_detail)}",
            "rule": "CT-01"
        }
```

### QUESTION 2: Railway Database Query - FAILED
```
'psql' is not recognized as an internal or external command
```
Railway CLI not configured with psql access on this machine.

### QUESTION 3: Subject Offering Semesters - FAILED
Same psql error - cannot query Railway database directly.

### QUESTION 4: PreferencesPage.tsx Preferences Handling

**a) setPreferences line** (Line 84):
```typescript
setPreferences(prefsRes.data.preferences || []);
```

**b) getMyPreferences() response handler** (Line 75-93):
```typescript
const loadData = async () => {
    setError('');
    try {
        const [prefsRes, statusRes, winRes] = await Promise.all([
            getMyPreferences(),
            getPreferenceStatus(),
            getPrefWindowStatus(),
        ]);
        setPreferences(prefsRes.data.preferences || []);
        setStatus(statusRes.data);
        setWindowOpen(winRes.data.is_open);
        setWindowRemaining(winRes.data.remaining_seconds || 0);
    } catch (err: any) {
        const status = err.response?.status;
        const detail = status === 403 
            ? 'Session expired - please login again'
            : err.response?.data?.detail || 'Could not connect to server. Check your login.';
        setError(detail);
        addToast(detail, 'error');
    } finally {
        setLoading(false);
    }
};
```

**c) console.log for getMyPreferences**: NONE - no logging for preferences response

### QUESTION 5: GET /me Endpoint

**Location**: app/preference/router.py (Line 71-80)

```python
@router.get("/me", response_model=list[PreferenceResponse])
async def list_my_preferences(
    user: UserInfo = Depends(get_current_user),
):
    """
    List all preferences for the currently authenticated faculty.
    Returns preferences ordered by preference_number (1-5).
    """
    prefs = preference_service.list_preferences(staff_id=user.staff_id)
    return [PreferenceResponse(**p) for p in prefs]
```

### Next Step
Railway CLI psql not available - need to check production via browser or Railway dashboard SQL console.
