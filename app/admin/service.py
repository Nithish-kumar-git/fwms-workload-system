"""
Admin service for allocation review, override, reassignment, and freeze.
PHASE 3: Enhanced HOD control with strict state validation and workload management.

All operations are coordinator/HOD-only and logged to audit_log.
All SQL uses parameterized queries.
"""

from sqlalchemy import text
from app.db.session import get_transaction
import logging

logger = logging.getLogger(__name__)

# PHASE 3: Maximum overload allowed (20% above norm)
MAX_OVERLOAD_PERCENT = 0.20


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

def list_allocations() -> list[dict]:
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
                JOIN cycle c ON c.id = a.cycle_id
                JOIN academic_year ay ON ay.id = c.academic_year_id
                WHERE c.status IN ('OPEN', 'ALLOCATED', 'FROZEN')
                ORDER BY p.name, sem.label, sec.label, sub.code
            """)
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
    
    PHASE 3 Enhancements:
    - Validates semester state (must be ALLOCATED, not FROZEN)
    - Respects 20% overload limit
    - Updates workload_summary immediately
    - Logs detailed before/after state
    
    Validates shift compatibility, workload capacity (≤ 20% overload), and multi-section.
    """
    with get_transaction() as session:
        # PHASE 3: Check cycle status - must be ALLOCATED, not FROZEN
        alloc_cycle_state = session.execute(
            text("""
                SELECT c.id, c.status
                FROM allocation a
                JOIN cycle c ON c.id = a.cycle_id
                WHERE a.id = :aid
            """),
            {"aid": allocation_id}
        ).fetchone()
        
        if not alloc_cycle_state:
            return {"success": False, "message": "Allocation not found"}
        
        cycle_id_check, cycle_status = alloc_cycle_state
        
        if cycle_status == "FROZEN":
            return {
                "success": False,
                "message": "Cannot override allocation: Cycle is FROZEN (finalized by HOD)"
            }
        
        if cycle_status not in ("OPEN", "ALLOCATED"):
            return {
                "success": False,
                "message": f"Cannot override allocation: Cycle must be OPEN or ALLOCATED (currently {cycle_status})"
            }
        
        # Load existing allocation with full details
        alloc = session.execute(
            text("""
                SELECT a.id, a.staff_id, a.subject_offering_id, a.cycle_id,
                       so.shift, ay.name, s.label AS semester_name,
                       sub.code, sub.name, sub.tch,
                       sub.l, sub.t, sub.p,
                       old_staff.name AS old_staff_name, old_staff.emp_code AS old_emp_code
                FROM allocation a
                JOIN subject_offering so ON so.id = a.subject_offering_id
                JOIN subject sub ON sub.id = so.subject_id
                JOIN staff old_staff ON old_staff.id = a.staff_id
                JOIN cycle c ON c.id = a.cycle_id
                JOIN academic_year ay ON ay.id = c.academic_year_id
                JOIN semester s ON s.id = c.semester_id
                WHERE a.id = :aid
            """),
            {"aid": allocation_id}
        ).fetchone()
        
        if alloc is None:
            return {"success": False, "message": "Allocation not found"}
        
        old_staff_id = alloc[1]
        offering_id = alloc[2]
        cycle_id = alloc[3]
        offering_shift = alloc[4]
        academic_year = alloc[5]
        semester_name = alloc[6]
        course_code = alloc[7]
        course_name = alloc[8]
        offer_tch = alloc[9] or 0
        old_staff_name = alloc[12]
        old_emp_code = alloc[13]
        
        if old_staff_id == new_staff_id:
            return {"success": False, "message": "New staff is the same as current staff"}
        
        # Log the staff ID we're looking up for debugging
        logger.info(f"Override: looking up new staff id={new_staff_id}")
        print(f"OVERRIDE: querying staff id={new_staff_id} type={type(new_staff_id)}", flush=True)
        
        # Load new staff with full details (with fallback values for missing columns)
        new_staff = session.execute(
            text("""
                SELECT id, name, emp_code, COALESCE(shift, 'SHIFT1') as shift, COALESCE(tch_norm, 16) AS tch_norm
                FROM staff WHERE id = :sid
            """),
            {"sid": new_staff_id}
        ).fetchone()
        
        if new_staff is None:
            logger.error(f"Override failed: staff id={new_staff_id} not found in database")
            print(f"OVERRIDE: staff id={new_staff_id} NOT FOUND in database", flush=True)
            return {"success": False, "message": f"Staff with id={new_staff_id} not found in database"}
        
        new_staff_name = new_staff[1]
        new_emp_code = new_staff[2]
        new_staff_shift = new_staff[3]
        new_staff_norm = new_staff[4]
        
        # VALIDATE: Shift compatibility
        if not _is_shift_compatible(new_staff_shift, offering_shift):
            return {"success": False, "message": "Shift incompatible: Faculty shift does not match subject offering shift"}
        
        # VALIDATE: Workload capacity with 20% overload limit
        current_tch = session.execute(
            text("""
                SELECT COALESCE(SUM(sub.tch), 0)
                FROM allocation a
                JOIN subject_offering so ON so.id = a.subject_offering_id
                JOIN subject sub ON sub.id = so.subject_id
                WHERE a.staff_id = :sid AND a.cycle_id = :cid
            """),
            {"sid": new_staff_id, "cid": cycle_id}
        ).scalar()
        
        max_allowed = new_staff_norm * (1.0 + MAX_OVERLOAD_PERCENT)
        new_total = current_tch + offer_tch
        
        if new_total > max_allowed:
            overload_pct = ((new_total - new_staff_norm) / new_staff_norm) * 100
            return {
                "success": False,
                "message": (
                    f"Would exceed 20% overload limit: "
                    f"{new_total} TCH > {max_allowed} TCH (norm: {new_staff_norm}, "
                    f"would be {overload_pct:.1f}% overloaded)"
                )
            }
        
        # VALIDATE: Multi-section constraint
        has_same_course = session.execute(
            text("""
                SELECT count(*) FROM allocation a
                JOIN subject_offering so ON so.id = a.subject_offering_id
                JOIN subject sub ON sub.id = so.subject_id
                WHERE a.staff_id = :sid AND sub.code = :code 
                  AND a.id != :aid AND a.cycle_id = :cid
            """),
            {"sid": new_staff_id, "code": course_code, "aid": allocation_id, "cid": cycle_id}
        ).scalar()
        
        if has_same_course > 0:
            return {"success": False, "message": f"Faculty already teaches {course_code} in another section"}
        
        # Perform override
        session.execute(
            text("UPDATE allocation SET staff_id = :new_sid WHERE id = :aid"),
            {"new_sid": new_staff_id, "aid": allocation_id}
        )
        
        # PHASE 3: Update workload_summary for both faculty immediately
        _refresh_workload_summary_for_cycle(session, old_staff_id, cycle_id, academic_year, semester_name)
        _refresh_workload_summary_for_cycle(session, new_staff_id, cycle_id, academic_year, semester_name)
        
        # PHASE 3: Enhanced audit log with before/after details
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'ALLOCATION_OVERRIDE', :details)
            """),
            {
                "actor": actor_id,
                "details": (
                    f'{{"allocation_id": {allocation_id}, '
                    f'"subject_offering_id": {offering_id}, '
                    f'"subject_code": "{course_code}", '
                    f'"subject_name": "{course_name}", '
                    f'"tch": {offer_tch}, '
                    f'"old_staff_id": {old_staff_id}, '
                    f'"old_staff_name": "{old_staff_name}", '
                    f'"old_emp_code": "{old_emp_code}", '
                    f'"new_staff_id": {new_staff_id}, '
                    f'"new_staff_name": "{new_staff_name}", '
                    f'"new_emp_code": "{new_emp_code}", '
                    f'"cycle_id": {cycle_id}}}'
                )
            }
        )
        
        session.commit()
        
        logger.info(
            f"Override: allocation {allocation_id} ({course_code}) "
            f"reassigned {old_staff_name} → {new_staff_name} by actor {actor_id}"
        )
    
    return {
        "success": True,
        "message": f"Successfully reassigned {course_code} from {old_staff_name} to {new_staff_name}",
        "allocation_id": allocation_id,
        "old_staff_id": old_staff_id,
        "old_staff_name": old_staff_name,
        "new_staff_id": new_staff_id,
        "new_staff_name": new_staff_name,
        "subject_code": course_code,
        "tch": offer_tch,
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
    
    PHASE 3 Enhancements:
    - Validates semester state (must be ALLOCATED, not FROZEN)
    - Respects 20% overload limit
    - Updates workload_summary immediately for both faculty
    - Logs detailed before/after state
    
    Deletes old allocation, creates new one, updates workload_summary atomically.
    """
    with get_transaction() as session:
        # PHASE 3: Check semester state - must be ALLOCATED, not FROZEN
        offering_semester_state = session.execute(
            text("""
                SELECT sem.id, sem.state
                FROM subject_offering so
                JOIN semester sem ON sem.id = so.semester_id
                WHERE so.id = :oid
            """),
            {"oid": subject_offering_id}
        ).fetchone()
        
        if not offering_semester_state:
            return {"success": False, "message": "Subject offering not found"}
        
        semester_id, semester_state = offering_semester_state
        
        if semester_state == "FROZEN":
            return {
                "success": False,
                "message": "Cannot reassign subject: Semester is FROZEN (finalized by HOD)"
            }
        
        if semester_state != "ALLOCATED":
            return {
                "success": False,
                "message": f"Cannot reassign subject: Semester must be ALLOCATED (currently {semester_state})"
            }
        
        # Find existing allocation with full details
        alloc = session.execute(
            text("""
                SELECT a.id, a.cycle_id,
                       so.shift, c.academic_year, s.label AS semester_name,
                       sub.code, sub.name, sub.tch, sub.l, sub.t, sub.p,
                       from_staff.name AS from_staff_name, from_staff.emp_code AS from_emp_code
                FROM allocation a
                JOIN subject_offering so ON so.id = a.subject_offering_id
                JOIN subject sub ON sub.id = so.subject_id
                JOIN staff from_staff ON from_staff.id = a.staff_id
                JOIN cycle c ON c.id = a.cycle_id
                JOIN semester s ON s.id = c.semester_id
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
        cycle_id = alloc[1]
        offering_shift = alloc[2]
        academic_year = alloc[3]
        semester_name = alloc[4]
        course_code = alloc[5]
        course_name = alloc[6]
        offer_tch = alloc[7] or 0
        l_val, t_val, p_val = alloc[8] or 0, alloc[9] or 0, alloc[10] or 0
        from_staff_name = alloc[11]
        from_emp_code = alloc[12]
        
        # Load target staff with full details
        to_staff = session.execute(
            text("""
                SELECT id, name, emp_code, shift, COALESCE(tch_norm, 40) AS tch_norm
                FROM staff WHERE id = :sid AND is_active = true
            """),
            {"sid": to_staff_id}
        ).fetchone()
        
        if to_staff is None:
            return {"success": False, "message": "Target staff not found or inactive"}
        
        to_staff_name = to_staff[1]
        to_emp_code = to_staff[2]
        to_staff_shift = to_staff[3]
        to_staff_norm = to_staff[4]
        
        # VALIDATE: Shift compatibility
        if not _is_shift_compatible(to_staff_shift, offering_shift):
            return {"success": False, "message": "Shift incompatible: Faculty shift does not match subject offering shift"}
        
        # VALIDATE: Workload capacity with 20% overload limit
        current_tch = session.execute(
            text("""
                SELECT COALESCE(SUM(sub.tch), 0)
                FROM allocation a
                JOIN subject_offering so ON so.id = a.subject_offering_id
                JOIN subject sub ON sub.id = so.subject_id
                WHERE a.staff_id = :sid AND a.cycle_id = :cid
            """),
            {"sid": to_staff_id, "cid": cycle_id}
        ).scalar()
        
        max_allowed = to_staff_norm * (1.0 + MAX_OVERLOAD_PERCENT)
        new_total = current_tch + offer_tch
        
        if new_total > max_allowed:
            overload_pct = ((new_total - to_staff_norm) / to_staff_norm) * 100
            return {
                "success": False,
                "message": (
                    f"Would exceed 20% overload limit: "
                    f"{new_total} TCH > {max_allowed} TCH (norm: {to_staff_norm}, "
                    f"would be {overload_pct:.1f}% overloaded)"
                )
            }
        
        # VALIDATE: Multi-section
        has_same = session.execute(
            text("""
                SELECT count(*) FROM allocation a
                JOIN subject_offering so ON so.id = a.subject_offering_id
                JOIN subject sub ON sub.id = so.subject_id
                WHERE a.staff_id = :sid AND sub.code = :code AND a.cycle_id = :cid
            """),
            {"sid": to_staff_id, "code": course_code, "cid": cycle_id}
        ).scalar()
        
        if has_same > 0:
            return {"success": False, "message": f"Target faculty already teaches {course_code} in another section"}
        
        # Delete old allocation
        session.execute(
            text("DELETE FROM allocation WHERE id = :aid"),
            {"aid": alloc_id}
        )
        
        # Create new allocation
        new_alloc = session.execute(
            text("""
                INSERT INTO allocation 
                    (staff_id, subject_offering_id, l_assigned, t_assigned, p_assigned, cycle_id)
                VALUES (:sid, :oid, :l, :t, :p, :cid)
                RETURNING id
            """),
            {"sid": to_staff_id, "oid": subject_offering_id, "l": l_val, "t": t_val, "p": p_val, "cid": cycle_id}
        )
        new_alloc_id = new_alloc.scalar()
        
        # PHASE 3: Update workload_summary for both faculty immediately
        _refresh_workload_summary_for_cycle(session, from_staff_id, cycle_id, academic_year, semester_name)
        _refresh_workload_summary_for_cycle(session, to_staff_id, cycle_id, academic_year, semester_name)
        
        # PHASE 3: Enhanced audit log with before/after details
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'ALLOCATION_REASSIGN', :details)
            """),
            {
                "actor": actor_id,
                "details": (
                    f'{{"subject_offering_id": {subject_offering_id}, '
                    f'"subject_code": "{course_code}", '
                    f'"subject_name": "{course_name}", '
                    f'"tch": {offer_tch}, '
                    f'"from_staff_id": {from_staff_id}, '
                    f'"from_staff_name": "{from_staff_name}", '
                    f'"from_emp_code": "{from_emp_code}", '
                    f'"to_staff_id": {to_staff_id}, '
                    f'"to_staff_name": "{to_staff_name}", '
                    f'"to_emp_code": "{to_emp_code}", '
                    f'"new_allocation_id": {new_alloc_id}, '
                    f'"semester_id": {semester_id}}}'
                )
            }
        )
        
        session.commit()
        
        logger.info(
            f"Reassign: {course_code} moved from {from_staff_name} → {to_staff_name} by actor {actor_id}"
        )
    
    return {
        "success": True,
        "message": f"Successfully reassigned {course_code} from {from_staff_name} to {to_staff_name}",
        "allocation_id": new_alloc_id,
        "from_staff_id": from_staff_id,
        "from_staff_name": from_staff_name,
        "to_staff_id": to_staff_id,
        "to_staff_name": to_staff_name,
        "subject_code": course_code,
        "tch": offer_tch,
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
    """
    Check if allocation is locked.
    
    PHASE 2: Checks both:
    - Legacy: selection_window.allocation_locked = true
    - New: Any semester in FROZEN state
    """
    # Check legacy selection window lock
    legacy_locked = session.execute(
        text("SELECT count(*) FROM selection_window WHERE allocation_locked = true")
    ).scalar()
    
    if legacy_locked > 0:
        return True
    
    # PHASE 2: Check if any semester is FROZEN
    frozen_count = session.execute(
        text("SELECT count(*) FROM semester WHERE state = 'FROZEN'")
    ).scalar()
    
    return frozen_count > 0


# ============================================================================
# STEP 7: Workload Summary
# ============================================================================

def get_workload_summary(
    academic_year: str | None = None, semester_id: int | None = None
) -> dict:
    """
    Get workload summary for all faculty with allocations.
    If academic_year and semester_id not provided, uses active cycle.
    """
    # Resolve from active cycle if not provided
    if academic_year is None or semester_id is None:
        from app.admin.cycle_service_new import get_active_cycle
        active_cycle = get_active_cycle()
        if active_cycle is None:
            return {
                "total_faculty": 0,
                "overloaded": 0,
                "underloaded": 0,
                "balanced": 0,
                "records": [],
            }
        academic_year = active_cycle["academic_year"]
        semester_id = active_cycle["semester_id"]
    
    with get_transaction() as session:
        rows = session.execute(
            text("""
                SELECT s.id, s.emp_code, s.name, s.designation,
                       COALESCE(s.tch_norm, 40) AS tch_norm,
                       COALESCE(ws.tch_total, 0) AS tch_assigned,
                       COALESCE(ws.deviation_hours, 0) AS deviation,
                       COALESCE(ws.total_workload, 0) AS total_workload
                FROM staff s
                LEFT JOIN workload_summary ws ON ws.staff_id = s.id
                    AND ws.academic_year = :year
                    AND ws.semester_id = :sem_id
                WHERE s.emp_code IS NOT NULL AND s.is_active = true
                ORDER BY s.designation, s.name
            """),
            {"year": academic_year, "sem_id": semester_id}
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
# Helper: Refresh workload_summary for a single faculty member (cycle-aware)
# ============================================================================

def _refresh_workload_summary_for_cycle(
    session, staff_id: int, cycle_id: int,
    academic_year: str, semester_name: str
):
    """
    Recalculate and upsert workload_summary for one faculty member.
    
    PHASE 3: Cycle-aware - computes workload from ALL allocations in the cycle.
    This ensures workload reflects all allocated semesters, not just one.
    """
    # Compute total TCH from ALL allocations in this cycle
    tch_total = session.execute(
        text("""
            SELECT COALESCE(SUM(sub.tch), 0)
            FROM allocation a
            JOIN subject_offering so ON so.id = a.subject_offering_id
            JOIN subject sub ON sub.id = so.subject_id
            WHERE a.staff_id = :sid AND a.cycle_id = :cid
        """),
        {"sid": staff_id, "cid": cycle_id}
    ).scalar()
    
    tch_norm = session.execute(
        text("SELECT COALESCE(tch_norm, 40) FROM staff WHERE id = :sid"),
        {"sid": staff_id}
    ).scalar()
    
    deviation = tch_total - tch_norm
    
    # Get semester_id from cycle and convert to semester_type
    semester_id = session.execute(
        text("SELECT semester_id FROM cycle WHERE id = :cid"),
        {"cid": cycle_id}
    ).scalar()
    
    # Convert semester_id to semester_type (ODD: 1,3,5 / EVEN: 2,4,6)
    semester_type = "ODD" if semester_id in (1, 3, 5) else "EVEN"
    
    # UPSERT workload_summary
    session.execute(
        text("""
            INSERT INTO workload_summary 
                (staff_id, academic_year, semester_type, tch_total,
                 norm_hours, deviation_hours, total_workload, cycle_id, old_academic_cycle_id)
            VALUES (:sid, :year, :sem_type, :tch_total,
                    :norm, :deviation, :tch_total, :cid, :cid)
            ON CONFLICT (staff_id, academic_year, semester_type)
            DO UPDATE SET 
                tch_total = EXCLUDED.tch_total,
                norm_hours = EXCLUDED.norm_hours,
                deviation_hours = EXCLUDED.deviation_hours,
                total_workload = EXCLUDED.total_workload,
                cycle_id = EXCLUDED.cycle_id,
                updated_at = now()
        """),
        {
            "sid": staff_id, "year": academic_year,
            "sem_type": semester_type, "tch_total": tch_total,
            "norm": tch_norm, "deviation": deviation, "cid": cycle_id,
        }
    )
    
    logger.debug(f"Refreshed workload for staff {staff_id}: {tch_total} TCH (norm: {tch_norm}, deviation: {deviation})")
