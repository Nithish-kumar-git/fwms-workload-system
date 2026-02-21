"""
Integration tests for window router endpoints.
Tests coordinator and staff endpoints with real HTTP requests.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy import text
from app.main import app
from app.db.session import get_transaction


client = TestClient(app)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def test_coordinator_session():
    """Create test coordinator and return session cookie."""
    # TODO: Implement OAuth flow or mock session
    # For now, return mock session
    return {"session_id": "test_coordinator_session"}


@pytest.fixture(scope="module")
def test_staff_session():
    """Create test staff and return session cookie."""
    # TODO: Implement OAuth flow or mock session
    return {"session_id": "test_staff_session"}


@pytest.fixture(scope="module")
def test_batch():
    """Create test batch."""
    with get_transaction() as session:
        result = session.execute(
            text("INSERT INTO batch (name, year) VALUES (:name, :year) RETURNING id"),
            {"name": "Router Test Batch", "year": 2024}
        ).fetchone()
        batch_id = result[0]
    
    yield batch_id
    
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
            text("INSERT INTO specialization (name, code) VALUES (:name, :code) RETURNING id"),
            {"name": "Router Test Spec", "code": "RTS"}
        ).fetchone()
        spec_id = result[0]
    
    yield spec_id
    
    with get_transaction() as session:
        session.execute(
            text("DELETE FROM specialization WHERE id = :id"),
            {"id": spec_id}
        )


# ============================================================================
# Test: Coordinator Endpoints
# ============================================================================

class TestCoordinatorEndpoints:
    """Test coordinator window management endpoints."""
    
    @pytest.mark.skip(reason="Requires OAuth session implementation")
    def test_create_window(self, test_coordinator_session, test_batch, test_specialization):
        """Test POST /windows to create window."""
        response = client.post(
            "/windows",
            json={
                "name": "Test Window",
                "batch_id": test_batch,
                "specialization_id": test_specialization,
                "max_subjects_per_staff": 3
            },
            cookies=test_coordinator_session
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["window_id"] is not None
    
    @pytest.mark.skip(reason="Requires OAuth session implementation")
    def test_schedule_window(self, test_coordinator_session):
        """Test POST /windows/{id}/schedule."""
        # Create window first
        create_response = client.post(
            "/windows",
            json={
                "name": "Schedule Test Window",
                "batch_id": 1,
                "specialization_id": 1,
                "max_subjects_per_staff": 3
            },
            cookies=test_coordinator_session
        )
        window_id = create_response.json()["window_id"]
        
        # Schedule window
        future_start = (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z'
        future_end = (datetime.utcnow() + timedelta(hours=3)).isoformat() + 'Z'
        
        response = client.post(
            f"/windows/{window_id}/schedule",
            json={
                "start_time": future_start,
                "end_time": future_end
            },
            cookies=test_coordinator_session
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.skip(reason="Requires OAuth session implementation")
    def test_open_window(self, test_coordinator_session):
        """Test POST /windows/{id}/open."""
        # Create and schedule window with past start_time
        # ... (implementation similar to above)
        pass
    
    @pytest.mark.skip(reason="Requires OAuth session implementation")
    def test_close_window(self, test_coordinator_session):
        """Test POST /windows/{id}/close."""
        pass
    
    @pytest.mark.skip(reason="Requires OAuth session implementation")
    def test_archive_window(self, test_coordinator_session):
        """Test POST /windows/{id}/archive."""
        pass
    
    @pytest.mark.skip(reason="Requires OAuth session implementation")
    def test_get_window(self, test_coordinator_session):
        """Test GET /windows/{id}."""
        pass
    
    @pytest.mark.skip(reason="Requires OAuth session implementation")
    def test_cannot_open_duplicate_window(self, test_coordinator_session, test_batch, test_specialization):
        """Test that opening two windows for same batch/spec returns 409."""
        # Create and open first window
        # Try to open second window
        # Assert 409 Conflict
        pass


# ============================================================================
# Test: Staff Endpoints
# ============================================================================

class TestStaffEndpoints:
    """Test staff read-only endpoints."""
    
    @pytest.mark.skip(reason="Requires OAuth session implementation")
    def test_get_current_window_when_open(self, test_staff_session):
        """Test GET /windows/current when OPEN window exists."""
        response = client.get(
            "/windows/current",
            cookies=test_staff_session
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["is_active"]:
            assert data["window_id"] is not None
            assert data["status"] == "OPEN"
            assert data["time_remaining_seconds"] is not None
        else:
            assert data["window_id"] is None
    
    @pytest.mark.skip(reason="Requires OAuth session implementation")
    def test_get_current_window_when_closed(self, test_staff_session):
        """Test GET /windows/current when no OPEN window exists."""
        response = client.get(
            "/windows/current",
            cookies=test_staff_session
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["window_id"] is None
    
    @pytest.mark.skip(reason="Requires OAuth session implementation")
    def test_get_current_window_no_assignment(self, test_staff_session):
        """Test GET /windows/current when staff has no batch/spec assignment."""
        # Create staff with no assignment
        # Call endpoint
        # Assert is_active=False
        pass


# ============================================================================
# Test: Authorization
# ============================================================================

class TestAuthorization:
    """Test endpoint authorization."""
    
    def test_create_window_requires_coordinator(self):
        """Test that non-coordinators cannot create windows."""
        response = client.post(
            "/windows",
            json={
                "name": "Unauthorized Test",
                "batch_id": 1,
                "specialization_id": 1
            }
        )
        
        # Should return 401 or 403 (depends on auth implementation)
        assert response.status_code in [401, 403]
    
    def test_get_current_window_requires_auth(self):
        """Test that unauthenticated users cannot access /windows/current."""
        response = client.get("/windows/current")
        
        # Should return 401 or 403
        assert response.status_code in [401, 403]


# ============================================================================
# Test: Validation
# ============================================================================

class TestValidation:
    """Test request validation."""
    
    @pytest.mark.skip(reason="Requires OAuth session implementation")
    def test_create_window_invalid_batch_id(self, test_coordinator_session):
        """Test that invalid batch_id is rejected."""
        response = client.post(
            "/windows",
            json={
                "name": "Invalid Batch",
                "batch_id": -1,  # Invalid
                "specialization_id": 1
            },
            cookies=test_coordinator_session
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.skip(reason="Requires OAuth session implementation")
    def test_schedule_window_invalid_time_order(self, test_coordinator_session):
        """Test that end_time before start_time is rejected."""
        # Create window
        # Try to schedule with end_time < start_time
        # Assert 400 error
        pass
    
    @pytest.mark.skip(reason="Requires OAuth session implementation")
    def test_schedule_window_past_start_time(self, test_coordinator_session):
        """Test that past start_time is rejected."""
        # Create window
        # Try to schedule with start_time in past
        # Assert 400 error
        pass
