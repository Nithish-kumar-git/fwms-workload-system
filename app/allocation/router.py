"""
FastAPI router for allocation endpoints.
Spec reference: final_system_specification.md Section 2 (Category B)

Endpoints:
  POST /api/allocation/run    Run the allocation engine (coordinator only)
"""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
import logging

from app.auth.dependencies import get_current_coordinator_id
from app.allocation.schemas import (
    AllocationRunResponse,
    AllocationRecord,
    UnallocatedRecord,
    FacultyWorkloadSummary,
)
from app.allocation import service as allocation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/allocation", tags=["allocation"])


class AllocationScope(BaseModel):
    academic_year: str | None = None
    semester_type: str | None = None
    academic_cycle_id: int | None = None
    program_id: int | None = None

@router.post("/run", response_model=AllocationRunResponse)
async def run_allocation(
    coordinator_id: int = Depends(get_current_coordinator_id),
    scope: AllocationScope | None = None,
):
    """
    Run the automatic allocation engine.
    
    Coordinator-only endpoint. Processes all faculty preferences,
    enforces workload/shift/multi-section constraints, and assigns
    subjects to faculty. Unallocated subjects are assigned to
    lowest-load compatible faculty in the final pass.
    
    This is idempotent — re-running clears previous allocations
    for the current academic year/semester and re-allocates.
    """
    if scope is None:
        scope = AllocationScope()
        
    try:
        result = allocation_service.run_allocation(
            academic_year=scope.academic_year,
            semester_type=scope.semester_type,
            academic_cycle_id=scope.academic_cycle_id,
            program_id=scope.program_id
        )
    except Exception as e:
        logger.error(f"Allocation engine failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Allocation engine error: {str(e)}"
        )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    # Convert dicts to Pydantic models
    alloc_records = [AllocationRecord(**a) for a in result["allocations"]]
    unalloc_records = [UnallocatedRecord(**u) for u in result["unallocated"]]
    wl_summaries = [FacultyWorkloadSummary(**w) for w in result["workload_summary"]]
    
    return AllocationRunResponse(
        success=True,
        message=result["message"],
        subjects_total=result["subjects_total"],
        subjects_assigned=result["subjects_assigned"],
        subjects_unassigned=result["subjects_unassigned"],
        faculty_overloaded=result["faculty_overloaded"],
        faculty_underloaded=result["faculty_underloaded"],
        faculty_balanced=result["faculty_balanced"],
        allocations=alloc_records,
        unallocated=unalloc_records,
        workload_summary=wl_summaries,
    )
