# BACKEND_STRUCTURE.md
## Faculty Subject Selection System — Backend Architecture

**Version:** 1.0  
**Status:** Production Specification  
**Deployment Context:** University on-premises (primary) OR approved cloud (secondary)  
**Developer Model:** Solo developer with AI assistance  
**Date:** 2026-02-07

---

## 1. ARCHITECTURAL PRINCIPLES

### 1.1 Core Design Philosophy

**Monolithic, Simple, Audit-Safe**

- Single FastAPI application (no microservices)
- Direct PostgreSQL connections (no ORM on write paths)
- Synchronous request handling (no event sourcing)
- File-based logging + optional structured logging
- Email abstraction (never blocks selections)

### 1.2 Deployment Assumptions

**PRIMARY TARGET:**
- University on-premises infrastructure
- Self-hosted PostgreSQL
- University SMTP server
- Standard Linux server (Ubuntu 22.04+)

**SECONDARY OPTIONS (if explicitly approved):**
- Railway (PostgreSQL + FastAPI hosting)
- Render (alternative to Railway)
- AWS/Azure/GCP (if university has cloud account)

**FORBIDDEN:**
- Serverless databases with connection limits
- Vercel serverless functions (backend must be stateful)
- Auto-scaling without connection pooling considerations

---

## 2. PROJECT STRUCTURE (FINAL)
```
faculty-subject-selection/
│
├── app/
│   ├── main.py                      # FastAPI bootstrap
│   │
│   ├── core/
│   │   ├── config.py                # Environment-based settings
│   │   └── logging_config.py        # Structured logging setup
│   │
│   ├── db/
│   │   ├── pool.py                  # SQLAlchemy engine (MANUAL)
│   │   ├── session.py               # Transaction context manager (MANUAL)
│   │   └── __init__.py
│   │
│   ├── auth/
│   │   ├── router.py                # OAuth endpoints
│   │   ├── dependencies.py          # get_current_user, require_coordinator
│   │   ├── google_oauth.py          # Google OAuth client
│   │   ├── session_manager.py       # Redis/memory session handling
│   │   ├── schemas.py               # Auth request/response models
│   │   └── __init__.py
│   │
│   ├── staff/
│   │   ├── router.py                # Staff endpoints (GET /subjects)
│   │   ├── service.py               # Business logic (eligibility checks)
│   │   ├── schemas.py               # Pydantic models
│   │   └── __init__.py
│   │
│   ├── selection/
│   │   ├── router.py                # HTTP layer (POST /select, /change)
│   │   ├── service.py               # Pre-transaction validation
│   │   ├── transactions.py          # FCFS SQL (HAND-WRITTEN, NO AI)
│   │   ├── schemas.py               # Request/response models
│   │   └── __init__.py
│   │
│   ├── coordinator/
│   │   ├── router.py                # Coordinator endpoints
│   │   ├── service.py               # Window management logic
│   │   ├── transactions.py          # Override transaction
│   │   ├── schemas.py               # Coordinator models
│   │   └── __init__.py
│   │
│   ├── audit/
│   │   ├── router.py                # Audit log read endpoints
│   │   ├── service.py               # Query builders
│   │   ├── schemas.py               # Audit response models
│   │   └── __init__.py
│   │
│   ├── notifications/
│   │   ├── email_adapter.py         # ABSTRACTION LAYER
│   │   ├── smtp_backend.py          # University SMTP implementation
│   │   ├── log_backend.py           # Development: log-only backend
│   │   ├── queue.py                 # Background task manager
│   │   ├── templates.py             # Email templates
│   │   └── __init__.py
│   │
│   ├── health/
│   │   ├── router.py                # /health, /health/deep
│   │   └── __init__.py
│   │
│   └── utils/
│       ├── rate_limit.py            # In-memory or Redis rate limiting
│       ├── errors.py                # HTTP exception handlers
│       └── __init__.py
│
├── migrations/
│   ├── schema.sql                   # Phase 1 database schema (DDL)
│   ├── seed_data.sql                # Test data (optional)
│   └── README.md
│
├── tests/
│   ├── conftest.py                  # Pytest fixtures
│   ├── test_auth.py
│   ├── test_selection.py            # Concurrency tests
│   ├── test_coordinator.py
│   └── README.md
│
├── logs/                            # Application logs (gitignored)
│   └── .gitkeep
│
├── .env.example                     # Environment template
├── .env                             # Actual config (gitignored)
├── .gitignore
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Tool configuration
├── README.md
└── DEPLOYMENT.md                    # Deployment guide
```

