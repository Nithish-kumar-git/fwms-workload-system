"""
JWT token utilities for session management.

Provides JWT-based authentication as an alternative/complement to session cookies.
Used by the frontend Axios client via Authorization: Bearer <token> header.
"""

import jwt
import time
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"


def create_jwt(staff_id: int, email: str, name: str, role: str) -> str:
    """
    Create a signed JWT token.
    
    Args:
        staff_id: Staff database ID
        email: Staff email
        name: Staff display name
        role: One of 'coordinator', 'hod', 'faculty'
        
    Returns:
        Encoded JWT string
    """
    payload = {
        "sub": str(staff_id),
        "email": email,
        "name": name,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + (settings.SESSION_EXPIRATION_HOURS * 3600),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_jwt(token: str) -> dict | None:
    """
    Verify and decode a JWT token.
    
    Returns:
        Decoded payload dict, or None if invalid/expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("JWT expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid JWT: {e}")
        return None
