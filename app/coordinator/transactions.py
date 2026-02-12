# CRITICAL FCFS FILE — REQUIRES EXTERNAL REVIEW BEFORE DEPLOYMENT
"""
Coordinator override transaction.
Spec reference: FSB_v1.1.md Section 4

This module implements coordinator-initiated subject selection overrides.
The override uses row-level locking to ensure safe concurrent access.
"""

from sqlalchemy import text
from app.db.session import get_transaction


def override_subject_transaction(
    coordinator_staff_id: int,
    subject_id: int
) -> dict:
    """
    Execute coordinator override transaction per FSB_v1.1.md Section 4.2.
    
    Args:
        coordinator_staff_id: Staff ID of the coordinator performing the override
        subject_id: Subject ID to override
    
    Returns:
        dict with keys: success (bool), message (str), affected_staff_id (int or None)
    
    Raises:
        Exception: Re-raises database exceptions for proper HTTP error mapping
    """
    
    with get_transaction(isolation_level="READ COMMITTED") as session:
        
        # Override Logic (Section 4.2 - EXACT)
        override_result = session.execute(
            text("""
                UPDATE subject_selection
                SET status = 'OVERRIDDEN'
                WHERE subject_id = :subject_id
                  AND status = 'SELECTED'
                FOR UPDATE
                RETURNING staff_id
            """),
            {"subject_id": subject_id}
        ).fetchone()
        
        if not override_result:
            return {
                "success": False,
                "message": "Subject no longer selected",
                "affected_staff_id": None
            }
        
        affected_staff_id = override_result[0]
        
        # Audit Log
        session.execute(
            text("""
                INSERT INTO audit_log
                  (actor_staff_id, action_type, subject_id, affected_staff_id, details, created_at)
                VALUES (:actor_staff_id, 'OVERRIDE', :subject_id, :affected_staff_id, '{}'::jsonb, now())
            """),
            {
                "actor_staff_id": coordinator_staff_id,
                "subject_id": subject_id,
                "affected_staff_id": affected_staff_id
            }
        )
        
        # COMMIT (automatic via context manager)
        return {
            "success": True,
            "message": "Subject override successful",
            "affected_staff_id": affected_staff_id
        }
