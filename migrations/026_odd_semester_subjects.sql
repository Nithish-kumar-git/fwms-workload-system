-- ============================================================================
-- Migration 026: Add Odd Semester Subject Offerings
-- Purpose: Populate MCA Sem I, III and BCA Sem I, III, V
-- Source: migrations/006_academic_seed.sql curriculum structure
-- ============================================================================

BEGIN;

-- Step 1: Ensure academic_year exists
INSERT INTO academic_year (name, start_date, end_date)
VALUES ('2025-2026', '2025-07-01', '2026-04-30')
ON CONFLICT (name) DO NOTHING;

-- Step 2: Ensure cycles exist for odd semesters (CLOSED by default)
INSERT INTO cycle (academic_year_id, semester_id, status)
SELECT ay.id, 1, 'CLOSED' FROM academic_year ay WHERE ay.name = '2025-2026'
ON CONFLICT (academic_year_id, semester_id) DO NOTHING;

INSERT INTO cycle (academic_year_id, semester_id, status)
SELECT ay.id, 3, 'CLOSED' FROM academic_year ay WHERE ay.name = '2025-2026'
ON CONFLICT (academic_year_id, semester_id) DO NOTHING;

INSERT INTO cycle (academic_year_id, semester_id, status)
SELECT ay.id, 5, 'CLOSED' FROM academic_year ay WHERE ay.name = '2025-2026'
ON CONFLICT (academic_year_id, semester_id) DO NOTHING;

-- Step 3: Upsert subjects (idempotent)
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category) VALUES
-- MCA Semester I
('CMA42001', 'Statistics for Computer Science', 3, 1, 0, 4, 4, 'BS'),
('CCM42001', 'Basics of Accounting', 1, 1, 0, 2, 2, 'BS'),
('CCA42001', 'Object Oriented Programming', 3, 0, 2, 4, 5, 'PC'),
('CCA42002', 'Data Communication and Networking', 2, 1, 0, 3, 3, 'PC'),
('CCA42003', 'Software Engineering Concepts', 3, 0, 0, 3, 3, 'PC'),
('CCA42004', 'Advanced Data Structures and Algorithms', 3, 0, 2, 4, 5, 'PC'),
('CCA42005', 'Python Programming', 2, 0, 2, 3, 4, 'PC'),
-- MCA Semester III
('CCA42010', 'Software Testing and Quality Assurance', 2, 1, 2, 4, 5, 'PC'),
('CCA42011', 'Cryptography and Network Security', 3, 0, 2, 4, 5, 'PC'),
('CEL42001', 'Communication Skills and Professional Development', 2, 0, 2, 3, 4, 'BS'),
('CCA42800', 'Research Paper Review', 0, 0, 6, 3, 6, 'PC'),
('CCA42801', 'Internship', 0, 0, 0, 2, 0, 'PC'),
-- BCA Semester I
('ACA31002', 'Computer Fundamentals and Organization', 2, 1, 0, 3, 3, 'CC'),
('ACA31003', 'Problem Solving Techniques', 2, 0, 2, 3, 4, 'CC'),
('ACA31004', 'Data Structures', 2, 1, 2, 4, 5, 'CC'),
('GMA31001', 'Mathematics for Computer Science', 3, 1, 0, 4, 4, 'BS'),
('GLS51001', 'Communication Skills', 2, 0, 1, 2, 3, 'HS'),
('GLS11001', 'Tamil Art and Culture', 1, 0, 1, 1, 2, 'HS'),
('GGE51003', 'Environmental Science and Sustainable Development', 2, 0, 0, 2, 2, 'VA'),
-- BCA Semester III
('ACA31010', 'Computer Networks', 3, 1, 0, 4, 4, 'CC'),
('ACA31009', 'Full Stack WEB Development', 3, 0, 2, 4, 5, 'CC'),
('GLS51005', 'Public Speaking', 1, 0, 1, 1, 2, 'HS'),
('GGE51015', 'Indian Knowledge System', 3, 0, 0, 0, 3, 'NC'),
('ABB31001', 'CSR and SDG', 1, 0, 2, 0, 3, 'NC'),
('ACA31800', 'Internship', 0, 0, 0, 4, 0, 'SI'),
-- BCA Semester V (Cyber Security)
('ACY31001', 'Python Programming for Cyber Security', 3, 0, 2, 4, 5, 'CC'),
('ACY31002', 'Ethical Hacking and Systems Defense', 3, 1, 0, 4, 4, 'CC'),
('ACY31003', 'Cyber Security and SIEM', 3, 0, 2, 4, 5, 'CC'),
('ACY31004', 'Security Ethics', 3, 0, 2, 4, 5, 'CC'),
('ACY31400', 'Python Programming Laboratory', 0, 0, 2, 1, 2, 'CC'),
('ACY31005', 'Industrial Cyber Threat Management', 2, 0, 0, 2, 2, 'CC')
ON CONFLICT (code) DO UPDATE SET 
    name=EXCLUDED.name, l=EXCLUDED.l, t=EXCLUDED.t, p=EXCLUDED.p, 
    credits=EXCLUDED.credits, tch=EXCLUDED.tch, course_category=EXCLUDED.course_category;

