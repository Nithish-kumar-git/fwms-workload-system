"""
Admin service for allocation review, override, reassignment, and freeze.
Spec reference: final_system_specification.md (Admin Override System)

All operations are coordinator-only and logged to audit_log.
All SQL uses parameterized queries.
"""

from sqlalchemy import text
from app.db.session import get_transaction
import logging

logger = logging.getLogger(__name__)


def _is_shift_compatible(staff_shift: str, offering_shift: int) -> bool:
    """Check shift compatibility (reused from allocation service)."""
    if not staff_shift or not offering_shift:
        return True
    s = str(staff_shift).upper().strip()
    if "SHIFT1+SHIFT2" in s or "BOTH" in s:
        return True
    if "2" in s and offering_shift == 1:
        return False
    if "1" in s and offering_shift == 2:
        return False
    return True


# ============================================================================
# STEP 1: Allocation Review
# ============================================================================

def list_allocations(academic_year: str = "2025-2026", semester_type: str = "EVEN") -> list[dict]:
    """
    List all allocations with full staff + subject details.
    """
    with get_transaction() as session:
        rows = session.execute(
            text("""
                SELECT a.id, a.staff_id, s.name, s.emp_code, s.designation,
                       a.subject_offering_id, sub.code, sub.name,
                       sec.label AS section_label, sem.label AS semester_label,
                       p.name AS program_name,
                       a.l_assigned, a.t_assigned, a.p_assigned, a.ltp_total,
                       a.allocated_at
                FROM allocation a
                JOIN staff s ON s.id = a.staff_id
                JOIN subject_offering so ON so.id = a.subject_offering_id
                JOIN subject sub ON sub.id = so.subject_id
                JOIN section sec ON sec.id = so.section_id
                JOIN semester sem ON sem.id = so.semester_id
                JOIN program p ON p.id = so.program_id
                WHERE so.academic_year = :year AND so.semester_type = :sem_type
                ORDER BY p.name, sem.label, sec.label, sub.code
            """),
            {"year": academic_year, "sem_type": semester_type}
        ).fetchall()
    
    return [
        {
            "allocation_id": r[0], "staff_id": r[1], "staff_name": r[2],
            "emp_code": r[3], "designation": r[4],
            "subject_offering_id": r[5], "subject_code": r[6],
            "subject_name": r[7], "section_label": r[8],
            "semester_label": r[9], "program_name": r[10],
            "l_assigned": r[11], "t_assigned": r[12],
            "p_assigned": r[13], "ltp_total": r[14],
            "allocated_at": r[15],
        }
        for r in rows
    ]


# ============================================================================
# STEP 2: Manual Override — reassign allocation to different faculty
# ============================================================================

