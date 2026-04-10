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


# ─── DEBUG Endpoints (public, no auth) ──────────────────────────────────────

@router.get("/export/staff-debug")
async def get_staff_debug():
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


@router.get("/debug-offerings")
async def debug_offerings():
    """
    PUBLIC DEBUG endpoint - Show subject offerings grouped by program and semester.
    No authentication required for debugging.
    """
    from app.db.session import get_transaction
    from sqlalchemy import text
    
    with get_transaction() as session:
        # Get open cycles
        open_cycles = session.execute(
            text("SELECT id, semester_id, status, academic_year_id FROM cycle WHERE status='OPEN'")
        ).fetchall()
        
        # Get offerings grouped by program and semester
        rows = session.execute(
            text("""
                SELECT p.name as prog, sem.label as sem, COUNT(*) as cnt, 
                       bool_and(so.is_active) as all_active,
                       array_agg(DISTINCT so.academic_year_id) as year_ids
                FROM subject_offering so
                JOIN program p ON p.id = so.program_id
                JOIN semester sem ON sem.id = so.semester_id
                GROUP BY p.name, sem.label
                ORDER BY p.name, sem.label
            """)
        ).fetchall()
        
        return {
            "open_cycles": [{"id": r[0], "semester_id": r[1], "status": r[2], "academic_year_id": r[3]} for r in open_cycles],
            "offerings_by_program_semester": [
                {
                    "program": r[0],
                    "semester": r[1],
                    "count": r[2],
                    "all_active": r[3],
                    "academic_year_ids": r[4]
                }
                for r in rows
            ]
        }


# ─── Admin Seeding Endpoints (public, no auth - for one-time setup) ──────────

@router.get("/admin/db-state")
async def db_state():
    """PUBLIC DEBUG - Show current database state for MCA seeding."""
    from app.db.session import get_transaction
    from sqlalchemy import text
    
    result = {}
    with get_transaction() as session:
        result["programs"] = [dict(r._mapping) for r in session.execute(
            text("SELECT id, name FROM program ORDER BY name")
        ).fetchall()]
        
        result["semesters"] = [dict(r._mapping) for r in session.execute(
            text("SELECT id, label FROM semester ORDER BY id")
        ).fetchall()]
        
        result["open_cycles"] = [dict(r._mapping) for r in session.execute(
            text("SELECT id, semester_id, status FROM cycle WHERE status='OPEN'")
        ).fetchall()]
        
        result["mca_offerings_by_sem"] = [dict(r._mapping) for r in session.execute(
            text("""
                SELECT p.name as prog, sem.label as sem_label, sem.id as sem_id, COUNT(*) as cnt
                FROM subject_offering so
                JOIN program p ON p.id = so.program_id
                JOIN semester sem ON sem.id = so.semester_id
                WHERE p.name ILIKE '%MCA%'
                GROUP BY p.name, sem.label, sem.id
                ORDER BY sem.id
            """)
        ).fetchall()]
        
        result["sections"] = [dict(r._mapping) for r in session.execute(
            text("SELECT id, label FROM section ORDER BY id")
        ).fetchall()]
    
    return result


@router.post("/admin/fix-duplicate-programs")
async def fix_duplicate_programs():
    """PUBLIC - Fix duplicate program names (case-insensitive consolidation)."""
    from app.db.session import get_transaction
    from sqlalchemy import text
    
    results = {"merged": [], "remaining": []}
    
    try:
        with get_transaction() as session:
            dups = session.execute(
                text("""
                    SELECT UPPER(REPLACE(name,' ','')) as key,
                           array_agg(id ORDER BY id) as ids,
                           array_agg(name ORDER BY id) as names
                    FROM program
                    GROUP BY UPPER(REPLACE(name,' ',''))
                    HAVING COUNT(*) > 1
                """)
            ).fetchall()
            
            for dup in dups:
                ids = dup[1]
                names = dup[2]
                keep_id = ids[0]
                
                for i, rid in enumerate(ids[1:], 1):
                    session.execute(
                        text("UPDATE subject_offering SET program_id=:k WHERE program_id=:r"),
                        {"k": keep_id, "r": rid}
                    )
                    session.execute(
                        text("DELETE FROM program WHERE id=:r"),
                        {"r": rid}
                    )
                    results["merged"].append(
                        f"Merged '{names[i]}' (id={rid}) into '{names[0]}' (id={keep_id})"
                    )
            
            session.commit()
            
            remaining = session.execute(
                text("SELECT id, name FROM program ORDER BY name")
            ).fetchall()
            results["remaining"] = [dict(r._mapping) for r in remaining]
            results["status"] = "SUCCESS"
            
    except Exception as e:
        results["status"] = "FAILED"
        results["error"] = str(e)
    
    return results


