# Quick Start Guide

## Start the Application

```bash
# Start all services (database, backend, frontend)
docker-compose up --build
```

Wait for:
- ✅ Database migrations complete (17 migrations)
- ✅ Backend server running on port 8000
- ✅ Frontend dev server running on port 5173

## Access the Application

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Test Login (DEV_AUTH_BYPASS enabled)

Click "Login with Google" - you'll be logged in as HOD automatically.

## Stop the Application

```bash
docker-compose down
```

## Reset Database (if needed)

```bash
# Stop and remove all data
docker-compose down -v

# Start fresh (will re-run all migrations)
docker-compose up --build
```

## View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Database only
docker-compose logs -f db
```

## Environment Configuration

Your `.env` file is already configured for local development with:
- PostgreSQL database
- DEV_AUTH_BYPASS enabled (no real OAuth needed)
- Memory-based sessions
- Log-based email backend

No additional configuration needed for local testing.

## Next Steps

Follow the comprehensive test checklist in `LOCAL_TEST_CHECKLIST.md` to verify all functionality.
