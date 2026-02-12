"""
Authentication router (PLACEHOLDER).
Spec reference: BACKEND_STRUCTURE.md Section 3.1

TODO: Replace with real OAuth endpoints per FSB_v1.1.md Section 1.
This is a TEMPORARY placeholder for testing purposes only.
"""

from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_staff_id
from app.auth.schemas import StaffInfoResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=StaffInfoResponse)
async def get_current_user_info(
    staff_id: int = Depends(get_current_staff_id)
):
    """
    Get current authenticated user info (PLACEHOLDER).
    
    TODO: Replace with real implementation:
    1. Query staff table for full user details
    2. Return actual name, email, role
    
    CURRENT BEHAVIOR: Returns hardcoded staff info
    """
    # PLACEHOLDER: Hardcoded response
    return StaffInfoResponse(
        staff_id=staff_id,
        email="test@hindustanuniv.ac.in",
        name="Test User",
        is_coordinator=False
    )


# TODO: Add OAuth endpoints when implementing real auth:
# @router.get("/login")
# async def login():
#     """Redirect to Google OAuth"""
#     pass
#
# @router.get("/callback")
# async def oauth_callback():
#     """Handle OAuth callback"""
#     pass
#
# @router.post("/logout")
# async def logout():
#     """Destroy session"""
#     pass
