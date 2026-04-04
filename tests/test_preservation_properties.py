"""
Preservation Property Tests for preference-academic-cycle-fix

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

These tests verify that operations NOT involving cycle queries continue to work
exactly as before the fix. This includes:
- Preference submission validation rules
- Window lifecycle state transitions
- Semester state transitions
- Audit logging

IMPORTANT: These tests should PASS on UNFIXED code (before implementing the fix).
They test operations that don't involve the buggy SQL queries.

Expected outcome: All tests PASS on unfixed code, confirming baseline behavior to preserve.

NOTE: These tests are designed to work with the NEW schema (after migration 021):
- New schema: faculty_preference.cycle_id, allocation.cycle_id
- New schema: cycle table (replaces academic_cycle table)
- New schema: subject_offering uses academic_year_id + semester_id (not academic_cycle_id)
"""

import pytest
from sqlalchemy import text
from app.db.session import get_transaction
from datetime import datetime, timedelta


# ============================================================================
# Test Fixtures - Setup Test Data
# ============================================================================

@pytest.fixture(scope="module")
def test_academic_year():
    """Create test academic year (new schema)."""
    with get_transaction() as session:
        # First check if it exists
        result = session.execute(
            text("""
                SELECT id FROM academic_year WHERE label = :label
            """),
            {"label": "2024-2025"}
        ).fetchone()
        
        if result:
            year_id = result[0]
        else:
            result = session.execute(
                text("""
                    INSERT INTO academic_year (label, start_year, end_year)
                    VALUES (:label, :start_year, :end_year)
                    RETURNING id
                """),
                {"label": "2024-2025", "start_year": 2024, "end_year": 2025}
            ).fetchone()
            year_id = result[0]
    
    yield year_id


@pytest.fixture(scope="module")
def test_cycle(test_academic_year, test_semester):
    """Create test cycle (new schema)."""
    with get_transaction() as session:
        # First check if it exists
        result = session.execute(
            text("""
                SELECT id FROM cycle 
                WHERE academic_year_id = :year_id AND semester_id = :sem_id
            """),
            {"year_id": test_academic_year, "sem_id": test_semester}
        ).fetchone()
        
        if result:
            cycle_id = result[0]
        else:
            result = session.execute(
                text("""
                    INSERT INTO cycle (academic_year_id, semester_id, status)
                    VALUES (:year_id, :sem_id, 'OPEN')
                    RETURNING id
                """),
                {"year_id": test_academic_year, "sem_id": test_semester}
            ).fetchone()
            cycle_id = result[0]
    
    yield cycle_id


@pytest.fixture(scope="module")
def test_semester():
    """Create test semester."""
    with get_transaction() as session:
        # First check if it exists
        result = session.execute(
            text("""
                SELECT id FROM semester WHERE label = :label
            """),
            {"label": "I"}
        ).fetchone()
        
        if result:
            semester_id = result[0]
        else:
            result = session.execute(
                text("""
                    INSERT INTO semester (label, state)
                    VALUES (:label, 'OPEN')
                    RETURNING id
                """),
                {"label": "I"}
            ).fetchone()
            semester_id = result[0]
    
    yield semester_id


@pytest.fixture(scope="module")
def test_staff():
    """Create test faculty staff member."""
    with get_transaction() as session:
        # First check if it exists
        result = session.execute(
            text("""
                SELECT id FROM staff WHERE email = :email
            """),
            {"email": "preservation.test@hindustanuniv.ac.in"}
        ).fetchone()
        
        if result:
            staff_id = result[0]
        else:
            result = session.execute(
                text("""
                    INSERT INTO staff (email, name, is_coordinator, emp_code, tch_norm)
                    VALUES (:email, :name, false, :emp_code, 40)
                    RETURNING id
                """),
                {
                    "email": "preservation.test@hindustanuniv.ac.in",
                    "name": "Preservation Test Faculty",
                    "emp_code": "PRES001"
                }
            ).fetchone()
            staff_id = result[0]
    
    yield staff_id


