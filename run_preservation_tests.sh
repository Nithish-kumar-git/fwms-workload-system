#!/bin/bash
# Script to run preservation property tests with proper database setup

set -e

echo "Starting test database..."
docker-compose -f docker-compose.test.yml up -d test_db

echo "Waiting for database to be ready..."
sleep 5

echo "Running migrations..."
docker-compose -f docker-compose.test.yml exec -T test_db psql -U postgres -d faculty_selection_test <<EOF
-- Run all necessary migrations
\i /docker-entrypoint-initdb.d/schema.sql
\i /docker-entrypoint-initdb.d/002_window_lifecycle.sql
\i /docker-entrypoint-initdb.d/003_seed_minimal.sql
\i /docker-entrypoint-initdb.d/005_workload_schema.sql
\i /docker-entrypoint-initdb.d/010_academic_cycle_support.sql
\i /docker-entrypoint-initdb.d/016_semester_state_management.sql
\i /docker-entrypoint-initdb.d/021_semester_specific_cycles.sql
EOF

echo "Running preservation tests..."
docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_preservation_properties.py -v --tb=short --color=yes

echo "Stopping test database..."
docker-compose -f docker-compose.test.yml down
