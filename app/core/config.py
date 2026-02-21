"""
Configuration management.
Spec reference: BACKEND_STRUCTURE.md Section 4
"""

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # Environment
    ENV: Literal["development", "staging", "production"] = "development"
    
    # Database
    DATABASE_URL: str
    POOL_SIZE: int = 10
    POOL_MAX_OVERFLOW: int = 20
    
    # OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    ALLOWED_EMAIL_DOMAIN: str = "hindustanuniv.ac.in"
    
    # Session
    REDIS_URL: str | None = None
    SESSION_BACKEND: Literal["redis", "memory"] = "memory"
    SESSION_EXPIRATION_HOURS: int = 4
    
    # Email
    EMAIL_BACKEND: Literal["smtp", "log"] = "log"
    
    # SMTP
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    
    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Security
    SECRET_KEY: str
    
    # Session cookies
    SESSION_COOKIE_NAME: str = "faculty_session"
    SESSION_COOKIE_SECURE: bool = True  # HTTPS only in production
    SESSION_COOKIE_HTTPONLY: bool = True  # Prevent XSS
    SESSION_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_BACKEND: Literal["redis", "memory"] = "memory"
    RATE_LIMIT_SELECT_MAX_REQUESTS: int = 10  # Max requests per window
    RATE_LIMIT_SELECT_WINDOW_SECONDS: int = 60  # Window duration
    
    # Correlation ID
    CORRELATION_ID_HEADER: str = "X-Correlation-ID"
    
    # Development auth bypass (NEVER enable in production)
    DEV_AUTH_BYPASS: bool = False
    
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def model_post_init(self, __context):
        """
        Validate configuration on startup (PRODUCTION HARDENING).
        
        Per implementation plan Phase 7:
        - Validate required fields
        - Validate SECRET_KEY length (min 32 chars)
        - Validate DATABASE_URL format
        - Environment-specific validation
        """
        # Validate SECRET_KEY length
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        
        # Validate DATABASE_URL format
        if not self.DATABASE_URL.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        
        # Production-specific validation
        if self.ENV == "production":
            # Enforce HTTPS cookies in production
            if not self.SESSION_COOKIE_SECURE:
                raise ValueError("SESSION_COOKIE_SECURE must be True in production")
            
            # Require OAuth credentials
            if not self.GOOGLE_CLIENT_ID or self.GOOGLE_CLIENT_ID == "your-client-id.apps.googleusercontent.com":
                raise ValueError("GOOGLE_CLIENT_ID must be configured in production")
            
            if not self.GOOGLE_CLIENT_SECRET or self.GOOGLE_CLIENT_SECRET == "your-secret":
                raise ValueError("GOOGLE_CLIENT_SECRET must be configured in production")
            
            # Require Redis for sessions in production
            if self.SESSION_BACKEND == "memory":
                raise ValueError("SESSION_BACKEND must be 'redis' in production (memory backend loses sessions on restart)")
            
            # Block development auth bypass in production — FAIL CLOSED
            if self.DEV_AUTH_BYPASS:
                raise RuntimeError(
                    "FATAL: DEV_AUTH_BYPASS=true is FORBIDDEN in production. "
                    "Application will not start. Set DEV_AUTH_BYPASS=false."
                )


settings = Settings()
