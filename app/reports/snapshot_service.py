"""
Snapshot service — immutable workload snapshots for export.

Pipeline stages:
  1. Faculty preferences submitted
  2. Coordinator allocation complete
  3. HOD approval → snapshot created, cycle locked

All exports read from snapshot ONLY. No live-table queries during export.
"""

from __future__ import annotations
import json
import logging
from typing import Optional
from collections import defaultdict

from sqlalchemy import text
from app.db.session import get_transaction

logger = logging.getLogger(__name__)


# ─── Pipeline Status ──────────────────────────────────────────────────────────

def get_pipeline_status() -> dict:
    """
    Check the 3-stage pipeline status for the active academic cycle.

    Returns:
        {
            preferences_submitted: bool,
            allocation_complete: bool,
            hod_approved: bool,
            snapshot_id: int | None,
            academic_year: str | None,
            semester_type: str | None,
            is_locked: bool,
            semester_state: str | None,
            semester_id: int | None,
            preferences_count: int,
            allocations_count: int,
        }
    """
    with get_transaction() as session:
        # Get active cycle
        cycle = session.execute(
            text("""
                SELECT id, academic_year, semester_type,
                       COALESCE(is_locked, false) AS is_locked
                FROM academic_cycle
                WHERE is_active = true
                LIMIT 1
            """)
        ).fetchone()

        if not cycle:
            return {
                "preferences_submitted": False,
                "allocation_complete": False,
                "hod_approved": False,
                "snapshot_id": None,
                "academic_year": None,
                "semester_type": None,
                "is_locked": False,
                "semester_state": None,
                "semester_id": None,
                "preferences_count": 0,
                "allocations_count": 0,
            }

        cycle_id, ay, st, is_locked = cycle

        # Get semester state for the active cycle
        semester_row = session.execute(
            text("""
                SELECT DISTINCT sem.id, sem.state
                FROM semester sem
                JOIN subject_offering so ON so.semester_id = sem.id
                WHERE so.academic_year = :year
                  AND so.semester_type = :sem_type
                LIMIT 1
            """),
            {"year": ay, "sem_type": st},
        ).fetchone()
        
        semester_id = semester_row[0] if semester_row else None
        semester_state = semester_row[1] if semester_row else None

        # ── Stage 1: preferences_submitted ──
        # Simple check: any preferences exist
        preferences_count = session.execute(
            text("""
                SELECT COUNT(*)
                FROM faculty_preference fp
                JOIN subject_offering so ON so.id = fp.subject_offering_id
                WHERE so.academic_year = :year
                  AND so.semester_type = :sem_type
            """),
            {"year": ay, "sem_type": st},
        ).scalar()
        
        preferences_submitted = (preferences_count > 0)

        # ── Stage 2: allocation_complete ──
        # Simple check: any allocations exist
        allocations_count = session.execute(
            text("""
                SELECT COUNT(*)
                FROM allocation a
                JOIN subject_offering so ON so.id = a.subject_offering_id
                WHERE so.academic_year = :year
                  AND so.semester_type = :sem_type
            """),
            {"year": ay, "sem_type": st},
        ).scalar()
        
        allocation_complete = (allocations_count > 0)

        # ── Stage 3: hod_approved ──
        # Simple check: snapshot exists
        snapshot_row = session.execute(
            text("""
                SELECT id FROM workload_snapshot
                WHERE academic_year = :year AND semester_type = :sem_type
                LIMIT 1
            """),
            {"year": ay, "sem_type": st},
        ).fetchone()
        hod_approved = snapshot_row is not None
        snapshot_id = snapshot_row[0] if snapshot_row else None

        return {
            "preferences_submitted": preferences_submitted,
            "allocation_complete": allocation_complete,
            "hod_approved": hod_approved,
            "snapshot_id": snapshot_id,
            "academic_year": ay,
            "semester_type": st,
            "is_locked": is_locked,
            "semester_state": semester_state,
            "semester_id": semester_id,
            "preferences_count": preferences_count,
            "allocations_count": allocations_count,
        }


# ─── Snapshot Creation ────────────────────────────────────────────────────────

