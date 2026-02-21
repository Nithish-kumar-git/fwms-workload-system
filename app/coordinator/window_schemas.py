"""
Window lifecycle request/response schemas.
Spec reference: window_lifecycle_design.md
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============================================================================
# Request Schemas
# ============================================================================

class CreateWindowRequest(BaseModel):
    """Request to create a new window in DRAFT state."""
    name: str = Field(..., min_length=1, max_length=255, description="Window name/description")
    batch_id: int = Field(..., gt=0, description="Batch ID")
    specialization_id: int = Field(..., gt=0, description="Specialization ID")
    start_time: Optional[str] = Field(None, description="Start time (ISO 8601), can be set later")
    end_time: Optional[str] = Field(None, description="End time (ISO 8601), can be set later")
    max_subjects_per_staff: int = Field(3, ge=1, le=10, description="Maximum subjects per staff")


class ScheduleWindowRequest(BaseModel):
    """Request to schedule a window (DRAFT → SCHEDULED)."""
    start_time: str = Field(..., description="Start time (ISO 8601), must be in future")
    end_time: str = Field(..., description="End time (ISO 8601), must be after start_time")


# ============================================================================
# Response Schemas
# ============================================================================

class WindowResponse(BaseModel):
    """Window metadata response."""
    id: int
    name: str
    status: str
    batch_id: int
    specialization_id: int
    start_time: Optional[str]
    end_time: Optional[str]
    max_subjects_per_staff: int
    created_at: str
    updated_at: str


class CurrentWindowResponse(BaseModel):
    """Current OPEN window for staff's batch/specialization."""
    window_id: Optional[int] = Field(None, description="Window ID if OPEN window exists")
    status: Optional[str] = Field(None, description="Window status (OPEN or null)")
    name: Optional[str] = Field(None, description="Window name")
    start_time: Optional[str] = Field(None, description="Window start time (ISO 8601)")
    end_time: Optional[str] = Field(None, description="Window end time (ISO 8601)")
    max_subjects_per_staff: Optional[int] = Field(None, description="Maximum subjects allowed")
    time_remaining_seconds: Optional[int] = Field(None, description="Seconds until window closes")
    is_active: bool = Field(..., description="True if OPEN window exists and not expired")


class WindowOperationResponse(BaseModel):
    """Response for window lifecycle operations."""
    success: bool
    message: str
    window_id: Optional[int] = None
