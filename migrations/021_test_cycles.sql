-- ============================================================================
-- Test Migration: Semester-Specific Cycles (Clean Schema Only)
-- For test environments - creates new schema without data migration
-- ============================================================================

BEGIN;

-- Create academic_year table
CREATE TABLE IF NOT EXISTS academic_year (
    id              SERIAL PRIMARY KEY,
    label           VARCHAR(20) NOT NULL UNIQUE,
    start_year      INTEGER NOT NULL,
    end_year        INTEGER NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create cycle table
CREATE TABLE IF NOT EXISTS cycle (
    id                  SERIAL PRIMARY KEY,
    academic_year_id    INTEGER NOT NULL REFERENCES academic_year(id) ON DELETE CASCADE,
    semester_id         BIGINT NOT NULL REFERENCES semester(id) ON DELETE CASCADE,
    status              VARCHAR(20) NOT NULL DEFAULT 'CLOSED',
    opened_at           TIMESTAMP,
    closed_at           TIMESTAMP,
    allocated_at        TIMESTAMP,
    frozen_at           TIMESTAMP,
    frozen_by_staff_id  BIGINT REFERENCES staff(id) ON DELETE SET NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(academic_year_id, semester_id)
);

CREATE INDEX IF NOT EXISTS idx_cycle_year ON cycle(academic_year_id);
CREATE INDEX IF NOT EXISTS idx_cycle_semester ON cycle(semester_id);
CREATE INDEX IF NOT EXISTS idx_cycle_status ON cycle(status);

-- Update subject_offering to use academic_year_id + semester_id
ALTER TABLE subject_offering
    ADD COLUMN IF NOT EXISTS academic_year_id INTEGER REFERENCES academic_year(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS semester_id BIGINT REFERENCES semester(id) ON DELETE CASCADE;

-- Update faculty_preference to use cycle_id
ALTER TABLE faculty_preference
    ADD COLUMN IF NOT EXISTS cycle_id INTEGER REFERENCES cycle(id) ON DELETE CASCADE;

-- Update selection_window to use cycle_id
ALTER TABLE selection_window
    ADD COLUMN IF NOT EXISTS cycle_id INTEGER REFERENCES cycle(id) ON DELETE CASCADE;

-- Update allocation to use cycle_id
ALTER TABLE allocation
    ADD COLUMN IF NOT EXISTS cycle_id INTEGER REFERENCES cycle(id) ON DELETE CASCADE;

COMMIT;
