# How to Apply Odd Semester Fix on Railway

## Quick Fix (Recommended)

Run this single command on Railway to apply the migration:

```bash
railway run bash -c "psql \$DATABASE_URL -f migrations/031_fix_odd_semester_offerings.sql"
```

## Step-by-Step Fix

### Step 1: Check Current State

```bash
railway run bash check_production_cycles.sh
```

This shows:
- Which cycles exist
- How many subject offerings per semester
- Which cycles are OPEN

**Expected problem:** Semesters I, III, V have 0 offerings

### Step 2: Apply Migration

```bash
railway run bash apply_migration_031.sh
```

This will:
- Create cycles for semesters I, III, V (if missing)
- Add 186 subject offerings for odd semesters
- Show verification counts

### Step 3: Verify Fix

```bash
railway run bash check_production_cycles.sh
```

**Expected after fix:**
- Semester I: ~63 offerings
- Semester III: ~51 offerings  
- Semester V: ~72 offerings

### Step 4: Test in UI

1. Go to Cycles page as TT Coordinator
2. Find a Semester I, III, or V cycle
3. Click "Open" to activate it
4. Go to Preferences page
5. You should now see subjects for odd semesters

## Alternative: Direct SQL

If the bash scripts don't work, run the SQL directly:

```bash
railway run psql
```

Then paste the contents of `migrations/031_fix_odd_semester_offerings.sql`

## What This Fixes

**Before:**
- Sem 2 cycle → Shows semesters II, IV, VI ✅
- Sem 1 cycle → Shows nothing ❌

**After:**
- Sem 2 cycle → Shows semesters II, IV, VI ✅
- Sem 1 cycle → Shows semesters I, III, V ✅

## Technical Details

The issue was that migration 030 used wrong subject codes:
- Used ACA31005-ACA31008 (Semester II codes) for Semester I
- Should use ACA31002-ACA31004 (Semester I codes)

Migration 031 fixes this by using the correct codes from migration 026.
