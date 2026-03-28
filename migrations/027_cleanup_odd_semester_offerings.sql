-- ============================================================================
-- Migration 027: Cleanup Wrong Cartesian Product from Migration 026
-- Purpose: Delete all odd semester offerings (they were created incorrectly)
-- ============================================================================

BEGIN;

-- Delete all odd semester offerings created by migration 026 (cartesian product error)
DELETE FROM subject_offering 
WHERE semester_id IN (1, 3, 5)
AND academic_year_id = (SELECT id FROM academic_year WHERE name = '2025-2026');

-- Verify cleanup
DO $$
DECLARE 
    v_odd_count INTEGER;
    v_total_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_odd_count FROM subject_offering WHERE semester_id IN (1, 3, 5);
    SELECT COUNT(*) INTO v_total_count FROM subject_offering;
    
    RAISE NOTICE '027: odd semester offerings after cleanup=%', v_odd_count;
    RAISE NOTICE '027: total offerings remaining=%', v_total_count;
END $$;

COMMIT;
