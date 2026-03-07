"""
Academic cycle service — manages multi-year/semester cycle lifecycle.

Functions:
  - get_active_cycle: returns the current active cycle or None
  - get_active_cycle_id: returns the active cycle id (raises if none)
  - create_cycle: create a new academic cycle
  - activate_cycle: set a cycle as active (deactivates all others)
  - list_cycles: return all cycles
"""

from sqlalchemy import text
from app.db.session import get_transaction
import logging

logger = logging.getLogger(__name__)


def get_active_cycle() -> dict | None:
    """Return the currently active academic cycle, or None."""
    with get_transaction() as session:
        row = session.execute(
            text("""
                SELECT id, academic_year, semester_type, start_date, end_date, is_active, created_at
                FROM academic_cycle
                WHERE is_active = true
                LIMIT 1
            """)
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "academic_year": row[1],
        "semester_type": row[2],
        "start_date": str(row[3]) if row[3] else None,
        "end_date": str(row[4]) if row[4] else None,
        "is_active": row[5],
        "created_at": str(row[6]),
    }


def get_active_cycle_id() -> int:
    """Return the active cycle ID. Raises ValueError if none exists."""
    cycle = get_active_cycle()
    if cycle is None:
        raise ValueError("No active academic cycle. Create and activate one first.")
    return cycle["id"]


def create_cycle(
    academic_year: str,
    semester_type: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Create a new academic cycle."""
    with get_transaction() as session:
        try:
            result = session.execute(
                text("""
                    INSERT INTO academic_cycle (academic_year, semester_type, start_date, end_date, is_active)
                    VALUES (:year, :sem, :start, :end, false)
                    RETURNING id
                """),
                {
                    "year": academic_year,
                    "sem": semester_type,
                    "start": start_date,
                    "end": end_date,
                },
            )
            cycle_id = result.scalar()
            session.commit()
        except Exception as e:
            if "uq_academic_cycle" in str(e) or "duplicate" in str(e).lower():
                return {"success": False, "message": f"Cycle {academic_year} {semester_type} already exists"}
            raise

    logger.info(f"Academic cycle created: id={cycle_id}, {academic_year} {semester_type}")
    return {"success": True, "message": "Cycle created", "cycle_id": cycle_id}


def activate_cycle(cycle_id: int) -> dict:
    """Activate a cycle (deactivates all others). Only one active at a time."""
    with get_transaction() as session:
        # Verify cycle exists
        row = session.execute(
            text("SELECT id FROM academic_cycle WHERE id = :id"),
            {"id": cycle_id},
        ).fetchone()

        if row is None:
            return {"success": False, "message": "Cycle not found"}

        # Deactivate all
        session.execute(text("UPDATE academic_cycle SET is_active = false WHERE is_active = true"))

        # Activate target
        session.execute(
            text("UPDATE academic_cycle SET is_active = true WHERE id = :id"),
            {"id": cycle_id},
        )

        session.commit()

    logger.info(f"Academic cycle activated: id={cycle_id}")
    return {"success": True, "message": "Cycle activated"}


def list_cycles() -> list[dict]:
    """Return all academic cycles ordered by creation date desc."""
    with get_transaction() as session:
        rows = session.execute(
            text("""
                SELECT id, academic_year, semester_type, start_date, end_date, is_active, created_at
                FROM academic_cycle
                ORDER BY created_at DESC
            """)
        ).fetchall()

    return [
        {
            "id": r[0],
            "academic_year": r[1],
            "semester_type": r[2],
            "start_date": str(r[3]) if r[3] else None,
            "end_date": str(r[4]) if r[4] else None,
            "is_active": r[5],
            "created_at": str(r[6]),
        }
        for r in rows
    ]
