-- ============================================================================
-- Migration 024: Fix Preference Window Semester Mismatch
-- Problem: Window points to semester 3 (0 offerings), active cycle is semester 2 (78 offerings)
-- Solution: Close wrong window and create new window for semester 2
-- ============================================================================

BEGIN;

-- Close all open windows
UPDATE selection_window SET status = 'CLOSED' WHERE status = 'OPEN';

-- Create new window for correct cycle (semester 2)
INSERT INTO selection_window (name, batch_id, specialization_id, start_time, end_time, status, max_subjects_per_staff, cycle_id, allocation_locked)
SELECT 
    'Preference Window 2025-2026 Sem-2',
    1, 
    1,
    NOW(),
    NOW() + INTERVAL '7 days',
    'OPEN',
    5,
    c.id,
    false
FROM cycle c
WHERE c.semester_id = 2 AND c.status = 'OPEN'
LIMIT 1;

-- Verify
DO $$
DECLARE 
    win_id INTEGER; 
    cyc_id INTEGER;
    sem_id INTEGER;
BEGIN
    SELECT sw.id, sw.cycle_id, c.semester_id 
    INTO win_id, cyc_id, sem_id
    FROM selection_window sw
    JOIN cycle c ON c.id = sw.cycle_id
    WHERE sw.status = 'OPEN' 
    LIMIT 1;
    
    RAISE NOTICE '024_fix: window=%, cycle=%, semester=%', win_id, cyc_id, sem_id;
END $$;

COMMIT;
