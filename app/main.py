"""
FastAPI application entry point.
Spec reference: BACKEND_STRUCTURE.md Section 2
"""

from fastapi import FastAPI
from app.core.logging_config import setup_logging
from app.health import router as health_router
import logging

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Faculty Subject Selection System",
        description="Production-critical FCFS-based subject allocation system",
        version="1.0.0"
    )
    
    # Include routers
    app.include_router(health_router.router)
    
    # TODO: Include additional routers when implemented:
    # app.include_router(auth_router.router)
    # app.include_router(staff_router.router)
    # app.include_router(selection_router.router)
    # app.include_router(coordinator_router.router)
    
    return app


app = create_app()


@app.on_event("startup")
async def startup_event():
    """Application startup handler."""
    setup_logging()
    logger.info("Faculty Subject Selection System starting up")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown handler."""
    logger.info("Faculty Subject Selection System shutting down")
