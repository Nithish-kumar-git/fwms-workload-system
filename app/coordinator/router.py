"""
Coordinator router - HTTP layer for coordinator operations.
Spec reference: BACKEND_STRUCTURE.md Section 3.1, FSB_v1.1.md Section 4

This module handles HTTP requests for coordinator overrides and delegates
to the transaction layer. No SQL or business logic is allowed here.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.coordinator.transactions import override_subject_transaction
from app.coordinator.schemas import OverrideSubjectRequest, OverrideSubjectResponse
from app.auth.dependencies import get_current_coordinator_id

router = APIRouter(prefix="/api/coordinator", tags=["coordinator"])



@router.post("/override", response_model=OverrideSubjectResponse)
async def override_subject(
    request: OverrideSubjectRequest,
    coordinator_staff_id: int = Depends(get_current_coordinator_id)
):
    """
    Override a subject selection (coordinator only).
    
    Spec reference: FSB_v1.1.md Section 4.2
    
    HTTP Error Mapping:
    - 404: Subject no longer selected
    - 409: Deadlock, lock timeout
    """
    
    # Call transaction layer
    result = override_subject_transaction(
        coordinator_staff_id=coordinator_staff_id,
        subject_id=request.subject_id
    )
    
    # Map transaction result to HTTP response
    if not result["success"]:
        # Determine HTTP status code based on message
        if result["message"] == "Subject no longer selected":
            status_code = 404
        else:
            # Fallback for unexpected errors
            status_code = 500
        
        raise HTTPException(status_code=status_code, detail=result["message"])
    
    # Success response
    return OverrideSubjectResponse(
        success=True,
        message=result["message"],
        affected_staff_id=result["affected_staff_id"]
    )
