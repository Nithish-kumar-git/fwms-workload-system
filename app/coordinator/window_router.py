"""
Window lifecycle router endpoints.
Spec reference: window_lifecycle_design.md

Coordinator endpoints for window management.
Staff endpoints for read-only window metadata.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from app.auth.dependencies import get_current_coordinator_id, get_current_staff_id
from app.coordinator.window_transactions import (
    create_window_transaction,
    schedule_window_transaction,
    open_window_transaction,
    close_window_transaction,
    archive_window_transaction
)
from app.coordinator.window_schemas import (
    CreateWindowRequest,
    ScheduleWindowRequest,
    WindowResponse,
    WindowOperationResponse,
    CurrentWindowResponse
)
from app.db.session import get_transaction
from app.utils.error_mapper import raise_http_from_db_error
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/windows", tags=["windows"])


# ============================================================================
# Coordinator Endpoints (Window Management)
# ============================================================================

@router.post("", response_model=WindowOperationResponse)
async def create_window(
    request: Request,
    body: CreateWindowRequest,
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """
    Create a new window in DRAFT state.
    
    Coordinator-only endpoint.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        result = create_window_transaction(
            coordinator_id=coordinator_id,
            name=body.name,
            batch_id=body.batch_id,
            specialization_id=body.specialization_id,
            start_time=body.start_time,
            end_time=body.end_time,
            max_subjects_per_staff=body.max_subjects_per_staff
        )
        
        if result["success"]:
            return WindowOperationResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create window error: {e}", exc_info=True)
        raise_http_from_db_error(e, correlation_id)


