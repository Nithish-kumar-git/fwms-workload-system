"""
Health check endpoints.
Spec reference: BACKEND_STRUCTURE.md Section 8.2
Window metrics reference: window_lifecycle_design.md Section 13
"""

from fastapi import APIRouter
from sqlalchemy import text
from app.db.session import get_transaction
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "fwms-api"}


@router.get("/deep")
async def deep_health_check():
    """Deep health check — verifies actual database connectivity."""
    db_status = "error"
    db_error = None

    try:
        with get_transaction() as session:
            session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_error = str(e)[:200]
        logger.warning(f"Deep health check: database unreachable — {db_error}")

    result = {"status": "ok" if db_status == "ok" else "degraded", "database": db_status}
    if db_error:
        result["database_error"] = db_error

    return result


@router.get("/metrics")
async def health_metrics():
    """
    Production health metrics endpoint.
    
    Returns:
    - Expired OPEN windows (status='OPEN' but now() > end_time)
    - Stuck SCHEDULED windows (status='SCHEDULED' but now() > start_time)
    - Total window counts by status
    
    Spec reference: window_lifecycle_design.md Section 13
    """
    try:
        with get_transaction() as session:
            # Metric 1: Expired OPEN windows
            expired_open = session.execute(
                text("""
                    SELECT 
                        id,
                        name,
                        batch_id,
                        specialization_id,
                        end_time,
                        EXTRACT(EPOCH FROM (now() - end_time)) AS expired_seconds
                    FROM selection_window
                    WHERE status = 'OPEN'
                      AND now() > end_time
                    ORDER BY end_time ASC
                """)
            ).fetchall()
            
            expired_open_list = [
                {
                    "window_id": row[0],
                    "name": row[1],
                    "batch_id": row[2],
                    "specialization_id": row[3],
                    "end_time": row[4].isoformat() if row[4] else None,
                    "expired_seconds": int(row[5]) if row[5] else 0
                }
                for row in expired_open
            ]
            
            # Metric 2: Stuck SCHEDULED windows
            stuck_scheduled = session.execute(
                text("""
                    SELECT 
                        id,
                        name,
                        batch_id,
                        specialization_id,
                        start_time,
                        EXTRACT(EPOCH FROM (now() - start_time)) AS overdue_seconds
                    FROM selection_window
                    WHERE status = 'SCHEDULED'
                      AND now() > start_time
                    ORDER BY start_time ASC
                """)
            ).fetchall()
            
            stuck_scheduled_list = [
                {
                    "window_id": row[0],
                    "name": row[1],
                    "batch_id": row[2],
                    "specialization_id": row[3],
                    "start_time": row[4].isoformat() if row[4] else None,
                    "overdue_seconds": int(row[5]) if row[5] else 0
                }
                for row in stuck_scheduled
            ]
            
            # Metric 3: Window counts by status
            status_counts = session.execute(
                text("""
                    SELECT status, COUNT(*) as count
                    FROM selection_window
                    GROUP BY status
                    ORDER BY status
                """)
            ).fetchall()
            
            status_summary = {row[0]: row[1] for row in status_counts}
            
            # Metric 4: Total active selections
            active_selections = session.execute(
                text("SELECT COUNT(*) FROM subject_selection")
            ).scalar()
            
            return {
                "status": "ok",
                "timestamp": "now()",  # Will be replaced by actual timestamp in response
                "windows": {
                    "expired_open": {
                        "count": len(expired_open_list),
                        "details": expired_open_list,
                        "alert": len(expired_open_list) > 0,
                        "message": "Coordinators should close expired windows" if expired_open_list else None
                    },
                    "stuck_scheduled": {
                        "count": len(stuck_scheduled_list),
                        "details": stuck_scheduled_list,
                        "alert": len(stuck_scheduled_list) > 0,
                        "message": "Coordinators should open overdue windows" if stuck_scheduled_list else None
                    },
                    "status_summary": status_summary
                },
                "selections": {
                    "total_active": active_selections
                }
            }
    
    except Exception as e:
        logger.error(f"Health metrics error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": "Internal error",
            "windows": None,
            "selections": None
        }
