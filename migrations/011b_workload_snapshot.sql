-- ============================================================================
-- Migration 011: Workload Snapshot & Cycle Locking
-- Purpose: Add immutable snapshot table for approved workload data
--          and locking mechanism on academic_cycle
-- ============================================================================

-- ============================================================================
-- STEP 1: Create workload_snapshot table (immutable after insert)
-- ============================================================================

CREATE TABLE IF NOT EXISTS workload_snapshot (
    id            BIGSERIAL PRIMARY KEY,
    academic_year VARCHAR(20) NOT NULL,
    semester_type VARCHAR(10) NOT NULL,
    approved_by   BIGINT NOT NULL,
    snapshot_data  JSONB NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_snapshot_approved_by
        FOREIGN KEY (approved_by) REFERENCES staff(id) ON DELETE RESTRICT,
    CONSTRAINT chk_snapshot_semester_type
        CHECK (semester_type IN ('ODD', 'EVEN'))
);

-- One snapshot per cycle (immutable — no updates allowed)
CREATE UNIQUE INDEX IF NOT EXISTS uq_snapshot_cycle
    ON workload_snapshot(academic_year, semester_type);

-- Performance index
CREATE INDEX IF NOT EXISTS idx_snapshot_lookup
    ON workload_snapshot(academic_year, semester_type);

-- ============================================================================
-- STEP 2: Add is_locked to academic_cycle
-- ============================================================================

ALTER TABLE academic_cycle
    ADD COLUMN IF NOT EXISTS is_locked BOOLEAN NOT NULL DEFAULT false;

-- ============================================================================
-- STEP 3: Prevent DELETE on workload_snapshot (database-level immutability)
-- ============================================================================

CREATE OR REPLACE FUNCTION prevent_snapshot_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'workload_snapshot is immutable: % operations are forbidden', TG_OP;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_snapshot_no_update ON workload_snapshot;
CREATE TRIGGER trg_snapshot_no_update
    BEFORE UPDATE ON workload_snapshot
    FOR EACH ROW
    EXECUTE FUNCTION prevent_snapshot_mutation();

DROP TRIGGER IF EXISTS trg_snapshot_no_delete ON workload_snapshot;
CREATE TRIGGER trg_snapshot_no_delete
    BEFORE DELETE ON workload_snapshot
    FOR EACH ROW
    EXECUTE FUNCTION prevent_snapshot_mutation();

-- ============================================================================
-- END OF MIGRATION 011
-- ============================================================================
