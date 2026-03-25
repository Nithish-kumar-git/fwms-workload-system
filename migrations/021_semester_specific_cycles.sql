-- ============================================================================
-- Migration 021: Semester-Specific Cycles Architecture
-- REMOVES: ODD/EVEN semester_type system
-- ADDS: Direct semester-specific cycle model
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Create new academic_year table (time only)
-- ============================================================================

CREATE TABLE IF NOT EXISTS academic_year (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(20) NOT NULL UNIQUE,  -- e.g. "2025-2026"
    start_date      DATE,
    end_date        DATE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE academic_year IS 'Academic year represents time period only, independent of semester structure';

-- ============================================================================
-- STEP 2: Update semester table to include program_id
-- ============================================================================

-- Add program_id to semester (which semester belongs to which program)
ALTER TABLE semester
    ADD COLUMN IF NOT EXISTS program_id BIGINT;

-- For existing semesters (I-VI), they apply to ALL programs, so we'll handle this differently
-- We'll keep program_id NULL for universal semesters
-- Later, program-specific semesters can be added if needed

COMMENT ON COLUMN semester.program_id IS 'NULL means semester applies to all programs. Specific program_id means semester is program-specific.';

-- ============================================================================
-- STEP 3: Create new cycle table (workflow controller)
-- ============================================================================

CREATE TABLE IF NOT EXISTS cycle (
    id                  SERIAL PRIMARY KEY,
    academic_year_id    INTEGER NOT NULL,
    semester_id         BIGINT NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'CLOSED',
    opened_at           TIMESTAMP,
    closed_at           TIMESTAMP,
    allocated_at        TIMESTAMP,
    frozen_at           TIMESTAMP,
    frozen_by_staff_id  BIGINT,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_cycle_academic_year FOREIGN KEY (academic_year_id) REFERENCES academic_year(id),
    CONSTRAINT fk_cycle_semester FOREIGN KEY (semester_id) REFERENCES semester(id),
    CONSTRAINT fk_cycle_frozen_by FOREIGN KEY (frozen_by_staff_id) REFERENCES staff(id),
    CONSTRAINT uq_cycle_year_semester UNIQUE (academic_year_id, semester_id),
    CONSTRAINT chk_cycle_status CHECK (status IN ('OPEN', 'CLOSED', 'ALLOCATED', 'FROZEN'))
);

CREATE INDEX idx_cycle_status ON cycle(status);
CREATE INDEX idx_cycle_academic_year ON cycle(academic_year_id);
CREATE INDEX idx_cycle_semester ON cycle(semester_id);

COMMENT ON TABLE cycle IS 'Cycle controls preference window workflow for a specific academic year + semester combination';

-- ============================================================================
-- STEP 4: Migrate existing data
-- ============================================================================

-- 4a. Extract unique academic years from old academic_cycle
INSERT INTO academic_year (name)
SELECT DISTINCT academic_year 
FROM academic_cycle
ON CONFLICT (name) DO NOTHING;

-- 4b. Create new cycles from old academic_cycle
-- For each old cycle with semester_type='EVEN', create cycles for semesters II, IV, VI
-- For each old cycle with semester_type='ODD', create cycles for semesters I, III, V

-- Get the current active cycle info
DO $$
DECLARE
    old_cycle_id INTEGER;
    old_year VARCHAR(20);
    old_sem_type VARCHAR(10);
    old_is_active BOOLEAN;
    old_is_locked BOOLEAN;
    new_year_id INTEGER;
    sem_id BIGINT;
    new_cycle_id INTEGER;
BEGIN
    -- Process each old academic_cycle
    FOR old_cycle_id, old_year, old_sem_type, old_is_active, old_is_locked IN
        SELECT id, academic_year, semester_type, is_active, is_locked
        FROM academic_cycle
    LOOP
        -- Get academic_year_id
        SELECT id INTO new_year_id FROM academic_year WHERE name = old_year;
        
        -- Create cycles for appropriate semesters
        IF old_sem_type = 'EVEN' THEN
            -- Create cycles for semesters II, IV, VI
            FOR sem_id IN
                SELECT id FROM semester WHERE label IN ('II', 'IV', 'VI')
            LOOP
                INSERT INTO cycle (academic_year_id, semester_id, status, created_at)
                VALUES (
                    new_year_id,
                    sem_id,
                    CASE WHEN old_is_locked THEN 'FROZEN' WHEN old_is_active THEN 'OPEN' ELSE 'CLOSED' END,
                    NOW()
                )
                ON CONFLICT (academic_year_id, semester_id) DO NOTHING
                RETURNING id INTO new_cycle_id;
                
                RAISE NOTICE 'Created cycle % for year % semester %', new_cycle_id, old_year, sem_id;
            END LOOP;
        ELSIF old_sem_type = 'ODD' THEN
            -- Create cycles for semesters I, III, V
            FOR sem_id IN
                SELECT id FROM semester WHERE label IN ('I', 'III', 'V')
            LOOP
                INSERT INTO cycle (academic_year_id, semester_id, status, created_at)
                VALUES (
                    new_year_id,
                    sem_id,
                    CASE WHEN old_is_locked THEN 'FROZEN' WHEN old_is_active THEN 'OPEN' ELSE 'CLOSED' END,
                    NOW()
                )
                ON CONFLICT (academic_year_id, semester_id) DO NOTHING
                RETURNING id INTO new_cycle_id;
                
                RAISE NOTICE 'Created cycle % for year % semester %', new_cycle_id, old_year, sem_id;
            END LOOP;
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- STEP 5: Update subject_offering to use academic_year_id
-- ============================================================================

-- Add academic_year_id column
ALTER TABLE subject_offering
    ADD COLUMN IF NOT EXISTS academic_year_id INTEGER;

-- Populate academic_year_id from academic_year string
UPDATE subject_offering so
SET academic_year_id = ay.id
FROM academic_year ay
WHERE so.academic_year = ay.name;

-- Make it NOT NULL after population
ALTER TABLE subject_offering
    ALTER COLUMN academic_year_id SET NOT NULL;

-- Add foreign key
ALTER TABLE subject_offering
    ADD CONSTRAINT fk_subject_offering_academic_year 
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(id);

-- ============================================================================
-- STEP 6: Update faculty_preference to use new cycle_id
-- ============================================================================

-- Add new_cycle_id column temporarily
ALTER TABLE faculty_preference
    ADD COLUMN IF NOT EXISTS new_cycle_id INTEGER;

-- Map old preferences to new cycles based on semester
UPDATE faculty_preference fp
SET new_cycle_id = c.id
FROM subject_offering so
JOIN semester s ON so.semester_id = s.id
JOIN academic_year ay ON so.academic_year = ay.name
JOIN cycle c ON c.academic_year_id = ay.id AND c.semester_id = s.id
WHERE fp.subject_offering_id = so.id;

-- Verify all preferences were mapped
DO $$
DECLARE
    unmapped_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO unmapped_count
    FROM faculty_preference
    WHERE new_cycle_id IS NULL;
    
    IF unmapped_count > 0 THEN
        RAISE EXCEPTION 'Migration failed: % preferences could not be mapped to new cycles', unmapped_count;
    END IF;
    
    RAISE NOTICE 'All preferences successfully mapped to new cycles';
END $$;

-- ============================================================================
-- STEP 7: Update allocation table to use new cycle_id
-- ============================================================================

-- Add new_cycle_id column temporarily
ALTER TABLE allocation
    ADD COLUMN IF NOT EXISTS new_cycle_id INTEGER;

-- Map old allocations to new cycles based on semester
UPDATE allocation a
SET new_cycle_id = c.id
FROM subject_offering so
JOIN semester s ON so.semester_id = s.id
JOIN academic_year ay ON so.academic_year = ay.name
JOIN cycle c ON c.academic_year_id = ay.id AND c.semester_id = s.id
WHERE a.subject_offering_id = so.id;

-- ============================================================================
-- STEP 8: Drop old foreign keys and rename new columns
-- ============================================================================

-- Drop old constraints
ALTER TABLE faculty_preference
    DROP CONSTRAINT IF EXISTS fk_faculty_preference_cycle;

ALTER TABLE allocation
    DROP CONSTRAINT IF EXISTS fk_allocation_cycle;

ALTER TABLE subject_offering
    DROP CONSTRAINT IF EXISTS fk_subject_offering_cycle;

-- Rename academic_cycle_id to old_academic_cycle_id in all tables
ALTER TABLE faculty_preference
    RENAME COLUMN academic_cycle_id TO old_academic_cycle_id;

ALTER TABLE allocation
    RENAME COLUMN academic_cycle_id TO old_academic_cycle_id;

ALTER TABLE subject_offering
    RENAME COLUMN academic_cycle_id TO old_academic_cycle_id;

-- Rename new_cycle_id to cycle_id
ALTER TABLE faculty_preference
    RENAME COLUMN new_cycle_id TO cycle_id;

ALTER TABLE allocation
    RENAME COLUMN new_cycle_id TO cycle_id;

-- Make cycle_id NOT NULL
ALTER TABLE faculty_preference
    ALTER COLUMN cycle_id SET NOT NULL;

ALTER TABLE allocation
    ALTER COLUMN cycle_id SET NOT NULL;

-- Add new foreign keys
ALTER TABLE faculty_preference
    ADD CONSTRAINT fk_faculty_preference_cycle 
    FOREIGN KEY (cycle_id) REFERENCES cycle(id);

ALTER TABLE allocation
    ADD CONSTRAINT fk_allocation_cycle 
    FOREIGN KEY (cycle_id) REFERENCES cycle(id);

-- ============================================================================
-- STEP 9: Remove semester_type from subject_offering
-- ============================================================================

-- Drop the check constraint first
ALTER TABLE subject_offering
    DROP CONSTRAINT IF EXISTS chk_subject_offering_semester_type;

-- Drop the column
ALTER TABLE subject_offering
    DROP COLUMN IF EXISTS semester_type;

-- Drop the academic_year string column (now using academic_year_id)
-- Keep it for now for backward compatibility, but it's redundant
-- ALTER TABLE subject_offering DROP COLUMN IF EXISTS academic_year;

-- ============================================================================
-- STEP 10: Update selection_window table
-- ============================================================================

-- Check if selection_window exists and update it
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'selection_window') THEN
        -- Add new columns
        ALTER TABLE selection_window
            ADD COLUMN IF NOT EXISTS new_cycle_id INTEGER;
        
        -- Map to new cycles
        UPDATE selection_window sw
        SET new_cycle_id = (
            SELECT c.id
            FROM academic_cycle ac
            JOIN academic_year ay ON ac.academic_year = ay.name
            JOIN cycle c ON c.academic_year_id = ay.id
            WHERE sw.academic_cycle_id = ac.id
            LIMIT 1
        );
        
        -- Drop old FK
        ALTER TABLE selection_window
            DROP CONSTRAINT IF EXISTS fk_selection_window_cycle;
        
        -- Rename columns
        ALTER TABLE selection_window
            RENAME COLUMN academic_cycle_id TO old_academic_cycle_id;
        
        ALTER TABLE selection_window
            RENAME COLUMN new_cycle_id TO cycle_id;
        
        -- Add new FK
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'selection_window' AND column_name = 'cycle_id') THEN
            ALTER TABLE selection_window
                ADD CONSTRAINT fk_selection_window_cycle 
                FOREIGN KEY (cycle_id) REFERENCES cycle(id);
        END IF;
    END IF;
