"""
Selection router - HTTP layer for subject selection.
Spec reference: BACKEND_STRUCTURE.md Section 3.1, FSB_v1.1.md Section 3.4

This module handles HTTP requests for subject selection and delegates
to the transaction layer. No SQL or business logic is allowed here.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.selection.transactions import select_subject_transaction
from app.selection.schemas import SelectSubjectRequest, SelectSubjectResponse
from app.auth.dependencies import get_current_staff_id

router = APIRouter(prefix="/api/selection", tags=["selection"])



@router.post("/select", response_model=SelectSubjectResponse)
async def select_subject(
    request: SelectSubjectRequest,
    staff_id: int = Depends(get_current_staff_id)
):
    """
    Select a subject (FCFS).
    
    Spec reference: FSB_v1.1.md Section 3.4
    
    HTTP Error Mapping (per FSB Section 7):
    - 403: Window closed, not eligible, quota exceeded
    - 409: Subject already selected, deadlock, lock timeout
    """
    
    # Call transaction layer
    result = select_subject_transaction(
        staff_id=staff_id,
        subject_id=request.subject_id,
        batch_id=request.batch_id,
        specialization_id=request.specialization_id
    )
    
    # Map transaction result to HTTP response
    if not result["success"]:
        # Determine HTTP status code based on message
        if result["message"] in ["Window closed", "Not eligible for this subject", "Quota exceeded"]:
            status_code = 403
        elif result["message"] == "Subject already selected":
            status_code = 409
        else:
            # Fallback for unexpected errors
            status_code = 500
        
        raise HTTPException(status_code=status_code, detail=result["message"])
    
    # Success response
    return SelectSubjectResponse(
        success=True,
        message=result["message"],
        selection_id=result["selection_id"]
    )
