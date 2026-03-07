-- ============================================================================
-- Migration 006: Academic Data Seed
-- Purpose: Populate programs, semesters, sections, subjects, subject_offerings
-- Source: final_system_specification.md + curriculum_full.md
-- ============================================================================

BEGIN;

-- ============================================================================
-- PRE-STEP: Make batch_id and specialization_id NULLABLE on subject table
-- Reason: Workload subjects use subject_offering for program/semester mapping,
-- not the FCFS batch/specialization columns. Existing FCFS subjects already
-- have values set, so this is backward-compatible.
-- ============================================================================

ALTER TABLE subject ALTER COLUMN batch_id DROP NOT NULL;
ALTER TABLE subject ALTER COLUMN specialization_id DROP NOT NULL;

-- ============================================================================
-- STEP 1: Programs
-- ============================================================================

INSERT INTO program (id, name, ug_pg) VALUES
(1, 'MCA', 'PG'),
(2, 'BCA', 'UG');

SELECT setval('program_id_seq', 2, true);

-- ============================================================================
-- STEP 2: Semesters (shared labels — MCA uses I-IV, BCA uses I-VI)
-- ============================================================================

INSERT INTO semester (id, label) VALUES
(1, 'I'),
(2, 'II'),
(3, 'III'),
(4, 'IV'),
(5, 'V'),
(6, 'VI');

SELECT setval('semester_id_seq', 6, true);

-- ============================================================================
-- STEP 3: Sections
-- MCA → 3 sections per year (A, B, C)
-- BCA → 6 sections per year (A, B, C, D, E, F)
-- ============================================================================

INSERT INTO section (id, label, shift) VALUES
(1, 'A', 1),
(2, 'B', 1),
(3, 'C', 1),
(4, 'D', 1),
(5, 'E', 1),
(6, 'F', 1);

SELECT setval('section_id_seq', 6, true);

-- ============================================================================
-- STEP 4: Subjects — MCA Core (Semesters I-IV)
-- Source: curriculum_full.md Tables 1-4
-- ============================================================================

-- Clear existing demo subjects (from 004_seed_demo.sql range)
-- Note: Only subjects that don't have FK references can be deleted
-- New subjects use codes from curriculum documents

-- MCA Semester I
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('CMA42001', 'Statistics for Computer Science', 3, 1, 0, 4, 4, 'BS', 'TH'),
('CCM42001', 'Basics of Accounting', 1, 1, 0, 2, 2, 'BS', 'TH'),
('CCA42001', 'Object Oriented Programming', 3, 0, 2, 4, 5, 'PC', 'TP'),
('CCA42002', 'Data Communication and Networking', 2, 1, 0, 3, 3, 'PC', 'TH'),
('CCA42003', 'Software Engineering Concepts', 3, 0, 0, 3, 3, 'PC', 'TH'),
('CCA42004', 'Advanced Data Structures and Algorithms', 3, 0, 2, 4, 5, 'PC', 'TP'),
('CCA42005', 'Python Programming', 2, 0, 2, 3, 4, 'PC', 'TP');

-- MCA Semester II
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('CCA42006', 'Machine Learning', 3, 0, 2, 4, 5, 'PC', 'TP'),
('CCA42007', 'Full Stack Web Development', 2, 0, 2, 3, 4, 'PC', 'TP'),
('CCA42008', 'Advanced Database Technologies', 2, 0, 2, 3, 4, 'PC', 'TP'),
('CCA42009', 'Research Methodology and IPR', 3, 0, 0, 3, 3, 'BS', 'TH'),
('CCA42400', 'Software Design Project', 0, 0, 4, 2, 4, 'PC', 'PR');

-- MCA Semester III
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('CCA42010', 'Software Testing and Quality Assurance', 2, 1, 2, 4, 5, 'PC', 'TP'),
('CCA42011', 'Cryptography and Network Security', 3, 0, 2, 4, 5, 'PC', 'TP'),
('CEL42001', 'Communication Skills and Professional Development', 2, 0, 2, 3, 4, 'BS', 'TP'),
('CCA42800', 'Research Paper Review', 0, 0, 6, 3, 6, 'PC', 'PR'),
('CCA42801', 'Internship', 0, 0, 0, 2, 0, 'PC', 'IN');

