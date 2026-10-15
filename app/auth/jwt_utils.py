"""
JWT token utilities for session management.

Provides JWT-based authentication as an alternative/complement to session cookies.
Used by the frontend Axios client via Authorization: Bearer <token> header.
"""

import jwt
import time
import logging
from app.core.config import settings
from app.demo.isolation import DEMO_ISSUER, accept_token_environment

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
    if settings.DEMO_MODE:
        payload.update(iss=DEMO_ISSUER, aud=DEMO_ISSUER)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_jwt(token: str) -> dict | None:
    """
    Verify and decode a JWT token.
    
    Returns:
        Decoded payload dict, or None if invalid/expired
    """
    try:
        if settings.DEMO_MODE:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM],
                                 issuer=DEMO_ISSUER, audience=DEMO_ISSUER,
                                 options={"require": ["sub", "exp", "iat", "iss", "aud"]})
        else:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload if accept_token_environment(payload, settings.DEMO_MODE) else None
    except jwt.ExpiredSignatureError:
        logger.debug("JWT expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid JWT: {e}")
        return None
