"""Coordinator allocation endpoints; transaction ownership stays in the service."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_coordinator_id
from app.allocation.schemas import AllocationRunResponse
from app.allocation import service as allocation_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/allocation", tags=["allocation"])


class AllocationScope(BaseModel):
    academic_year: str | None = None
    semester_id: int | None = Field(None, gt=0)
    program_id: int | None = Field(None, gt=0)


def _require_success(result):
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/run", response_model=AllocationRunResponse)
async def run_allocation(
    coordinator_id: int = Depends(get_current_coordinator_id),
    scope: AllocationScope | None = None,
):
    """Allocate only the selected semester/program in its matching OPEN cycle."""
    if scope is None or (scope.semester_id is None and not scope.academic_year):
        raise HTTPException(status_code=400, detail="Must provide either semester_id OR academic_year")
    try:
        result = allocation_service.run_allocation(
            academic_year=scope.academic_year, semester_id=scope.semester_id,
            program_id=scope.program_id,
        )
    except Exception as error:
        logger.error("Allocation failed (%s)", type(error).__name__)
        raise HTTPException(status_code=500, detail="Allocation failed; check current status before retrying") from None
    return _require_success(result)


@router.post("/run-all")
async def run_all_open_semesters(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Allocate all selected OPEN cycles atomically; any failure rolls back all."""
    try:
        batch = allocation_service.run_all_open_semesters()
    except Exception as error:
        logger.error("Batch allocation failed (%s)", type(error).__name__)
        raise HTTPException(status_code=500, detail="Allocation failed; check current status before retrying") from None
    _require_success(batch)
    results = batch["results"]
    assigned = sum(result["subjects_assigned"] for result in results)
    unassigned = sum(result["subjects_unassigned"] for result in results)
    return {
        "success": True,
        "message": f"Allocated {len(results)} semesters: {assigned} assigned, {unassigned} unassigned",
        "semesters_processed": len(results),
        "subjects_total": assigned + unassigned,
        "subjects_assigned": assigned, "subjects_unassigned": unassigned,
        "faculty_overloaded": 0, "faculty_underloaded": 0, "faculty_balanced": 0,
        "allocations": [], "unallocated": [],
        "results": [{"semester_id": result["semester_id"], "status": "success",
                     "assigned": result["subjects_assigned"], "unassigned": result["subjects_unassigned"]}
                    for result in results],
    }
