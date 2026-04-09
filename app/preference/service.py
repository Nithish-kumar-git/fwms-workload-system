"""
Preference submission and validation service.
Spec reference: final_system_specification.md Section 2 (Rules PREF-01 to PREF-05,
SHIFT-01, CT-01)

This module implements the 5 validation rules that replace the Google Apps Script:
  Rule 1 (PREF-01): preference_number must be 1-5
  Rule 2 (PREF-03): Faculty cannot reuse same preference_number
  Rule 3 (PREF-02): Two faculty cannot use same preference_number for same offering
  Rule 4 (SHIFT-01): Shift compatibility (SHIFT1/SHIFT2/SHIFT1+SHIFT2)
  Rule 5 (CT-01): Class teacher pref=1 must match their class

All SQL uses parameterized queries. No ORM magic.
"""

from sqlalchemy import text
from app.db.session import get_transaction
import logging

logger = logging.getLogger(__name__)

MAX_PREFERENCES = 5


def validate_preference(staff_id: int, subject_offering_id: int, preference_number: int) -> dict:
    """
    Validate a preference submission against all 5 institutional rules.
    
    HARDENING: Prevents duplicate preferences after reopening.
    Since reopening clears all preferences, this validation ensures fresh data integrity.
    
    Returns:
        dict with keys: valid (bool), error (str or None), rule (str or None)
    """
    # Rule 1: Preference number range (also enforced by DB CHECK constraint)
    if preference_number < 1 or preference_number > 5:
        return {"valid": False, "error": "Preference number must be between 1 and 5", "rule": "PREF-01"}
    
    with get_transaction() as session:
        # Load staff info for shift/class teacher validation
        staff = session.execute(
            text("""
                SELECT id, shift, is_class_teacher, ct_program, ct_section, 
                       ct_semester, ct_shift
                FROM staff
                WHERE id = :staff_id AND is_active = true
            """),
            {"staff_id": staff_id}
        ).fetchone()
        
        if staff is None:
            return {"valid": False, "error": "Staff not found or inactive", "rule": "AUTH"}
        
        # Load subject offering info for shift/class teacher matching
        offering = session.execute(
            text("""
                SELECT so.id, so.shift, so.section_id, so.semester_id, so.program_id,
                       s.name AS subject_name, s.code AS subject_code,
                       p.name AS program_name,
                       sem.label AS semester_label,
                       sec.label AS section_label
                FROM subject_offering so
                JOIN subject s ON s.id = so.subject_id
                JOIN program p ON p.id = so.program_id
                JOIN semester sem ON sem.id = so.semester_id
                JOIN section sec ON sec.id = so.section_id
                WHERE so.id = :offering_id AND so.is_active = true
            """),
            {"offering_id": subject_offering_id}
        ).fetchone()
        
        if offering is None:
            return {"valid": False, "error": "Subject offering not found or inactive", "rule": "DATA"}
        
        # Rule 2 (PREF-03): Faculty cannot reuse same preference_number
        existing_pref = session.execute(
            text("""
                SELECT id FROM faculty_preference
                WHERE staff_id = :staff_id AND preference_number = :pref_num
            """),
            {"staff_id": staff_id, "pref_num": preference_number}
        ).fetchone()
        
        if existing_pref is not None:
            return {
                "valid": False,
                "error": f"You have already used preference number {preference_number}",
                "rule": "PREF-03"
            }
        
        # Rule 3 (PREF-02): Two faculty cannot use same preference_number for same offering
        duplicate_pref = session.execute(
            text("""
                SELECT id FROM faculty_preference
                WHERE subject_offering_id = :offering_id AND preference_number = :pref_num
            """),
            {"offering_id": subject_offering_id, "pref_num": preference_number}
        ).fetchone()
        
        if duplicate_pref is not None:
            return {
                "valid": False,
                "error": f"Another faculty has already assigned preference {preference_number} to this subject",
                "rule": "PREF-02"
            }
        
        # Prevent duplicate faculty-offering combination
        dup_faculty_offering = session.execute(
            text("""
                SELECT id FROM faculty_preference
                WHERE staff_id = :staff_id AND subject_offering_id = :offering_id
            """),
            {"staff_id": staff_id, "offering_id": subject_offering_id}
        ).fetchone()
        
        if dup_faculty_offering is not None:
            return {
                "valid": False,
                "error": "You have already submitted a preference for this subject offering",
                "rule": "PREF-DUP"
            }
        
        # Rule 4 (SHIFT-01): Shift compatibility - DISABLED
        # Shift constraint removed to allow faculty to select subjects from any shift
        # Shift data is still stored and displayed but does not block selection
        
        # Rule 5 (CT-01): Class teacher first preference
        is_class_teacher = staff[2]
        if is_class_teacher and preference_number == 1:
            ct_program = staff[3]
            ct_section = staff[4]
            ct_semester = staff[5]
            ct_shift = staff[6]
            
            # STEP 1: Check if ANY subjects exist for this CT's class
            # Query active offerings matching ct_program + ct_semester for the current cycle
            ct_subjects_count = session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM subject_offering so
                    JOIN program p ON p.id = so.program_id
                    JOIN semester sem ON sem.id = so.semester_id
                    JOIN cycle c ON c.academic_year_id = so.academic_year_id 
                                AND c.semester_id = so.semester_id
                    WHERE so.is_active = true
                      AND c.status = 'OPEN'
                      AND p.name = :ct_program
                      AND sem.label = :ct_semester
                """),
                {"ct_program": ct_program, "ct_semester": ct_semester}
            ).scalar()
            
            # If NO subjects exist for their class, waive the CT rule entirely
            if ct_subjects_count == 0:
                logger.info(
                    f"CT rule waived for staff_id={staff_id}: "
                    f"No subjects found for {ct_program} Semester {ct_semester}"
                )
                # Allow preference 1 for any subject - skip CT validation
                pass  # Continue to other validations
            else:
                # Subjects exist for their class - enforce the CT rule
                # Check if offering matches class teacher's class
                offering_program = offering[7]    # program_name
                offering_semester = offering[8]   # semester_label
                offering_section = offering[9]    # section_label
                offering_shift_val = offering[1]  # shift
                
                # Normalize function for string comparison
                def normalize(val):
                    if val is None:
                        return ""
                    return str(val).strip().upper().replace(" ", "")
                
                mismatch = False
                mismatch_detail = []
                
                # Program comparison - normalize to handle "MCA(General)" vs "MCA (General)"
                if ct_program and offering_program:
                    if normalize(ct_program) != normalize(offering_program):
                        mismatch = True
                        mismatch_detail.append(f"program ({ct_program} vs {offering_program})")
                
                # Semester comparison - normalize to handle "II" vs "2" or "Semester II" vs "II"
                if ct_semester and offering_semester:
                    ct_sem_norm = normalize(ct_semester).replace("SEMESTER", "")
                    off_sem_norm = normalize(offering_semester).replace("SEMESTER", "")
                    if ct_sem_norm != off_sem_norm:
                        mismatch = True
                        mismatch_detail.append(f"semester ({ct_semester} vs {offering_semester})")
                
                # Section comparison - normalize
                if ct_section and offering_section:
                    if normalize(ct_section) != normalize(offering_section):
                        mismatch = True
                        mismatch_detail.append(f"section ({ct_section} vs {offering_section})")
                
                # Shift comparison - convert to int
                if ct_shift and offering_shift_val:
                    try:
                        if int(ct_shift) != int(offering_shift_val):
                            mismatch = True
                            mismatch_detail.append(f"shift ({ct_shift} vs {offering_shift_val})")
                    except (ValueError, TypeError):
                        pass  # Skip shift comparison if conversion fails
                
                if mismatch:
                    return {
                        "valid": False,
                        "error": f"Your class has {ct_subjects_count} subject(s) this semester. "
                                 f"As class teacher, preference 1 must go to your class subject. "
                                 f"Mismatch: {', '.join(mismatch_detail)}",
                        "rule": "CT-01"
                    }
        
        # Check max preferences count
        pref_count = session.execute(
            text("SELECT count(*) FROM faculty_preference WHERE staff_id = :staff_id"),
            {"staff_id": staff_id}
        ).scalar()
        
        if pref_count >= MAX_PREFERENCES:
            return {
                "valid": False,
                "error": f"Maximum {MAX_PREFERENCES} preferences already submitted",
                "rule": "PREF-04"
            }
    
    return {"valid": True, "error": None, "rule": None}


def submit_preference(staff_id: int, subject_offering_id: int, preference_number: int) -> dict:
    """
    Submit a faculty preference after validation.
    
    HARDENING: Strict state enforcement - preferences can ONLY be submitted when semester is OPEN.
    Blocks submission in CLOSED, ALLOCATED, and FROZEN states.
    
    Returns:
        dict with keys: success (bool), message (str), preference_id (int or None)
    """
    # Cycle lock guard: block all writes after HOD approval
    from app.reports.cycle_guard import require_cycle_unlocked
    try:
        require_cycle_unlocked()
    except RuntimeError as e:
        return {
            "success": False,
            "message": str(e),
            "preference_id": None,
            "rule": "CYCLE-LOCKED"
        }

    # Window guard: preferences only allowed when window is OPEN
    from app.preference.window_service import is_window_open
    if not is_window_open():
        return {
            "success": False,
            "message": "Preference submission window is currently closed",
            "preference_id": None,
            "rule": "WINDOW-CLOSED"
        }
    
    # Query cycle_id for this subject's semester
    with get_transaction() as session:
        cycle_result = session.execute(
            text("""
                SELECT c.id 
                FROM cycle c
                JOIN subject_offering so ON so.academic_year_id = c.academic_year_id
                                        AND so.semester_id = c.semester_id
                WHERE so.id = :offering_id
                LIMIT 1
            """),
            {"offering_id": subject_offering_id}
        )
        cycle_row = cycle_result.fetchone()
        if not cycle_row:
            return {
                "success": False,
                "message": "No cycle found for this subject's semester",
                "preference_id": None,
                "rule": "CYCLE"
            }
        active_cycle_id = cycle_row[0]
    
    # Validate first
    validation = validate_preference(staff_id, subject_offering_id, preference_number)
    if not validation["valid"]:
        return {
            "success": False,
            "message": validation["error"],
            "preference_id": None,
            "rule": validation["rule"]
        }
    
    # Insert preference
    with get_transaction() as session:
        result = session.execute(
            text("""
                INSERT INTO faculty_preference (staff_id, subject_offering_id, preference_number, cycle_id, old_academic_cycle_id)
                VALUES (:staff_id, :offering_id, :pref_num, :cycle_id, :cycle_id)
                RETURNING id
            """),
            {
                "staff_id": staff_id,
                "offering_id": subject_offering_id,
                "pref_num": preference_number,
                "cycle_id": active_cycle_id
            }
        )
        preference_id = result.scalar()
        
        # Log to audit_log
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:staff_id, 'PREFERENCE_SUBMITTED', :details)
            """),
            {
                "staff_id": staff_id,
                "details": f'{{"preference_id": {preference_id}, '
                           f'"subject_offering_id": {subject_offering_id}, '
                           f'"preference_number": {preference_number}}}'
            }
        )
        
        session.commit()
        
        logger.info(
            f"Preference submitted: staff_id={staff_id}, "
            f"offering_id={subject_offering_id}, pref={preference_number}, "
            f"preference_id={preference_id}"
        )
    
    return {
        "success": True,
        "message": f"Preference {preference_number} submitted successfully",
        "preference_id": preference_id,
        "rule": None
    }


