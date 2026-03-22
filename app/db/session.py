# CRITICAL FCFS FILE — REQUIRES EXTERNAL REVIEW BEFORE DEPLOYMENT
"""
Transaction context manager for FCFS-safe database operations.
Spec reference: BACKEND_STRUCTURE.md Section 5.2

This context manager provides:
- Explicit isolation level control (READ COMMITTED by default)
- 5-second lock timeout to prevent indefinite blocking
- Automatic rollback on exceptions
- Clean connection handling

NOTE: This context manager does NOT auto-commit.
      Callers MUST call session.commit() explicitly.
"""

from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.db.pool import engine

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

_VALID_ISOLATION_LEVELS: frozenset[str] = frozenset({
    "READ COMMITTED",
    "REPEATABLE READ",
    "SERIALIZABLE",
})

@contextmanager
def get_transaction(isolation_level: str = "READ COMMITTED"):
    """
    Transaction context manager (FCFS-safe)
    
    Default: READ COMMITTED (most transactions)
    Override: REPEATABLE READ (only if explicitly needed)
    
    Guarantees:
    - Explicit isolation level (whitelist-validated)
    - 5s lock timeout
    - Automatic rollback on exception
    - Connection always returned clean
    
    IMPORTANT: Caller must call session.commit() explicitly.
    Read-only operations do not need to commit.
    """
    if isolation_level not in _VALID_ISOLATION_LEVELS:
        raise ValueError("Invalid isolation level")

    session = SessionLocal()
    try:
        session.execute(text(f"BEGIN TRANSACTION ISOLATION LEVEL {isolation_level}"))
        session.execute(text("SET LOCAL lock_timeout = '5s'"))
        
        yield session
        
    except Exception:
        session.rollback()
        raise
        
    finally:
        session.close()

