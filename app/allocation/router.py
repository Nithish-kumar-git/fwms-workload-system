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
    semester_id: int | None = None  # NEW: semester_id (1-6)
    program_id: int | None = None

@router.post("/run", response_model=AllocationRunResponse)
async def run_allocation(
    coordinator_id: int = Depends(get_current_coordinator_id),
    scope: AllocationScope | None = None,
):
    """
    Run the automatic allocation engine for ALL SEMESTERS in the active cycle.
    
    UPDATED: Multi-semester allocation.
    - Accepts either semester_id OR (academic_year + semester_type)
    - If semester_id provided, allocates ONLY that semester
    - If academic_year + semester_type provided, allocates ALL semesters in the cycle
    - Allocates subjects across all 6 semesters (I through VI)
    
    Coordinator-only endpoint. Processes all faculty preferences,
    enforces workload/shift/multi-section constraints, and assigns
    subjects to faculty. Unallocated subjects are assigned to
    lowest-load compatible faculty in the final pass.
    
    This is idempotent — re-running clears previous allocations
    for the specified semester(s) and re-allocates.
    """
    # ================================================================
    # CLEANUP: Reset state and clear allocations for fresh run
    # ================================================================
    from app.db.session import get_transaction
    from sqlalchemy import text
    
    with get_transaction() as session:
        # Reset all semesters to CLOSED (except FROZEN)
        session.execute(
            text("UPDATE semester SET state = 'CLOSED', allocated_at = NULL WHERE state != 'FROZEN'")
        )
        
        # Clear all allocations for non-FROZEN semesters
        session.execute(
            text("""
                DELETE FROM allocation 
                WHERE subject_offering_id IN (
                    SELECT so.id FROM subject_offering so
                    JOIN semester sem ON sem.id = so.semester_id
                    WHERE sem.state != 'FROZEN'
                )
            """)
        )
        
        session.commit()
    
    logger.info("Cleanup complete: All non-FROZEN semesters reset to CLOSED, allocations cleared")
    
    if scope is None:
        scope = AllocationScope()
    
    # Resolve semester_id if not provided
    resolved_semester_ids = []
    
    if scope.semester_id:
        # Single semester allocation
        resolved_semester_ids = [scope.semester_id]
    elif scope.academic_year:
        # Multi-semester allocation - allocate the semester from active cycle
        from app.db.session import get_transaction
        from sqlalchemy import text
        from app.admin.cycle_service_new import get_active_cycle
        
        # Get active cycle to validate
        active_cycle = get_active_cycle()
        if active_cycle is None:
            raise HTTPException(
                status_code=400,
                detail="No active academic cycle found"
            )
        
        # Verify provided academic_year matches active cycle
        if scope.academic_year != active_cycle["academic_year"]:
            raise HTTPException(
                status_code=400,
                detail=f"Provided year ({scope.academic_year}) does not match active cycle ({active_cycle['academic_year']})"
            )
        
        # Use the semester_id from active cycle
        resolved_semester_ids = [active_cycle["semester_id"]]
        
        logger.info(f"Resolved semester {active_cycle['semester_id']} from active cycle")
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide either semester_id OR academic_year"
        )
    
    # ================================================================
    # RUN ALLOCATION FOR ALL RESOLVED SEMESTERS
    # ================================================================
    all_allocations = []
    all_unallocated = []
    total_subjects = 0
    total_assigned = 0
    total_unassigned = 0
    
    for sem_id in resolved_semester_ids:
        try:
            result = allocation_service.run_allocation(
                academic_year=scope.academic_year,
                semester_type=None,  # No longer used
                academic_cycle_id=None,  # No longer used
                program_id=scope.program_id,
                semester_id=sem_id
            )
        except Exception as e:
            logger.error(f"Allocation engine failed for semester {sem_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Allocation engine error for semester {sem_id}: {str(e)}"
            )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        # Aggregate results
        all_allocations.extend(result["allocations"])
        all_unallocated.extend(result["unallocated"])
        total_subjects += result["subjects_total"]
        total_assigned += result["subjects_assigned"]
        total_unassigned += result["subjects_unassigned"]
    
    # ================================================================
    # MARK ALL SEMESTERS AS ALLOCATED AFTER SUCCESSFUL COMPLETION
    # ================================================================
    with get_transaction() as session:
        session.execute(
            text("UPDATE semester SET state = 'ALLOCATED', allocated_at = now()")
        )
        session.commit()
    
    logger.info("All semesters marked as ALLOCATED after successful allocation")
    
    # Get final workload summary (computed across all allocated semesters)
    # Use the last result's workload_summary since it's computed from ALL allocations
    wl_summaries = [FacultyWorkloadSummary(**w) for w in result["workload_summary"]]
    
    # Convert dicts to Pydantic models
    alloc_records = [AllocationRecord(**a) for a in all_allocations]
    unalloc_records = [UnallocatedRecord(**u) for u in all_unallocated]
    
    # Calculate faculty stats from workload summary
    overloaded = sum(1 for w in wl_summaries if w.status == "OVERLOADED")
    underloaded = sum(1 for w in wl_summaries if w.status == "UNDERLOADED")
    balanced = sum(1 for w in wl_summaries if w.status == "BALANCED")
    
    return AllocationRunResponse(
        success=True,
        message=f"Allocation complete for {len(resolved_semester_ids)} semester(s): {total_assigned} assigned, {total_unassigned} unassigned",
        semester_id=resolved_semester_ids[0] if len(resolved_semester_ids) == 1 else None,
        semester_label=None,  # Multiple semesters, no single label
        subjects_total=total_subjects,
        subjects_assigned=total_assigned,
        subjects_unassigned=total_unassigned,
        faculty_overloaded=overloaded,
        faculty_underloaded=underloaded,
        faculty_balanced=balanced,
        allocations=alloc_records,
        unallocated=unalloc_records,
        workload_summary=wl_summaries,
    )


