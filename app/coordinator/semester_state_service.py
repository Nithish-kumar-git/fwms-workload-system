"""
Semester state management service.
PHASE 2: Controls semester workflow states and transitions.

State flow:
  CLOSED → OPEN → CLOSED → ALLOCATED → FROZEN
  
State descriptions:
  - CLOSED: Default state, no preferences allowed
  - OPEN: Faculty can submit preferences
  - CLOSED: Preferences locked, ready for allocation
  - ALLOCATED: Allocation completed, can be edited
  - FROZEN: Finalized by HOD, no changes allowed
"""

from sqlalchemy import text
from app.db.session import get_transaction
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SemesterState:
    """Semester workflow states"""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    ALLOCATED = "ALLOCATED"
    FROZEN = "FROZEN"


def get_semester_state(semester_id: int) -> dict | None:
    """
    Get current state of a semester.
    
    Returns:
        dict with semester info and state, or None if not found
    """
    with get_transaction() as session:
        row = session.execute(
            text("""
                SELECT id, label, state, opened_at, closed_at, 
                       allocated_at, frozen_at, frozen_by_staff_id
                FROM semester
                WHERE id = :sid
            """),
            {"sid": semester_id}
        ).fetchone()
        
        if not row:
            return None
        
        return {
            "id": row[0],
            "label": row[1],
            "state": row[2],
            "opened_at": row[3],
            "closed_at": row[4],
            "allocated_at": row[5],
            "frozen_at": row[6],
            "frozen_by_staff_id": row[7],
        }


def open_semester(semester_id: int, coordinator_id: int) -> dict:
    """
    Open semester for faculty preference submission.
    
    Allowed transitions:
    - CLOSED → OPEN (initial open)
    - ALLOCATED → OPEN (reopen for rework, clears ALL derived data)
    
    HARDENING: When reopening from ALLOCATED, clears:
    - All allocations for this semester
    - All workload summaries for this semester
    - All preferences for this semester (fresh start)
    
    Returns:
        dict with success status and message
    """
    with get_transaction() as session:
        # Get current state and academic_cycle_id
        row = session.execute(
            text("""
                SELECT sem.state, so.academic_cycle_id
                FROM semester sem
                LEFT JOIN subject_offering so ON so.semester_id = sem.id
                WHERE sem.id = :sid
                LIMIT 1
            """),
            {"sid": semester_id}
        ).fetchone()
        
        if not row:
            return {"success": False, "message": f"Semester {semester_id} not found"}
        
        current_state = row[0]
        cycle_id = row[1]
        
        # Validate transition
        if current_state == SemesterState.FROZEN:
            return {
                "success": False,
                "message": "Cannot reopen FROZEN semester. Semester is finalized by HOD."
            }
        
        if current_state == SemesterState.OPEN:
            return {
                "success": False,
                "message": "Semester is already OPEN"
            }
        
        # If reopening from ALLOCATED or CLOSED, clear ALL derived data
        if current_state in (SemesterState.ALLOCATED, SemesterState.CLOSED):
            logger.warning(f"Reopening semester {semester_id} from {current_state} - clearing ALL derived data")
            
            # STEP 1: Clear allocations for this semester ONLY
            # CRITICAL: Use semester_id filter to maintain single-semester isolation
            deleted_allocs = session.execute(
                text("""
                    DELETE FROM allocation 
                    WHERE subject_offering_id IN (
                        SELECT id FROM subject_offering WHERE semester_id = :sid
                    )
                """),
                {"sid": semester_id}
            ).rowcount
            
            logger.info(f"  Cleared {deleted_allocs} allocations for semester {semester_id}")
            
            # STEP 2: Clear ALL preferences for this semester (fresh start)
            # CRITICAL: Use semester_id filter to maintain single-semester isolation
            deleted_prefs = session.execute(
                text("""
                    DELETE FROM faculty_preference
                    WHERE subject_offering_id IN (
                        SELECT id FROM subject_offering WHERE semester_id = :sid
                    )
                """),
                {"sid": semester_id}
            ).rowcount
            
            logger.info(f"  Cleared {deleted_prefs} preferences for semester {semester_id} (fresh start)")
            
            # NOTE: workload_summary is NOT deleted here because:
            # 1. It uses (academic_year, semester_type) not semester_id
            # 2. Deleting by cycle_id would affect OTHER semesters (breaks isolation)
            # 3. Allocation service will properly delete and regenerate it
            logger.info(f"  Workload summaries will be regenerated during next allocation")
        
        # Update state
        session.execute(
            text("""
                UPDATE semester
                SET state = :new_state,
                    opened_at = :now,
                    closed_at = NULL,
                    allocated_at = NULL
                WHERE id = :sid
            """),
            {"new_state": SemesterState.OPEN, "now": datetime.utcnow(), "sid": semester_id}
        )
        
        # Audit log
        action_type = "SEMESTER_REOPENED" if current_state == SemesterState.ALLOCATED else "SEMESTER_OPENED"
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, :action, :details)
            """),
            {
                "actor": coordinator_id,
                "action": action_type,
                "details": f'{{"semester_id": {semester_id}, "previous_state": "{current_state}"}}'
            }
        )
        
        session.commit()
        
        logger.info(f"Semester {semester_id} opened by coordinator {coordinator_id} (was {current_state})")
        return {"success": True, "message": f"Semester {semester_id} opened for preferences (all previous data cleared)"}


def close_semester(semester_id: int, coordinator_id: int) -> dict:
    """
    Close semester (lock preferences, ready for allocation).
    
    Transition: OPEN → CLOSED
    
    Validates that at least some preferences have been submitted.
    
    Returns:
        dict with success status and message
    """
    with get_transaction() as session:
        # Get current state
        row = session.execute(
            text("SELECT state FROM semester WHERE id = :sid"),
            {"sid": semester_id}
        ).fetchone()
        
        if not row:
            return {"success": False, "message": f"Semester {semester_id} not found"}
        
        current_state = row[0]
        
        # Validate transition
        if current_state != SemesterState.OPEN:
            return {
                "success": False,
                "message": f"Cannot close semester in state {current_state}. Must be OPEN."
            }
        
        # Check if any preferences have been submitted
        pref_count = session.execute(
            text("""
                SELECT COUNT(*)
                FROM faculty_preference fp
                JOIN subject_offering so ON so.id = fp.subject_offering_id
                WHERE so.semester_id = :sid
            """),
            {"sid": semester_id}
        ).scalar()
        
        if pref_count == 0:
            return {
                "success": False,
                "message": "Cannot close semester with no preferences submitted. At least one preference is required."
            }
        
        # Update state
        session.execute(
            text("""
                UPDATE semester
                SET state = :new_state,
                    closed_at = :now
                WHERE id = :sid
            """),
            {"new_state": SemesterState.CLOSED, "now": datetime.utcnow(), "sid": semester_id}
        )
        
        # Audit log
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'SEMESTER_CLOSED', :details)
            """),
            {
                "actor": coordinator_id,
                "details": f'{{"semester_id": {semester_id}, "preference_count": {pref_count}}}'
            }
        )
        
        session.commit()
        
        logger.info(f"Semester {semester_id} closed by coordinator {coordinator_id} ({pref_count} preferences)")
        return {"success": True, "message": f"Semester {semester_id} closed with {pref_count} preferences, ready for allocation"}


