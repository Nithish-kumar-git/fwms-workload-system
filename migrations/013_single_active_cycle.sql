-- ============================================================================
-- Migration 013: Enforce Single Active Academic Cycle
-- Purpose: Guarantee at most one academic_cycle row has is_active = true.
--
-- Without this constraint, two coordinators could accidentally activate
-- different cycles, breaking allocation, reports, and preferences.
--
-- Uses a partial unique index on a constant expression — PostgreSQL allows
-- only one row to satisfy the WHERE clause + indexed value combination.
-- ============================================================================

BEGIN;

-- Safety: check if more than one active cycle already exists
DO $$
DECLARE
    active_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO active_count
    FROM academic_cycle
    WHERE is_active = true;

    IF active_count > 1 THEN
        RAISE EXCEPTION 'Migration 013 blocked: % active cycles found. Deactivate extras before running.', active_count;
    END IF;
END $$;

-- Partial unique index: only one row with is_active = true
CREATE UNIQUE INDEX IF NOT EXISTS uq_one_active_cycle
ON academic_cycle (is_active)
WHERE is_active = true;

COMMENT ON INDEX uq_one_active_cycle IS
'CRITICAL: Enforces at most one active academic cycle at any time';

COMMIT;
