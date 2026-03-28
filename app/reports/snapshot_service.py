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
    Check the 3-stage pipeline status for the active cycle.

    Returns:
        {
            preferences_submitted: bool,
            allocation_complete: bool,
            hod_approved: bool,
            snapshot_id: int | None,
            academic_year: str | None,
            semester_id: int | None,
            is_locked: bool,
            semester_state: str | None,
            preferences_count: int,
            allocations_count: int,
        }
    """
    with get_transaction() as session:
        # Get active cycle (OPEN, ALLOCATED, or FROZEN)
        cycle = session.execute(
            text("""
                SELECT c.id, ay.name, c.semester_id, c.status
                FROM cycle c
                JOIN academic_year ay ON ay.id = c.academic_year_id
                WHERE c.status IN ('OPEN', 'ALLOCATED', 'FROZEN')
                ORDER BY 
                    CASE c.status
                        WHEN 'FROZEN' THEN 1
                        WHEN 'ALLOCATED' THEN 2
                        WHEN 'OPEN' THEN 3
                    END
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
                "semester_id": None,
                "is_locked": False,
                "semester_state": None,
                "preferences_count": 0,
                "allocations_count": 0,
            }

        cycle_id, ay, semester_id, status = cycle
        is_locked = (status == 'FROZEN')

        # Get semester state for the active cycle
        semester_row = session.execute(
            text("""
                SELECT sem.id, sem.state
                FROM semester sem
                WHERE sem.id = :sem_id
                LIMIT 1
            """),
            {"sem_id": semester_id},
        ).fetchone()
        
        semester_state = semester_row[1] if semester_row else None

        # ── Stage 1: preferences_submitted ──
        # Simple check: any preferences exist
        preferences_count = session.execute(
            text("""
                SELECT COUNT(*)
                FROM faculty_preference fp
                JOIN subject_offering so ON so.id = fp.subject_offering_id
                WHERE so.academic_year = :year
                  AND so.semester_id = :sem_id
            """),
            {"year": ay, "sem_id": semester_id},
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
                  AND so.semester_id = :sem_id
            """),
            {"year": ay, "sem_id": semester_id},
        ).scalar()
        
        allocation_complete = (allocations_count > 0)

        # ── Stage 3: hod_approved ──
        # Simple check: snapshot exists
        snapshot_row = session.execute(
            text("""
                SELECT id FROM workload_snapshot
                WHERE academic_year = :year AND semester_id = :sem_id
                LIMIT 1
            """),
            {"year": ay, "sem_id": semester_id},
        ).fetchone()
        hod_approved = snapshot_row is not None
        snapshot_id = snapshot_row[0] if snapshot_row else None

        return {
            "preferences_submitted": preferences_submitted,
            "allocation_complete": allocation_complete,
            "hod_approved": hod_approved,
            "snapshot_id": snapshot_id,
            "academic_year": ay,
            "semester_id": semester_id,
            "is_locked": is_locked,
            "semester_state": semester_state,
            "preferences_count": preferences_count,
            "allocations_count": allocations_count,
        }


# ─── Snapshot Creation ────────────────────────────────────────────────────────

def _build_snapshot_data(session, ay: str, sem_id: int) -> list[dict]:
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
               AND ws.semester_id = :sem_id
            WHERE so.academic_year = :year
              AND so.semester_id = :sem_id
              AND s.is_active = true
            ORDER BY s.emp_code ASC, p.name, sem.label, sec.label
        """),
        {"year": ay, "sem_id": sem_id},
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
               AND ws.semester_id = :sem_id
            WHERE s.emp_code IS NOT NULL
              AND s.is_active = true
              AND s.id NOT IN (
                  SELECT DISTINCT a2.staff_id
                  FROM allocation a2
                  JOIN subject_offering so2 ON so2.id = a2.subject_offering_id
                  WHERE so2.academic_year = :year AND so2.semester_id = :sem_id
              )
            ORDER BY s.emp_code ASC
        """),
        {"year": ay, "sem_id": sem_id},
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
    Create an immutable workload snapshot for the active cycle.

    Steps:
        1. Verify active cycle exists and is not already locked
        2. Verify no snapshot already exists (immutable — one per cycle)
        3. Build snapshot data from live tables
        4. INSERT into workload_snapshot
        5. Lock the cycle (status = 'FROZEN')

    Returns:
        {"snapshot_id": int, "academic_year": str, "semester_id": int}

    Raises:
        RuntimeError on validation failure
    """
    with get_transaction() as session:
        # Get active cycle (OPEN or ALLOCATED, not FROZEN)
        cycle = session.execute(
            text("""
                SELECT c.id, ay.name, c.semester_id, c.status
                FROM cycle c
                JOIN academic_year ay ON ay.id = c.academic_year_id
                WHERE c.status IN ('OPEN', 'ALLOCATED')
                ORDER BY 
                    CASE c.status
                        WHEN 'ALLOCATED' THEN 1
                        WHEN 'OPEN' THEN 2
                    END
                LIMIT 1
            """)
        ).fetchone()

        if not cycle:
            raise RuntimeError("No active cycle found.")

        cycle_id, ay, semester_id, status = cycle

        # Check if snapshot already exists — idempotent: return existing
        existing = session.execute(
            text("""
                SELECT id FROM workload_snapshot
                WHERE academic_year = :year AND semester_id = :sem_id
            """),
            {"year": ay, "sem_id": semester_id},
        ).fetchone()

        if existing:
            return {
                "snapshot_id": existing[0],
                "academic_year": ay,
                "semester_id": semester_id,
                "already_existed": True,
            }

        # Build snapshot data
        snapshot_data = _build_snapshot_data(session, ay, semester_id)

        if not snapshot_data:
            raise RuntimeError(
                "Cannot create snapshot — no allocation data found. "
                "Run allocation first."
            )

        # Insert snapshot (immutable: DB triggers prevent UPDATE/DELETE)
        snapshot_id = session.execute(
            text("""
                INSERT INTO workload_snapshot
                    (academic_year, semester_id, approved_by, snapshot_data)
                VALUES (:year, :sem_id, :approved_by, :data)
                RETURNING id
            """),
            {
                "year": ay, "sem_id": semester_id,
                "approved_by": approved_by,
                "data": json.dumps(snapshot_data),
            },
        ).scalar()

        # Lock the cycle
        session.execute(
            text("""
                UPDATE cycle
                SET status = 'FROZEN', frozen_at = now()
                WHERE id = :cid
            """),
            {"cid": cycle_id},
        )
        
        # Set semester to FROZEN
        session.execute(
            text("""
                UPDATE semester
                SET state = 'FROZEN',
                    frozen_at = now(),
                    frozen_by_staff_id = :hod_id
                WHERE id = :sem_id
            """),
            {"hod_id": approved_by, "sem_id": semester_id}
        )

        session.commit()

        logger.info(
            f"Workload snapshot created: id={snapshot_id}, "
            f"cycle={ay} Sem{semester_id}, approved_by={approved_by}, "
            f"faculty_blocks={len(snapshot_data)}, "
            f"semester FROZEN"
        )

        return {
            "snapshot_id": snapshot_id,
            "academic_year": ay,
            "semester_id": semester_id,
        }


