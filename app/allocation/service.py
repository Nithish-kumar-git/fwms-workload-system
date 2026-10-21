"""
Allocation engine — automatic subject-to-faculty assignment.
Spec reference: final_system_specification.md Section 2 (Category B)

This module implements the complete allocation pipeline:
  1. Load input data (staff, preferences, offerings)
  2. Compute remaining capacity per faculty
  3. Stage 1: Process preference_number = 1 (highest priority)
  4. Stage 2: Process preference_number = 2, 3, 4, 5
  5. Workload constraint: tch_assigned + offering.tch ≤ tch_norm
  6. Multi-section constraint: prevent same course to same faculty > 1 section
  7. Final pass: assign unallocated subjects to lowest-load compatible faculty
  8. Persist allocations and update workload_summary

All SQL uses parameterized queries. All mutations happen in a single transaction.
"""

from contextlib import nullcontext
from sqlalchemy import text
from app.db.session import get_transaction
import logging

logger = logging.getLogger(__name__)


def _is_shift_compatible(staff_shift: str, offering_shift: int, relaxed: bool = False) -> bool:
    """Check if a faculty member's shift allows teaching this offering.
    
    Args:
        staff_shift: Faculty shift designation (SHIFT1, SHIFT2, SHIFT1+SHIFT2, etc.)
        offering_shift: Offering shift (1 or 2)
        relaxed: If True, allow SHIFT2 faculty to teach SHIFT1 (FINAL_PASS only)
    """
    if not staff_shift or not offering_shift:
        return True  # No constraint if data missing
    
    s = str(staff_shift).upper().strip()
    
    # SHIFT1+SHIFT2 or BOTH → always compatible
    if "SHIFT1+SHIFT2" in s or "BOTH" in s:
        return True
    
    # RELAXED MODE (FINAL_PASS): Allow SHIFT2 faculty to teach SHIFT1
    if relaxed and "2" in s and offering_shift == 1:
        return True  # SHIFT2 faculty CAN teach SHIFT1 in final pass
    
    if "2" in s and offering_shift == 1:
        return False  # SHIFT2 faculty cannot teach SHIFT1 (strict mode)
    if "1" in s and offering_shift == 2:
        return False  # SHIFT1 faculty cannot teach SHIFT2
    
    return True


