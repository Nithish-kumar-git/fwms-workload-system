BEGIN;

-- Drop incorrect constraint: UNIQUE(subject_offering_id, preference_number)
-- This blocks multiple faculty from choosing the same subject
DROP INDEX IF EXISTS uq_subject_offering_preference;

-- Drop old per-faculty constraint without academic_cycle_id
DROP INDEX IF EXISTS uq_faculty_preference_number;

-- Drop our previous attempt if it exists
DROP INDEX IF EXISTS uq_staff_pref_per_cycle;
ALTER TABLE faculty_preference DROP CONSTRAINT IF EXISTS uq_staff_preference;

-- Correct constraint: each faculty uses each preference_number once per cycle
ALTER TABLE faculty_preference
ADD CONSTRAINT uq_staff_preference UNIQUE (staff_id, preference_number, academic_cycle_id);

-- Fix NULL designations
UPDATE staff
SET designation = 'Assistant Professor'
WHERE designation IS NULL OR TRIM(designation) = '';

COMMIT;