-- MCA Semester IV
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('CCA42802', 'Project Work', 0, 0, 40, 20, 40, 'PC', 'PJ');

-- ============================================================================
-- STEP 4b: Subjects — MCA Department Electives
-- Source: curriculum_full.md Table 5 (unique electives)
-- ============================================================================

-- DE-1 (Semester II)
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('CCA42500', 'Cloud Computing Concepts', 3, 0, 0, 3, 3, 'DE', 'TH'),
('CCA42501', 'Internet of Things', 3, 0, 0, 3, 3, 'DE', 'TH'),
('CCA42502', 'Big Data Framework', 3, 0, 0, 3, 3, 'DE', 'TH'),
('CCA42503', 'Virtualization Techniques', 3, 0, 0, 3, 3, 'DE', 'TH');

-- DE-2 (Semester II)
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('CCA42504', 'Data Analysis and Visualization Techniques', 2, 0, 2, 3, 4, 'DE', 'TP'),
('CCA42505', 'BlockChain Technology', 2, 0, 2, 3, 4, 'DE', 'TP'),
('CCA42506', 'R Programming', 2, 0, 2, 3, 4, 'DE', 'TP'),
('CCA42507', 'Cloud Application Development', 2, 0, 2, 3, 4, 'DE', 'TP'),
('CCA42508', 'Cloud Managed Services', 2, 0, 2, 3, 4, 'DE', 'TP');

-- DE-3 (Semester III)
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('CCA42509', 'Natural Language Processing', 2, 0, 2, 3, 4, 'DE', 'TP'),
('CCA42510', 'Principles of Deep Learning', 2, 0, 2, 3, 4, 'DE', 'TP'),
('CCA42511', 'Data Classification Methods and Evaluation', 2, 0, 2, 3, 4, 'DE', 'TP'),
('CCA42512', 'Cloud Computing with Web Services', 2, 0, 2, 3, 4, 'DE', 'TP');

-- DE-4 (Semester III)
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('CCA42513', 'Augmented and Virtual Reality', 2, 0, 2, 3, 4, 'DE', 'TP'),
('CCA42514', 'Big Data Analytics', 2, 0, 2, 3, 4, 'DE', 'TP'),
('CCA42515', 'Predictive Analytics', 2, 0, 2, 3, 4, 'DE', 'TP'),
('CCA42516', 'Cloud Security', 2, 0, 2, 3, 4, 'DE', 'TP'),
('CCA42517', 'Cloud Platform Essentials', 2, 0, 2, 3, 4, 'DE', 'TP');

-- ============================================================================
-- STEP 4c: Subjects — BCA Core (Semesters I-VI)
-- Source: curriculum_full.md BCA Table 1
-- ============================================================================

-- BCA Semester I
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('ACA31002', 'Computer Fundamentals and Organization', 2, 1, 0, 3, 3, 'CC', 'TH'),
('ACA31003', 'Problem Solving Techniques', 2, 0, 2, 3, 4, 'CC', 'TP'),
('ACA31004', 'Data Structures', 2, 1, 2, 4, 5, 'CC', 'TP'),
('GMA31001', 'Mathematics for Computer Science', 3, 1, 0, 4, 4, 'BS', 'TH'),
('GLS51001', 'Communication Skills', 2, 0, 1, 2, 3, 'HS', 'TP'),
('GLS11001', 'Tamil Art and Culture', 1, 0, 1, 1, 2, 'HS', 'TP'),
('GGE51003', 'Environmental Science and Sustainable Development', 2, 0, 0, 2, 2, 'VA', 'TH'),
('GBP01400', 'Health and Wellbeing', 0, 0, 2, 1, 2, 'HS', 'PR'),
('GPE21401', 'Yoga', 0, 0, 2, 1, 2, 'VA', 'PR'),
('GPE21402', 'Sports', 0, 0, 2, 1, 2, 'VA', 'PR'),
('GPE21403', 'Fitness', 0, 0, 2, 1, 2, 'VA', 'PR'),
('AVC31401', 'Fine Arts', 0, 0, 2, 1, 2, 'VA', 'PR'),
('GGE51401', 'Outreach (NCC) Level-I', 0, 0, 2, 1, 2, 'HS', 'PR'),
('GGE51402', 'Outreach (NSS) Level-I', 0, 0, 2, 1, 2, 'HS', 'PR'),
('ASS21001', 'Community Development', 1, 0, 1, 0, 2, 'NC', 'TP');

