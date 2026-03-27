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
    TEMP: Auth removed for production diagnosis.
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
            ]
        }
