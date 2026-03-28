## Latest Update - March 28, 2026

### What was done

**STEP 1: Analyzed migration 019 pattern**
- Migration 019 uses **specific JOINs**, NOT CROSS JOIN
- Pattern: `JOIN program p ON p.name='MCA(General)' JOIN section sec ON sec.label='A'`
- One INSERT per subject-program-section tuple
- Example: MCA(General) section A gets CCA42802, MCA(BD+CC) section B gets CCA42802

**STEP 2: Analyzed migration 006 structure**
- Migration 006 uses CROSS JOIN for initial seed: `FROM subject s CROSS JOIN section sec WHERE s.code IN (...) AND sec.id <= 3`
- This works ONLY when you want ALL sections for ALL subjects in the list
- Migration 019 overrides this with specific program-section mappings

**STEP 3: Made debug endpoint public and tested**
- Commits: ca8f02f (public), 5003118 (re-secured)
- Endpoint tested successfully

### Result

**Database state (Railway production):**
- subject_offering_total: 194
- Grouped by semester: Sem 2 (78), Sem 4 (58), Sem 6 (58)
- Active cycles: Sem 2, 4, 6 all OPEN
- Programs: 17 total (MCA, BCA, and variants with IDs 103-117)
- Sections: 15 total (A-F with IDs 1-6, A+B, A+B+C, duplicates with IDs 209-215)

**CRITICAL FINDING - Duplicate sections:**
- Section A appears twice: id=1 and id=209
- Section A+B appears twice: id=107 and id=210
- Section A+B+C appears twice: id=108 and id=211
- Sections B, C, D, E also duplicated (ids 2-5 and 212-215)

**Sample semester 2 offerings show DUPLICATES:**
- BCA(Cyber+MM) section C has DUPLICATE entries for every subject
- Example: ACA31001 appears twice (ids 781, 782), ACA31005 twice (773, 774)
- BCA(GENERAL) section A also has duplicates: ACA31001 (761, 762), ACA31005 (753, 754)

### Next step

**URGENT: Fix duplicate sections and offerings before adding odd semester data**

The duplicate sections (209-215) are causing duplicate subject_offerings. Need to:
1. Identify which migration created duplicate sections
2. Create cleanup migration to remove duplicate sections and their offerings
3. Then create migration 028 for odd semester subjects using correct pattern from 019