-- BCA Semester II
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('ACA31005', 'Object Oriented Programming', 2, 0, 2, 3, 4, 'CC', 'TP'),
('ACA31006', 'Database Management Systems', 2, 0, 2, 3, 4, 'CC', 'TP'),
('ACA31007', 'Multimedia Systems', 2, 0, 2, 3, 4, 'CC', 'TP'),
('ACA31008', 'Operating Systems', 2, 1, 0, 3, 3, 'CC', 'TH'),
('GLS51002', 'Personality Development and Soft Skills', 2, 0, 1, 2, 3, 'HS', 'TP'),
('ACA31001', 'Digital Technological Solutions', 2, 0, 2, 3, 4, 'AE', 'TP'),
('GLS51008', 'Tamil', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS51009', 'Hindi', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS51010', 'Telugu', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS11002', 'Advanced Tamil', 2, 0, 0, 2, 2, 'HS', 'TH');

-- BCA Semester III
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('ACA31010', 'Computer Networks', 3, 1, 0, 4, 4, 'CC', 'TP'),
('ACA31009', 'Full Stack WEB Development', 3, 0, 2, 4, 5, 'CC', 'TP'),
('GLS51011', 'French', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS51012', 'German', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS51013', 'Spanish', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS51014', 'Korean', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS51015', 'Mandarin', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS51016', 'Japanese', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS51005', 'Public Speaking', 1, 0, 1, 1, 2, 'HS', 'TP'),
('GGE51015', 'Indian Knowledge System', 3, 0, 0, 0, 3, 'NC', 'TH'),
('ABB31001', 'CSR and SDG', 1, 0, 2, 0, 3, 'NC', 'TP'),
('ACA31800', 'Internship', 0, 0, 0, 4, 0, 'SI', 'IN');

-- BCA Semester IV
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('ACA31011', 'Software Engineering', 2, 1, 2, 4, 5, 'CC', 'TP'),
('ACA31015', 'E-Commerce Technologies', 3, 0, 0, 3, 3, 'CC', 'TH'),
('ACA31012', 'Mobile Application Development', 2, 0, 2, 3, 4, 'CC', 'TP'),
('ACA31014', 'Digital Marketing', 3, 0, 0, 3, 3, 'CC', 'TH'),
('ACM31001', 'Accounting Tools', 1, 0, 2, 2, 3, 'SE', 'TP'),
('GLS11003', 'French Intermediate', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS11004', 'German Intermediate', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS11005', 'Spanish Intermediate', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS11006', 'Korean Intermediate', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS11007', 'Mandarin Intermediate', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS11008', 'Japanese Intermediate', 2, 0, 0, 2, 2, 'HS', 'TH'),
('GLS51006', 'English for Competitive Examinations', 1, 0, 1, 1, 2, 'HS', 'TP');

-- BCA Semester V (Cyber Security specialization)
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('ACY31001', 'Python Programming for Cyber Security', 3, 0, 2, 4, 5, 'CC', 'TP'),
('ACY31002', 'Ethical Hacking and Systems Defense', 3, 1, 0, 4, 4, 'CC', 'TH'),
('ACY31003', 'Cyber Security and SIEM', 3, 0, 2, 4, 5, 'CC', 'TP'),
('ACY31004', 'Security Ethics', 3, 0, 2, 4, 5, 'CC', 'TP'),
('ACY31400', 'Python Programming Laboratory', 0, 0, 2, 1, 2, 'CC', 'PR'),
('ACY31005', 'Industrial Cyber Threat Management', 2, 0, 0, 2, 2, 'CC', 'TH');

-- BCA Semester VI (Cyber Security specialization)
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('ACY31006', 'API and Network Security', 3, 1, 0, 4, 4, 'CC', 'TH'),
('ACY31007', 'Secure Coding Practices', 3, 1, 0, 4, 4, 'CC', 'TH'),
('ACY31008', 'Industrial Access Control Models and Practices', 2, 0, 0, 2, 2, 'NC', 'TH'),
('GGE51001', 'Universal Human Values', 2, 0, 0, 2, 2, 'HS', 'TH'),
('ACY31800', 'Project', 0, 0, 14, 7, 14, 'RP', 'PJ');

-- ============================================================================
-- STEP 4d: Subjects — BCA Electives
-- Source: curriculum_full.md BCA Elective Tables
-- ============================================================================

-- DE-1 (Semester III)
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('ACA31500', 'MATLAB Programming', 2, 0, 2, 3, 4, 'DE', 'TP'),
('ACA31501', 'User Interface Design', 2, 0, 2, 3, 4, 'DE', 'TP'),
('ACA31502', 'Graphic Design', 2, 0, 2, 3, 4, 'DE', 'TP'),
('ACA31503', 'Digital Media and Visual Effects', 2, 0, 2, 3, 4, 'DE', 'TP'),
('ACA31504', 'Advanced Database Technologies', 2, 0, 2, 3, 4, 'DE', 'TP'),
('ACA31505', 'Data Science Tools', 2, 0, 2, 3, 4, 'DE', 'TP');

-- DE-2 (Semester IV)
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('ACA31508', 'Software Modeling Architecture', 2, 0, 2, 3, 4, 'DE', 'TP'),
('ACA31509', 'Information Security', 2, 0, 2, 3, 4, 'DE', 'TP'),
('ACA31510', '2-D Animation and Editing', 2, 0, 2, 3, 4, 'DE', 'TP'),
('ACA31511', '3-D Architectural Visualization and Visual FX', 2, 0, 2, 3, 4, 'DE', 'TP'),
('ACA31512', 'Data Modelling and Integration', 2, 0, 2, 3, 4, 'DE', 'TP'),
('ACA31513', 'Databases in R Programming', 2, 0, 2, 3, 4, 'DE', 'TP');

-- DE-3 (Semester V — Cyber)
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('ACY31500', 'Principles of Computer Security', 2, 0, 2, 3, 4, 'DE', 'TP'),
('ACY31501', 'Cyber Forensics', 2, 0, 2, 3, 4, 'DE', 'TP');

-- DE-4 (Semester VI — Cyber)
INSERT INTO subject (code, name, l, t, p, credits, tch, course_category, course_type) VALUES
('ACY31502', 'Cyber Security Techniques and Tools', 2, 0, 2, 3, 4, 'DE', 'TP'),
('ACY31503', 'IOT Security', 2, 0, 2, 3, 4, 'DE', 'TP');

-- ============================================================================
-- STEP 5: Subject Offerings
-- Creates teaching instances: subject × program × semester × section
-- MCA: 3 sections (A, B, C) × semesters I-IV
-- BCA: 6 sections (A-F) × semesters I-VI
-- Academic year: 2025-2026, EVEN semester
-- ============================================================================

-- MCA Semester I offerings (7 core subjects × 3 sections = 21 offerings)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 1, 1, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('CMA42001','CCM42001','CCA42001','CCA42002','CCA42003','CCA42004','CCA42005')
AND sec.id <= 3;

-- MCA Semester II offerings (5 core + elective slots × 3 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 1, 2, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('CCA42006','CCA42007','CCA42008','CCA42009','CCA42400')
AND sec.id <= 3;

-- MCA Semester II electives (DE-1 pool × 3 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 1, 2, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('CCA42500','CCA42501','CCA42502','CCA42503',
                 'CCA42504','CCA42505','CCA42506','CCA42507','CCA42508')
AND sec.id <= 3;

-- MCA Semester III offerings (5 core × 3 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 1, 3, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('CCA42010','CCA42011','CEL42001','CCA42800','CCA42801')
AND sec.id <= 3;

-- MCA Semester III electives (DE-3/DE-4 pool × 3 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 1, 3, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('CCA42509','CCA42510','CCA42511','CCA42512',
                 'CCA42513','CCA42514','CCA42515','CCA42516','CCA42517')
AND sec.id <= 3;

-- MCA Semester IV offerings (1 project × 3 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 1, 4, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code = 'CCA42802'
AND sec.id <= 3;

-- BCA Semester I offerings (core subjects × 6 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 2, 1, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('ACA31002','ACA31003','ACA31004','GMA31001','GLS51001','GLS11001','GGE51003')
AND sec.id <= 6;

-- BCA Semester II offerings (core subjects × 6 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 2, 2, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('ACA31005','ACA31006','ACA31007','ACA31008','GLS51002','ACA31001')
AND sec.id <= 6;

-- BCA Semester III offerings (core + language subjects × 6 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 2, 3, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('ACA31010','ACA31009','GLS51005','GGE51015','ABB31001')
AND sec.id <= 6;

-- BCA Semester III electives (DE-1 × 6 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 2, 3, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('ACA31500','ACA31501','ACA31502','ACA31503','ACA31504','ACA31505')
AND sec.id <= 6;

-- BCA Semester IV offerings (core × 6 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 2, 4, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('ACA31011','ACA31015','ACA31012','ACA31014','ACM31001','GLS51006')
AND sec.id <= 6;

-- BCA Semester IV electives (DE-2 × 6 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 2, 4, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('ACA31508','ACA31509','ACA31510','ACA31511','ACA31512','ACA31513')
AND sec.id <= 6;

-- BCA Semester V offerings (Cyber core × 6 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 2, 5, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('ACY31001','ACY31002','ACY31003','ACY31004','ACY31400','ACY31005')
AND sec.id <= 6;

-- BCA Semester V electives (DE-3 × 6 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 2, 5, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('ACY31500','ACY31501')
AND sec.id <= 6;

-- BCA Semester VI offerings (core × 6 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 2, 6, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('ACY31006','ACY31007','ACY31008','GGE51001','ACY31800')
AND sec.id <= 6;

-- BCA Semester VI electives (DE-4 × 6 sections)
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, academic_year, semester_type)
SELECT s.id, 2, 6, sec.id, 1, '2025-2026', 'EVEN'
FROM subject s
CROSS JOIN section sec
WHERE s.code IN ('ACY31502','ACY31503')
AND sec.id <= 6;

-- ============================================================================
-- STEP 6: Verification
-- ============================================================================

DO $$
DECLARE
    v_program INTEGER;
    v_semester INTEGER;
    v_section INTEGER;
    v_subject INTEGER;
    v_offering INTEGER;
    v_tch_mismatch INTEGER;
    v_dup_codes INTEGER;
BEGIN
    SELECT count(*) INTO v_program FROM program;
    SELECT count(*) INTO v_semester FROM semester;
    SELECT count(*) INTO v_section FROM section;
    SELECT count(*) INTO v_subject FROM subject WHERE tch IS NOT NULL;
    SELECT count(*) INTO v_offering FROM subject_offering;
    
    -- Check TCH = L + T + P
    SELECT count(*) INTO v_tch_mismatch 
    FROM subject 
    WHERE tch IS NOT NULL AND tch != (l + t + p);
    
    -- Check duplicate codes
    SELECT count(*) INTO v_dup_codes 
    FROM (SELECT code FROM subject WHERE tch IS NOT NULL GROUP BY code HAVING count(*) > 1) x;
    
    RAISE NOTICE '=== ACADEMIC DATA SEED VERIFICATION ===';
    RAISE NOTICE 'Programs: %', v_program;
    RAISE NOTICE 'Semesters: %', v_semester;
    RAISE NOTICE 'Sections: %', v_section;
    RAISE NOTICE 'Subjects (with curriculum data): %', v_subject;
    RAISE NOTICE 'Subject Offerings: %', v_offering;
    RAISE NOTICE 'TCH mismatches (should be 0): %', v_tch_mismatch;
    RAISE NOTICE 'Duplicate course codes (should be 0): %', v_dup_codes;
END $$;

COMMIT;

-- ============================================================================
-- END OF SEED 006
-- ============================================================================
