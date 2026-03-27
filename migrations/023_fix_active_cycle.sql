-- ============================================================================
-- Migration 023: Fix Active Cycle (Semester 1 → Semester 2)
-- Problem: Active cycle is semester 1 (no data), but subject offerings exist for semester 2 (78 records)
-- Solution: Close ODD semesters (1,3,5) and open semester 2
-- ============================================================================

BEGIN;

-- Close wrong cycles (1 and 3 which have no subject offerings)
UPDATE cycle SET status = 'CLOSED' WHERE semester_id IN (1, 3, 5);

-- Open semester 2 cycle (has 78 subject offerings)
UPDATE cycle SET status = 'OPEN', opened_at = NOW() WHERE semester_id = 2;

-- Verify
DO $$
DECLARE
    active_sem INTEGER;
    offering_count INTEGER;
BEGIN
    SELECT c.semester_id INTO active_sem FROM cycle c WHERE c.status = 'OPEN' LIMIT 1;
    SELECT COUNT(*) INTO offering_count FROM subject_offering WHERE semester_id = active_sem;
    
    RAISE NOTICE '023_fix: active semester=%, offerings=%', active_sem, offering_count;
END $$;

COMMIT;
