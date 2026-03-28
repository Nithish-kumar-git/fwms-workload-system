"""
Temporary debug router for production diagnostics.
DELETE THIS FILE after debugging is complete.
"""

from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_staff_id
from app.db.session import get_transaction
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/db-state")
async def debug_db_state():
    """
    Diagnostic endpoint to check database state.
    Returns counts and samples from key tables.
    """
    with get_transaction() as session:
        # Check subject_offering count
        so_count = session.execute(text("SELECT COUNT(*) FROM subject_offering")).scalar()
        
        # Check subject_offering grouped by academic_year and semester_id
        so_grouped = session.execute(text("""
            SELECT academic_year, semester_id, COUNT(*) as count
            FROM subject_offering
            GROUP BY academic_year, semester_id
            ORDER BY academic_year, semester_id
        """)).fetchall()
        
        # Check active cycle
        active_cycle = session.execute(text("""
            SELECT c.id, ay.name as academic_year, c.semester_id, c.status
            FROM cycle c
            JOIN academic_year ay ON ay.id = c.academic_year_id
            WHERE c.status = 'OPEN'
            LIMIT 1
        """)).fetchone()
        
        # Check all cycles
        all_cycles = session.execute(text("""
            SELECT c.id, ay.name as academic_year, c.semester_id, c.status
            FROM cycle c
            JOIN academic_year ay ON ay.id = c.academic_year_id
            ORDER BY c.id
        """)).fetchall()
        
        # Check academic_year table
        academic_years = session.execute(text("""
            SELECT id, name FROM academic_year ORDER BY id
        """)).fetchall()
        
        # Get programs
        programs_result = session.execute(text("""
            SELECT p.id, p.name, p.ug_pg FROM program p ORDER BY p.id
        """)).fetchall()
        
        # Get sections
        sections_result = session.execute(text("""
            SELECT s.id, s.label FROM section s ORDER BY s.id
        """)).fetchall()
        
        # Sample semester 2 offerings
        sample_offerings = session.execute(text("""
            SELECT so.id, p.name as program, sem.label as semester, sec.label as section, sub.code, sub.name
            FROM subject_offering so
            JOIN program p ON p.id = so.program_id
            JOIN semester sem ON sem.id = so.semester_id
            JOIN section sec ON sec.id = so.section_id
            JOIN subject sub ON sub.id = so.subject_id
            WHERE so.semester_id = 2
            ORDER BY p.name, sec.label, sub.code
            LIMIT 30
        """)).fetchall()
        
        # Duplicate sections
        dup_sections = session.execute(text("""
            SELECT label, COUNT(*), array_agg(id ORDER BY id) as ids
            FROM section 
            GROUP BY label 
            HAVING COUNT(*) > 1 
            ORDER BY label
        """)).fetchall()
        
        # Duplicate offerings
        dup_offerings = session.execute(text("""
            SELECT subject_id, program_id, semester_id, section_id, COUNT(*), array_agg(id ORDER BY id)
            FROM subject_offering 
            GROUP BY subject_id, program_id, semester_id, section_id
            HAVING COUNT(*) > 1 
            LIMIT 10
        """)).fetchall()
        
        return {
            "subject_offering_total": so_count,
            "subject_offering_grouped": [
                {"academic_year": r[0], "semester_id": r[1], "count": r[2]}
                for r in so_grouped
            ],
            "active_cycle": {
                "id": active_cycle[0],
                "academic_year": active_cycle[1],
                "semester_id": active_cycle[2],
                "status": active_cycle[3]
            } if active_cycle else None,
            "all_cycles": [
                {"id": r[0], "academic_year": r[1], "semester_id": r[2], "status": r[3]}
                for r in all_cycles
            ],
            "academic_years": [
                {"id": r[0], "name": r[1]}
                for r in academic_years
            ],
            "programs": [
                {"id": r[0], "name": r[1], "ug_pg": r[2]}
                for r in programs_result
            ],
            "sections": [
                {"id": r[0], "label": r[1]}
                for r in sections_result
            ],
            "sample_sem2_offerings": [
                {"id": r[0], "program": r[1], "semester": r[2], "section": r[3], "code": r[4], "name": r[5]}
                for r in sample_offerings
            ],
            "duplicate_sections": [
                {"label": r[0], "count": r[1], "ids": r[2]}
                for r in dup_sections
            ],
            "duplicate_offerings_sample": [
                {"count": r[4], "ids": r[5]}
                for r in dup_offerings
            ]
        }
