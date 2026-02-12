"""
Pydantic schemas for selection endpoints.
Spec reference: BACKEND_STRUCTURE.md Section 3.1

This module defines request and response models for subject selection.
No business logic is allowed here.
"""

from pydantic import BaseModel, Field


class SelectSubjectRequest(BaseModel):
    """Request model for POST /api/selection/select"""
    
    subject_id: int = Field(..., description="ID of the subject to select")
    batch_id: int = Field(..., description="Batch ID for eligibility verification")
    specialization_id: int = Field(..., description="Specialization ID for eligibility verification")


class SelectSubjectResponse(BaseModel):
    """Response model for POST /api/selection/select"""
    
    success: bool = Field(..., description="Whether the selection was successful")
    message: str = Field(..., description="Human-readable result message")
    selection_id: int | None = Field(None, description="ID of the created selection record (null on failure)")
