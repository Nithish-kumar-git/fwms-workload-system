-- ============================================================================
-- Migration 010: Multi-Academic-Year Support
-- Phase 10 — Academic Cycle Entity + FK Linkage
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Create academic_cycle table
-- ============================================================================

CREATE TABLE IF NOT EXISTS academic_cycle (
    id              SERIAL PRIMARY KEY,
    academic_year   VARCHAR(20) NOT NULL,       -- e.g. "2025-2026"
    semester_type   VARCHAR(10) NOT NULL,        -- ODD / EVEN
    start_date      DATE,
    end_date        DATE,
    is_active       BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_academic_cycle UNIQUE (academic_year, semester_type),
    CONSTRAINT chk_semester_type CHECK (semester_type IN ('ODD', 'EVEN'))
);

-- ============================================================================
-- STEP 2: Insert default cycle for existing data
-- ============================================================================

INSERT INTO academic_cycle (academic_year, semester_type, is_active)
VALUES ('2025-2026', 'EVEN', true)
ON CONFLICT (academic_year, semester_type) DO NOTHING;

-- ============================================================================
-- STEP 3: Add academic_cycle_id FK to operational tables
-- ============================================================================

-- subject_offering
ALTER TABLE subject_offering
    ADD COLUMN IF NOT EXISTS academic_cycle_id INTEGER;

UPDATE subject_offering SET academic_cycle_id = (
    SELECT id FROM academic_cycle WHERE academic_year = '2025-2026' AND semester_type = 'EVEN'
) WHERE academic_cycle_id IS NULL;

ALTER TABLE subject_offering
    ALTER COLUMN academic_cycle_id SET NOT NULL;

ALTER TABLE subject_offering
    ADD CONSTRAINT fk_subject_offering_cycle
    FOREIGN KEY (academic_cycle_id) REFERENCES academic_cycle(id);

-- faculty_preference
ALTER TABLE faculty_preference
    ADD COLUMN IF NOT EXISTS academic_cycle_id INTEGER;

UPDATE faculty_preference SET academic_cycle_id = (
    SELECT id FROM academic_cycle WHERE academic_year = '2025-2026' AND semester_type = 'EVEN'
) WHERE academic_cycle_id IS NULL;

ALTER TABLE faculty_preference
    ALTER COLUMN academic_cycle_id SET NOT NULL;

ALTER TABLE faculty_preference
    ADD CONSTRAINT fk_faculty_preference_cycle
    FOREIGN KEY (academic_cycle_id) REFERENCES academic_cycle(id);

-- allocation
ALTER TABLE allocation
    ADD COLUMN IF NOT EXISTS academic_cycle_id INTEGER;

UPDATE allocation SET academic_cycle_id = (
    SELECT id FROM academic_cycle WHERE academic_year = '2025-2026' AND semester_type = 'EVEN'
) WHERE academic_cycle_id IS NULL;

ALTER TABLE allocation
    ALTER COLUMN academic_cycle_id SET NOT NULL;

ALTER TABLE allocation
    ADD CONSTRAINT fk_allocation_cycle
    FOREIGN KEY (academic_cycle_id) REFERENCES academic_cycle(id);

-- workload_summary
ALTER TABLE workload_summary
    ADD COLUMN IF NOT EXISTS academic_cycle_id INTEGER;

UPDATE workload_summary SET academic_cycle_id = (
    SELECT id FROM academic_cycle WHERE academic_year = '2025-2026' AND semester_type = 'EVEN'
) WHERE academic_cycle_id IS NULL;

ALTER TABLE workload_summary
    ALTER COLUMN academic_cycle_id SET NOT NULL;

ALTER TABLE workload_summary
    ADD CONSTRAINT fk_workload_summary_cycle
    FOREIGN KEY (academic_cycle_id) REFERENCES academic_cycle(id);

-- selection_window
ALTER TABLE selection_window
    ADD COLUMN IF NOT EXISTS academic_cycle_id INTEGER;

UPDATE selection_window SET academic_cycle_id = (
    SELECT id FROM academic_cycle WHERE academic_year = '2025-2026' AND semester_type = 'EVEN'
) WHERE academic_cycle_id IS NULL;

-- selection_window may have 0 rows, so don't SET NOT NULL if empty
DO $$
BEGIN
    IF (SELECT count(*) FROM selection_window) > 0 THEN
        ALTER TABLE selection_window ALTER COLUMN academic_cycle_id SET NOT NULL;
    END IF;
END $$;

ALTER TABLE selection_window
    ADD CONSTRAINT fk_selection_window_cycle
    FOREIGN KEY (academic_cycle_id) REFERENCES academic_cycle(id);

-- ============================================================================
-- STEP 4: Indexes for cycle_id columns
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_subject_offering_cycle ON subject_offering(academic_cycle_id);
CREATE INDEX IF NOT EXISTS idx_faculty_preference_cycle ON faculty_preference(academic_cycle_id);
CREATE INDEX IF NOT EXISTS idx_allocation_cycle ON allocation(academic_cycle_id);
CREATE INDEX IF NOT EXISTS idx_workload_summary_cycle ON workload_summary(academic_cycle_id);
CREATE INDEX IF NOT EXISTS idx_selection_window_cycle ON selection_window(academic_cycle_id);
CREATE INDEX IF NOT EXISTS idx_academic_cycle_active ON academic_cycle(is_active);

COMMIT;
