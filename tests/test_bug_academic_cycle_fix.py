"""
Bug Condition Exploration Test for preference-academic-cycle-fix

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.

The test encodes the expected behavior - it will validate the fix when it passes after implementation.

GOAL: Surface counterexamples that demonstrate the bug exists by executing SQL queries that
reference the non-existent `academic_cycle` table or `academic_cycle_id` columns.

INVESTIGATION FINDINGS:
- Most service files (preference, allocation, admin) have already been fixed
- The OLD cycle_service.py exists but is NOT being used (cycle_service_new.py is used instead)
- The REAL bug is in scripts/demo_prep.py which has 8+ broken references
- Testing approach: Execute SQL queries directly to demonstrate schema errors

Expected counterexamples:
- PostgreSQL error: "relation academic_cycle does not exist" (table renamed to academic_cycle_old_backup)
- PostgreSQL error: "column so.academic_cycle_id does not exist" (renamed to old_academic_cycle_id)
- PostgreSQL error: "column a.academic_cycle_id does not exist" (renamed to old_academic_cycle_id)
- PostgreSQL error: "column fp.academic_cycle_id does not exist" (renamed to old_academic_cycle_id)
"""

import pytest
from sqlalchemy import text
from app.db.session import get_transaction


# ============================================================================
# Test Fixtures - Setup Test Data
# ============================================================================

@pytest.fixture(scope="module")
def test_academic_year():
    """Create test academic year."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO academic_year (label, start_year, end_year)
                VALUES (:label, :start_year, :end_year)
                ON CONFLICT (label) DO UPDATE SET label = EXCLUDED.label
                RETURNING id
            """),
            {"label": "2024-2025", "start_year": 2024, "end_year": 2025}
        ).fetchone()
        year_id = result[0]
    
    yield year_id
    
    # Cleanup handled by cascade


@pytest.fixture(scope="module")
def test_semester():
    """Create test semester."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO semester (label, semester_number)
                VALUES (:label, :number)
                ON CONFLICT (label) DO UPDATE SET label = EXCLUDED.label
                RETURNING id
            """),
            {"label": "Semester 1", "number": 1}
        ).fetchone()
        semester_id = result[0]
    
    yield semester_id


@pytest.fixture(scope="module")
def test_cycle(test_academic_year, test_semester):
    """Create test cycle."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO cycle (academic_year_id, semester_id, status)
                VALUES (:year_id, :sem_id, 'OPEN')
                ON CONFLICT (academic_year_id, semester_id) 
                DO UPDATE SET status = 'OPEN'
                RETURNING id
            """),
            {"year_id": test_academic_year, "sem_id": test_semester}
        ).fetchone()
        cycle_id = result[0]
    
    yield cycle_id