def _build_snapshot_data(session, ay: str, st: str) -> list[dict]:
    """
    Build the snapshot JSON from live tables.
    Uses the SAME data logic as the Excel generator.
    Returns a list of faculty block dicts ready for JSONB storage.
    """
    rows = session.execute(
        text("""
            SELECT
                s.id            AS staff_id,
                s.emp_code,
                s.name          AS faculty_name,
                s.designation,
                p.ug_pg,
                p.name          AS programme,
                COALESCE(sub.course_category, '')  AS course_category,
                sem.label       AS semester,
                sec.label       AS section,
                COALESCE(so.student_strength, 0)   AS student_strength,
                sub.code        AS course_code,
                sub.name        AS course_name,
                COALESCE(a.complexity, '')          AS complexity,
                COALESCE(sub.credits, 0)           AS credits,
                COALESCE(a.l_assigned, 0)           AS l_assigned,
                COALESCE(a.t_assigned, 0)           AS t_assigned,
                COALESCE(a.p_assigned, 0)           AS p_assigned,
                COALESCE(ws.norm_hours, 12)         AS norm_hours,
                COALESCE(ws.other_academic, 0)      AS other_academic,
                COALESCE(ws.remarks, '')             AS remarks,
                ws.research_scholars
            FROM allocation a
            JOIN subject_offering so ON so.id = a.subject_offering_id
            JOIN subject sub         ON sub.id = so.subject_id
            JOIN program p           ON p.id = so.program_id
            JOIN semester sem        ON sem.id = so.semester_id
            JOIN section sec         ON sec.id = so.section_id
            JOIN staff s             ON s.id = a.staff_id
            LEFT JOIN workload_summary ws
                ON ws.staff_id = s.id
               AND ws.academic_year = :year
               AND ws.semester_type = :sem_type
            WHERE so.academic_year = :year
              AND so.semester_type = :sem_type
              AND s.is_active = true
            ORDER BY s.emp_code ASC, p.name, sem.label, sec.label
        """),
        {"year": ay, "sem_type": st},
    ).fetchall()

    # Parse into flat dicts
    flat = []
    for r in rows:
        l_val = r[14] or 0
        t_val = r[15] or 0
        p_val = r[16] or 0
        ltp = l_val + t_val + p_val

        flat.append({
            "staff_id":         r[0],
            "emp_code":         r[1] or "",
            "faculty_name":     r[2] or "",
            "designation":      r[3] or "",
            "ug_pg":            r[4] or "",
            "programme":        r[5] or "",
            "course_category":  r[6],
            "semester":         r[7] or "",
            "section":          r[8] or "",
            "student_strength": r[9],
            "course_code":      r[10] or "",
            "course_name":      r[11] or "",
            "complexity":       r[12],
            "credits":          r[13],
            "l":                l_val,
            "t":                t_val,
            "p":                p_val,
            "ltp":              ltp,
            "tch":              ltp,
            "norm_hours":       r[17],
            "other_academic":   r[18],
            "remarks":          r[19],
        })

    # Also fetch unassigned faculty
    unassigned = session.execute(
        text("""
            SELECT s.id, s.emp_code, s.name, s.designation,
                   COALESCE(ws.norm_hours, 12),
                   COALESCE(ws.other_academic, 0),
                   COALESCE(ws.remarks, '')
            FROM staff s
            LEFT JOIN workload_summary ws
                ON ws.staff_id = s.id
               AND ws.academic_year = :year
               AND ws.semester_type = :sem_type
            WHERE s.emp_code IS NOT NULL
              AND s.is_active = true
              AND s.id NOT IN (
                  SELECT DISTINCT a2.staff_id
                  FROM allocation a2
                  JOIN subject_offering so2 ON so2.id = a2.subject_offering_id
                  WHERE so2.academic_year = :year AND so2.semester_type = :sem_type
              )
            ORDER BY s.emp_code ASC
        """),
        {"year": ay, "sem_type": st},
    ).fetchall()

    for r in unassigned:
        flat.append({
            "staff_id":         r[0],
            "emp_code":         r[1] or "",
            "faculty_name":     r[2] or "",
            "designation":      r[3] or "",
            "ug_pg":            "", "programme":       "", "course_category": "",
            "semester":         "", "section":         "",
            "student_strength": 0,  "course_code":     "", "course_name":     "",
            "complexity":       "", "credits":         0,
            "l": 0, "t": 0, "p": 0, "ltp": 0, "tch": 0,
            "norm_hours":       r[4],
            "other_academic":   r[5],
            "remarks":          r[6],
        })

    # Group by faculty
    grouped = defaultdict(list)
    meta = {}
    for row in flat:
        sid = row["staff_id"]
        grouped[sid].append(row)
        if sid not in meta:
            meta[sid] = {
                "emp_code":      row["emp_code"],
                "faculty_name":  row["faculty_name"],
                "designation":   row["designation"],
                "norm_hours":    row["norm_hours"],
                "other_academic": row["other_academic"],
                "remarks":       row["remarks"],
            }

    blocks = []
    serial = 0
    for sid, fac_rows in grouped.items():
        serial += 1
        m = meta[sid]
        total_tch = sum(r["tch"] for r in fac_rows)
        min_wl = m["norm_hours"]
        deviation = total_tch - min_wl
        total_workload = total_tch + m["other_academic"]

        subject_rows = [r for r in fac_rows if r["course_code"]]
        # Build compact subject list for JSON (no staff_id duplication)
        subjects_json = []
        for s in (subject_rows if subject_rows else fac_rows):
            subjects_json.append({
                "ug_pg":           s["ug_pg"],
                "programme":       s["programme"],
                "course_category": s["course_category"],
                "semester":        s["semester"],
                "section":         s["section"],
                "student_strength": s["student_strength"],
                "course_code":     s["course_code"],
                "course_name":     s["course_name"],
                "complexity":      s["complexity"],
                "credits":         s["credits"],
                "l":               s["l"],
                "t":               s["t"],
                "p":               s["p"],
                "ltp":             s["ltp"],
                "tch":             s["tch"],
            })

        blocks.append({
            "serial":         serial,
            "emp_code":       m["emp_code"],
            "faculty_name":   m["faculty_name"],
            "designation":    m["designation"],
            "min_workload":   min_wl,
            "deviation":      deviation,
            "remarks":        m["remarks"],
            "other_academic": m["other_academic"],
            "total_workload": total_workload,
            "total_tch":      total_tch,
            "subjects":       subjects_json,
        })

    blocks.sort(key=lambda b: b["emp_code"])
    return blocks


