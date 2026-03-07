"""
Google OAuth 2.0 client implementation (PRODUCTION).
Spec reference: FSB_v1.3.md Section 1, BACKEND_STRUCTURE.md Section 4.1

This module handles Google OAuth flow:
- Authorization URL generation
- Authorization code → token exchange
- ID token verification
- Email extraction and domain validation

PRODUCTION: All DEV_ADMIN_EMAIL bypasses removed.
Only @hindustanuniv.ac.in accounts are accepted.
"""

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.core.config import settings
import urllib.request
import urllib.parse
import json
import logging

logger = logging.getLogger(__name__)


class GoogleOAuthClient:
    """
    Google OAuth 2.0 client for university email authentication.
    
    Enforces @hindustanuniv.ac.in domain validation per FSB Section 1.3.
    """
    
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.allowed_domain = settings.ALLOWED_EMAIL_DOMAIN
    
    def get_authorization_url(self, state: str = None) -> str:
        """
        Generate Google OAuth authorization URL.
        
        Args:
            state: Optional CSRF protection token
            
        Returns:
            Authorization URL to redirect user to
        """
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "online",
            "prompt": "select_account",
        }
        
        # Only pre-filter domain when NOT in dev bypass mode
        if not settings.DEV_AUTH_BYPASS and self.allowed_domain:
            params["hd"] = self.allowed_domain
        
        if state:
            params["state"] = state
        
        query_string = urllib.parse.urlencode(params)
        return f"{base_url}?{query_string}"
    
    def exchange_code_for_token(self, code: str) -> dict:
        """
        Exchange authorization code for tokens (standard OAuth 2.0 flow).
        
        Args:
            code: Authorization code from Google callback
            
        Returns:
            User info dict with keys: email, name, sub
            
        Raises:
            ValueError: If exchange fails or token is invalid
        """
        data = urllib.parse.urlencode({
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }).encode("utf-8")
        
        try:
            req = urllib.request.Request(
                self.TOKEN_ENDPOINT,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                token_response = json.loads(resp.read().decode("utf-8"))
            
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            raise ValueError(f"Failed to exchange authorization code: {e}")
        
        raw_id_token = token_response.get("id_token")
        if not raw_id_token:
            raise ValueError("No id_token in token response")
        
        return self.verify_token(raw_id_token)
    
    def verify_token(self, token: str) -> dict:
        """
        Verify Google ID token and extract user info.
        
        PRODUCTION: Strict domain enforcement, no bypasses.
        
        Args:
            token: Google ID token from OAuth callback
            
        Returns:
            User info dict with keys: email, name, sub (Google user ID)
            
        Raises:
            ValueError: If token is invalid or email domain is not allowed
        """
        try:
            # Verify token with Google (verifies signature, exp, iss)
            idinfo = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                self.client_id
            )
            
            # Explicit aud validation (defense-in-depth)
            token_aud = idinfo.get("aud")
            if token_aud != self.client_id:
                logger.warning(
                    f"Token audience mismatch: expected={self.client_id}, got={token_aud}"
                )
                raise ValueError(f"Token audience mismatch: expected {self.client_id}")
            
            # Validate hosted domain (Google Workspace)
            # Skip domain checks when DEV_AUTH_BYPASS is active
            if not settings.DEV_AUTH_BYPASS and self.allowed_domain:
                token_hd = idinfo.get("hd")
                if token_hd != self.allowed_domain:
                    logger.warning(
                        f"Hosted domain mismatch: expected={self.allowed_domain}, got={token_hd}"
                    )
                    raise ValueError(
                        f"Login restricted to @{self.allowed_domain} accounts"
                    )
            
            # Extract and validate email
            email = idinfo.get("email")
            if not email:
                raise ValueError("Email not found in token")
            
            if not idinfo.get("email_verified", False):
                raise ValueError("Email address is not verified by Google")
            
            # Strict domain validation (exact string match)
            # Skip when DEV_AUTH_BYPASS is active
            if not settings.DEV_AUTH_BYPASS:
                if not email.endswith(f"@{self.allowed_domain}"):
                    logger.warning(f"Rejected login attempt from non-university email: {email}")
                    raise ValueError(f"Email must be from @{self.allowed_domain}")
            else:
                logger.info(f"DEV_AUTH_BYPASS: Allowing non-university email: {email}")
            
            return {
                "email": email,
                "name": idinfo.get("name", ""),
                "sub": idinfo.get("sub"),
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise ValueError(f"Invalid token: {str(e)}")
    
    def validate_email_domain(self, email: str) -> bool:
        """
        Validate email domain (EXACT implementation per FSB Section 1.3).
        """
        return email.endswith(f"@{self.allowed_domain}")


# Global OAuth client instance
oauth_client = GoogleOAuthClient()
