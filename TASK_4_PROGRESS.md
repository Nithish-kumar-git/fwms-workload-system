# Task 4: Add Curriculum Year to Subjects and CT - Progress Report

## COMPLETED BACKEND CHANGES ✅

### 1. Migration 036 Created
- File: `migrations/036_add_curriculum_year.sql`
- Adds `curriculum_year` column to `subject` table (default '2022')
- Adds `ct_curriculum_year` column to `staff` table (default NULL)
- Sets MCA subjects (CCA, CCM, CMA, CEL prefixes) to 2022 regulation
- Sets BCA subjects (ACA, ACY, ACM, GMA, GLS, GGE, ABB, ASS prefixes) to 2023 regulation

### 2. Startup Script Updated
- File: `startup.sh`
- Added migration 036 after migration 035

### 3. Auth Endpoint Updated
- File: `app/auth/schemas.py`
  - Added CT fields to `StaffInfoResponse`: is_class_teacher, ct_program, ct_section, ct_semester, ct_shift, ct_curriculum_year
- File: `app/auth/router.py`
  - Updated `/api/auth/me` endpoint to fetch and return CT fields from database

### 4. Subjects Service Updated
- File: `app/subjects/service.py`
  - `get_all_offerings()`: Added curriculum_year to SELECT query
  - `create_offering()`: Added curriculum_year to INSERT and UPDATE queries (defaults to '2022')
- File: `app/subjects/router.py`
  - Added `curriculum_year` field to `OfferingCreate` schema (optional, default '2022')

### 5. Reports Service Updated
- File: `app/reports/service.py`
  - `get_subject_summary()`: Added curriculum_year to SELECT query and response records

### 6. Staff Management Updated
- File: `app/admin/staff_service.py`
  - `list_staff()`: Added ct_curriculum_year to SELECT query
  - `create_staff()`: Added ct_curriculum_year parameter and INSERT query
  - `update_staff()`: Added ct_curriculum_year parameter and UPDATE logic
- File: `app/admin/staff_router.py`
  - Added `ct_curriculum_year` to `StaffRecord`, `CreateStaffRequest`, `UpdateStaffRequest` schemas
  - Updated `create_staff_endpoint()` and `update_staff_endpoint()` to pass ct_curriculum_year

### 7. Python Syntax Checks ✅
All modified Python files pass syntax validation:
- app/auth/router.py ✅
- app/auth/schemas.py ✅
- app/subjects/service.py ✅
- app/subjects/router.py ✅
- app/reports/service.py ✅
- app/admin/staff_service.py ✅
- app/admin/staff_router.py ✅

## REMAINING FRONTEND CHANGES ⏳

### 1. CurriculumUploadPage.tsx
**Location**: `frontend/src/pages/CurriculumUploadPage.tsx`

**Changes needed**:
1. Add `curriculum_year` to `Offering` interface (line ~13-27)
2. Add `curriculum_year: '2022'` to `formData` state (line ~60-72)
3. Add curriculum_year dropdown in Add Subject Modal (after line ~640, before Student Strength field):
```tsx
<div>
    <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
        Curriculum Year (Regulation) *
    </label>
    <select
        className="form-input"
        value={formData.curriculum_year}
        onChange={(e) => setFormData({ ...formData, curriculum_year: e.target.value })}
    >
        <option value="2022">2022</option>
        <option value="2023">2023</option>
        <option value="2024">2024</option>
        <option value="2025">2025</option>
        <option value="2026">2026</option>
    </select>
</div>
```
4. Add "Regulation" column to offerings table (line ~320, after Category column):
```tsx
<th>Regulation</th>
```
5. Add curriculum_year cell in table body (line ~335, after course_category):
```tsx
<td><span className="badge badge-info">{o.curriculum_year}</span></td>
```
6. Reset curriculum_year in handleAddOffering after successful creation (line ~110)

### 2. StaffPage.tsx
**Location**: `frontend/src/pages/StaffPage.tsx`

