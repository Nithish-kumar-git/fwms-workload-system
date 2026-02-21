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
    
    # TODO: Include additional routers when implemented:
    # app.include_router(staff_router.router)
    # app.include_router(audit_router.router)
    
    return app


app = create_app()


@app.on_event("startup")
async def startup_event():
    """Application startup handler."""
    # Configure structured logging (production-grade)
    configure_logging()
    logger.info("Faculty Subject Selection System starting up")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown handler."""
    logger.info("Faculty Subject Selection System shutting down")
