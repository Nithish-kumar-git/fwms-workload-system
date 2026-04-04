#!/bin/bash
# Script to run preservation property tests with proper database setup

set -e

echo "=== Starting Preservation Tests ==="

# Start test database
echo "Starting test database..."
docker-compose -f docker-compose.test.yml up -d test_db

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 5

# Run migrations and tests in one command
echo "Running migrations and tests..."
docker-compose -f docker-compose.test.yml run --rm test sh -c "
  echo 'Running migrations...' &&
  for f in migrations/schema.sql migrations/002_window_lifecycle.sql migrations/003_seed_minimal.sql migrations/005_workload_schema.sql migrations/010_academic_cycle_support.sql migrations/016_semester_state_management.sql migrations/021_semester_specific_cycles.sql; do
    echo \"Running \$f...\" &&
    psql \$DATABASE_URL -f \$f || exit 1
  done &&
  echo 'Running preservation tests...' &&
  pytest tests/test_preservation_properties.py -v --tb=short --color=yes
"

# Capture exit code
TEST_EXIT_CODE=$?

# Stop test database
echo "Stopping test database..."
docker-compose -f docker-compose.test.yml down

# Exit with test result
exit $TEST_EXIT_CODE
