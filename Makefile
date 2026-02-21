# Makefile for Faculty Subject Selection System
# One-command development environment management

.PHONY: help up down restart logs test clean build

# Default target
help:
	@echo "Faculty Subject Selection System - Docker Commands"
	@echo ""
	@echo "Development:"
	@echo "  make up        - Start development environment (DB + App)"
	@echo "  make down      - Stop development environment"
	@echo "  make restart   - Restart development environment"
	@echo "  make logs      - View application logs"
	@echo "  make shell     - Open shell in app container"
	@echo ""
	@echo "Testing:"
	@echo "  make test      - Run all tests in isolated environment"
	@echo "  make test-unit - Run unit tests only"
	@echo "  make test-int  - Run integration tests only"
	@echo ""
	@echo "Maintenance:"
	@echo "  make build     - Rebuild Docker images"
	@echo "  make clean     - Remove all containers and volumes"
	@echo "  make migrate   - Run migrations manually"
	@echo "  make psql      - Connect to development database"

# ============================================================================
# Development Commands
# ============================================================================

up:
	@echo "Starting development environment..."
	docker-compose up -d
	@echo ""
	@echo "✅ Environment ready!"
	@echo "   API: http://localhost:8000"
	@echo "   Health: http://localhost:8000/health"
	@echo "   Docs: http://localhost:8000/docs"
	@echo ""
	@echo "View logs: make logs"

down:
	@echo "Stopping development environment..."
	docker-compose down

restart:
	@echo "Restarting development environment..."
	docker-compose restart

logs:
	docker-compose logs -f app

shell:
	docker-compose exec app sh

# ============================================================================
# Testing Commands
# ============================================================================

test:
	@echo "Running all tests in isolated environment..."
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test
	docker-compose -f docker-compose.test.yml down

test-unit:
	@echo "Running unit tests..."
	docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_window_lifecycle.py -v
	docker-compose -f docker-compose.test.yml down

test-int:
	@echo "Running integration tests..."
	docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_window_integration.py -v
	docker-compose -f docker-compose.test.yml down

# ============================================================================
# Maintenance Commands
# ============================================================================

build:
	@echo "Building Docker images..."
	docker-compose build --no-cache

clean:
	@echo "Removing all containers, volumes, and images..."
	docker-compose down -v --rmi local
	docker-compose -f docker-compose.test.yml down -v --rmi local
	@echo "✅ Cleanup complete"

migrate:
	@echo "Running migrations..."
	docker-compose exec app sh -c "psql $$DATABASE_URL -f migrations/schema.sql"
	docker-compose exec app sh -c "psql $$DATABASE_URL -f migrations/002_window_lifecycle.sql"
	@echo "✅ Migrations complete"

psql:
	@echo "Connecting to development database..."
	docker-compose exec db psql -U postgres -d faculty_selection

# ============================================================================
# Health Check
# ============================================================================

health:
	@echo "Checking application health..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ Application not responding"
	@echo ""
	@curl -s http://localhost:8000/health/metrics | python -m json.tool || echo "❌ Metrics endpoint not responding"
