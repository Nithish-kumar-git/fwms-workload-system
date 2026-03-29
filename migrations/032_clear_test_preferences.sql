-- Migration 032: Clear test preference submissions for fresh staff testing
-- Purpose: Remove all faculty_preference test data while preserving staff, subjects, allocations, and cycles
-- Date: 2026-03-29

-- Clear only preference submissions, keep everything else intact
DELETE FROM faculty_preference;

-- Reset preference window to open so staff can submit fresh
UPDATE preference_window SET is_open = true WHERE id = (SELECT MAX(id) FROM preference_window);

-- Verification queries
SELECT COUNT(*) AS preferences_remaining FROM faculty_preference;
SELECT is_open FROM preference_window ORDER BY id DESC LIMIT 1;
