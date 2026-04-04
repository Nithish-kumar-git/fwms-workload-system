"""
FastAPI router for admin / coordinator endpoints.
Spec reference: final_system_specification.md (Admin Override System)

All endpoints require coordinator authentication.

Endpoints:
  GET    /api/admin/allocations          Review all allocations
  PUT    /api/admin/allocation/{id}      Override allocation (reassign staff)
  POST   /api/admin/reassign             Move subject between faculty
  POST   /api/admin/allocation/freeze    Lock allocations
  POST   /api/admin/allocation/unfreeze  Unlock allocations (emergency)
  GET    /api/admin/workload-summary     Faculty workload report
"""

from fastapi import APIRouter, Depends, HTTPException
import logging

from app.auth.dependencies import get_current_coordinator_id
from app.admin.schemas import (
    AllocationReviewResponse, AllocationDetail,
    OverrideRequest, OverrideResponse,
    ReassignRequest, ReassignResponse,
    FreezeResponse,
    WorkloadSummaryResponse, WorkloadSummaryRecord,
)
from app.admin import service as admin_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/staff/list")
async def get_staff_list(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Get list of all staff with full details.
    Returns staff sorted by emp_code.
    """
    from app.admin.staff_service import list_staff
    
    return list_staff()


@router.get("/staff/list-debug")
async def get_staff_list_debug():
    """
    PUBLIC DEBUG endpoint - Get list of all staff with is_active status.
    No authentication required for debugging.
    """
    from app.db.session import get_transaction
    from sqlalchemy import text
    
    with get_transaction() as session:
        rows = session.execute(
            text("""
                SELECT id, name, emp_code, designation, is_active 
                FROM staff 
                WHERE emp_code IS NOT NULL 
                ORDER BY emp_code
            """)
        ).fetchall()
        
        return [
            {
                "id": r[0],
                "name": r[1],
                "emp_code": r[2],
                "designation": r[3],
                "is_active": r[4]
            }
            for r in rows
        ]


@router.get("/staff/debug-role-ct")
async def debug_role_ct():
    """
    PUBLIC DEBUG endpoint - Test role and CT field mapping.
    No authentication required for debugging.
    """
    from app.admin.staff_service import list_staff
    
    result = list_staff()
    return result[:30]  # return first 30 (all staff)


@router.get("/allocations", response_model=AllocationReviewResponse)
async def list_allocations(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    List all allocations with full staff + subject details.
    Used by the admin dashboard to inspect allocation results.
    """
    allocs = admin_service.list_allocations()
    return AllocationReviewResponse(
        total=len(allocs),
        allocations=[AllocationDetail(**a) for a in allocs],
    )


@router.put("/allocation/{allocation_id}", response_model=OverrideResponse)
async def override_allocation(
    allocation_id: int,
    request: OverrideRequest,
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Override an allocation: reassign a subject to a different faculty.
    Validates shift compatibility, workload capacity, and multi-section constraint.
    """
    # DEBUG: Log incoming request
    print(f"OVERRIDE DEBUG: allocation_id={allocation_id}, new_staff_id={request.new_staff_id}, type={type(request.new_staff_id)}", flush=True)
    logger.info(f"Override request: allocation_id={allocation_id}, new_staff_id={request.new_staff_id}")
    
    # DEBUG: Check if staff exists in database
    from app.db.session import get_transaction
    from sqlalchemy import text
    with get_transaction() as session:
        check = session.execute(
            text("SELECT id, name, is_active FROM staff WHERE id = :sid"),
            {"sid": request.new_staff_id}
        ).fetchone()
        print(f"OVERRIDE DEBUG: staff lookup result = {check}", flush=True)
    
    result = admin_service.override_allocation(
        allocation_id=allocation_id,
        new_staff_id=request.new_staff_id,
        actor_id=coordinator_id,
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return OverrideResponse(**result)


@router.post("/reassign", response_model=ReassignResponse)
async def reassign_subject(
    request: ReassignRequest,
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Move a subject offering from one faculty to another.
    Validates constraints and updates workload summaries.
    """
    result = admin_service.reassign_subject(
        subject_offering_id=request.subject_offering_id,
        from_staff_id=request.from_staff_id,
        to_staff_id=request.to_staff_id,
        actor_id=coordinator_id,
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return ReassignResponse(**result)


@router.post("/allocation/freeze", response_model=FreezeResponse)
async def freeze_allocation(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Freeze all allocations. Prevents preference submission and re-runs.
    """
    result = admin_service.freeze_allocation(actor_id=coordinator_id)
    return FreezeResponse(**result)


@router.post("/allocation/unfreeze", response_model=FreezeResponse)
async def unfreeze_allocation(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Emergency unfreeze. Re-enables modifications.
    """
    result = admin_service.unfreeze_allocation(actor_id=coordinator_id)
    return FreezeResponse(**result)


@router.get("/workload-summary", response_model=WorkloadSummaryResponse)
async def get_workload_summary(
    coordinator_id: int = Depends(get_current_coordinator_id),
    academic_year: str | None = None,
    semester_type: str | None = None,
):
    """
    Get workload summary for all faculty.
    Used for the final workload report (deviation analysis).
    
    Query parameters:
    - academic_year: Optional, defaults to active cycle
    - semester_type: Optional, defaults to active cycle
    """
    result = admin_service.get_workload_summary(
        academic_year=academic_year,
        semester_type=semester_type
    )
    result["records"] = [WorkloadSummaryRecord(**r) for r in result["records"]]
    return WorkloadSummaryResponse(**result)
