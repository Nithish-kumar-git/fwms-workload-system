-- ============================================================================
-- FIX: Allocation Pipeline Data Issues
-- Safe to run multiple times (idempotent)
-- ============================================================================

BEGIN;

-- FIX 1: NULL designation in staff → set safe default
UPDATE staff
SET designation = 'Assistant Professor'
WHERE designation IS NULL OR TRIM(designation) = '';

-- Prevent future NULLs
ALTER TABLE staff ALTER COLUMN designation SET DEFAULT 'Assistant Professor';

-- FIX 2: Clean up any invalid faculty_preference rows
-- Delete preferences with preference_number outside 1-5
DELETE FROM faculty_preference WHERE preference_number < 1 OR preference_number > 5;

-- Delete preferences pointing to non-existent subject_offerings
DELETE FROM faculty_preference fp
WHERE NOT EXISTS (SELECT 1 FROM subject_offering so WHERE so.id = fp.subject_offering_id);

-- Delete preferences pointing to non-existent staff
DELETE FROM faculty_preference fp
WHERE NOT EXISTS (SELECT 1 FROM staff s WHERE s.id = fp.staff_id);

-- FIX 3: Delete duplicate (staff_id, preference_number) keeping latest
DELETE FROM faculty_preference fp1
WHERE fp1.id NOT IN (
    SELECT MAX(fp2.id) FROM faculty_preference fp2
    GROUP BY fp2.staff_id, fp2.preference_number
);

-- FIX 4: Ensure academic_cycle_id is set on all preference rows
UPDATE faculty_preference
SET academic_cycle_id = (
    SELECT id FROM academic_cycle WHERE is_active = true ORDER BY id LIMIT 1
)
WHERE academic_cycle_id IS NULL;

-- VERIFY
DO $$
DECLARE
    v_null_desig INTEGER;
    v_bad_prefs  INTEGER;
    v_null_cycle INTEGER;
BEGIN
    SELECT count(*) INTO v_null_desig FROM staff WHERE designation IS NULL;
    SELECT count(*) INTO v_bad_prefs FROM faculty_preference WHERE preference_number < 1 OR preference_number > 5;
    SELECT count(*) INTO v_null_cycle FROM faculty_preference WHERE academic_cycle_id IS NULL;

    RAISE NOTICE '=== PIPELINE FIX VERIFICATION ===';
    RAISE NOTICE 'NULL designations remaining: % (should be 0)', v_null_desig;
    RAISE NOTICE 'Invalid pref numbers remaining: % (should be 0)', v_bad_prefs;
    RAISE NOTICE 'NULL cycle prefs remaining: % (should be 0)', v_null_cycle;
END $$;

COMMIT;
