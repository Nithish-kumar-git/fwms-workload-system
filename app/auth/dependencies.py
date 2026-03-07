"""
Authentication dependencies for FastAPI (PRODUCTION).
Spec reference: FSB_v1.3.md Section 1.5, BACKEND_STRUCTURE.md Section 3.1

Supports dual authentication:
- Session cookie (faculty_session) — set by OAuth callback
- JWT Bearer token (Authorization: Bearer <token>) — returned by callback

Role is ALWAYS read fresh from DB on every request.
"""

from fastapi import Cookie, HTTPException, Depends, Header
from sqlalchemy import text
from typing import Optional
import logging
from app.auth.session_manager import session_manager
from app.auth.jwt_utils import verify_jwt
from app.db.session import get_transaction

logger = logging.getLogger(__name__)


class UserInfo:
    """User information from session + database."""
    
    def __init__(self, staff_id: int, email: str, name: str, is_coordinator: bool, role: str = "faculty"):
        self.staff_id = staff_id
        self.email = email
        self.name = name
        self.is_coordinator = is_coordinator
        self.role = role


async def get_current_user(
    faculty_session: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
) -> UserInfo:
    """
    Get current authenticated user.
    
    Checks in order:
    1. JWT Bearer token from Authorization header
    2. Session cookie
    
    Role is ALWAYS read from DB (never trust cached/token role alone).
    
    Raises:
        HTTPException 401: If no valid auth found
    """
    from app.core.config import settings
    
    # DEV AUTH BYPASS (blocked in production by config validation)
    if settings.DEV_AUTH_BYPASS:
        logger.warning("🚨 DEV_AUTH_BYPASS ACTIVE: Auto-authenticating as staff_id=1")
        return UserInfo(
            staff_id=1,
            email="dev@example.com",
            name="Development User",
            is_coordinator=True,
            role="coordinator"
        )
    
    staff_id = None
    
    # PATH 1: JWT Bearer token
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        payload = verify_jwt(token)
        if payload and "sub" in payload:
            staff_id = int(payload["sub"])
    
    # PATH 2: Session cookie
    if staff_id is None and faculty_session:
        staff_id = session_manager.get_staff_id(faculty_session)
    
    # No valid auth
    if staff_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Fresh DB lookup (role is NEVER cached)
    try:
        with get_transaction() as session:
            result = session.execute(
                text("""
                    SELECT s.id, s.email, s.name, s.is_coordinator
                    FROM staff s
                    WHERE s.id = :staff_id AND s.is_active = true
                """),
                {"staff_id": staff_id}
            ).fetchone()
            
            if result is None:
                logger.warning(f"Staff {staff_id} not found (orphaned session)")
                raise HTTPException(status_code=401, detail="User not found")
            
            is_coordinator = result[3]
            
            # Resolve full role
            role = "faculty"
            if is_coordinator:
                role = "coordinator"
            else:
                role_row = session.execute(
                    text("""
                        SELECT role_name FROM faculty_role
                        WHERE staff_id = :sid AND role_name = 'HOD'
                        LIMIT 1
                    """),
                    {"sid": result[0]}
                ).fetchone()
                if role_row:
                    role = "hod"
            
            return UserInfo(
                staff_id=result[0],
                email=result[1],
                name=result[2],
                is_coordinator=is_coordinator,
                role=role
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in get_current_user: {e}")
        raise HTTPException(status_code=500, detail="Authentication error")


async def get_current_staff_id(
    user: UserInfo = Depends(get_current_user)
) -> int:
    """Get current staff ID (for staff endpoints)."""
    return user.staff_id


async def get_current_coordinator_id(
    user: UserInfo = Depends(get_current_user)
) -> int:
    """
    Get current coordinator staff ID (for coordinator endpoints).
    Enforces is_coordinator=true from database.
    """
    if not user.is_coordinator:
        logger.warning(f"Access denied: staff_id={user.staff_id} attempted coordinator action")
        raise HTTPException(
            status_code=403, 
            detail="Coordinator access required"
        )
    return user.staff_id
