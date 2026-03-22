"""
Authentication dependencies for FastAPI.

3-Role System: faculty / tt_coordinator / hod
Role is ALWAYS read fresh from DB on every request.
"""

from fastapi import Cookie, HTTPException, Depends, Header, Request
from sqlalchemy import text
from typing import Optional
import logging
from app.auth.session_manager import session_manager
from app.auth.jwt_utils import verify_jwt
from app.db.session import get_transaction

logger = logging.getLogger(__name__)


class UserInfo:
    """User information from session + database."""

    def __init__(self, staff_id: int, email: str, name: str, role: str):
        self.staff_id = staff_id
        self.email = email
        self.name = name
        self.role = role
        # Derived convenience flags
        self.is_hod = role == "hod"
        self.is_coordinator = role in ("tt_coordinator", "hod")
        self.is_faculty = role == "faculty"


def _lookup_staff_by_id(staff_id: int) -> UserInfo:
    """Fresh DB lookup for a staff member by ID. Returns UserInfo with role from DB."""
    with get_transaction() as session:
        row = session.execute(
            text("SELECT id, email, name, role FROM staff WHERE id = :id"),
            {"id": staff_id}
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=401, detail=f"Staff {staff_id} not found")

        return UserInfo(
            staff_id=row[0],
            email=row[1],
            name=row[2],
            role=row[3] or "faculty"
        )


async def get_current_user(
    request: Request,
    faculty_session: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
) -> UserInfo:
    """
    Get current authenticated user.

    DEV_AUTH_BYPASS: Allows login without token, but respects JWT if present.
    Production: JWT Bearer token or session cookie required.
    Role is ALWAYS read fresh from DB.
    """
    from app.core.config import settings

    staff_id = None

    # PATH 1: JWT Bearer token (check first, even in dev mode)
    if authorization and authorization.startswith("Bearer "):
        payload = verify_jwt(authorization[7:])
        if payload and "sub" in payload:
            staff_id = int(payload["sub"])
            logger.info(f"JWT auth: staff_id={staff_id}")

    # PATH 2: Session cookie
    if staff_id is None and faculty_session:
        staff_id = session_manager.get_staff_id(faculty_session)
        if staff_id:
            logger.info(f"Session auth: staff_id={staff_id}")

    # PATH 3: DEV AUTH BYPASS (only if no token provided)
    if staff_id is None and settings.DEV_AUTH_BYPASS:
        logger.warning("DEV_AUTH_BYPASS: No token provided, returning mock coordinator user")
        return UserInfo(
            staff_id=1,
            email="dev@example.com",
            name="Dev User",
            role="tt_coordinator"
        )

    # No authentication found
    if staff_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return _lookup_staff_by_id(staff_id)


# ─── Permission Guards ───


async def get_current_staff_id(
    user: UserInfo = Depends(get_current_user)
) -> int:
    """Get current staff ID (any authenticated user)."""
    return user.staff_id


async def get_current_hod(
    user: UserInfo = Depends(get_current_user)
) -> UserInfo:
    """Require HOD role. Returns full UserInfo."""
    if user.role != "hod":
        logger.warning(f"HOD access denied: staff_id={user.staff_id}, role={user.role}")
        raise HTTPException(status_code=403, detail="HOD access required")
    return user


async def get_current_hod_id(
    user: UserInfo = Depends(get_current_hod)
) -> int:
    """Require HOD role. Returns staff_id."""
    return user.staff_id


async def get_current_coordinator(
    user: UserInfo = Depends(get_current_user)
) -> UserInfo:
    """Require coordinator or HOD role. Returns full UserInfo."""
    if user.role not in ("tt_coordinator", "hod"):
        logger.warning(f"Coordinator access denied: staff_id={user.staff_id}, role={user.role}")
        raise HTTPException(status_code=403, detail="Coordinator access required")
    return user


async def get_current_coordinator_id(
    user: UserInfo = Depends(get_current_coordinator)
) -> int:
    """Require coordinator or HOD role. Returns staff_id."""
    return user.staff_id


async def get_current_faculty(
    user: UserInfo = Depends(get_current_user)
) -> UserInfo:
    """Require faculty role. Returns full UserInfo."""
    if user.role != "faculty":
        logger.warning(f"Faculty access denied: staff_id={user.staff_id}, role={user.role}")
        raise HTTPException(status_code=403, detail="Faculty access required")
    return user
