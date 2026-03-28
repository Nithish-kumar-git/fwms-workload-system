## Latest Update - March 28, 2026

### What was done

**STEP 1: Detected duplicates via debug endpoint**
- Duplicate sections: A, B, C, D, E, A+B, A+B+C (IDs 1-6, 107-108 vs 209-215)
- Duplicate offerings: 12+ duplicates in semester 6 (BCA subjects)
- Example: ACA31017 BCA(General) section A appeared twice (ids 641, 671)

**STEP 2: Created migration 028 - cleanup duplicate sections**
- Deleted faculty_preference and allocation referencing duplicate sections
- Deleted subject_offerings using section IDs 209-215
- Deleted duplicate sections (kept 1-6, 107-108)
- Result: 8 sections remain (A, B, C, D, E, F, A+B, A+B+C)

**STEP 3: Created migration 029 - cleanup duplicate offerings**
- Deleted faculty_preference and allocation for duplicate offerings
- Deleted duplicate offerings (kept lower ID in each pair)
- Strategy: WHERE EXISTS subquery to find duplicates by subject+program+semester+section

### Result

**Before cleanup:**
- Sections: 15 (7 duplicates)
- Offerings: 194 (97 duplicates)

**After cleanup:**
- Sections: 8 (no duplicates)
- Offerings: 85 (no duplicates)
- Migration 029 log: "029: offerings=85, duplicates=0"

**Commits:**
- 0c244c7: migration 028 (sections cleanup)
- 1a7d33d: migration 029 (offerings cleanup)

### Next step

Database is now clean. Ready to add odd semester subjects using correct pattern from migration 019.
