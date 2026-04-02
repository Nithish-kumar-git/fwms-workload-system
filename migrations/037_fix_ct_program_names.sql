-- Migration 037: Fix CT program names to match actual program table names
-- Issue: ct_program stores "MCA" or "BCA" but programs table has "MCA(General)", "BCA(General)" etc.

BEGIN;

-- Fix ct_program values to match actual program names in program table
-- Map short names to full names
UPDATE staff 
SET ct_program = 'MCA(General)' 
WHERE ct_program IN ('MCA', 'mca', 'MCA ', 'MCA(AI)') 
  AND is_class_teacher = true;

UPDATE staff 
SET ct_program = 'BCA(General)' 
WHERE ct_program IN ('BCA', 'bca', 'BCA ', 'BCA(Cyber)') 
  AND is_class_teacher = true;

-- Show all CT assignments after fix
SELECT id, emp_code, name, is_class_teacher, ct_program, ct_section, ct_semester, ct_shift, ct_curriculum_year 
FROM staff 
WHERE is_class_teacher = true 
ORDER BY emp_code;

COMMIT;
