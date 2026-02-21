-- ============================================================================
-- Window Lifecycle Migration
-- Adds status-based lifecycle management to selection_window table
-- Spec reference: window_lifecycle_design.md
-- ============================================================================

-- Step 1: Add status column with default DRAFT
ALTER TABLE selection_window 
ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'DRAFT';

-- Step 2: Add batch_id and specialization_id columns (NOT NULL)
ALTER TABLE selection_window
ADD COLUMN batch_id BIGINT NOT NULL,
ADD COLUMN specialization_id BIGINT NOT NULL;

-- Step 3: Add foreign key constraints
ALTER TABLE selection_window
ADD CONSTRAINT fk_window_batch 
  FOREIGN KEY (batch_id) REFERENCES batch(id) ON DELETE RESTRICT;

ALTER TABLE selection_window
ADD CONSTRAINT fk_window_specialization 
  FOREIGN KEY (specialization_id) REFERENCES specialization(id) ON DELETE RESTRICT;

-- Step 4: Add state domain constraint
ALTER TABLE selection_window
ADD CONSTRAINT chk_window_status 
  CHECK (status IN ('DRAFT', 'SCHEDULED', 'OPEN', 'CLOSED', 'ARCHIVED'));

-- Step 5: Pre-index duplicate OPEN window detection
-- CRITICAL: Detect duplicate OPEN windows BEFORE creating unique index
-- If duplicates exist, migration will fail with clear error message
DO $$
DECLARE
    duplicate_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO duplicate_count
    FROM (
        SELECT batch_id, specialization_id, COUNT(*) as open_count
        FROM selection_window
        WHERE status = 'OPEN'
        GROUP BY batch_id, specialization_id
        HAVING COUNT(*) > 1
    ) duplicates;
    
    IF duplicate_count > 0 THEN
        RAISE EXCEPTION 'Migration failed: % duplicate OPEN windows detected. Close duplicate windows before migration.', duplicate_count;
    END IF;
    
    RAISE NOTICE 'Pre-index validation passed: No duplicate OPEN windows found';
END $$;

-- Step 6: Create partial unique index (single OPEN window per batch/spec)
CREATE UNIQUE INDEX uq_one_open_window_per_batch_spec
ON selection_window(batch_id, specialization_id)
WHERE status = 'OPEN';

COMMENT ON INDEX uq_one_open_window_per_batch_spec IS 
'CRITICAL: Enforces single OPEN window per (batch_id, specialization_id)';

-- Step 7: Create immutability trigger for start_time and end_time
CREATE OR REPLACE FUNCTION prevent_window_time_update()
RETURNS TRIGGER AS $$
BEGIN
    -- Allow updates if new status is DRAFT
    IF NEW.status = 'DRAFT' THEN
        RETURN NEW;
    END IF;
    
    -- Prevent start_time or end_time changes after SCHEDULED
    -- Use IS DISTINCT FROM to handle NULL comparisons correctly
    IF NEW.start_time IS DISTINCT FROM OLD.start_time OR 
       NEW.end_time IS DISTINCT FROM OLD.end_time THEN
        RAISE EXCEPTION 'start_time and end_time are immutable after SCHEDULED state';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_window_time_update
BEFORE UPDATE ON selection_window
FOR EACH ROW
EXECUTE FUNCTION prevent_window_time_update();

COMMENT ON TRIGGER trg_prevent_window_time_update ON selection_window IS
'CRITICAL: Prevents modification of start_time/end_time after SCHEDULED state';

-- Step 8: Update audit_log action_type constraint
ALTER TABLE audit_log
DROP CONSTRAINT chk_audit_log_action_type;

ALTER TABLE audit_log
ADD CONSTRAINT chk_audit_log_action_type 
  CHECK (action_type IN (
    'SELECT', 'CHANGE', 'OVERRIDE', 
    'WINDOW_CREATED', 'WINDOW_SCHEDULED', 'WINDOW_OPENED', 
    'WINDOW_CLOSED', 'WINDOW_ARCHIVED'
  ));

-- Step 9: Add index on window status for performance
CREATE INDEX idx_selection_window_status ON selection_window(status);

-- Step 10: Add composite index for batch/spec lookups
CREATE INDEX idx_selection_window_batch_spec 
ON selection_window(batch_id, specialization_id);

-- ============================================================================
-- Data Migration (if needed)
-- ============================================================================

-- Migrate existing windows based on is_active and time range
-- This is a one-time migration for existing data
UPDATE selection_window
SET status = CASE
  WHEN is_active = true AND now() BETWEEN start_time AND end_time THEN 'OPEN'
  WHEN is_active = true AND now() < start_time THEN 'SCHEDULED'
  WHEN is_active = false THEN 'CLOSED'
  ELSE 'DRAFT'
END
WHERE status = 'DRAFT';  -- Only update rows that haven't been migrated

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify single OPEN window constraint
-- Should return 0 or 1 row per (batch_id, specialization_id)
SELECT batch_id, specialization_id, COUNT(*) as open_count
FROM selection_window
WHERE status = 'OPEN'
GROUP BY batch_id, specialization_id
HAVING COUNT(*) > 1;

-- Verify all windows have valid status
SELECT status, COUNT(*) 
FROM selection_window 
GROUP BY status;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
