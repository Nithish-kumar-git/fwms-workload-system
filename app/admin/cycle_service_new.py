"""
Service layer for semester-specific cycle management.
NEW ARCHITECTURE: Cycles are per (academic_year + semester), not ODD/EVEN.

IMPORTANT: This service uses the NEW cycle table schema from migration 021:
- cycle.academic_year_id (FK to academic_year.id)
- cycle.semester_id (FK to semester.id)
- cycle.status ('OPEN', 'CLOSED', 'ALLOCATED', 'FROZEN')
"""

import logging
from sqlalchemy import text
from app.db.session import get_transaction

logger = logging.getLogger(__name__)


def create_cycle(academic_year: str, semester_id: int, start_date: str | None = None, end_date: str | None = None) -> dict:
    """
    Create a new semester-specific cycle.
    
    Args:
        academic_year: e.g. "2025-2026"
        semester_id: 1-6 (I-VI)
        start_date: Optional start date
        end_date: Optional end date
    
    Returns:
        {"success": bool, "message": str, "cycle_id": int | None}
    """
    with get_transaction() as session:
        # Ensure academic_year exists in academic_year table
        year_row = session.execute(
            text("SELECT id FROM academic_year WHERE name = :name"),
            {"name": academic_year}
        ).fetchone()
        
        if not year_row:
            # Create academic_year if it doesn't exist
            session.execute(
                text("INSERT INTO academic_year (name, start_date, end_date) VALUES (:name, :start_date, :end_date)"),
                {"name": academic_year, "start_date": start_date, "end_date": end_date}
            )
            year_row = session.execute(
                text("SELECT id FROM academic_year WHERE name = :name"),
                {"name": academic_year}
            ).fetchone()
        
        academic_year_id = year_row[0]
        
        # Check if cycle already exists
        existing = session.execute(
            text("SELECT id FROM cycle WHERE academic_year_id = :year_id AND semester_id = :sem_id"),
            {"year_id": academic_year_id, "sem_id": semester_id}
        ).fetchone()
        
        if existing:
            return {
                "success": False,
                "message": f"Cycle for {academic_year} Semester {semester_id} already exists",
                "cycle_id": None
            }
        
        # Create new cycle with status='CLOSED'
        result = session.execute(
            text("""
                INSERT INTO cycle (academic_year_id, semester_id, status)
                VALUES (:year_id, :sem_id, 'CLOSED')
                RETURNING id
            """),
            {"year_id": academic_year_id, "sem_id": semester_id}
        )
        
        cycle_id = result.fetchone()[0]
        session.commit()
        
        logger.info(f"Created cycle {cycle_id} for {academic_year} Semester {semester_id}")
        
        return {
            "success": True,
            "message": f"Cycle created for {academic_year} Semester {semester_id}",
            "cycle_id": cycle_id
        }


def activate_cycle(cycle_id: int) -> dict:
    """
    Activate a cycle (set status='OPEN').
    Only one cycle can be OPEN at a time.
    
    Returns:
        {"success": bool, "message": str}
    """
    with get_transaction() as session:
        # Check if cycle exists
        cycle = session.execute(
            text("SELECT id, status FROM cycle WHERE id = :id"),
            {"id": cycle_id}
        ).fetchone()
        
        if not cycle:
            return {"success": False, "message": "Cycle not found"}
        
        if cycle[1] == 'FROZEN':
            return {"success": False, "message": "Cannot activate a frozen cycle"}
        
        # Close all other OPEN cycles
        session.execute(
            text("UPDATE cycle SET status = 'CLOSED', closed_at = NOW() WHERE status = 'OPEN'")
        )
        
        # Open this cycle
        session.execute(
            text("UPDATE cycle SET status = 'OPEN', opened_at = NOW() WHERE id = :id"),
            {"id": cycle_id}
        )
        
        session.commit()
        
        logger.info(f"Activated cycle {cycle_id}")
        
        return {"success": True, "message": "Cycle activated"}


