# Odd Semester Cycle Fix

## Problem

When clicking "Sem 2" cycle, it shows even semesters (II, IV, VI) correctly.
When clicking "Sem 1" cycle, it does NOT show odd semesters (I, III, V).

## Root Cause Analysis

### Migration History
1. **Migration 026** - Created odd semester offerings with CORRECT subject codes
2. **Migration 027** - DELETED all odd semester offerings (cleanup of cartesian product error)
3. **Migration 030** - Attempted to re-add odd semester offerings but used WRONG subject codes
   - Used Semester II codes (ACA31005, ACA31006, ACA31007, ACA31008) for Semester I
   - These codes don't match the actual Semester I subjects (ACA31002, ACA31003, ACA31004)

### Result
- Production database has NO odd semester subject offerings
- Cycles for semesters I, III, V exist but have 0 offerings
- When user opens "Sem 1" cycle, the preference page shows nothing

## Solution

### Migration 031: Fix Odd Semester Offerings

Created `migrations/031_fix_odd_semester_offerings.sql` which:

1. **Ensures cycles exist** for semesters I, III, V (idempotent)
2. **Ensures subjects exist** with correct codes (idempotent)
3. **Creates subject offerings** using CORRECT codes:

**MCA Semester I (21 offerings):**
- 7 subjects: CMA42001, CCM42001, CCA42001, CCA42002, CCA42003, CCA42004, CCA42005
- 3 sections: A, B, C
- 3 programs: MCA(General), MCA(BD), MCA(CC)

**MCA Semester III (15 offerings):**
- 5 subjects: CCA42010, CCA42011, CEL42001, CCA42800, CCA42801
- 3 sections: A, B, C
- 3 programs: MCA(General), MCA(BD), MCA(CC)

**BCA Semester I (42 offerings):**
- 7 subjects: ACA31002, ACA31003, ACA31004, GMA31001, GLS51001, GLS11001, GGE51003
- 6 sections: A, B, C, D, E, F
- 6 programs: BCA(General), BCA(DB), BCA(MM), BCA(Cyber), BCA(DB+MM), BCA(Cyber+MM)

**BCA Semester III (36 offerings):**
- 6 subjects: ACA31010, ACA31009, GLS51005, GGE51015, ABB31001, ACA31800
- 6 sections: A, B, C, D, E, F
- 6 programs: BCA(General), BCA(DB), BCA(MM), BCA(Cyber), BCA(DB+MM), BCA(Cyber+MM)

**BCA Semester V (72 offerings):**
- 6 subjects: ACY31001, ACY31002, ACY31003, ACY31004, ACY31400, ACY31005
- 6 sections: A, B, C, D, E, F
- 2 programs: BCA(Cyber), BCA(Cyber+MM)

**Expected Total: 186 odd semester offerings**

## How to Apply

### On Railway Production:

```bash
# 1. Check current state
railway run bash check_production_cycles.sh

# 2. Apply migration
railway run bash apply_migration_031.sh

# 3. Verify results
railway run bash check_production_cycles.sh
```

### Manual Application:

```bash
# Connect to Railway database
railway run psql

# Run migration
\i migrations/031_fix_odd_semester_offerings.sql

# Verify
SELECT semester_id, COUNT(*) FROM subject_offering GROUP BY semester_id ORDER BY semester_id;
```

## Expected Results After Fix

### Cycle Table:
```
semester_id | semester_label | status  | offerings
------------|----------------|---------|----------
1           | I              | CLOSED  | 63
2           | II             | OPEN    | 78
3           | III            | CLOSED  | 51
4           | IV             | CLOSED  | ~50
5           | V              | CLOSED  | 72
6           | VI             | CLOSED  | ~50
```

### User Experience:
- Click "Sem 1" cycle → Opens preference window → Shows semesters I, III, V with subjects
- Click "Sem 2" cycle → Opens preference window → Shows semesters II, IV, VI with subjects

## Files Changed
- `migrations/031_fix_odd_semester_offerings.sql` - NEW migration
- `apply_migration_031.sh` - Script to apply migration on Railway
- `check_production_cycles.sh` - Script to verify database state