def create_snapshot(approved_by: int) -> dict:
    """
    Create an immutable workload snapshot for the active academic cycle.

    Steps:
        1. Verify active cycle exists and is not already locked
        2. Verify no snapshot already exists (immutable — one per cycle)
        3. Build snapshot data from live tables
        4. INSERT into workload_snapshot
        5. Lock the academic_cycle (is_locked = true)

    Returns:
        {"snapshot_id": int, "academic_year": str, "semester_type": str}

    Raises:
        RuntimeError on validation failure
    """
    with get_transaction() as session:
        # Get active cycle
        cycle = session.execute(
            text("""
                SELECT id, academic_year, semester_type,
                       COALESCE(is_locked, false) AS is_locked
                FROM academic_cycle
                WHERE is_active = true
                LIMIT 1
            """)
        ).fetchone()

        if not cycle:
            raise RuntimeError("No active academic cycle found.")

        cycle_id, ay, st, is_locked = cycle

        # Check if snapshot already exists — idempotent: return existing
        existing = session.execute(
            text("""
                SELECT id FROM workload_snapshot
                WHERE academic_year = :year AND semester_type = :sem_type
            """),
            {"year": ay, "sem_type": st},
        ).fetchone()

        if existing:
            return {
                "snapshot_id": existing[0],
                "academic_year": ay,
                "semester_type": st,
                "already_existed": True,
            }

        # Build snapshot data
        snapshot_data = _build_snapshot_data(session, ay, st)

        if not snapshot_data:
            raise RuntimeError(
                "Cannot create snapshot — no allocation data found. "
                "Run allocation first."
            )

        # Insert snapshot (immutable: DB triggers prevent UPDATE/DELETE)
        snapshot_id = session.execute(
            text("""
                INSERT INTO workload_snapshot
                    (academic_year, semester_type, approved_by, snapshot_data)
                VALUES (:year, :sem_type, :approved_by, :data)
                RETURNING id
            """),
            {
                "year": ay, "sem_type": st,
                "approved_by": approved_by,
                "data": json.dumps(snapshot_data),
            },
        ).scalar()

        # Lock the cycle
        session.execute(
            text("""
                UPDATE academic_cycle
                SET is_locked = true
                WHERE id = :cid
            """),
            {"cid": cycle_id},
        )
        
        # Set ALL semesters to FROZEN
        session.execute(
            text("""
                UPDATE semester
                SET state = 'FROZEN',
                    frozen_at = now(),
                    frozen_by_staff_id = :hod_id
            """),
            {"hod_id": approved_by}
        )

        session.commit()

        logger.info(
            f"Workload snapshot created: id={snapshot_id}, "
            f"cycle={ay} {st}, approved_by={approved_by}, "
            f"faculty_blocks={len(snapshot_data)}, "
            f"all semesters FROZEN"
        )

        return {
            "snapshot_id": snapshot_id,
            "academic_year": ay,
            "semester_type": st,
        }


# ─── Snapshot Retrieval ───────────────────────────────────────────────────────

def get_snapshot() -> dict:
    """
    Get the approved snapshot for the active academic cycle.

    Returns:
        {
            "snapshot_id": int,
            "academic_year": str,
            "semester_type": str,
            "approved_by": int,
            "created_at": str,
            "snapshot_data": list[dict],
        }

    Raises:
        RuntimeError if no active cycle or no snapshot exists.
    """
    with get_transaction() as session:
        cycle = session.execute(
            text("""
                SELECT academic_year, semester_type
                FROM academic_cycle
                WHERE is_active = true
                LIMIT 1
            """)
        ).fetchone()

        if not cycle:
            raise RuntimeError("No active academic cycle found.")

        ay, st = cycle

        row = session.execute(
            text("""
                SELECT id, approved_by, snapshot_data, created_at
                FROM workload_snapshot
                WHERE academic_year = :year AND semester_type = :sem_type
                LIMIT 1
            """),
            {"year": ay, "sem_type": st},
        ).fetchone()

        if not row:
            raise RuntimeError(
                f"No approved snapshot for {ay} {st}. "
                "HOD must approve the workload before export."
            )

        return {
            "snapshot_id":   row[0],
            "academic_year": ay,
            "semester_type": st,
            "approved_by":   row[1],
            "created_at":    str(row[3]),
            "snapshot_data": row[2] if isinstance(row[2], list) else json.loads(row[2]),
        }