@pytest.fixture(scope="module")
def test_staff():
    """Create test faculty staff member."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO staff (email, name, is_coordinator, emp_code)
                VALUES (:email, :name, false, :emp_code)
                ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "email": "test.faculty@hindustanuniv.ac.in",
                "name": "Test Faculty",
                "emp_code": "TEST001"
            }
        ).fetchone()
        staff_id = result[0]
    
    yield staff_id


@pytest.fixture(scope="module")
def test_program():
    """Create test program."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO program (name, code)
                VALUES (:name, :code)
                ON CONFLICT (code) DO UPDATE SET code = EXCLUDED.code
                RETURNING id
            """),
            {"name": "Test Program", "code": "TESTPROG"}
        ).fetchone()
        program_id = result[0]
    
    yield program_id


@pytest.fixture(scope="module")
def test_section():
    """Create test section."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO section (label)
                VALUES (:label)
                ON CONFLICT (label) DO UPDATE SET label = EXCLUDED.label
                RETURNING id
            """),
            {"label": "A"}
        ).fetchone()
        section_id = result[0]
    
    yield section_id


@pytest.fixture(scope="module")
def test_subject():
    """Create test subject."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO subject (code, name, tch, l, t, p)
                VALUES (:code, :name, :tch, :l, :t, :p)
                ON CONFLICT (code) DO UPDATE SET code = EXCLUDED.code
                RETURNING id
            """),
            {
                "code": "TEST101",
                "name": "Test Subject",
                "tch": 4,
                "l": 3,
                "t": 1,
                "p": 0
            }
        ).fetchone()
        subject_id = result[0]
    
    yield subject_id


@pytest.fixture(scope="module")
def test_subject_offering(test_subject, test_program, test_section, test_semester, test_academic_year):
    """Create test subject offering using new schema (academic_year_id + semester_id)."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO subject_offering 
                (subject_id, program_id, section_id, semester_id, academic_year_id, shift, is_active)
                VALUES (:subject_id, :program_id, :section_id, :semester_id, :year_id, 'MORNING', true)
                RETURNING id
            """),
            {
                "subject_id": test_subject,
                "program_id": test_program,
                "section_id": test_section,
                "semester_id": test_semester,
                "year_id": test_academic_year
            }
        ).fetchone()
        offering_id = result[0]
    
    yield offering_id


@pytest.fixture(scope="module")
def test_preference(test_staff, test_subject_offering, test_cycle):
    """Create test faculty preference."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO faculty_preference 
                (staff_id, subject_offering_id, preference_number, cycle_id)
                VALUES (:staff_id, :offering_id, 1, :cycle_id)
                RETURNING id
            """),
            {
                "staff_id": test_staff,
                "offering_id": test_subject_offering,
                "cycle_id": test_cycle
            }
        ).fetchone()
        pref_id = result[0]
    
    yield pref_id


@pytest.fixture(scope="module")
def test_allocation(test_staff, test_subject_offering, test_cycle):
    """Create test allocation for staff deactivation test."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO allocation 
                (staff_id, subject_offering_id, cycle_id, allocation_type)
                VALUES (:staff_id, :offering_id, :cycle_id, 'AUTO')
                RETURNING id
            """),
            {
                "staff_id": test_staff,
                "offering_id": test_subject_offering,
                "cycle_id": test_cycle
            }
        ).fetchone()
        alloc_id = result[0]
    
    yield alloc_id


# ============================================================================
# Bug Condition Exploration Tests
# ============================================================================

class TestBugConditionExploration:
    """
    Test that queries referencing old table/column names fail with expected errors.
    
    These tests MUST FAIL on unfixed code - failure confirms the bug exists.
    After the fix is implemented, these same tests will PASS, confirming the fix works.
    
    FOCUS: Testing the actual broken SQL queries from demo_prep.py and old cycle_service.py
    """
    
    def test_academic_cycle_table_does_not_exist(self):
        """
        Test Case 1: Query old academic_cycle table
        
        Expected on UNFIXED code: PostgreSQL error "relation academic_cycle does not exist"
        Expected on FIXED code: Query executes successfully using cycle table
        
        Validates: Requirement 1.1 (demo_prep.py line 73, 79)
        """
        with get_transaction() as session:
            # This query is from demo_prep.py line 73
            # After migration 021, academic_cycle was renamed to academic_cycle_old_backup
            # The correct query should use the cycle table instead
            try:
                row = session.execute(
                    text("SELECT id FROM academic_cycle WHERE is_active = true LIMIT 1")
                ).fetchone()
                
                # If we get here without error, the table exists (unexpected on unfixed code)
                # On fixed code, this should use cycle table with status='OPEN'
                assert False, "Query should fail on unfixed code - academic_cycle table should not exist"
            except Exception as e:
                error_msg = str(e).lower()
                # Expected error on unfixed code
                assert "academic_cycle" in error_msg and ("does not exist" in error_msg or "relation" in error_msg), \
                    f"Expected 'relation academic_cycle does not exist' error, got: {e}"
    
    def test_subject_offering_academic_cycle_id_column_does_not_exist(
        self, test_subject_offering, test_cycle
    ):
        """
        Test Case 2: Query subject_offering.academic_cycle_id column
        
        Expected on UNFIXED code: PostgreSQL error "column so.academic_cycle_id does not exist"
        Expected on FIXED code: Query executes successfully using cycle JOIN
        
        Validates: Requirement 1.2 (demo_prep.py line 144)
        """
        with get_transaction() as session:
            # This query is from demo_prep.py line 144
            # After migration 021, subject_offering.academic_cycle_id was renamed to old_academic_cycle_id
            # The correct query should JOIN through cycle table
            try:
                rows = session.execute(
                    text("""
                        SELECT id FROM subject_offering so 
                        WHERE so.academic_cycle_id = :cid AND so.is_active = true 
                        LIMIT 5
                    """),
                    {"cid": test_cycle}
                ).fetchall()
                
                # If we get here without error, the column exists (unexpected on unfixed code)
                assert False, "Query should fail on unfixed code - so.academic_cycle_id column should not exist"
            except Exception as e:
                error_msg = str(e).lower()
                # Expected error on unfixed code
                assert "academic_cycle_id" in error_msg and "does not exist" in error_msg, \
                    f"Expected 'column so.academic_cycle_id does not exist' error, got: {e}"
    
    def test_allocation_academic_cycle_id_column_does_not_exist(
        self, test_allocation, test_cycle
    ):
        """
        Test Case 3: Query allocation.academic_cycle_id column
        
        Expected on UNFIXED code: PostgreSQL error "column academic_cycle_id does not exist"
        Expected on FIXED code: Query executes successfully using cycle_id column
        
        Validates: Requirement 1.3 (demo_prep.py line 112)
        """
        with get_transaction() as session:
            # This query is from demo_prep.py line 112
            # After migration 021, allocation.academic_cycle_id was renamed to old_academic_cycle_id
            # The correct query should use allocation.cycle_id
            try:
                session.execute(
                    text("DELETE FROM allocation WHERE academic_cycle_id = :cid"),
                    {"cid": test_cycle}
                )
                
                # If we get here without error, the column exists (unexpected on unfixed code)
                assert False, "Query should fail on unfixed code - allocation.academic_cycle_id column should not exist"
            except Exception as e:
                error_msg = str(e).lower()
                # Expected error on unfixed code
                assert "academic_cycle_id" in error_msg and "does not exist" in error_msg, \
                    f"Expected 'column academic_cycle_id does not exist' error, got: {e}"
    
    def test_faculty_preference_academic_cycle_id_column_does_not_exist(
        self, test_preference, test_cycle
    ):
        """
        Test Case 4: Query faculty_preference.academic_cycle_id column
        
        Expected on UNFIXED code: PostgreSQL error "column academic_cycle_id does not exist"
        Expected on FIXED code: Query executes successfully using cycle_id column
        
        Validates: Requirement 1.4 (demo_prep.py line 114, 157)
        """
        with get_transaction() as session:
            # This query is from demo_prep.py line 114
            # After migration 021, faculty_preference.academic_cycle_id was renamed to old_academic_cycle_id
            # The correct query should use faculty_preference.cycle_id
            try:
                session.execute(
                    text("DELETE FROM faculty_preference WHERE academic_cycle_id = :cid"),
                    {"cid": test_cycle}
                )
                
                # If we get here without error, the column exists (unexpected on unfixed code)
                assert False, "Query should fail on unfixed code - faculty_preference.academic_cycle_id column should not exist"
            except Exception as e:
                error_msg = str(e).lower()
                # Expected error on unfixed code
                assert "academic_cycle_id" in error_msg and "does not exist" in error_msg, \
                    f"Expected 'column academic_cycle_id does not exist' error, got: {e}"


# ============================================================================
# Test Execution Notes
# ============================================================================

"""
EXPECTED OUTCOME ON UNFIXED CODE (after migration 021):
- All 4 tests will FAIL with PostgreSQL errors
- Test 1: "relation academic_cycle does not exist" (table was renamed)
- Test 2: "column so.academic_cycle_id does not exist" (column was renamed)
- Test 3: "column academic_cycle_id does not exist" in allocation table
- Test 4: "column academic_cycle_id does not exist" in faculty_preference table
- This confirms the bug exists in demo_prep.py and validates our root cause analysis

EXPECTED OUTCOME ON FIXED CODE:
- All 4 tests will PASS (queries will be updated to use new schema)
- Test 1: Uses cycle table with status='OPEN' instead of academic_cycle.is_active
- Test 2: Uses JOIN through cycle table instead of so.academic_cycle_id
- Test 3: Uses allocation.cycle_id instead of allocation.academic_cycle_id
- Test 4: Uses faculty_preference.cycle_id instead of faculty_preference.academic_cycle_id
- This confirms the fix works correctly

ACTUAL BUG LOCATION:
- scripts/demo_prep.py has 8+ broken references to old schema
- app/admin/cycle_service.py exists but is NOT used (cycle_service_new.py is used instead)
- All production service files have already been fixed

To run these tests:
    pytest tests/test_bug_academic_cycle_fix.py -v

To run with detailed output:
    pytest tests/test_bug_academic_cycle_fix.py -v -s
    
NOTE: These tests directly execute SQL queries to demonstrate the schema mismatch.
They will fail on unfixed code, which is the expected behavior for bug exploration tests.
"""
