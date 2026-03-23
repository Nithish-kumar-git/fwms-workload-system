@echo off
set DB=PostgreSQL:postgresql://postgres:PwkKicjRAziuXFEgyHNjFFbhjkHpJvGU@centerbeam.proxy.rlwy.net:33638/railway
psql "%DB%" < migrations\001_schema.sql
psql "%DB%" < migrations\002_initial_data.sql
psql "%DB%" < migrations\003_batch_specialization.sql
psql "%DB%" < migrations\004_demo_staff.sql
psql "%DB%" < migrations\005_workload_schema.sql
psql "%DB%" < migrations\006_academic_seed.sql
psql "%DB%" < migrations\007_faculty_seed.sql
psql "%DB%" < migrations\008_subject_offerings.sql
psql "%DB%" < migrations\009_preference_schema.sql
psql "%DB%" < migrations\010_academic_cycle.sql
psql "%DB%" < migrations\011_workload_snapshot.sql
psql "%DB%" < migrations\011b_workload_snapshot.sql
psql "%DB%" < migrations\012_fix_audit_constraint.sql
psql "%DB%" < migrations\013_single_active_cycle.sql
psql "%DB%" < migrations\014_fix_allocation_pipeline.sql
psql "%DB%" < migrations\015_fix_preference_constraint.sql
psql "%DB%" < migrations\016_semester_state_management.sql
psql "%DB%" < migrations\017_add_role_column.sql
psql "%DB%" < migrations\019_final_fixed.sql
psql "%DB%" < migrations\020_real_faculty.sql
echo All migrations done!
pause