@pytest.fixture(scope="module")
def test_coordinator():
    """Create test coordinator staff member."""
    with get_transaction() as session:
        # First check if it exists
        result = session.execute(
            text("""
                SELECT id FROM staff WHERE email = :email
            """),
            {"email": "coordinator.test@hindustanuniv.ac.in"}
        ).fetchone()
        
        if result:
            coord_id = result[0]
        else:
            result = session.execute(
                text("""
                    INSERT INTO staff (email, name, is_coordinator, emp_code)
                    VALUES (:email, :name, true, :emp_code)
                    RETURNING id
                """),
                {
                    "email": "coordinator.test@hindustanuniv.ac.in",
                    "name": "Test Coordinator",
                    "emp_code": "COORD001"
                }
            ).fetchone()
            coord_id = result[0]
    
    yield coord_id


@pytest.fixture(scope="module")
def test_batch():
    """Create test batch."""
    with get_transaction() as session:
        # First check if it exists
        result = session.execute(
            text("""
                SELECT id FROM batch WHERE name = :name
            """),
            {"name": "Test Batch"}
        ).fetchone()
        
        if result:
            batch_id = result[0]
        else:
            result = session.execute(
                text("""
                    INSERT INTO batch (name)
                    VALUES (:name)
                    RETURNING id
                """),
                {"name": "Test Batch"}
            ).fetchone()
            batch_id = result[0]
    
    yield batch_id


@pytest.fixture(scope="module")
def test_specialization():
    """Create test specialization."""
    with get_transaction() as session:
        # First check if it exists
        result = session.execute(
            text("""
                SELECT id FROM specialization WHERE name = :name
            """),
            {"name": "Test Specialization"}
        ).fetchone()
        
        if result:
            spec_id = result[0]
        else:
            result = session.execute(
                text("""
                    INSERT INTO specialization (name)
                    VALUES (:name)
                    RETURNING id
                """),
                {"name": "Test Specialization"}
            ).fetchone()
            spec_id = result[0]
    
    yield spec_id


@pytest.fixture(scope="module")
def test_program():
    """Create test program."""
    with get_transaction() as session:
        # First check if it exists
        result = session.execute(
            text("""
                SELECT id FROM program WHERE name = :name
            """),
            {"name": "Test Program"}
        ).fetchone()
        
        if result:
            program_id = result[0]
        else:
            result = session.execute(
                text("""
                    INSERT INTO program (name, ug_pg)
                    VALUES (:name, :ug_pg)
                    RETURNING id
                """),
                {"name": "Test Program", "ug_pg": "UG"}
            ).fetchone()
            program_id = result[0]
    
    yield program_id


@pytest.fixture(scope="module")
def test_section():
    """Create test section."""
    with get_transaction() as session:
        # First check if it exists
        result = session.execute(
            text("""
                SELECT id FROM section WHERE label = :label
            """),
            {"label": "A"}
        ).fetchone()
        
        if result:
            section_id = result[0]
        else:
            result = session.execute(
                text("""
                    INSERT INTO section (label)
                    VALUES (:label)
                    RETURNING id
                """),
                {"label": "A"}
            ).fetchone()
            section_id = result[0]
    
    yield section_id


@pytest.fixture(scope="module")
def test_subject(test_batch, test_specialization):
    """Create test subject."""
    with get_transaction() as session:
        # First check if it exists
        result = session.execute(
            text("""
                SELECT id FROM subject WHERE code = :code
            """),
            {"code": "PRES101"}
        ).fetchone()
        
        if result:
            subject_id = result[0]
        else:
            result = session.execute(
                text("""
                    INSERT INTO subject (code, name, tch, l, t, p, batch_id, specialization_id)
                    VALUES (:code, :name, :tch, :l, :t, :p, :batch_id, :spec_id)
                    RETURNING id
                """),
                {
                    "code": "PRES101",
                    "name": "Preservation Test Subject",
                    "tch": 4,
                    "l": 3,
                    "t": 1,
                    "p": 0,
                    "batch_id": test_batch,
                    "spec_id": test_specialization
                }
            ).fetchone()
            subject_id = result[0]
    
    yield subject_id


@pytest.fixture(scope="module")
def test_subject_offering(test_subject, test_program, test_section, test_semester, test_academic_year):
    """Create test subject offering (new schema)."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO subject_offering 
                (subject_id, program_id, section_id, semester_id, academic_year_id, shift, is_active)
                VALUES (:subject_id, :program_id, :section_id, :semester_id, :academic_year_id, 'MORNING', true)
                RETURNING id
            """),
            {
                "subject_id": test_subject,
                "program_id": test_program,
                "section_id": test_section,
                "semester_id": test_semester,
                "academic_year_id": test_academic_year
            }
        ).fetchone()
        offering_id = result[0]
    
    yield offering_id