@router.post("/{window_id}/schedule", response_model=WindowOperationResponse)
async def schedule_window(
    request: Request,
    window_id: int,
    body: ScheduleWindowRequest,
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """
    Schedule a window (DRAFT → SCHEDULED).
    
    Preconditions:
    - start_time IS NOT NULL
    - end_time IS NOT NULL
    - end_time > start_time
    - start_time > now()
    
    After scheduling, start_time and end_time become IMMUTABLE.
    
    Coordinator-only endpoint.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        result = schedule_window_transaction(
            coordinator_id=coordinator_id,
            window_id=window_id,
            start_time=body.start_time,
            end_time=body.end_time
        )
        
        if result["success"]:
            return WindowOperationResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schedule window error: {e}", exc_info=True)
        raise_http_from_db_error(e, correlation_id)


@router.post("/{window_id}/open", response_model=WindowOperationResponse)
async def open_window(
    request: Request,
    window_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """
    Open a window (SCHEDULED → OPEN).
    
    Precondition: now() >= start_time
    Constraint: Only ONE OPEN window per (batch_id, specialization_id)
    
    Coordinator-only endpoint.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        result = open_window_transaction(
            coordinator_id=coordinator_id,
            window_id=window_id
        )
        
        if result["success"]:
            return WindowOperationResponse(**result)
        else:
            # Check for specific error conditions
            if "already open" in result["message"].lower():
                raise HTTPException(status_code=409, detail=result["message"])
            else:
                raise HTTPException(status_code=400, detail=result["message"])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Open window error: {e}", exc_info=True)
        raise_http_from_db_error(e, correlation_id)


@router.post("/{window_id}/close", response_model=WindowOperationResponse)
async def close_window(
    request: Request,
    window_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """
    Close a window (OPEN → CLOSED).
    
    Can be called early (before end_time) or after expiration.
    
    Coordinator-only endpoint.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        result = close_window_transaction(
            coordinator_id=coordinator_id,
            window_id=window_id
        )
        
        if result["success"]:
            return WindowOperationResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Close window error: {e}", exc_info=True)
        raise_http_from_db_error(e, correlation_id)


@router.post("/{window_id}/archive", response_model=WindowOperationResponse)
async def archive_window(
    request: Request,
    window_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """
    Archive a window (CLOSED → ARCHIVED).
    
    Coordinator-only endpoint.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        result = archive_window_transaction(
            coordinator_id=coordinator_id,
            window_id=window_id
        )
        
        if result["success"]:
            return WindowOperationResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Archive window error: {e}", exc_info=True)
        raise_http_from_db_error(e, correlation_id)


@router.get("/{window_id}", response_model=WindowResponse)
async def get_window(
    request: Request,
    window_id: int,
    coordinator_id: int = Depends(get_current_coordinator_id)
):
    """
    Get window metadata by ID.
    
    Coordinator-only endpoint.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        with get_transaction() as session:
            window = session.execute(
                text("""
                    SELECT id, name, status, batch_id, specialization_id,
                           start_time, end_time, max_subjects_per_staff,
                           created_at, updated_at
                    FROM selection_window
                    WHERE id = :window_id
                """),
                {"window_id": window_id}
            ).fetchone()
            
            if not window:
                raise HTTPException(status_code=404, detail="Window not found")
            
            return WindowResponse(
                id=window[0],
                name=window[1],
                status=window[2],
                batch_id=window[3],
                specialization_id=window[4],
                start_time=window[5].isoformat() if window[5] else None,
                end_time=window[6].isoformat() if window[6] else None,
                max_subjects_per_staff=window[7],
                created_at=window[8].isoformat() if window[8] else None,
                updated_at=window[9].isoformat() if window[9] else None
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get window error: {e}", exc_info=True)
        raise_http_from_db_error(e, correlation_id)


# ============================================================================
# Staff Endpoints (Read-Only)
# ============================================================================

@router.get("/current", response_model=CurrentWindowResponse)
async def get_current_window(
    request: Request,
    staff_id: int = Depends(get_current_staff_id)
):
    """
    Get current OPEN window for staff's batch/specialization.
    
    Returns window metadata if an OPEN window exists for the staff's
    assigned batch/specialization, otherwise returns is_active=false.
    
    Staff read-only endpoint (per stakeholder policy).
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        with get_transaction() as session:
            # Get staff's batch and specialization assignment
            assignment = session.execute(
                text("""
                    SELECT batch_id, specialization_id
                    FROM staff_assignment
                    WHERE staff_id = :staff_id
                    LIMIT 1
                """),
                {"staff_id": staff_id}
            ).fetchone()
            
            if not assignment:
                # Staff not assigned to any batch/spec
                return CurrentWindowResponse(
                    window_id=None,
                    status=None,
                    name=None,
                    start_time=None,
                    end_time=None,
                    max_subjects_per_staff=None,
                    time_remaining_seconds=None,
                    is_active=False
                )
            
            batch_id = assignment[0]
            specialization_id = assignment[1]
            
            # Get OPEN window for this batch/spec
            window = session.execute(
                text("""
                    SELECT id, name, start_time, end_time, max_subjects_per_staff,
                           EXTRACT(EPOCH FROM (end_time - now())) AS time_remaining
                    FROM selection_window
                    WHERE status = 'OPEN'
                      AND batch_id = :batch_id
                      AND specialization_id = :spec_id
                      AND now() BETWEEN start_time AND end_time
                    LIMIT 1
                """),
                {"batch_id": batch_id, "spec_id": specialization_id}
            ).fetchone()
            
            if not window:
                # No active OPEN window
                return CurrentWindowResponse(
                    window_id=None,
                    status=None,
                    name=None,
                    start_time=None,
                    end_time=None,
                    max_subjects_per_staff=None,
                    time_remaining_seconds=None,
                    is_active=False
                )
            
            # Active OPEN window found
            return CurrentWindowResponse(
                window_id=window[0],
                status='OPEN',
                name=window[1],
                start_time=window[2].isoformat() if window[2] else None,
                end_time=window[3].isoformat() if window[3] else None,
                max_subjects_per_staff=window[4],
                time_remaining_seconds=int(window[5]) if window[5] else 0,
                is_active=True
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current window error: {e}", exc_info=True)
        raise_http_from_db_error(e, correlation_id)
