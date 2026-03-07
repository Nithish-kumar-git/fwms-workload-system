"""
FastAPI router for staff management.
Coordinator-only CRUD endpoints for faculty records.

Endpoints:
  GET    /api/admin/staff              List all staff
  POST   /api/admin/staff              Create new staff
  PUT    /api/admin/staff/{id}         Update staff fields
  PATCH  /api/admin/staff/{id}/deactivate   Deactivate staff
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import logging

from app.auth.dependencies import get_current_coordinator_id
from app.admin.staff_service import (
    list_staff,
    create_staff,
    update_staff,
    deactivate_staff,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/staff", tags=["staff-management"])


# --- Schemas ---

class StaffRecord(BaseModel):
    id: int
    emp_code: str | None = None
    name: str | None = None
    email: str | None = None
    designation: str | None = None
    shift: str | None = None
    tch_norm: int | None = None
    is_coordinator: bool = False
    is_active: bool = True
    is_class_teacher: bool = False
    ct_program: str | None = None
    ct_section: str | None = None
    ct_semester: str | None = None
    ct_shift: str | None = None


class CreateStaffRequest(BaseModel):
    emp_code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    email: EmailStr
    designation: str = "Assistant Professor"
    shift: str = "SHIFT1"
    tch_norm: int = 16
    is_coordinator: bool = False
    is_class_teacher: bool = False
    ct_program: str | None = None
    ct_section: str | None = None
    ct_semester: str | None = None
    ct_shift: str | None = None


class UpdateStaffRequest(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    shift: Optional[str] = None
    tch_norm: Optional[int] = None
    is_coordinator: Optional[bool] = None
    is_class_teacher: Optional[bool] = None
    ct_program: Optional[str] = None
    ct_section: Optional[str] = None
    ct_semester: Optional[str] = None
    ct_shift: Optional[str] = None


class ActionResponse(BaseModel):
    success: bool
    message: str
    staff_id: int | None = None


# --- Endpoints ---

@router.get("", response_model=list[StaffRecord])
async def list_staff_endpoint(
    _coordinator_id: int = Depends(get_current_coordinator_id),
):
    """List all staff records. Coordinator-only."""
    return [StaffRecord(**s) for s in list_staff()]


@router.post("", response_model=ActionResponse)
async def create_staff_endpoint(
    body: CreateStaffRequest,
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Create a new staff record. Coordinator-only."""
    result = create_staff(
        coordinator_id=coordinator_id,
        emp_code=body.emp_code,
        name=body.name,
        email=body.email,
        designation=body.designation,
        shift=body.shift,
        tch_norm=body.tch_norm,
        is_coordinator=body.is_coordinator,
        is_class_teacher=body.is_class_teacher,
        ct_program=body.ct_program,
        ct_section=body.ct_section,
        ct_semester=body.ct_semester,
        ct_shift=body.ct_shift,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return ActionResponse(**result)


@router.put("/{staff_id}", response_model=ActionResponse)
async def update_staff_endpoint(
    staff_id: int,
    body: UpdateStaffRequest,
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Update staff fields. Coordinator-only."""
    result = update_staff(
        coordinator_id=coordinator_id,
        staff_id=staff_id,
        name=body.name,
        designation=body.designation,
        shift=body.shift,
        tch_norm=body.tch_norm,
        is_coordinator=body.is_coordinator,
        is_class_teacher=body.is_class_teacher,
        ct_program=body.ct_program,
        ct_section=body.ct_section,
        ct_semester=body.ct_semester,
        ct_shift=body.ct_shift,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return ActionResponse(**result)


@router.patch("/{staff_id}/deactivate", response_model=ActionResponse)
async def deactivate_staff_endpoint(
    staff_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Deactivate a staff member. Coordinator-only. Blocked if active allocations."""
    result = deactivate_staff(coordinator_id=coordinator_id, staff_id=staff_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return ActionResponse(**result)
