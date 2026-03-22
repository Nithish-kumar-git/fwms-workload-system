# CRITICAL FCFS FILE — REQUIRES EXTERNAL REVIEW BEFORE DEPLOYMENT
"""
FCFS subject selection transaction.
Spec reference: FSB_v1.3.md Section 3.2 (Advisory Lock Serialization)

This module implements the SELECT SUBJECT transaction flow exactly as specified.
Database constraints are the ONLY arbiter of FCFS fairness.

ADVISORY LOCK ORDERING (FROZEN):
1. FOR SHARE (window and eligibility validation)
2. pg_advisory_xact_lock(staff_id, window_id)
3. Row-level write locks (FOR UPDATE on quota, slot)
4. INSERT/DELETE on subject_selection
5. Audit log insert
"""

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.db.session import get_transaction


def select_subject_transaction(
    staff_id: int,
    subject_id: int,
    batch_id: int,
    specialization_id: int
) -> dict:
    """
    Execute SELECT SUBJECT transaction per FSB_v1.3.md Section 3.5.
    
    Returns:
        dict with keys: success (bool), message (str), selection_id (int or None)
    
    Raises:
        Exception: Re-raises database exceptions for proper HTTP error mapping
    """
    
    try:
        with get_transaction(isolation_level="READ COMMITTED") as session:
            
            # Set lock timeout per FSB v1.3 §3.5
            session.execute(text("SET LOCAL lock_timeout = '5s'"))
            
            # Step 1 — Window Validation (FOR SHARE)
            # Updated per window_lifecycle_design.md:
            # - status = 'OPEN' (replaces is_active)
            # - batch_id scoping (CRITICAL)
            # - specialization_id scoping (CRITICAL)
            # - LIMIT 1 (defensive: partial unique index guarantees at most 1 row)
            #
            # LOCK ORDERING (FROZEN):
            # 1. FOR SHARE (window validation) ← YOU ARE HERE
            # 2. pg_advisory_xact_lock(staff_id, window_id)
            # 3. FOR UPDATE (quota, slot)
            # 4. INSERT/DELETE
            window_result = session.execute(
                text("""
                    SELECT id, max_subjects_per_staff
                    FROM selection_window
                    WHERE status = 'OPEN'
                      AND batch_id = :batch_id
                      AND specialization_id = :specialization_id
                      AND now() BETWEEN start_time AND end_time
                    FOR SHARE
                    LIMIT 1
                """),
                {"batch_id": batch_id, "specialization_id": specialization_id}
            ).fetchone()
            
            if not window_result:
                return {
                    "success": False,
                    "message": "Window closed",
                    "selection_id": None
                }
            
            window_id = window_result[0]
            max_subjects_per_staff = window_result[1]
            
            # Step 1.5 — Eligibility Verification (FOR SHARE)
            eligibility_result = session.execute(
                text("""
                    SELECT sa.id
                    FROM staff_assignment sa
                    JOIN subject s
                      ON s.batch_id = sa.batch_id
                     AND s.specialization_id = sa.specialization_id
                    WHERE sa.staff_id = :staff_id
                      AND s.id = :subject_id
                    FOR SHARE
                """),
                {"staff_id": staff_id, "subject_id": subject_id}
            ).fetchone()
            
            if not eligibility_result:
                return {
                    "success": False,
                    "message": "Not eligible for this subject",
                    "selection_id": None
                }
            
            # Step 1.75a — Staff-level Advisory Lock (serializes slot computation per staff)
            session.execute(
                text("SELECT pg_advisory_xact_lock(:staff_id)"),
                {"staff_id": staff_id}
            )
            
            # Step 1.75b — Staff+Window Advisory Lock (FSB v1.3 Rule 2)
            # MUST be acquired AFTER window/eligibility validation
            # MUST be acquired BEFORE quota check, slot assignment, INSERT/DELETE
            session.execute(
                text("SELECT pg_advisory_xact_lock(:staff_id, :window_id)"),
                {"staff_id": staff_id, "window_id": window_id}
            )
            
            # Step 2 — Lock Quota (FOR UPDATE)
            # Cannot use COUNT(*) with FOR UPDATE, must fetch rows and count
            quota_rows = session.execute(
                text("""
                    SELECT id
                    FROM subject_selection
                    WHERE staff_id = :staff_id
                      AND window_id = :window_id
                      AND status = 'SELECTED'
                    FOR UPDATE
                """),
                {"staff_id": staff_id, "window_id": window_id}
            ).fetchall()
            
            current_count = len(quota_rows)
            
            if current_count >= max_subjects_per_staff:
                return {
                    "success": False,
                    "message": "Quota exceeded",
                    "selection_id": None
                }
            
            # Step 3 — Assign staff_slot_number (FOR UPDATE)
            # Cannot use MAX() with FOR UPDATE, must fetch rows and compute max
            slot_rows = session.execute(
                text("""
                    SELECT staff_slot_number
                    FROM subject_selection
                    WHERE staff_id = :staff_id
                      AND window_id = :window_id
                      AND status = 'SELECTED'
                    FOR UPDATE
                """),
                {"staff_id": staff_id, "window_id": window_id}
            ).fetchall()
            
            staff_slot_number = max([row[0] for row in slot_rows], default=0) + 1
            
            # Step 4 — FCFS Claim (ONLY arbiter)
            insert_result = session.execute(
                text("""
                    INSERT INTO subject_selection
                      (subject_id, staff_id, batch_id, specialization_id,
                       window_id, staff_slot_number, status, selected_at)
                    VALUES (:subject_id, :staff_id, :batch_id, :specialization_id,
                            :window_id, :staff_slot_number, 'SELECTED', now())
                    ON CONFLICT (subject_id) WHERE status = 'SELECTED'
                    DO NOTHING
                    RETURNING id
                """),
                {
                    "subject_id": subject_id,
                    "staff_id": staff_id,
                    "batch_id": batch_id,
                    "specialization_id": specialization_id,
                    "window_id": window_id,
                    "staff_slot_number": staff_slot_number
                }
            ).fetchone()
            
            if not insert_result:
                return {
                    "success": False,
                    "message": "Subject already selected",
                    "selection_id": None
                }
            
            selection_id = insert_result[0]
            
            # Step 5 — Audit Log
            session.execute(
                text("""
                    INSERT INTO audit_log
                      (actor_staff_id, action_type, subject_id, affected_staff_id, details, created_at)
                    VALUES (:actor_staff_id, 'SELECT', :subject_id, :affected_staff_id, '{}'::jsonb, now())
                """),
                {
                    "actor_staff_id": staff_id,
                    "subject_id": subject_id,
                    "affected_staff_id": staff_id
                }
            )
            
            # Explicit commit — transaction boundary
            session.commit()
            return {
                "success": True,
                "message": "Subject selected successfully",
                "selection_id": selection_id
            }
    
    except Exception as e:
        error_msg = str(e)
        
        # FSB v1.3 §3.5: Deadlock handling (SQLSTATE 40P01)
        if "40P01" in error_msg or "deadlock" in error_msg.lower():
            return {
                "success": False,
                "message": "Concurrent change detected, please try again",
                "selection_id": None
            }
        
        # Lock timeout handling (SQLSTATE 55P03)
        if "55P03" in error_msg or "lock timeout" in error_msg.lower():
            return {
                "success": False,
                "message": "Concurrent change detected, please try again",
                "selection_id": None
            }
        
        # Re-raise other exceptions for proper HTTP error mapping
        raise