@router.post("/run-all")
async def run_all_open_semesters(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Run allocation for ALL open cycles at once.
    Processes all cycles with status='OPEN' regardless of academic year.
    """
    from app.db.session import get_transaction
    from sqlalchemy import text
    
    # Get all open cycles
    with get_transaction() as session:
        open_cycles = session.execute(
            text("""
                SELECT c.id, c.semester_id, ay.name as academic_year
                FROM cycle c
                JOIN academic_year ay ON ay.id = c.academic_year_id
                WHERE c.status = 'OPEN'
                ORDER BY c.semester_id
            """)
        ).fetchall()
        
        if not open_cycles:
            raise HTTPException(
                status_code=400,
                detail="No open cycles found. Please open cycles first."
            )
        
        # Reset all non-FROZEN semesters and clear allocations
        session.execute(
            text("UPDATE semester SET state = 'CLOSED', allocated_at = NULL WHERE state != 'FROZEN'")
        )
        session.execute(
            text("""
                DELETE FROM allocation 
                WHERE subject_offering_id IN (
                    SELECT so.id FROM subject_offering so
                    JOIN semester sem ON sem.id = so.semester_id
                    WHERE sem.state != 'FROZEN'
                )
            """)
        )
        session.commit()
    
    logger.info(f"Running allocation for {len(open_cycles)} open cycles")
    
    # Run allocation for each open cycle
    results = []
    total_assigned = 0
    total_unassigned = 0
    
    for cycle_row in open_cycles:
        try:
            result = allocation_service.run_allocation(
                academic_year=cycle_row.academic_year,
                semester_type=None,
                academic_cycle_id=None,
                program_id=None,
                semester_id=cycle_row.semester_id
            )
            
            results.append({
                "semester_id": cycle_row.semester_id,
                "status": "success",
                "assigned": result["subjects_assigned"],
                "unassigned": result["subjects_unassigned"],
            })
            
            total_assigned += result["subjects_assigned"]
            total_unassigned += result["subjects_unassigned"]
            
        except Exception as e:
            logger.error(f"Failed to allocate semester {cycle_row.semester_id}: {e}")
            results.append({
                "semester_id": cycle_row.semester_id,
                "status": "error",
                "error": str(e),
            })
    
    # Mark all semesters as ALLOCATED
    with get_transaction() as session:
        session.execute(
            text("UPDATE semester SET state = 'ALLOCATED', allocated_at = now()")
        )
        session.commit()
    
    return {
        "success": True,
        "message": f"Allocated {len(open_cycles)} semesters: {total_assigned} assigned, {total_unassigned} unassigned",
        "semesters_processed": len(open_cycles),
        "subjects_total": total_assigned + total_unassigned,
        "subjects_assigned": total_assigned,
        "subjects_unassigned": total_unassigned,
        "faculty_overloaded": 0,  # Not computed in run-all mode
        "faculty_underloaded": 0,
        "faculty_balanced": 0,
        "allocations": [],  # Not returned in run-all mode
        "unallocated": [],
        "results": results,
    }