def list_cycles() -> list[dict]:
    """
    List all cycles with their academic year and semester details.
    Joins with academic_year and semester tables.
    
    Returns:
        List of cycle dictionaries
    """
    with get_transaction() as session:
        rows = session.execute(
            text("""
                SELECT 
                    c.id,
                    ay.name as academic_year,
                    c.semester_id,
                    s.label as semester_name,
                    c.status,
                    c.opened_at,
                    c.closed_at,
                    c.allocated_at,
                    c.frozen_at,
                    c.created_at
                FROM cycle c
                JOIN academic_year ay ON c.academic_year_id = ay.id
                JOIN semester s ON c.semester_id = s.id
                ORDER BY c.created_at DESC
            """)
        ).fetchall()
        
        return [
            {
                "id": row[0],
                "academic_year": row[1],
                "semester_id": row[2],
                "semester_name": row[3],
                "status": row[4],
                "is_active": row[4] == 'OPEN',
                "opened_at": row[5].isoformat() if row[5] else None,
                "closed_at": row[6].isoformat() if row[6] else None,
                "allocated_at": row[7].isoformat() if row[7] else None,
                "frozen_at": row[8].isoformat() if row[8] else None,
                "created_at": row[9].isoformat() if row[9] else None,
                "allocation_count": None,  # Not included in list_cycles, only in get_cycle_history
            }
            for row in rows
        ]


def get_active_cycle() -> dict | None:
    """
    Get the currently active (OPEN) cycle.
    Joins with academic_year and semester tables.
    
    Returns:
        Cycle dictionary with id, academic_year, semester_id, semester_name, status, is_active
        or None if no active cycle
    """
    with get_transaction() as session:
        row = session.execute(
            text("""
                SELECT 
                    c.id,
                    ay.name as academic_year,
                    c.semester_id,
                    s.label as semester_name,
                    c.status,
                    c.opened_at,
                    c.closed_at,
                    c.allocated_at,
                    c.frozen_at,
                    c.created_at
                FROM cycle c
                JOIN academic_year ay ON c.academic_year_id = ay.id
                JOIN semester s ON c.semester_id = s.id
                WHERE c.status = 'OPEN'
                LIMIT 1
            """)
        ).fetchone()
        
        if not row:
            return None
        
        return {
            "id": row[0],
            "academic_year": row[1],
            "semester_id": row[2],
            "semester_name": row[3],
            "status": row[4],
            "is_active": True,
            "opened_at": row[5].isoformat() if row[5] else None,
            "closed_at": row[6].isoformat() if row[6] else None,
            "allocated_at": row[7].isoformat() if row[7] else None,
            "frozen_at": row[8].isoformat() if row[8] else None,
            "created_at": row[9].isoformat() if row[9] else None,
            "allocation_count": None,  # Not included for active cycle
        }



def archive_cycle(cycle_id: int) -> dict:
    """
    Archive a cycle by setting its status to FROZEN.
    This marks the cycle as finalized and prevents further modifications.
    
    Args:
        cycle_id: ID of the cycle to archive
    
    Returns:
        {"success": bool, "message": str, "cycle_id": int | None}
    """
    with get_transaction() as session:
        # Check if cycle exists
        cycle = session.execute(
            text("SELECT id, status FROM cycle WHERE id = :id"),
            {"id": cycle_id}
        ).fetchone()
        
        if not cycle:
            return {"success": False, "message": "Cycle not found", "cycle_id": None}
        
        if cycle[1] == 'FROZEN':
            return {"success": False, "message": "Cycle is already frozen", "cycle_id": cycle_id}
        
        # Set status to FROZEN
        session.execute(
            text("UPDATE cycle SET status = 'FROZEN', frozen_at = NOW() WHERE id = :id"),
            {"id": cycle_id}
        )
        
        session.commit()
        
        logger.info(f"Archived cycle {cycle_id} (status set to FROZEN)")
        
        return {
            "success": True,
            "message": "Cycle archived successfully",
            "cycle_id": cycle_id
        }


