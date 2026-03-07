-- Step-by-step debug: each step separated
-- Run each block individually to find the error

-- Test A: cycle exists?
SELECT id, academic_year, semester_type, is_active FROM academic_cycle;

-- Test B: coordinator exists?
SELECT id, name, is_coordinator FROM staff WHERE is_coordinator = true LIMIT 1;

-- Test C: selection_window?
SELECT id, status, academic_year FROM selection_window LIMIT 3;

-- Test D: can we delete prefs?
SELECT count(*) AS pref_count FROM faculty_preference WHERE academic_cycle_id = 1;

-- Test E: can we delete allocations?
SELECT count(*) AS alloc_count FROM allocation WHERE academic_cycle_id = 1;

-- Test F: can we delete workload_summary?
SELECT count(*) AS wl_count FROM workload_summary WHERE academic_cycle_id = 1;

-- Test G: count compatible offerings for staff_id=1
SELECT s.shift, count(so.id) AS compatible
FROM staff s, subject_offering so
WHERE s.id = 1
  AND so.academic_cycle_id = 1
  AND so.is_active = true
  AND (
      s.shift IS NULL
      OR s.shift = 'SHIFT1+SHIFT2'
      OR (s.shift = 'SHIFT1' AND so.shift = 1)
      OR (s.shift = 'SHIFT2' AND so.shift = 2)
  )
GROUP BY s.shift;
