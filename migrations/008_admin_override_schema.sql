-- ============================================================================
-- Migration 008: Admin Override Schema Extension
-- Purpose: Add allocation_locked flag + expand audit_log action types
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Add allocation_locked column to selection_window
-- When true: preferences cannot be submitted, allocation cannot be re-run
-- ============================================================================

ALTER TABLE selection_window ADD COLUMN IF NOT EXISTS allocation_locked BOOLEAN NOT NULL DEFAULT false;

-- ============================================================================
-- STEP 2: Expand audit_log action types for admin operations
-- ============================================================================

ALTER TABLE audit_log DROP CONSTRAINT IF EXISTS chk_audit_log_action_type;

ALTER TABLE audit_log ADD CONSTRAINT chk_audit_log_action_type 
  CHECK (action_type IN (
    -- Existing FCFS action types (FSB v1.3)
    'SELECT', 'CHANGE', 'OVERRIDE',
    -- Window lifecycle action types
    'WINDOW_CREATED', 'WINDOW_SCHEDULED', 'WINDOW_OPENED', 
    'WINDOW_CLOSED', 'WINDOW_ARCHIVED',
    -- Preference system action types
    'PREFERENCE_SUBMITTED', 'PREFERENCE_CLEARED',
    -- Allocation engine action types
    'ALLOCATION_CREATED', 'ALLOCATION_REMOVED',
    'WORKLOAD_CALCULATED', 'APPROVAL_GRANTED',
    -- Admin override action types (NEW)
    'ALLOCATION_OVERRIDE', 'ALLOCATION_REASSIGN',
    'ALLOCATION_FREEZE', 'ALLOCATION_UNFREEZE'
  ));

COMMIT;
