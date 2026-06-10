"""
Demo login endpoint tests.

Tests the /api/auth/demo-login endpoint to ensure demo users can log in
without authentication and receive valid JWT tokens.
"""

import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

# Skip all tests in this file if DATABASE_URL is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="Skipping: DATABASE_URL not set in this environment"
)

client = TestClient(app)


def test_demo_login_returns_200():
    """Test that POST /api/auth/demo-login returns 200 OK."""
    response = client.post("/api/auth/demo-login")
    assert response.status_code == 200


def test_demo_login_returns_access_token():
    """Test that demo login response contains access_token."""
    response = client.post("/api/auth/demo-login")
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_demo_login_returns_token_type():
    """Test that demo login response contains token_type."""
    response = client.post("/api/auth/demo-login")
    assert response.status_code == 200
    
    data = response.json()
    assert "token_type" in data
    assert data["token_type"] == "bearer"


def test_demo_login_returns_user_with_demo_email():
    """Test that demo login response contains user with demo email."""
    response = client.post("/api/auth/demo-login")
    assert response.status_code == 200
    
    data = response.json()
    assert "user" in data
    assert "email" in data["user"]
    assert data["user"]["email"] == "demo@fwms-demo.com"


def test_demo_login_returns_user_with_name():
    """Test that demo login response contains user with name."""
    response = client.post("/api/auth/demo-login")
    assert response.status_code == 200
    
    data = response.json()
    assert "user" in data
    assert "name" in data["user"]
    assert isinstance(data["user"]["name"], str)
    assert len(data["user"]["name"]) > 0


def test_demo_login_returns_user_with_role():
    """Test that demo login response contains user with HOD role."""
    response = client.post("/api/auth/demo-login")
    assert response.status_code == 200
    
    data = response.json()
    assert "user" in data
    assert "role" in data["user"]
    assert data["user"]["role"] == "hod"


def test_demo_login_is_idempotent():
    """Test that calling demo-login twice still returns 200 with valid token."""
    # First call
    response1 = client.post("/api/auth/demo-login")
    assert response1.status_code == 200
    data1 = response1.json()
    assert "access_token" in data1
    
    # Second call
    response2 = client.post("/api/auth/demo-login")
    assert response2.status_code == 200
    data2 = response2.json()
    assert "access_token" in data2
    
    # Both should return valid tokens (they may be different, that's ok)
    assert len(data1["access_token"]) > 0
    assert len(data2["access_token"]) > 0


def test_demo_login_no_auth_required():
    """Test that demo login does not require authentication."""
    # Demo login should work without any auth headers
    response = client.post("/api/auth/demo-login")
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "demo@fwms-demo.com"


def test_demo_login_no_request_body_required():
    """Test that demo login does not require a request body."""
    # No JSON body needed
    response = client.post("/api/auth/demo-login")
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
