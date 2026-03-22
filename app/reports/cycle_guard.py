"""
Cycle lock guard — blocks all write operations when the academic cycle is frozen.

Usage:
    from app.reports.cycle_guard import require_cycle_unlocked
    require_cycle_unlocked()  # raises RuntimeError if locked
"""

from sqlalchemy import text
from app.db.session import get_transaction


def is_cycle_locked() -> bool:
    """Check if the active academic cycle is locked (frozen after HOD approval)."""
    with get_transaction() as session:
        row = session.execute(
            text("""
                SELECT COALESCE(is_locked, false)
                FROM academic_cycle
                WHERE is_active = true
                LIMIT 1
            """)
        ).fetchone()
        if not row:
            return False
        return bool(row[0])


def require_cycle_unlocked() -> None:
    """
    Raise RuntimeError if the active cycle is locked.
    Call this at the top of any write operation (preferences, allocations).
    """
    if is_cycle_locked():
        raise RuntimeError(
            "Academic cycle is frozen after HOD approval. "
            "No further changes to preferences or allocations are allowed."
        )
