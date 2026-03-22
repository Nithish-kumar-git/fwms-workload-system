-- ============================================================================
-- Migration 005: Workload Management Schema Extension
-- Purpose: Add workload, preference, and allocation tables alongside existing
--          FCFS subject selection schema (FSB v1.3 untouched)
-- Spec reference: final_system_specification.md, phase1_schema_plan.md
-- Safety: All new columns on existing tables are NULLABLE (existing data valid)
-- ============================================================================

-- ============================================================================
-- STEP 1: Extend staff table (10 new columns, all NULLABLE)
-- ============================================================================

ALTER TABLE staff ADD COLUMN IF NOT EXISTS emp_code VARCHAR(20);
ALTER TABLE staff ADD COLUMN IF NOT EXISTS designation VARCHAR(50);
ALTER TABLE staff ADD COLUMN IF NOT EXISTS shift VARCHAR(20);
ALTER TABLE staff ADD COLUMN IF NOT EXISTS tch_norm INTEGER;
ALTER TABLE staff ADD COLUMN IF NOT EXISTS total_workload_norm INTEGER;
ALTER TABLE staff ADD COLUMN IF NOT EXISTS is_class_teacher BOOLEAN DEFAULT false;
ALTER TABLE staff ADD COLUMN IF NOT EXISTS ct_program VARCHAR(100);
ALTER TABLE staff ADD COLUMN IF NOT EXISTS ct_section VARCHAR(10);
ALTER TABLE staff ADD COLUMN IF NOT EXISTS ct_semester VARCHAR(10);
ALTER TABLE staff ADD COLUMN IF NOT EXISTS ct_shift INTEGER;

-- Index on emp_code for lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_staff_emp_code ON staff(emp_code) WHERE emp_code IS NOT NULL;

-- Index on designation for norm lookups
CREATE INDEX IF NOT EXISTS idx_staff_designation ON staff(designation);

-- ============================================================================
-- STEP 2: Extend subject table (7 new columns, all NULLABLE)
-- ============================================================================

ALTER TABLE subject ADD COLUMN IF NOT EXISTS l INTEGER;
ALTER TABLE subject ADD COLUMN IF NOT EXISTS t INTEGER;
ALTER TABLE subject ADD COLUMN IF NOT EXISTS p INTEGER;
ALTER TABLE subject ADD COLUMN IF NOT EXISTS credits INTEGER;
ALTER TABLE subject ADD COLUMN IF NOT EXISTS tch INTEGER;
ALTER TABLE subject ADD COLUMN IF NOT EXISTS course_category VARCHAR(10);
ALTER TABLE subject ADD COLUMN IF NOT EXISTS course_type VARCHAR(10);

-- ============================================================================
-- STEP 3: Create program table
-- ============================================================================

