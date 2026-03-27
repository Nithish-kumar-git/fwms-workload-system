## Latest Update - March 28, 2026

### QUESTION 1: app/reports/service.py functions

**_resolve_active_cycle()** (Line 26):
```python
def _resolve_active_cycle(session) -> tuple[str, int]:
    row = session.execute(
        text("""
            SELECT ay.name, c.semester_id
            FROM cycle c
            JOIN academic_year ay ON ay.id = c.academic_year_id
            WHERE c.status = 'OPEN'
            LIMIT 1
        """)
    ).fetchone()
    if not row:
        raise RuntimeError("No active cycle found. Activate a cycle before generating reports.")
    return row[0], row[1]
```

**get_subject_summary()** (Line 126):
```python
def get_subject_summary(academic_year: Optional[str] = None, semester_id: Optional[int] = None) -> dict:
    with get_transaction() as session:
        if academic_year is None or semester_id is None:
            academic_year, semester_id = _resolve_active_cycle(session)
        
        rows = session.execute(
            text("""
                SELECT so.id, sub.code, sub.name, p.name AS program,
                       sem.label AS semester, sec.label AS section,
                       s.name AS faculty_name, s.emp_code,
                       COALESCE(sub.tch, 0) AS tch,
                       CASE WHEN a.id IS NOT NULL THEN true ELSE false END AS allocated
                FROM subject_offering so
                JOIN subject sub ON sub.id = so.subject_id
                JOIN program p ON p.id = so.program_id
                JOIN semester sem ON sem.id = so.semester_id
                JOIN section sec ON sec.id = so.section_id
                LEFT JOIN allocation a ON a.subject_offering_id = so.id
                LEFT JOIN staff s ON s.id = a.staff_id
                WHERE so.academic_year = :year AND so.semester_id = :sem_id
                ORDER BY p.name, sem.label, sec.label, sub.code
            """),
            {"year": academic_year, "sem_id": semester_id}
        ).fetchall()
    return {"total": len(records), "records": records}
```

### QUESTION 2: app/preference/service.py functions

**submit_preference()** (Line 208):
- Checks cycle lock guard (require_cycle_unlocked)
- Checks window guard (is_window_open)
- Queries active cycle: `SELECT id FROM cycle WHERE status = 'OPEN' LIMIT 1`
- Validates preference (duplicate checks)
- Inserts into faculty_preference with cycle_id
- Logs to audit_log

**list_preferences()** (Line 312):
```python
def list_preferences(staff_id: int) -> list[dict]:
    from app.admin.cycle_service_new import get_active_cycle
    active_cycle = get_active_cycle()
    if not active_cycle:
        return []

    with get_transaction() as session:
        rows = session.execute(
            text("""
                SELECT fp.id, fp.staff_id, fp.subject_offering_id, fp.preference_number,
                       fp.submitted_at,
                       s.code AS subject_code, s.name AS subject_name,
                       sec.label AS section_label, sem.label AS semester_label,
                       p.name AS program_name
                FROM faculty_preference fp
                JOIN subject_offering so ON so.id = fp.subject_offering_id
                JOIN subject s ON s.id = so.subject_id
                JOIN section sec ON sec.id = so.section_id
                JOIN semester sem ON sem.id = so.semester_id
                JOIN program p ON p.id = so.program_id
                JOIN cycle c ON c.academic_year_id = so.academic_year_id 
                            AND c.semester_id = so.semester_id
                WHERE fp.staff_id = :staff_id
                  AND c.id = :cid
                ORDER BY fp.preference_number
            """),
            {"staff_id": staff_id, "cid": active_cycle["id"]}
        ).fetchall()
```

### QUESTION 3: Production API Tests

**curl /api/pref-window/status**:
```json
{
  "is_open": true,
  "status": "OPEN",
  "window_id": 8,
  "start_time": "2026-03-27 22:30:25.681409+00:00",
  "end_time": "2026-04-03 22:30:25.681409+00:00",
  "remaining_seconds": 604103,
  "academic_year": "2025-2026",
  "semester_id": 2
}
```

**curl /api/cycles/**:
FAILED - curl returned truncated output "les/"

### QUESTION 4: PreferencesPage.tsx sections

**submitPreference call** (handleSubmit function):
```typescript
const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!offeringId || !prefNum) return;

    const dupMsg = validateSelection(offeringId, prefNum);
    if (dupMsg) {
        setDuplicateError(dupMsg);
        addToast(dupMsg, 'error');
        return;
    }

    setSubmitting(true);
    setDuplicateError('');
    try {
        await submitPreference({
            subject_offering_id: parseInt(offeringId),
            preference_number: parseInt(prefNum),
        });
        addToast('Preference saved successfully', 'success');
        setOfferingId('');
        setPrefNum('');
        loadData();
        loadOfferings();
    } catch (err: any) {
        const msg = err.response?.data?.detail || 'Submission failed';
        addToast(msg, 'error');
        setDuplicateError(msg);
    } finally {
        setSubmitting(false);
    }
};
```

**"Your Preferences" slots** (1-5 display):
```typescript
{[1, 2, 3, 4, 5].map((n) => {
    const pref = preferences.find((p) => p.preference_number === n);
    return (
        <div key={n} style={{...}}>
            <span>{n}</span>
            {pref ? (
                <div>
                    <div>{pref.subject_name}</div>
                    <div>{pref.subject_code}</div>
                </div>
            ) : (
                <span>Empty</span>
            )}
            {pref && windowOpen && (
                <button onClick={() => handleDelete(pref.id)}>
                    <XCircle size={14} />
                </button>
            )}
        </div>
    );
})}
```

**loadPreferences()** - MISSING. Uses loadData() instead:
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
        const detail = err.response?.data?.detail || 'Could not connect to server. Check your login.';
        setError(detail);
        addToast(detail, 'error');
    } finally {
        setLoading(false);
    }
};
```

**loadOfferings()** function:
```typescript
const loadOfferings = async () => {
    setOfferingsLoading(true);
    try {
        const res = await getSubjectSummary();
        console.log('Subject Summary API Response:', res.data);
        console.log('Records count:', res.data.records?.length || 0);
        setOfferings(res.data.records || []);
    } catch (err) {
        console.error('Failed to load subject offerings:', err);
    } finally {
        setOfferingsLoading(false);
    }
};
```

### QUESTION 5: frontend/src/api/client.ts functions

**submitPreference**:
```typescript
export const submitPreference = (data: {
    subject_offering_id: number;
    preference_number: number;
}) => api.post('/preferences', data);
```

**getMyPreferences**:
```typescript
export const getMyPreferences = () => api.get('/preferences/me');
```

**Response interceptor** (401/403/409 handling):
```typescript
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response) {
            const status = error.response.status;
            if (status === 401 || status === 403) {
                console.warn(`Auth error ${status} on ${error.config?.url}`);
                // DO NOT clear localStorage — let AuthContext handle logout
            }
        } else if (error.request) {
            console.error('Server unavailable:', error.message);
        }
        return Promise.reject(error);
    }
);
```

### Next Step
Need to retry /api/cycles/ endpoint test - curl output was truncated.
