"""
Authentication endpoint tests.

Tests the /api/auth/me endpoint to ensure proper authentication
and authorization checks are in place.
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


def test_auth_me_without_token_returns_401():
    """Test that GET /api/auth/me without token returns 401 Unauthorized."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_auth_me_with_invalid_token_returns_401():
    """Test that GET /api/auth/me with invalid token returns 401 Unauthorized."""
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401


def test_auth_me_with_malformed_token_returns_401():
    """Test that GET /api/auth/me with malformed token returns 401 Unauthorized."""
    # Token without "Bearer" prefix
    headers = {"Authorization": "not_bearer_token"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401


def test_auth_me_with_empty_token_returns_401():
    """Test that GET /api/auth/me with empty Bearer token returns 401 Unauthorized."""
    headers = {"Authorization": "Bearer "}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401


def test_auth_me_with_demo_token_returns_200():
    """Test that GET /api/auth/me with valid demo token returns 200 OK."""
    # First, get a valid token from demo-login
    login_response = client.post("/api/auth/demo-login")
    assert login_response.status_code == 200
    
    token = login_response.json()["access_token"]
    
    # Now use that token to call /auth/me
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200


def test_auth_me_with_demo_token_returns_user_data():
    """Test that /api/auth/me with valid token returns correct user data."""
    # Get valid token
    login_response = client.post("/api/auth/demo-login")
    token = login_response.json()["access_token"]
    
    # Call /auth/me
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "email" in data
    assert data["email"] == "demo@fwms-demo.com"
    assert "name" in data
    assert "role" in data
    assert data["role"] == "hod"


def test_auth_me_response_contains_staff_id():
    """Test that /api/auth/me response contains staff_id."""
    # Get valid token
    login_response = client.post("/api/auth/demo-login")
    token = login_response.json()["access_token"]
    
    # Call /auth/me
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "staff_id" in data
    assert isinstance(data["staff_id"], int)
    assert data["staff_id"] > 0


def test_auth_me_no_authorization_header_returns_401():
    """Test that /api/auth/me without Authorization header returns 401."""
    # No headers at all
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_auth_me_with_expired_signature_returns_401():
    """Test that /api/auth/me with a token with invalid signature returns 401."""
    # Create a JWT-like string with invalid signature
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.invalid_signature_here"
    
    headers = {"Authorization": f"Bearer {fake_token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
