-- Migration 034: Seed MCA Semester I and III subjects and offerings
-- Also fix duplicate program names

-- ============================================================================
-- PART 1: Insert MCA Semester I and III subjects (if not exist)
-- ============================================================================

-- Semester I subjects (curriculum_year=2022)
INSERT INTO subject (code, name, course_category, l, t, p, credits, tch, curriculum_year)
VALUES 
    ('CMA42001', 'Statistics for Computer Science', 'BS', 3, 1, 0, 4, 4, '2022'),
    ('CCM42001', 'Basics of Accounting', 'BS', 1, 1, 0, 2, 2, '2022'),
    ('CCA42001', 'Object Oriented Programming', 'PC', 3, 0, 2, 4, 5, '2022'),
    ('CCA42002', 'Data Communication and Networking', 'PC', 2, 1, 0, 3, 3, '2022'),
    ('CCA42003', 'Software Engineering Concepts', 'PC', 3, 0, 0, 3, 3, '2022'),
    ('CCA42004', 'Advanced Data Structures and Algorithms', 'PC', 3, 0, 2, 4, 5, '2022'),
    ('CCA42005', 'Python Programming', 'PC', 2, 0, 2, 3, 4, '2022')
ON CONFLICT (code) DO NOTHING;

-- Semester III subjects (curriculum_year=2022)
INSERT INTO subject (code, name, course_category, l, t, p, credits, tch, curriculum_year)
VALUES 
    ('CCA42010', 'Software Testing and Quality Assurance', 'PC', 2, 1, 2, 4, 5, '2022'),
    ('CCA42011', 'Cryptography and Network Security', 'PC', 3, 0, 2, 4, 5, '2022'),
    ('CEL42001', 'Communication Skills and Professional Development', 'BS', 2, 0, 2, 3, 3, '2022')
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- PART 2: Create subject_offerings for MCA programs in Semester I and III
-- ============================================================================

-- Create offerings for Semester I (id=1)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, is_active, academic_year_id)
SELECT 
    s.id as subject_id,
    p.id as program_id,
    1 as semester_id,  -- Semester I
    sec.id as section_id,
    'Shift 1' as shift,
    true as is_active,
    1 as academic_year_id
FROM subject s
CROSS JOIN program p
CROSS JOIN section sec
WHERE s.code IN ('CMA42001', 'CCM42001', 'CCA42001', 'CCA42002', 'CCA42003', 'CCA42004', 'CCA42005')
  AND p.name ILIKE '%MCA%'
  AND NOT EXISTS (
      SELECT 1 FROM subject_offering so2
      WHERE so2.subject_id = s.id
        AND so2.program_id = p.id
        AND so2.semester_id = 1
        AND so2.section_id = sec.id
  );

-- Create offerings for Semester III (id=3)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, is_active, academic_year_id)
SELECT 
    s.id as subject_id,
    p.id as program_id,
    3 as semester_id,  -- Semester III
    sec.id as section_id,
    'Shift 1' as shift,
    true as is_active,
    1 as academic_year_id
FROM subject s
CROSS JOIN program p
CROSS JOIN section sec
WHERE s.code IN ('CCA42010', 'CCA42011', 'CEL42001')
  AND p.name ILIKE '%MCA%'
  AND NOT EXISTS (
      SELECT 1 FROM subject_offering so2
      WHERE so2.subject_id = s.id
        AND so2.program_id = p.id
        AND so2.semester_id = 3
        AND so2.section_id = sec.id
  );

-- ============================================================================
-- PART 3: Fix duplicate program names (case-insensitive consolidation)
-- ============================================================================

-- Merge BCA(CYBER+MM) into BCA(Cyber+MM) - keep the one with lower ID
DO $$
DECLARE
    keep_id INT;
    dup_id INT;
BEGIN
    -- BCA(CYBER+MM) vs BCA(Cyber+MM)
    SELECT MIN(id), MAX(id) INTO keep_id, dup_id
    FROM program
    WHERE UPPER(REPLACE(name, ' ', '')) = 'BCA(CYBER+MM)';
    
    IF dup_id IS NOT NULL AND keep_id != dup_id THEN
        UPDATE subject_offering SET program_id = keep_id WHERE program_id = dup_id;
        DELETE FROM program WHERE id = dup_id;
        RAISE NOTICE 'Merged program ID % into %', dup_id, keep_id;
    END IF;
    
    -- BCA(GENERAL) vs BCA(General)
    SELECT MIN(id), MAX(id) INTO keep_id, dup_id
    FROM program
    WHERE UPPER(REPLACE(name, ' ', '')) = 'BCA(GENERAL)';
    
    IF dup_id IS NOT NULL AND keep_id != dup_id THEN
        UPDATE subject_offering SET program_id = keep_id WHERE program_id = dup_id;
        DELETE FROM program WHERE id = dup_id;
        RAISE NOTICE 'Merged program ID % into %', dup_id, keep_id;
    END IF;
END $$;

-- ============================================================================
-- Verification queries (output to logs)
-- ============================================================================

DO $$
DECLARE
    mca_odd_count INT;
    total_programs INT;
BEGIN
    SELECT COUNT(*) INTO mca_odd_count
    FROM subject_offering so
    JOIN program p ON p.id = so.program_id
    WHERE p.name ILIKE '%MCA%' AND so.semester_id IN (1, 3);
    
    SELECT COUNT(DISTINCT name) INTO total_programs
    FROM program;
    
    RAISE NOTICE 'MCA odd semester offerings: %', mca_odd_count;
    RAISE NOTICE 'Total unique programs: %', total_programs;
END $$;
