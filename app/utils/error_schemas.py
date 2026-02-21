"""
Standardized error response schemas.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    error_code: Optional[str] = None
    message: str
    details: Optional[dict] = None
    correlation_id: Optional[str] = None
    timestamp: datetime = datetime.utcnow()
