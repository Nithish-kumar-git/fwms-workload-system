# Railway to Render Migration Guide

## Complete Technical Specification for Production Migration

---

## 1. TECH STACK

### Backend
- **Framework**: FastAPI 0.109.0
- **Runtime**: Python 3.12
- **ASGI Server**: Uvicorn 0.27.0 (with standard extras)
- **Database**: PostgreSQL (via psycopg2-binary 2.9.9 + SQLAlchemy 2.0.25)

### Frontend
- **Framework**: React 19.2.0 + Vite 7.3.1
- **Language**: TypeScript 5.9.3
- **Build Tool**: Vite
- **Deployment**: Vercel (separate from backend)

### Key Dependencies
- **Auth**: google-auth 2.27.0, PyJWT 2.11.0
- **Session**: redis 5.0.1 (optional, defaults to in-memory)
- **Reports**: openpyxl 3.1.2, reportlab 4.0.9

---

## 2. START COMMAND

**Exact command used in production:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Location**: `startup.sh` (lines 48-50)

**Important**: 
- Uses `$PORT` environment variable (NOT hardcoded)
- Runs migrations BEFORE starting server
- Requires `postgresql-client` for migrations

---

## 3. BUILD COMMAND

**Backend**: NO build step required (Python runtime)

**Frontend** (deployed separately on Vercel):
```bash
cd frontend && npm install && npm run build
```

---

## 4. PORT CONFIGURATION

**Port Source**: `process.env.PORT` (environment variable)

**Code Location**: `startup.sh` line 48:
```bash
PORT=${PORT:-8000}
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Default**: 8000 (if PORT not set)

**✅ Render Compatible**: Yes - Render provides PORT automatically

---

## 5. ENVIRONMENT VARIABLES (Complete List)

### REQUIRED (Application will NOT start without these):

1. **DATABASE_URL** (PostgreSQL connection string)
   - Format: `postgresql://user:password@host:port/database`
   - Render provides this automatically when you add PostgreSQL

2. **SECRET_KEY** (JWT signing key)
   - Must be 32+ characters
   - Generate: `python -c "import secrets; print(secrets.token_hex(32))"`

3. **GOOGLE_CLIENT_ID** (OAuth)
   - From Google Cloud Console

4. **GOOGLE_CLIENT_SECRET** (OAuth)
   - From Google Cloud Console

5. **GOOGLE_REDIRECT_URI** (OAuth callback)
   - Format: `https://your-render-app.onrender.com/api/auth/callback`
   - **CRITICAL**: Must match Google Cloud Console authorized redirect URIs

### RECOMMENDED:

6. **ENV** (environment name)
   - Value: `production`
   - Default: `development`

7. **FRONTEND_URL** (CORS configuration)
   - Value: `https://fwms-workload-system.vercel.app`
   - Used for CORS allow_origins

8. **DEV_AUTH_BYPASS** (security)
   - Value: `False` (MUST be False in production)
   - Default: `False`

### OPTIONAL:

9. **REDIS_URL** (session storage)
   - Format: `redis://host:port`
   - If not set, uses in-memory sessions (loses sessions on restart)

10. **SESSION_BACKEND**
    - Values: `redis` or `memory`
    - Default: `memory`

11. **LOG_LEVEL**
    - Values: `DEBUG`, `INFO`, `WARNING`, `ERROR`
    - Default: `INFO`

12. **POOL_SIZE** (database connection pool)
    - Default: `10`

13. **POOL_MAX_OVERFLOW** (database connection pool)
    - Default: `20`

14. **ALLOWED_EMAIL_DOMAIN** (OAuth restriction)
    - Default: `hindustanuniv.ac.in`

---

## 6. DATABASE CONNECTION CODE

**File**: `app/db/pool.py`

```python
from sqlalchemy import create_engine
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,  # ← Uses DATABASE_URL env var
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.POOL_MAX_OVERFLOW,
    pool_timeout=5,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
    isolation_level=None,
)
```

**Connection Format**: Standard PostgreSQL URL
```
postgresql://user:password@host:port/database
```

**Render Compatibility**: ✅ Render provides DATABASE_URL in exact same format as Railway

---

## 7. FILE UPLOADS & LOCAL STORAGE

**File Uploads**: ✅ YES - Used for curriculum upload

**Location**: `app/curriculum/router.py`

**Storage Type**: **TEMPORARY ONLY** (in-memory processing)

