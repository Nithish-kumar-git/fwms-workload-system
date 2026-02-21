-- ============================================================================
-- DEMO SEED DATA — Faculty Subject Selection System
-- Purpose: Realistic demo data for controlled college demo
-- Deterministic IDs — safe to re-run after schema reset
-- ============================================================================

-- Clean existing data (respect FK order)
DELETE FROM subject_selection;
DELETE FROM audit_log;    -- Must be done via direct SQL since triggers block DELETE in normal mode
DELETE FROM staff_assignment;
DELETE FROM subject;
DELETE FROM selection_window;
DELETE FROM specialization;
DELETE FROM batch;
DELETE FROM staff;

-- Temporarily disable audit_log delete trigger for cleanup
DROP TRIGGER IF EXISTS trg_prevent_audit_log_delete ON audit_log;
DELETE FROM audit_log;

-- Re-create the trigger
CREATE OR REPLACE FUNCTION prevent_audit_log_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'DELETE on audit_log is forbidden - audit log is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_audit_log_delete
BEFORE DELETE ON audit_log
FOR EACH ROW
EXECUTE FUNCTION prevent_audit_log_delete();

-- ============================================================================
-- STAFF (15 members: 3 coordinators + 12 faculty)
-- ============================================================================

INSERT INTO staff (id, email, name, is_coordinator, is_active) VALUES
-- Coordinators
(1,  'hod.cse@hindustanuniv.ac.in',      'Dr. Rajesh Kumar',       true,  true),
(2,  'hod.ece@hindustanuniv.ac.in',       'Dr. Priya Sharma',       true,  true),
(3,  'hod.mech@hindustanuniv.ac.in',      'Dr. Suresh Iyer',        true,  true),
-- Faculty
(4,  'anand.v@hindustanuniv.ac.in',       'Prof. Anand Venkatesh',   false, true),
(5,  'deepa.r@hindustanuniv.ac.in',       'Prof. Deepa Ramesh',      false, true),
(6,  'kartik.m@hindustanuniv.ac.in',      'Prof. Kartik Menon',      false, true),
(7,  'lakshmi.s@hindustanuniv.ac.in',     'Prof. Lakshmi Subramanian', false, true),
(8,  'mohan.g@hindustanuniv.ac.in',       'Prof. Mohan Gopal',       false, true),
(9,  'nithya.k@hindustanuniv.ac.in',      'Prof. Nithya Krishnan',   false, true),
(10, 'pradeep.j@hindustanuniv.ac.in',     'Prof. Pradeep Jayaraman', false, true),
(11, 'revathi.n@hindustanuniv.ac.in',     'Prof. Revathi Nair',      false, true),
(12, 'senthil.b@hindustanuniv.ac.in',     'Prof. Senthil Balaji',    false, true),
(13, 'uma.d@hindustanuniv.ac.in',         'Prof. Uma Devi',          false, true),
(14, 'vijay.t@hindustanuniv.ac.in',       'Prof. Vijay Thirumalai',  false, true),
(15, 'yamini.p@hindustanuniv.ac.in',      'Prof. Yamini Pillai',     false, true);

SELECT setval('staff_id_seq', 15, true);

-- ============================================================================
-- BATCHES (3 admission years)
-- ============================================================================

INSERT INTO batch (id, name, is_active) VALUES
(1, '2022 Batch', true),
(2, '2023 Batch', true),
(3, '2024 Batch', true);

SELECT setval('batch_id_seq', 3, true);

-- ============================================================================
-- SPECIALIZATIONS (3 departments × consistent across batches)
-- ============================================================================

INSERT INTO specialization (id, name, is_active) VALUES
(1, 'Computer Science & Engineering',     true),
(2, 'Electronics & Communication Engg',   true),
(3, 'Mechanical Engineering',             true);

SELECT setval('specialization_id_seq', 3, true);

-- ============================================================================
-- SUBJECTS (36 total: 4 subjects × 3 specializations × 3 batches)
-- ============================================================================

-- CSE - 2022 Batch (Semester 5/6 level)
INSERT INTO subject (id, code, name, batch_id, specialization_id) VALUES
(1,  'CS601', 'Compiler Design',                 1, 1),
(2,  'CS602', 'Computer Networks',                1, 1),
(3,  'CS603', 'Machine Learning',                 1, 1),
(4,  'CS604', 'Software Engineering',             1, 1);

-- CSE - 2023 Batch (Semester 3/4 level)
INSERT INTO subject (id, code, name, batch_id, specialization_id) VALUES
(5,  'CS401', 'Data Structures & Algorithms',     2, 1),
(6,  'CS402', 'Database Management Systems',      2, 1),
(7,  'CS403', 'Operating Systems',                2, 1),
(8,  'CS404', 'Discrete Mathematics',             2, 1);

-- CSE - 2024 Batch (Semester 1/2 level)
INSERT INTO subject (id, code, name, batch_id, specialization_id) VALUES
(9,  'CS201', 'Programming in C',                 3, 1),
(10, 'CS202', 'Digital Logic Design',             3, 1),
(11, 'CS203', 'Engineering Mathematics I',        3, 1),
(12, 'CS204', 'Physics for Computing',            3, 1);

-- ECE - 2022 Batch
INSERT INTO subject (id, code, name, batch_id, specialization_id) VALUES
(13, 'EC601', 'VLSI Design',                      1, 2),
(14, 'EC602', 'Digital Signal Processing',         1, 2),
(15, 'EC603', 'Embedded Systems',                  1, 2),
(16, 'EC604', 'Antenna & Wave Propagation',        1, 2);

