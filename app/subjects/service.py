"""
Subject offering management service.
Provides CRUD operations for subject offerings, programs, sections, and semesters.
"""

from sqlalchemy import text


def get_all_programs(session):
    """Get all active programs."""
    rows = session.execute(
        text("SELECT id, name, ug_pg FROM program WHERE is_active = true ORDER BY name")
    ).fetchall()
    return [{"id": r.id, "name": r.name, "ug_pg": r.ug_pg} for r in rows]


def get_all_sections(session):
    """Get all sections."""
    rows = session.execute(
        text("SELECT id, label, shift FROM section ORDER BY label")
    ).fetchall()
    return [{"id": r.id, "label": r.label, "shift": r.shift} for r in rows]


def get_all_semesters(session):
    """Get all semesters."""
    rows = session.execute(
        text("SELECT id, label FROM semester ORDER BY id")
    ).fetchall()
    return [{"id": r.id, "label": r.label} for r in rows]


def get_all_offerings(session, semester_id=None, program_id=None):
    """Get all subject offerings with optional filters."""
    where = "WHERE so.is_active = true"
    params = {}
    
    if semester_id:
        where += " AND so.semester_id = :sem"
        params["sem"] = semester_id
    
    if program_id:
        where += " AND so.program_id = :prog"
        params["prog"] = program_id
    
    rows = session.execute(
        text(f"""
            SELECT so.id, s.code, s.name, s.l, s.t, s.p, s.tch, s.credits,
                   s.course_category, so.shift, so.student_strength,
                   so.academic_year, so.semester_id, so.program_id, so.section_id,
                   sem.label AS semester_label, sec.label AS section_label,
                   p.name AS program_name, s.id AS subject_id
            FROM subject_offering so
            JOIN subject s ON s.id = so.subject_id
            JOIN semester sem ON sem.id = so.semester_id
            JOIN section sec ON sec.id = so.section_id
            JOIN program p ON p.id = so.program_id
            {where}
            ORDER BY p.name, sem.id, sec.label, s.code
        """),
        params
    ).fetchall()
    
    return [dict(r._mapping) for r in rows]


def create_offering(session, data: dict):
    """Create a new subject offering."""
    # Check if subject with this code exists, create if not
    existing_subject = session.execute(
        text("SELECT id FROM subject WHERE code = :code"),
        {"code": data["course_code"]}
    ).fetchone()
    
    if existing_subject:
        subject_id = existing_subject.id
        # Update subject details
        session.execute(
            text("""
                UPDATE subject 
                SET name=:name, l=:l, t=:t, p=:p,
                    tch=:tch, credits=:credits, course_category=:cat, updated_at=NOW()
                WHERE id=:id
            """),
            {
                "name": data["course_name"], "l": data["l"], "t": data["t"],
                "p": data["p"], "tch": data["l"] + data["t"] + data["p"],
                "credits": data["credits"], "cat": data["course_category"], 
                "id": subject_id
            }
        )
    else:
        # Create new subject
        row = session.execute(
            text("""
                INSERT INTO subject (code, name, l, t, p, tch, credits, course_category,
                                   batch_id, specialization_id, is_active)
                VALUES (:code, :name, :l, :t, :p, :tch, :credits, :cat, 1, 1, true)
                RETURNING id
            """),
            {
                "code": data["course_code"], "name": data["course_name"],
                "l": data["l"], "t": data["t"], "p": data["p"],
                "tch": data["l"] + data["t"] + data["p"],
                "credits": data["credits"], "cat": data["course_category"]
            }
        ).fetchone()
        subject_id = row.id
    
    # Get current academic year
    ay = session.execute(
        text("SELECT id, name FROM academic_year ORDER BY id DESC LIMIT 1")
    ).fetchone()
    
    # Check if offering already exists for this combo
    existing_offering = session.execute(
        text("""
            SELECT id FROM subject_offering
            WHERE subject_id=:sid AND program_id=:prog AND semester_id=:sem
              AND section_id=:sec AND academic_year_id=:ay
        """),
        {
            "sid": subject_id, "prog": data["program_id"],
            "sem": data["semester_id"], "sec": data["section_id"], "ay": ay.id
        }
    ).fetchone()
    
    if existing_offering:
        return {
            "success": False,
            "message": "This subject offering already exists for this program/semester/section/year"
        }
    
    result = session.execute(
        text("""
            INSERT INTO subject_offering
            (subject_id, program_id, semester_id, section_id, shift,
             student_strength, academic_year, academic_year_id, is_active)
            VALUES (:sid, :prog, :sem, :sec, :shift, :strength, :ay_name, :ay_id, true)
            RETURNING id
        """),
        {
            "sid": subject_id, "prog": data["program_id"],
            "sem": data["semester_id"], "sec": data["section_id"],
            "shift": data["shift"], "strength": data["student_strength"],
            "ay_name": ay.name, "ay_id": ay.id
        }
    ).fetchone()
    
    session.commit()
    
    return {
        "success": True,
        "offering_id": result.id,
        "message": "Subject offering created successfully"
    }


