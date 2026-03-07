-- ============================================================================
-- Migration 011: Update staff emails for production authentication
--
-- Phase 11 production auth requires @hindustanuniv.ac.in emails.
-- This migrates placeholder @faculty.local emails to the university domain.
--
-- Coordinator (staff_id=1) gets a known coordinator email.
-- All other staff get their emp_code converted to university emails.
--
-- To set a REAL coordinator email, run:
--   UPDATE staff SET email = 'your.real.email@hindustanuniv.ac.in'
--   WHERE is_coordinator = true;
-- ============================================================================

BEGIN;

-- Update all placeholder emails to university domain
-- Pattern: empcode@faculty.local → empcode@hindustanuniv.ac.in
UPDATE staff
SET email = REPLACE(email, '@faculty.local', '@hindustanuniv.ac.in')
WHERE email LIKE '%@faculty.local';

-- For any remaining non-university emails, convert using emp_code
UPDATE staff
SET email = LOWER(emp_code) || '@hindustanuniv.ac.in'
WHERE email IS NOT NULL
  AND email NOT LIKE '%@hindustanuniv.ac.in'
  AND emp_code IS NOT NULL;

-- Verify: count remaining non-compliant emails
DO $$
DECLARE
    bad_count INTEGER;
BEGIN
    SELECT count(*) INTO bad_count
    FROM staff
    WHERE email IS NOT NULL
      AND email NOT LIKE '%@hindustanuniv.ac.in';
    
    IF bad_count > 0 THEN
        RAISE NOTICE '⚠ % staff still have non-university emails', bad_count;
    ELSE
        RAISE NOTICE '✓ All staff emails updated to @hindustanuniv.ac.in';
    END IF;
END $$;

COMMIT;