**Details**:
- Accepts Excel files via `multipart/form-data`
- Parses file in memory using `openpyxl`
- Does NOT save files to disk
- No persistent file storage required

**Render Compatibility**: ✅ No issues - ephemeral filesystem is fine

---

## 8. CRON JOBS / SCHEDULED TASKS

**Status**: ❌ NONE

No background workers, cron jobs, or scheduled tasks.

**Render Compatibility**: ✅ No additional services needed

---

## 9. WEBSOCKET CONNECTIONS

**Status**: ❌ NONE

Pure REST API - no WebSockets, no real-time features.

**Render Compatibility**: ✅ No special configuration needed

---

## 10. FOLDER STRUCTURE

```
faculty_selection/
├── app/                    # Backend Python code
│   ├── admin/             # Admin endpoints
│   ├── allocation/        # Allocation logic
│   ├── auth/              # OAuth + JWT
│   ├── coordinator/       # Coordinator endpoints
│   ├── core/              # Config + middleware
│   ├── db/                # Database connection
│   ├── health/            # Health check
│   ├── preference/        # Preference submission
│   ├── reports/           # Report generation
│   ├── selection/         # Selection endpoints
│   ├── subjects/          # Subject management
│   ├── curriculum/        # Curriculum upload
│   └── main.py            # FastAPI app entry point
├── frontend/              # React + Vite (deployed separately on Vercel)
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── migrations/            # SQL migration files (39 files)
├── tests/                 # Test files
├── logs/                  # Log directory (created at runtime)
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker config
├── docker-compose.yml     # Local development
├── startup.sh             # Production startup script
└── .env.example           # Environment variable template
```

---

## 11. DEPLOYMENT CONFIG FILES

### A. Dockerfile (exists)

**File**: `Dockerfile`

**Key Points**:
- Multi-stage build (builder + runtime)
- Python 3.12-slim base
- Installs `postgresql-client` for migrations
- Exposes port via `$PORT` environment variable
- Health check on `/health` endpoint
- Runs `startup.sh` as entrypoint

**Render Usage**: Can use this Dockerfile OR use Render's native Python environment

### B. startup.sh (CRITICAL)

**File**: `startup.sh`

**What it does**:
1. Tests database connection
2. Runs Python import check
3. Executes 39 SQL migration files sequentially
4. Starts uvicorn server on `$PORT`

**Render Requirement**: Must run this script as start command

### C. railway.toml

**Status**: ❌ Does NOT exist

No Railway-specific config file.

### D. vercel.json (frontend only)

**File**: `vercel.json`

**Purpose**: Frontend deployment config (NOT relevant for backend migration)

---

## 12. PACKAGE FILES

### A. requirements.txt (Backend)

**File**: `requirements.txt`

**Key Dependencies**:
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic[email]==2.5.3
psycopg2-binary==2.9.9
SQLAlchemy==2.0.25
google-auth==2.27.0
PyJWT==2.11.0
redis==5.0.1
openpyxl==3.1.2
reportlab==4.0.9
python-dotenv==1.0.0
pytest==7.4.4
```

**No scripts section** (Python doesn't use package.json scripts)

### B. frontend/package.json

**File**: `frontend/package.json`

**Scripts**:
```json
{
  "dev": "vite",
  "build": "tsc -b && vite build",
  "lint": "eslint .",
  "preview": "vite preview"
}
```

**Note**: Frontend is deployed separately on Vercel, NOT on Render

---

## 13. DATABASE_URL FORMAT

**Variable Name**: `DATABASE_URL`

**Format**: Standard PostgreSQL connection string
```
postgresql://username:password@hostname:port/database_name
```

**Example**:
```
postgresql://postgres:mypassword@dpg-abc123.oregon-postgres.render.com:5432/faculty_db
```

**Code Usage**: `app/core/config.py` line 18:
```python
class Settings(BaseSettings):
    DATABASE_URL: str  # ← Loaded from environment
```

**Validation**: `app/core/config.py` lines 115-117:
```python
if not self.DATABASE_URL.startswith("postgresql://"):
    raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
