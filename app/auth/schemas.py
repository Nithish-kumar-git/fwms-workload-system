"""
Pydantic schemas for authentication endpoints.
Spec reference: BACKEND_STRUCTURE.md Section 3.1

This module defines request and response models for authentication.
No business logic is allowed here.
"""

from pydantic import BaseModel, Field


class StaffInfoResponse(BaseModel):
    """Response model for GET /api/auth/me"""
    
    staff_id: int = Field(..., description="Staff member ID")
    email: str = Field(..., description="Staff email address")
    name: str = Field(..., description="Staff member name")
    is_coordinator: bool = Field(..., description="Whether staff member is a coordinator")
