"""
Health endpoint tests.

Tests the /api/health endpoint to ensure the service is responding correctly.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_200():
    """Test that GET /api/health returns 200 OK."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_endpoint_returns_correct_structure():
    """Test that GET /api/health returns correct JSON structure."""
    response = client.get("/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


def test_health_endpoint_no_auth_required():
    """Test that health endpoint does not require authentication."""
    # Health check should work without any auth headers
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