-- ECE - 2023 Batch
INSERT INTO subject (id, code, name, batch_id, specialization_id) VALUES
(17, 'EC401', 'Signals & Systems',                 2, 2),
(18, 'EC402', 'Analog Circuits',                   2, 2),
(19, 'EC403', 'Microprocessors',                   2, 2),
(20, 'EC404', 'Electromagnetic Theory',            2, 2);

-- ECE - 2024 Batch
INSERT INTO subject (id, code, name, batch_id, specialization_id) VALUES
(21, 'EC201', 'Basic Electrical Engineering',      3, 2),
(22, 'EC202', 'Electronic Devices & Circuits',     3, 2),
(23, 'EC203', 'Engineering Mathematics I',         3, 2),
(24, 'EC204', 'Physics for Electronics',           3, 2);

-- MECH - 2022 Batch
INSERT INTO subject (id, code, name, batch_id, specialization_id) VALUES
(25, 'ME601', 'Heat Transfer',                     1, 3),
(26, 'ME602', 'Manufacturing Technology',          1, 3),
(27, 'ME603', 'Dynamics of Machinery',             1, 3),
(28, 'ME604', 'Finite Element Analysis',           1, 3);

-- MECH - 2023 Batch
INSERT INTO subject (id, code, name, batch_id, specialization_id) VALUES
(29, 'ME401', 'Fluid Mechanics',                   2, 3),
(30, 'ME402', 'Thermodynamics',                    2, 3),
(31, 'ME403', 'Strength of Materials',             2, 3),
(32, 'ME404', 'Kinematics of Machinery',           2, 3);

-- MECH - 2024 Batch
INSERT INTO subject (id, code, name, batch_id, specialization_id) VALUES
(33, 'ME201', 'Engineering Drawing',               3, 3),
(34, 'ME202', 'Workshop Practice',                 3, 3),
(35, 'ME203', 'Engineering Mathematics I',         3, 3),
(36, 'ME204', 'Engineering Chemistry',             3, 3);

SELECT setval('subject_id_seq', 36, true);

-- ============================================================================
-- STAFF ASSIGNMENTS (eligibility — who can teach what)
-- ============================================================================
-- Faculty are assigned to specific batch+specialization combinations
-- Each faculty member is eligible for 1-2 batch/spec combos

INSERT INTO staff_assignment (staff_id, batch_id, specialization_id) VALUES
-- CSE Faculty
(4,  1, 1),  -- Anand → CSE 2022
(4,  2, 1),  -- Anand → CSE 2023
(5,  1, 1),  -- Deepa → CSE 2022
(5,  3, 1),  -- Deepa → CSE 2024
(6,  2, 1),  -- Kartik → CSE 2023
(6,  3, 1),  -- Kartik → CSE 2024
(7,  1, 1),  -- Lakshmi → CSE 2022
(7,  2, 1),  -- Lakshmi → CSE 2023

-- ECE Faculty
(8,  1, 2),  -- Mohan → ECE 2022
(8,  2, 2),  -- Mohan → ECE 2023
(9,  1, 2),  -- Nithya → ECE 2022
(9,  3, 2),  -- Nithya → ECE 2024
(10, 2, 2),  -- Pradeep → ECE 2023
(10, 3, 2),  -- Pradeep → ECE 2024
(11, 1, 2),  -- Revathi → ECE 2022
(11, 2, 2),  -- Revathi → ECE 2023

-- MECH Faculty
(12, 1, 3),  -- Senthil → MECH 2022
(12, 2, 3),  -- Senthil → MECH 2023
(13, 1, 3),  -- Uma → MECH 2022
(13, 3, 3),  -- Uma → MECH 2024
(14, 2, 3),  -- Vijay → MECH 2023
(14, 3, 3),  -- Vijay → MECH 2024
(15, 1, 3),  -- Yamini → MECH 2022
(15, 2, 3);  -- Yamini → MECH 2023

-- Coordinators are also eligible (they are also faculty)
INSERT INTO staff_assignment (staff_id, batch_id, specialization_id) VALUES
(1, 1, 1),   -- Dr. Rajesh (HOD CSE) → CSE 2022
(2, 1, 2),   -- Dr. Priya (HOD ECE) → ECE 2022
(3, 1, 3);   -- Dr. Suresh (HOD MECH) → MECH 2022

-- ============================================================================
-- NO WINDOWS PRE-CREATED — Coordinator creates during demo
-- NO SELECTIONS PRE-MADE — Staff select during demo
-- ============================================================================

-- ============================================================================
-- VERIFICATION QUERIES (run manually to confirm)
-- ============================================================================
-- SELECT count(*) AS staff_count FROM staff;                     -- Expected: 15
-- SELECT count(*) AS batch_count FROM batch;                     -- Expected: 3
-- SELECT count(*) AS spec_count FROM specialization;             -- Expected: 3
-- SELECT count(*) AS subject_count FROM subject;                 -- Expected: 36
-- SELECT count(*) AS assignment_count FROM staff_assignment;     -- Expected: 27
-- SELECT count(*) AS window_count FROM selection_window;         -- Expected: 0
-- SELECT count(*) AS selection_count FROM subject_selection;     -- Expected: 0