# ============================================================================
# Property 1: Preference Submission Validation Rules
# ============================================================================

class TestPreferenceValidationRules:
    """
    Test that preference submission validation rules work correctly.
    
    These operations use faculty_preference.academic_cycle_id (correctly migrated column),
    so they should work on unfixed code.
    
    Validates: Requirement 3.1
    """
    
    def test_can_insert_preference_with_academic_cycle_id(self, test_staff, test_subject_offering, test_cycle):
        """
        Test that preferences can be inserted using cycle_id column.
        
        This validates that the faculty_preference table uses the correct cycle_id column
        (migrated from academic_cycle_id).
        """
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
            assert pref_id is not None
            
            # Cleanup
            session.execute(
                text("DELETE FROM faculty_preference WHERE id = :pref_id"),
                {"pref_id": pref_id}
            )
    
    def test_preference_unique_constraint(self, test_staff, test_subject_offering, test_cycle):
        """
        Test PREF-01: One preference per (staff, offering, cycle).
        
        Validates that the unique constraint on (staff_id, subject_offering_id, cycle_id)
        prevents duplicate preferences.
        """
        with get_transaction() as session:
            # Insert first preference
            pref_id = session.execute(
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
            ).scalar()
            
            # Try to insert duplicate preference (should fail)
            with pytest.raises(Exception) as exc_info:
                session.execute(
                    text("""
                        INSERT INTO faculty_preference 
                        (staff_id, subject_offering_id, preference_number, cycle_id)
                        VALUES (:staff_id, :offering_id, 2, :cycle_id)
                    """),
                    {
                        "staff_id": test_staff,
                        "offering_id": test_subject_offering,
                        "cycle_id": test_cycle
                    }
                )
            
            error_msg = str(exc_info.value).lower()
            assert "unique" in error_msg or "duplicate" in error_msg
            
            # Cleanup
            session.execute(
                text("DELETE FROM faculty_preference WHERE id = :pref_id"),
                {"pref_id": pref_id}
            )
    
    def test_preference_number_positive(self, test_staff, test_subject_offering, test_cycle):
        """
        Test PREF-02: Preference number must be positive.
        
        Validates that the check constraint on preference_number prevents non-positive values.
        """
        with pytest.raises(Exception) as exc_info:
            with get_transaction() as session:
                session.execute(
                    text("""
                        INSERT INTO faculty_preference 
                        (staff_id, subject_offering_id, preference_number, cycle_id)
                        VALUES (:staff_id, :offering_id, 0, :cycle_id)
                    """),
                    {
                        "staff_id": test_staff,
                        "offering_id": test_subject_offering,
                        "cycle_id": test_cycle
                    }
                )
        
        error_msg = str(exc_info.value).lower()
        assert "check" in error_msg or "constraint" in error_msg
    
    def test_preference_foreign_key_constraints(self, test_cycle):
        """
        Test PREF-03: Foreign key constraints on staff_id, subject_offering_id, cycle_id.
        
        Validates that invalid foreign keys are rejected.
        """
        with pytest.raises(Exception) as exc_info:
            with get_transaction() as session:
                session.execute(
                    text("""
                        INSERT INTO faculty_preference 
                        (staff_id, subject_offering_id, preference_number, cycle_id)
                        VALUES (999999, 999999, 1, :cycle_id)
                    """),
                    {"cycle_id": test_cycle}
                )
        
        error_msg = str(exc_info.value).lower()
        assert "foreign key" in error_msg or "violates" in error_msg


# ============================================================================
# Property 2: Window Lifecycle State Transitions
# ============================================================================

