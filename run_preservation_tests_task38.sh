#!/bin/sh
set -e

echo "Running migrations on test DB..."
for f in migrations/schema.sql migrations/002_window_lifecycle.sql migrations/003_seed_minimal.sql migrations/005_workload_schema.sql migrations/010_academic_cycle_support.sql migrations/016_semester_state_management.sql migrations/021_semester_specific_cycles.sql; do
  echo "Running $f..."
  psql $DATABASE_URL -f $f || exit 1
done

echo "Running preservation tests..."
pytest tests/test_preservation_properties.py -v --tb=short --color=yes
