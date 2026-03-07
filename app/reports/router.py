"""
FastAPI router for report endpoints.
Spec reference: final_system_specification.md (Reporting System)

Endpoints:
  GET /api/reports/faculty-workload       Per-faculty workload report
  GET /api/reports/subject-summary        Subject-wise allocation report
  GET /api/reports/department-summary     Aggregate department statistics
  GET /api/reports/export/workload.xlsx   Excel download (3 sheets)
  GET /api/reports/export/workload.pdf    PDF download
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import io
import logging

from app.auth.dependencies import get_current_coordinator_id
from app.reports.schemas import (
    FacultyWorkloadResponse, FacultyWorkloadRecord, SubjectAssignment,
    SubjectSummaryResponse, SubjectSummaryRecord,
    DepartmentSummaryResponse,
)
from app.reports import service as report_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/faculty-workload", response_model=FacultyWorkloadResponse)
async def faculty_workload(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Per-faculty workload report with assigned subject details."""
    data = report_service.get_faculty_workload()
    for rec in data["records"]:
        rec["subjects_assigned"] = [SubjectAssignment(**s) for s in rec["subjects_assigned"]]
    data["records"] = [FacultyWorkloadRecord(**r) for r in data["records"]]
    return FacultyWorkloadResponse(**data)


@router.get("/subject-summary", response_model=SubjectSummaryResponse)
async def subject_summary(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Subject-wise report showing assigned faculty per offering."""
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


@router.get("/export/workload.xlsx")
async def export_excel(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Download workload report as Excel file (3 sheets)."""
    try:
        excel_bytes = report_service.generate_excel_report()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=workload_report.xlsx"},
    )


@router.get("/export/workload.pdf")
async def export_pdf(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Download workload report as PDF."""
    try:
        pdf_bytes = report_service.generate_pdf_report()
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")

    content_type = "application/pdf"
    # Fallback is plain text
    if pdf_bytes[:4] != b"%PDF":
        content_type = "text/plain"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type=content_type,
        headers={"Content-Disposition": "attachment; filename=workload_report.pdf"},
    )
