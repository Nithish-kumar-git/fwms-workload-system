BEGIN;

-- Add odd semester subject offerings using correct pattern from migration 019
-- Pattern: One INSERT per subject-program-section tuple with specific JOINs

-- Semester 1 (ODD) - BCA subjects
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 56, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(GENERAL)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='ACA31005';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 56, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(GENERAL)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='ACA31006';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 56, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(GENERAL)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='ACA31007';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 56, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(GENERAL)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='ACA31008';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 56, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(GENERAL)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='ACA31001';


INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 44, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General+DB)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='ACA31005';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 44, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General+DB)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='ACA31006';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 44, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General+DB)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='ACA31007';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 44, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General+DB)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='ACA31008';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 44, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General+DB)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='ACA31001';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 57, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(Cyber+MM)' 
JOIN section sec ON sec.label='C' 
WHERE s.code='ACA31005';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 57, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(Cyber+MM)' 
JOIN section sec ON sec.label='C' 
WHERE s.code='ACA31006';


INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 57, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(Cyber+MM)' 
JOIN section sec ON sec.label='C' 
WHERE s.code='ACA31007';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 57, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(Cyber+MM)' 
JOIN section sec ON sec.label='C' 
WHERE s.code='ACA31008';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 57, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(Cyber+MM)' 
JOIN section sec ON sec.label='C' 
WHERE s.code='ACA31001';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 56, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General+DB)' 
JOIN section sec ON sec.label='D' 
WHERE s.code='ACA31005';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 56, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General+DB)' 
JOIN section sec ON sec.label='D' 
WHERE s.code='ACA31006';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 56, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General+DB)' 
JOIN section sec ON sec.label='D' 
WHERE s.code='ACA31007';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 56, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General+DB)' 
JOIN section sec ON sec.label='D' 
WHERE s.code='ACA31008';


INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 1, sec.id, 1, 56, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General+DB)' 
JOIN section sec ON sec.label='D' 
WHERE s.code='ACA31001';

-- Semester 3 (ODD) - BCA subjects
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 3, sec.id, 1, 55, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='ACA31011';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 3, sec.id, 1, 55, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='ACA31015';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 3, sec.id, 1, 55, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='ACA31012';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 3, sec.id, 1, 55, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='ACA31014';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 3, sec.id, 1, 52, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General+DB)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='ACA31011';


INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 3, sec.id, 1, 52, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General+DB)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='ACA31015';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 3, sec.id, 1, 52, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General+DB)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='ACA31012';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 3, sec.id, 1, 52, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General+DB)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='ACA31014';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 3, sec.id, 1, 49, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(CYBER+MM)' 
JOIN section sec ON sec.label='C' 
WHERE s.code='ACA31011';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 3, sec.id, 1, 49, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(CYBER+MM)' 
JOIN section sec ON sec.label='C' 
WHERE s.code='ACA31015';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 3, sec.id, 1, 49, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(CYBER+MM)' 
JOIN section sec ON sec.label='C' 
WHERE s.code='ACA31012';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 3, sec.id, 1, 49, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(CYBER+MM)' 
JOIN section sec ON sec.label='C' 
WHERE s.code='ACA31014';


-- Semester 5 (ODD) - BCA subjects
INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 63, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='ACA31017';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 63, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='ACA31018';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 63, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='ACA31019';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 63, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='GGE51011';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 63, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='GGE51001';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 63, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General)' 
JOIN section sec ON sec.label='A' 
WHERE s.code='ACA31801';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 74, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(DB+MM)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='ACA31017';


INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 74, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(DB+MM)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='ACA31018';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 74, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(DB+MM)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='ACA31019';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 74, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(DB+MM)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='GGE51011';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 74, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(DB+MM)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='GGE51001';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 74, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(DB+MM)' 
JOIN section sec ON sec.label='B' 
WHERE s.code='ACA31801';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 45, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(General)' 
JOIN section sec ON sec.label='A+B' 
WHERE s.code='ACA31525';

INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 45, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(DB)' 
JOIN section sec ON sec.label='A+B' 
WHERE s.code='ACA31526';


INSERT INTO subject_offering (subject_id, program_id, semester_id, section_id, shift, student_strength, academic_year, semester_type, academic_cycle_id) 
SELECT s.id, p.id, 5, sec.id, 1, 45, '2025-2026', 'ODD', 1 
FROM subject s 
JOIN program p ON p.name='BCA(MM)' 
JOIN section sec ON sec.label='A+B' 
WHERE s.code='ACA31523';

-- Add logging to verify counts
DO $$
DECLARE
    total_offerings INTEGER;
    odd_offerings INTEGER;
    even_offerings INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_offerings FROM subject_offering;
    SELECT COUNT(*) INTO odd_offerings FROM subject_offering WHERE semester_type = 'ODD';
    SELECT COUNT(*) INTO even_offerings FROM subject_offering WHERE semester_type = 'EVEN';
    
    RAISE NOTICE '030: total_offerings=%, odd=%, even=%', total_offerings, odd_offerings, even_offerings;
END $$;

COMMIT;
