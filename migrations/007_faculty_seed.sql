-- ============================================================================
-- Migration 007: Faculty Data Seed
-- Purpose: Import 27 faculty members from FACULTY-LIST Excel sheet
-- Source: institutional_rules.md (extracted from WORKLOAD-GENERATION Excel)
-- Safety: Appends new records only. Existing staff row (id=1) not modified.
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 2-3: Insert Staff Records with Class Teacher Assignments
-- Email format: empcode@faculty.local (placeholder until real emails linked)
-- total_workload_norm: Professor=38, AssocProf=38, AsstProf=40, Part-time=24
-- ============================================================================

-- Note: Row 1 (MCT44, Dr. S. Gokila) appears as both HOD and Professor.
-- We use HOD as designation + Professor norm. HOD role tracked in faculty_role.

-- 1. MCT44 — Dr. S. Gokila (HOD + Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift, is_coordinator)
VALUES ('mct44@faculty.local', 'Dr. S. Gokila', 'MCT44', 'HOD', 'SHIFT1', 10, 38,
    true, 'MCA', 'A', 'II', 1, true);

-- 2. MCT50 — Dr. S. Sudha (Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct50@faculty.local', 'Dr. S. Sudha', 'MCT50', 'Professor', 'SHIFT1', 14, 38,
    true, 'MCA', 'A', 'IV', 1);

-- 3. MCT68 — Dr. Ayyanathan A (Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher)
VALUES ('mct68@faculty.local', 'Dr. Ayyanathan A', 'MCT68', 'Professor', 'SHIFT1', 10, 38,
    false);

-- 4. MCT61 — Dr. H J Shanthi (Associate Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct61@faculty.local', 'Dr. H J Shanthi', 'MCT61', 'Associate Professor', 'SHIFT1', 14, 38,
    true, 'BCA', 'A', 'VI', 1);

-- 5. MCT69 — Dr. Priya M (Associate Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct69@faculty.local', 'Dr. Priya M', 'MCT69', 'Associate Professor', 'SHIFT1+SHIFT2', 14, 38,
    true, 'BCA', 'A', 'VI', 2);

-- 6. CNS02 — Mr. N. Sivakumar (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher)
VALUES ('cns02@faculty.local', 'Mr. N. Sivakumar', 'CNS02', 'Assistant Professor', 'SHIFT1', 8, 40,
    false);

-- 7. MCT48 — Dr. Sathish Kumar M (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct48@faculty.local', 'Dr. Sathish Kumar M', 'MCT48', 'Assistant Professor', 'SHIFT1', 14, 40,
    true, 'MCA', 'B', 'II', 1);

-- 8. MCT49 — Dr. Angelina Benita D (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct49@faculty.local', 'Dr. Angelina Benita D', 'MCT49', 'Assistant Professor', 'SHIFT1', 16, 40,
    true, 'BCA', 'A', 'II', 1);

-- 9. MCT54 — Mrs. Vinitha Sushila Devi S (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher)
VALUES ('mct54@faculty.local', 'Mrs. Vinitha Sushila Devi S', 'MCT54', 'Assistant Professor', 'SHIFT2', 16, 40,
    false);

-- 10. MCT65 — Dr. Lakshmanan S (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct65@faculty.local', 'Dr. Lakshmanan S', 'MCT65', 'Assistant Professor', 'SHIFT1', 14, 40,
    true, 'BCA', 'B', 'VI', 1);

-- 11. MCT39 — Dr Sherin Eliyas (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct39@faculty.local', 'Dr. Sherin Eliyas', 'MCT39', 'Assistant Professor', 'SHIFT1', 16, 40,
    true, 'MCA', 'B', 'IV', 1);

-- 12. MCT60 — Dr. Nathiya R (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct60@faculty.local', 'Dr. Nathiya R', 'MCT60', 'Assistant Professor', 'SHIFT1', 16, 40,
    true, 'BCA', 'A', 'IV', 1);

-- 13. MCT53 — Mrs. Sophia Janit R (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct53@faculty.local', 'Mrs. Sophia Janit R', 'MCT53', 'Assistant Professor', 'SHIFT1', 16, 40,
    true, 'BCA', 'C', 'IV', 1);

-- 14. MCT58 — Mrs. Kalpana K (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct58@faculty.local', 'Mrs. Kalpana K', 'MCT58', 'Assistant Professor', 'SHIFT2', 14, 40,
    true, 'BCA', 'E', 'II', 2);

-- 15. MCT63 — Mrs. Karunambikai M (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct63@faculty.local', 'Mrs. Karunambikai M', 'MCT63', 'Assistant Professor', 'SHIFT1', 16, 40,
    true, 'BCA', 'B', 'IV', 1);

-- 16. MCT59 — Dr. Vanitha Jaitly (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher)
VALUES ('mct59@faculty.local', 'Dr. Vanitha Jaitly', 'MCT59', 'Assistant Professor', 'SHIFT1', 16, 40,
    false);

-- 17. MCT73 — Mrs. Mary Reni (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher)
VALUES ('mct73@faculty.local', 'Mrs. Mary Reni', 'MCT73', 'Assistant Professor', 'SHIFT1', 16, 40,
    false);