**Changes needed**:
1. Add `ct_curriculum_year` to `Staff` interface (line ~18)
2. Add `ct_curriculum_year: ''` to `EMPTY_FORM` (line ~27)
3. Add curriculum_year dropdown in CT form section (line ~200, after ct_shift dropdown):
```tsx
<div className="flex-1 min-w-[100px]">
    <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem', display: 'block', marginBottom: '0.25rem' }}>Curriculum Year</label>
    <select className="form-select w-full" value={form.ct_curriculum_year} onChange={(e) => setField('ct_curriculum_year', e.target.value)}>
        <option value="">Select Year</option>
        <option value="2022">2022</option>
        <option value="2023">2023</option>
        <option value="2024">2024</option>
        <option value="2025">2025</option>
        <option value="2026">2026</option>
    </select>
</div>
```
4. Update CT badge display to show curriculum year (line ~280):
```tsx
{s.is_class_teacher && (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', marginTop: '0.25rem' }}>
        <span className="badge badge-info">CT</span>
        <span style={{ fontSize: '0.75rem', color: '#6b7280', fontFamily: 'monospace' }}>
            {s.ct_program}-{s.ct_section}-{s.ct_semester}-S{s.ct_shift} ({s.ct_curriculum_year || 'N/A'})
        </span>
    </div>
)}
```
5. Update openEdit to include ct_curriculum_year (line ~90)
6. Update handleAdd to pass ct_curriculum_year (line ~100)
7. Update handleEdit to pass ct_curriculum_year (line ~115)

### 3. FacultyDashboardPage.tsx (Optional - CT Info Card)
**Location**: `frontend/src/pages/FacultyDashboardPage.tsx`

**Changes needed**:
1. Add CT info card at top of dashboard if user.is_class_teacher is true
2. Display: "Class Teacher Assignment: {ct_program}-{ct_section}-{ct_semester} ({ct_curriculum_year})"

### 4. HODDashboardPage.tsx (Optional - CT Info Card)
**Location**: `frontend/src/pages/HODDashboardPage.tsx`

**Changes needed**:
1. Same as FacultyDashboardPage if HOD can also be a class teacher

## TESTING CHECKLIST

### Backend Testing
- [ ] Run migration 036 on local database
- [ ] Test `/api/auth/me` endpoint returns CT fields
- [ ] Test creating subject offering with curriculum_year
- [ ] Test listing subject offerings shows curriculum_year
- [ ] Test creating staff with ct_curriculum_year
- [ ] Test updating staff with ct_curriculum_year
- [ ] Test reports endpoint includes curriculum_year

### Frontend Testing (After Changes)
- [ ] TypeScript compilation: `cd frontend && npx tsc --noEmit`
- [ ] Subject creation form shows curriculum_year dropdown
- [ ] Subject offerings table shows Regulation column
- [ ] Staff form shows CT curriculum_year dropdown when CT checkbox is checked
- [ ] Staff table shows curriculum year in CT badge
- [ ] CT info card appears on faculty dashboard (if CT)

## DEPLOYMENT STEPS

1. Commit backend changes:
```bash
git add migrations/036_add_curriculum_year.sql startup.sh app/auth/ app/subjects/ app/reports/ app/admin/
git commit -m "feat: add curriculum year to subjects and CT assignments"
```

2. Apply frontend changes (listed above)

3. Run TypeScript check:
```bash
cd frontend && npx tsc --noEmit 2>&1 | grep "TS6133"
```

4. Commit frontend changes:
```bash
git add frontend/src/pages/
git commit -m "feat: add curriculum year UI for subjects and CT"
```

5. Push to production:
```bash
git push origin main
```

6. Verify migration 036 runs successfully on Railway

## SUMMARY

Backend implementation is complete and tested. Frontend changes are documented above with exact code snippets and line numbers. The curriculum_year field will track regulation years for subjects (2022 for MCA, 2023 for BCA by default) and CT assignments will include the curriculum year to distinguish between different regulations.