@router.post("/admin/seed-mca-odd")
async def seed_mca_odd_semesters():
    """PUBLIC - One-time endpoint to seed MCA Sem I and III subject offerings."""
    from app.db.session import get_transaction
    from sqlalchemy import text
    
    results = {
        "subjects_created": [],
        "subjects_existed": [],
        "offerings_created": 0,
        "offerings_existed": 0,
        "programs_found": [],
        "errors": []
    }
    
    try:
        with get_transaction() as session:
            # Get MCA program ids
            mca_progs = session.execute(
                text("SELECT id, name FROM program WHERE name ILIKE '%MCA%'")
            ).fetchall()
            results["programs_found"] = [dict(r._mapping) for r in mca_progs]
            mca_prog_ids = [r[0] for r in mca_progs]
            
            if not mca_prog_ids:
                results["errors"].append("No MCA programs found in program table")
                return results
            
            # Get semester IDs - try label column only
            semesters = session.execute(
                text("SELECT id, label FROM semester ORDER BY id")
            ).fetchall()
            sem_map = {}
            
            for s in semesters:
                r = dict(s._mapping)
                val = r.get('label', '')
                v = str(val).strip().upper()
                if v in ('I', 'SEMESTER I', 'SEM I', '1'):
                    sem_map[1] = r['id']
                elif v in ('II', 'SEMESTER II', 'SEM II', '2'):
                    sem_map[2] = r['id']
                elif v in ('III', 'SEMESTER III', 'SEM III', '3'):
                    sem_map[3] = r['id']
            
            results["semester_map"] = sem_map
            
            if 1 not in sem_map or 3 not in sem_map:
                results["errors"].append(f"Could not find sem I or III ids. Found: {sem_map}")
                results["all_semesters"] = [dict(s._mapping) for s in semesters]
                return results
            
            # Get sections and academic year
            sections = session.execute(
                text("SELECT id, label FROM section ORDER BY id")
            ).fetchall()
            section_ids = [r[0] for r in sections]
            
            academic_year_id = session.execute(
                text("SELECT id FROM academic_year ORDER BY id DESC LIMIT 1")
            ).scalar()
            
            results["section_ids"] = section_ids
            results["academic_year_id"] = academic_year_id
            
            # Subjects to seed
            sem1_subjects = [
                ("CMA42001", "Statistics for Computer Science", "BS", 3, 1, 0, 4, 4, 2022),
                ("CCM42001", "Basics of Accounting", "BS", 1, 1, 0, 2, 2, 2022),
                ("CCA42001", "Object Oriented Programming", "PC", 3, 0, 2, 4, 5, 2022),
                ("CCA42002", "Data Communication and Networking", "PC", 2, 1, 0, 3, 3, 2022),
                ("CCA42003", "Software Engineering Concepts", "PC", 3, 0, 0, 3, 3, 2022),
                ("CCA42004", "Advanced Data Structures and Algorithms", "PC", 3, 0, 2, 4, 5, 2022),
                ("CCA42005", "Python Programming", "PC", 2, 0, 2, 3, 4, 2022),
            ]
            
            sem3_subjects = [
                ("CCA42010", "Software Testing and Quality Assurance", "PC", 2, 1, 2, 4, 5, 2022),
                ("CCA42011", "Cryptography and Network Security", "PC", 3, 0, 2, 4, 5, 2022),
                ("CEL42001", "Communication Skills and Professional Development", "BS", 2, 0, 2, 3, 3, 2022),
            ]
            
            def upsert_subject(code, name, cat, l, t, p, credits, tch, cy):
                existing = session.execute(
                    text("SELECT id FROM subject WHERE code=:code"),
                    {"code": code}
                ).scalar()
                
                if existing:
                    results["subjects_existed"].append(code)
                    return existing
                
                row = session.execute(
                    text("""
                        INSERT INTO subject(code, name, course_category, l, t, p, credits, tch, curriculum_year)
                        VALUES(:code, :name, :cat, :l, :t, :p, :credits, :tch, :cy)
                        RETURNING id
                    """),
                    dict(code=code, name=name, cat=cat, l=l, t=t, p=p, credits=credits, tch=tch, cy=cy)
                ).scalar()
                
                results["subjects_created"].append(code)
                return row
            
            def upsert_offering(sub_id, prog_id, sem_id, sec_id, ay_id):
                existing = session.execute(
                    text("""
                        SELECT id FROM subject_offering
                        WHERE subject_id=:s AND program_id=:p AND semester_id=:sem AND section_id=:sec
                    """),
                    dict(s=sub_id, p=prog_id, sem=sem_id, sec=sec_id)
                ).scalar()
                
                if existing:
                    results["offerings_existed"] += 1
                    return
                
                session.execute(
                    text("""
                        INSERT INTO subject_offering(subject_id, program_id, semester_id, section_id, shift, is_active, academic_year_id)
                        VALUES(:s, :p, :sem, :sec, 1, true, :ay)
                    """),
                    dict(s=sub_id, p=prog_id, sem=sem_id, sec=sec_id, ay=ay_id)
                )
                results["offerings_created"] += 1
            
            # Seed Sem I
            for subj in sem1_subjects:
                sid = upsert_subject(*subj)
                for prog_id in mca_prog_ids:
                    for sec_id in section_ids:
                        upsert_offering(sid, prog_id, sem_map[1], sec_id, academic_year_id)
            
            # Seed Sem III
            for subj in sem3_subjects:
                sid = upsert_subject(*subj)
                for prog_id in mca_prog_ids:
                    for sec_id in section_ids:
                        upsert_offering(sid, prog_id, sem_map[3], sec_id, academic_year_id)
            
            session.commit()
            results["status"] = "SUCCESS"
            
    except Exception as e:
        results["errors"].append(str(e))
        results["status"] = "FAILED"
    
    return results


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


