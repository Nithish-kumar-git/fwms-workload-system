"""
API endpoints for semester state management.
PHASE 2: Semester workflow control.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import logging

from app.auth.dependencies import get_current_coordinator_id, get_current_hod_id
from app.coordinator import semester_state_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/semester", tags=["semester-state"])


class SemesterStateResponse(BaseModel):
    """Response model for semester state queries"""
    id: int
    label: str
    state: str
    opened_at: str | None = None
    closed_at: str | None = None
    allocated_at: str | None = None
    frozen_at: str | None = None
    frozen_by_staff_id: int | None = None


class StateTransitionResponse(BaseModel):
    """Response model for state transitions"""
    success: bool
    message: str


@router.get("/{semester_id}/state", response_model=SemesterStateResponse)
async def get_semester_state(
    semester_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """
    Get current state of a semester.
    
    Coordinator-only endpoint.
    """
    state_info = semester_state_service.get_semester_state(semester_id)
    
    if not state_info:
        raise HTTPException(status_code=404, detail=f"Semester {semester_id} not found")
    
    return SemesterStateResponse(
        id=state_info["id"],
        label=state_info["label"],
        state=state_info["state"],
        opened_at=state_info["opened_at"].isoformat() if state_info["opened_at"] else None,
        closed_at=state_info["closed_at"].isoformat() if state_info["closed_at"] else None,
        allocated_at=state_info["allocated_at"].isoformat() if state_info["allocated_at"] else None,
        frozen_at=state_info["frozen_at"].isoformat() if state_info["frozen_at"] else None,
        frozen_by_staff_id=state_info["frozen_by_staff_id"]
    )


@router.post("/{semester_id}/open", response_model=StateTransitionResponse)
async def open_semester(
    semester_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """
    Open semester for faculty preference submission.
    
    Transition: CLOSED → OPEN
    
    Coordinator-only endpoint.
    """
    result = semester_state_service.open_semester(semester_id, coordinator_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return StateTransitionResponse(success=True, message=result["message"])


@router.post("/{semester_id}/close", response_model=StateTransitionResponse)
async def close_semester(
    semester_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """
    Close semester (lock preferences, ready for allocation).
    
    Transition: OPEN → CLOSED
    
    Coordinator-only endpoint.
    """
    result = semester_state_service.close_semester(semester_id, coordinator_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return StateTransitionResponse(success=True, message=result["message"])


@router.post("/{semester_id}/freeze", response_model=StateTransitionResponse)
async def freeze_semester(
    semester_id: int,
    hod_id: int = Depends(get_current_hod_id)
):
    """
    Freeze semester (finalize, no further changes allowed).
    
    Transition: ALLOCATED → FROZEN
    
    HOD-only endpoint.
    """
    result = semester_state_service.freeze_semester(semester_id, hod_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return StateTransitionResponse(success=True, message=result["message"])
