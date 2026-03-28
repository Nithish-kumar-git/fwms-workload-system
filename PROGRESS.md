## Latest Update - March 28, 2026

### BUG 1: "Your Preferences" always empty - FIXED

**Root Cause**: Backend returns plain array, frontend expected {preferences: []}

**Changed in frontend/src/pages/PreferencesPage.tsx** (Line 84):

BEFORE:
```typescript
setPreferences(prefsRes.data.preferences || []);
```

AFTER:
```typescript
setPreferences(Array.isArray(prefsRes.data) ? prefsRes.data : prefsRes.data.preferences || []);
```

---

### BUG 2: Class teacher validation reads wrong columns - FIXED

**Root Cause**: Column indexes mismatched between staff SELECT and offering SELECT

**Staff Query** (app/preference/service.py Line 42-49):
```sql
SELECT id, shift, is_class_teacher, ct_program, ct_section, ct_semester, ct_shift
FROM staff
```
Indexes: [0]=id, [1]=shift, [2]=is_class_teacher, [3]=ct_program, [4]=ct_section, [5]=ct_semester, [6]=ct_shift ✓

**Offering Query** (Line 56-68):
```sql
SELECT so.id, so.shift, so.section_id, so.semester_id, so.program_id,
       s.name AS subject_name, s.code AS subject_code,
       p.name AS program_name,
       sem.label AS semester_label,
       sec.label AS section_label
```
Indexes: [0]=id, [1]=shift, [2]=section_id, [3]=semester_id, [4]=program_id, [5]=subject_name, [6]=subject_code, [7]=program_name, [8]=semester_label, [9]=section_label

**Changed in app/preference/service.py** (Line 151-163):

BEFORE:
```python
offering_program = offering[8]    # program_name
offering_semester = offering[7]   # semester_label
offering_section = offering[9]    # section_label
```

AFTER:
```python
offering_program = offering[7]    # program_name
offering_semester = offering[8]   # semester_label
offering_section = offering[9]    # section_label
```

---

### BUG 3: Odd semesters show "No subjects match" - FIXED

**Root Cause**: Hardcoded all 6 semesters but production only has even semesters (II, IV, VI)

**Changed in frontend/src/pages/PreferencesPage.tsx** (Line 125-129):

BEFORE:
```typescript
// Fixed semester options - always show all 6 semesters regardless of data
const semesters = ['I', 'II', 'III', 'IV', 'V', 'VI'];
```

AFTER:
```typescript
// Dynamic semester options - only show semesters that have data
const semesters = useMemo(() => {
    const available = [...new Set(offerings.map((o) => o.semester))].sort();
    return available;
}, [offerings]);
```

---

### Commits
- c2fc34b: "Fix: preferences display + class teacher column order + semester filter"
- Pushed to main successfully