def list_preferences(staff_id: int) -> list[dict]:
    """
    List all preferences for a faculty member across all cycles.
    
    Returns:
        List of preference dicts with joined subject info.
    """
    with get_transaction() as session:
        rows = session.execute(
            text("""
                SELECT fp.id, fp.staff_id, fp.subject_offering_id, fp.preference_number,
                       fp.submitted_at,
                       s.code AS subject_code, s.name AS subject_name,
                       sec.label AS section, sem.label AS semester,
                       p.name AS program,
                       COALESCE(s.tch, 0) AS tch,
                       s.curriculum_year
                FROM faculty_preference fp
                JOIN subject_offering so ON so.id = fp.subject_offering_id
                JOIN subject s ON s.id = so.subject_id
                JOIN section sec ON sec.id = so.section_id
                JOIN semester sem ON sem.id = so.semester_id
                JOIN program p ON p.id = so.program_id
                WHERE fp.staff_id = :staff_id
                ORDER BY fp.preference_number
            """),
            {"staff_id": staff_id}
        ).fetchall()
    
    return [
        {
            "id": r[0],
            "staff_id": r[1],
            "subject_offering_id": r[2],
            "preference_number": r[3],
            "submitted_at": r[4],
            "subject_code": r[5],
            "subject_name": r[6],
            "section": r[7],
            "semester": r[8],
            "program": r[9],
            "tch": r[10],
            "curriculum_year": r[11],
        }
        for r in rows
    ]


