# Implementation Plan: Coordinator Preference Review Dashboard

## Overview

This implementation plan creates a centralized dashboard for TT Coordinators and HODs to monitor faculty preference submissions and review allocation results. The feature consists of two backend API endpoints that aggregate data from existing database tables, and a React frontend page with tabbed views for preference tracking and allocation review.

The implementation follows established patterns from the reports module for backend data aggregation and the StaffEmailsPage for frontend UI layout and styling.

## Tasks

- [ ] 1. Implement backend service functions for data aggregation
  - [x] 1.1 Implement `get_preference_overview()` in `app/reports/service.py`
    - Query active cycle to get semester_id and academic_year
    - Fetch all active faculty from staff table
    - For each faculty, count total available subjects from subject_offering
    - For each faculty, count submitted preferences from faculty_preference
    - Calculate submission status: "Submitted" (all subjects), "Partial" (some subjects), "Not Submitted" (none)
    - Fetch preference details with subject information for expandable rows
    - Return aggregated data with total_faculty, submitted_count, partial_count, not_submitted_count, and records array
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 8.1_
  
  - [x] 1.2 Implement `get_allocation_overview()` in `app/reports/service.py`
    - Query active cycle to get semester_id and academic_year
    - Fetch all active faculty from staff table
    - For each faculty, sum total TCH from allocation joined with subject_offering
    - For each faculty, count assigned subjects
    - Calculate workload status: "Overloaded" (TCH > 18), "Balanced" (14 ≤ TCH ≤ 18), "Underloaded" (TCH < 14)
    - Fetch assigned subject details for expandable rows
    - Return aggregated data with total_faculty, overloaded_count, balanced_count, underloaded_count, and records array
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 8.2_
  
  - [ ] 1.3 Write unit tests for service functions
    - Test get_preference_overview() with no active cycle returns empty list
    - Test get_preference_overview() with faculty having all preferences submitted
    - Test get_preference_overview() with faculty having partial preferences
    - Test get_preference_overview() with faculty having no preferences
    - Test get_allocation_overview() with no active cycle returns empty list
    - Test get_allocation_overview() with overloaded faculty (TCH > 18)
    - Test get_allocation_overview() with balanced faculty (14 ≤ TCH ≤ 18)
    - Test get_allocation_overview() with underloaded faculty (TCH < 14)
    - _Requirements: 2.1-2.7, 3.1-3.7, 8.1-8.3_

- [ ] 2. Implement backend API endpoints
  - [x] 2.1 Add `GET /api/reports/coordinator/preference-overview` endpoint in `app/reports/router.py`
    - Use get_current_coordinator_id dependency for authentication
    - Call report_service.get_preference_overview()
    - Return JSON response with preference overview data
    - Handle authentication errors (HTTP 401) and authorization errors (HTTP 403)
    - _Requirements: 2.1, 2.2, 2.6, 2.7_
  
  - [x] 2.2 Add `GET /api/reports/coordinator/allocation-overview` endpoint in `app/reports/router.py`
    - Use get_current_coordinator_id dependency for authentication
    - Call report_service.get_allocation_overview()
    - Return JSON response with allocation overview data
    - Handle authentication errors (HTTP 401) and authorization errors (HTTP 403)
    - _Requirements: 3.1, 3.2, 3.6, 3.7_
  
  - [ ] 2.3 Write integration tests for API endpoints
    - Test preference-overview endpoint with coordinator role returns HTTP 200
    - Test preference-overview endpoint with faculty role returns HTTP 403
    - Test preference-overview endpoint without authentication returns HTTP 401
    - Test allocation-overview endpoint with coordinator role returns HTTP 200
    - Test allocation-overview endpoint with faculty role returns HTTP 403
    - Test allocation-overview endpoint without authentication returns HTTP 401
    - _Requirements: 1.1, 1.2, 1.3, 2.6, 2.7, 3.6, 3.7_

- [x] 3. Checkpoint - Verify backend endpoints work correctly
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement frontend API client functions
  - [x] 4.1 Add API client functions in `frontend/src/api/client.ts`
    - Implement fetchPreferenceOverview() function to call GET /api/reports/coordinator/preference-overview
    - Implement fetchAllocationOverview() function to call GET /api/reports/coordinator/allocation-overview
    - Add proper TypeScript types for request and response data
    - Include error handling for network failures and API errors
    - _Requirements: 2.1, 3.1, 4.8, 4.9, 5.9, 5.10_

