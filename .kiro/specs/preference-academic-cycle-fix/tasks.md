# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Schema Column Reference Errors
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: For deterministic bugs, scope the property to the concrete failing case(s) to ensure reproducibility
  - Test that queries referencing `so.academic_cycle_id` or `a.academic_cycle_id` fail with "column does not exist" errors
  - Test cases:
    - Call `GET /api/preferences/me` as authenticated faculty (expect PostgreSQL error: "column so.academic_cycle_id does not exist")
    - Call `GET /api/pref-window/status` as coordinator (expect PostgreSQL error: "column so.academic_cycle_id does not exist")
    - Call `POST /api/allocation/run` with valid semester_id (expect PostgreSQL error: "column so.academic_cycle_id does not exist")
    - Call `DELETE /api/admin/staff/{id}` for staff with allocations (expect PostgreSQL error: "column a.academic_cycle_id does not exist")
  - The test assertions should match the Expected Behavior Properties from design (queries execute successfully after fix)
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Query Operations Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs (operations not involving cycle queries)
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements
  - Test cases:
    - Preference submission: Submit new preference and verify validation rules (PREF-01 through PREF-05, SHIFT-01, CT-01) work correctly
    - Window lifecycle: Open and close preference window, verify state transitions work correctly
    - Semester state transitions: Open, close, and allocate semester, verify state machine works correctly
    - Audit logging: Verify all operations generate correct audit log entries
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix SQL queries to use new cycle table schema

  - [x] 3.1 Fix preference service query (app/preference/service.py line 356-374)
    - Replace direct `so.academic_cycle_id` reference with JOIN through cycle table
    - Add JOIN: `JOIN cycle c ON c.academic_year_id = so.academic_year_id AND c.semester_id = so.semester_id`
    - Update WHERE clause: `AND c.id = :cid` instead of `AND so.academic_cycle_id = :cid`
    - _Bug_Condition: isBugCondition(query) where query.references("so.academic_cycle_id")_
    - _Expected_Behavior: Query executes successfully by joining through cycle table using academic_year_id and semester_id_
    - _Preservation: All preference submission validation rules continue to work unchanged_
    - _Requirements: 2.1, 3.1_

  - [x] 3.2 Fix semester state service query (app/coordinator/semester_state_service.py line 85-90)
    - Replace `so.academic_cycle_id` with JOIN through cycle table
    - Add JOIN: `LEFT JOIN cycle c ON c.semester_id = sem.id AND c.academic_year_id = so.academic_year_id`
    - Update SELECT: `c.id AS cycle_id` instead of `so.academic_cycle_id`
    - _Bug_Condition: isBugCondition(query) where query.references("so.academic_cycle_id")_
    - _Expected_Behavior: Query executes successfully and returns correct cycle_id_
    - _Preservation: Window lifecycle management continues to work unchanged_
    - _Requirements: 2.4, 3.2_

  - [x] 3.3 Fix allocation service offering query (app/allocation/service.py line 131-135)
    - Replace `WHERE so.academic_cycle_id = :cid` with JOIN through cycle table
    - Add JOIN: `JOIN cycle c ON c.academic_year_id = so.academic_year_id AND c.semester_id = so.semester_id`
    - Update WHERE clause: `WHERE c.id = :cid` instead of `WHERE so.academic_cycle_id = :cid`
    - _Bug_Condition: isBugCondition(query) where query.references("so.academic_cycle_id")_
    - _Expected_Behavior: Query executes successfully and filters offerings by cycle correctly_
    - _Preservation: Allocation algorithm logic remains unchanged_
    - _Requirements: 2.3, 3.3_

  - [x] 3.4 Fix allocation service workload summary query (app/allocation/service.py line 689-692)
    - Replace `a.academic_cycle_id = :cid` with `a.cycle_id = :cid` (allocation table already migrated correctly)
    - Simplify query to use existing `allocation.cycle_id` column directly
    - _Bug_Condition: isBugCondition(query) where query.references("a.academic_cycle_id")_
    - _Expected_Behavior: Query executes successfully using allocation.cycle_id column_
    - _Preservation: Workload calculation produces identical results_
    - _Requirements: 2.3, 3.4_

  - [x] 3.5 Fix staff service deactivation query (app/admin/staff_service.py line 207-209)
    - Replace `JOIN academic_cycle ac ON ac.id = a.academic_cycle_id` with `JOIN cycle c ON c.id = a.cycle_id`
    - Replace `ac.is_active = true` with `c.status != 'FROZEN'`
    - _Bug_Condition: isBugCondition(query) where query.references("a.academic_cycle_id") OR query.joins("academic_cycle")_
    - _Expected_Behavior: Query executes successfully using cycle table and status field_
    - _Preservation: Staff deactivation validation continues to work unchanged_
    - _Requirements: 1.4, 3.4_

  - [x] 3.6 Fix demo script query (scripts/demo_prep.py line 144-146)
    - Replace direct `so.academic_cycle_id` reference with JOIN through cycle table
    - Add JOIN: `JOIN cycle c ON c.academic_year_id = so.academic_year_id AND c.semester_id = so.semester_id`
    - Update WHERE clause: `WHERE c.id = {cycle_id}` instead of `WHERE so.academic_cycle_id = {cycle_id}`
    - _Bug_Condition: isBugCondition(query) where query.references("so.academic_cycle_id")_
    - _Expected_Behavior: Demo script generates preferences successfully_
    - _Preservation: Demo data generation logic remains unchanged_
    - _Requirements: 2.1_

  - [x] 3.7 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Schema-Compliant Queries Execute Successfully
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify all previously failing endpoints now return successful responses:
      - `GET /api/preferences/me` returns preferences with correct subject details
      - `GET /api/pref-window/status` returns window status with correct cycle information
      - `POST /api/allocation/run` creates allocations successfully
      - `DELETE /api/admin/staff/{id}` validates active allocations correctly
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.8 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Query Operations Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions):
      - Preference submission validation rules work correctly
      - Window lifecycle state transitions work correctly
      - Semester state machine works correctly
      - Audit logging generates correct entries
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
  - Verify no PostgreSQL "column does not exist" errors
  - Verify all affected endpoints return correct data
  - Verify no regressions in existing functionality
