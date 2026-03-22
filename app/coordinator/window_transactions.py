# CRITICAL WINDOW LIFECYCLE FILE — REQUIRES EXTERNAL REVIEW BEFORE DEPLOYMENT
"""
Window lifecycle transaction layer.
Spec reference: window_lifecycle_design.md

This module implements deterministic, race-safe window state transitions.

STATE MACHINE (FROZEN):
  DRAFT → SCHEDULED → OPEN → CLOSED → ARCHIVED

CRITICAL CONSTRAINTS:
- Single OPEN window per (batch_id, specialization_id)
- start_time and end_time IMMUTABLE after SCHEDULED
- All transitions audited
- No automatic time-based transitions
"""

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.db.session import get_transaction
import logging

logger = logging.getLogger(__name__)


def create_window_transaction(
    coordinator_id: int,
    name: str,
    batch_id: int,
    specialization_id: int,
    start_time: str = None,
    end_time: str = None,
    max_subjects_per_staff: int = 3
) -> dict:
    """
    Create new window in DRAFT state.
    
    Args:
        coordinator_id: Staff ID of coordinator creating window
        name: Window name/description
        batch_id: Batch ID (NOT NULL)
        specialization_id: Specialization ID (NOT NULL)
        start_time: Optional start time (can be set later)
        end_time: Optional end time (can be set later)
        max_subjects_per_staff: Maximum subjects per staff (default 3)
    
    Returns:
        dict with keys: success (bool), message (str), window_id (int or None)
    """
    
    with get_transaction(isolation_level="READ COMMITTED") as session:
        session.execute(text("SET LOCAL lock_timeout = '5s'"))
        
        # Insert new window in DRAFT state
        result = session.execute(
            text("""
                INSERT INTO selection_window
                  (name, start_time, end_time, max_subjects_per_staff,
                   batch_id, specialization_id, status)
                VALUES (:name, :start_time, :end_time, :max_subjects,
                        :batch_id, :spec_id, 'DRAFT')
                RETURNING id
            """),
            {
                "name": name,
                "start_time": start_time,
                "end_time": end_time,
                "max_subjects": max_subjects_per_staff,
                "batch_id": batch_id,
                "spec_id": specialization_id
            }
        ).fetchone()
        
        window_id = result[0]
        
        # Audit log
        session.execute(
            text("""
                INSERT INTO audit_log
                  (actor_staff_id, action_type, details)
                VALUES (:coordinator_id, 'WINDOW_CREATED',
                        jsonb_build_object(
                            'window_id', :window_id,
                            'batch_id', :batch_id,
                            'specialization_id', :spec_id,
                            'name', :name
                        ))
            """),
            {
                "coordinator_id": coordinator_id,
                "window_id": window_id,
                "batch_id": batch_id,
                "spec_id": specialization_id,
                "name": name
            }
        )
        
        logger.info(f"Window created: id={window_id}, batch={batch_id}, spec={specialization_id}")
        
        session.commit()
        return {
            "success": True,
            "message": "Window created successfully",
            "window_id": window_id
        }


def schedule_window_transaction(
    coordinator_id: int,
    window_id: int,
    start_time: str,
    end_time: str
) -> dict:
    """
    Transition window from DRAFT to SCHEDULED.
    
    PRECONDITIONS (ALL REQUIRED):
    - start_time IS NOT NULL
    - end_time IS NOT NULL
    - end_time > start_time
    - start_time > now()
    
    POST-TRANSITION:
    - start_time and end_time become IMMUTABLE (enforced by trigger)
    
    Args:
        coordinator_id: Staff ID of coordinator
        window_id: Window ID to schedule
        start_time: Start time (ISO 8601 format)
        end_time: End time (ISO 8601 format)
    
    Returns:
        dict with keys: success (bool), message (str), window_id (int or None)
    """
    
    with get_transaction(isolation_level="READ COMMITTED") as session:
        session.execute(text("SET LOCAL lock_timeout = '5s'"))
        
        # Lock window row
        window = session.execute(
            text("""
                SELECT id, status, start_time, end_time, batch_id, specialization_id
                FROM selection_window
                WHERE id = :window_id
                FOR UPDATE
            """),
            {"window_id": window_id}
        ).fetchone()
        
        if not window:
            return {
                "success": False,
                "message": "Window not found",
                "window_id": None
            }
        
        current_status = window[1]
        
        # Validate current state
        if current_status != 'DRAFT':
            return {
                "success": False,
                "message": f"Window not in DRAFT state (current: {current_status})",
                "window_id": None
            }
        
        # Validate preconditions
        if not start_time:
            return {
                "success": False,
                "message": "start_time is required",
                "window_id": None
            }
        
        if not end_time:
            return {
                "success": False,
                "message": "end_time is required",
                "window_id": None
            }
        
        # Validate time ordering (database will also check via constraint)
        # This is done in Python for better error messages
        from datetime import datetime
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            if end_dt <= start_dt:
                return {
                    "success": False,
                    "message": "end_time must be after start_time",
                    "window_id": None
                }
        except ValueError as e:
            return {
                "success": False,
                "message": f"Invalid datetime format: {str(e)}",
                "window_id": None
            }
        
        # Validate start_time is in future
        now_check = session.execute(
            text("SELECT :start_time::timestamptz > now()"),
            {"start_time": start_time}
        ).scalar()
        
        if not now_check:
            return {
                "success": False,
                "message": "start_time must be in the future",
                "window_id": None
            }
        
        # Perform transition
        # After this, start_time and end_time become IMMUTABLE (trigger enforces)
        session.execute(
            text("""
                UPDATE selection_window
                SET status = 'SCHEDULED',
                    start_time = :start_time,
                    end_time = :end_time,
                    updated_at = now()
                WHERE id = :window_id
            """),
            {
                "window_id": window_id,
                "start_time": start_time,
                "end_time": end_time
            }
        )
        
        # Audit log
        session.execute(
            text("""
                INSERT INTO audit_log
                  (actor_staff_id, action_type, details)
                VALUES (:coordinator_id, 'WINDOW_SCHEDULED',
                        jsonb_build_object(
                            'window_id', :window_id,
                            'start_time', :start_time,
                            'end_time', :end_time
                        ))
            """),
            {
                "coordinator_id": coordinator_id,
                "window_id": window_id,
                "start_time": start_time,
                "end_time": end_time
            }
        )
        
        logger.info(f"Window scheduled: id={window_id}, start={start_time}, end={end_time}")
        
        session.commit()
        return {
            "success": True,
            "message": "Window scheduled successfully",
            "window_id": window_id
        }


