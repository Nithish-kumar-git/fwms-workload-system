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


def _is_shift_compatible(staff_shift: str, offering_shift: int) -> bool:
    """Check if a faculty member's shift allows teaching this offering."""
    if not staff_shift or not offering_shift:
        return True  # No constraint if data missing
    
    s = str(staff_shift).upper().strip()
    
    # SHIFT1+SHIFT2 or BOTH → always compatible
    if "SHIFT1+SHIFT2" in s or "BOTH" in s:
        return True
    
    if "2" in s and offering_shift == 1:
        return False  # SHIFT2 faculty cannot teach SHIFT1
    if "1" in s and offering_shift == 2:
        return False  # SHIFT1 faculty cannot teach SHIFT2
    
    return True


def run_allocation(
    academic_year: str | None = None, 
    semester_type: str | None = None, 
    academic_cycle_id: int | None = None,
    program_id: int | None = None
) -> dict:
    """
    Run the complete allocation engine.
    
    Steps:
    1. Clear existing allocations for this academic year/semester
    2. Load all active staff with workload norms
    3. Load all active subject offerings with TCH values
    4. Load all faculty preferences (ordered by preference_number)
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
    # CYCLE GUARD: Resolve active academic cycle
    # ================================================================
    from app.admin.cycle_service import get_active_cycle
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
    
    allocations = []       # List of allocation dicts to insert
    unallocated = []       # Offerings that couldn't be assigned
    
    with get_transaction() as session:
        # WORKFLOW ENFORCEMENT: Fail if no preferences exist
        pref_count = session.execute(
            text("SELECT count(*) FROM faculty_preference WHERE academic_cycle_id = :cid"),
            {"cid": cycle_id}
        ).scalar()
        if pref_count == 0:
            return {
                "success": False,
                "message": "Allocation disabled: No faculty preferences submitted for the active cycle.",
                "subjects_total": 0, "subjects_assigned": 0, "subjects_unassigned": 0,
                "faculty_overloaded": 0, "faculty_underloaded": 0, "faculty_balanced": 0,
                "allocations": [], "unallocated": [], "workload_summary": [],
            }
        # ================================================================
        # STEP 1: Clear existing allocations for this run
        # ================================================================
        if program_id:
            session.execute(
                text("""
                    DELETE FROM allocation 
                    WHERE academic_cycle_id = :cid 
                      AND subject_offering_id IN (SELECT id FROM subject_offering WHERE program_id = :pid)
                """),
                {"cid": cycle_id, "pid": program_id}
            )
            # Workload summaries are fully rebuilt at the end, but we need to clear them before recalculation
            session.execute(
                text("DELETE FROM workload_summary WHERE academic_cycle_id = :cid"),
                {"cid": cycle_id}
            )
        else:
            session.execute(
                text("DELETE FROM allocation WHERE academic_cycle_id = :cid"),
                {"cid": cycle_id}
            )
            session.execute(
                text("DELETE FROM workload_summary WHERE academic_cycle_id = :cid"),
                {"cid": cycle_id}
            )
        
        # ================================================================
        # STEP 2: Load staff data
        # ================================================================
        staff_rows = session.execute(
            text("""
                SELECT s.id, s.name, s.emp_code, s.designation, s.shift,
                       COALESCE(s.tch_norm, 16) AS tch_norm,
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
            staff_map[r[0]] = {
                "id": r[0], "name": r[1], "emp_code": r[2],
                "designation": r[3], "shift": r[4], "tch_norm": r[5],
                "is_class_teacher": r[6], "ct_program": r[7],
                "ct_section": r[8], "ct_semester": r[9], "ct_shift": r[10],
                "tch_assigned": 0,  # running total
                "assigned_codes": set(),  # track course codes for multi-section
            }
        
        logger.info(f"Loaded {len(staff_map)} faculty members")
        
        # ================================================================
        # STEP 3: Load subject offerings
        # ================================================================
        # Build offering query — filter by program_id only if provided
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
        """
        offering_params = {"cid": cycle_id}
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
        
        logger.info(f"Loaded {len(offering_map)} subject offerings")
        
        # ================================================================
        # STEP 4: Load faculty preferences (all stages)
        # ================================================================
        pref_rows = session.execute(
            text("""
                SELECT fp.staff_id, fp.subject_offering_id, fp.preference_number
                FROM faculty_preference fp
                WHERE fp.academic_cycle_id = :cid
                ORDER BY fp.preference_number, fp.submitted_at
            """),
            {"cid": cycle_id}
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
        
        logger.info(f"Loaded {len(pref_rows)} preferences across 5 stages")
        
        # ================================================================
        # HELPER: Try to allocate an offering to a faculty member
        # ================================================================
        def try_allocate(staff_id, offering_id, stage_label, pref_num=None):
            """
            Attempt to allocate an offering to a faculty member.
            Returns True if allocated, False if constraints prevent it.
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
            if not _is_shift_compatible(staff["shift"], offering["shift"]):
                return False
            
            # CONSTRAINT: Workload capacity
            offer_tch = offering["tch"] or 0
            if offer_tch > 0 and staff["tch_assigned"] + offer_tch > staff["tch_norm"]:
                return False  # Would exceed norm
            
            # CONSTRAINT: Multi-section — same course code already assigned
            course_code = offering["code"]
            if course_code in staff["assigned_codes"]:
                return False  # Already teaching this course in another section
            
            # All constraints pass — allocate
            allocations.append({
                "staff_id": staff_id,
                "subject_offering_id": offering_id,       # was: offering_id
                "l_assigned": offering["l"],
                "t_assigned": offering["t"],
                "p_assigned": offering["p"],
                "tch": offer_tch,
                "allocation_stage": stage_label,           # was: stage
                "preference_number": pref_num,             # was: pref_num
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
            
            return True
        
        # ================================================================
        # STAGE 1: Process preference_number = 1 (highest priority)
        # ================================================================
        stage1_count = 0
        for pref in prefs_by_stage[1]:
            if try_allocate(pref["staff_id"], pref["offering_id"], "PREF_1", 1):
                stage1_count += 1
        
        logger.info(f"Stage 1 (pref=1): {stage1_count} allocated")
        
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
        
        logger.info(f"Stage 2 (pref=2-5): {stage2_count} allocated")
        
        # ================================================================
        # FINAL PASS: Assign unallocated to lowest-load compatible faculty
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
            
            # Find compatible faculty sorted by ascending tch_assigned
            candidates = sorted(
                staff_map.values(),
                key=lambda s: s["tch_assigned"]
            )
            
            allocated = False
            for candidate in candidates:
                if try_allocate(candidate["id"], oid, "FINAL_PASS"):
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
                    "reason": "No compatible faculty with available capacity",
                })
        
        logger.info(f"Final pass: {final_count} allocated, {len(unallocated)} unallocated")
        
        # ================================================================
        # PERSIST: Insert allocation records
        # ================================================================
        for alloc in allocations:
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
        
        logger.info(f"Persisted {len(allocations)} allocation records")
        
        # ================================================================
        # WORKLOAD SUMMARY: Insert/update per faculty
        # ================================================================
        workload_summaries = []
        overloaded = 0
        underloaded = 0
        balanced = 0
        
        for sid, staff in staff_map.items():
            tch_assigned = staff["tch_assigned"]
            tch_norm = staff["tch_norm"]
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
            
            session.execute(
                text("""
                    INSERT INTO workload_summary 
                        (staff_id, academic_year, semester_type, tch_total,
                         norm_hours, deviation_hours, total_workload, academic_cycle_id)
                    VALUES (:staff_id, :year, :sem_type, :tch_total,
                            :norm, :deviation, :total, :cid)
                """),
                {
                    "staff_id": sid,
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
                "staff_id": sid,
                "emp_code": staff["emp_code"],
                "name": staff["name"],
                "designation": staff["designation"],
                "tch_norm": tch_norm,
                "tch_assigned": tch_assigned,
                "deviation": deviation,
                "status": status,
            })
        
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
                    f'"total_assigned": {len(allocations)}, '
                    f'"total_unassigned": {len(unallocated)}, '
                    f'"overloaded": {overloaded}, '
                    f'"underloaded": {underloaded}}}'
                )
            }
        )
        
        session.commit()
        
        logger.info(
            f"Allocation complete: {len(allocations)} assigned, "
            f"{len(unallocated)} unassigned, "
            f"{overloaded} overloaded, {underloaded} underloaded"
        )
    
    return {
        "success": True,
        "message": (
            f"Allocation complete: {len(allocations)} assigned, "
            f"{len(unallocated)} unassigned"
        ),
        "subjects_total": len(offering_map),
        "subjects_assigned": len(allocations),
        "subjects_unassigned": len(unallocated),
        "faculty_overloaded": overloaded,
        "faculty_underloaded": underloaded,
        "faculty_balanced": balanced,
        "allocations": allocations,
        "unallocated": unallocated,
        "workload_summary": workload_summaries,
    }
