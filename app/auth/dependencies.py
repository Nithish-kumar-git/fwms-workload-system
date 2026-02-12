"""
Authentication dependencies (PLACEHOLDER).
Spec reference: BACKEND_STRUCTURE.md Section 3.1

TODO: Replace with real OAuth implementation per FSB_v1.1.md Section 1.
This is a TEMPORARY placeholder for testing purposes only.
"""

from fastapi import Depends, HTTPException


def get_current_staff_id() -> int:
    """
    Placeholder dependency for extracting authenticated staff_id.
    
    TODO: Replace with actual OAuth session validation:
    1. Extract session cookie/token
    2. Validate session in Redis/memory
    3. Query staff table for fresh role data
    4. Return staff_id
    
    CURRENT BEHAVIOR: Returns hardcoded staff_id = 1
    """
    # PLACEHOLDER: Hardcoded for testing
    return 1


def get_current_coordinator_id() -> int:
    """
    Placeholder dependency for extracting authenticated coordinator staff_id.
    
    TODO: Replace with actual OAuth + role validation:
    1. Extract session cookie/token
    2. Validate session in Redis/memory
    3. Query staff table: SELECT id, is_coordinator WHERE id = :staff_id
    4. Verify is_coordinator = true
    5. Return staff_id
    
    CURRENT BEHAVIOR: Returns hardcoded coordinator_staff_id = 1
    """
    # PLACEHOLDER: Hardcoded for testing
    # In production, this MUST query database for is_coordinator
    staff_id = 1
    is_coordinator = True  # HARDCODED - MUST be from database
    
    if not is_coordinator:
        raise HTTPException(
            status_code=403,
            detail="Coordinator access required"
        )
    
    return staff_id