def override_allocation(allocation_id: int, new_staff_id: int, actor_id: int) -> dict:
    """
    Override an allocation: change the assigned staff.
    Validates shift compatibility, workload capacity, and multi-section.
    """
    with get_transaction() as session:
        # Check frozen
        if _is_allocation_locked(session):
            return {"success": False, "message": "Allocation is frozen. Unfreeze before making changes."}
        
        # Load existing allocation
        alloc = session.execute(
            text("""
                SELECT a.id, a.staff_id, a.subject_offering_id,
                       so.shift, sub.code, sub.tch,
                       sub.l, sub.t, sub.p
                FROM allocation a
                JOIN subject_offering so ON so.id = a.subject_offering_id
                JOIN subject sub ON sub.id = so.subject_id
                WHERE a.id = :aid
            """),
            {"aid": allocation_id}
        ).fetchone()
        
        if alloc is None:
            return {"success": False, "message": "Allocation not found"}
        
        old_staff_id = alloc[1]
        offering_id = alloc[2]
        offering_shift = alloc[3]
        course_code = alloc[4]
        offer_tch = alloc[5] or 0
        
        if old_staff_id == new_staff_id:
            return {"success": False, "message": "New staff is the same as current staff"}
        
        # Load new staff
        new_staff = session.execute(
            text("""
                SELECT id, shift, COALESCE(tch_norm, 16) AS tch_norm
                FROM staff WHERE id = :sid AND is_active = true
            """),
            {"sid": new_staff_id}
        ).fetchone()
        
        if new_staff is None:
            return {"success": False, "message": "New staff not found or inactive"}
        
        # VALIDATE: Shift compatibility
        if not _is_shift_compatible(new_staff[1], offering_shift):
            return {"success": False, "message": "Shift incompatible"}
        
        # VALIDATE: Workload capacity
        current_tch = session.execute(
            text("""
                SELECT COALESCE(SUM(sub.tch), 0)
                FROM allocation a
                JOIN subject_offering so ON so.id = a.subject_offering_id
                JOIN subject sub ON sub.id = so.subject_id
                WHERE a.staff_id = :sid
            """),
            {"sid": new_staff_id}
        ).scalar()
        
        if current_tch + offer_tch > new_staff[2]:
            return {
                "success": False,
                "message": f"Would exceed workload norm ({current_tch} + {offer_tch} > {new_staff[2]})"
            }
        
        # VALIDATE: Multi-section constraint
        has_same_course = session.execute(
            text("""
                SELECT count(*) FROM allocation a
                JOIN subject_offering so ON so.id = a.subject_offering_id
                JOIN subject sub ON sub.id = so.subject_id
                WHERE a.staff_id = :sid AND sub.code = :code AND a.id != :aid
            """),
            {"sid": new_staff_id, "code": course_code, "aid": allocation_id}
        ).scalar()
        
        if has_same_course > 0:
            return {"success": False, "message": "Faculty already teaches this course in another section"}
        
        # Perform override
        session.execute(
            text("UPDATE allocation SET staff_id = :new_sid WHERE id = :aid"),
            {"new_sid": new_staff_id, "aid": allocation_id}
        )
        
        # Audit log
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'ALLOCATION_OVERRIDE', :details)
            """),
            {
                "actor": actor_id,
                "details": (
                    f'{{"allocation_id": {allocation_id}, '
                    f'"old_staff_id": {old_staff_id}, '
                    f'"new_staff_id": {new_staff_id}, '
                    f'"subject_offering_id": {offering_id}}}'
                )
            }
        )
        
        session.commit()
        
        logger.info(
            f"Override: allocation {allocation_id} "
            f"reassigned {old_staff_id} → {new_staff_id}"
        )
    
    return {
        "success": True,
        "message": "Allocation overridden successfully",
        "allocation_id": allocation_id,
        "old_staff_id": old_staff_id,
        "new_staff_id": new_staff_id,
    }


# ============================================================================
# STEP 3: Subject Reassignment
# ============================================================================

def reassign_subject(
    subject_offering_id: int, from_staff_id: int, 
    to_staff_id: int, actor_id: int
) -> dict:
    """
    Move a subject offering from one faculty to another.
    Deletes old allocation, creates new one, updates workload_summary.
    """
    with get_transaction() as session:
        # Check frozen
        if _is_allocation_locked(session):
            return {"success": False, "message": "Allocation is frozen."}
        
        # Find existing allocation
        alloc = session.execute(
            text("""
                SELECT a.id, so.shift, sub.code, sub.tch, sub.l, sub.t, sub.p
                FROM allocation a
                JOIN subject_offering so ON so.id = a.subject_offering_id
                JOIN subject sub ON sub.id = so.subject_id
                WHERE a.staff_id = :from_sid AND a.subject_offering_id = :oid
            """),
            {"from_sid": from_staff_id, "oid": subject_offering_id}
        ).fetchone()
        
        if alloc is None:
            return {
                "success": False,
                "message": "No allocation found for this staff + subject offering"
            }
        
        alloc_id = alloc[0]
        offering_shift = alloc[1]
        course_code = alloc[2]
        offer_tch = alloc[3] or 0
        l_val, t_val, p_val = alloc[4] or 0, alloc[5] or 0, alloc[6] or 0
        
        # Load target staff
        to_staff = session.execute(
            text("""
                SELECT id, shift, COALESCE(tch_norm, 16) AS tch_norm
                FROM staff WHERE id = :sid AND is_active = true
            """),
            {"sid": to_staff_id}
        ).fetchone()
        
        if to_staff is None:
            return {"success": False, "message": "Target staff not found or inactive"}
        
        # VALIDATE: Shift compatibility
        if not _is_shift_compatible(to_staff[1], offering_shift):
            return {"success": False, "message": "Shift incompatible"}
        
        # VALIDATE: Workload capacity
        current_tch = session.execute(
            text("""
                SELECT COALESCE(SUM(sub.tch), 0)
                FROM allocation a
                JOIN subject_offering so ON so.id = a.subject_offering_id
                JOIN subject sub ON sub.id = so.subject_id
                WHERE a.staff_id = :sid
            """),
            {"sid": to_staff_id}
        ).scalar()
        
        if current_tch + offer_tch > to_staff[2]:
            return {
                "success": False,
                "message": f"Would exceed workload norm ({current_tch} + {offer_tch} > {to_staff[2]})"
            }
        
        # VALIDATE: Multi-section
        has_same = session.execute(
            text("""
                SELECT count(*) FROM allocation a
                JOIN subject_offering so ON so.id = a.subject_offering_id
                JOIN subject sub ON sub.id = so.subject_id
                WHERE a.staff_id = :sid AND sub.code = :code
            """),
            {"sid": to_staff_id, "code": course_code}
        ).scalar()
        
        if has_same > 0:
            return {"success": False, "message": "Target faculty already teaches this course"}
        
        # Delete old allocation
        session.execute(
            text("DELETE FROM allocation WHERE id = :aid"),
            {"aid": alloc_id}
        )
        
        # Create new allocation
        new_alloc = session.execute(
            text("""
                INSERT INTO allocation 
                    (staff_id, subject_offering_id, l_assigned, t_assigned, p_assigned)
                VALUES (:sid, :oid, :l, :t, :p)
                RETURNING id
            """),
            {"sid": to_staff_id, "oid": subject_offering_id, "l": l_val, "t": t_val, "p": p_val}
        )
        new_alloc_id = new_alloc.scalar()
        
        # Update workload_summary for both faculty
        _refresh_workload_summary(session, from_staff_id)
        _refresh_workload_summary(session, to_staff_id)
        
        # Audit log
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'ALLOCATION_REASSIGN', :details)
            """),
            {
                "actor": actor_id,
                "details": (
                    f'{{"subject_offering_id": {subject_offering_id}, '
                    f'"from_staff_id": {from_staff_id}, '
                    f'"to_staff_id": {to_staff_id}, '
                    f'"new_allocation_id": {new_alloc_id}}}'
                )
            }
        )
        
        session.commit()
        
        logger.info(
            f"Reassign: offering {subject_offering_id} "
            f"moved {from_staff_id} → {to_staff_id}"
        )
    
    return {
        "success": True,
        "message": "Subject reassigned successfully",
        "allocation_id": new_alloc_id,
    }


