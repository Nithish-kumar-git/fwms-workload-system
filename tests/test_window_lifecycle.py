"""
Unit tests for window lifecycle state transitions.
Spec reference: window_lifecycle_design.md

Test Coverage:
- State transition validation (valid and invalid transitions)
- Single OPEN window constraint enforcement
- Time immutability trigger after SCHEDULED
- Concurrent window open race conditions
- SCHEDULED precondition validation
- Idempotency guarantees
"""

import pytest
from sqlalchemy import text
from app.db.session import get_transaction
from app.coordinator.window_transactions import (
    create_window_transaction,
    schedule_window_transaction,
    open_window_transaction,
    close_window_transaction,
    archive_window_transaction
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def coordinator_id():
    """Fixture for coordinator staff ID."""
    # TODO: Create test coordinator in database
    return 1


@pytest.fixture
def batch_id():
    """Fixture for test batch ID."""
    # TODO: Create test batch in database
    return 1


@pytest.fixture
def specialization_id():
    """Fixture for test specialization ID."""
    # TODO: Create test specialization in database
    return 1


@pytest.fixture
def future_start_time():
    """Fixture for future start time (ISO 8601)."""
    from datetime import datetime, timedelta
    future = datetime.utcnow() + timedelta(hours=1)
    return future.isoformat() + 'Z'


@pytest.fixture
def future_end_time():
    """Fixture for future end time (ISO 8601)."""
    from datetime import datetime, timedelta
    future = datetime.utcnow() + timedelta(hours=3)
    return future.isoformat() + 'Z'


@pytest.fixture
def draft_window(coordinator_id, batch_id, specialization_id):
    """Fixture that creates a DRAFT window and returns window_id."""
    result = create_window_transaction(
        coordinator_id=coordinator_id,
        name="Test Window",
        batch_id=batch_id,
        specialization_id=specialization_id
    )
    assert result["success"]
    window_id = result["window_id"]
    
    yield window_id
    
    # Cleanup: Delete window after test
    with get_transaction() as session:
        session.execute(
            text("DELETE FROM selection_window WHERE id = :window_id"),
            {"window_id": window_id}
        )


@pytest.fixture
def scheduled_window(draft_window, coordinator_id, future_start_time, future_end_time):
    """Fixture that creates a SCHEDULED window and returns window_id."""
    result = schedule_window_transaction(
        coordinator_id=coordinator_id,
        window_id=draft_window,
        start_time=future_start_time,
        end_time=future_end_time
    )
    assert result["success"]
    return draft_window


# ============================================================================
# Test: State Transition Validation
# ============================================================================

class TestStateTransitions:
    """Test valid and invalid state transitions."""
    
    def test_draft_to_scheduled_valid(self, draft_window, coordinator_id, future_start_time, future_end_time):
        """Test valid DRAFT → SCHEDULED transition."""
        result = schedule_window_transaction(
            coordinator_id=coordinator_id,
            window_id=draft_window,
            start_time=future_start_time,
            end_time=future_end_time
        )
        
        assert result["success"] is True
        assert result["window_id"] == draft_window
        
        # Verify status in database
        with get_transaction() as session:
            status = session.execute(
                text("SELECT status FROM selection_window WHERE id = :window_id"),
                {"window_id": draft_window}
            ).scalar()
            assert status == 'SCHEDULED'
    
    def test_scheduled_to_open_valid(self, scheduled_window, coordinator_id):
        """Test valid SCHEDULED → OPEN transition."""
        # TODO: Set start_time to past (or mock now())
        # TODO: Call open_window_transaction
        # TODO: Verify status = 'OPEN'
        pytest.skip("Requires time mocking or past start_time")
    
    def test_open_to_closed_valid(self, coordinator_id):
        """Test valid OPEN → CLOSED transition."""
        # TODO: Create OPEN window
        # TODO: Call close_window_transaction
        # TODO: Verify status = 'CLOSED'
        pytest.skip("Requires OPEN window fixture")
    
    def test_closed_to_archived_valid(self, coordinator_id):
        """Test valid CLOSED → ARCHIVED transition."""
        # TODO: Create CLOSED window
        # TODO: Call archive_window_transaction
        # TODO: Verify status = 'ARCHIVED'
        pytest.skip("Requires CLOSED window fixture")
    
    def test_draft_to_open_invalid(self, draft_window, coordinator_id):
        """Test invalid DRAFT → OPEN transition (must go through SCHEDULED)."""
        result = open_window_transaction(
            coordinator_id=coordinator_id,
            window_id=draft_window
        )
        
        assert result["success"] is False
        assert "SCHEDULED" in result["message"]
    
    def test_closed_to_open_invalid(self, coordinator_id):
        """Test invalid CLOSED → OPEN transition (no reverse transitions)."""
        # TODO: Create CLOSED window
        # TODO: Call open_window_transaction
        # TODO: Verify error message about state
        pytest.skip("Requires CLOSED window fixture")
    
    def test_open_to_scheduled_invalid(self, coordinator_id):
        """Test invalid OPEN → SCHEDULED transition (no reverse transitions)."""
        # TODO: Create OPEN window
        # TODO: Call schedule_window_transaction
        # TODO: Verify error message
        pytest.skip("Requires OPEN window fixture")


# ============================================================================
# Test: SCHEDULED Preconditions
# ============================================================================

class TestScheduledPreconditions:
    """Test SCHEDULED transition precondition validation."""
    
    def test_schedule_requires_start_time(self, draft_window, coordinator_id, future_end_time):
        """Test that scheduling requires start_time."""
        result = schedule_window_transaction(
            coordinator_id=coordinator_id,
            window_id=draft_window,
            start_time=None,
            end_time=future_end_time
        )
        
        assert result["success"] is False
        assert "start_time is required" in result["message"]
    
    def test_schedule_requires_end_time(self, draft_window, coordinator_id, future_start_time):
        """Test that scheduling requires end_time."""
        result = schedule_window_transaction(
            coordinator_id=coordinator_id,
            window_id=draft_window,
            start_time=future_start_time,
            end_time=None
        )
        
        assert result["success"] is False
        assert "end_time is required" in result["message"]
    
    def test_schedule_requires_end_after_start(self, draft_window, coordinator_id):
        """Test that end_time must be after start_time."""
        from datetime import datetime, timedelta
        
        start = datetime.utcnow() + timedelta(hours=2)
        end = datetime.utcnow() + timedelta(hours=1)  # Before start
        
        result = schedule_window_transaction(
            coordinator_id=coordinator_id,
            window_id=draft_window,
            start_time=start.isoformat() + 'Z',
            end_time=end.isoformat() + 'Z'
        )
        
        assert result["success"] is False
        assert "end_time must be after start_time" in result["message"]
    
    def test_schedule_requires_future_start_time(self, draft_window, coordinator_id):
        """Test that start_time must be in the future."""
        from datetime import datetime, timedelta
        
        past_start = datetime.utcnow() - timedelta(hours=1)
        future_end = datetime.utcnow() + timedelta(hours=1)
        
        result = schedule_window_transaction(
            coordinator_id=coordinator_id,
            window_id=draft_window,
            start_time=past_start.isoformat() + 'Z',
            end_time=future_end.isoformat() + 'Z'
        )
        
        assert result["success"] is False
        assert "start_time must be in the future" in result["message"]


# ============================================================================
# Test: Time Immutability Trigger
# ============================================================================

class TestTimeImmutability:
    """Test that start_time and end_time are immutable after SCHEDULED."""
    
    def test_can_update_time_in_draft(self, draft_window):
        """Test that start_time/end_time can be updated in DRAFT state."""
        from datetime import datetime, timedelta
        
        new_start = datetime.utcnow() + timedelta(hours=5)
        
        with get_transaction() as session:
            # Should succeed (status = DRAFT)
            session.execute(
                text("""
                    UPDATE selection_window
                    SET start_time = :new_start
                    WHERE id = :window_id
                """),
                {"new_start": new_start, "window_id": draft_window}
            )
        
        # Verify update succeeded
        with get_transaction() as session:
            updated_start = session.execute(
                text("SELECT start_time FROM selection_window WHERE id = :window_id"),
                {"window_id": draft_window}
            ).scalar()
            # TODO: Assert updated_start matches new_start
    
    def test_cannot_update_start_time_after_scheduled(self, scheduled_window):
        """Test that start_time cannot be updated after SCHEDULED."""
        from datetime import datetime, timedelta
        
        new_start = datetime.utcnow() + timedelta(hours=10)
        
        with pytest.raises(Exception) as exc_info:
            with get_transaction() as session:
                session.execute(
                    text("""
                        UPDATE selection_window
                        SET start_time = :new_start
                        WHERE id = :window_id
                    """),
                    {"new_start": new_start, "window_id": scheduled_window}
                )
        
        assert "immutable after SCHEDULED" in str(exc_info.value)
    
    def test_cannot_update_end_time_after_scheduled(self, scheduled_window):
        """Test that end_time cannot be updated after SCHEDULED."""
        from datetime import datetime, timedelta
        
        new_end = datetime.utcnow() + timedelta(hours=20)
        
        with pytest.raises(Exception) as exc_info:
            with get_transaction() as session:
                session.execute(
                    text("""
                        UPDATE selection_window
                        SET end_time = :new_end
                        WHERE id = :window_id
                    """),
                    {"new_end": new_end, "window_id": scheduled_window}
                )
        
        assert "immutable after SCHEDULED" in str(exc_info.value)
    
    def test_can_update_other_fields_after_scheduled(self, scheduled_window):
        """Test that other fields (e.g., name) can be updated after SCHEDULED."""
        with get_transaction() as session:
            # Should succeed (only start_time/end_time are immutable)
            session.execute(
                text("""
                    UPDATE selection_window
                    SET name = 'Updated Name'
                    WHERE id = :window_id
                """),
                {"window_id": scheduled_window}
            )
        
        # Verify update succeeded
        with get_transaction() as session:
            updated_name = session.execute(
                text("SELECT name FROM selection_window WHERE id = :window_id"),
                {"window_id": scheduled_window}
            ).scalar()
            assert updated_name == 'Updated Name'


# ============================================================================
# Test: Single OPEN Window Constraint
# ============================================================================

class TestSingleOpenWindow:
    """Test that only one OPEN window is allowed per (batch_id, specialization_id)."""
    
    def test_cannot_open_two_windows_same_batch_spec(self, coordinator_id, batch_id, specialization_id):
        """Test that opening two windows for same batch/spec fails."""
        # TODO: Create two SCHEDULED windows for same batch/spec
        # TODO: Open first window (should succeed)
        # TODO: Try to open second window (should fail with unique violation)
        # TODO: Verify error message mentions "already open"
        pytest.skip("Requires two SCHEDULED window fixtures")
    
    def test_can_open_windows_different_batch(self, coordinator_id, specialization_id):
        """Test that windows for different batches can both be OPEN."""
        # TODO: Create two SCHEDULED windows with different batch_id
        # TODO: Open both windows (should both succeed)
        pytest.skip("Requires multiple batch fixtures")
    
    def test_can_open_windows_different_spec(self, coordinator_id, batch_id):
        """Test that windows for different specializations can both be OPEN."""
        # TODO: Create two SCHEDULED windows with different specialization_id
        # TODO: Open both windows (should both succeed)
        pytest.skip("Requires multiple specialization fixtures")
    
    def test_can_open_after_closing_previous(self, coordinator_id, batch_id, specialization_id):
        """Test that a new window can be opened after closing previous one."""
        # TODO: Create and open first window
        # TODO: Close first window
        # TODO: Create and open second window for same batch/spec (should succeed)
        pytest.skip("Requires OPEN and CLOSED window fixtures")


# ============================================================================
# Test: Concurrent Window Open Race
# ============================================================================

class TestConcurrentWindowOpen:
    """Test concurrent window opening race conditions."""
    
    def test_concurrent_open_same_batch_spec(self, coordinator_id, batch_id, specialization_id):
        """Test that concurrent opens for same batch/spec result in only one success."""
        import threading
        
        # TODO: Create two SCHEDULED windows for same batch/spec
        # TODO: Open both windows concurrently using threads
        # TODO: Verify exactly one succeeds, one fails with unique violation
        pytest.skip("Requires threading and two SCHEDULED window fixtures")
    
    def test_concurrent_open_different_batch_spec(self, coordinator_id):
        """Test that concurrent opens for different batch/spec both succeed."""
        import threading
        
        # TODO: Create two SCHEDULED windows with different batch/spec
        # TODO: Open both windows concurrently using threads
        # TODO: Verify both succeed
        pytest.skip("Requires threading and multiple batch/spec fixtures")


# ============================================================================
# Test: Idempotency
# ============================================================================

class TestIdempotency:
    """Test idempotent behavior of state transitions."""
    
    def test_schedule_already_scheduled_window(self, scheduled_window, coordinator_id, future_start_time, future_end_time):
        """Test that scheduling an already-scheduled window fails cleanly."""
        result = schedule_window_transaction(
            coordinator_id=coordinator_id,
            window_id=scheduled_window,
            start_time=future_start_time,
            end_time=future_end_time
        )
        
        assert result["success"] is False
        assert "DRAFT" in result["message"]
    
    def test_open_already_open_window(self, coordinator_id):
        """Test that opening an already-open window fails cleanly."""
        # TODO: Create OPEN window
        # TODO: Try to open again
        # TODO: Verify error message
        pytest.skip("Requires OPEN window fixture")
    
    def test_close_already_closed_window(self, coordinator_id):
        """Test that closing an already-closed window fails cleanly."""
        # TODO: Create CLOSED window
        # TODO: Try to close again
        # TODO: Verify error message
        pytest.skip("Requires CLOSED window fixture")


# ============================================================================
# Test: Audit Logging
# ============================================================================

class TestAuditLogging:
    """Test that all state transitions are audited."""
    
    def test_create_window_creates_audit_log(self, coordinator_id, batch_id, specialization_id):
        """Test that creating a window creates an audit log entry."""
        result = create_window_transaction(
            coordinator_id=coordinator_id,
            name="Audit Test Window",
            batch_id=batch_id,
            specialization_id=specialization_id
        )
        
        assert result["success"]
        window_id = result["window_id"]
        
        # Verify audit log entry
        with get_transaction() as session:
            audit_entry = session.execute(
                text("""
                    SELECT action_type, actor_staff_id, details
                    FROM audit_log
                    WHERE details->>'window_id' = :window_id::text
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"window_id": window_id}
            ).fetchone()
            
            assert audit_entry is not None
            assert audit_entry[0] == 'WINDOW_CREATED'
            assert audit_entry[1] == coordinator_id
        
        # Cleanup
        with get_transaction() as session:
            session.execute(
                text("DELETE FROM selection_window WHERE id = :window_id"),
                {"window_id": window_id}
            )
    
    def test_schedule_window_creates_audit_log(self, draft_window, coordinator_id, future_start_time, future_end_time):
        """Test that scheduling a window creates an audit log entry."""
        result = schedule_window_transaction(
            coordinator_id=coordinator_id,
            window_id=draft_window,
            start_time=future_start_time,
            end_time=future_end_time
        )
        
        assert result["success"]
        
        # Verify audit log entry
        with get_transaction() as session:
            audit_entry = session.execute(
                text("""
                    SELECT action_type, actor_staff_id
                    FROM audit_log
                    WHERE details->>'window_id' = :window_id::text
                      AND action_type = 'WINDOW_SCHEDULED'
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"window_id": draft_window}
            ).fetchone()
            
            assert audit_entry is not None
            assert audit_entry[0] == 'WINDOW_SCHEDULED'
            assert audit_entry[1] == coordinator_id
