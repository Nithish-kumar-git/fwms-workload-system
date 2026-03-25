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
    program_id: int | None = None
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
    
    with get_transaction() as session:
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
                "assigned_codes": set(),  # Per-semester tracking for multi-section constraint
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
                WHERE so.academic_cycle_id = :cid
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
                WHERE fp.academic_cycle_id = :cid
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
        
        # ================================================================
        # FINAL PASS: Assign unallocated to compatible faculty
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
    
    return {
        "allocations": allocations,
        "unallocated": unallocated,
        "total": len(offering_map),
        "assigned": len(allocations),
        "unassigned": len(unallocated),
    }


def run_allocation(
    academic_year: str | None = None, 
    semester_type: str | None = None, 
    academic_cycle_id: int | None = None,
    program_id: int | None = None,
    semester_id: int | None = None
) -> dict:
    """
    Run the complete allocation engine for a SINGLE SEMESTER.
    
    PHASE 1: Single-semester allocation only.
    - Allocates subjects for ONE semester at a time
    - No cross-semester capacity tracking
    - Workload calculated within this semester only
    
    Required parameters (at least one combination):
    - semester_id: Direct semester ID (preferred)
    - OR academic_year + semester_type (resolved via active cycle)
    
    Steps:
    1. Validate semester selection
    2. Load staff with workload norms
    3. Load subject offerings for THIS SEMESTER ONLY
    4. Load faculty preferences for THIS SEMESTER ONLY
    5. Stage 1: Process pref=1 allocations
    6. Stage 2: Process pref=2-5 allocations  
    7. Final pass: assign remaining to lowest-load compatible faculty
    8. Persist allocation records
    9. Update workload_summary table
    10. Log and return results
    
    Returns:
        dict with allocation results, unallocated list, workload summaries
    """
    # ================================================================
    # CYCLE LOCK GUARD: Block writes after HOD approval
    # ================================================================
    from app.reports.cycle_guard import require_cycle_unlocked
    try:
        require_cycle_unlocked()
    except RuntimeError as e:
        return {
            "success": False,
            "message": str(e),
            "subjects_total": 0, "subjects_assigned": 0, "subjects_unassigned": 0,
            "faculty_overloaded": 0, "faculty_underloaded": 0, "faculty_balanced": 0,
            "allocations": [], "unallocated": [], "workload_summary": [],
        }

    # ================================================================
    # CYCLE GUARD: Resolve active academic cycle
    # ================================================================
    from app.admin.cycle_service_new import get_active_cycle
    active_cycle = get_active_cycle()
    if active_cycle is None:
        return {
            "success": False,
            "message": "No active academic cycle. Create and activate one first.",
            "subjects_total": 0, "subjects_assigned": 0, "subjects_unassigned": 0,
            "faculty_overloaded": 0, "faculty_underloaded": 0, "faculty_balanced": 0,
            "allocations": [], "unallocated": [], "workload_summary": [],
        }
    
    # Use cycle values (override params for safety)
    if academic_cycle_id and academic_cycle_id != active_cycle["id"]:
        return {
            "success": False,
            "message": f"Must run allocation for the active academic cycle (ID {active_cycle['id']}).",
            "subjects_total": 0, "subjects_assigned": 0, "subjects_unassigned": 0,
            "faculty_overloaded": 0, "faculty_underloaded": 0, "faculty_balanced": 0,
            "allocations": [], "unallocated": [], "workload_summary": [],
        }

    if academic_year and semester_type:
        if active_cycle["academic_year"] != academic_year or active_cycle["semester_type"] != semester_type:
            return {
                "success": False,
                "message": f"Must run allocation for the active academic cycle ({active_cycle['academic_year']} {active_cycle['semester_type']}).",
                "subjects_total": 0, "subjects_assigned": 0, "subjects_unassigned": 0,
                "faculty_overloaded": 0, "faculty_underloaded": 0, "faculty_balanced": 0,
                "allocations": [], "unallocated": [], "workload_summary": [],
            }

    cycle_id = active_cycle["id"]
    # Always resolve these from the active cycle so they're never None
    academic_year = active_cycle["academic_year"]
    semester_type = active_cycle["semester_type"]
    
    # ================================================================
    # RESOLVE TARGET SEMESTER
    # ================================================================
    target_semester_id = None
    target_semester_label = None
    
    if semester_id:
        # Direct semester ID provided
        with get_transaction() as session:
            sem_row = session.execute(
                text("SELECT id, label FROM semester WHERE id = :sid"),
                {"sid": semester_id}
            ).fetchone()
            
            if not sem_row:
                return {
                    "success": False,
                    "message": f"Semester ID {semester_id} not found.",
                    "subjects_total": 0, "subjects_assigned": 0, "subjects_unassigned": 0,
                    "faculty_overloaded": 0, "faculty_underloaded": 0, "faculty_balanced": 0,
                    "allocations": [], "unallocated": [], "workload_summary": [],
                }
            
            target_semester_id = sem_row[0]
            target_semester_label = sem_row[1]
    else:
        # No semester_id provided - return error (PHASE 1: require explicit semester)
        return {
            "success": False,
            "message": "semester_id is required for allocation. Please specify which semester to allocate.",
            "subjects_total": 0, "subjects_assigned": 0, "subjects_unassigned": 0,
            "faculty_overloaded": 0, "faculty_underloaded": 0, "faculty_balanced": 0,
            "allocations": [], "unallocated": [], "workload_summary": [],
        }
    
    logger.info(f"Running allocation for Semester {target_semester_label} (ID {target_semester_id})")
    
    # ================================================================
    # PHASE 2: Validate semester state (must be CLOSED, not ALLOCATED or FROZEN)
    # ================================================================
    from app.coordinator.semester_state_service import get_semester_state, SemesterState, mark_semester_allocated
    
    semester_info = get_semester_state(target_semester_id)
    if not semester_info:
        return {
            "success": False,
            "message": f"Semester {target_semester_id} not found",
            "subjects_total": 0, "subjects_assigned": 0, "subjects_unassigned": 0,
            "faculty_overloaded": 0, "faculty_underloaded": 0, "faculty_balanced": 0,
            "allocations": [], "unallocated": [], "workload_summary": [],
        }
    
    current_state = semester_info["state"]
    
    if current_state == SemesterState.FROZEN:
        return {
            "success": False,
            "message": "Cannot run allocation: Semester is FROZEN (finalized by HOD). No modifications allowed.",
            "subjects_total": 0, "subjects_assigned": 0, "subjects_unassigned": 0,
            "faculty_overloaded": 0, "faculty_underloaded": 0, "faculty_balanced": 0,
            "allocations": [], "unallocated": [], "workload_summary": [],
        }
    
    if current_state == SemesterState.ALLOCATED:
        return {
            "success": False,
            "message": "Cannot run allocation: Semester is already ALLOCATED. Reopen semester first to rerun allocation.",
            "subjects_total": 0, "subjects_assigned": 0, "subjects_unassigned": 0,
            "faculty_overloaded": 0, "faculty_underloaded": 0, "faculty_balanced": 0,
            "allocations": [], "unallocated": [], "workload_summary": [],
        }
    
    if current_state != SemesterState.CLOSED:
        return {
            "success": False,
            "message": f"Cannot run allocation: Semester must be CLOSED (currently {current_state})",
            "subjects_total": 0, "subjects_assigned": 0, "subjects_unassigned": 0,
            "faculty_overloaded": 0, "faculty_underloaded": 0, "faculty_balanced": 0,
            "allocations": [], "unallocated": [], "workload_summary": [],
        }
    
    # ================================================================
    # LOAD STAFF CAPACITY (SINGLE SEMESTER SCOPE)
    # ================================================================
    with get_transaction() as session:
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
    
    # Run allocation for this specific semester
    sem_result = _run_allocation_for_semester(
        cycle_id=cycle_id,
        academic_year=academic_year,
        semester_type=semester_type,
        semester_id=target_semester_id,
        semester_label=target_semester_label,
        semester_capacity=staff_capacity,
        program_id=program_id
    )
    
    all_allocations = sem_result["allocations"]
    all_unallocated = sem_result["unallocated"]
    
    # ================================================================
    # PERSIST ALLOCATION RESULTS (SINGLE SEMESTER)
    # HARDENING: Ensure idempotent operation - clear stale data for THIS semester only
    # ================================================================
    with get_transaction() as session:
        # Clear existing allocations for this specific semester ONLY
        # CRITICAL: Maintains single-semester isolation
        deleted_allocs = session.execute(
            text("""
                DELETE FROM allocation 
                WHERE academic_cycle_id = :cid 
                  AND subject_offering_id IN (
                      SELECT id FROM subject_offering 
                      WHERE semester_id = :sem_id AND academic_cycle_id = :cid
                  )
            """),
            {"cid": cycle_id, "sem_id": target_semester_id}
        ).rowcount
        
        logger.info(f"Cleared {deleted_allocs} existing allocations for semester {target_semester_label}")
        
        # Persist all allocation records for THIS semester
        for alloc in all_allocations:
            session.execute(
                text("""
                    INSERT INTO allocation 
                        (staff_id, subject_offering_id, l_assigned, t_assigned, p_assigned, academic_cycle_id)
                    VALUES (:staff_id, :offering_id, :l, :t, :p, :cid)
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
        # RECOMPUTE WORKLOAD SUMMARIES FROM ALL ALLOCATIONS IN CYCLE
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
                LEFT JOIN allocation a ON a.staff_id = s.id AND a.academic_cycle_id = :cid
                LEFT JOIN subject_offering so ON so.id = a.subject_offering_id
                LEFT JOIN subject sub ON sub.id = so.subject_id
                WHERE s.is_active = true AND s.emp_code IS NOT NULL
                GROUP BY s.id, s.emp_code, s.name, s.designation, s.tch_norm
                ORDER BY s.id
            """),
            {"cid": cycle_id}
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
                         norm_hours, deviation_hours, total_workload, academic_cycle_id)
                    VALUES (:staff_id, :year, :sem_type, :tch_total,
                            :norm, :deviation, :total, :cid)
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
        
        session.commit()
        
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
    # PHASE 2: Mark ALL semesters as ALLOCATED
    # ================================================================
    with get_transaction() as session:
        session.execute(
            text("UPDATE semester SET state = 'ALLOCATED', allocated_at = now()")
        )
        session.commit()
    
    logger.info("All semesters marked as ALLOCATED")
    
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
