"""
Integration tests for window lifecycle.
Spec reference: window_lifecycle_design.md

These tests require a real database connection and test:
- Concurrent window open races
- Full lifecycle flow with FCFS integration
- Real transaction isolation and locking behavior
"""

import pytest
import threading
import time
from datetime import datetime, timedelta
from sqlalchemy import text
from app.db.session import get_transaction
from app.coordinator.window_transactions import (
    create_window_transaction,
    schedule_window_transaction,
    open_window_transaction,
    close_window_transaction,
    archive_window_transaction
)
from app.selection.transactions import select_subject_transaction


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def test_coordinator():
    """Create test coordinator staff member."""
    with get_transaction() as session:
        # Create coordinator
        result = session.execute(
            text("""
                INSERT INTO staff (email, name, is_coordinator)
                VALUES (:email, :name, true)
                RETURNING id
            """),
            {
                "email": "test.coordinator@hindustanuniv.ac.in",
                "name": "Test Coordinator"
            }
        ).fetchone()
        coordinator_id = result[0]
    
    yield coordinator_id
    
    # Cleanup
    with get_transaction() as session:
        session.execute(
            text("DELETE FROM staff WHERE id = :id"),
            {"id": coordinator_id}
        )


@pytest.fixture(scope="module")
def test_staff():
    """Create test staff member (non-coordinator)."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO staff (email, name, is_coordinator)
                VALUES (:email, :name, false)
                RETURNING id
            """),
            {
                "email": "test.staff@hindustanuniv.ac.in",
                "name": "Test Staff"
            }
        ).fetchone()
        staff_id = result[0]
    
    yield staff_id
    
    # Cleanup
    with get_transaction() as session:
        session.execute(
            text("DELETE FROM staff WHERE id = :id"),
            {"id": staff_id}
        )


@pytest.fixture(scope="module")
def test_batch():
    """Create test batch."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO batch (name, year)
                VALUES (:name, :year)
                RETURNING id
            """),
            {"name": "Test Batch 2024", "year": 2024}
        ).fetchone()
        batch_id = result[0]
    
    yield batch_id
    
    # Cleanup
    with get_transaction() as session:
        session.execute(
            text("DELETE FROM batch WHERE id = :id"),
            {"id": batch_id}
        )


@pytest.fixture(scope="module")
def test_specialization():
    """Create test specialization."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO specialization (name, code)
                VALUES (:name, :code)
                RETURNING id
            """),
            {"name": "Test Specialization", "code": "TEST"}
        ).fetchone()
        spec_id = result[0]
    
    yield spec_id
    
    # Cleanup
    with get_transaction() as session:
        session.execute(
            text("DELETE FROM specialization WHERE id = :id"),
            {"id": spec_id}
        )