-- Step 4: Create subject_offerings for odd semesters
-- Using same pattern as migration 019 but for odd semesters

-- MCA Semester I offerings (7 subjects × 3 sections = 21 offerings)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, academic_year_id)
SELECT s.id, p.id, 1, sec.id, 1, 40, '2025-2026',
    (SELECT id FROM academic_year WHERE name = '2025-2026')
FROM subject s
CROSS JOIN (SELECT id FROM program WHERE name IN ('MCA(General)', 'MCA(BD)', 'MCA(CC)')) p
CROSS JOIN (SELECT id FROM section WHERE label IN ('A', 'B', 'C')) sec
WHERE s.code IN ('CMA42001','CCM42001','CCA42001','CCA42002','CCA42003','CCA42004','CCA42005')
ON CONFLICT DO NOTHING;

-- MCA Semester III offerings (5 subjects × 3 sections = 15 offerings)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, academic_year_id)
SELECT s.id, p.id, 3, sec.id, 1, 40, '2025-2026',
    (SELECT id FROM academic_year WHERE name = '2025-2026')
FROM subject s
CROSS JOIN (SELECT id FROM program WHERE name IN ('MCA(General)', 'MCA(BD)', 'MCA(CC)')) p
CROSS JOIN (SELECT id FROM section WHERE label IN ('A', 'B', 'C')) sec
WHERE s.code IN ('CCA42010','CCA42011','CEL42001','CCA42800','CCA42801')
ON CONFLICT DO NOTHING;

-- BCA Semester I offerings (7 core subjects × 6 sections = 42 offerings)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, academic_year_id)
SELECT s.id, p.id, 1, sec.id, 1, 50, '2025-2026',
    (SELECT id FROM academic_year WHERE name = '2025-2026')
FROM subject s
CROSS JOIN (SELECT id FROM program WHERE name IN ('BCA(General)', 'BCA(DB)', 'BCA(MM)', 'BCA(Cyber)', 'BCA(DB+MM)', 'BCA(Cyber+MM)')) p
CROSS JOIN (SELECT id FROM section WHERE label IN ('A', 'B', 'C', 'D', 'E', 'F')) sec
WHERE s.code IN ('ACA31002','ACA31003','ACA31004','GMA31001','GLS51001','GLS11001','GGE51003')
ON CONFLICT DO NOTHING;

-- BCA Semester III offerings (5 subjects × 6 sections = 30 offerings)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, academic_year_id)
SELECT s.id, p.id, 3, sec.id, 1, 50, '2025-2026',
    (SELECT id FROM academic_year WHERE name = '2025-2026')
FROM subject s
CROSS JOIN (SELECT id FROM program WHERE name IN ('BCA(General)', 'BCA(DB)', 'BCA(MM)', 'BCA(Cyber)', 'BCA(DB+MM)', 'BCA(Cyber+MM)')) p
CROSS JOIN (SELECT id FROM section WHERE label IN ('A', 'B', 'C', 'D', 'E', 'F')) sec
WHERE s.code IN ('ACA31010','ACA31009','GLS51005','GGE51015','ABB31001')
ON CONFLICT DO NOTHING;

-- BCA Semester V offerings (6 subjects × 6 sections = 36 offerings)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, academic_year_id)
SELECT s.id, p.id, 5, sec.id, 1, 50, '2025-2026',
    (SELECT id FROM academic_year WHERE name = '2025-2026')
FROM subject s
CROSS JOIN (SELECT id FROM program WHERE name IN ('BCA(Cyber)', 'BCA(Cyber+MM)')) p
CROSS JOIN (SELECT id FROM section WHERE label IN ('A', 'B', 'C', 'D', 'E', 'F')) sec
WHERE s.code IN ('ACY31001','ACY31002','ACY31003','ACY31004','ACY31400','ACY31005')
ON CONFLICT DO NOTHING;

-- Step 5: Verification
DO $$
DECLARE
    v_sem1_count INTEGER;
    v_sem3_count INTEGER;
    v_sem5_count INTEGER;
    v_total_odd INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_sem1_count FROM subject_offering WHERE semester_id = 1;
    SELECT COUNT(*) INTO v_sem3_count FROM subject_offering WHERE semester_id = 3;
    SELECT COUNT(*) INTO v_sem5_count FROM subject_offering WHERE semester_id = 5;
    v_total_odd := v_sem1_count + v_sem3_count + v_sem5_count;
    
    RAISE NOTICE '026: Semester I offerings=%', v_sem1_count;
    RAISE NOTICE '026: Semester III offerings=%', v_sem3_count;
    RAISE NOTICE '026: Semester V offerings=%', v_sem5_count;
    RAISE NOTICE '026: Total odd semester offerings=%', v_total_odd;
END $$;

COMMIT;