def change_subject_transaction(
    staff_id: int,
    old_subject_id: int,
    new_subject_id: int,
    batch_id: int,
    specialization_id: int
) -> dict:
    """
    Execute CHANGE SUBJECT transaction per FSB_v1.3.md Section 3.6.
    
    CRITICAL: Acquires NEW subject before releasing OLD (deadlock-safe).
    CRITICAL: Reuses original staff_slot_number (does NOT recompute MAX).
    
    Returns:
        dict with keys: success (bool), message (str), selection_id (int or None)
    
    Raises:
        Exception: Re-raises database exceptions for proper HTTP error mapping
    """
    
    try:
        with get_transaction(isolation_level="READ COMMITTED") as session:
            
            # Set lock timeout per FSB v1.3 §3.5
            session.execute(text("SET LOCAL lock_timeout = '5s'"))
            
            # Step 1 — Window Validation (FOR SHARE)
            # Updated per window_lifecycle_design.md:
            # - status = 'OPEN' (replaces is_active)
            # - batch_id scoping (CRITICAL)
            # - specialization_id scoping (CRITICAL)
            # - LIMIT 1 (defensive: partial unique index guarantees at most 1 row)
            #
            # LOCK ORDERING (FROZEN):
            # 1. FOR SHARE (window validation) ← YOU ARE HERE
            # 2. pg_advisory_xact_lock(staff_id, window_id)
            # 3. FOR UPDATE (old selection row)
            # 4. UPDATE
            window_result = session.execute(
                text("""
                    SELECT id, max_subjects_per_staff
                    FROM selection_window
                    WHERE status = 'OPEN'
                      AND batch_id = :batch_id
                      AND specialization_id = :specialization_id
                      AND now() BETWEEN start_time AND end_time
                    FOR SHARE
                    LIMIT 1
                """),
                {"batch_id": batch_id, "specialization_id": specialization_id}
            ).fetchone()
            
            if not window_result:
                return {
                    "success": False,
                    "message": "Window closed",
                    "selection_id": None
                }
            
            window_id = window_result[0]
            
            # Step 1.5 — Eligibility Verification for NEW subject (FOR SHARE)
            eligibility_result = session.execute(
                text("""
                    SELECT sa.id
                    FROM staff_assignment sa
                    JOIN subject s
                      ON s.batch_id = sa.batch_id
                     AND s.specialization_id = sa.specialization_id
                    WHERE sa.staff_id = :staff_id
                      AND s.id = :subject_id
                    FOR SHARE
                """),
                {"staff_id": staff_id, "subject_id": new_subject_id}
            ).fetchone()
            
            if not eligibility_result:
                return {
                    "success": False,
                    "message": "Not eligible for new subject",
                    "selection_id": None
                }
            
            # Step 1.75a — Staff-level Advisory Lock (serializes slot computation per staff)
            session.execute(
                text("SELECT pg_advisory_xact_lock(:staff_id)"),
                {"staff_id": staff_id}
            )
            
            # Step 1.75b — Staff+Window Advisory Lock (FSB v1.3 Rule 1)
            # CHANGE transactions MUST acquire advisory lock
            session.execute(
                text("SELECT pg_advisory_xact_lock(:staff_id, :window_id)"),
                {"staff_id": staff_id, "window_id": window_id}
            )
            
            # Step 2 — Lock OLD subject row and retrieve slot number (FOR UPDATE)
            # FSB v1.3 Rule 4: MUST reuse original staff_slot_number
            old_selection = session.execute(
                text("""
                    SELECT id, staff_slot_number
                    FROM subject_selection
                    WHERE subject_id = :old_subject_id
                      AND staff_id = :staff_id
                      AND window_id = :window_id
                      AND status = 'SELECTED'
                    FOR UPDATE
                """),
                {
                    "old_subject_id": old_subject_id,
                    "staff_id": staff_id,
                    "window_id": window_id
                }
            ).fetchone()
            
            if not old_selection:
                return {
                    "success": False,
                    "message": "Old subject not found or already changed",
                    "selection_id": None
                }
            
            old_selection_id = old_selection[0]
            reused_slot_number = old_selection[1]  # Preserved immutably
            
            # Step 3 — Atomic UPDATE: swap subject_id on existing row
            # Preserves staff_slot_number immutably, no DELETE+INSERT needed
            update_count = session.execute(
                text("""
                    UPDATE subject_selection
                    SET subject_id = :new_subject_id,
                        updated_at = now()
                    WHERE id = :selection_id
                      AND status = 'SELECTED'
                """),
                {
                    "new_subject_id": new_subject_id,
                    "selection_id": old_selection_id
                }
            ).rowcount
            
            if update_count == 0:
                return {
                    "success": False,
                    "message": "Change failed unexpectedly",
                    "selection_id": None
                }
            
            # Step 4 — Audit Log
            session.execute(
                text("""
                    INSERT INTO audit_log
                      (actor_staff_id, action_type, subject_id, affected_staff_id, details, created_at)
                    VALUES (:actor_staff_id, 'CHANGE', :subject_id, :affected_staff_id, 
                            jsonb_build_object('old_subject_id', :old_subject_id, 'new_subject_id', :new_subject_id), now())
                """),
                {
                    "actor_staff_id": staff_id,
                    "subject_id": new_subject_id,
                    "affected_staff_id": staff_id,
                    "old_subject_id": old_subject_id,
                    "new_subject_id": new_subject_id
                }
            )
            
            # Explicit commit — transaction boundary
            session.commit()
            return {
                "success": True,
                "message": "Subject changed successfully",
                "selection_id": old_selection_id
            }
    
    except Exception as e:
        error_msg = str(e)
        
        # FSB v1.3 §3.6: Deadlock handling (SQLSTATE 40P01)
        if "40P01" in error_msg or "deadlock" in error_msg.lower():
            return {
                "success": False,
                "message": "Concurrent change detected, please try again",
                "selection_id": None
            }
        
        # Lock timeout handling (SQLSTATE 55P03)
        if "55P03" in error_msg or "lock timeout" in error_msg.lower():
            return {
                "success": False,
                "message": "Concurrent change detected, please try again",
                "selection_id": None
            }
        
        # Re-raise other exceptions for proper HTTP error mapping
        raise
