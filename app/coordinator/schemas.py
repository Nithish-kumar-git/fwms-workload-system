"""
Pydantic schemas for coordinator endpoints.
Spec reference: BACKEND_STRUCTURE.md Section 3.1

This module defines request and response models for coordinator operations.
No business logic is allowed here.
"""

from pydantic import BaseModel, Field


class OverrideSubjectRequest(BaseModel):
    """Request model for POST /api/coordinator/override"""
    
    subject_id: int = Field(..., description="ID of the subject to override")


class OverrideSubjectResponse(BaseModel):
    """Response model for POST /api/coordinator/override"""
    
    success: bool = Field(..., description="Whether the override was successful")
    message: str = Field(..., description="Human-readable result message")
    affected_staff_id: int | None = Field(None, description="ID of the staff member whose selection was overridden")