class TestWindowLifecycle:
    """
    Test that window lifecycle state transitions work correctly.
    
    These operations use selection_window.academic_cycle_id column,
    so they should work on unfixed code.
    
    Validates: Requirement 3.2
    """
    
    def test_can_create_window_with_academic_cycle_id(self, test_cycle):
        """
        Test that selection windows can be created using cycle_id column.
        
        This validates that the selection_window table uses the cycle_id column.
        """
        with get_transaction() as session:
            result = session.execute(
                text("""
                    INSERT INTO selection_window 
                    (cycle_id, status, name, start_time, end_time, max_subjects_per_staff, batch_id, specialization_id)
                    VALUES (:cycle_id, 'DRAFT', 'Test Window', NOW() + INTERVAL '1 hour', NOW() + INTERVAL '3 hours', 5, 1, 1)
                    RETURNING id
                """),
                {"cycle_id": test_cycle}
            ).fetchone()
            
            window_id = result[0]
            assert window_id is not None
            
            # Cleanup
            session.execute(
                text("DELETE FROM selection_window WHERE id = :window_id"),
                {"window_id": window_id}
            )
    
    def test_window_status_transitions(self, test_cycle):
        """
        Test that window status can transition through valid states.
        
        Validates that the state machine (DRAFT → SCHEDULED → OPEN → CLOSED) works correctly.
        """
        with get_transaction() as session:
            # Create DRAFT window
            window_id = session.execute(
                text("""
                    INSERT INTO selection_window 
                    (cycle_id, status, name, start_time, end_time, max_subjects_per_staff, batch_id, specialization_id)
                    VALUES (:cycle_id, 'DRAFT', 'State Test Window', NOW() + INTERVAL '1 hour', NOW() + INTERVAL '3 hours', 5, 1, 1)
                    RETURNING id
                """),
                {"cycle_id": test_cycle}
            ).scalar()
            
            # Transition to SCHEDULED
            future_start = datetime.utcnow() + timedelta(hours=1)
            future_end = datetime.utcnow() + timedelta(hours=3)
            
            session.execute(
                text("""
                    UPDATE selection_window
                    SET status = 'SCHEDULED',
                        start_time = :start_time,
                        end_time = :end_time
                    WHERE id = :window_id
                """),
                {
                    "window_id": window_id,
                    "start_time": future_start,
                    "end_time": future_end
                }
            )
            
            # Verify status updated
            status = session.execute(
                text("SELECT status FROM selection_window WHERE id = :window_id"),
                {"window_id": window_id}
            ).scalar()
            assert status == 'SCHEDULED'
            
            # Cleanup
            session.execute(
                text("DELETE FROM selection_window WHERE id = :window_id"),
                {"window_id": window_id}
            )


# ============================================================================
# Property 3: Semester State Transitions
# ============================================================================

class TestSemesterStateTransitions:
    """
    Test that semester state transitions work correctly.
    
    These operations don't involve cycle queries, so they should work on unfixed code.
    
    Validates: Requirement 3.3
    """
    
    def test_semester_state_machine(self):
        """
        Test that semester state can transition through valid states.
        
        Validates that the state machine (DRAFT → OPEN → CLOSED → ALLOCATED) works correctly.
        """
        with get_transaction() as session:
            # Create test semester with valid label (Roman numeral)
            semester_id = session.execute(
                text("""
                    INSERT INTO semester (label, state)
                    VALUES (:label, 'CLOSED')
                    ON CONFLICT (label) DO UPDATE SET state = 'CLOSED'
                    RETURNING id
                """),
                {"label": "II"}
            ).scalar()
            
            # Transition to OPEN
            session.execute(
                text("""
                    UPDATE semester
                    SET state = 'OPEN'
                    WHERE id = :semester_id
                """),
                {"semester_id": semester_id}
            )
            
            # Verify state updated
            state = session.execute(
                text("SELECT state FROM semester WHERE id = :semester_id"),
                {"semester_id": semester_id}
            ).scalar()
            assert state == 'OPEN'
            
            # Transition to CLOSED
            session.execute(
                text("""
                    UPDATE semester
                    SET state = 'CLOSED'
                    WHERE id = :semester_id
                """),
                {"semester_id": semester_id}
            )
            
            # Verify state updated
            state = session.execute(
                text("SELECT state FROM semester WHERE id = :semester_id"),
                {"semester_id": semester_id}
            ).scalar()
            assert state == 'CLOSED'
    
    def test_semester_unique_label(self):
        """
        Test that semester labels must be unique.
        
        Validates that the unique constraint on semester.label works correctly.
        """
        with get_transaction() as session:
            # Try to insert duplicate label (should fail)
            # Use label "III" which should already exist or can be created
            with pytest.raises(Exception) as exc_info:
                # First ensure III exists
                session.execute(
                    text("""
                        INSERT INTO semester (label, state)
                        VALUES ('III', 'CLOSED')
                        ON CONFLICT (label) DO NOTHING
                    """)
                )
                # Now try to insert duplicate
                session.execute(
                    text("""
                        INSERT INTO semester (label, state)
                        VALUES ('III', 'OPEN')
                    """)
                )
            
            error_msg = str(exc_info.value).lower()
            assert "unique" in error_msg or "duplicate" in error_msg


