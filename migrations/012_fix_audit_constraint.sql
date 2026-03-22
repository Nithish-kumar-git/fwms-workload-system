-- ============================================================================
-- Migration 012: Expand audit_log action_type constraint
-- Purpose: Fix CRITICAL constraint mismatch between backend code and DB
--
-- Backend code emits these action_types that are NOT in migration 009:
--   SELECT, CHANGE, OVERRIDE         (FCFS subsystem)
--   STAFF_CREATED, STAFF_UPDATED, STAFF_DEACTIVATED  (staff management)
--
-- This migration adds those values while retaining all existing values
-- for backward compatibility. No code changes required.
-- ============================================================================

BEGIN;

ALTER TABLE audit_log DROP CONSTRAINT IF EXISTS chk_audit_log_action_type;

ALTER TABLE audit_log ADD CONSTRAINT chk_audit_log_action_type
CHECK (action_type IN (
    -- FCFS selection (legacy names from original schema.sql / code)
    'SELECT', 'CHANGE', 'OVERRIDE',

    -- FCFS selection (migration-009 names — retained for compatibility)
    'SUBJECT_SELECTED', 'SUBJECT_DESELECTED',
    'SELECTION_LOCKED', 'SELECTION_UNLOCKED',
    'COORDINATOR_OVERRIDE',

    -- Window lifecycle
    'WINDOW_CREATED', 'WINDOW_SCHEDULED', 'WINDOW_OPENED',
    'WINDOW_CLOSED', 'WINDOW_ARCHIVED',

    -- Preference system
    'PREFERENCE_SUBMITTED', 'PREFERENCE_CLEARED',

    -- Allocation engine
    'ALLOCATION_RUN',

    -- Admin overrides
    'ALLOCATION_OVERRIDE', 'ALLOCATION_REASSIGN',
    'ALLOCATION_FREEZE', 'ALLOCATION_UNFREEZE',

    -- Staff management (added by staff_service.py)
    'STAFF_CREATED', 'STAFF_UPDATED', 'STAFF_DEACTIVATED'
));

COMMIT;