def _run_allocation_for_semester(
    cycle_id: int,
    academic_year: str,
    semester_type: str,
    semester_id: int,
    semester_label: str,
    semester_capacity: dict,
    program_id: int | None = None,
    *, session,
) -> dict:
    """
    Run allocation for a single semester.
    
    PHASE 1: Single-semester allocation only.
    - Processes ONE semester at a time
    - No cross-semester capacity tracking
    - Workload calculated within this semester only
    
    Args:
        semester_capacity: Single-semester capacity tracker
            {staff_id: {"tch_norm": X, "tch_assigned": 0 (fresh for this semester)}}
    
    Returns:
        dict with allocations, unallocated, total, assigned, unassigned counts
    """
    allocations = []
    unallocated = []
    
    with nullcontext(session):
        # ================================================================
        # STEP 1: Load staff data (fresh capacity for this semester)
        # ================================================================
        staff_rows = session.execute(
            text("""
                SELECT s.id, s.name, s.emp_code,
                       COALESCE(NULLIF(TRIM(s.designation), ''), 'Assistant Professor') AS designation,
                       s.shift,
                       COALESCE(s.tch_norm, 40) AS tch_norm,
                       s.is_class_teacher, s.ct_program, s.ct_section,
                       s.ct_semester, s.ct_shift
                FROM staff s
                WHERE s.is_active = true AND s.emp_code IS NOT NULL
                ORDER BY s.id
            """)
        ).fetchall()
        
        # Build staff lookup: {staff_id: staff_dict}
        staff_map = {}
        for r in staff_rows:
            staff_id = r[0]
            staff_map[staff_id] = {
                "id": staff_id, "name": r[1], "emp_code": r[2],
                "designation": r[3], "shift": r[4], 
                "tch_norm": semester_capacity[staff_id]["tch_norm"],
                "tch_assigned": semester_capacity[staff_id]["tch_assigned"],  # Fresh for this semester
                "is_class_teacher": r[6], "ct_program": r[7],
                "ct_section": r[8], "ct_semester": r[9], "ct_shift": r[10],
                "assigned_codes": set(semester_capacity[staff_id].get("assigned_codes", ())),  # Per-semester tracking for multi-section constraint
            }
        
        logger.info(f"  Semester {semester_label}: Loaded {len(staff_map)} faculty (single-semester capacity)")
        
        # ================================================================
        # STEP 2: Load subject offerings FOR THIS SEMESTER ONLY
        # ================================================================
        offering_sql = """
                SELECT so.id, so.subject_id, so.program_id, so.semester_id,
                       so.section_id, so.shift,
                       s.code, s.name, COALESCE(s.tch, s.l + s.t + s.p, 0) AS tch,
                       s.l, s.t, s.p,
                       p.name AS program_name,
                       sem.label AS semester_label,
                       sec.label AS section_label
                FROM subject_offering so
                JOIN subject s ON s.id = so.subject_id
                JOIN program p ON p.id = so.program_id
                JOIN semester sem ON sem.id = so.semester_id
                JOIN section sec ON sec.id = so.section_id
                JOIN cycle c ON c.academic_year_id = so.academic_year_id 
                            AND c.semester_id = so.semester_id
                WHERE c.id = :cid
                  AND so.is_active = true
                  AND so.semester_id = :sem_id
        """
        offering_params = {"cid": cycle_id, "sem_id": semester_id}
        if program_id is not None:
            offering_sql += "  AND so.program_id = :pid\n"
            offering_params["pid"] = program_id
        offering_sql += "  ORDER BY so.id"
        
        offering_rows = session.execute(
            text(offering_sql), offering_params
        ).fetchall()
        
        # Build offering lookup: {offering_id: offering_dict}
        offering_map = {}
        for r in offering_rows:
            offering_map[r[0]] = {
                "id": r[0], "subject_id": r[1], "program_id": r[2],
                "semester_id": r[3], "section_id": r[4], "shift": r[5],
                "code": r[6], "name": r[7], "tch": r[8],
                "l": r[9] or 0, "t": r[10] or 0, "p": r[11] or 0,
                "program_name": r[12], "semester_label": r[13],
                "section_label": r[14],
            }
        
        # Track which offerings have been assigned
        assigned_offerings = set()
        
        logger.info(f"  Semester {semester_label}: Loaded {len(offering_map)} subject offerings")
        
        # ================================================================
        # STEP 3: Load faculty preferences FOR THIS SEMESTER ONLY
        # ================================================================
        pref_rows = session.execute(
            text("""
                SELECT fp.staff_id, fp.subject_offering_id, fp.preference_number
                FROM faculty_preference fp
                JOIN subject_offering so ON so.id = fp.subject_offering_id
                JOIN cycle c ON c.academic_year_id = so.academic_year_id 
                            AND c.semester_id = so.semester_id
                WHERE c.id = :cid
                  AND fp.cycle_id = :cid
                  AND so.semester_id = :sem_id
                ORDER BY fp.preference_number, fp.submitted_at
            """),
            {"cid": cycle_id, "sem_id": semester_id}
        ).fetchall()
        
        # Group preferences by stage
        prefs_by_stage = {1: [], 2: [], 3: [], 4: [], 5: []}
        for r in pref_rows:
            pref_num = r[2]
            if pref_num in prefs_by_stage:
                prefs_by_stage[pref_num].append({
                    "staff_id": r[0],
                    "offering_id": r[1],
                    "pref_num": r[2],
                })
        
        logger.info(f"  Semester {semester_label}: Loaded {len(pref_rows)} preferences")
        
        # ================================================================
        # HELPER: Try to allocate an offering to a faculty member
        # ================================================================
        def try_allocate(staff_id, offering_id, stage_label, pref_num=None, relaxed_shift=False, relaxed_multi_section=False, allow_overload=False, max_overload_pct=0.0):
            """
            Attempt to allocate an offering to a faculty member.
            Returns True if allocated, False if constraints prevent it.
            
            Args:
                allow_overload: If True, allow exceeding tch_norm up to max_overload_pct
                max_overload_pct: Maximum overload percentage (e.g., 0.2 = 20% above norm)
            """
            if offering_id in assigned_offerings:
                return False  # Already assigned
            
            if staff_id not in staff_map:
                return False  # Staff not found
            
            staff = staff_map[staff_id]
            offering = offering_map.get(offering_id)
            if not offering:
                return False
            
            # CONSTRAINT: Shift compatibility (SHIFT-01)
            if not _is_shift_compatible(staff["shift"], offering["shift"], relaxed=relaxed_shift):
                return False
            
            # CONSTRAINT: Workload capacity (SINGLE SEMESTER ONLY)
            offer_tch = offering["tch"] or 0
            if offer_tch > 0:
                max_allowed = staff["tch_norm"]
                if allow_overload:
                    max_allowed = staff["tch_norm"] * (1.0 + max_overload_pct)
                
                if staff["tch_assigned"] + offer_tch > max_allowed:
                    return False  # Would exceed limit FOR THIS SEMESTER
            
            # CONSTRAINT: Multi-section — same course code already assigned
            course_code = offering["code"]
            if course_code in staff["assigned_codes"]:
                if not relaxed_multi_section:
                    return False  # Already teaching this course in another section
            
            # All constraints pass — allocate
            allocations.append({
                "staff_id": staff_id,
                "subject_offering_id": offering_id,
                "l_assigned": offering["l"],
                "t_assigned": offering["t"],
                "p_assigned": offering["p"],
                "tch": offer_tch,
                "allocation_stage": stage_label,
                "preference_number": pref_num,
                "staff_name": staff["name"],
                "emp_code": staff["emp_code"],
                "subject_code": offering["code"],
                "subject_name": offering["name"],
                "section_label": offering["section_label"],
                "semester_label": offering["semester_label"],
                "program_name": offering["program_name"],
            })
            
            # Update tracking
            assigned_offerings.add(offering_id)
            staff["tch_assigned"] += offer_tch
            staff["assigned_codes"].add(course_code)
            
            # Update semester capacity tracker
            semester_capacity[staff_id]["tch_assigned"] += offer_tch
            
            return True
        
        # ================================================================
        # STAGE 1: Process preference_number = 1 (highest priority)
        # ================================================================
        stage1_count = 0
        for pref in prefs_by_stage[1]:
            if try_allocate(pref["staff_id"], pref["offering_id"], "PREF_1", 1):
                stage1_count += 1
        
        logger.info(f"  Semester {semester_label}: Stage 1 (pref=1): {stage1_count} allocated")
        
        # ================================================================
        # STAGE 2: Process preference_number = 2, 3, 4, 5
        # ================================================================
        stage2_count = 0
        for pref_num in [2, 3, 4, 5]:
            for pref in prefs_by_stage[pref_num]:
                if try_allocate(
                    pref["staff_id"], pref["offering_id"],
                    f"PREF_{pref_num}", pref_num
                ):
                    stage2_count += 1
        
        logger.info(f"  Semester {semester_label}: Stage 2 (pref=2-5): {stage2_count} allocated")
        
        # Track preference-based allocations for FINAL PASS guard
        preference_based_count = stage1_count + stage2_count
        
        # ================================================================
        # FINAL PASS: Assign unallocated to compatible faculty
        # FIX 2: Only run if at least some preference-based allocations succeeded
        # Multi-pass strategy with progressive relaxation:
        #   PASS 1: Strict (no overload, no shift/multi-section relaxation)
        #   PASS 2: Relax shift constraint (SHIFT2 → SHIFT1)
        #   PASS 3: Relax multi-section constraint
        #   PASS 4: Allow 10% overload for underloaded faculty
        #   PASS 5: Allow 20% overload for all faculty (MAXIMUM ALLOWED)
        # ================================================================
        final_count = 0
        remaining_offerings = [
            oid for oid in offering_map.keys() 
            if oid not in assigned_offerings
        ]
        
        if preference_based_count > 0:
            # Only run final pass if at least some preference allocations succeeded
            for oid in remaining_offerings:
                offering = offering_map[oid]
                offer_tch = offering["tch"] or 0
                
                # Skip offerings with 0 TCH (e.g., internships, projects)
                if offer_tch == 0:
                    unallocated.append({
                        "subject_offering_id": oid,
                        "subject_code": offering["code"],
                        "subject_name": offering["name"],
                        "section_label": offering["section_label"],
                        "semester_label": offering["semester_label"],
                        "program_name": offering["program_name"],
                        "tch": offer_tch,
                        "reason": "Zero TCH (internship/project/non-credit)",
                    })
                    continue
                
                # Sort candidates: underloaded first, then by lowest load
                candidates = sorted(
                    staff_map.values(),
                    key=lambda s: (
                        0 if s["tch_assigned"] < s["tch_norm"] else 1,  # Underloaded first
                        s["tch_assigned"]  # Then by lowest load
                    )
                )
                
                allocated = False
                
                # PASS 1: Strict constraints (no overload, no relaxation)
                for candidate in candidates:
                    if try_allocate(candidate["id"], oid, "FINAL_PASS", 
                                   relaxed_shift=False, relaxed_multi_section=False, 
                                   allow_overload=False):
                        final_count += 1
                        allocated = True
                        break
                
                if allocated:
                    continue
                
                # PASS 2: Relax shift constraint (allow SHIFT2 → SHIFT1)
                for candidate in candidates:
                    if try_allocate(candidate["id"], oid, "FINAL_PASS_RELAXED_SHIFT", 
                                   relaxed_shift=True, relaxed_multi_section=False, 
                                   allow_overload=False):
                        final_count += 1
                        allocated = True
                        break
                
                if allocated:
                    continue
                
                # PASS 3: Relax multi-section constraint
                for candidate in candidates:
                    if try_allocate(candidate["id"], oid, "FINAL_PASS_RELAXED_MULTI", 
                                   relaxed_shift=True, relaxed_multi_section=True, 
                                   allow_overload=False):
                        final_count += 1
                        allocated = True
                        break
                
                if allocated:
                    continue
                
                # PASS 4: Allow 10% overload (prioritize underloaded faculty)
                underloaded_candidates = [
                    c for c in candidates 
                    if c["tch_assigned"] < c["tch_norm"]
                ]
                
                for candidate in underloaded_candidates:
                    if try_allocate(candidate["id"], oid, "FINAL_PASS_OVERLOAD_10", 
                                   relaxed_shift=True, relaxed_multi_section=True, 
                                   allow_overload=True, max_overload_pct=0.10):
                        final_count += 1
                        allocated = True
                        break
                
                if allocated:
                    continue
                
                # PASS 5: Allow 20% overload for all faculty (MAXIMUM ALLOWED)
                for candidate in candidates:
                    if try_allocate(candidate["id"], oid, "FINAL_PASS_OVERLOAD_20", 
                                   relaxed_shift=True, relaxed_multi_section=True, 
                                   allow_overload=True, max_overload_pct=0.20):
                        final_count += 1
                        allocated = True
                        break
                
                if not allocated:
                    unallocated.append({
                        "subject_offering_id": oid,
                        "subject_code": offering["code"],
                        "subject_name": offering["name"],
                        "section_label": offering["section_label"],
                        "semester_label": offering["semester_label"],
                        "program_name": offering["program_name"],
                        "tch": offer_tch,
                        "reason": "No compatible faculty with available capacity (even with 20% overload)",
                    })
            
            logger.info(f"  Semester {semester_label}: Final pass: {final_count} allocated, {len(unallocated)} unallocated")
        else:
            # No preference-based allocations succeeded - skip final pass
            logger.info(f"  Semester {semester_label}: Skipping final pass - no preference allocations made")
            # Mark all remaining offerings as unallocated
            for oid in remaining_offerings:
                offering = offering_map[oid]
                unallocated.append({
                    "subject_offering_id": oid,
                    "subject_code": offering["code"],
                    "subject_name": offering["name"],
                    "section_label": offering["section_label"],
                    "semester_label": offering["semester_label"],
                    "program_name": offering["program_name"],
                    "tch": offering["tch"] or 0,
                    "reason": "No preference-based allocations succeeded - final pass skipped",
                })
    
    return {
        "allocations": allocations,
        "unallocated": unallocated,
        "total": len(offering_map),
        "assigned": len(allocations),
        "unassigned": len(unallocated),
    }


