# Docker Development Environment — Quick Start

## One-Command Setup

```bash
# Start development environment
make up

# Run tests
make test

# Stop environment
make down
```

## Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Make (optional, can use docker-compose directly)

## Environment Variables

Create `.env` file (optional, defaults provided):

```bash
# OAuth (required for production)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Security (required for production)
SECRET_KEY=your-secret-key

# Optional
LOG_LEVEL=INFO
SESSION_BACKEND=memory
```

## Available Commands

### Development
- `make up` — Start DB + App (auto-migrates)
- `make down` — Stop all services
- `make restart` — Restart services
- `make logs` — View application logs
- `make shell` — Open shell in app container

### Testing
- `make test` — Run all tests (isolated DB)
- `make test-unit` — Run unit tests only
- `make test-int` — Run integration tests only

### Maintenance
- `make build` — Rebuild Docker images
- `make clean` — Remove all containers/volumes
- `make migrate` — Run migrations manually
- `make psql` — Connect to development DB
- `make health` — Check application health

## Architecture

```
docker-compose.yml          # Development environment
├── db (postgres:16)        # Port 5432
└── app (python:3.12-slim)  # Port 8000 (hot reload)

docker-compose.test.yml     # Test environment
├── test_db (postgres:16)   # Port 5433 (tmpfs)
└── test (pytest runner)    # Isolated test execution
```

## Features

✅ **Zero Global Dependencies** — No Python/pytest/uvicorn required on host  
✅ **Automatic Migrations** — Runs on startup  
✅ **Hot Reload** — Code changes reflected immediately  
✅ **Isolated Testing** — Separate test DB with tmpfs  
✅ **Health Checks** — Built-in container health monitoring  
✅ **Multi-Stage Build** — Minimal production image  

## Accessing Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/health/metrics
- **Database**: localhost:5432 (user: postgres, pass: postgres)

## Troubleshooting

**Port already in use**:
```bash
make down
docker ps -a  # Check for orphaned containers
```

**Database connection failed**:
```bash
make logs  # Check if DB is healthy
make psql  # Test direct connection
```

**Migrations failed**:
```bash
make shell
psql $DATABASE_URL -f migrations/schema.sql
```

## Production Deployment

See `DEPLOYMENT.md` for production configuration (not included in dev setup).

**DO NOT** use development credentials in production.
