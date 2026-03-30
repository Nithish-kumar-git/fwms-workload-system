"""
Subject management API router.
Provides endpoints for TT Coordinator to manage subject offerings, programs, and sections.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.auth.dependencies import get_current_coordinator_id
from app.subjects import service

router = APIRouter(prefix="/api/subjects", tags=["subjects"])


class OfferingCreate(BaseModel):
    course_code: str
    course_name: str
    l: int
    t: int
    p: int
    credits: int
    course_category: str
    program_id: int
    semester_id: int
    section_id: int
    shift: int
    student_strength: int


class SectionCreate(BaseModel):
    label: str
    shift: int


class ProgramCreate(BaseModel):
    name: str
    ug_pg: str  # UG or PG


@router.get("/programs")
def list_programs(
    session: Session = Depends(get_db),
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """Get all active programs."""
    return service.get_all_programs(session)


@router.get("/sections")
def list_sections(
    session: Session = Depends(get_db),
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """Get all sections."""
    return service.get_all_sections(session)


@router.get("/semesters")
def list_semesters(
    session: Session = Depends(get_db),
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """Get all semesters."""
    return service.get_all_semesters(session)


@router.get("/offerings")
def list_offerings(
    semester_id: Optional[int] = None,
    program_id: Optional[int] = None,
    session: Session = Depends(get_db),
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """Get all subject offerings with optional filters."""
    return service.get_all_offerings(session, semester_id, program_id)


@router.post("/offerings")
def create_offering(
    data: OfferingCreate,
    session: Session = Depends(get_db),
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """Create a new subject offering."""
    result = service.create_offering(session, data.dict())
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.delete("/offerings/{offering_id}")
def delete_offering(
    offering_id: int,
    session: Session = Depends(get_db),
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """Delete or archive a subject offering."""
    return service.delete_offering(session, offering_id)


@router.post("/sections")
def create_section(
    data: SectionCreate,
    session: Session = Depends(get_db),
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """Create a new section."""
    return service.add_section(session, data.label, data.shift)


@router.post("/programs")
def create_program(
    data: ProgramCreate,
    session: Session = Depends(get_db),
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """Create a new program."""
    return service.add_program(session, data.name, data.ug_pg)