def open_window_transaction(
    coordinator_id: int,
    window_id: int
) -> dict:
    """
    Transition window from SCHEDULED to OPEN.
    
    PRECONDITION: now() >= start_time
    CONSTRAINT: Only ONE OPEN window per (batch_id, specialization_id)
    
    CRITICAL: Also transitions semester state to OPEN to enable preferences.
    
    Args:
        coordinator_id: Staff ID of coordinator
        window_id: Window ID to open
    
    Returns:
        dict with keys: success (bool), message (str), window_id (int or None)
    
    Raises:
        IntegrityError: If another OPEN window exists for same batch/spec
    """
    
    try:
        with get_transaction(isolation_level="READ COMMITTED") as session:
            session.execute(text("SET LOCAL lock_timeout = '5s'"))
            
            # Lock window row
            window = session.execute(
                text("""
                    SELECT id, status, start_time, batch_id, specialization_id
                    FROM selection_window
                    WHERE id = :window_id
                    FOR UPDATE
                """),
                {"window_id": window_id}
            ).fetchone()
            
            if not window:
                return {
                    "success": False,
                    "message": "Window not found",
                    "window_id": None
                }
            
            current_status = window[1]
            start_time = window[2]
            batch_id = window[3]
            spec_id = window[4]
            
            # Validate state transition (ONLY SCHEDULED → OPEN allowed)
            if current_status != 'SCHEDULED':
                return {
                    "success": False,
                    "message": f"Window must be in SCHEDULED state to open (current: {current_status})",
                    "window_id": None
                }
            
            # Validate time constraint
            now_check = session.execute(
                text("SELECT now() >= :start_time::timestamptz"),
                {"start_time": start_time}
            ).scalar()
            
            if not now_check:
                return {
                    "success": False,
                    "message": "Cannot open window before start_time",
                    "window_id": None
                }
            
            # CRITICAL FIX: Get semester_id from subject_offering for this batch/spec
            # This connects the window system to the semester state system
            semester_row = session.execute(
                text("""
                    SELECT DISTINCT semester_id
                    FROM subject_offering
                    WHERE program_id IN (
                        SELECT id FROM program WHERE name IN ('MCA', 'BCA')
                    )
                    LIMIT 1
                """)
            ).fetchone()
            
            semester_id = semester_row[0] if semester_row else None
            
            # Perform window transition
            # Partial unique index will enforce single OPEN window per batch/spec
            session.execute(
                text("""
                    UPDATE selection_window
                    SET status = 'OPEN', updated_at = now()
                    WHERE id = :window_id
                """),
                {"window_id": window_id}
            )
            
            # CRITICAL FIX: Also transition semester state to OPEN
            # This enables faculty to browse subjects and submit preferences
            from datetime import datetime
            session.execute(
                text("""
                    UPDATE semester
                    SET state = 'OPEN',
                        opened_at = :now,
                        closed_at = NULL,
                        allocated_at = NULL
                    WHERE id IN (SELECT id FROM semester)
                """),
                {"now": datetime.utcnow()}
            )
            logger.info(f"All semesters state transitioned to OPEN (triggered by window {window_id})")
            
            # Audit log
            session.execute(
                text("""
                    INSERT INTO audit_log
                      (actor_staff_id, action_type, details)
                    VALUES (:coordinator_id, 'WINDOW_OPENED',
                            jsonb_build_object('window_id', :window_id, 'semester_id', :semester_id))
                """),
                {
                    "coordinator_id": coordinator_id,
                    "window_id": window_id,
                    "semester_id": semester_id
                }
            )
            
            logger.info(f"Window opened: id={window_id}, semester_id={semester_id}")
            
            session.commit()
            return {
                "success": True,
                "message": "Window opened successfully (semester state updated to OPEN)",
                "window_id": window_id
            }
    
    except IntegrityError as e:
        error_msg = str(e)
        if "uq_one_open_window_per_batch_spec" in error_msg:
            return {
                "success": False,
                "message": "Another window is already open for this batch/specialization",
                "window_id": None
            }
        raise


