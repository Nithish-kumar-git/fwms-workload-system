"""
Server-side session management.
Spec reference: FSB_v1.3.md Section 1.4, BACKEND_STRUCTURE.md Section 4.1

This module handles session storage and validation:
- Redis-backed session store (primary)
- In-memory fallback for development
- 4-hour session expiration
- Session format: session:<uuid> -> {"staff_id": int}
"""

import uuid
import json
import logging
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class SessionBackend(ABC):
    """Abstract session storage backend."""
    
    @abstractmethod
    def create_session(self, staff_id: int) -> str:
        """Create new session, return session ID."""
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data, return None if not found or expired."""
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Delete session, return True if existed."""
        pass


class RedisSessionBackend(SessionBackend):
    """
    Redis-backed session store (PRODUCTION).
    
    Session key format: session:<uuid>
    Session value: JSON {"staff_id": int}
    Expiration: 4 hours (per FSB Section 1.4)
    """
    
    def __init__(self):
        try:
            import redis
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis session backend initialized")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    def create_session(self, staff_id: int) -> str:
        """Create new session in Redis."""
        session_id = str(uuid.uuid4())
        session_key = f"session:{session_id}"
        session_data = json.dumps({"staff_id": staff_id})
        
        # Set with expiration (4 hours per FSB Section 1.4)
        expiration_seconds = settings.SESSION_EXPIRATION_HOURS * 3600
        self.redis_client.setex(
            session_key,
            expiration_seconds,
            session_data
        )
        
        logger.info(f"Session created: {session_id} for staff_id={staff_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data from Redis."""
        session_key = f"session:{session_id}"
        session_data = self.redis_client.get(session_key)
        
        if session_data is None:
            return None
        
        try:
            return json.loads(session_data)
        except json.JSONDecodeError:
            logger.error(f"Invalid session data for {session_id}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis."""
        session_key = f"session:{session_id}"
        deleted = self.redis_client.delete(session_key)
        
        if deleted:
            logger.info(f"Session deleted: {session_id}")
        
        return deleted > 0


class InMemorySessionBackend(SessionBackend):
    """
    In-memory session store (DEVELOPMENT ONLY).
    
    WARNING: Sessions are lost on server restart.
    NOT suitable for production use.
    """
    
    def __init__(self):
        self.sessions = {}  # {session_id: {"staff_id": int, "expires_at": timestamp}}
        logger.warning("Using in-memory session backend (DEVELOPMENT ONLY)")
    
    def create_session(self, staff_id: int) -> str:
        """Create new session in memory."""
        import time
        
        session_id = str(uuid.uuid4())
        expiration_seconds = settings.SESSION_EXPIRATION_HOURS * 3600
        expires_at = time.time() + expiration_seconds
        
        self.sessions[session_id] = {
            "staff_id": staff_id,
            "expires_at": expires_at
        }
        
        logger.info(f"Session created (in-memory): {session_id} for staff_id={staff_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data from memory."""
        import time
        
        session_data = self.sessions.get(session_id)
        
        if session_data is None:
            return None
        
        # Check expiration
        if time.time() > session_data["expires_at"]:
            # Expired, delete it
            del self.sessions[session_id]
            return None
        
        return {"staff_id": session_data["staff_id"]}
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session from memory."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session deleted (in-memory): {session_id}")
            return True
        return False


class SessionManager:
    """
    Session manager with backend abstraction.
    
    Automatically selects backend based on configuration:
    - Redis (production)
    - In-memory (development)
    """
    
    def __init__(self):
        if settings.SESSION_BACKEND == "redis":
            self.backend = RedisSessionBackend()
        else:
            self.backend = InMemorySessionBackend()
    
    def create_session(self, staff_id: int) -> str:
        """
        Create new session for staff member.
        
        Args:
            staff_id: Staff ID from database
            
        Returns:
            Session ID (UUID)
        """
        return self.backend.create_session(staff_id)
    
    def get_staff_id(self, session_id: str) -> Optional[int]:
        """
        Get staff ID from session.
        
        Args:
            session_id: Session ID from cookie
            
        Returns:
            Staff ID if session is valid, None otherwise
        """
        session_data = self.backend.get_session(session_id)
        if session_data is None:
            return None
        return session_data.get("staff_id")
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session (logout).
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if session existed and was deleted
        """
        return self.backend.delete_session(session_id)


# Global session manager instance
session_manager = SessionManager()
