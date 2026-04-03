"""
Staff management service — CRUD operations for faculty records.

Functions:
  - list_staff: return all faculty with summary info
  - create_staff: create new faculty record
  - update_staff: update faculty fields
  - deactivate_staff: set is_active=false with allocation guard
"""

from sqlalchemy import text
from app.db.session import get_transaction
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

ALLOWED_DOMAIN = settings.ALLOWED_EMAIL_DOMAIN


def list_staff() -> list[dict]:
    """Return all staff records with key fields."""
    with get_transaction() as session:
        rows = session.execute(
            text("""
                SELECT s.id, s.emp_code, s.name, s.email, s.designation,
                       s.shift, s.tch_norm, s.role, s.is_coordinator, s.is_active,
                       s.is_class_teacher, s.ct_program, s.ct_section,
                       s.ct_semester, CAST(s.ct_shift AS VARCHAR) AS ct_shift,
                       s.ct_curriculum_year
                FROM staff s
                ORDER BY s.name
            """)
        ).fetchall()

    return [dict(r._mapping) for r in rows]


def create_staff(
    coordinator_id: int,
    emp_code: str,
    name: str,
    email: str,
    designation: str = "Assistant Professor",
    shift: str = "SHIFT1",
    tch_norm: int = 40,
    role: str = "faculty",
    is_coordinator: bool = False,
    is_class_teacher: bool = False,
    ct_program: str | None = None,
    ct_section: str | None = None,
    ct_semester: str | None = None,
    ct_shift: str | None = None,
    ct_curriculum_year: str | None = None,
) -> dict:
    """Create a new staff record with validation."""
    # Domain validation
    if not email.endswith(f"@{ALLOWED_DOMAIN}"):
        return {"success": False, "message": f"Email must be from @{ALLOWED_DOMAIN}"}

    with get_transaction() as session:
        # emp_code uniqueness
        existing = session.execute(
            text("SELECT id FROM staff WHERE emp_code = :code"),
            {"code": emp_code}
        ).fetchone()
        if existing:
            return {"success": False, "message": f"Employee code {emp_code} already exists"}

        # Email uniqueness
        existing_email = session.execute(
            text("SELECT id FROM staff WHERE email = :email"),
            {"email": email}
        ).fetchone()
        if existing_email:
            return {"success": False, "message": f"Email {email} already exists"}

        result = session.execute(
            text("""
                INSERT INTO staff (emp_code, name, email, designation, shift,
                    tch_norm, role, is_coordinator, is_active,
                    is_class_teacher, ct_program, ct_section, ct_semester, ct_shift, ct_curriculum_year)
                VALUES (:emp_code, :name, :email, :designation, :shift,
                    :tch_norm, :role, :is_coordinator, true,
                    :is_ct, :ct_prog, :ct_sec, :ct_sem, :ct_shift, :ct_curr_year)
                RETURNING id
            """),
            {
                "emp_code": emp_code, "name": name, "email": email,
                "designation": designation, "shift": shift, "tch_norm": tch_norm,
                "role": role, "is_coordinator": is_coordinator,
                "is_ct": is_class_teacher, "ct_prog": ct_program,
                "ct_sec": ct_section, "ct_sem": ct_semester, "ct_shift": ct_shift,
                "ct_curr_year": ct_curriculum_year,
            },
        )
        staff_id = result.scalar()

        # Audit
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'STAFF_CREATED', :details)
            """),
            {
                "actor": coordinator_id,
                "details": f'{{"staff_id": {staff_id}, "emp_code": "{emp_code}", "name": "{name}"}}',
            },
        )
        session.commit()

    logger.info(f"Staff created: id={staff_id}, emp_code={emp_code}")
    return {"success": True, "message": "Staff created", "staff_id": staff_id}


def update_staff(
    coordinator_id: int,
    staff_id: int,
    name: str | None = None,
    designation: str | None = None,
    shift: str | None = None,
    tch_norm: int | None = None,
    role: str | None = None,
    is_coordinator: bool | None = None,
    is_class_teacher: bool | None = None,
    ct_program: str | None = None,
    ct_section: str | None = None,
    ct_semester: str | None = None,
    ct_shift: str | None = None,
    ct_curriculum_year: str | None = None,
) -> dict:
    """Update staff fields (only provided fields)."""
    
    # Validate CT assignment: if is_class_teacher=true, must have program, section, semester
    if is_class_teacher:
        if not ct_program or not ct_section or not ct_semester:
            return {
                "success": False,
                "message": "Class teacher must have program, section, and semester assigned"
            }
    
    updates = []
    params: dict = {"sid": staff_id}

    if name is not None:
        updates.append("name = :name")
        params["name"] = name
    if designation is not None:
        updates.append("designation = :designation")
        params["designation"] = designation
    if shift is not None:
        updates.append("shift = :shift")
        params["shift"] = shift
    if tch_norm is not None:
        updates.append("tch_norm = :tch_norm")
        params["tch_norm"] = tch_norm
    if role is not None:
        updates.append("role = :role")
        params["role"] = role
    if is_coordinator is not None:
        updates.append("is_coordinator = :is_coord")
        params["is_coord"] = is_coordinator
    if is_class_teacher is not None:
        updates.append("is_class_teacher = :is_ct")
        params["is_ct"] = is_class_teacher
    if ct_program is not None:
        updates.append("ct_program = :ct_prog")
        params["ct_prog"] = ct_program
    if ct_section is not None:
        updates.append("ct_section = :ct_sec")
        params["ct_sec"] = ct_section
    if ct_semester is not None:
        updates.append("ct_semester = :ct_sem")
        params["ct_sem"] = ct_semester
    if ct_shift is not None:
        updates.append("ct_shift = :ct_shift")
        params["ct_shift"] = ct_shift
    if ct_curriculum_year is not None:
        updates.append("ct_curriculum_year = :ct_curr_year")
        params["ct_curr_year"] = ct_curriculum_year

    if not updates:
        return {"success": False, "message": "No fields to update"}

    with get_transaction() as session:
        session.execute(
            text(f"UPDATE staff SET {', '.join(updates)} WHERE id = :sid"),
            params,
        )

        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'STAFF_UPDATED', :details)
            """),
            {
                "actor": coordinator_id,
                "details": f'{{"staff_id": {staff_id}, "fields": "{", ".join(updates)}"}}',
            },
        )
        session.commit()

    logger.info(f"Staff updated: id={staff_id}")
    return {"success": True, "message": "Staff updated"}


def deactivate_staff(coordinator_id: int, staff_id: int) -> dict:
    """Deactivate a staff member. Blocked if they have allocations in active cycle."""
    with get_transaction() as session:
        # Check for allocations in active cycle
        alloc_count = session.execute(
            text("""
                SELECT count(*) FROM allocation a
                JOIN cycle c ON c.id = a.cycle_id
                WHERE a.staff_id = :sid AND c.status != 'FROZEN'
            """),
            {"sid": staff_id},
        ).scalar()

        if alloc_count and alloc_count > 0:
            return {
                "success": False,
                "message": f"Cannot deactivate: staff has {alloc_count} allocations in active cycle",
            }

        session.execute(
            text("UPDATE staff SET is_active = false WHERE id = :sid"),
            {"sid": staff_id},
        )

        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'STAFF_DEACTIVATED', :details)
            """),
            {
                "actor": coordinator_id,
                "details": f'{{"staff_id": {staff_id}}}',
            },
        )
        session.commit()

    logger.info(f"Staff deactivated: id={staff_id}")
    return {"success": True, "message": "Staff deactivated"}
