-- 3-Role System Migration
-- Adds role column to staff table, replacing is_coordinator boolean logic

ALTER TABLE staff ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'faculty';

-- Assign roles based on current data
UPDATE staff SET role = 'hod' WHERE id = 1;
UPDATE staff SET role = 'tt_coordinator' WHERE id = 3;
UPDATE staff SET role = 'faculty' WHERE role IS NULL OR role = 'faculty';

-- Verify
SELECT id, name, email, is_coordinator, role FROM staff ORDER BY id;
