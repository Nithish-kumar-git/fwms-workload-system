"""
FastAPI router for report endpoints.

Endpoints:
  GET  /api/reports/faculty-workload           Per-faculty workload report
  GET  /api/reports/subject-summary            Subject-wise allocation report
  GET  /api/reports/department-summary         Aggregate department statistics
  GET  /api/reports/pipeline-status            Pipeline stage check
  POST /api/reports/approve-workload           HOD freezes workload → snapshot
  GET  /api/reports/export/workload.xlsx       Excel download (3 sheets)
  GET  /api/reports/export/master-workload.xlsx  Master workload sheet (from snapshot)
  GET  /api/reports/export/workload.pdf        PDF download (from snapshot)
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import io
import logging

from app.auth.dependencies import (
    get_current_coordinator_id,
    get_current_coordinator,
    get_current_hod,
    get_current_hod_id,
    get_current_staff_id,
)
from app.reports.schemas import (
    FacultyWorkloadResponse, FacultyWorkloadRecord, SubjectAssignment,
    SubjectSummaryResponse, SubjectSummaryRecord,
    DepartmentSummaryResponse,
)
from app.reports import service as report_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


# ─── Live Report Endpoints (view only, not for export) ───────────────────────

@router.get("/faculty-workload", response_model=FacultyWorkloadResponse)
async def faculty_workload(
    staff_id: int = Depends(get_current_staff_id),
):
    """Per-faculty workload report with assigned subject details. Accessible by all authenticated users."""
    data = report_service.get_faculty_workload()
    for rec in data["records"]:
        rec["subjects_assigned"] = [SubjectAssignment(**s) for s in rec["subjects_assigned"]]
    data["records"] = [FacultyWorkloadRecord(**r) for r in data["records"]]
    return FacultyWorkloadResponse(**data)


@router.get("/subject-summary", response_model=SubjectSummaryResponse)
async def subject_summary(
    staff_id: int = Depends(get_current_staff_id),
):
    """Subject-wise report showing assigned faculty per offering. Accessible by all authenticated users."""
    data = report_service.get_subject_summary()
    data["records"] = [SubjectSummaryRecord(**r) for r in data["records"]]
    return SubjectSummaryResponse(**data)


@router.get("/department-summary", response_model=DepartmentSummaryResponse)
async def department_summary(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Aggregate department workload statistics."""
    data = report_service.get_department_summary()
    return DepartmentSummaryResponse(**data)


# ─── Pipeline Status ─────────────────────────────────────────────────────────