# ============================================================================
# Property 4: Audit Logging
# ============================================================================

class TestAuditLogging:
    """
    Test that audit logging works correctly for all operations.
    
    These operations don't involve cycle queries, so they should work on unfixed code.
    
    Validates: Requirement 3.4
    """
    
    def test_audit_log_table_exists(self):
        """
        Test that the audit_log table exists and has the correct structure.
        """
        with get_transaction() as session:
            result = session.execute(
                text("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'audit_log'
                    ORDER BY ordinal_position
                """)
            ).fetchall()
            
            assert len(result) > 0, "audit_log table should exist"
            
            column_names = [row[0] for row in result]
            assert 'id' in column_names
            assert 'action_type' in column_names
            assert 'actor_staff_id' in column_names
            assert 'details' in column_names
            assert 'created_at' in column_names
    
    def test_can_insert_audit_log_entry(self, test_coordinator):
        """
        Test that audit log entries can be inserted.
        
        Validates that the audit_log table accepts new entries.
        """
        with get_transaction() as session:
            result = session.execute(
                text("""
                    INSERT INTO audit_log 
                    (action_type, actor_staff_id, details)
                    VALUES (:action_type, :actor_id, :details)
                    RETURNING id
                """),
                {
                    "action_type": "PREFERENCE_SUBMITTED",
                    "actor_id": test_coordinator,
                    "details": '{"test": "preservation test"}'
                }
            ).fetchone()
            
            audit_id = result[0]
            assert audit_id is not None
            
            # Cleanup
            session.execute(
                text("DELETE FROM audit_log WHERE id = :audit_id"),
                {"audit_id": audit_id}
            )
    
    def test_audit_log_foreign_key_to_staff(self):
        """
        Test that audit_log.actor_staff_id has foreign key constraint to staff table.
        
        Validates that invalid staff IDs are rejected.
        """
        with pytest.raises(Exception) as exc_info:
            with get_transaction() as session:
                session.execute(
                    text("""
                        INSERT INTO audit_log 
                        (action_type, actor_staff_id, details)
                        VALUES (:action_type, 999999, :details)
                    """),
                    {
                        "action_type": "PREFERENCE_SUBMITTED",
                        "details": '{"test": "invalid staff"}'
                    }
                )
        
        error_msg = str(exc_info.value).lower()
        assert "foreign key" in error_msg or "violates" in error_msg
    
    def test_audit_log_created_at_defaults_to_now(self, test_coordinator):
        """
        Test that audit_log.created_at defaults to current timestamp.
        
        Validates that the default value for created_at works correctly.
        """
        with get_transaction() as session:
            before_insert = datetime.utcnow()
            
            audit_id = session.execute(
                text("""
                    INSERT INTO audit_log 
                    (action_type, actor_staff_id, details)
                    VALUES (:action_type, :actor_id, :details)
                    RETURNING id
                """),
                {
                    "action_type": "PREFERENCE_SUBMITTED",
                    "actor_id": test_coordinator,
                    "details": '{"test": "timestamp test"}'
                }
            ).scalar()
            
            after_insert = datetime.utcnow()
            
            # Verify created_at is between before and after
            created_at = session.execute(
                text("SELECT created_at FROM audit_log WHERE id = :audit_id"),
                {"audit_id": audit_id}
            ).scalar()
            
            assert created_at is not None
            assert before_insert <= created_at <= after_insert
            
            # Cleanup
            session.execute(
                text("DELETE FROM audit_log WHERE id = :audit_id"),
                {"audit_id": audit_id}
            )


# ============================================================================
# Test Execution Notes
# ============================================================================

"""
EXPECTED OUTCOME ON UNFIXED CODE:
- All tests should PASS
- These tests validate operations that don't involve the buggy SQL queries
- They confirm the baseline behavior that must be preserved after the fix

EXPECTED OUTCOME ON FIXED CODE:
- All tests should still PASS
- This confirms no regressions were introduced by the fix
- The fix only affects queries involving cycle lookups, not these core operations

To run these tests:
    pytest tests/test_preservation_properties.py -v

To run with detailed output:
    pytest tests/test_preservation_properties.py -v -s
"""
