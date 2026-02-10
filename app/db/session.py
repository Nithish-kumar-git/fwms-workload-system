# CRITICAL FCFS FILE — REQUIRES EXTERNAL REVIEW BEFORE DEPLOYMENT
"""
Transaction context manager for FCFS-safe database operations.
Spec reference: BACKEND_STRUCTURE.md Section 5.2

This context manager provides:
- Explicit isolation level control (READ COMMITTED by default)
- 5-second lock timeout to prevent indefinite blocking
- Automatic rollback on exceptions
- Clean connection handling
"""

from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.db.pool import engine

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

@contextmanager
def get_transaction(isolation_level: str = "READ COMMITTED"):
    """
    Transaction context manager (FCFS-safe)
    
    Default: READ COMMITTED (most transactions)
    Override: REPEATABLE READ (only if explicitly needed)
    
    Guarantees:
    - Explicit isolation level
    - 5s lock timeout
    - Automatic rollback on exception
    - Connection always returned clean
    """
    session = SessionLocal()
    try:
        session.execute(text(f"BEGIN TRANSACTION ISOLATION LEVEL {isolation_level}"))
        session.execute(text("SET LOCAL lock_timeout = '5s'"))
        
        yield session
        
        session.commit()
        
    except Exception:
        session.rollback()
        raise
        
    finally:
        session.close()
