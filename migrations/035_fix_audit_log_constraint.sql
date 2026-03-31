-- ============================================================================
-- Migration 035: Add STAFF_ROLE_UPDATED to audit_log action_type constraint
-- Purpose: Fix check constraint violation when staff roles are updated
--
-- Error: new row for relation "audit_log" violates check constraint 
--        "chk_audit_log_action_type" with failing value: STAFF_ROLE_UPDATED
--
-- This migration adds STAFF_ROLE_UPDATED to the existing constraint values
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
    'STAFF_CREATED', 'STAFF_UPDATED', 'STAFF_DEACTIVATED',
    'STAFF_ROLE_UPDATED'
));

COMMIT;