@router.get("/pipeline-status")
async def pipeline_status(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Returns the 3-stage pipeline status:
    - preferences_submitted
    - allocation_complete
    - hod_approved (snapshot exists)
    """
    from app.reports.snapshot_service import get_pipeline_status
    return get_pipeline_status()


# ─── HOD Approval ────────────────────────────────────────────────────────────

@router.post("/approve-workload")
async def approve_workload(
    hod_id: int = Depends(get_current_hod_id),
):
    """
    HOD approves and freezes the workload.
    Creates an immutable snapshot and locks the academic cycle.
    """
    from app.reports.snapshot_service import create_snapshot
    try:
        result = create_snapshot(approved_by=hod_id)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": True,
        "message": "Workload approved and frozen.",
        **result,
    }


# ─── Snapshot-Enforced Exports ───────────────────────────────────────────────

def _get_snapshot_or_live_data() -> tuple[dict | None, str, int]:
    """
    Get snapshot if it exists (FROZEN state), otherwise prepare for live data (ALLOCATED or OPEN state).
    Returns (snapshot_or_none, academic_year, semester_id).
    Raises HTTP 400 if no semesters are ALLOCATED, OPEN, or FROZEN.
    """
    from app.reports.snapshot_service import get_snapshot
    from app.db.session import get_transaction
    from sqlalchemy import text
    
    # Try to get snapshot first (for FROZEN cycles)
    with get_transaction() as session:
        # Check for any cycle that's OPEN, ALLOCATED, or FROZEN
        cycle_row = session.execute(
            text("""
                SELECT c.id, ay.name, c.semester_id, c.status
                FROM cycle c
                JOIN academic_year ay ON c.academic_year_id = ay.id
                WHERE c.status IN ('OPEN', 'ALLOCATED', 'FROZEN')
                ORDER BY 
                    CASE c.status
                        WHEN 'FROZEN' THEN 1
                        WHEN 'ALLOCATED' THEN 2
                        WHEN 'OPEN' THEN 3
                    END
                LIMIT 1
            """)
        ).fetchone()
        
        if not cycle_row:
            raise HTTPException(
                status_code=400,
                detail="No active academic cycle found. Cycle must be OPEN, ALLOCATED, or FROZEN."
            )
        
        cycle_id, academic_year, semester_id, status = cycle_row
        
        # If FROZEN, try to get snapshot
        if status == 'FROZEN':
            try:
                snapshot = get_snapshot()
                return snapshot, snapshot["academic_year"], snapshot.get("semester_id", semester_id)
            except RuntimeError:
                # No snapshot even though FROZEN - fall through to live data
                pass
        
        # For OPEN or ALLOCATED (or FROZEN without snapshot), use live data
        # Check if there's any allocation data
        allocated_count = session.execute(
            text("""
                SELECT COUNT(*)
                FROM allocation a
                JOIN subject_offering so ON so.id = a.subject_offering_id
                WHERE so.academic_year = :year
                  AND so.semester_id = :sem_id
            """),
            {"year": academic_year, "sem_id": semester_id}
        ).scalar()
        
        if allocated_count == 0 and status != 'OPEN':
            raise HTTPException(
                status_code=400,
                detail="Cannot export: No allocation data found. Run allocation first."
            )
        
        return None, academic_year, semester_id


@router.get("/export/workload.xlsx")
async def export_excel(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Download workload report as Excel file (3 sheets). Works when semester is ALLOCATED or FROZEN."""
    snapshot, academic_year, semester_id = _get_snapshot_or_live_data()
    
    try:
        excel_bytes = report_service.generate_excel_report(academic_year, semester_id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="workload_report_Sem{semester_id}.xlsx"'},
    )


@router.get("/export/master-workload.xlsx")
async def export_master_workload(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Download the institutional Master Workload Excel sheet.
    Works when semester is ALLOCATED (uses live data) or FROZEN (uses snapshot).
    """
    snapshot, academic_year, semester_id = _get_snapshot_or_live_data()

    from app.reports.master_workload_excel import generate_from_snapshot
    
    if snapshot:
        # Use snapshot data (FROZEN state)
        snapshot_data = snapshot["snapshot_data"]
    else:
        # Use live data (ALLOCATED state)
        from app.reports.snapshot_service import _build_snapshot_data
        from app.db.session import get_transaction
        with get_transaction() as session:
            snapshot_data = _build_snapshot_data(session, academic_year, semester_id)
    
    try:
        excel_bytes = generate_from_snapshot(
            snapshot_data=snapshot_data,
            academic_year=academic_year,
            semester_id=semester_id,
        )
    except Exception as e:
        logger.error(f"Master workload Excel generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Excel generation error: {str(e)}")

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="Master_Workload_{academic_year}_Sem{semester_id}.xlsx"'},
    )


@router.get("/export/workload.pdf")
async def export_pdf(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Download workload report as PDF.
    Works when semester is ALLOCATED (uses live data) or FROZEN (uses snapshot).
    """
    snapshot, academic_year, semester_id = _get_snapshot_or_live_data()

    from app.reports.pdf_generator import generate_pdf_from_snapshot
    
    if snapshot:
        # Use snapshot data (FROZEN state)
        snapshot_data = snapshot["snapshot_data"]
    else:
        # Use live data (ALLOCATED state)
        from app.reports.snapshot_service import _build_snapshot_data
        from app.db.session import get_transaction
        with get_transaction() as session:
            snapshot_data = _build_snapshot_data(session, academic_year, semester_id)
    
    try:
        pdf_bytes = generate_pdf_from_snapshot(
            snapshot_data=snapshot_data,
            academic_year=academic_year,
            semester_id=semester_id,
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Master_Workload_{academic_year}_Sem{semester_id}.pdf"'},
    )