- [ ] 5. Implement frontend dashboard page component
  - [x] 5.1 Create `PreferenceReviewDashboardPage.tsx` with basic structure
    - Set up component with page-container, page-header, page-title, page-subtitle classes
    - Add state management for activeTab, prefData, allocData, search, expandedRows, loading, activeCycle
    - Implement useEffect hooks to fetch active cycle and dashboard data on mount
    - Add loading indicator while fetching data
    - _Requirements: 4.1, 4.8, 5.9, 6.4, 8.4_
  
  - [x] 5.2 Implement Preference Submissions tab
    - Create tab navigation with "Preference Submissions" as default active tab
    - Implement stats bar showing total_faculty, submitted_count, partial_count, not_submitted_count
    - Create data table with columns: Employee Code, Name, Available Subjects, Submitted Preferences, Status
    - Add status badges with colors: green for "Submitted", yellow for "Partial", red for "Not Submitted"
    - Implement expandable rows to show preference details with subject code, name, program, semester, section, and rank
    - Add search box with icon for filtering by employee code or name
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 6.3, 6.5, 6.6, 6.7_
  
  - [x] 5.3 Implement Allocation Results tab
    - Create "Allocation Results" tab button
    - Implement stats bar showing total_faculty, overloaded_count, balanced_count, underloaded_count
    - Create data table with columns: Employee Code, Name, Total TCH, Assigned Subjects Count, Workload Status
    - Add workload status badges with colors: red for "Overloaded", green for "Balanced", yellow for "Underloaded"
    - Implement expandable rows to show assigned subject details with subject code, name, program, semester, section, and TCH
    - Add search box with icon for filtering by employee code or name
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 6.3, 6.5, 6.6, 6.7_
  
  - [x] 5.4 Implement active cycle display and error handling
    - Display active cycle's academic year and semester at top of dashboard
    - Show "No active cycle configured" message when no active cycle exists
    - Implement error message display with retry button for API failures
    - Add toast notifications for network timeouts and errors
    - _Requirements: 4.9, 5.10, 8.3, 8.4, 8.5_
  
  - [x] 5.5 Apply styling and layout patterns
    - Use glass-card CSS class for main dashboard container
    - Use data-table CSS class for all tables
    - Use badge classes: badge-success, badge-warning, badge-danger for status indicators
    - Use icons from lucide-react library (Search, ChevronDown, ChevronUp, etc.)
    - Implement grid layout for stats bar with equal-width stat cards
    - Position search icon on left side of input field
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_
  
  - [ ] 5.6 Write component tests for PreferenceReviewDashboardPage
    - Test page renders with loading state initially
    - Test preference tab displays stats bar with correct counts
    - Test allocation tab displays stats bar with correct counts
    - Test search box filters table rows by employee code
    - Test search box filters table rows by name
    - Test clicking row expands to show subject details
    - Test clicking expanded row collapses details
    - Test status badge colors are correct
    - Test workload badge colors are correct
    - Test error state displays error message and retry button
    - _Requirements: 4.1-4.9, 5.1-5.10_

- [x] 6. Integrate dashboard into application navigation and routing
  - [x] 6.1 Add navigation item to `frontend/src/components/Navbar.tsx`
    - Add "Pref Review" item to coordinatorItems array
    - Position between "Allocation" and "Review" items
    - Use ClipboardList icon from lucide-react
    - Set path to /admin/preference-review
    - Implement active styling when current route matches
    - _Requirements: 1.4, 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 6.2 Add route to `frontend/src/App.tsx`
    - Add route for /admin/preference-review within RequireCoordinator guard
    - Import and render PreferenceReviewDashboardPage component
    - Ensure route is positioned logically with other coordinator routes
    - _Requirements: 1.1, 1.2, 1.3_

- [-] 7. Final checkpoint - End-to-end testing and verification
  - Verify coordinator can access /admin/preference-review page
  - Verify faculty cannot access /admin/preference-review page (redirected)
  - Verify navigation item appears and shows active styling
  - Verify active cycle displays at top of page
  - Verify both tabs load and display correct data
  - Verify search functionality works on both tabs
  - Verify row expansion works on both tabs
  - Verify badge colors are correct
  - Verify error handling works with retry button
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The implementation leverages existing database tables and follows established patterns from the reports module and StaffEmailsPage
- No database migrations are required as all necessary tables already exist
- The feature uses Python for backend and TypeScript/React for frontend
- Authentication and authorization are handled by existing dependencies (get_current_coordinator_id)
- Active cycle context is automatically filtered in backend service functions
