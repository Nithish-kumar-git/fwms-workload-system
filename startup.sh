#!/bin/sh
set -e

echo "Running database migrations..."

run_migration() {
    echo "Running $1..."
    psql $DATABASE_URL -f migrations/$1 || echo "Warning: $1 failed (may already be applied)"
}

run_migration schema.sql
run_migration 002_window_lifecycle.sql
run_migration 003_seed_minimal.sql
run_migration 004_seed_demo.sql
run_migration 005_workload_schema.sql
run_migration 006_academic_seed.sql
run_migration 007_faculty_seed.sql
run_migration 008_admin_override_schema.sql
run_migration 009_window_audit_types.sql
run_migration 010_academic_cycle_support.sql
run_migration 011_update_staff_emails.sql
run_migration 011b_workload_snapshot.sql
run_migration 012_fix_audit_constraint.sql
run_migration 013_single_active_cycle.sql
run_migration 014_fix_allocation_pipeline.sql
run_migration 015_fix_preference_constraint.sql
run_migration 016_semester_state_management.sql
run_migration 017_add_role_column.sql
run_migration 019_final_fixed.sql
run_migration 019_real_subjects_final.sql
run_migration 020_real_faculty.sql
run_migration 021_semester_specific_cycles.sql

echo "All migrations done. Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
