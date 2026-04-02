"""
Pydantic schemas for preference endpoints.
Spec reference: final_system_specification.md Section 2 (Category A)

This module defines request and response models for faculty preference submission.
No business logic is allowed here.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SubmitPreferenceRequest(BaseModel):
    """Request model for POST /api/preferences"""
    
    subject_offering_id: int = Field(..., description="ID of the subject offering to prefer")
    preference_number: int = Field(..., ge=1, le=5, description="Preference rank (1-5)")


class PreferenceResponse(BaseModel):
    """Response model for a single preference record."""
    
    id: int
    staff_id: int
    subject_offering_id: int
    preference_number: int
    submitted_at: datetime
    # Joined fields (optional, populated on GET)
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    section_label: Optional[str] = None
    semester_label: Optional[str] = None
    program_name: Optional[str] = None
    # Additional fields from list_preferences query
    program: Optional[str] = None
    semester: Optional[str] = None
    section: Optional[str] = None
    tch: Optional[int] = 0


class SubmitPreferenceResponse(BaseModel):
    """Response model for POST /api/preferences"""
    
    success: bool = Field(..., description="Whether the submission was successful")
    message: str = Field(..., description="Human-readable result message")
    preference_id: Optional[int] = Field(None, description="ID of created preference record")


class DeletePreferenceResponse(BaseModel):
    """Response model for DELETE /api/preferences/{id}"""
    
    success: bool
    message: str


class PreferenceStatusResponse(BaseModel):
    """Response model for GET /api/preferences/status"""
    
    staff_id: int
    total_submitted: int = Field(..., description="Number of preferences submitted")
    remaining: int = Field(..., description="Number of preferences still needed")
    max_preferences: int = Field(default=5, description="Maximum allowed preferences")
    is_complete: bool = Field(..., description="Whether all 5 preferences submitted")
    preferences: list[PreferenceResponse] = Field(default_factory=list)
