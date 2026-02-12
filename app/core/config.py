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
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_BACKEND: Literal["redis", "memory"] = "memory"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