# ============================================================================
# STEP 4-5: Freeze / Unfreeze
# ============================================================================

def freeze_allocation(actor_id: int) -> dict:
    """Lock all allocations — prevent preference submission and re-runs."""
    with get_transaction() as session:
        session.execute(
            text("UPDATE selection_window SET allocation_locked = true WHERE allocation_locked = false")
        )
        
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'ALLOCATION_FREEZE', '{"action": "freeze"}')
            """),
            {"actor": actor_id}
        )
        
        session.commit()
    
    logger.info(f"Allocation frozen by staff_id={actor_id}")
    return {"success": True, "message": "Allocation frozen", "allocation_locked": True}


def unfreeze_allocation(actor_id: int) -> dict:
    """Unlock allocations — emergency override."""
    with get_transaction() as session:
        session.execute(
            text("UPDATE selection_window SET allocation_locked = false WHERE allocation_locked = true")
        )
        
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'ALLOCATION_UNFREEZE', '{"action": "unfreeze"}')
            """),
            {"actor": actor_id}
        )
        
        session.commit()
    
    logger.info(f"Allocation unfrozen by staff_id={actor_id}")
    return {"success": True, "message": "Allocation unfrozen", "allocation_locked": False}


def _is_allocation_locked(session) -> bool:
    """Check if any selection window has allocation_locked = true."""
    result = session.execute(
        text("SELECT count(*) FROM selection_window WHERE allocation_locked = true")
    ).scalar()
    return result > 0


