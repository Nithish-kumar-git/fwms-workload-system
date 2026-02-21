"""
SQLSTATE-to-HTTP error mapper.
Spec reference: FSB_v1.3.md Section 7, Implementation Plan Phase 5

This module maps PostgreSQL error codes to HTTP status codes
and provides client-friendly error messages.
"""

import logging
from typing import Tuple, Optional
from psycopg2 import errors as pg_errors
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# SQLSTATE to HTTP status code mapping (per FSB Section 7)
SQLSTATE_HTTP_MAP = {
    "40001": 409,  # Serialization failure
    "40P01": 409,  # Deadlock detected
    "55P03": 409,  # Lock timeout
    "23505": 409,  # Unique violation (subject already selected)
    "23503": 400,  # Foreign key violation
    "23502": 400,  # Not null violation
}


# Client-friendly error messages (no raw SQL)
ERROR_MESSAGES = {
    "40001": "Concurrent change detected, please try again",
    "40P01": "Concurrent change detected, please try again",
    "55P03": "Request timeout due to high load, please try again",
    "23505": "Subject already selected by another staff member",
    "23503": "Invalid reference (data integrity error)",
    "23502": "Required field missing",
}


def map_db_error_to_http(
    exception: Exception,
    correlation_id: Optional[str] = None
) -> Tuple[int, str, dict]:
    """
    Map database exception to HTTP status code and client-friendly message.
    
    Args:
        exception: Database exception (psycopg2 or SQLAlchemy)
        correlation_id: Request correlation ID for error tracking
        
    Returns:
        Tuple of (status_code, message, details)
    """
    # Extract SQLSTATE from exception
    sqlstate = None
    constraint_name = None
    
    # Try to extract SQLSTATE from psycopg2 exception
    if hasattr(exception, "pgcode"):
        sqlstate = exception.pgcode
    elif hasattr(exception, "orig") and hasattr(exception.orig, "pgcode"):
        # SQLAlchemy wrapped exception
        sqlstate = exception.orig.pgcode
        if hasattr(exception.orig, "diag"):
            constraint_name = exception.orig.diag.constraint_name
    
    # Map SQLSTATE to HTTP status
    if sqlstate in SQLSTATE_HTTP_MAP:
        status_code = SQLSTATE_HTTP_MAP[sqlstate]
        message = ERROR_MESSAGES.get(sqlstate, "Database error")
        
        # Log the error with context
        logger.warning(
            f"Database error mapped to HTTP {status_code}: "
            f"SQLSTATE={sqlstate}, constraint={constraint_name}, "
            f"correlation_id={correlation_id}"
        )
        
        details = {
            "error_code": sqlstate,
            "correlation_id": correlation_id,
        }
        
        return status_code, message, details
    
    # Unknown database error
    logger.error(
        f"Unmapped database error: {exception}, "
        f"SQLSTATE={sqlstate}, correlation_id={correlation_id}"
    )
    
    return 500, "Internal server error", {"correlation_id": correlation_id}


def raise_http_from_db_error(
    exception: Exception,
    correlation_id: Optional[str] = None
):
    """
    Raise HTTPException from database error.
    
    Args:
        exception: Database exception
        correlation_id: Request correlation ID
        
    Raises:
        HTTPException with mapped status code and client-friendly message
    """
    status_code, message, details = map_db_error_to_http(exception, correlation_id)
    raise HTTPException(status_code=status_code, detail=message)