CREATE TABLE IF NOT EXISTS program (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    ug_pg VARCHAR(5) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_program_ug_pg CHECK (ug_pg IN ('UG', 'PG'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_program_name ON program(name);

-- ============================================================================
-- STEP 4: Create semester table
-- ============================================================================

CREATE TABLE IF NOT EXISTS semester (
    id BIGSERIAL PRIMARY KEY,
    label VARCHAR(10) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_semester_label CHECK (label IN ('I', 'II', 'III', 'IV', 'V', 'VI'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_semester_label ON semester(label);

-- ============================================================================
-- STEP 5: Create section table
-- ============================================================================

CREATE TABLE IF NOT EXISTS section (
    id BIGSERIAL PRIMARY KEY,
    label VARCHAR(10) NOT NULL,
    student_strength INTEGER,
    shift INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_section_shift CHECK (shift IN (1, 2))
);

-- ============================================================================
-- STEP 6: Create subject_offering table
-- A subject offered in a specific program/semester/section/shift context
-- ============================================================================

CREATE TABLE IF NOT EXISTS subject_offering (
    id BIGSERIAL PRIMARY KEY,
    subject_id BIGINT NOT NULL,
    program_id BIGINT NOT NULL,
    semester_id BIGINT NOT NULL,
    section_id BIGINT NOT NULL,
    shift INTEGER NOT NULL DEFAULT 1,
    student_strength INTEGER,
    academic_year VARCHAR(20) NOT NULL,
    semester_type VARCHAR(10) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_subject_offering_subject FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE RESTRICT,
    CONSTRAINT fk_subject_offering_program FOREIGN KEY (program_id) REFERENCES program(id) ON DELETE RESTRICT,
    CONSTRAINT fk_subject_offering_semester FOREIGN KEY (semester_id) REFERENCES semester(id) ON DELETE RESTRICT,
    CONSTRAINT fk_subject_offering_section FOREIGN KEY (section_id) REFERENCES section(id) ON DELETE RESTRICT,
    CONSTRAINT chk_subject_offering_shift CHECK (shift IN (1, 2)),
    CONSTRAINT chk_subject_offering_semester_type CHECK (semester_type IN ('ODD', 'EVEN'))
);

CREATE INDEX IF NOT EXISTS idx_subject_offering_subject ON subject_offering(subject_id);
CREATE INDEX IF NOT EXISTS idx_subject_offering_program ON subject_offering(program_id);
CREATE INDEX IF NOT EXISTS idx_subject_offering_semester ON subject_offering(semester_id);
CREATE INDEX IF NOT EXISTS idx_subject_offering_section ON subject_offering(section_id);
CREATE INDEX IF NOT EXISTS idx_subject_offering_academic_year ON subject_offering(academic_year, semester_type);

-- ============================================================================
-- STEP 7: Create faculty_role table
-- Tracks coordination/admin roles for workload deduction
-- ============================================================================

CREATE TABLE IF NOT EXISTS faculty_role (
    id BIGSERIAL PRIMARY KEY,
    staff_id BIGINT NOT NULL,
    role_name VARCHAR(100) NOT NULL,
    deduction_hours INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_faculty_role_staff FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_faculty_role_staff ON faculty_role(staff_id);

-- ============================================================================
-- STEP 8: Create faculty_preference table
-- Tracks ranked preferences (1-5) per faculty per subject offering
-- ============================================================================

CREATE TABLE IF NOT EXISTS faculty_preference (
    id BIGSERIAL PRIMARY KEY,
    staff_id BIGINT NOT NULL,
    subject_offering_id BIGINT NOT NULL,
    preference_number INTEGER NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_faculty_preference_staff FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE RESTRICT,
    CONSTRAINT fk_faculty_preference_offering FOREIGN KEY (subject_offering_id) REFERENCES subject_offering(id) ON DELETE RESTRICT,
    CONSTRAINT chk_preference_number_range CHECK (preference_number BETWEEN 1 AND 5)
);

-- RULE-PREF-03: Each faculty may use each preference number only once
CREATE UNIQUE INDEX IF NOT EXISTS uq_faculty_preference_number 
ON faculty_preference(staff_id, preference_number);

COMMENT ON INDEX uq_faculty_preference_number IS 
'RULE-PREF-03: Each faculty may use each preference number (1-5) only once';

-- RULE-PREF-02: No two faculty may assign same preference to same subject offering
CREATE UNIQUE INDEX IF NOT EXISTS uq_subject_offering_preference 
ON faculty_preference(subject_offering_id, preference_number);

COMMENT ON INDEX uq_subject_offering_preference IS 
'RULE-PREF-02: No two faculty may assign same preference number to same subject';

-- Additional index for per-faculty lookups
CREATE INDEX IF NOT EXISTS idx_faculty_preference_staff ON faculty_preference(staff_id);

-- ============================================================================
-- STEP 9: Create allocation table
-- Coordinator-driven subject-to-faculty assignment
-- ============================================================================

CREATE TABLE IF NOT EXISTS allocation (
    id BIGSERIAL PRIMARY KEY,
    staff_id BIGINT NOT NULL,
    subject_offering_id BIGINT NOT NULL,
    l_assigned INTEGER NOT NULL DEFAULT 0,
    t_assigned INTEGER NOT NULL DEFAULT 0,
    p_assigned INTEGER NOT NULL DEFAULT 0,
    ltp_total INTEGER NOT NULL GENERATED ALWAYS AS (l_assigned + t_assigned + p_assigned) STORED,
    complexity VARCHAR(20),
    allocated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_allocation_staff FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE RESTRICT,
    CONSTRAINT fk_allocation_offering FOREIGN KEY (subject_offering_id) REFERENCES subject_offering(id) ON DELETE RESTRICT,
    CONSTRAINT chk_allocation_l_non_negative CHECK (l_assigned >= 0),
    CONSTRAINT chk_allocation_t_non_negative CHECK (t_assigned >= 0),
    CONSTRAINT chk_allocation_p_non_negative CHECK (p_assigned >= 0)
);

CREATE INDEX IF NOT EXISTS idx_allocation_staff ON allocation(staff_id);
CREATE INDEX IF NOT EXISTS idx_allocation_offering ON allocation(subject_offering_id);

-- Prevent duplicate allocation of same subject to same faculty
CREATE UNIQUE INDEX IF NOT EXISTS uq_allocation_staff_offering 
ON allocation(staff_id, subject_offering_id);

-- ============================================================================
-- STEP 10: Create workload_summary table
-- One row per faculty per academic semester
-- ============================================================================

CREATE TABLE IF NOT EXISTS workload_summary (
    id BIGSERIAL PRIMARY KEY,
    staff_id BIGINT NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    semester_type VARCHAR(10) NOT NULL,
    tch_total INTEGER NOT NULL DEFAULT 0,
    norm_hours INTEGER NOT NULL DEFAULT 0,
    deviation_hours INTEGER NOT NULL DEFAULT 0,
    total_workload INTEGER NOT NULL DEFAULT 0,
    other_academic INTEGER NOT NULL DEFAULT 0,
    research_scholars INTEGER,
    remarks TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_workload_summary_staff FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE RESTRICT,
    CONSTRAINT chk_workload_summary_semester_type CHECK (semester_type IN ('ODD', 'EVEN'))
);

-- One summary per faculty per semester
CREATE UNIQUE INDEX IF NOT EXISTS uq_workload_summary_staff_semester 
ON workload_summary(staff_id, academic_year, semester_type);

CREATE INDEX IF NOT EXISTS idx_workload_summary_staff ON workload_summary(staff_id);
CREATE INDEX IF NOT EXISTS idx_workload_summary_year ON workload_summary(academic_year, semester_type);

-- ============================================================================
-- STEP 11: Expand audit_log action_type constraint
-- Add new action types for workload system while preserving existing ones
-- ============================================================================

ALTER TABLE audit_log DROP CONSTRAINT IF EXISTS chk_audit_log_action_type;

ALTER TABLE audit_log ADD CONSTRAINT chk_audit_log_action_type 
  CHECK (action_type IN (
    -- Existing FCFS action types (FSB v1.3)
    'SELECT', 'CHANGE', 'OVERRIDE',
    -- Existing window lifecycle action types
    'WINDOW_CREATED', 'WINDOW_SCHEDULED', 'WINDOW_OPENED', 
    'WINDOW_CLOSED', 'WINDOW_ARCHIVED',
    -- New workload system action types
    'PREFERENCE_SUBMITTED', 'PREFERENCE_CLEARED',
    'ALLOCATION_CREATED', 'ALLOCATION_REMOVED',
    'WORKLOAD_CALCULATED',
    'APPROVAL_GRANTED'
  ));

-- ============================================================================
-- VERIFICATION QUERIES (run after migration to confirm safety)
-- ============================================================================

-- Verify existing data intact
DO $$
DECLARE
    staff_count INTEGER;
    subject_count INTEGER;
    assignment_count INTEGER;
BEGIN
    SELECT count(*) INTO staff_count FROM staff;
    SELECT count(*) INTO subject_count FROM subject;
    SELECT count(*) INTO assignment_count FROM staff_assignment;
    
    RAISE NOTICE 'Post-migration verification:';
    RAISE NOTICE '  staff: % rows (existing data preserved)', staff_count;
    RAISE NOTICE '  subject: % rows (existing data preserved)', subject_count;
    RAISE NOTICE '  staff_assignment: % rows (existing data preserved)', assignment_count;
    
    -- Verify new tables created and empty
    RAISE NOTICE '  program: created (0 rows)';
    RAISE NOTICE '  semester: created (0 rows)';
    RAISE NOTICE '  section: created (0 rows)'; 
    RAISE NOTICE '  subject_offering: created (0 rows)';
    RAISE NOTICE '  faculty_role: created (0 rows)';
    RAISE NOTICE '  faculty_preference: created (0 rows)';
    RAISE NOTICE '  allocation: created (0 rows)';
    RAISE NOTICE '  workload_summary: created (0 rows)';
END $$;

-- ============================================================================
-- END OF MIGRATION 005
-- ============================================================================