# ============================================================================
# STEP 7: Workload Summary
# ============================================================================

def get_workload_summary(
    academic_year: str = "2025-2026", semester_type: str = "EVEN"
) -> dict:
    """
    Get workload summary for all faculty with allocations.
    """
    with get_transaction() as session:
        rows = session.execute(
            text("""
                SELECT s.id, s.emp_code, s.name, s.designation,
                       COALESCE(s.tch_norm, 16) AS tch_norm,
                       COALESCE(ws.tch_total, 0) AS tch_assigned,
                       COALESCE(ws.deviation_hours, 0) AS deviation,
                       COALESCE(ws.total_workload, 0) AS total_workload
                FROM staff s
                LEFT JOIN workload_summary ws ON ws.staff_id = s.id
                    AND ws.academic_year = :year
                    AND ws.semester_type = :sem_type
                WHERE s.emp_code IS NOT NULL AND s.is_active = true
                ORDER BY s.designation, s.name
            """),
            {"year": academic_year, "sem_type": semester_type}
        ).fetchall()
    
    records = []
    overloaded = 0
    underloaded = 0
    balanced = 0
    
    for r in rows:
        tch_norm = r[4]
        tch_assigned = r[5]
        deviation = r[6]
        
        if deviation > 0:
            status = "OVERLOADED"
            overloaded += 1
        elif deviation < -2:
            status = "UNDERLOADED"
            underloaded += 1
        else:
            status = "BALANCED"
            balanced += 1
        
        records.append({
            "staff_id": r[0], "emp_code": r[1], "name": r[2],
            "designation": r[3], "tch_norm": tch_norm,
            "tch_assigned": tch_assigned, "deviation": deviation,
            "total_workload": r[7], "status": status,
        })
    
    return {
        "total_faculty": len(records),
        "overloaded": overloaded,
        "underloaded": underloaded,
        "balanced": balanced,
        "records": records,
    }


# ============================================================================
# Helper: Refresh workload_summary for a single faculty member
# ============================================================================

def _refresh_workload_summary(
    session, staff_id: int,
    academic_year: str = "2025-2026", semester_type: str = "EVEN"
):
    """Recalculate and upsert workload_summary for one faculty member."""
    tch_total = session.execute(
        text("""
            SELECT COALESCE(SUM(sub.tch), 0)
            FROM allocation a
            JOIN subject_offering so ON so.id = a.subject_offering_id
            JOIN subject sub ON sub.id = so.subject_id
            WHERE a.staff_id = :sid
              AND so.academic_year = :year
              AND so.semester_type = :sem_type
        """),
        {"sid": staff_id, "year": academic_year, "sem_type": semester_type}
    ).scalar()
    
    tch_norm = session.execute(
        text("SELECT COALESCE(tch_norm, 16) FROM staff WHERE id = :sid"),
        {"sid": staff_id}
    ).scalar()
    
    deviation = tch_total - tch_norm
    
    session.execute(
        text("""
            INSERT INTO workload_summary 
                (staff_id, academic_year, semester_type, tch_total,
                 norm_hours, deviation_hours, total_workload)
            VALUES (:sid, :year, :sem_type, :tch_total,
                    :norm, :deviation, :tch_total)
            ON CONFLICT (staff_id, academic_year, semester_type)
            DO UPDATE SET 
                tch_total = EXCLUDED.tch_total,
                norm_hours = EXCLUDED.norm_hours,
                deviation_hours = EXCLUDED.deviation_hours,
                total_workload = EXCLUDED.total_workload,
                updated_at = now()
        """),
        {
            "sid": staff_id, "year": academic_year,
            "sem_type": semester_type, "tch_total": tch_total,
            "norm": tch_norm, "deviation": deviation,
        }
    )