-- 18. LAT74 — Dr. C Bagyalakshmi (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('lat74@faculty.local', 'Dr. C Bagyalakshmi', 'LAT74', 'Assistant Professor', 'SHIFT2', 16, 40,
    true, 'BCA', 'B', 'VI', 2);

-- 19. MCT71 — Mr. Prabu (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct71@faculty.local', 'Mr. Prabu', 'MCT71', 'Assistant Professor', 'SHIFT2', 16, 40,
    true, 'BCA', 'B', 'IV', 2);

-- 20. MCT70 — Dr. C Bala Kamatchi (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct70@faculty.local', 'Dr. C Bala Kamatchi', 'MCT70', 'Assistant Professor', 'SHIFT1+SHIFT2', 16, 40,
    true, 'BCA', 'A', 'IV', 2);

-- 21. MCT78 — Dr. Sheeja Sudheer (Associate Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct78@faculty.local', 'Dr. Sheeja Sudheer', 'MCT78', 'Associate Professor', 'SHIFT1+SHIFT2', 14, 38,
    true, 'BCA', 'D', 'II', 1);

-- 22. MCT77 — Dr. Jaya Sundaram (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct77@faculty.local', 'Dr. Jaya Sundaram', 'MCT77', 'Assistant Professor', 'SHIFT1+SHIFT2', 16, 40,
    true, 'BCA', 'B', 'II', 1);

-- 23. MCT76 — Ms. Karthika (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift)
VALUES ('mct76@faculty.local', 'Ms. Karthika', 'MCT76', 'Assistant Professor', 'SHIFT1+SHIFT2', 16, 40,
    true, 'BCA', 'C', 'II', 1);

-- 24. MCT79 — Ms. Divya Prabha B (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher)
VALUES ('mct79@faculty.local', 'Ms. Divya Prabha B', 'MCT79', 'Assistant Professor', 'SHIFT1', 16, 40,
    false);

-- 25. MCT75 — Mr. Shyam Praveen B (Assistant Professor)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher)
VALUES ('mct75@faculty.local', 'Mr. Shyam Praveen B', 'MCT75', 'Assistant Professor', 'SHIFT2', 16, 40,
    false);

-- 26. MCT01 — Dr. Anitha S Pillai (Professor, Part-time 3 days)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher)
VALUES ('mct01@faculty.local', 'Dr. Anitha S Pillai', 'MCT01', 'Professor', 'SHIFT1', 8, 24,
    false);

-- 27. MCT42 — Mr. Ramanayagam (Associate Professor, Part-time 3 days)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher)
VALUES ('mct42@faculty.local', 'Mr. Ramanayagam', 'MCT42', 'Associate Professor', 'SHIFT1', 8, 24,
    false);

-- 28. MCP04 — Mr. Senthil (Assistant Professor, Part-time 3 days)
INSERT INTO staff (email, name, emp_code, designation, shift, tch_norm, total_workload_norm,
    is_class_teacher)
VALUES ('mcp04@faculty.local', 'Mr. Senthil', 'MCP04', 'Assistant Professor', 'SHIFT2', 8, 24,
    false);

-- ============================================================================
-- STEP 4: Faculty Roles
-- HOD role for Dr. S. Gokila
-- ============================================================================

INSERT INTO faculty_role (staff_id, role_name, deduction_hours)
SELECT id, 'HOD', 2 FROM staff WHERE emp_code = 'MCT44';

-- ============================================================================
-- STEP 5: Verification
-- ============================================================================

DO $$
DECLARE
    v_total_staff INTEGER;
    v_new_staff INTEGER;
    v_faculty_roles INTEGER;
    v_dup_codes INTEGER;
    v_class_teachers INTEGER;
    v_invalid_fk INTEGER;
BEGIN
    SELECT count(*) INTO v_total_staff FROM staff;
    SELECT count(*) INTO v_new_staff FROM staff WHERE emp_code IS NOT NULL;
    SELECT count(*) INTO v_faculty_roles FROM faculty_role;
    
    -- Check no duplicate emp_codes
    SELECT count(*) INTO v_dup_codes 
    FROM (SELECT emp_code FROM staff WHERE emp_code IS NOT NULL GROUP BY emp_code HAVING count(*) > 1) x;
    
    -- Count class teachers
    SELECT count(*) INTO v_class_teachers FROM staff WHERE is_class_teacher = true;
    
    -- Verify faculty_role FK integrity
    SELECT count(*) INTO v_invalid_fk 
    FROM faculty_role fr 
    LEFT JOIN staff s ON s.id = fr.staff_id 
    WHERE s.id IS NULL;
    
    RAISE NOTICE '=== FACULTY IMPORT VERIFICATION ===';
    RAISE NOTICE 'Total staff rows: %', v_total_staff;
    RAISE NOTICE 'New staff with emp_code: %', v_new_staff;
    RAISE NOTICE 'Faculty roles: %', v_faculty_roles;
    RAISE NOTICE 'Class teachers: %', v_class_teachers;
    RAISE NOTICE 'Duplicate emp_codes (should be 0): %', v_dup_codes;
    RAISE NOTICE 'Invalid FK refs (should be 0): %', v_invalid_fk;
    
    -- TCH norm check by designation
    RAISE NOTICE '--- TCH Norm Distribution ---';
    PERFORM (
        SELECT count(*) FROM staff WHERE designation = 'HOD' AND tch_norm IS NOT NULL
    );
END $$;

-- Show designation distribution
SELECT designation, count(*), 
       string_agg(DISTINCT tch_norm::text, ', ') AS tch_norms,
       string_agg(DISTINCT total_workload_norm::text, ', ') AS total_norms
FROM staff 
WHERE emp_code IS NOT NULL
GROUP BY designation
ORDER BY designation;

-- Show class teacher assignments
SELECT emp_code, name, ct_program, ct_section, ct_semester, ct_shift
FROM staff
WHERE is_class_teacher = true AND emp_code IS NOT NULL
ORDER BY ct_program, ct_section;

COMMIT;

-- ============================================================================
-- END OF SEED 007
-- ============================================================================