class AllocationScopeError(ValueError):
    """Invalid allocation scope; no data changes may survive this error."""


def _failure(message):
    return {
        "success": False, "message": message,
        "subjects_total": 0, "subjects_assigned": 0, "subjects_unassigned": 0,
        "faculty_overloaded": 0, "faculty_underloaded": 0, "faculty_balanced": 0,
        "allocations": [], "unallocated": [], "workload_summary": [],
    }


def _resolve_scope(session, academic_year=None, semester_id=None,
                   academic_cycle_id=None, program_id=None):
    """Resolve and lock the requested OPEN cycle and semester before any writes."""
    if semester_id is None and not academic_year and academic_cycle_id is None:
        raise AllocationScopeError("Must provide either semester_id OR academic_year")
    if any(value is not None and value <= 0
           for value in (semester_id, academic_cycle_id, program_id)):
        raise AllocationScopeError("Scope IDs must be positive")
    query = """
        SELECT c.id, ay.name, sem.id, sem.label, sem.state
        FROM cycle c
        JOIN academic_year ay ON ay.id = c.academic_year_id
        JOIN semester sem ON sem.id = c.semester_id
        WHERE c.status = 'OPEN'
    """
    params = {}
    for value, clause, name in (
        (academic_year, "ay.name = :year", "year"),
        (semester_id, "sem.id = :sid", "sid"),
        (academic_cycle_id, "c.id = :cid", "cid"),
    ):
        if value is not None:
            query += " AND " + clause
            params[name] = value
    # Year-only requests retain the existing single-active-semester behavior.
    row = session.execute(text(query + " ORDER BY sem.id, c.id LIMIT 1 FOR UPDATE OF c, sem"), params).fetchone()
    if not row:
        raise AllocationScopeError("No open academic cycle matches the requested scope")
    cid, year, sid, label, state = row
    if state not in ("OPEN", "CLOSED"):
        raise AllocationScopeError(
            "Cannot run allocation: semester is " + state + "; reopen it first if allocation is allowed"
        )
    if program_id is not None:
        if not session.execute(text("SELECT id FROM program WHERE id = :pid AND is_active = true"),
                               {"pid": program_id}).fetchone():
            raise AllocationScopeError("Program not found or inactive")
    scope_filter = "so.semester_id = :sid AND so.academic_year_id = c.academic_year_id"
    offering_params = {"cid": cid, "sid": sid}
    if program_id is not None:
        scope_filter += " AND so.program_id = :pid"
        offering_params["pid"] = program_id
    offerings = session.execute(text("""
        SELECT count(*) FROM subject_offering so JOIN cycle c ON c.id = :cid
        WHERE """ + scope_filter + " AND so.is_active = true"), offering_params).scalar()
    if not offerings:
        raise AllocationScopeError("No active offerings in the requested scope")
    preferences = session.execute(text("""
        SELECT count(*) FROM faculty_preference fp
        JOIN subject_offering so ON so.id = fp.subject_offering_id
        JOIN cycle c ON c.id = fp.cycle_id
        WHERE fp.cycle_id = :cid AND """ + scope_filter), offering_params).scalar()
    if not preferences:
        raise AllocationScopeError("No preferences submitted in the requested scope")
    return {"cycle_id": cid, "academic_year": year, "semester_id": sid,
            "semester_label": label, "semester_type": "ODD" if label in ("I", "III", "V") else "EVEN"}


