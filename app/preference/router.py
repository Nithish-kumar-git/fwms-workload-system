"""
FastAPI router for faculty preference endpoints.
Spec reference: final_system_specification.md Section 2 (Category A)

Endpoints:
  POST   /api/preferences          Submit a preference
  GET    /api/preferences/me       List my preferences
  GET    /api/preferences/status   Get completion status
  DELETE /api/preferences/{id}     Remove a preference
"""

from fastapi import APIRouter, Depends, HTTPException
import logging

from app.auth.dependencies import get_current_user, UserInfo
from app.preference.schemas import (
    SubmitPreferenceRequest,
    SubmitPreferenceResponse,
    PreferenceResponse,
    DeletePreferenceResponse,
    PreferenceStatusResponse,
)
from app.preference import service as preference_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.post("", response_model=SubmitPreferenceResponse)
async def submit_preference(
    request: SubmitPreferenceRequest,
    user: UserInfo = Depends(get_current_user),
):
    """
    Submit a faculty preference for a subject offering.
    
    Validates against all 5 institutional rules:
    - PREF-01: preference number 1-5
    - PREF-03: no reuse of same preference number by faculty
    - PREF-02: no two faculty with same pref number for same subject
    - SHIFT-01: shift compatibility
    - CT-01: class teacher first preference must match their class
    """
    result = preference_service.submit_preference(
        staff_id=user.staff_id,
        subject_offering_id=request.subject_offering_id,
        preference_number=request.preference_number,
    )
    
    if not result["success"]:
        rule = result.get("rule", "")
        # Map rules to HTTP status codes
        if rule == "AUTH":
            raise HTTPException(status_code=401, detail=result["message"])
        elif rule == "DATA":
            raise HTTPException(status_code=404, detail=result["message"])
        elif rule in ("PREF-01", "PREF-02", "PREF-03", "PREF-04", "PREF-DUP"):
            raise HTTPException(status_code=409, detail=result["message"])
        elif rule in ("SHIFT-01", "CT-01"):
            raise HTTPException(status_code=403, detail=result["message"])
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    return SubmitPreferenceResponse(
        success=True,
        message=result["message"],
        preference_id=result["preference_id"],
    )


@router.get("/me", response_model=list[PreferenceResponse])
async def list_my_preferences(
    user: UserInfo = Depends(get_current_user),
):
    """
    List all preferences for the currently authenticated faculty.
    Returns preferences ordered by preference_number (1-5).
    """
    prefs = preference_service.list_preferences(staff_id=user.staff_id)
    return [PreferenceResponse(**p) for p in prefs]


@router.get("/status", response_model=PreferenceStatusResponse)
async def get_preference_status(
    user: UserInfo = Depends(get_current_user),
):
    """
    Get preference completion status for the current faculty.
    
    Returns:
    - total_submitted: how many preferences submitted (0-5)
    - remaining: how many more needed  
    - is_complete: whether all 5 are submitted
    - preferences: list of current preferences with subject details
    """
    status = preference_service.get_preference_status(staff_id=user.staff_id)
    # Convert nested preference dicts to PreferenceResponse objects
    status["preferences"] = [PreferenceResponse(**p) for p in status["preferences"]]
    return PreferenceStatusResponse(**status)


@router.delete("/{preference_id}", response_model=DeletePreferenceResponse)
async def delete_preference(
    preference_id: int,
    user: UserInfo = Depends(get_current_user),
):
    """
    Delete a specific preference by ID.
    Only the owning faculty can delete their own preferences.
    """
    result = preference_service.delete_preference(
        staff_id=user.staff_id,
        preference_id=preference_id,
    )
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    
    return DeletePreferenceResponse(**result)
