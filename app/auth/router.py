"""
Authentication router (PRODUCTION).
Spec reference: FSB_v1.3.md Section 1, BACKEND_STRUCTURE.md Section 3.1

This module implements Google OAuth 2.0 flow:
- Login redirect to Google
- OAuth callback handler
- Logout (session destruction)
- Current user info endpoint
"""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import text
import logging
from app.auth.google_oauth import oauth_client
from app.auth.session_manager import session_manager
from app.auth.dependencies import get_current_user, UserInfo
from app.auth.schemas import LoginResponse, StaffInfoResponse, LogoutResponse
from app.db.session import get_transaction
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/login", response_model=LoginResponse)
async def login():
    """
    Initiate Google OAuth login flow.
    
    Redirects user to Google OAuth consent screen.
    Per FSB Section 1.2, exact URL:
    https://accounts.google.com/o/oauth2/v2/auth
    """
    authorization_url = oauth_client.get_authorization_url()
    
    # Return redirect URL (frontend will handle redirect)
    return LoginResponse(authorization_url=authorization_url)


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(None),
    response: Response = None
):
    """
    Handle Google OAuth callback.
    
    Per FSB Section 1.2:
    1. Verify Google token
    2. Extract email
    3. Validate email domain (@hindustanuniv.ac.in)
    4. Query staff table
    5. Create server-side session
    6. Redirect to /dashboard
    
    Raises:
        HTTPException 401: If token invalid or email not allowed
        HTTPException 404: If staff not found in database
    """
    try:
        # Exchange authorization code for tokens, then verify ID token
        # This performs: code → POST to Google → id_token → verify + domain check
        try:
            user_info = oauth_client.exchange_code_for_token(code)
        except ValueError as e:
            logger.warning(f"OAuth token exchange failed: {e}")
            raise HTTPException(status_code=401, detail=str(e))
        
        email = user_info["email"]
        
        # Query staff table to get staff_id
        with get_transaction() as session:
            result = session.execute(
                text("""
                    SELECT id, email, name, is_coordinator
                    FROM staff
                    WHERE email = :email
                """),
                {"email": email}
            ).fetchone()
            
            if result is None:
                logger.warning(f"Staff not found for email: {email}")
                raise HTTPException(
                    status_code=404,
                    detail="Staff member not found. Please contact administrator."
                )
            
            staff_id = result[0]
        
        # Create server-side session (per FSB Section 1.4)
        session_id = session_manager.create_session(staff_id)
        
        # Set session cookie
        response_obj = RedirectResponse(url="/dashboard", status_code=302)
        response_obj.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_id,
            httponly=settings.SESSION_COOKIE_HTTPONLY,
            secure=settings.SESSION_COOKIE_SECURE,
            samesite=settings.SESSION_COOKIE_SAMESITE,
            max_age=settings.SESSION_EXPIRATION_HOURS * 3600
        )
        
        logger.info(f"User logged in: staff_id={staff_id}, email={email}")
        return response_obj
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/me", response_model=StaffInfoResponse)
async def get_current_user_info(
    user: UserInfo = Depends(get_current_user)
):
    """
    Get current authenticated user info (PRODUCTION).
    
    Returns fresh user data from database (per FSB Section 1.4).
    Role (is_coordinator) is NEVER cached.
    """
    return StaffInfoResponse(
        staff_id=user.staff_id,
        email=user.email,
        name=user.name,
        is_coordinator=user.is_coordinator
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    user: UserInfo = Depends(get_current_user),
    faculty_session: str = Cookie(None),
    response: Response = None
):
    """
    Logout (destroy session).
    
    Per FSB Section 1.4:
    - Delete session key from Redis/memory
    - Clear session cookie
    """
    # Invalidate session server-side
    if faculty_session:
        session_manager.delete_session(faculty_session)
    
    # Clear session cookie on client
    response_obj = Response(content='{"success": true, "message": "Logged out successfully"}')
    response_obj.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        httponly=settings.SESSION_COOKIE_HTTPONLY,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE
    )
    
    logger.info(f"User logged out: staff_id={user.staff_id}")
    
    return LogoutResponse(success=True, message="Logged out successfully")
