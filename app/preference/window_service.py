"""
Preference window service — manages the preference submission window lifecycle.
Uses the existing selection_window table and window_transactions module.

Convenience layer that provides:
  - open_preference_window: creates + opens a window in one step
  - close_preference_window: closes the active window
  - get_window_status: returns current window state with remaining time
  - is_window_open: guard check for preference submissions
"""

from sqlalchemy import text
from app.db.session import get_transaction
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def open_preference_window(
    coordinator_id: int,
    start_time: str,
    end_time: str,
    academic_year: str | None = None,
    semester_id: int | None = None,
    cycle_id: int | None = None,
) -> dict:
    """
    Open a preference submission window.
    Follows the frozen lifecycle: DRAFT → SCHEDULED → OPEN.
    Only one OPEN window allowed per academic_year + semester_id.
    """
    with get_transaction() as session:
        # Check for existing OPEN window
        existing = session.execute(
            text("""
                SELECT id FROM selection_window
                WHERE status = 'OPEN'
                LIMIT 1
            """),
        ).fetchone()

        if existing is not None:
            return {
                "success": False,
                "message": f"An open window already exists (id={existing[0]}). Close it first.",
            }

        resolved_cycle_id = None
        # 1. Use explicit ID
        if cycle_id is not None:
            resolved_cycle_id = cycle_id
        # 2. Lookup by year/semester
        elif academic_year and semester_id:
            cycle_row = session.execute(
                text("""
                    SELECT id FROM cycle
                    WHERE academic_year = :year AND semester_id = :sem_id
                    ORDER BY id DESC LIMIT 1
                """),
                {"year": academic_year, "sem_id": semester_id},
            ).fetchone()
            resolved_cycle_id = cycle_row[0] if cycle_row else None
        
        # 3. Fallback to active cycle
        if resolved_cycle_id is None:
            from app.admin.cycle_service_new import get_active_cycle
            active = get_active_cycle()
            if active:
                resolved_cycle_id = active["id"]
                academic_year = active["academic_year"]
                semester_id = active["semester_id"]
            else:
                return {"success": False, "message": "Failed to resolve cycle scope"}
                
        # ---- LIFECYCLE STEP 1: Insert as DRAFT ----
        result = session.execute(
            text("""
                INSERT INTO selection_window
                    (name, batch_id, specialization_id, start_time, end_time,
                     status, max_subjects_per_staff, cycle_id,
                     allocation_locked)
                VALUES (
                    :name, 1, 1, :start_time, :end_time,
                    'DRAFT', 5, :cycle_id, false
                )
                RETURNING id
            """),
            {
                "name": f"Preference Window {academic_year} Sem-{semester_id}",
                "start_time": start_time,
                "end_time": end_time,
                "cycle_id": resolved_cycle_id,
            },
        )
        window_id = result.scalar()

        # Audit: WINDOW_CREATED
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'WINDOW_CREATED', :details)
            """),
            {
                "actor": coordinator_id,
                "details": (
                    f'{{"window_id": {window_id}, '
                    f'"academic_year": "{academic_year}", '
                    f'"semester_id": {semester_id}}}'
                ),
            },
        )

        # ---- LIFECYCLE STEP 2: Transition DRAFT → SCHEDULED ----
        session.execute(
            text("""
                UPDATE selection_window
                SET status = 'SCHEDULED', updated_at = now()
                WHERE id = :id
            """),
            {"id": window_id},
        )

        # Audit: WINDOW_SCHEDULED
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'WINDOW_SCHEDULED', :details)
            """),
            {
                "actor": coordinator_id,
                "details": (
                    f'{{"window_id": {window_id}, '
                    f'"start_time": "{start_time}", '
                    f'"end_time": "{end_time}"}}'
                ),
            },
        )

        # ---- LIFECYCLE STEP 3: Transition SCHEDULED → OPEN ----
        session.execute(
            text("""
                UPDATE selection_window
                SET status = 'OPEN', updated_at = now()
                WHERE id = :id
            """),
            {"id": window_id},
        )

        # Audit: WINDOW_OPENED
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'WINDOW_OPENED', :details)
            """),
            {
                "actor": coordinator_id,
                "details": (
                    f'{{"window_id": {window_id}, '
                    f'"academic_year": "{academic_year}", '
                    f'"semester_id": {semester_id}, '
                    f'"start_time": "{start_time}", '
                    f'"end_time": "{end_time}"}}'
                ),
            },
        )

        session.commit()

    logger.info(f"Preference window opened: id={window_id} (DRAFT→SCHEDULED→OPEN)")
    return {
        "success": True,
        "message": "Preference window opened",
        "window_id": window_id,
    }


def close_preference_window(coordinator_id: int) -> dict:
    """Close the currently open preference window."""
    with get_transaction() as session:
        window = session.execute(
            text("SELECT id FROM selection_window WHERE status = 'OPEN' LIMIT 1")
        ).fetchone()

        if window is None:
            return {"success": False, "message": "No open window found"}

        window_id = window[0]
        session.execute(
            text("UPDATE selection_window SET status = 'CLOSED' WHERE id = :id"),
            {"id": window_id},
        )

        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'WINDOW_CLOSED', :details)
            """),
            {
                "actor": coordinator_id,
                "details": f'{{"window_id": {window_id}}}',
            },
        )

        session.commit()

    logger.info(f"Preference window closed: id={window_id}")
    return {"success": True, "message": "Preference window closed", "window_id": window_id}


def get_window_status() -> dict:
    """
    Get the current preference window status.
    Returns is_open, timing details, and remaining time.
    """
    with get_transaction() as session:
        row = session.execute(
            text("""
                SELECT sw.id, sw.status, sw.start_time, sw.end_time,
                       ay.name AS academic_year, c.semester_id
                FROM selection_window sw
                LEFT JOIN cycle c ON c.id = sw.cycle_id
                LEFT JOIN academic_year ay ON ay.id = c.academic_year_id
                WHERE sw.status = 'OPEN'
                ORDER BY sw.id DESC LIMIT 1
            """),
        ).fetchone()

    if row is None:
        return {
            "is_open": False,
            "status": "CLOSED",
            "window_id": None,
            "start_time": None,
            "end_time": None,
            "remaining_seconds": 0,
            "academic_year": None,
            "semester_id": None,
        }

    now = datetime.now(timezone.utc)
    end_time = row[3]
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    remaining = max(0, int((end_time - now).total_seconds()))

    return {
        "is_open": True,
        "status": row[1],  # 'OPEN', 'CLOSED', 'SCHEDULED'
        "window_id": row[0],
        "start_time": str(row[2]),
        "end_time": str(row[3]),
        "remaining_seconds": remaining,
        "academic_year": row[4],
        "semester_id": row[5],
    }


def is_window_open() -> bool:
    """Quick check: is there an open preference window?"""
    status = get_window_status()
    return status["is_open"]
