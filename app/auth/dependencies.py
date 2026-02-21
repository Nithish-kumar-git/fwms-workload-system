"""
Authentication dependencies for FastAPI.
Spec reference: FSB_v1.3.md Section 1.5, BACKEND_STRUCTURE.md Section 3.1

This module provides FastAPI dependencies for:
- Session validation
- Role-based access control (Staff / Coordinator)
- Fresh DB role check on EVERY request (per FSB Section 1.4)
"""

from fastapi import Cookie, HTTPException, Depends
from sqlalchemy import text
from typing import Optional
import logging
from app.auth.session_manager import session_manager
from app.db.session import get_transaction

logger = logging.getLogger(__name__)


class UserInfo:
    """User information from session + database."""
    
    def __init__(self, staff_id: int, email: str, name: str, is_coordinator: bool):
        self.staff_id = staff_id
        self.email = email
        self.name = name
        self.is_coordinator = is_coordinator


async def get_current_user(
    faculty_session: Optional[str] = Cookie(None)
) -> UserInfo:
    """
    Get current authenticated user.
    
    DEVELOPMENT MODE: Auto-authenticates as staff_id=1 (coordinator)
    PRODUCTION MODE: Requires valid session + OAuth
    
    Validates session and queries database for fresh user info.
    Role (is_coordinator) is ALWAYS read from DB, never cached (per FSB Section 1.4).
    
    Args:
        faculty_session: Session ID from cookie
        
    Returns:
        UserInfo with staff_id, email, name, is_coordinator
        
    Raises:
        HTTPException 401: If session is invalid or user not found
    """
    from app.core.config import settings
    
    # DEVELOPMENT-ONLY AUTH BYPASS
    # Explicit opt-in via DEV_AUTH_BYPASS=true (blocked in production by config validation)
    if settings.DEV_AUTH_BYPASS:
        logger.warning("🚨 DEV_AUTH_BYPASS ACTIVE: Auto-authenticating as staff_id=1 (coordinator)")
        return UserInfo(
            staff_id=1,
            email="dev@example.com",
            name="Development User",
            is_coordinator=True
        )
    
    # PRODUCTION AUTH PATH
    # Validate session exists
    if not faculty_session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get staff_id from session
    staff_id = session_manager.get_staff_id(faculty_session)
    if staff_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Query database for fresh user info (CRITICAL: role must be fresh)
    try:
        with get_transaction() as session:
            result = session.execute(
                text("""
                    SELECT id, email, name, is_coordinator
                    FROM staff
                    WHERE id = :staff_id
                """),
                {"staff_id": staff_id}
            ).fetchone()
            
            if result is None:
                # Staff was deleted after session creation
                logger.warning(f"Staff {staff_id} not found in database (orphaned session)")
                raise HTTPException(status_code=401, detail="User not found")
            
            return UserInfo(
                staff_id=result[0],
                email=result[1],
                name=result[2],
                is_coordinator=result[3]
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in get_current_user: {e}")
        raise HTTPException(status_code=500, detail="Authentication error")


async def get_current_staff_id(
    user: UserInfo = Depends(get_current_user)
) -> int:
    """
    Get current staff ID (for staff endpoints).
    
    Args:
        user: Current user from get_current_user dependency
        
    Returns:
        Staff ID
    """
    return user.staff_id


async def get_current_coordinator_id(
    user: UserInfo = Depends(get_current_user)
) -> int:
    """
    Get current coordinator staff ID (for coordinator endpoints).
    
    Enforces is_coordinator=true from database (per FSB Section 1.5).
    
    Args:
        user: Current user from get_current_user dependency
        
    Returns:
        Staff ID (coordinator only)
        
    Raises:
        HTTPException 403: If user is not a coordinator
    """
    if not user.is_coordinator:
        logger.warning(f"Access denied: staff_id={user.staff_id} attempted coordinator action")
        raise HTTPException(
            status_code=403, 
            detail="Coordinator access required"
        )
    
    return user.staff_id
