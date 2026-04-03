-- Migration 039: Fix staff roles for HOD and TT Coordinator
-- MCT44 (Dr. S. Gokila) should be 'hod'
-- MCT48 (Dr. Sathish Kumar M) should be 'tt_coordinator'

BEGIN;

-- Fix HOD role - MCT44 Dr. S. Gokila
UPDATE staff 
SET role = 'hod' 
WHERE emp_code = 'MCT44';

-- Fix TT Coordinator role - MCT48 Dr. Sathish Kumar M  
UPDATE staff 
SET role = 'tt_coordinator' 
WHERE emp_code = 'MCT48';

-- Verify all roles
SELECT emp_code, name, role 
FROM staff 
WHERE emp_code IS NOT NULL
ORDER BY emp_code;

COMMIT;
