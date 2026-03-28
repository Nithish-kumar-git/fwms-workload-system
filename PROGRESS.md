## Latest Update - March 28, 2026

### Migration 026 Cartesian Product Error - CLEANED UP

#### Problem Identified
Migration 026 used CROSS JOIN incorrectly, creating cartesian product:
- 7 MCA Sem I subjects × 3 programs × 3 sections = 63 offerings per subject
- Expected: 7 subjects × 3 sections = 21 offerings
- Created 4,560 wrong offerings instead of ~144

#### Root Cause
```sql
FROM subject s
CROSS JOIN (SELECT id FROM program WHERE name IN ('MCA(General)', 'MCA(BD)', 'MCA(CC)')) p
CROSS JOIN (SELECT id FROM section WHERE label IN ('A', 'B', 'C')) sec
```
This creates: subject × program × section (wrong)
Should be: subject × (program+section pairs) (correct)

#### Cleanup Migration 027
Created `migrations/027_cleanup_odd_semester_offerings.sql`:
- Deleted all 4,560 wrong odd semester offerings
- Verified cleanup: 0 odd semester offerings remain
- Total offerings back to 194 (even semesters only)

#### Railway Logs
```
026: Total odd semester offerings=4560
DELETE 4560
027: odd semester offerings after cleanup=0
027: total offerings remaining=194
```

#### Commits
- a33b196: "URGENT: cleanup wrong cartesian product from migration 026"

#### Next Step
DO NOT create new subject offerings yet. Need to understand correct program-section mapping from migrations/019_real_subjects_final.sql first.
