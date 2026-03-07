"""
Pydantic schemas for admin endpoints.
Spec reference: final_system_specification.md (Admin Override System)
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# --- Allocation Review ---

class AllocationDetail(BaseModel):
    """Full allocation record with joined staff + subject details."""
    allocation_id: int
    staff_id: int
    staff_name: str
    emp_code: str
    designation: str
    subject_offering_id: int
    subject_code: str
    subject_name: str
    section_label: str
    semester_label: str
    program_name: str
    l_assigned: int
    t_assigned: int
    p_assigned: int
    ltp_total: int
    allocated_at: datetime


class AllocationReviewResponse(BaseModel):
    """Response for GET /api/admin/allocations"""
    total: int
    allocations: list[AllocationDetail]


# --- Manual Override ---

class OverrideRequest(BaseModel):
    """Request for PUT /api/admin/allocation/{id}"""
    new_staff_id: int = Field(..., description="Staff ID to reassign to")


class OverrideResponse(BaseModel):
    """Response for PUT /api/admin/allocation/{id}"""
    success: bool
    message: str
    allocation_id: int
    old_staff_id: int
    new_staff_id: int


# --- Subject Reassignment ---

class ReassignRequest(BaseModel):
    """Request for POST /api/admin/reassign"""
    subject_offering_id: int
    from_staff_id: int
    to_staff_id: int


class ReassignResponse(BaseModel):
    """Response for POST /api/admin/reassign"""
    success: bool
    message: str
    allocation_id: Optional[int] = None


# --- Freeze / Unfreeze ---

class FreezeResponse(BaseModel):
    """Response for freeze/unfreeze endpoints"""
    success: bool
    message: str
    allocation_locked: bool


# --- Workload Summary ---

class WorkloadSummaryRecord(BaseModel):
    """Single faculty workload summary row."""
    staff_id: int
    emp_code: str
    name: str
    designation: str
    tch_norm: int
    tch_assigned: int
    deviation: int
    total_workload: int
    status: str  # BALANCED / OVERLOADED / UNDERLOADED


class WorkloadSummaryResponse(BaseModel):
    """Response for GET /api/admin/workload-summary"""
    total_faculty: int
    overloaded: int
    underloaded: int
    balanced: int
    records: list[WorkloadSummaryRecord]