def mark_semester_allocated(semester_id: int) -> dict:
    """
    Mark semester as allocated (called automatically after allocation completes).
    
    Transition: CLOSED → ALLOCATED
    
    Returns:
        dict with success status and message
    """
    with get_transaction() as session:
        # Get current state
        row = session.execute(
            text("SELECT state FROM semester WHERE id = :sid"),
            {"sid": semester_id}
        ).fetchone()
        
        if not row:
            return {"success": False, "message": f"Semester {semester_id} not found"}
        
        current_state = row[0]
        
        # Validate transition
        if current_state != SemesterState.CLOSED:
            return {
                "success": False,
                "message": f"Cannot mark as allocated in state {current_state}. Must be CLOSED."
            }
        
        # Update state
        session.execute(
            text("""
                UPDATE semester
                SET state = :new_state,
                    allocated_at = :now
                WHERE id = :sid
            """),
            {"new_state": SemesterState.ALLOCATED, "now": datetime.utcnow(), "sid": semester_id}
        )
        
        session.commit()
        
        logger.info(f"Semester {semester_id} marked as ALLOCATED")
        return {"success": True, "message": f"Semester {semester_id} allocation completed"}


def freeze_semester(semester_id: int, hod_id: int) -> dict:
    """
    Freeze semester (finalize by HOD, no further changes allowed).
    
    Transition: ALLOCATED → FROZEN
    
    Returns:
        dict with success status and message
    """
    with get_transaction() as session:
        # Get current state
        row = session.execute(
            text("SELECT state FROM semester WHERE id = :sid"),
            {"sid": semester_id}
        ).fetchone()
        
        if not row:
            return {"success": False, "message": f"Semester {semester_id} not found"}
        
        current_state = row[0]
        
        # Validate transition
        if current_state != SemesterState.ALLOCATED:
            return {
                "success": False,
                "message": f"Cannot freeze semester in state {current_state}. Must be ALLOCATED."
            }
        
        # Update state
        session.execute(
            text("""
                UPDATE semester
                SET state = :new_state,
                    frozen_at = :now,
                    frozen_by_staff_id = :hod_id
                WHERE id = :sid
            """),
            {
                "new_state": SemesterState.FROZEN,
                "now": datetime.utcnow(),
                "hod_id": hod_id,
                "sid": semester_id
            }
        )
        
        # Audit log
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'SEMESTER_FROZEN', :details)
            """),
            {
                "actor": hod_id,
                "details": f'{{"semester_id": {semester_id}}}'
            }
        )
        
        session.commit()
        
        logger.info(f"Semester {semester_id} frozen by HOD {hod_id}")
        return {"success": True, "message": f"Semester {semester_id} frozen, no further changes allowed"}


def validate_semester_state(semester_id: int, required_state: str) -> tuple[bool, str]:
    """
    Validate that semester is in required state.
    
    Args:
        semester_id: Semester ID to check
        required_state: Required state (e.g., SemesterState.OPEN)
    
    Returns:
        (is_valid, error_message)
    """
    semester_info = get_semester_state(semester_id)
    
    if not semester_info:
        return False, f"Semester {semester_id} not found"
    
    if semester_info["state"] != required_state:
        return False, f"Semester must be in {required_state} state (currently {semester_info['state']})"
    
    return True, ""


def is_semester_frozen(semester_id: int) -> bool:
    """Check if semester is frozen."""
    semester_info = get_semester_state(semester_id)
    return semester_info and semester_info["state"] == SemesterState.FROZEN