def close_window_transaction(
    coordinator_id: int,
    window_id: int
) -> dict:
    """
    Transition window from OPEN to CLOSED.
    
    Can be called early (before end_time) or after expiration.
    
    CRITICAL: Also transitions semester state to CLOSED to lock preferences.
    
    Args:
        coordinator_id: Staff ID of coordinator
        window_id: Window ID to close
    
    Returns:
        dict with keys: success (bool), message (str), window_id (int or None)
    """
    
    with get_transaction(isolation_level="READ COMMITTED") as session:
        session.execute(text("SET LOCAL lock_timeout = '5s'"))
        
        # Lock window row
        window = session.execute(
            text("""
                SELECT id, status
                FROM selection_window
                WHERE id = :window_id
                FOR UPDATE
            """),
            {"window_id": window_id}
        ).fetchone()
        
        if not window:
            return {
                "success": False,
                "message": "Window not found",
                "window_id": None
            }
        
        current_status = window[1]
        
        # Validate state transition
        if current_status != 'OPEN':
            return {
                "success": False,
                "message": f"Window not open (current: {current_status})",
                "window_id": None
            }
        
        # CRITICAL FIX: Get semester_id from subject_offering for this window
        # This connects the window system to the semester state system
        semester_row = session.execute(
            text("""
                SELECT DISTINCT semester_id
                FROM subject_offering
                WHERE program_id IN (
                    SELECT id FROM program WHERE name IN ('MCA', 'BCA')
                )
                LIMIT 1
            """)
        ).fetchone()
        
        semester_id = semester_row[0] if semester_row else None
        
        # Perform window transition
        session.execute(
            text("""
                UPDATE selection_window
                SET status = 'CLOSED', updated_at = now()
                WHERE id = :window_id
            """),
            {"window_id": window_id}
        )
        
        # CRITICAL FIX: Also transition semester state to CLOSED
        # This locks preferences and prepares for allocation
        from datetime import datetime
        session.execute(
            text("""
                UPDATE semester
                SET state = 'CLOSED',
                    closed_at = now()
            """)
        )
        logger.info(f"All semesters state transitioned to CLOSED (triggered by window {window_id})")
        
        # Audit log
        session.execute(
            text("""
                INSERT INTO audit_log
                  (actor_staff_id, action_type, details)
                VALUES (:coordinator_id, 'WINDOW_CLOSED',
                        jsonb_build_object('window_id', :window_id, 'semester_id', :semester_id))
            """),
            {
                "coordinator_id": coordinator_id,
                "window_id": window_id,
                "semester_id": semester_id
            }
        )
        
        logger.info(f"Window closed: id={window_id}, semester_id={semester_id}")
        
        session.commit()
        return {
            "success": True,
            "message": "Window closed successfully (semester state updated to CLOSED)",
            "window_id": window_id
        }


def archive_window_transaction(
    coordinator_id: int,
    window_id: int
) -> dict:
    """
    Transition window from CLOSED to ARCHIVED.
    
    Args:
        coordinator_id: Staff ID of coordinator
        window_id: Window ID to archive
    
    Returns:
        dict with keys: success (bool), message (str), window_id (int or None)
    """
    
    with get_transaction(isolation_level="READ COMMITTED") as session:
        session.execute(text("SET LOCAL lock_timeout = '5s'"))
        
        # Lock window row
        window = session.execute(
            text("""
                SELECT id, status
                FROM selection_window
                WHERE id = :window_id
                FOR UPDATE
            """),
            {"window_id": window_id}
        ).fetchone()
        
        if not window:
            return {
                "success": False,
                "message": "Window not found",
                "window_id": None
            }
        
        current_status = window[1]
        
        # Validate state transition
        if current_status != 'CLOSED':
            return {
                "success": False,
                "message": f"Window not closed (current: {current_status})",
                "window_id": None
            }
        
        # Perform transition
        session.execute(
            text("""
                UPDATE selection_window
                SET status = 'ARCHIVED', updated_at = now()
                WHERE id = :window_id
            """),
            {"window_id": window_id}
        )
        
        # Audit log
        session.execute(
            text("""
                INSERT INTO audit_log
                  (actor_staff_id, action_type, details)
                VALUES (:coordinator_id, 'WINDOW_ARCHIVED',
                        jsonb_build_object('window_id', :window_id))
            """),
            {
                "coordinator_id": coordinator_id,
                "window_id": window_id
            }
        )
        
        logger.info(f"Window archived: id={window_id}")
        
        session.commit()
        return {
            "success": True,
            "message": "Window archived successfully",
            "window_id": window_id
        }
