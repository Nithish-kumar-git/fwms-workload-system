BEGIN;

-- ============================================================
-- Migration 029: Cleanup Duplicate Subject Offerings
-- Problem: Same subject-program-semester-section appears twice
-- Strategy: Keep lower ID, delete higher ID
-- ============================================================

-- Delete faculty_preferences for duplicate offerings (keep lower ID)
DELETE FROM faculty_preference 
WHERE subject_offering_id IN (
    SELECT id FROM subject_offering so1
    WHERE EXISTS (
        SELECT 1 FROM subject_offering so2
        WHERE so2.subject_id = so1.subject_id
        AND so2.program_id = so1.program_id
        AND so2.semester_id = so1.semester_id
        AND so2.section_id = so1.section_id
        AND so2.id < so1.id
    )
);

-- Delete allocations for duplicate offerings (keep lower ID)
DELETE FROM allocation 
WHERE subject_offering_id IN (
    SELECT id FROM subject_offering so1
    WHERE EXISTS (
        SELECT 1 FROM subject_offering so2
        WHERE so2.subject_id = so1.subject_id
        AND so2.program_id = so1.program_id
        AND so2.semester_id = so1.semester_id
        AND so2.section_id = so1.section_id
        AND so2.id < so1.id
    )
);

-- Delete duplicate offerings (keep lower ID)
DELETE FROM subject_offering so1
WHERE EXISTS (
    SELECT 1 FROM subject_offering so2
    WHERE so2.subject_id = so1.subject_id
    AND so2.program_id = so1.program_id
    AND so2.semester_id = so1.semester_id
    AND so2.section_id = so1.section_id
    AND so2.id < so1.id
);

-- Verify cleanup
DO $$
DECLARE 
    total_off INTEGER;
    dup_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_off FROM subject_offering;
    
    SELECT COUNT(*) INTO dup_count FROM (
        SELECT subject_id, program_id, semester_id, section_id
        FROM subject_offering
        GROUP BY subject_id, program_id, semester_id, section_id
        HAVING COUNT(*) > 1
    ) x;
    
    RAISE NOTICE '029: offerings=%, duplicates=%', total_off, dup_count;
END $$;

COMMIT;
