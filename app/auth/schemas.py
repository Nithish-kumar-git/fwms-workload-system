"""
Authentication schemas (request/response models).
3-Role System: faculty / tt_coordinator / hod
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
    """Current user information with role."""
    staff_id: int
    email: EmailStr
    name: str
    role: str  # 'faculty' | 'tt_coordinator' | 'hod'
    is_class_teacher: bool = False
    ct_program: Optional[str] = None
    ct_section: Optional[str] = None
    ct_semester: Optional[str] = None
    ct_shift: Optional[str] = None
    ct_curriculum_year: Optional[str] = None


class LogoutResponse(BaseModel):
    """Logout confirmation."""
    success: bool
    message: str
