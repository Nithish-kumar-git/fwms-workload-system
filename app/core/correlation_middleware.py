"""
Request correlation ID middleware.
Spec reference: Implementation Plan Phase 4

This middleware:
- Generates UUID for each request
- Injects into logging context
- Returns in response header: X-Correlation-ID
- Logs request start/end with duration
"""

import uuid
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.config import settings

logger = logging.getLogger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Correlation ID middleware for request tracking.
    
    Generates or extracts correlation ID from request header,
    adds to logging context, and includes in response.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract correlation ID
        correlation_id = request.headers.get(
            settings.CORRELATION_ID_HEADER,
            str(uuid.uuid4())
        )
        
        # Store in request state for access in route handlers
        request.state.correlation_id = correlation_id
        
        # Log request start
        start_time = time.time()
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add correlation ID to response header
            response.headers[settings.CORRELATION_ID_HEADER] = correlation_id
            
            # Log request end
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"status={response.status_code} duration={duration_ms:.2f}ms",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                }
            )
            
            return response
        
        except Exception as e:
            # Log exception with correlation ID
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"error={str(e)} duration={duration_ms:.2f}ms",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
                exc_info=True
            )
            raise