---

## 3. MODULE RESPONSIBILITIES (STRICT)

### 3.1 Responsibility Matrix

| Module | Allowed | Forbidden |
|--------|---------|-----------|
| `router.py` | HTTP parsing, `Depends()`, status codes | SQL, transactions, business logic |
| `service.py` | Business rules, validation, orchestration | Direct SQL writes, locking |
| `transactions.py` | Raw SQL, `FOR UPDATE`, `BEGIN/COMMIT` | HTTP responses, Pydantic models |
| `schemas.py` | Pydantic models, validation | Any logic |
| `dependencies.py` | Reusable FastAPI dependencies | Endpoint-specific logic |

### 3.2 Critical Path Ownership

**FCFS Transactions (HAND-WRITTEN ONLY):**
- `app/selection/transactions.py`
- `app/coordinator/transactions.py`
- `app/db/pool.py`
- `app/db/session.py`

**AI-Assisted (with manual review):**
- `app/auth/google_oauth.py`
- `app/auth/dependencies.py`
- All `router.py` files
- All `schemas.py` files

**Safe for Full AI Generation:**
- `app/health/router.py`
- Email templates
- Test fixtures

---

## 4. CONFIGURATION MANAGEMENT

### 4.1 Environment Variables

**File:** `.env.example`
```bash
# ============================================
# DEPLOYMENT ENVIRONMENT
# ============================================
ENV=development  # development | staging | production

# ============================================
# DATABASE (ON-PREM OR CLOUD)
# ============================================
DATABASE_URL=postgresql://user:password@localhost:5432/faculty_selection

# Connection pool settings (CONSERVATIVE DEFAULTS)
POOL_SIZE=10
POOL_MAX_OVERFLOW=20

# ============================================
# GOOGLE OAUTH
# ============================================
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback

# Email domain validation
ALLOWED_EMAIL_DOMAIN=hindustanuniv.ac.in

# ============================================
# SESSION MANAGEMENT (Redis OPTIONAL)
# ============================================
REDIS_URL=redis://localhost:6379/0  # Optional
SESSION_BACKEND=memory  # memory | redis
SESSION_EXPIRATION_HOURS=4

# ============================================
# EMAIL BACKEND
# ============================================
EMAIL_BACKEND=smtp  # smtp | log

# University SMTP (PRIMARY)
SMTP_HOST=smtp.hindustanuniv.ac.in
SMTP_PORT=587
SMTP_USER=  # Optional (if auth required)
SMTP_PASSWORD=  # Optional
SMTP_FROM=timetable@hindustanuniv.ac.in

# ============================================
# LOGGING
# ============================================
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR
LOG_FILE=logs/app.log

# ============================================
# SECURITY
# ============================================
SECRET_KEY=your-secret-key-change-in-production-min-32-chars

# ============================================
# RATE LIMITING (OPTIONAL)
# ============================================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_BACKEND=memory  # memory | redis
```

### 4.2 Settings Class

**File:** `app/core/config.py`
```python
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
    EMAIL_BACKEND: Literal["smtp", "log"] = "smtp"
    
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
```

---

## 5. DATABASE CONNECTION LAYER

### 5.1 Connection Pool Configuration

**File:** `app/db/pool.py` ⚠️ **HAND-WRITTEN ONLY**
```python
from sqlalchemy import create_engine
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    
    # CONSERVATIVE pool sizing (adjust after load testing)
    pool_size=settings.POOL_SIZE,              # Default: 10
    max_overflow=settings.POOL_MAX_OVERFLOW,   # Default: 20 (total 30)
    pool_timeout=5,                            # Fail fast
    
    # Connection health
    pool_pre_ping=True,        # Test connection before use
    pool_recycle=3600,         # Recycle after 1 hour
    
    # Performance
    echo=False,                # Disable SQL logging in production
    
    # Isolation (set per-transaction, not globally)
    isolation_level=None,
)
```

### 5.2 Transaction Context Manager

