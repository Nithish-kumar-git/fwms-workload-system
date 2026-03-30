"""
FastAPI router for preference window management.
Coordinator endpoints for opening/closing the preference submission window.

Endpoints:
  POST /api/pref-window/open     Open preference window
  POST /api/pref-window/close    Close preference window
  GET  /api/pref-window/status   Get current window status
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import logging

from app.auth.dependencies import get_current_coordinator_id
from app.preference.window_service import (
    open_preference_window,
    close_preference_window,
    get_window_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pref-window", tags=["preference-window"])


# --- Schemas ---

class OpenWindowRequest(BaseModel):
    start_time: str = Field(..., description="ISO datetime")
    end_time: str = Field(..., description="ISO datetime")
    academic_year: str | None = Field(None, description="e.g. 2025-2026")
    semester_id: int | None = Field(None, description="Semester ID (1-6)")
    cycle_id: int | None = Field(None)


class WindowResponse(BaseModel):
    success: bool
    message: str
    window_id: int | None = None


class WindowStatusResponse(BaseModel):
    is_open: bool
    status: str = 'CLOSED'  # 'OPEN', 'CLOSED', 'SCHEDULED'
    window_id: int | None = None
    start_time: str | None = None
    end_time: str | None = None
    remaining_seconds: int = 0
    academic_year: str | None = None
    semester_id: int | None = None


# --- Endpoints ---

@router.post("/open", response_model=WindowResponse)
async def open_window(
    body: OpenWindowRequest,
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Open a preference submission window. Coordinator-only."""
    result = open_preference_window(
        coordinator_id=coordinator_id,
        start_time=body.start_time,
        end_time=body.end_time,
        academic_year=body.academic_year,
        semester_id=body.semester_id,
        cycle_id=body.cycle_id,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return WindowResponse(**result)


@router.post("/close", response_model=WindowResponse)
async def close_window(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Close the active preference window. Coordinator-only."""
    result = close_preference_window(coordinator_id=coordinator_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return WindowResponse(**result)


@router.get("/status", response_model=WindowStatusResponse)
async def window_status():
    """Get current preference window status. Public endpoint."""
    return WindowStatusResponse(**get_window_status())


@router.post("/open-group")
async def open_window_for_group(
    body: dict,
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Open preference window for ODD (1,3,5) or EVEN (2,4,6) semesters at once.
    Coordinator-only endpoint.
    """
    semester_group = body.get("semester_group")  # "ODD" or "EVEN"
    academic_year = body.get("academic_year")
    start_time = body.get("start_time")
    end_time = body.get("end_time")
    
    if semester_group not in ["ODD", "EVEN"]:
        raise HTTPException(status_code=400, detail="semester_group must be ODD or EVEN")
    
    if not academic_year or not start_time or not end_time:
        raise HTTPException(status_code=400, detail="academic_year, start_time, and end_time are required")
    
    # Determine semester IDs based on group
    if semester_group == "ODD":
        semester_ids = [1, 3, 5]
    else:  # EVEN
        semester_ids = [2, 4, 6]
    
    results = []
    from app.db.session import get_transaction
    from sqlalchemy import text
    
    # First, close any existing open windows
    with get_transaction() as session:
        session.execute(
            text("UPDATE selection_window SET status = 'CLOSED' WHERE status = 'OPEN'")
        )
        session.commit()
    
    # Open window for each semester in the group
    for sem_id in semester_ids:
        try:
            result = open_preference_window(
                coordinator_id=coordinator_id,
                start_time=start_time,
                end_time=end_time,
                academic_year=academic_year,
                semester_id=sem_id,
                cycle_id=None,
            )
            results.append({
                "semester_id": sem_id,
                "status": "opened" if result["success"] else "error",
                "message": result.get("message", ""),
                "window_id": result.get("window_id"),
            })
        except Exception as e:
            logger.error(f"Failed to open window for semester {sem_id}: {e}")
            results.append({
                "semester_id": sem_id,
                "status": "error",
                "message": str(e),
                "window_id": None,
            })
    
    # Check if all succeeded
    all_success = all(r["status"] == "opened" for r in results)
    
    return {
        "success": all_success,
        "semester_group": semester_group,
        "message": f"Opened windows for {semester_group} semesters ({', '.join(map(str, semester_ids))})",
        "results": results,
    }
