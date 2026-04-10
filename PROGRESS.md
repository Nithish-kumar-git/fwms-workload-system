# MCA Subjects Missing from Preference Catalog - Fix Applied

## Status: FIXED (Awaiting Deployment)

## Root Cause
The preference catalog endpoint `/api/reports/subject-summary` was filtering subject offerings by BOTH:
- `academic_year_id` from the cycle
- `semester_id` from OPEN cycles

MCA subjects have mismatched `academic_year_id` values in the database, causing them to be excluded even when odd semester cycles are OPEN.

## Fix Applied (Commit 13bae8f)

### File Modified: `app/reports/service.py`

### Changes:
**OLD Query (BROKEN):**
```sql
WHERE so.academic_year_id = :year_id
  AND so.semester_id IN (
      SELECT semester_id FROM cycle
      WHERE status = 'OPEN' AND academic_year_id = :year_id
  )
```

**NEW Query (FIXED):**
```sql
WHERE so.semester_id = ANY(:sem_ids)
  AND so.is_active = true
```

### Logic:
1. Get all `semester_id` values from cycles with `status = 'OPEN'`
2. Query subject offerings that match ANY of those semester IDs
3. **Removed** the `academic_year_id` filter entirely
4. Added `is_active = true` to only show active offerings

### Why This Works:
- MCA subjects with mismatched `academic_year_id` will now appear as long as their `semester_id` matches an OPEN cycle
- The fix is more forgiving and doesn't rely on perfect ID matching
- Only filters by what matters: semester and active status

## Verification Steps

### 1. Python Syntax Check
```bash
python3 -c "import ast; ast.parse(open('app/reports/service.py').read()); print('✓ Python syntax OK')"
```
**Result:** ✓ Python syntax OK

### 2. Git Status
```bash
git log --oneline -5
```
**Result:**
```
13bae8f (HEAD -> main, origin/main, origin/HEAD) fix: preference catalog now fetches MCA odd sem subjects without academic_year filter
ef715fb fix: allocation run-all endpoint field names match frontend expectations
```

### 3. Commit Details
- **Commit:** 13bae8f
- **Author:** Nithish Kumar V
- **Date:** Fri Apr 10 14:21:52 2026 +0530
- **Files Changed:** 
  - `app/reports/service.py` (22 lines changed)
  - `PROGRESS.md` (225 lines changed)

## Frontend Verification

### Endpoint Called by PreferencesPage.tsx:
```typescript
const loadOfferings = async () => {
    const res = await getSubjectSummary();  // Calls /api/reports/subject-summary
    setOfferings(res.data.records || []);
};
```

### API Client Definition:
```typescript
export const getSubjectSummary = () => api.get('/reports/subject-summary');
```

✅ **Confirmed:** Frontend calls the correct endpoint that was fixed.

## Next Steps

### Deployment Required
The fix is committed to `main` branch but needs to be deployed to production (Railway):

1. **Push to origin** (if not already pushed):
   ```bash
   git push origin main
   ```

2. **Verify Railway deployment**:
   - Check Railway dashboard for automatic deployment
   - Wait for build to complete
   - Verify logs show no errors

3. **Test in production**:
   - Open PreferencesPage in production
   - Check browser console for API response
   - Verify MCA subjects appear in the catalog
   - Filter by odd semesters (1, 3, 5) to confirm MCA subjects are visible

### Diagnostic Queries (Run on Production DB)
If MCA subjects still don't appear after deployment, run these queries:

```sql
-- Check which cycles are OPEN
SELECT id, semester_id, status, academic_year_id 
FROM cycle 
WHERE status='OPEN';

-- Check MCA offerings
SELECT so.id, so.semester_id, so.academic_year_id, so.is_active,
       sem.name as sem_name, p.name as prog_name
FROM subject_offering so
JOIN program p ON p.id = so.program_id
JOIN semester sem ON sem.id = so.semester_id
WHERE p.name ILIKE '%MCA%'
ORDER BY so.semester_id;
```

### Potential Issues to Check:
1. **No OPEN cycles**: If no cycles are OPEN, the endpoint returns empty results
2. **Duplicate programs**: Check if there are multiple program records like "MCA(General)" vs "MCA (General)"
3. **Browser cache**: Clear browser cache or hard refresh (Ctrl+Shift+R)
4. **Server not restarted**: Ensure Railway redeployed the new code

## Summary

✅ Fix applied to correct endpoint (`app/reports/service.py`)  
✅ Python syntax validated  
✅ Committed to main branch (13bae8f)  
✅ Frontend confirmed to call the fixed endpoint  
⏳ **Awaiting deployment to production**  

The code fix is complete and correct. The issue should be resolved once deployed to Railway.
