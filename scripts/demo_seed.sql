-- ============================================================================
-- DEMO SEED — One-Click Workflow Preparation
-- ============================================================================
-- Idempotent: safe to run multiple times (deletes + re-inserts).
-- NOTE: Run allocation via API after this: POST /api/allocation/run
-- ============================================================================

BEGIN;

DO $$
DECLARE
    v_cycle_id INT;
    v_coord_id INT;
    v_window_id INT;
    v_staff RECORD;
    v_offering RECORD;
    v_pref_num INT;
    v_total_prefs INT := 0;
    v_staff_count INT := 0;
BEGIN

    -- Step 1: Get active academic cycle
    SELECT id INTO v_cycle_id FROM academic_cycle WHERE is_active = true LIMIT 1;
    IF v_cycle_id IS NULL THEN
        INSERT INTO academic_cycle (academic_year, semester_type, is_active)
        VALUES ('2025-2026', 'EVEN', true)
        RETURNING id INTO v_cycle_id;
    END IF;
    RAISE NOTICE 'Step 1: cycle_id=%', v_cycle_id;

    -- Step 2: Get coordinator
    SELECT id INTO v_coord_id
    FROM staff WHERE is_coordinator = true AND is_active = true
    ORDER BY id LIMIT 1;
    IF v_coord_id IS NULL THEN
        SELECT id INTO v_coord_id FROM staff WHERE is_active = true ORDER BY id LIMIT 1;
    END IF;
    RAISE NOTICE 'Step 2: coordinator_id=%', v_coord_id;

    -- Step 3: Open preference window if needed
    SELECT id INTO v_window_id FROM selection_window WHERE status = 'OPEN' LIMIT 1;
    IF v_window_id IS NULL THEN
        INSERT INTO selection_window
            (name, batch_id, specialization_id, start_time, end_time,
             status, max_subjects_per_staff, academic_cycle_id,
             allocation_locked)
        VALUES (
            'Demo Window', 1, 1,
            NOW(), NOW() + INTERVAL '7 days',
            'OPEN', 5, v_cycle_id, false
        )
        RETURNING id INTO v_window_id;
        RAISE NOTICE 'Step 3: window opened id=%', v_window_id;
    ELSE
        RAISE NOTICE 'Step 3: window already open id=%', v_window_id;
    END IF;

    -- Step 4: Clear old data
    DELETE FROM allocation WHERE academic_cycle_id = v_cycle_id;
    DELETE FROM workload_summary WHERE academic_cycle_id = v_cycle_id;
    DELETE FROM faculty_preference WHERE academic_cycle_id = v_cycle_id;
    RAISE NOTICE 'Step 4: cleared old data';

    -- Step 5: Seed 5 shift-compatible preferences per faculty
    FOR v_staff IN
        SELECT id, shift FROM staff WHERE is_active = true ORDER BY id
    LOOP
        v_pref_num := 0;
        v_staff_count := v_staff_count + 1;

        FOR v_offering IN
            SELECT so.id
            FROM subject_offering so
            WHERE so.academic_cycle_id = v_cycle_id
              AND so.is_active = true
              AND (
                  v_staff.shift IS NULL
                  OR v_staff.shift = 'SHIFT1+SHIFT2'
                  OR (v_staff.shift = 'SHIFT1' AND so.shift = 1)
                  OR (v_staff.shift = 'SHIFT2' AND so.shift = 2)
              )
            ORDER BY RANDOM()
            LIMIT 5
        LOOP
            v_pref_num := v_pref_num + 1;
            INSERT INTO faculty_preference
                (staff_id, subject_offering_id, preference_number, academic_cycle_id)
            VALUES
                (v_staff.id, v_offering.id, v_pref_num, v_cycle_id);
            v_total_prefs := v_total_prefs + 1;
        END LOOP;
    END LOOP;

    RAISE NOTICE 'Step 5: seeded % preferences for % faculty', v_total_prefs, v_staff_count;
    RAISE NOTICE 'DONE — now run: POST /api/allocation/run';

END $$;

COMMIT;
