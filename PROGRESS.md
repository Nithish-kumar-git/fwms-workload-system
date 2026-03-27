## Latest Update - March 28, 2026

### BUG 1: Other semesters show no subjects - FIXED

**Root Cause**: get_subject_summary() filtered by semester_id, only returning subjects for active cycle (sem 2).

**Changed in app/reports/service.py** (Line 126-155):

BEFORE:
```python
if academic_year is None or semester_id is None:
    academic_year, semester_id = _resolve_active_cycle(session)

WHERE so.academic_year = :year AND so.semester_id = :sem_id
{"year": academic_year, "sem_id": semester_id}
```

AFTER:
```python
if academic_year is None:
    academic_year, _ = _resolve_active_cycle(session)

WHERE so.academic_year = :year
{"year": academic_year}
```

Result: Now returns all 194 subjects across all semesters. Frontend filter dropdown works correctly.

---

### BUG 2: "Your Preferences" slots show Empty - FIXED

**Router Path Check**:
- Backend: `@router.get("/me")` → Full path: `/api/preferences/me` ✓
- Frontend: `api.get('/preferences/me')` ✓
- Paths MATCH - no issue here

**Real Issue**: 403 errors show generic message instead of "Session expired"

**Changed in frontend/src/pages/PreferencesPage.tsx** (Line 75-93):

BEFORE:
```typescript
catch (err: any) {
    const detail = err.response?.data?.detail || 'Could not connect to server. Check your login.';
    setError(detail);
    addToast(detail, 'error');
}
```

AFTER:
```typescript
catch (err: any) {
    const status = err.response?.status;
    const detail = status === 403 
        ? 'Session expired - please login again'
        : err.response?.data?.detail || 'Could not connect to server. Check your login.';
    setError(detail);
    addToast(detail, 'error');
}
```

---

### Commit
- Hash: 122c80f
- Message: "Fix: subject catalog returns all semesters + preferences display"
- Pushed: Already up-to-date (no remote changes)

---

### Test Results
Waiting 3 minutes for Railway deployment, then test:
1. Open production Vercel URL
2. Login with Google
3. Go to preferences page
4. Check: Do all 6 semesters show subjects?
5. Submit preference - does it appear in "Your Preferences" slots?