**File:** `app/db/session.py` ⚠️ **HAND-WRITTEN ONLY**
```python
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.db.pool import engine

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

@contextmanager
def get_transaction(isolation_level: str = "READ COMMITTED"):
    """
    Transaction context manager (FCFS-safe)
    
    Default: READ COMMITTED (most transactions)
    Override: REPEATABLE READ (only if explicitly needed)
    
    Guarantees:
    - Explicit isolation level
    - 5s lock timeout
    - Automatic rollback on exception
    - Connection always returned clean
    """
    session = SessionLocal()
    try:
        session.execute(text(f"BEGIN TRANSACTION ISOLATION LEVEL {isolation_level}"))
        session.execute(text("SET LOCAL lock_timeout = '5s'"))
        
        yield session
        
        session.commit()
        
    except Exception:
        session.rollback()
        raise
        
    finally:
        session.close()
```

---

## 6. EMAIL ABSTRACTION LAYER (CRITICAL)

### 6.1 Design Principle

> Email failures MUST NEVER affect selection correctness.

**Pattern:** Queue + Adapter
```
Selection Transaction
        ↓
     COMMIT
        ↓
  Queue Email Task (async)
        ↓
  Email Adapter (abstraction)
        ↓
   ┌────────────────┐
   │ SMTP Backend   │ (University server)
   │ Log Backend    │ (Dev/testing: just log)
   └────────────────┘
```

### 6.2 Email Adapter Interface

**File:** `app/notifications/email_adapter.py`
```python
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class EmailBackend(ABC):
    """
    Abstract email backend
    
    Implementations:
    - SMTPBackend (university SMTP server)
    - LogBackend (dev/testing: prints to log)
    """
    
    @abstractmethod
    def send_email(
        self, 
        to: str, 
        subject: str, 
        body: str,
        html_body: str = None
    ) -> bool:
        """
        Send email (best-effort)
        
        Returns:
        - True if sent successfully
        - False if failed (logged internally)
        
        MUST NOT raise exceptions
        """
        pass

# Global backend (configured at startup)
_email_backend: EmailBackend = None

def configure_email_backend(backend: EmailBackend):
    global _email_backend
    _email_backend = backend

def send_email_async(to: str, subject: str, body: str, html_body: str = None):
    """
    Send email asynchronously (queued via BackgroundTasks)
    
    Failures are logged, not raised
    """
    try:
        success = _email_backend.send_email(to, subject, body, html_body)
        if not success:
            logger.warning(f"Email send failed: to={to}, subject={subject}")
    except Exception as e:
        logger.error(f"Email backend exception: {e}")
```

---

## 7. DEPENDENCIES

### 7.1 requirements.txt
```txt
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic[email]==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9

# Authentication
google-auth==2.25.2
python-jose[cryptography]==3.3.0

# Session & Caching (Redis OPTIONAL)
redis==5.0.1

# Utilities
python-multipart==0.0.6
email-validator==2.1.0

# Development (optional, not in production)
# pytest==7.4.3
# httpx==0.25.2
# locust==2.20.0
```

---

## 8. DEPLOYMENT OPTIONS

### 8.1 On-Premises Deployment (PRIMARY)

**Target:** University Linux server (Ubuntu 22.04+)

**Requirements:**
- PostgreSQL 14+ (installed on-prem or managed)
- Redis (optional, for sessions/rate limiting)
- Python 3.12+
- Systemd (for service management)
- Nginx (reverse proxy)

**Installation:**
```bash
# 1. Clone repository
git clone <repo-url>
cd faculty-subject-selection

# 2. Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env  # Edit with university settings

# 5. Initialize database
psql -U postgres -f migrations/schema.sql

# 6. Run application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 8.2 Cloud Deployment (OPTIONAL)

**Railway / Render / AWS:**
- Only if university explicitly approves
- Must use managed PostgreSQL (not serverless)
- Configure environment variables in platform dashboard

---

## 9. SECURITY CONSIDERATIONS

### 9.1 Environment Secrets

**NEVER commit to Git:**
- `.env` (actual secrets)
- Database passwords
- OAuth client secrets
- API keys

**Store securely:**
- University password manager
- Environment variables (production server)
- Cloud secret management (if approved)

---

## 10. TESTING INFRASTRUCTURE

### 10.1 Test Database

**File:** `tests/conftest.py`
```python
import pytest
from sqlalchemy import create_engine
from app.db.session import SessionLocal

@pytest.fixture(scope="session")
def test_db():
    """Test database fixture"""
    TEST_DATABASE_URL = "postgresql://user:password@localhost:5432/faculty_selection_test"
    
    engine = create_engine(TEST_DATABASE_URL)
    
    # Create schema
    with open("migrations/schema.sql") as f:
        engine.execute(f.read())
    
    yield engine
    
    engine.dispose()
```

---

**END OF BACKEND_STRUCTURE.md**