END $$;

-- ============================================================================
-- STEP 11: Update workload_summary table
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workload_summary') THEN
        ALTER TABLE workload_summary
            ADD COLUMN IF NOT EXISTS new_cycle_id INTEGER;
        
        UPDATE workload_summary ws
        SET new_cycle_id = (
            SELECT c.id
            FROM academic_cycle ac
            JOIN academic_year ay ON ac.academic_year = ay.name
            JOIN cycle c ON c.academic_year_id = ay.id
            WHERE ws.academic_cycle_id = ac.id
            LIMIT 1
        );
        
        ALTER TABLE workload_summary
            DROP CONSTRAINT IF EXISTS fk_workload_summary_cycle;
        
        ALTER TABLE workload_summary
            RENAME COLUMN academic_cycle_id TO old_academic_cycle_id;
        
        ALTER TABLE workload_summary
            RENAME COLUMN new_cycle_id TO cycle_id;
        
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'workload_summary' AND column_name = 'cycle_id') THEN
            ALTER TABLE workload_summary
                ADD CONSTRAINT fk_workload_summary_cycle 
                FOREIGN KEY (cycle_id) REFERENCES cycle(id);
        END IF;
    END IF;
END $$;

-- ============================================================================
-- STEP 12: Rename old academic_cycle table for backup
-- ============================================================================

ALTER TABLE academic_cycle RENAME TO academic_cycle_old_backup;

-- ============================================================================
-- VALIDATION
-- ============================================================================

DO $$
DECLARE
    cycle_count INTEGER;
    pref_count INTEGER;
    alloc_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO cycle_count FROM cycle;
    SELECT COUNT(*) INTO pref_count FROM faculty_preference WHERE cycle_id IS NOT NULL;
    SELECT COUNT(*) INTO alloc_count FROM allocation WHERE cycle_id IS NOT NULL;
    
    RAISE NOTICE '=== MIGRATION COMPLETE ===';
    RAISE NOTICE 'Created % new semester-specific cycles', cycle_count;
    RAISE NOTICE 'Migrated % preferences', pref_count;
    RAISE NOTICE 'Migrated % allocations', alloc_count;
    RAISE NOTICE 'Old academic_cycle table renamed to academic_cycle_old_backup';
END $$;

COMMIT;
