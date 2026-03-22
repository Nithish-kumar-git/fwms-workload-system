"""
Pydantic schemas for report endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


# --- Faculty Workload Report ---

class SubjectAssignment(BaseModel):
    """A single subject assigned to a faculty member."""
    course_code: str
    course_name: str
    program: str
    semester: str
    section: str
    l: int
    t: int
    p: int
    tch: int


class FacultyWorkloadRecord(BaseModel):
    """Workload report for one faculty."""
    staff_id: int
    emp_code: str
    name: str
    designation: str
    assigned_tch: int
    tch_norm: int
    deviation_hours: int
    subjects_assigned: list[SubjectAssignment]


class FacultyWorkloadResponse(BaseModel):
    """Response for GET /api/reports/faculty-workload"""
    total_faculty: int
    records: list[FacultyWorkloadRecord]


# --- Subject Summary ---

class SubjectSummaryRecord(BaseModel):
    """One row in the subject-wise report."""
    subject_offering_id: int
    course_code: str
    course_name: str
    program: str
    semester: str
    section: str
    faculty_name: Optional[str] = None
    faculty_emp_code: Optional[str] = None
    tch: int
    allocated: bool


class SubjectSummaryResponse(BaseModel):
    """Response for GET /api/reports/subject-summary"""
    total: int
    records: list[SubjectSummaryRecord]


# --- Department Summary ---

class DepartmentSummaryResponse(BaseModel):
    """Response for GET /api/reports/department-summary"""
    total_subject_offerings: int
    allocated_subjects: int
    unallocated_subjects: int
    total_faculty: int
    average_workload: float
    faculty_overloaded: int
    faculty_underloaded: int
    faculty_balanced: int
