# Bugfix Requirements Document

## Introduction

This bugfix addresses a critical system failure caused by incomplete migration from the ODD/EVEN semester_type architecture to semester-specific cycles. Migration 021 successfully updated the database schema to use `semester_id` (1-6) instead of `semester_type` (ODD/EVEN), but the backend API layer and frontend were not updated, causing complete system breakage.

The system is currently non-functional because:
- Backend APIs expect `semester_type` parameter that no longer exists in the database
- Frontend sends `semester_type` to backend endpoints
- Database queries fail because the `academic_cycle` table was renamed to `academic_cycle_old_backup`
- The new `cycle` table structure is not being used by the application code

This affects all core workflows: cycle management, preference submission, allocation, and reporting.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN coordinator attempts to create a new cycle THEN the system expects `semester_type` (ODD/EVEN) parameter instead of `semester_id` (1-6)

1.2 WHEN coordinator attempts to create a cycle THEN the backend queries the non-existent `academic_cycle` table instead of the new `cycle` table

1.3 WHEN coordinator views the cycles list THEN the system displays "ODD/EVEN" labels instead of semester-specific labels (I, II, III, IV, V, VI)

1.4 WHEN faculty attempts to submit preferences THEN the system queries `academic_cycle` table which no longer exists, causing database errors

1.5 WHEN coordinator runs allocation THEN the system uses `semester_type` filtering instead of `semester_id`, causing incorrect subject filtering

1.6 WHEN coordinator generates reports THEN the system queries using `semester_type` parameter which no longer exists in `subject_offering` table

1.7 WHEN frontend loads cycle management page THEN the UI shows ODD/EVEN dropdown instead of semester selector (I-VI)

1.8 WHEN any API endpoint tries to get active cycle THEN it queries `academic_cycle` table which has been renamed to `academic_cycle_old_backup`

1.9 WHEN preference service validates submissions THEN it queries `academic_cycle.is_active` which fails because the table no longer exists

1.10 WHEN allocation service loads subject offerings THEN it filters by `semester_type` column which was removed from `subject_offering` table

### Expected Behavior (Correct)

2.1 WHEN coordinator attempts to create a new cycle THEN the system SHALL accept `semester_id` (1-6) parameter and create a cycle in the new `cycle` table

2.2 WHEN coordinator attempts to create a cycle THEN the backend SHALL query the new `cycle` table and join with `academic_year` and `semester` tables

2.3 WHEN coordinator views the cycles list THEN the system SHALL display semester-specific labels (I, II, III, IV, V, VI) from the `semester` table

2.4 WHEN faculty attempts to submit preferences THEN the system SHALL query the new `cycle` table to get the active cycle

2.5 WHEN coordinator runs allocation THEN the system SHALL filter subject offerings by `semester_id` from the active cycle

2.6 WHEN coordinator generates reports THEN the system SHALL resolve semester information from the `cycle` table joined with `semester` table

2.7 WHEN frontend loads cycle management page THEN the UI SHALL show a semester selector with options I, II, III, IV, V, VI

2.8 WHEN any API endpoint tries to get active cycle THEN it SHALL query the new `cycle` table WHERE status = 'OPEN'

2.9 WHEN preference service validates submissions THEN it SHALL query `cycle` table with status = 'OPEN' to get the active cycle

2.10 WHEN allocation service loads subject offerings THEN it SHALL filter by `semester_id` from the `semester` table

### Unchanged Behavior (Regression Prevention)

3.1 WHEN coordinator activates a cycle THEN the system SHALL CONTINUE TO ensure only one cycle is active at a time

3.2 WHEN faculty submits preferences THEN the system SHALL CONTINUE TO validate all 5 institutional rules (PREF-01 through PREF-05, SHIFT-01, CT-01)

3.3 WHEN allocation runs THEN the system SHALL CONTINUE TO respect workload constraints (tch_norm) and shift compatibility

3.4 WHEN reports are generated THEN the system SHALL CONTINUE TO show faculty workload, subject summary, and department statistics

3.5 WHEN preference window is closed THEN the system SHALL CONTINUE TO block preference submissions

3.6 WHEN semester is in FROZEN state THEN the system SHALL CONTINUE TO block all modifications

3.7 WHEN allocation completes THEN the system SHALL CONTINUE TO update workload_summary table

3.8 WHEN cycle is locked (HOD approved) THEN the system SHALL CONTINUE TO block all write operations

3.9 WHEN faculty views their preferences THEN the system SHALL CONTINUE TO show only preferences for the active cycle

3.10 WHEN coordinator views unallocated subjects THEN the system SHALL CONTINUE TO show subjects that could not be assigned

3.11 WHEN staff authentication occurs THEN the system SHALL CONTINUE TO validate JWT tokens and role permissions

3.12 WHEN database transactions fail THEN the system SHALL CONTINUE TO rollback changes and return error messages
