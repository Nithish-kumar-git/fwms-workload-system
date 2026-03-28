BEGIN;

-- ============================================================
-- Migration 028: Cleanup Duplicate Sections and Offerings
-- Problem: Sections A, B, C, D, E, A+B, A+B+C exist twice
-- Keep lower IDs (1-6, 107-108), delete higher IDs (209-215)
-- ============================================================

-- Delete faculty_preferences that reference duplicate section offerings
DELETE FROM faculty_preference 
WHERE subject_offering_id IN (
    SELECT so.id FROM subject_offering so
    WHERE so.section_id IN (209, 210, 211, 212, 213, 214, 215)
);

-- Delete allocations that reference duplicate section offerings
DELETE FROM allocation 
WHERE subject_offering_id IN (
    SELECT so.id FROM subject_offering so
    WHERE so.section_id IN (209, 210, 211, 212, 213, 214, 215)
);

-- Delete subject_offerings that use duplicate sections
DELETE FROM subject_offering 
WHERE section_id IN (209, 210, 211, 212, 213, 214, 215);

-- Delete duplicate sections (keep 1-6, 107-108)
DELETE FROM section 
WHERE id IN (209, 210, 211, 212, 213, 214, 215);

-- Verify cleanup
DO $$
DECLARE 
    total_sec INTEGER; 
    total_off INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_sec FROM section;
    SELECT COUNT(*) INTO total_off FROM subject_offering;
    RAISE NOTICE '028: sections=%, offerings=%', total_sec, total_off;
END $$;

COMMIT;
