#!/bin/sh
set -e

echo "DATABASE_URL is: $DATABASE_URL"
echo "Testing DB connection..."
psql $DATABASE_URL -c "SELECT 1;" || { echo "DB CONNECTION FAILED"; exit 1; }

echo "Checking Python imports..."
python app/startup_check.py || { echo "IMPORT CHECK FAILED - see above"; exit 1; }

echo "Running database migrations..."

run_migration() {
    echo "Running $1..."
    if psql $DATABASE_URL -f migrations/$1; then
        echo "OK: $1"
    else
        echo "SKIP: $1 (may already be applied)"
    fi
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
run_migration 022_fix_production_data.sql
run_migration 023_fix_active_cycle.sql
run_migration 024_fix_preference_window.sql
run_migration 025_open_all_even_cycles.sql
run_migration 026_odd_semester_subjects.sql
run_migration 027_cleanup_odd_semester_offerings.sql
run_migration 028_cleanup_duplicates.sql
run_migration 029_cleanup_duplicate_offerings.sql
run_migration 030_odd_semester_subjects.sql
run_migration 031_fix_odd_semester_offerings.sql
run_migration 032_clear_test_preferences.sql
run_migration 033_fix_staff_emails.sql
run_migration 034_fix_real_staff_emails.sql
run_migration 035_fix_audit_log_constraint.sql
run_migration 036_add_curriculum_year.sql
run_migration 037_fix_ct_program_names.sql

echo "All migrations done. Starting server..."
# Use PORT from environment, default to 8000 if not set
PORT=${PORT:-8000}
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