# ─── Debug Endpoints (Temporary) ──────────────────────────────────────────────

@router.get("/export/debug-test")
async def debug_export_test():
    """Temporary debug endpoint - returns JSON with traceback instead of file"""
    import traceback as tb_module
    try:
        snapshot, academic_year, semester_id = _get_snapshot_or_live_data()
        
        from app.reports.snapshot_service import _build_snapshot_data
        from app.db.session import get_transaction
        with get_transaction() as session:
            snapshot_data = _build_snapshot_data(session, academic_year, semester_id)
        
        return {
            "status": "ok",
            "academic_year": academic_year,
            "semester_id": semester_id,
            "snapshot_data_count": len(snapshot_data),
            "first_row_keys": list(snapshot_data[0].keys()) if snapshot_data else [],
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": tb_module.format_exc()
        }


@router.get("/export/debug-pdf")
async def debug_pdf_test():
    """Temporary debug endpoint - tests PDF generation, returns JSON"""
    import traceback as tb_module
    try:
        snapshot, academic_year, semester_id = _get_snapshot_or_live_data()
        
        from app.reports.snapshot_service import _build_snapshot_data
        from app.reports.pdf_generator import generate_pdf_from_snapshot
        from app.db.session import get_transaction
        with get_transaction() as session:
            snapshot_data = _build_snapshot_data(session, academic_year, semester_id)
        
        pdf_bytes = generate_pdf_from_snapshot(
            snapshot_data=snapshot_data,
            academic_year=academic_year,
            semester_id=semester_id,
        )
        
        return {"status": "ok", "pdf_size_bytes": len(pdf_bytes)}
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": tb_module.format_exc()
        }


@router.get("/export/debug-excel")
async def debug_excel_test():
    """Temporary debug endpoint - tests master workload Excel generation"""
    import traceback as tb_module
    try:
        snapshot, academic_year, semester_id = _get_snapshot_or_live_data()
        
        from app.reports.snapshot_service import _build_snapshot_data
        from app.reports.master_workload_excel import generate_from_snapshot
        from app.db.session import get_transaction
        with get_transaction() as session:
            snapshot_data = _build_snapshot_data(session, academic_year, semester_id)
        
        excel_bytes = generate_from_snapshot(
            snapshot_data=snapshot_data,
            academic_year=academic_year,
            semester_id=semester_id,
        )
        
        return {"status": "ok", "excel_size_bytes": len(excel_bytes)}
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": tb_module.format_exc()
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
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Master workload Excel generation failed: {e}\n{tb}")
        raise HTTPException(status_code=500, detail=f"Excel error: {str(e)}\n\nTraceback:\n{tb}")

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
        import traceback
        tb = traceback.format_exc()
        logger.error(f"PDF generation failed: {e}\n{tb}")
        raise HTTPException(status_code=500, detail=f"PDF error: {str(e)}\n\nTraceback:\n{tb}")

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Master_Workload_{academic_year}_Sem{semester_id}.pdf"'},
    )
