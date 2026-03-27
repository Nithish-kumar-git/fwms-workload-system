-- ============================================================================
-- Migration 022: Fix Production Database State (Idempotent)
-- Purpose: Repair failed migration 021 on Railway production
-- Safe to run multiple times - uses IF NOT EXISTS and ON CONFLICT
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Create indexes that failed in migration 021
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_cycle_status ON cycle(status);
CREATE INDEX IF NOT EXISTS idx_cycle_academic_year ON cycle(academic_year_id);
CREATE INDEX IF NOT EXISTS idx_cycle_semester ON cycle(semester_id);

-- ============================================================================
-- STEP 2: Ensure academic_year table has 2025-2026
-- ============================================================================

INSERT INTO academic_year (name, start_date, end_date)
VALUES ('2025-2026', '2025-07-01', '2026-04-30')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- STEP 3: Ensure academic_year_id column exists in subject_offering
-- ============================================================================

ALTER TABLE subject_offering 
    ADD COLUMN IF NOT EXISTS academic_year_id INTEGER;

-- ============================================================================
-- STEP 4: Populate academic_year_id where null
-- ============================================================================

UPDATE subject_offering so
SET academic_year_id = ay.id
FROM academic_year ay
WHERE so.academic_year = ay.name
  AND so.academic_year_id IS NULL;

-- ============================================================================
-- STEP 5: Add foreign key constraint if not exists
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_subject_offering_academic_year'
    ) THEN
        ALTER TABLE subject_offering
            ADD CONSTRAINT fk_subject_offering_academic_year 
            FOREIGN KEY (academic_year_id) REFERENCES academic_year(id);
    END IF;
END $$;

-- ============================================================================
-- STEP 6: Ensure cycles exist for semesters 2, 4, 6
-- ============================================================================

-- Cycle for Semester II (OPEN)
INSERT INTO cycle (academic_year_id, semester_id, status)
SELECT ay.id, 2, 'OPEN'
FROM academic_year ay 
WHERE ay.name = '2025-2026'
ON CONFLICT (academic_year_id, semester_id) DO NOTHING;

-- Cycle for Semester IV (CLOSED)
INSERT INTO cycle (academic_year_id, semester_id, status)
SELECT ay.id, 4, 'CLOSED'
FROM academic_year ay 
WHERE ay.name = '2025-2026'
ON CONFLICT (academic_year_id, semester_id) DO NOTHING;

-- Cycle for Semester VI (CLOSED)
INSERT INTO cycle (academic_year_id, semester_id, status)
SELECT ay.id, 6, 'CLOSED'
FROM academic_year ay 
WHERE ay.name = '2025-2026'
ON CONFLICT (academic_year_id, semester_id) DO NOTHING;

-- ============================================================================
-- STEP 7: Verify and log results
-- ============================================================================

DO $$
DECLARE
    ay_count INTEGER;
    cycle_count INTEGER;
    offering_count INTEGER;
    offering_with_year_id INTEGER;
BEGIN
    SELECT COUNT(*) INTO ay_count FROM academic_year;
    SELECT COUNT(*) INTO cycle_count FROM cycle;
    SELECT COUNT(*) INTO offering_count FROM subject_offering;
    SELECT COUNT(*) INTO offering_with_year_id FROM subject_offering WHERE academic_year_id IS NOT NULL;
    
    RAISE NOTICE '=== MIGRATION 022 COMPLETE ===';
    RAISE NOTICE 'Academic years: %', ay_count;
    RAISE NOTICE 'Cycles: %', cycle_count;
    RAISE NOTICE 'Subject offerings total: %', offering_count;
    RAISE NOTICE 'Subject offerings with academic_year_id: %', offering_with_year_id;
END $$;

COMMIT;
