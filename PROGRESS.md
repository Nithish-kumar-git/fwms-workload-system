# MCA Subjects Missing - FIXED

## Root Cause
MCA programs had NO subject_offering records for odd semesters (I, III, V) in the database.

## Solution Applied

### Migration 034 Created
File: `migrations/034_seed_mca_odd_semesters.sql`

**What it does:**
1. Inserts 10 MCA subjects for Semesters I and III (if not exist)
2. Creates subject_offerings for all MCA programs × all sections × Semesters I and III
3. Fixes duplicate program names (BCA(CYBER+MM) vs BCA(Cyber+MM), BCA(GENERAL) vs BCA(General))

### Subjects Added

**Semester I (7 subjects):**
- CMA42001 | Statistics for Computer Science | L=3 T=1 P=0 C=4 TCH=4
- CCM42001 | Basics of Accounting | L=1 T=1 P=0 C=2 TCH=2
- CCA42001 | Object Oriented Programming | L=3 T=0 P=2 C=4 TCH=5
- CCA42002 | Data Communication and Networking | L=2 T=1 P=0 C=3 TCH=3
- CCA42003 | Software Engineering Concepts | L=3 T=0 P=0 C=3 TCH=3
- CCA42004 | Advanced Data Structures and Algorithms | L=3 T=0 P=2 C=4 TCH=5
- CCA42005 | Python Programming | L=2 T=0 P=2 C=3 TCH=4

**Semester III (3 subjects):**
- CCA42010 | Software Testing and Quality Assurance | L=2 T=1 P=2 C=4 TCH=5
- CCA42011 | Cryptography and Network Security | L=3 T=0 P=2 C=4 TCH=5
- CEL42001 | Communication Skills and Professional Development | L=2 T=0 P=2 C=3 TCH=3

### Duplicate Programs Fixed
- BCA(CYBER+MM) merged into BCA(Cyber+MM)
- BCA(GENERAL) merged into BCA(General)

## How to Apply Migration to Production

**Option 1: Via Railway CLI**
```bash
railway run bash apply_migration_034.sh
```

**Option 2: Via Railway Dashboard**
1. Go to Railway project → Database
2. Open PostgreSQL console
3. Copy/paste contents of `migrations/034_seed_mca_odd_semesters.sql`
4. Execute

**Option 3: Via psql directly**
```bash
psql $DATABASE_URL -f migrations/034_seed_mca_odd_semesters.sql
```

## Expected Results After Migration

**Before:**
- MCA offerings: Only in semesters II, IV (EVEN)
- Total MCA offerings: ~16

**After:**
- MCA offerings: In semesters I, II, III, IV (ODD + EVEN)
- Total MCA offerings: ~100+ (7 MCA programs × 2 sections × 10 subjects)

## Verification

After applying migration, check:
```sql
SELECT COUNT(*) FROM subject_offering so
JOIN program p ON p.id = so.program_id
WHERE p.name ILIKE '%MCA%' AND so.semester_id IN (1, 3);
```

Should return > 0 (previously was 0).

## Files Modified
- `migrations/034_seed_mca_odd_semesters.sql` - Migration script
- `apply_migration_034.sh` - Helper script to apply migration

## Commits
- `8047238` - seed: add MCA sem I and III subject offerings, fix duplicate programs (migration 034)
- `bdaf144` - docs: root cause analysis - MCA subjects are in EVEN semesters only
- `a09bd9d` - debug: add offerings debug endpoint to diagnose MCA subjects issue

## Status
✅ Migration created and committed
⏳ **PENDING**: Migration needs to be applied to production database
✅ Code fix already deployed (removes academic_year_id filter)

## Next Steps
1. Apply migration 034 to production database
2. Verify MCA subjects appear in preference catalog when odd semester cycles are open
3. Test with actual users