@pytest.fixture
def test_subject(test_batch, test_specialization):
    """Create test subject."""
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO subject (code, name, credits, batch_id, specialization_id, total_slots)
                VALUES (:code, :name, :credits, :batch_id, :spec_id, :slots)
                RETURNING id
            """),
            {
                "code": "TEST101",
                "name": "Test Subject",
                "credits": 3,
                "batch_id": test_batch,
                "spec_id": test_specialization,
                "slots": 10
            }
        ).fetchone()
        subject_id = result[0]
    
    yield subject_id
    
    # Cleanup
    with get_transaction() as session:
        session.execute(
            text("DELETE FROM subject WHERE id = :id"),
            {"id": subject_id}
        )


@pytest.fixture
def staff_assignment(test_staff, test_batch, test_specialization):
    """Assign test staff to batch/specialization."""
    with get_transaction() as session:
        session.execute(
            text("""
                INSERT INTO staff_assignment (staff_id, batch_id, specialization_id)
                VALUES (:staff_id, :batch_id, :spec_id)
            """),
            {
                "staff_id": test_staff,
                "batch_id": test_batch,
                "spec_id": test_specialization
            }
        )
    
    yield
    
    # Cleanup
    with get_transaction() as session:
        session.execute(
            text("""
                DELETE FROM staff_assignment 
                WHERE staff_id = :staff_id 
                  AND batch_id = :batch_id 
                  AND specialization_id = :spec_id
            """),
            {
                "staff_id": test_staff,
                "batch_id": test_batch,
                "spec_id": test_specialization
            }
        )


# ============================================================================
# Test: Concurrent Window Open Race
# ============================================================================

class TestConcurrentWindowOpenRace:
    """Test concurrent window opening with real database transactions."""
    
    def test_concurrent_open_same_batch_spec_only_one_succeeds(
        self, test_coordinator, test_batch, test_specialization
    ):
        """
        Test that when two coordinators try to open windows for the same
        batch/spec concurrently, only one succeeds due to partial unique index.
        """
        # Create two SCHEDULED windows for same batch/spec
        future_start = datetime.utcnow() - timedelta(minutes=5)  # In past so we can open
        future_end = datetime.utcnow() + timedelta(hours=2)
        
        window1_result = create_window_transaction(
            coordinator_id=test_coordinator,
            name="Concurrent Test Window 1",
            batch_id=test_batch,
            specialization_id=test_specialization
        )
        assert window1_result["success"]
        window1_id = window1_result["window_id"]
        
        window2_result = create_window_transaction(
            coordinator_id=test_coordinator,
            name="Concurrent Test Window 2",
            batch_id=test_batch,
            specialization_id=test_specialization
        )
        assert window2_result["success"]
        window2_id = window2_result["window_id"]
        
        # Schedule both windows
        for window_id in [window1_id, window2_id]:
            result = schedule_window_transaction(
                coordinator_id=test_coordinator,
                window_id=window_id,
                start_time=future_start.isoformat() + 'Z',
                end_time=future_end.isoformat() + 'Z'
            )
            assert result["success"]
        
        # Concurrent open using threads
        results = []
        errors = []
        
        def open_window(window_id):
            try:
                result = open_window_transaction(
                    coordinator_id=test_coordinator,
                    window_id=window_id
                )
                results.append((window_id, result))
            except Exception as e:
                errors.append((window_id, str(e)))
        
        # Start both threads simultaneously
        thread1 = threading.Thread(target=open_window, args=(window1_id,))
        thread2 = threading.Thread(target=open_window, args=(window2_id,))
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Verify results: exactly one should succeed
        success_count = sum(1 for _, result in results if result["success"])
        failure_count = sum(1 for _, result in results if not result["success"])
        
        assert success_count == 1, f"Expected 1 success, got {success_count}"
        assert failure_count == 1, f"Expected 1 failure, got {failure_count}"
        
        # Verify failure message mentions "already open"
        failed_result = next(result for _, result in results if not result["success"])
        assert "already open" in failed_result["message"].lower()
        
        # Cleanup
        with get_transaction() as session:
            session.execute(
                text("DELETE FROM selection_window WHERE id IN (:w1, :w2)"),
                {"w1": window1_id, "w2": window2_id}
            )
    
    def test_concurrent_open_different_batch_both_succeed(
        self, test_coordinator, test_specialization
    ):
        """
        Test that concurrent opens for different batches both succeed.
        """
        # Create two test batches
        with get_transaction() as session:
            batch1_id = session.execute(
                text("INSERT INTO batch (name, year) VALUES (:name, :year) RETURNING id"),
                {"name": "Concurrent Batch 1", "year": 2024}
            ).scalar()
            
            batch2_id = session.execute(
                text("INSERT INTO batch (name, year) VALUES (:name, :year) RETURNING id"),
                {"name": "Concurrent Batch 2", "year": 2024}
            ).scalar()
        
        try:
            # Create and schedule windows for different batches
            future_start = datetime.utcnow() - timedelta(minutes=5)
            future_end = datetime.utcnow() + timedelta(hours=2)
            
            window_ids = []
            for batch_id in [batch1_id, batch2_id]:
                create_result = create_window_transaction(
                    coordinator_id=test_coordinator,
                    name=f"Window for Batch {batch_id}",
                    batch_id=batch_id,
                    specialization_id=test_specialization
                )
                assert create_result["success"]
                window_id = create_result["window_id"]
                window_ids.append(window_id)
                
                schedule_result = schedule_window_transaction(
                    coordinator_id=test_coordinator,
                    window_id=window_id,
                    start_time=future_start.isoformat() + 'Z',
                    end_time=future_end.isoformat() + 'Z'
                )
                assert schedule_result["success"]
            
            # Concurrent open
            results = []
            
            def open_window(window_id):
                result = open_window_transaction(
                    coordinator_id=test_coordinator,
                    window_id=window_id
                )
                results.append((window_id, result))
            
            threads = [threading.Thread(target=open_window, args=(wid,)) for wid in window_ids]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            # Both should succeed (different batches)
            success_count = sum(1 for _, result in results if result["success"])
            assert success_count == 2, f"Expected 2 successes, got {success_count}"
            
        finally:
            # Cleanup
            with get_transaction() as session:
                session.execute(
                    text("DELETE FROM selection_window WHERE batch_id IN (:b1, :b2)"),
                    {"b1": batch1_id, "b2": batch2_id}
                )
                session.execute(
                    text("DELETE FROM batch WHERE id IN (:b1, :b2)"),
                    {"b1": batch1_id, "b2": batch2_id}
                )


# ============================================================================
# Test: Full Lifecycle with FCFS Integration
# ============================================================================

class TestFullLifecycleWithFCFS:
    """Test complete window lifecycle with FCFS subject selection."""
    
    def test_full_lifecycle_draft_to_archived_with_fcfs(
        self,
        test_coordinator,
        test_staff,
        test_batch,
        test_specialization,
        test_subject,
        staff_assignment
    ):
        """
        Test complete lifecycle: DRAFT → SCHEDULED → OPEN → FCFS selection → CLOSED → ARCHIVED
        """
        # Step 1: CREATE window (DRAFT)
        create_result = create_window_transaction(
            coordinator_id=test_coordinator,
            name="Full Lifecycle Test Window",
            batch_id=test_batch,
            specialization_id=test_specialization,
            max_subjects_per_staff=3
        )
        assert create_result["success"]
        window_id = create_result["window_id"]
        
        # Verify DRAFT status
        with get_transaction() as session:
            status = session.execute(
                text("SELECT status FROM selection_window WHERE id = :id"),
                {"id": window_id}
            ).scalar()
            assert status == 'DRAFT'
        
        # Step 2: SCHEDULE window (DRAFT → SCHEDULED)
        future_start = datetime.utcnow() - timedelta(minutes=5)  # Past so we can open
        future_end = datetime.utcnow() + timedelta(hours=2)
        
        schedule_result = schedule_window_transaction(
            coordinator_id=test_coordinator,
            window_id=window_id,
            start_time=future_start.isoformat() + 'Z',
            end_time=future_end.isoformat() + 'Z'
        )
        assert schedule_result["success"]
        
        # Verify SCHEDULED status
        with get_transaction() as session:
            status = session.execute(
                text("SELECT status FROM selection_window WHERE id = :id"),
                {"id": window_id}
            ).scalar()
            assert status == 'SCHEDULED'
        
        # Step 3: OPEN window (SCHEDULED → OPEN)
        open_result = open_window_transaction(
            coordinator_id=test_coordinator,
            window_id=window_id
        )
        assert open_result["success"]
        
        # Verify OPEN status
        with get_transaction() as session:
            status = session.execute(
                text("SELECT status FROM selection_window WHERE id = :id"),
                {"id": window_id}
            ).scalar()
            assert status == 'OPEN'
        
        # Step 4: FCFS subject selection (while OPEN)
        selection_result = select_subject_transaction(
            staff_id=test_staff,
            subject_id=test_subject,
            batch_id=test_batch,
            specialization_id=test_specialization
        )
        assert selection_result["success"], f"Selection failed: {selection_result['message']}"
        selection_id = selection_result["selection_id"]
        
        # Verify selection was created
        with get_transaction() as session:
            selection_exists = session.execute(
                text("SELECT COUNT(*) FROM subject_selection WHERE id = :id"),
                {"id": selection_id}
            ).scalar()
            assert selection_exists == 1
        
        # Step 5: CLOSE window (OPEN → CLOSED)
        close_result = close_window_transaction(
            coordinator_id=test_coordinator,
            window_id=window_id
        )
        assert close_result["success"]
        
        # Verify CLOSED status
        with get_transaction() as session:
            status = session.execute(
                text("SELECT status FROM selection_window WHERE id = :id"),
                {"id": window_id}
            ).scalar()
            assert status == 'CLOSED'
        
        # Step 6: Verify FCFS blocked after CLOSED
        # Try to select another subject (should fail - window closed)
        with get_transaction() as session:
            # Create another subject
            subject2_id = session.execute(
                text("""
                    INSERT INTO subject (code, name, credits, batch_id, specialization_id, total_slots)
                    VALUES (:code, :name, :credits, :batch_id, :spec_id, :slots)
                    RETURNING id
                """),
                {
                    "code": "TEST102",
                    "name": "Test Subject 2",
                    "credits": 3,
                    "batch_id": test_batch,
                    "spec_id": test_specialization,
                    "slots": 10
                }
            ).scalar()
        
        try:
            selection2_result = select_subject_transaction(
                staff_id=test_staff,
                subject_id=subject2_id,
                batch_id=test_batch,
                specialization_id=test_specialization
            )
            assert not selection2_result["success"]
            assert "window closed" in selection2_result["message"].lower()
        finally:
            # Cleanup subject2
            with get_transaction() as session:
                session.execute(
                    text("DELETE FROM subject WHERE id = :id"),
                    {"id": subject2_id}
                )
        
        # Step 7: ARCHIVE window (CLOSED → ARCHIVED)
        archive_result = archive_window_transaction(
            coordinator_id=test_coordinator,
            window_id=window_id
        )
        assert archive_result["success"]
        
        # Verify ARCHIVED status
        with get_transaction() as session:
            status = session.execute(
                text("SELECT status FROM selection_window WHERE id = :id"),
                {"id": window_id}
            ).scalar()
            assert status == 'ARCHIVED'
        
        # Step 8: Verify audit trail
        with get_transaction() as session:
            audit_actions = session.execute(
                text("""
                    SELECT action_type
                    FROM audit_log
                    WHERE details->>'window_id' = :window_id::text
                    ORDER BY created_at ASC
                """),
                {"window_id": window_id}
            ).fetchall()
            
            action_types = [row[0] for row in audit_actions]
            expected_actions = [
                'WINDOW_CREATED',
                'WINDOW_SCHEDULED',
                'WINDOW_OPENED',
                'WINDOW_CLOSED',
                'WINDOW_ARCHIVED'
            ]
            
            for expected in expected_actions:
                assert expected in action_types, f"Missing audit action: {expected}"
        
        # Cleanup
        with get_transaction() as session:
            session.execute(
                text("DELETE FROM subject_selection WHERE id = :id"),
                {"id": selection_id}
            )
            session.execute(
                text("DELETE FROM selection_window WHERE id = :id"),
                {"id": window_id}
            )
    
    def test_fcfs_blocked_when_window_expired(
        self,
        test_coordinator,
        test_staff,
        test_batch,
        test_specialization,
        test_subject,
        staff_assignment
    ):
        """
        Test that FCFS is blocked when window is OPEN but expired (now > end_time).
        """
        # Create and schedule window with end_time in the past
        create_result = create_window_transaction(
            coordinator_id=test_coordinator,
            name="Expired Window Test",
            batch_id=test_batch,
            specialization_id=test_specialization
        )
        assert create_result["success"]
        window_id = create_result["window_id"]
        
        # Schedule with past times
        past_start = datetime.utcnow() - timedelta(hours=2)
        past_end = datetime.utcnow() - timedelta(hours=1)  # Expired
        
        schedule_result = schedule_window_transaction(
            coordinator_id=test_coordinator,
            window_id=window_id,
            start_time=past_start.isoformat() + 'Z',
            end_time=past_end.isoformat() + 'Z'
        )
        assert schedule_result["success"]
        
        # Open window (will succeed even though expired)
        open_result = open_window_transaction(
            coordinator_id=test_coordinator,
            window_id=window_id
        )
        assert open_result["success"]
        
        # Verify window is OPEN
        with get_transaction() as session:
            status = session.execute(
                text("SELECT status FROM selection_window WHERE id = :id"),
                {"id": window_id}
            ).scalar()
            assert status == 'OPEN'
        
        # Try FCFS selection (should fail - expired)
        selection_result = select_subject_transaction(
            staff_id=test_staff,
            subject_id=test_subject,
            batch_id=test_batch,
            specialization_id=test_specialization
        )
        assert not selection_result["success"]
        assert "window closed" in selection_result["message"].lower()
        
        # Cleanup
        with get_transaction() as session:
            session.execute(
                text("DELETE FROM selection_window WHERE id = :id"),
                {"id": window_id}
            )