def get_cycle_history() -> list[dict]:
    """
    Get all archived cycles (status FROZEN or ALLOCATED).
    Shows historical cycles with allocation counts.
    
    Returns:
        List of cycle dictionaries with allocation counts
    """
    with get_transaction() as session:
        rows = session.execute(
            text("""
                SELECT 
                    c.id,
                    ay.name as academic_year,
                    c.semester_id,
                    s.label as semester_name,
                    c.status,
                    c.opened_at,
                    c.closed_at,
                    c.allocated_at,
                    c.frozen_at,
                    c.created_at,
                    COUNT(a.id) as allocation_count
                FROM cycle c
                JOIN academic_year ay ON c.academic_year_id = ay.id
                JOIN semester s ON c.semester_id = s.id
                LEFT JOIN allocation a ON a.cycle_id = c.id
                WHERE c.status IN ('FROZEN', 'ALLOCATED')
                GROUP BY c.id, ay.name, c.semester_id, s.label, c.status, 
                         c.opened_at, c.closed_at, c.allocated_at, c.frozen_at, c.created_at
                ORDER BY c.created_at DESC
            """)
        ).fetchall()
        
        return [
            {
                "id": row[0],
                "academic_year": row[1],
                "semester_id": row[2],
                "semester_name": row[3],
                "status": row[4],
                "is_active": False,  # Archived cycles are never active
                "opened_at": row[5].isoformat() if row[5] else None,
                "closed_at": row[6].isoformat() if row[6] else None,
                "allocated_at": row[7].isoformat() if row[7] else None,
                "frozen_at": row[8].isoformat() if row[8] else None,
                "created_at": row[9].isoformat() if row[9] else None,
                "allocation_count": row[10],
            }
            for row in rows
        ]


def create_new_semester_cycle(academic_year: str, semester_id: int) -> dict:
    """
    Create a new OPEN cycle for a given semester.
    Before creating, sets any existing OPEN cycle for the same semester to CLOSED.
    This allows starting fresh for a new academic year.
    
    Args:
        academic_year: e.g. "2025-2026"
        semester_id: 1-6 (I-VI)
    
    Returns:
        {"success": bool, "message": str, "cycle_id": int | None}
    """
    with get_transaction() as session:
        # Ensure academic_year exists in academic_year table
        year_row = session.execute(
            text("SELECT id FROM academic_year WHERE name = :name"),
            {"name": academic_year}
        ).fetchone()
        
        if not year_row:
            # Create academic_year if it doesn't exist
            session.execute(
                text("INSERT INTO academic_year (name) VALUES (:name)"),
                {"name": academic_year}
            )
            year_row = session.execute(
                text("SELECT id FROM academic_year WHERE name = :name"),
                {"name": academic_year}
            ).fetchone()
        
        academic_year_id = year_row[0]
        
        # Close any existing OPEN cycles for this semester
        session.execute(
            text("""
                UPDATE cycle 
                SET status = 'CLOSED', closed_at = NOW() 
                WHERE semester_id = :sem_id AND status = 'OPEN'
            """),
            {"sem_id": semester_id}
        )
        
        # Check if cycle already exists for this academic year + semester
        existing = session.execute(
            text("SELECT id FROM cycle WHERE academic_year_id = :year_id AND semester_id = :sem_id"),
            {"year_id": academic_year_id, "sem_id": semester_id}
        ).fetchone()
        
        if existing:
            return {
                "success": False,
                "message": f"Cycle for {academic_year} Semester {semester_id} already exists",
                "cycle_id": None
            }
        
        # Create new cycle with status='OPEN'
        result = session.execute(
            text("""
                INSERT INTO cycle (academic_year_id, semester_id, status, opened_at)
                VALUES (:year_id, :sem_id, 'OPEN', NOW())
                RETURNING id
            """),
            {"year_id": academic_year_id, "sem_id": semester_id}
        )
        
        cycle_id = result.fetchone()[0]
        session.commit()
        
        logger.info(f"Created new semester cycle {cycle_id} for {academic_year} Semester {semester_id} (status=OPEN)")
        
        return {
            "success": True,
            "message": f"New semester cycle created for {academic_year} Semester {semester_id}",
            "cycle_id": cycle_id
        }