# ─── Snapshot Retrieval ───────────────────────────────────────────────────────

def get_snapshot() -> dict:
    """
    Get the approved snapshot for the active cycle.

    Returns:
        {
            "snapshot_id": int,
            "academic_year": str,
            "semester_id": int,
            "approved_by": int,
            "created_at": str,
            "snapshot_data": list[dict],
        }

    Raises:
        RuntimeError if no active cycle or no snapshot exists.
    """
    with get_transaction() as session:
        # Get active cycle (prefer FROZEN, then ALLOCATED, then OPEN)
        cycle = session.execute(
            text("""
                SELECT ay.name, c.semester_id
                FROM cycle c
                JOIN academic_year ay ON ay.id = c.academic_year_id
                WHERE c.status IN ('OPEN', 'ALLOCATED', 'FROZEN')
                ORDER BY 
                    CASE c.status
                        WHEN 'FROZEN' THEN 1
                        WHEN 'ALLOCATED' THEN 2
                        WHEN 'OPEN' THEN 3
                    END
                LIMIT 1
            """)
        ).fetchone()

        if not cycle:
            raise RuntimeError("No active cycle found.")

        ay, semester_id = cycle

        row = session.execute(
            text("""
                SELECT id, approved_by, snapshot_data, created_at
                FROM workload_snapshot
                WHERE academic_year = :year AND semester_id = :sem_id
                LIMIT 1
            """),
            {"year": ay, "sem_id": semester_id},
        ).fetchone()

        if not row:
            raise RuntimeError(
                f"No approved snapshot for {ay} Sem{semester_id}. "
                "HOD must approve the workload before export."
            )

        return {
            "snapshot_id":   row[0],
            "academic_year": ay,
            "semester_id": semester_id,
            "approved_by":   row[1],
            "created_at":    str(row[3]),
            "snapshot_data": row[2] if isinstance(row[2], list) else json.loads(row[2]),
        }
