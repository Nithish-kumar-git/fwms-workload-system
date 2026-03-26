# Bugfix Requirements Document

## Introduction

After migrating from the `academic_cycle` table to the `cycle` table (migration 021), several preference system endpoints are crashing with "column so.academic_cycle_id does not exist" errors. The `subject_offering` table schema changed during the migration - the `academic_cycle_id` column was renamed to `old_academic_cycle_id`, and the table now uses `academic_year`, `semester_id`, and `academic_year_id` to reference cycles. However, multiple service files still reference the old `so.academic_cycle_id` column, causing 500 errors when faculty try to view their preferences or coordinators check preference window status.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a faculty member calls `/api/preferences/me` to view their submitted preferences THEN the system crashes with "column so.academic_cycle_id does not exist" error (line 356 in `app/preference/service.py`)

1.2 WHEN a coordinator calls `/api/pref-window/status` to check preference window status THEN the system crashes with "column so.academic_cycle_id does not exist" error (in `app/preference/window_service.py`)

1.3 WHEN the allocation service queries subject offerings by cycle THEN the system crashes with "column so.academic_cycle_id does not exist" error (line 131 in `app/allocation/service.py`)

1.4 WHEN the semester state service queries subject offerings THEN the system crashes with "column so.academic_cycle_id does not exist" error (line 85 in `app/coordinator/semester_state_service.py`)

### Expected Behavior (Correct)

2.1 WHEN a faculty member calls `/api/preferences/me` to view their submitted preferences THEN the system SHALL successfully retrieve preferences by joining through the new cycle table structure using `academic_year`, `semester_id`, and `academic_year_id`

2.2 WHEN a coordinator calls `/api/pref-window/status` to check preference window status THEN the system SHALL successfully retrieve window status by joining through the new cycle table structure

2.3 WHEN the allocation service queries subject offerings by cycle THEN the system SHALL successfully filter offerings by joining the cycle table on `academic_year_id` and `semester_id`

2.4 WHEN the semester state service queries subject offerings THEN the system SHALL successfully retrieve offerings without referencing the non-existent `academic_cycle_id` column

### Unchanged Behavior (Regression Prevention)

3.1 WHEN faculty submit new preferences THEN the system SHALL CONTINUE TO validate and store preferences correctly using the `faculty_preference.cycle_id` column

3.2 WHEN coordinators open or close preference windows THEN the system SHALL CONTINUE TO manage window lifecycle correctly using the `selection_window.cycle_id` column

3.3 WHEN allocations are created THEN the system SHALL CONTINUE TO store allocations correctly using the `allocation.cycle_id` column

3.4 WHEN reports are generated THEN the system SHALL CONTINUE TO query workload data correctly using the cycle table structure
