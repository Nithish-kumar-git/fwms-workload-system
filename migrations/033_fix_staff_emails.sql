-- ============================================================================
-- Migration 033: Fix Staff Emails for Google OAuth Login
-- Purpose: Update staff emails from @faculty.local to @hindustanuniv.ac.in
-- ============================================================================

BEGIN;

-- Fix HOD email (id=16, MCT44, Dr. S. Gokila)
UPDATE staff 
SET email = 'sgokila@hindustanuniv.ac.in' 
WHERE id = 16;

-- Fix TT Coordinator email (id=22, MCT48, Dr. Sathish Kumar M)
UPDATE staff 
SET email = 'sathishkm@hindustanuniv.ac.in' 
WHERE id = 22;

-- For all OTHER staff: derive email from emp_code
-- Pattern: lowercase(emp_code) + '@hindustanuniv.ac.in'
-- Example: MCT49 -> mct49@hindustanuniv.ac.in
UPDATE staff 
SET email = LOWER(emp_code) || '@hindustanuniv.ac.in'
WHERE emp_code IS NOT NULL
  AND id NOT IN (16, 22);  -- Don't override HOD and Coordinator we just set

-- Verify results
SELECT id, emp_code, name, email, role 
FROM staff 
WHERE is_active = true
ORDER BY id 
LIMIT 10;

COMMIT;

-- ============================================================================
-- END OF MIGRATION 033
-- ============================================================================
