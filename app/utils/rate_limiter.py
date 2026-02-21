"""
Rate limiting middleware.
Spec reference: Implementation Plan Phase 6

This module provides:
- Redis-backed rate limit store (primary)
- In-memory fallback for development
- Sliding window algorithm
- Per-user limits (keyed by staff_id)
- Rate limit headers in response
"""

import time
import logging
from typing import Optional
from fastapi import Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitBackend:
    """Abstract rate limit storage backend."""
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.
        
        Args:
            key: Rate limit key (e.g., "staff_id:123")
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (allowed, remaining, reset_timestamp)
        """
        raise NotImplementedError


class RedisRateLimitBackend(RateLimitBackend):
    """Redis-backed rate limiter using sliding window."""
    
    def __init__(self):
        try:
            import redis
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Redis rate limit backend initialized")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int, int]:
        """Check rate limit using Redis sorted set (sliding window)."""
        now = time.time()
        window_start = now - window_seconds
        rate_limit_key = f"rate_limit:{key}"
        
        # Remove old entries outside window
        self.redis_client.zremrangebyscore(rate_limit_key, 0, window_start)
        
        # Count requests in current window
        current_count = self.redis_client.zcard(rate_limit_key)
        
        if current_count >= max_requests:
            # Rate limit exceeded
            # Get oldest entry to calculate reset time
            oldest = self.redis_client.zrange(rate_limit_key, 0, 0, withscores=True)
            if oldest:
                reset_timestamp = int(oldest[0][1] + window_seconds)
            else:
                reset_timestamp = int(now + window_seconds)
            
            return False, 0, reset_timestamp
        
        # Add current request
        self.redis_client.zadd(rate_limit_key, {str(now): now})
        
        # Set expiration on key (cleanup)
        self.redis_client.expire(rate_limit_key, window_seconds)
        
        remaining = max_requests - (current_count + 1)
        reset_timestamp = int(now + window_seconds)
        
        return True, remaining, reset_timestamp


class InMemoryRateLimitBackend(RateLimitBackend):
    """In-memory rate limiter (DEVELOPMENT ONLY)."""
    
    def __init__(self):
        self.requests = {}  # {key: [(timestamp, ...), ...]}
        logger.warning("Using in-memory rate limit backend (DEVELOPMENT ONLY)")
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int, int]:
        """Check rate limit using in-memory sliding window."""
        now = time.time()
        window_start = now - window_seconds
        
        # Get or create request list for this key
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old entries
        self.requests[key] = [
            ts for ts in self.requests[key]
            if ts > window_start
        ]
        
        current_count = len(self.requests[key])
        
        if current_count >= max_requests:
            # Rate limit exceeded
            oldest = min(self.requests[key]) if self.requests[key] else now
            reset_timestamp = int(oldest + window_seconds)
            return False, 0, reset_timestamp
        
        # Add current request
        self.requests[key].append(now)
        
        remaining = max_requests - (current_count + 1)
        reset_timestamp = int(now + window_seconds)
        
        return True, remaining, reset_timestamp


class RateLimiter:
    """Rate limiter with backend abstraction."""
    
    def __init__(self):
        if not settings.RATE_LIMIT_ENABLED:
            self.backend = None
            logger.info("Rate limiting disabled")
        elif settings.RATE_LIMIT_BACKEND == "redis":
            self.backend = RedisRateLimitBackend()
        else:
            self.backend = InMemoryRateLimitBackend()
    
    def check_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.
        
        Args:
            key: Rate limit key
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (allowed, remaining, reset_timestamp)
        """
        if self.backend is None:
            # Rate limiting disabled
            return True, max_requests, int(time.time() + window_seconds)
        
        return self.backend.check_rate_limit(key, max_requests, window_seconds)


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit_dependency(
    request: Request,
    staff_id: int = None,
    max_requests: Optional[int] = None,
    window_seconds: Optional[int] = None
):
    """
    FastAPI dependency for rate limiting.
    
    Usage:
        @router.post("/select", dependencies=[Depends(rate_limit_dependency)])
        async def select_subject(...):
            ...
    
    Args:
        request: FastAPI request object
        staff_id: Staff ID from auth dependency (extracted from get_current_staff_id)
        max_requests: Override default max requests
        window_seconds: Override default window
        
    Raises:
        HTTPException 429: If rate limit exceeded
    """
    # Skip if rate limiting disabled
    if not settings.RATE_LIMIT_ENABLED:
        return
    
    # Extract staff_id from auth dependency if not provided directly
    if staff_id is None:
        # Fallback: try to get from request state
        if not hasattr(request.state, "staff_id"):
            # No authenticated user, skip rate limiting
            return
        staff_id = request.state.staff_id
    
    # Use defaults if not specified
    if max_requests is None:
        max_requests = settings.RATE_LIMIT_SELECT_MAX_REQUESTS
    if window_seconds is None:
        window_seconds = settings.RATE_LIMIT_SELECT_WINDOW_SECONDS
    
    # Check rate limit
    key = f"staff_id:{staff_id}"
    allowed, remaining, reset_timestamp = rate_limiter.check_limit(
        key, max_requests, window_seconds
    )
    
    # Add rate limit headers to response (will be added by middleware)
    request.state.rate_limit_headers = {
        "X-RateLimit-Limit": str(max_requests),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset_timestamp),
    }
    
    if not allowed:
        retry_after = reset_timestamp - int(time.time())
        logger.warning(
            f"Rate limit exceeded for staff_id={staff_id}, "
            f"retry_after={retry_after}s"
        )
        raise HTTPException(
            status_code=429,
            detail="Too many requests, please try again later",
            headers={
                "Retry-After": str(retry_after),
                **request.state.rate_limit_headers,
            }
        )
