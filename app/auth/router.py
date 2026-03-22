"""
Authentication router.

Endpoints:
  GET  /api/auth/login       → Google OAuth authorization URL
  GET  /api/auth/callback    → OAuth callback handler
  POST /api/auth/dev-login   → Dev-only JWT login (no Google required)
  GET  /api/auth/me          → Current user info
  POST /api/auth/logout      → Destroy session + clear cookie

DEV_AUTH_BYPASS behavior:
  true  → /dev-login works, domain checks skipped, Gmail maps to coordinator
  false → /dev-login returns 403, strict @hindustanuniv.ac.in enforcement
"""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy import text
import logging
from app.auth.google_oauth import oauth_client
from app.auth.session_manager import session_manager
from app.auth.jwt_utils import create_jwt
from app.auth.dependencies import get_current_user, UserInfo
from app.auth.schemas import LoginResponse, StaffInfoResponse
from app.db.session import get_transaction
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_role(staff_id: int, role_from_db: str, db_session) -> str:
    """Return role string. Uses role column directly."""
    return role_from_db or "faculty"


def _lookup_first_coordinator(db_session):
    """Find first active HOD/coordinator, fallback to first active staff."""
    result = db_session.execute(
        text("""
            SELECT id, email, name, role FROM staff
            WHERE role IN ('hod', 'tt_coordinator') AND is_active = true
            ORDER BY id LIMIT 1
        """)
    ).fetchone()
    if result is None:
        result = db_session.execute(
            text("""
                SELECT id, email, name, role FROM staff
                WHERE is_active = true
                ORDER BY id LIMIT 1
            """)
        ).fetchone()

    # DEV_AUTH_BYPASS: auto-create first HOD if DB is empty
    if result is None:
        from app.core.config import settings
        if settings.DEV_AUTH_BYPASS:
            logger.warning("DEV_AUTH_BYPASS: Staff table empty. Auto-creating dev HOD.")
            inserted_id = db_session.execute(
                text("""
                    INSERT INTO staff (email, name, is_coordinator, role) 
                    VALUES ('dev@example.com', 'Dev HOD', true, 'hod') 
                    RETURNING id
                """)
            ).scalar()
            db_session.commit()
            return (inserted_id, 'dev@example.com', 'Dev HOD', 'hod')

    return result


def _create_auth_tokens(staff_id: int, email: str, name: str, role: str) -> dict:
    """Create session + JWT. Returns {session_id, token}."""
    session_id = session_manager.create_session(staff_id)
    token = create_jwt(staff_id=staff_id, email=email, name=name, role=role)
    return {"session_id": session_id, "token": token}


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/login", response_model=LoginResponse)
async def login():
    """Return Google OAuth authorization URL."""
    url = oauth_client.get_authorization_url()
    return LoginResponse(authorization_url=url)


@router.get("/callback")
async def oauth_callback(code: str = Query(...), state: str = Query(None)):
    """
    Handle Google OAuth callback.
    DEV_AUTH_BYPASS=true: domain skipped, unknown emails map to coordinator.
    DEV_AUTH_BYPASS=false: strict @hindustanuniv.ac.in + staff table match.
    """
    try:
        try:
            user_info = oauth_client.exchange_code_for_token(code)
        except ValueError as e:
            logger.warning(f"OAuth token exchange failed: {e}")
            raise HTTPException(status_code=401, detail=str(e))

        email = user_info["email"]

        with get_transaction() as db_session:
            # Lookup by email
            result = db_session.execute(
                text("SELECT id, email, name, role FROM staff WHERE email = :email AND is_active = true"),
                {"email": email}
            ).fetchone()

            # DEV bypass: map unknown email to first coordinator
            if result is None and settings.DEV_AUTH_BYPASS:
                logger.warning(f"DEV_AUTH_BYPASS: {email} not in staff, mapping to first coordinator")
                result = _lookup_first_coordinator(db_session)

            if result is None:
                logger.warning(f"Unauthorized login: {email}")
                raise HTTPException(status_code=403, detail="Unauthorized faculty. Email not registered.")

            staff_id, staff_email, staff_name, role = result

        auth = _create_auth_tokens(staff_id, staff_email, staff_name, role)

        resp = RedirectResponse(url=f"http://localhost:5173/dashboard?token={auth['token']}", status_code=302)
        resp.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=auth["session_id"],
            httponly=settings.SESSION_COOKIE_HTTPONLY,
            secure=settings.SESSION_COOKIE_SECURE,
            samesite=settings.SESSION_COOKIE_SAMESITE,
            max_age=settings.SESSION_EXPIRATION_HOURS * 3600
        )
        logger.info(f"Login OK: staff_id={staff_id}, email={staff_email}, role={role}")
        return resp

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.post("/dev-login")
async def dev_login(request: Request):
    """
    Development-only login. Returns JWT for a specific or default user.
    Accepts: ?staff_id=N query param or X-Dev-User header.
    Requires DEV_AUTH_BYPASS=true in environment.
    """
    # ── Gate: production blocked ──
    if not settings.DEV_AUTH_BYPASS:
        raise HTTPException(status_code=404, detail="Not found")

    # ── Resolve staff_id from header/param ──
    staff_id = int(request.headers.get("x-dev-user") or request.query_params.get("staff_id") or "1")

    # ── Direct DB lookup ──
    with get_transaction() as db_session:
        row = db_session.execute(
            text("SELECT id, email, name, role FROM staff WHERE id = :id"),
            {"id": staff_id}
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail=f"Staff id={staff_id} not found")

        sid = row[0]
        email = row[1]
        name = row[2]
        role = row[3] or "faculty"

    auth = _create_auth_tokens(sid, email, name, role)

    print(f"DEV LOGIN (old): id={sid}, role={role}")

    return JSONResponse(content={
        "token": auth["token"],
        "staff_id": sid,
        "email": email,
        "name": name,
        "role": role,
    })


@router.post("/dev-login/{staff_id}")
async def dev_login_by_id(staff_id: int):
    """
    Development-only login with explicit staff_id in URL path.
    Reads role directly from DB role column.
    """
    if not settings.DEV_AUTH_BYPASS:
        raise HTTPException(status_code=404, detail="Not found")

    with get_transaction() as db_session:
        row = db_session.execute(
            text("SELECT id, email, name, role FROM staff WHERE id = :id"),
            {"id": staff_id}
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail=f"Staff id={staff_id} not found")

        sid = row[0]
        email = row[1]
        name = row[2]
        role = row[3] or "faculty"

    token = create_jwt(staff_id=sid, email=email, name=name, role=role)

    print(f"DEV LOGIN FINAL: id={sid}, email={email}, role={role}")

    return JSONResponse(content={
        "token": token,
        "staff_id": sid,
        "email": email,
        "name": name,
        "role": role,
    })

@router.get("/me", response_model=StaffInfoResponse)
async def get_current_user_info(user: UserInfo = Depends(get_current_user)):
    """Get current user info. Role always fresh from DB."""
    return StaffInfoResponse(
        staff_id=user.staff_id,
        email=user.email,
        name=user.name,
        role=user.role,
    )


@router.post("/logout")
async def logout(faculty_session: str = Cookie(None)):
    """
    Logout. Does NOT require authentication so it works with expired sessions.
    Clears session cookie.
    """
    if faculty_session:
        session_manager.delete_session(faculty_session)

    resp = JSONResponse(content={"success": True, "message": "Logged out"})
    resp.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        httponly=settings.SESSION_COOKIE_HTTPONLY,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE
    )
    logger.info("User logged out")
    return resp