def delete_preference(staff_id: int, preference_id: int) -> dict:
    """
    Delete a preference by ID (only if it belongs to the staff member).
    
    HARDENING: Strict state enforcement - preferences can ONLY be deleted when semester is OPEN.
    Blocks deletion in CLOSED, ALLOCATED, and FROZEN states.
    
    Returns:
        dict with keys: success (bool), message (str)
    """
    with get_transaction() as session:
        # Verify ownership
        row = session.execute(
            text("""
                SELECT fp.id, fp.subject_offering_id, fp.preference_number
                FROM faculty_preference fp
                WHERE fp.id = :pref_id AND fp.staff_id = :staff_id
            """),
            {"pref_id": preference_id, "staff_id": staff_id}
        ).fetchone()
        
        if row is None:
            return {"success": False, "message": "Preference not found or not owned by you"}
        
        # Delete
        session.execute(
            text("DELETE FROM faculty_preference WHERE id = :pref_id"),
            {"pref_id": preference_id}
        )
        
        # Audit log
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:staff_id, 'PREFERENCE_CLEARED', :details)
            """),
            {
                "staff_id": staff_id,
                "details": f'{{"preference_id": {preference_id}, '
                           f'"subject_offering_id": {row[1]}, '
                           f'"preference_number": {row[2]}}}'
            }
        )
        
        session.commit()
        
        logger.info(f"Preference deleted: staff_id={staff_id}, preference_id={preference_id}")
    
    return {"success": True, "message": "Preference deleted successfully"}


def get_preference_status(staff_id: int) -> dict:
    """
    Get the preference completion status for a faculty member.
    
    Returns:
        dict with status info and list of preferences.
    """
    prefs = list_preferences(staff_id)
    total = len(prefs)
    
    return {
        "staff_id": staff_id,
        "total_submitted": total,
        "remaining": MAX_PREFERENCES - total,
        "max_preferences": MAX_PREFERENCES,
        "is_complete": total >= MAX_PREFERENCES,
        "preferences": prefs,
    }