def run_allocation(academic_year=None, semester_type=None, academic_cycle_id=None,
                   program_id=None, semester_id=None):
    """Validate, calculate, persist and change status in one transaction."""
    if semester_id is None and not academic_year and academic_cycle_id is None:
        return _failure("Must provide either semester_id OR academic_year")
    try:
        with get_transaction() as session:
            scope = _resolve_scope(session, academic_year, semester_id, academic_cycle_id, program_id)
            result = _allocate_in_transaction(session, scope, program_id)
            session.commit()
            return result
    except AllocationScopeError as error:
        return _failure(str(error))


def run_all_open_semesters():
    """Validate every selected cycle first; commit the whole batch or none."""
    try:
        with get_transaction() as session:
            cycles = session.execute(text(
                "SELECT id FROM cycle WHERE status = 'OPEN' ORDER BY semester_id, id"
            )).fetchall()
            if not cycles:
                raise AllocationScopeError("No open cycles found. Please open cycles first.")
            scopes = [_resolve_scope(session, academic_cycle_id=row[0]) for row in cycles]
            results = [_allocate_in_transaction(session, scope) for scope in scopes]
            session.commit()
            return {"success": True, "results": results}
    except AllocationScopeError as error:
        return _failure(str(error))


def _allocate_in_transaction(session, scope, program_id=None):
    """Caller owns the transaction; this function must never commit."""
    cycle_id = scope["cycle_id"]
    academic_year = scope["academic_year"]
    semester_type = scope["semester_type"]
    target_semester_id = scope["semester_id"]
    target_semester_label = scope["semester_label"]
    # ================================================================
    # LOAD STAFF CAPACITY (SINGLE SEMESTER SCOPE)
    # ================================================================
    with nullcontext(session):
        staff_rows = session.execute(
            text("""
                SELECT s.id, s.name, s.emp_code,
                       COALESCE(NULLIF(TRIM(s.designation), ''), 'Assistant Professor') AS designation,
                       COALESCE(s.tch_norm, 40) AS tch_norm
                FROM staff s
                WHERE s.is_active = true AND s.emp_code IS NOT NULL
                ORDER BY s.id
            """)
        ).fetchall()
        
        # Single-semester capacity tracker: {staff_id: {"tch_norm": X, "tch_assigned": 0}}
        staff_capacity = {}
        for r in staff_rows:
            staff_capacity[r[0]] = {
                "id": r[0],
                "name": r[1],
                "emp_code": r[2],
                "designation": r[3],
                "tch_norm": r[4],
                "tch_assigned": 0,  # Fresh capacity for THIS semester only
            }
        
        logger.info(f"Loaded {len(staff_capacity)} faculty for single-semester allocation")
    
    # ================================================================
    # RUN ALLOCATION FOR SINGLE SEMESTER
    # ================================================================
    logger.info(f"Processing Semester {target_semester_label} (ID {target_semester_id})")
    
    if program_id is not None:
        retained = session.execute(text("""
            SELECT a.staff_id, sub.code, COALESCE(sub.tch, sub.l + sub.t + sub.p, 0)
            FROM allocation a JOIN subject_offering so ON so.id = a.subject_offering_id
            JOIN subject sub ON sub.id = so.subject_id
            WHERE a.cycle_id = :cid AND so.semester_id = :sid AND so.program_id <> :pid
        """), {"cid": cycle_id, "sid": target_semester_id, "pid": program_id}).fetchall()
        for staff_id, code, tch in retained:
            if staff_id in staff_capacity:
                staff_capacity[staff_id]["tch_assigned"] += tch
                staff_capacity[staff_id].setdefault("assigned_codes", set()).add(code)

    # Run allocation for this specific semester
    sem_result = _run_allocation_for_semester(
        cycle_id=cycle_id,
        academic_year=academic_year,
        semester_type=semester_type,
        semester_id=target_semester_id,
        semester_label=target_semester_label,
        semester_capacity=staff_capacity,
        program_id=program_id, session=session,
    )
    
    all_allocations = sem_result["allocations"]
    all_unallocated = sem_result["unallocated"]
    
    # ================================================================
    # PERSIST ALLOCATION RESULTS (SINGLE SEMESTER)
    # HARDENING: Ensure idempotent operation - clear stale data for THIS semester only
    # ================================================================
    with nullcontext(session):
        # Clear existing allocations for this specific semester ONLY
        # CRITICAL: Maintains single-semester isolation
        deleted_allocs = session.execute(
            text("""
                DELETE FROM allocation 
                WHERE cycle_id = :cid AND subject_offering_id IN (
                    SELECT so.id FROM subject_offering so
                    JOIN cycle c ON c.academic_year_id = so.academic_year_id
                                AND c.semester_id = so.semester_id
                    WHERE c.id = :cid AND so.semester_id = :sem_id
                      AND (:pid IS NULL OR so.program_id = :pid)
                )
            """),
            {"cid": cycle_id, "sem_id": target_semester_id, "pid": program_id}
        ).rowcount
        
        logger.info(f"Cleared {deleted_allocs} existing allocations for semester {target_semester_label}")
        
        # Persist all allocation records for THIS semester
        for alloc in all_allocations:
            session.execute(
                text("""
                    INSERT INTO allocation 
                        (staff_id, subject_offering_id, l_assigned, t_assigned, p_assigned, cycle_id, old_academic_cycle_id)
                    VALUES (:staff_id, :offering_id, :l, :t, :p, :cid, :cid)
                """),
                {
                    "staff_id": alloc["staff_id"],
                    "offering_id": alloc["subject_offering_id"],
                    "l": alloc["l_assigned"],
                    "t": alloc["t_assigned"],
                    "p": alloc["p_assigned"],
                    "cid": cycle_id,
                }
            )
        
        logger.info(f"Persisted {len(all_allocations)} allocation records for semester {target_semester_label}")
        
        # ================================================================
        # RECOMPUTE THE SHARED YEAR/PARITY WORKLOAD SUMMARY BUCKET
        # CRITICAL: This ensures semester isolation - we recompute from actual data
        # instead of blindly deleting everything
        # ================================================================
        
        # Step 1: Calculate workload for ALL staff based on ALL allocations in this cycle
        # This aggregates across ALL semesters that have been allocated
        workload_rows = session.execute(
            text("""
                SELECT 
                    s.id, s.emp_code, s.name,
                    COALESCE(NULLIF(TRIM(s.designation), ''), 'Assistant Professor') AS designation,
                    COALESCE(s.tch_norm, 40) AS tch_norm,
                    COALESCE(SUM(sub.tch), 0) AS tch_assigned
                FROM staff s
                LEFT JOIN allocation a ON a.staff_id = s.id AND a.cycle_id IN (
                    SELECT c.id FROM cycle c JOIN academic_year ay ON ay.id = c.academic_year_id
                    JOIN semester sem ON sem.id = c.semester_id
                    WHERE ay.name = :year
                      AND CASE WHEN sem.label IN ('I','III','V') THEN 'ODD' ELSE 'EVEN' END = :sem_type
                )
                LEFT JOIN subject_offering so ON so.id = a.subject_offering_id
                LEFT JOIN subject sub ON sub.id = so.subject_id
                WHERE s.is_active = true AND s.emp_code IS NOT NULL
                GROUP BY s.id, s.emp_code, s.name, s.designation, s.tch_norm
                ORDER BY s.id
            """),
            {"year": academic_year, "sem_type": semester_type}
        ).fetchall()
        
        workload_summaries = []
        overloaded = 0
        underloaded = 0
        balanced = 0
        
        # Step 2: Upsert workload summaries (update if exists, insert if not)
        for r in workload_rows:
            staff_id, emp_code, name, designation, tch_norm, tch_assigned = r
            deviation = tch_assigned - tch_norm
            
            if deviation > 0:
                status = "OVERLOADED"
                overloaded += 1
            elif deviation < -2:
                status = "UNDERLOADED"
                underloaded += 1
            else:
                status = "BALANCED"
                balanced += 1
            
            # UPSERT: Update if exists, insert if not
            # This maintains data for other semesters while updating current semester
            session.execute(
                text("""
                    INSERT INTO workload_summary 
                        (staff_id, academic_year, semester_type, tch_total,
                         norm_hours, deviation_hours, total_workload, cycle_id, old_academic_cycle_id)
                    VALUES (:staff_id, :year, :sem_type, :tch_total,
                            :norm, :deviation, :total, :cid, :cid)
                    ON CONFLICT (staff_id, academic_year, semester_type)
                    DO UPDATE SET
                        tch_total = EXCLUDED.tch_total,
                        norm_hours = EXCLUDED.norm_hours,
                        deviation_hours = EXCLUDED.deviation_hours,
                        total_workload = EXCLUDED.total_workload,
                        updated_at = now()
                """),
                {
                    "staff_id": staff_id,
                    "year": academic_year,
                    "sem_type": semester_type,
                    "tch_total": tch_assigned,
                    "norm": tch_norm,
                    "deviation": deviation,
                    "total": tch_assigned,
                    "cid": cycle_id,
                }
            )
            
            workload_summaries.append({
                "staff_id": staff_id,
                "emp_code": emp_code,
                "name": name,
                "designation": designation,
                "tch_norm": tch_norm,
                "tch_assigned": tch_assigned,
                "deviation": deviation,
                "status": status,
            })
        
        logger.info(f"Updated workload summaries for {len(workload_summaries)} staff (computed from all allocations in cycle)")
        
        # ================================================================
        # AUDIT LOG
        # ================================================================
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (
                    COALESCE(
                        (SELECT id FROM staff WHERE is_coordinator = true AND is_active = true ORDER BY id LIMIT 1),
                        (SELECT id FROM staff WHERE is_active = true ORDER BY id LIMIT 1)
                    ),
                    'ALLOCATION_RUN',
                    :details
                )
            """),
            {
                "details": (
                    f'{{"academic_year": "{academic_year}", '
                    f'"semester_type": "{semester_type}", '
                    f'"semester_id": {target_semester_id}, '
                    f'"semester_label": "{target_semester_label}", '
                    f'"total_assigned": {len(all_allocations)}, '
                    f'"total_unassigned": {len(all_unallocated)}, '
                    f'"overloaded": {overloaded}, '
                    f'"underloaded": {underloaded}}}'
                )
            }
        )
        
        
        # Log allocation summary
        logger.info("=" * 60)
        logger.info(f"ALLOCATION SUMMARY FOR SEMESTER {target_semester_label}:")
        logger.info(
            f"  {len(all_allocations)}/{sem_result['total']} assigned "
            f"({len(all_unallocated)} unassigned)"
        )
        logger.info(
            f"  Faculty: {overloaded} overloaded, {underloaded} underloaded, {balanced} balanced"
        )
        logger.info("=" * 60)
    
    # ================================================================
    # PHASE 2: Mark the selected semester as ALLOCATED and update cycle status
    # ================================================================
    with nullcontext(session):
        session.execute(
            text("UPDATE semester SET state = 'ALLOCATED', allocated_at = now() WHERE id = :sid"),
            {"sid": target_semester_id}
        )
        # Update cycle status to ALLOCATED after successful allocation
        session.execute(
            text("UPDATE cycle SET status = 'ALLOCATED' WHERE id = :cid"),
            {"cid": cycle_id}
        )
    
    logger.info("Selected semester and cycle marked as ALLOCATED")
    
    return {
        "success": True,
        "message": (
            f"Allocation complete for Semester {target_semester_label}: "
            f"{len(all_allocations)} assigned, {len(all_unallocated)} unassigned"
        ),
        "semester_id": target_semester_id,
        "semester_label": target_semester_label,
        "subjects_total": sem_result["total"],
        "subjects_assigned": len(all_allocations),
        "subjects_unassigned": len(all_unallocated),
        "faculty_overloaded": overloaded,
        "faculty_underloaded": underloaded,
        "faculty_balanced": balanced,
        "allocations": all_allocations,
        "unallocated": all_unallocated,
        "workload_summary": workload_summaries,
    }
