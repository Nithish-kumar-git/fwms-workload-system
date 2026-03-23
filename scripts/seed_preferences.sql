BEGIN;

-- Clean all existing preferences
TRUNCATE faculty_preference;

-- Insert up to 5 preferences per active faculty
INSERT INTO faculty_preference (staff_id, subject_offering_id, preference_number, academic_cycle_id)
SELECT *
FROM (
    SELECT
        s.id AS staff_id,
        so.id AS subject_offering_id,
        ROW_NUMBER() OVER (PARTITION BY s.id ORDER BY so.id) AS preference_number,
        ac.id AS academic_cycle_id
    FROM staff s
    JOIN subject_offering so
        ON so.academic_cycle_id = (
            SELECT id FROM academic_cycle WHERE is_active = true LIMIT 1
        )
    JOIN academic_cycle ac ON ac.is_active = true
    WHERE s.is_active = true
      AND s.emp_code IS NOT NULL
) ranked
WHERE preference_number <= 5;

-- Verify
DO $$
DECLARE
    v_total INTEGER;
    v_faculty INTEGER;
BEGIN
    SELECT count(*) INTO v_total FROM faculty_preference;
    SELECT count(DISTINCT staff_id) INTO v_faculty FROM faculty_preference;
    RAISE NOTICE 'Preferences inserted: % total rows for % faculty', v_total, v_faculty;
END $$;

COMMIT;
