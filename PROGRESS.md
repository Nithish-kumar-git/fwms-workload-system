## Latest Update - March 28, 2026

### Migration 026 Cartesian Product Analysis

#### Migration 027 Cleanup - SUCCESS
Railway logs confirmed:
```
DELETE 4560
027: odd semester offerings after cleanup=0
027: total offerings remaining=194
```

#### Database State After Cleanup
- Total offerings: 194 (even semesters only)
- Semester 2: 78 offerings
- Semester 4: 58 offerings  
- Semester 6: 58 offerings
- Odd semesters (1, 3, 5): 0 offerings

#### Programs in Database (17 total)
Base: MCA, BCA
MCA variants: MCA(BD), MCA(BD+CC), MCA(CC), MCA(General), MCA(General+BD), MCA(General+CC)
BCA variants: BCA(CYBER+MM), BCA(Cyber), BCA(Cyber+MM), BCA(DB), BCA(DB+MM), BCA(GENERAL), BCA(General), BCA(General+DB), BCA(MM)

#### Sections in Database (15 total)
Single: A, B, C, D, E, F
Combined: A+B, A+B+C

#### Sample Semester 2 Offerings (showing duplicates issue)
BCA(Cyber+MM) + Section C + ACA31001: 2 duplicate rows (IDs 781, 782)
BCA(Cyber+MM) + Section C + ACA31005: 2 duplicate rows (IDs 773, 774)
BCA(GENERAL) + Section A + ACA31001: 2 duplicate rows (IDs 761, 762)

Even semester data has duplicates from migration 019!

#### Correct Pattern from Migration 019
```sql
-- ONE INSERT per subject-program-section combination
INSERT INTO subject_offering (...) 
SELECT s.id, p.id, 4, sec.id, 1, 42, '2025-2026', 'EVEN', 1 
FROM subject s 
JOIN program p ON p.name='MCA(General)'  -- specific program
JOIN section sec ON sec.label='A'        -- specific section
WHERE s.code='CCA42802';                 -- specific subject
```

#### Wrong Pattern from Migration 026
```sql
-- CROSS JOIN creates cartesian product
FROM subject s
CROSS JOIN (SELECT id FROM program WHERE name IN (...)) p  -- all programs
CROSS JOIN (SELECT id FROM section WHERE label IN (...)) sec  -- all sections
WHERE s.code IN (...)  -- multiple subjects
```
Result: 7 subjects × 3 programs × 3 sections = 63 offerings (wrong)

#### Commits
- a33b196: Cleanup migration 027
- f05bfbe: Temp debug queries
- a17db25: Re-secure debug endpoint

#### Next Step
Need to create migration 028 with correct pattern: one INSERT per subject-program-section tuple, not cartesian product.