def delete_offering(session, offering_id: int):
    """Delete or archive a subject offering."""
    # Check for existing preferences
    pref_count = session.execute(
        text("SELECT COUNT(*) FROM faculty_preference WHERE subject_offering_id = :id"),
        {"id": offering_id}
    ).scalar()
    
    # Check for existing allocations
    alloc_count = session.execute(
        text("SELECT COUNT(*) FROM allocation WHERE subject_offering_id = :id"),
        {"id": offering_id}
    ).scalar()
    
    if pref_count > 0 or alloc_count > 0:
        # Archive instead of hard delete
        session.execute(
            text("UPDATE subject_offering SET is_active = false WHERE id = :id"),
            {"id": offering_id}
        )
        session.commit()
        return {
            "success": True,
            "message": f"Subject archived (had {pref_count} preferences and {alloc_count} allocations). Hidden from preferences but history preserved."
        }
    else:
        session.execute(
            text("DELETE FROM subject_offering WHERE id = :id"),
            {"id": offering_id}
        )
        session.commit()
        return {
            "success": True,
            "message": "Subject offering deleted permanently"
        }


def add_section(session, label: str, shift: int):
    """Add a new section."""
    existing = session.execute(
        text("SELECT id FROM section WHERE label = :label AND shift = :shift"),
        {"label": label, "shift": shift}
    ).fetchone()
    
    if existing:
        return {
            "success": False,
            "message": "Section already exists",
            "id": existing.id
        }
    
    row = session.execute(
        text("INSERT INTO section (label, shift) VALUES (:label, :shift) RETURNING id"),
        {"label": label, "shift": shift}
    ).fetchone()
    
    session.commit()
    
    return {
        "success": True,
        "id": row.id,
        "message": f"Section {label} created"
    }


def add_program(session, name: str, ug_pg: str):
    """Add a new program."""
    existing = session.execute(
        text("SELECT id FROM program WHERE name = :name"),
        {"name": name}
    ).fetchone()
    
    if existing:
        return {
            "success": False,
            "message": "Program already exists",
            "id": existing.id
        }
    
    row = session.execute(
        text("INSERT INTO program (name, ug_pg) VALUES (:name, :ug_pg) RETURNING id"),
        {"name": name, "ug_pg": ug_pg}
    ).fetchone()
    
    session.commit()
    
    return {
        "success": True,
        "id": row.id,
        "message": f"Program {name} created"
    }



def delete_section(session, section_id: int):
    """Delete a section if not used in any active subject offerings."""
    count = session.execute(
        text("""
            SELECT COUNT(*) FROM subject_offering 
            WHERE section_id = :id AND is_active = true
        """),
        {"id": section_id}
    ).scalar()
    
    if count > 0:
        return {
            "success": False,
            "message": f"Cannot delete: used in {count} active subject offerings"
        }
    
    session.execute(
        text("DELETE FROM section WHERE id = :id"),
        {"id": section_id}
    )
    session.commit()
    
    return {
        "success": True,
        "message": "Section deleted"
    }


def delete_program(session, program_id: int):
    """Delete a program if not used in any active subject offerings."""
    count = session.execute(
        text("""
            SELECT COUNT(*) FROM subject_offering 
            WHERE program_id = :id AND is_active = true
        """),
        {"id": program_id}
    ).scalar()
    
    if count > 0:
        return {
            "success": False,
            "message": f"Cannot delete: used in {count} active subject offerings"
        }
    
    session.execute(
        text("DELETE FROM program WHERE id = :id"),
        {"id": program_id}
    )
    session.commit()
    
    return {
        "success": True,
        "message": "Program deleted"
    }
