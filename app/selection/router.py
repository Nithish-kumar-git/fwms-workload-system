"""
Selection router - HTTP layer for subject selection.
Spec reference: BACKEND_STRUCTURE.md Section 3.1, FSB_v1.1.md Section 3.4

This module handles HTTP requests for subject selection and delegates
to the transaction layer. No SQL or business logic is allowed here.

PRODUCTION BUILD:
- SQLSTATE-to-HTTP error mapping
- Correlation ID in error responses
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from app.selection.transactions import select_subject_transaction
from app.selection.schemas import SelectSubjectRequest, SelectSubjectResponse
from app.auth.dependencies import get_current_staff_id
from app.utils.error_mapper import raise_http_from_db_error
import logging

router = APIRouter(prefix="/api/selection", tags=["selection"])
logger = logging.getLogger(__name__)



@router.post("/select", response_model=SelectSubjectResponse)
async def select_subject(
    request_body: SelectSubjectRequest,
    request: Request,
    staff_id: int = Depends(get_current_staff_id)
):
    """
    Select a subject (FCFS).
    
    Spec reference: FSB_v1.1.md Section 3.4
    
    HTTP Error Mapping (per FSB Section 7):
    - 403: Window closed, not eligible, quota exceeded
    - 409: Subject already selected, deadlock, lock timeout
    """
    # Get correlation ID from request state
    correlation_id = getattr(request.state, "correlation_id", None)
    
    try:
        # Call transaction layer
        result = select_subject_transaction(
            staff_id=staff_id,
            subject_id=request_body.subject_id,
            batch_id=request_body.batch_id,
            specialization_id=request_body.specialization_id
        )
        
        # Map transaction result to HTTP response
        if not result["success"]:
            # Determine HTTP status code based on message
            if result["message"] in ["Window closed", "Not eligible for this subject", "Quota exceeded"]:
                status_code = 403
            elif result["message"] in ["Subject already selected", "Concurrent change detected, please try again"]:
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
    
    except HTTPException:
        raise
    except Exception as e:
        # Map database errors to HTTP (SQLSTATE mapping)
        logger.error(f"Selection transaction error: {e}", exc_info=True)
        raise_http_from_db_error(e, correlation_id)
