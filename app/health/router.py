"""
Health check endpoints.
Spec reference: BACKEND_STRUCTURE.md Section 8.2
"""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}


@router.get("/deep")
async def deep_health_check():
    """Deep health check endpoint.
    
    Placeholder for future DB connectivity verification.
    DO NOT implement DB access here until critical files are ready.
    """
    # TODO: Add database connectivity check when app/db/pool.py is implemented
    return {"status": "ok", "database": "not_checked"}
