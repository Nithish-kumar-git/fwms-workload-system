"""
Authentication schemas (request/response models).
Spec reference: FSB_v1.3.md Section 1, BACKEND_STRUCTURE.md Section 3.1
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginResponse(BaseModel):
    """Response for login endpoint (redirect URL)."""
    authorization_url: str


class OAuthCallbackRequest(BaseModel):
    """OAuth callback query parameters."""
    code: str
    state: Optional[str] = None


class StaffInfoResponse(BaseModel):
    """Current user information."""
    staff_id: int
    email: EmailStr
    name: str
    is_coordinator: bool


class LogoutResponse(BaseModel):
    """Logout confirmation."""
    success: bool
    message: str
