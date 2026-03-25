"""
FastAPI router for academic cycle management.
Coordinator endpoints for creating, activating, and listing academic cycles.

Endpoints:
  POST /api/cycles          Create new cycle
  POST /api/cycles/activate Activate a cycle
  GET  /api/cycles          List all cycles
  GET  /api/cycles/active   Get current active cycle
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import logging

from app.auth.dependencies import get_current_coordinator_id
from app.admin.cycle_service_new import (
    create_cycle,
    activate_cycle,
    list_cycles,
    get_active_cycle,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cycles", tags=["academic-cycles"])


# --- Schemas ---

class CreateCycleRequest(BaseModel):
    academic_year: str = Field(..., description="e.g. 2025-2026")
    semester_id: int = Field(..., description="Semester ID (1-6 for I-VI)")
    start_date: str | None = None
    end_date: str | None = None


class ActivateCycleRequest(BaseModel):
    cycle_id: int


class CycleResponse(BaseModel):
    id: int
    academic_year: str
    semester_id: int
    semester_name: str
    status: str
    opened_at: str | None = None
    closed_at: str | None = None
    allocated_at: str | None = None
    frozen_at: str | None = None
    is_active: bool
    created_at: str


class ActionResponse(BaseModel):
    success: bool
    message: str
    cycle_id: int | None = None


# --- Endpoints ---

@router.post("", response_model=ActionResponse)
async def create_cycle_endpoint(
    body: CreateCycleRequest,
    _coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Create a new academic cycle. Coordinator-only."""
    result = create_cycle(
        academic_year=body.academic_year,
        semester_id=body.semester_id,
        start_date=body.start_date,
        end_date=body.end_date,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return ActionResponse(**result)


@router.post("/activate", response_model=ActionResponse)
async def activate_cycle_endpoint(
    body: ActivateCycleRequest,
    _coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Activate an academic cycle. Coordinator-only."""
    result = activate_cycle(body.cycle_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return ActionResponse(**result)


@router.get("", response_model=list[CycleResponse])
async def list_cycles_endpoint(
    _coordinator_id: int = Depends(get_current_coordinator_id),
):
    """List all academic cycles. Coordinator-only."""
    return [CycleResponse(**c) for c in list_cycles()]


@router.get("/active", response_model=CycleResponse | None)
async def get_active_cycle_endpoint():
    """Get the currently active cycle. Public endpoint."""
    cycle = get_active_cycle()
    if cycle is None:
        raise HTTPException(status_code=404, detail="No active academic cycle")
    return CycleResponse(**cycle)
