-- Migration 032: Clear test preference submissions for fresh staff testing
-- Purpose: Remove all faculty_preference test data while preserving staff, subjects, allocations, and cycles
-- Date: 2026-03-29

-- Clear only preference submissions, keep everything else intact
DELETE FROM faculty_preference;

-- Reset selection window to open so staff can submit fresh
-- Note: Table is called selection_window (not preference_window) and uses status column (not is_open)
UPDATE selection_window SET status = 'OPEN' WHERE id = (SELECT MAX(id) FROM selection_window);

-- Verification queries
SELECT COUNT(*) AS preferences_remaining FROM faculty_preference;
SELECT status FROM selection_window ORDER BY id DESC LIMIT 1;