```

---

## 14. HARDCODED RAILWAY URLs

**Search Results**: Found in documentation/test files ONLY

**Production Code**: ✅ NO hardcoded Railway URLs

**Files with Railway URLs** (all non-production):
- `call_admin_apis.py` - Test script
- `call_apis.py` - Test script
- `call_proper_shift_fix.py` - Test script
- `call_shift_apis.py` - Test script
- `check_semesters.py` - Test script
- Various `.md` documentation files

**Action Required**: Update test scripts to use new Render URL after migration

**Production Code Check**:
- ✅ `app/main.py` - Uses `FRONTEND_URL` env var
- ✅ `app/core/config.py` - No hardcoded URLs
- ✅ `frontend/src/api/client.ts` - Uses `VITE_API_URL` env var

---

## RENDER MIGRATION CHECKLIST

### Pre-Migration

- [ ] Export Railway PostgreSQL database
- [ ] Save all environment variables from Railway dashboard
- [ ] Note current Railway URL for updating test scripts

### Render Setup

- [ ] Create new Render account/project
- [ ] Create PostgreSQL database on Render
- [ ] Create Web Service on Render
- [ ] Configure build settings:
  - Build Command: (leave empty)
  - Start Command: `sh startup.sh`
  - Environment: Python 3.12

### Environment Variables (Set in Render Dashboard)

- [ ] DATABASE_URL (auto-provided by Render PostgreSQL)
- [ ] SECRET_KEY (generate new: `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] GOOGLE_CLIENT_ID (copy from Railway)
- [ ] GOOGLE_CLIENT_SECRET (copy from Railway)
- [ ] GOOGLE_REDIRECT_URI (update to: `https://your-app.onrender.com/api/auth/callback`)
- [ ] FRONTEND_URL (set to: `https://fwms-workload-system.vercel.app`)
- [ ] ENV (set to: `production`)
- [ ] DEV_AUTH_BYPASS (set to: `False`)

### Google OAuth Update

- [ ] Go to Google Cloud Console
- [ ] Update Authorized Redirect URIs
- [ ] Add: `https://your-app.onrender.com/api/auth/callback`
- [ ] Remove old Railway URL

### Database Migration

- [ ] Import database dump to Render PostgreSQL
- [ ] OR let startup.sh run all migrations on first deploy

### Vercel Frontend Update

- [ ] Update VITE_API_URL in Vercel dashboard
- [ ] New value: `https://your-app.onrender.com`
- [ ] Trigger new Vercel deployment

### Testing

- [ ] Test health endpoint: `curl https://your-app.onrender.com/health`
- [ ] Test OAuth login flow
- [ ] Test preference submission
- [ ] Test allocation
- [ ] Test report generation

### Post-Migration

- [ ] Update test scripts with new Render URL
- [ ] Update documentation
- [ ] Monitor Render logs for errors
- [ ] Verify database connection pool metrics

---

## CRITICAL NOTES FOR RENDER

1. **Startup Time**: First deploy will take 5-10 minutes (39 migrations)
2. **Health Check**: Use `/health` endpoint (NOT `/api/health`)
3. **Port**: Render provides PORT automatically - startup.sh handles it
4. **Migrations**: Run automatically on every deploy via startup.sh
5. **Free Tier Limitations**:
   - Service spins down after 15 minutes of inactivity
   - Cold start takes 30-60 seconds
   - Database limited to 1GB storage
6. **Session Storage**: Use in-memory (loses sessions on restart) or add Redis
7. **File Storage**: No persistent storage needed (all in-memory processing)

---

## DIFFERENCES: Railway vs Render

| Feature | Railway | Render |
|---------|---------|--------|
| DATABASE_URL format | ✅ Same | ✅ Same |
| PORT env var | ✅ Provided | ✅ Provided |
| PostgreSQL | ✅ Included | ✅ Included |
| Free tier | ❌ Removed | ✅ Available |
| Cold starts | ❌ No | ✅ Yes (15min idle) |
| Build time | ~2 min | ~2-3 min |
| Startup script | ✅ Supported | ✅ Supported |

---

## ESTIMATED MIGRATION TIME

- **Setup**: 30 minutes
- **Database export/import**: 15 minutes
- **First deployment**: 10 minutes (migrations)
- **Testing**: 30 minutes
- **Total**: ~90 minutes

---

## SUPPORT RESOURCES

- Render Docs: https://render.com/docs
- Render Python Guide: https://render.com/docs/deploy-fastapi
- Render PostgreSQL: https://render.com/docs/databases

---

**Generated**: 2026-04-19
**Project**: Faculty Workload Management System
**Migration**: Railway → Render Free Tier
