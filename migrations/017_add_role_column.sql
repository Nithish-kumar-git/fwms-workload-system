-- ============================================================================
-- Migration 017: Add Role Column to Staff Table
-- Purpose: Add 3-role system (faculty, tt_coordinator, hod) to staff table
-- Replaces is_coordinator boolean logic with explicit role column
-- ============================================================================

BEGIN;

-- Add role column with default 'faculty'
ALTER TABLE staff ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'faculty';

-- HARDCODED ROLE ASSIGNMENTS BY STAFF ID (DO NOT CHANGE)
UPDATE staff SET role = 'hod' WHERE id = 16;
UPDATE staff SET role = 'faculty' WHERE id = 17;
UPDATE staff SET role = 'tt_coordinator' WHERE id = 22;

-- Everyone else defaults to faculty
UPDATE staff SET role = 'faculty' WHERE role IS NULL OR role = '';

-- Add constraint for valid roles (drop first if exists to handle re-runs)
ALTER TABLE staff DROP CONSTRAINT IF EXISTS chk_staff_role;
ALTER TABLE staff ADD CONSTRAINT chk_staff_role 
CHECK (role IN ('faculty', 'tt_coordinator', 'hod'));

-- Add index for role-based queries
CREATE INDEX IF NOT EXISTS idx_staff_role ON staff(role);

COMMIT;

-- ============================================================================
-- END OF MIGRATION 017
-- ============================================================================
