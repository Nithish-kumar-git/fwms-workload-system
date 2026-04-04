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

from app.auth.dependencies import get_current_hod_id
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
    role: str | None = None
    is_coordinator: bool = False
    is_active: bool = True
    is_class_teacher: bool = False
    ct_program: str | None = None
    ct_section: str | None = None
    ct_semester: str | None = None
    ct_shift: str | None = None
    ct_curriculum_year: str | None = None


class CreateStaffRequest(BaseModel):
    emp_code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    email: EmailStr
    designation: str = "Assistant Professor"
    shift: str = "SHIFT1"
    tch_norm: int = 40
    role: str = "faculty"  # 'faculty', 'tt_coordinator', 'hod'
    is_coordinator: bool = False
    is_class_teacher: bool = False
    ct_program: str | None = None
    ct_section: str | None = None
    ct_semester: str | None = None
    ct_shift: str | None = None
    ct_curriculum_year: str | None = None


class UpdateStaffRequest(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    shift: Optional[str] = None
    tch_norm: Optional[int] = None
    role: Optional[str] = None  # 'faculty', 'tt_coordinator', 'hod'
    is_coordinator: Optional[bool] = None
    is_class_teacher: Optional[bool] = None
    ct_program: Optional[str] = None
    ct_section: Optional[str] = None
    ct_semester: Optional[str] = None
    ct_shift: Optional[str] = None
    ct_curriculum_year: Optional[str] = None


class ActionResponse(BaseModel):
    success: bool
    message: str
    staff_id: int | None = None


# --- Endpoints ---

@router.get("", response_model=list[StaffRecord])
async def list_staff_endpoint(
    _hod_id: int = Depends(get_current_hod_id),
):
    """List all staff records. Coordinator-only."""
    return [StaffRecord(**s) for s in list_staff()]


@router.post("", response_model=ActionResponse)
async def create_staff_endpoint(
    body: CreateStaffRequest,
    hod_id: int = Depends(get_current_hod_id),
):
    """Create a new staff record. HOD-only."""
    result = create_staff(
        coordinator_id=hod_id,
        emp_code=body.emp_code,
        name=body.name,
        email=body.email,
        designation=body.designation,
        shift=body.shift,
        tch_norm=body.tch_norm,
        role=body.role,
        is_coordinator=body.is_coordinator,
        is_class_teacher=body.is_class_teacher,
        ct_program=body.ct_program,
        ct_section=body.ct_section,
        ct_semester=body.ct_semester,
        ct_shift=body.ct_shift,
        ct_curriculum_year=body.ct_curriculum_year,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return ActionResponse(**result)


@router.put("/{staff_id}", response_model=ActionResponse)
async def update_staff_endpoint(
    staff_id: int,
    body: UpdateStaffRequest,
    hod_id: int = Depends(get_current_hod_id),
):
    """Update staff fields. HOD-only."""
    result = update_staff(
        coordinator_id=hod_id,
        staff_id=staff_id,
        name=body.name,
        designation=body.designation,
        shift=body.shift,
        tch_norm=body.tch_norm,
        role=body.role,
        is_coordinator=body.is_coordinator,
        is_class_teacher=body.is_class_teacher,
        ct_program=body.ct_program,
        ct_section=body.ct_section,
        ct_semester=body.ct_semester,
        ct_shift=body.ct_shift,
        ct_curriculum_year=body.ct_curriculum_year,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return ActionResponse(**result)


@router.patch("/{staff_id}/deactivate", response_model=ActionResponse)
async def deactivate_staff_endpoint(
    staff_id: int,
    hod_id: int = Depends(get_current_hod_id),
):
    """Deactivate a staff member. HOD-only. Blocked if active allocations."""
    result = deactivate_staff(coordinator_id=hod_id, staff_id=staff_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return ActionResponse(**result)


class UpdateEmailRequest(BaseModel):
    email: EmailStr


class UpdateRoleRequest(BaseModel):
    role: str = Field(..., pattern="^(faculty|tt_coordinator|hod)$")


@router.get("/emails", response_model=list[StaffRecord])
async def list_staff_emails(
    _hod_id: int = Depends(get_current_hod_id),
):
    """List all staff with their emails. HOD-only."""
    return [StaffRecord(**s) for s in list_staff()]


@router.patch("/{staff_id}/email", response_model=ActionResponse)
async def update_staff_email(
    staff_id: int,
    body: UpdateEmailRequest,
    hod_id: int = Depends(get_current_hod_id),
):
    """Update staff email address. HOD-only."""
    from app.db.session import get_transaction
    from sqlalchemy import text
    
    with get_transaction() as session:
        # Check if staff exists
        staff = session.execute(
            text("SELECT id, name FROM staff WHERE id = :id"),
            {"id": staff_id}
        ).fetchone()
        
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        # Check if email already in use
        existing = session.execute(
            text("SELECT id FROM staff WHERE email = :email AND id != :id"),
            {"email": body.email, "id": staff_id}
        ).fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use by another staff member")
        
        # Update email
        session.execute(
            text("UPDATE staff SET email = :email WHERE id = :id"),
            {"email": body.email, "id": staff_id}
        )
        
        # Audit log
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:hod_id, 'STAFF_EMAIL_UPDATED',
                        jsonb_build_object('staff_id', :staff_id, 'new_email', :email))
            """),
            {"hod_id": hod_id, "staff_id": staff_id, "email": body.email}
        )
        
        session.commit()
    
    return ActionResponse(success=True, message="Email updated successfully", staff_id=staff_id)


@router.patch("/{staff_id}/role", response_model=ActionResponse)
async def update_staff_role(
    staff_id: int,
    body: UpdateRoleRequest,
    hod_id: int = Depends(get_current_hod_id),
):
    """Update staff role. HOD-only."""
    from app.db.session import get_transaction
    from sqlalchemy import text
    
    with get_transaction() as session:
        # Check if staff exists
        staff = session.execute(
            text("SELECT id, name, role FROM staff WHERE id = :id"),
            {"id": staff_id}
        ).fetchone()
        
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        old_role = staff[2]
        
        # Update role
        session.execute(
            text("UPDATE staff SET role = :role WHERE id = :id"),
            {"role": body.role, "id": staff_id}
        )
        
        # Audit log
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:hod_id, 'STAFF_ROLE_UPDATED',
                        jsonb_build_object('staff_id', :staff_id, 'old_role', :old_role, 'new_role', :new_role))
            """),
            {"hod_id": hod_id, "staff_id": staff_id, "old_role": old_role, "new_role": body.role}
        )
        
        session.commit()
    
    return ActionResponse(success=True, message=f"Role updated to {body.role}", staff_id=staff_id)
