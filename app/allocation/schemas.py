"""
Pydantic schemas for allocation endpoints.
Spec reference: final_system_specification.md Section 2 (Category B)

Request and response models for automatic subject allocation.
"""

from pydantic import BaseModel, Field
from typing import Optional


class AllocationRecord(BaseModel):
    """Single allocation record in results."""
    staff_id: int
    staff_name: str
    emp_code: str
    subject_offering_id: int
    subject_code: str
    subject_name: str
    section_label: str
    semester_label: str
    program_name: str
    l_assigned: int
    t_assigned: int
    p_assigned: int
    tch: int
    preference_number: Optional[int] = None
    allocation_stage: str  # 'PREF_1', 'PREF_2', ..., 'FINAL_PASS'


class UnallocatedRecord(BaseModel):
    """Subject offering that could not be allocated."""
    subject_offering_id: int
    subject_code: str
    subject_name: str
    section_label: str
    semester_label: str
    program_name: str
    tch: int
    reason: str


class FacultyWorkloadSummary(BaseModel):
    """Workload summary for one faculty member."""
    staff_id: int
    emp_code: str
    name: str
    designation: str = "Unknown"
    tch_norm: int
    tch_assigned: int
    deviation: int
    status: str  # 'BALANCED', 'OVERLOADED', 'UNDERLOADED'


class AllocationRunResponse(BaseModel):
    """Response model for POST /api/allocation/run"""
    success: bool
    message: str
    semester_id: int | None = Field(None, description="Semester ID that was allocated")
    semester_label: str | None = Field(None, description="Semester label (e.g., 'I', 'II')")
    subjects_total: int = Field(..., description="Total subject offerings considered")
    subjects_assigned: int = Field(..., description="Successfully assigned")
    subjects_unassigned: int = Field(..., description="Could not be assigned")
    faculty_overloaded: int = Field(..., description="Faculty exceeding tch_norm")
    faculty_underloaded: int = Field(..., description="Faculty below tch_norm")
    faculty_balanced: int = Field(..., description="Faculty at or near tch_norm")
    allocations: list[AllocationRecord] = Field(default_factory=list)
    unallocated: list[UnallocatedRecord] = Field(default_factory=list)
    workload_summary: list[FacultyWorkloadSummary] = Field(default_factory=list)
