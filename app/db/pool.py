# CRITICAL FCFS FILE — REQUIRES EXTERNAL REVIEW BEFORE DEPLOYMENT
"""
PostgreSQL connection pool configuration.
Spec reference: BACKEND_STRUCTURE.md Section 5.1

This file implements the database connection pool using SQLAlchemy.
Conservative pool sizing is used to prevent connection exhaustion.
"""

from sqlalchemy import create_engine
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    
    # CONSERVATIVE pool sizing (adjust after load testing)
    pool_size=settings.POOL_SIZE,              # Default: 10
    max_overflow=settings.POOL_MAX_OVERFLOW,   # Default: 20 (total 30)
    pool_timeout=5,                            # Fail fast
    
    # Connection health
    pool_pre_ping=True,        # Test connection before use
    pool_recycle=3600,         # Recycle after 1 hour
    
    # Performance
    echo=False,                # Disable SQL logging in production
    
    # Isolation (set per-transaction, not globally)
    isolation_level=None,
)
