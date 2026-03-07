"""
FastAPI application entry point.
Spec reference: BACKEND_STRUCTURE.md Section 2

PRODUCTION BUILD - Integrated middleware:
- Correlation ID tracking
- Structured logging
- Error handling
"""

from fastapi import FastAPI
from app.core.logging_config import configure_logging
from app.core.correlation_middleware import CorrelationIDMiddleware
from app.health import router as health_router
from app.auth import router as auth_router
from app.selection import router as selection_router
from app.coordinator import router as coordinator_router
from app.coordinator import window_router
from app.preference import router as preference_router
from app.preference import window_router as pref_window_router
from app.allocation import router as allocation_router
from app.admin import router as admin_router
from app.admin import cycle_router
from app.admin import staff_router
from app.reports import router as reports_router
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Faculty Subject Selection System",
        description="Production-critical FCFS-based subject allocation system",
        version="1.0.0"
    )
    
    # Add middleware (order matters: last added = first executed)
    app.add_middleware(CorrelationIDMiddleware)
    
    # Include routers
    app.include_router(health_router.router)
    app.include_router(auth_router.router)
    app.include_router(selection_router.router)
    app.include_router(coordinator_router.router)
    app.include_router(window_router.router, prefix="/api")
    app.include_router(preference_router.router)
    app.include_router(pref_window_router.router)
    app.include_router(allocation_router.router)
    app.include_router(admin_router.router)
    app.include_router(cycle_router.router)
    app.include_router(staff_router.router)
    app.include_router(reports_router.router)
    
    # TODO: Include additional routers when implemented:
    # app.include_router(staff_router.router)
    # app.include_router(audit_router.router)
    
    return app


app = create_app()


@app.on_event("startup")
async def startup_event():
    """Application startup handler."""
    configure_logging()
    logger.info("Faculty Subject Selection System starting up")
    
    # ── Auth diagnostic ──
    auth_mode = "DEV" if settings.DEV_AUTH_BYPASS else "PRODUCTION"
    logger.info(f"DEV_AUTH_BYPASS={settings.DEV_AUTH_BYPASS}")
    logger.info(f"AUTH_MODE={auth_mode}")
    if settings.DEV_AUTH_BYPASS:
        logger.warning("⚠ DEV AUTH BYPASS IS ACTIVE — domain restrictions disabled")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown handler."""
    logger.info("Faculty Subject Selection System shutting down")
