# Requirements Document

## Introduction

The Coordinator Preference Review Dashboard provides TT Coordinators and HODs with a centralized interface to monitor faculty preference submission status and review allocation results. This feature enables coordinators to track which faculty have submitted preferences, identify incomplete submissions, and assess workload distribution after allocation runs.

The dashboard consolidates two critical views: preference submission tracking (before allocation) and allocation result review (after allocation), allowing coordinators to manage the complete preference-to-allocation workflow from a single interface.

## Glossary

- **Dashboard**: The Coordinator Preference Review Dashboard web page
- **Coordinator**: A user with role `tt_coordinator` or `hod`
- **Faculty**: A staff member who submits teaching preferences
- **Preference_System**: The existing system that stores faculty teaching preferences
- **Allocation_System**: The existing system that assigns subjects to faculty
- **Backend_API**: The FastAPI backend service
- **Frontend_UI**: The React TypeScript frontend application
- **Preference_Tab**: The "Preference Submissions" view in the Dashboard
- **Allocation_Tab**: The "Allocation Results" view in the Dashboard
- **Stats_Bar**: The statistics summary displayed above each tab's table
- **Data_Table**: The table component displaying staff records with expandable rows
- **Expandable_Row**: A table row that can be clicked to show additional details
- **Search_Box**: The input field for filtering table records
- **Active_Cycle**: The currently open academic cycle for preference collection and allocation

## Requirements

### Requirement 1: Dashboard Access Control

**User Story:** As a TT Coordinator or HOD, I want to access the Preference Review Dashboard, so that I can monitor preference submissions and allocation results.

#### Acceptance Criteria

1. WHEN a user with role `tt_coordinator` navigates to `/admin/preference-review`, THE Frontend_UI SHALL display the Dashboard
2. WHEN a user with role `hod` navigates to `/admin/preference-review`, THE Frontend_UI SHALL display the Dashboard
3. WHEN a user with role `faculty` attempts to navigate to `/admin/preference-review`, THE Frontend_UI SHALL redirect to the faculty dashboard
4. THE Frontend_UI SHALL display a navigation link to the Dashboard in the coordinator navigation menu between "Allocation" and "Review"

### Requirement 2: Preference Submission Overview Endpoint

**User Story:** As a Coordinator, I want to retrieve preference submission statistics for all faculty, so that I can identify who has submitted preferences and who has not.

#### Acceptance Criteria

1. THE Backend_API SHALL provide endpoint `GET /api/reports/coordinator/preference-overview`
2. WHEN the endpoint receives a request from an authenticated Coordinator, THE Backend_API SHALL return a list of all active faculty with their preference submission status
3. FOR EACH faculty record, THE Backend_API SHALL include staff id, employee code, name, total subjects available, subjects with preferences submitted, and submission status
4. THE Backend_API SHALL calculate submission status as "Submitted" WHEN all available subjects have preferences, "Partial" WHEN some subjects have preferences, and "Not Submitted" WHEN no preferences exist
5. WHEN a faculty member has submitted preferences, THE Backend_API SHALL include the list of subjects with their preference ranks in the response
6. THE Backend_API SHALL return HTTP 401 WHEN the request lacks valid authentication
7. THE Backend_API SHALL return HTTP 403 WHEN the authenticated user is not a Coordinator

### Requirement 3: Allocation Results Overview Endpoint

**User Story:** As a Coordinator, I want to retrieve allocation results for all faculty, so that I can assess workload distribution and identify overloaded or underloaded staff.

#### Acceptance Criteria

1. THE Backend_API SHALL provide endpoint `GET /api/reports/coordinator/allocation-overview`
2. WHEN the endpoint receives a request from an authenticated Coordinator, THE Backend_API SHALL return a list of all active faculty with their allocation details
3. FOR EACH faculty record, THE Backend_API SHALL include staff id, employee code, name, total teaching contact hours allocated, workload status, and list of assigned subjects
4. THE Backend_API SHALL calculate workload status as "Overloaded" WHEN total TCH exceeds 18, "Balanced" WHEN total TCH is between 14 and 18 inclusive, and "Underloaded" WHEN total TCH is less than 14
5. FOR EACH assigned subject, THE Backend_API SHALL include subject code, subject name, program, semester, section, and teaching contact hours
6. THE Backend_API SHALL return HTTP 401 WHEN the request lacks valid authentication
7. THE Backend_API SHALL return HTTP 403 WHEN the authenticated user is not a Coordinator

### Requirement 4: Preference Submissions Tab Display

**User Story:** As a Coordinator, I want to view preference submission status for all faculty in a table, so that I can quickly identify who needs to submit preferences.

#### Acceptance Criteria

1. WHEN the Dashboard loads, THE Frontend_UI SHALL display the Preference_Tab as the default active tab
2. THE Preference_Tab SHALL display a Stats_Bar showing total faculty count, submitted count, partial count, and not submitted count
3. THE Preference_Tab SHALL display a Search_Box above the Data_Table
4. THE Preference_Tab SHALL display a Data_Table with columns: Employee Code, Name, Available Subjects, Submitted Preferences, and Status
5. THE Data_Table SHALL display a status badge for each faculty member colored green for "Submitted", yellow for "Partial", and red for "Not Submitted"
6. WHEN a Coordinator clicks on a table row, THE Frontend_UI SHALL expand the row to show the list of subjects with their preference ranks
7. WHEN a Coordinator types in the Search_Box, THE Frontend_UI SHALL filter the Data_Table to show only rows matching the search term in employee code or name
8. THE Frontend_UI SHALL display a loading indicator WHILE fetching preference overview data from the Backend_API
9. WHEN the Backend_API returns an error, THE Frontend_UI SHALL display an error message with a retry button

### Requirement 5: Allocation Results Tab Display

**User Story:** As a Coordinator, I want to view allocation results for all faculty in a table, so that I can assess workload distribution and identify staffing issues.

#### Acceptance Criteria

1. WHEN a Coordinator clicks the "Allocation Results" tab, THE Frontend_UI SHALL display the Allocation_Tab
2. THE Allocation_Tab SHALL display a Stats_Bar showing total faculty count, overloaded count, balanced count, and underloaded count
3. THE Allocation_Tab SHALL display a Search_Box above the Data_Table
4. THE Allocation_Tab SHALL display a Data_Table with columns: Employee Code, Name, Total TCH, Assigned Subjects Count, and Workload Status
5. THE Data_Table SHALL display a workload status badge colored red for "Overloaded", green for "Balanced", and yellow for "Underloaded"
6. WHEN a Coordinator clicks on a table row, THE Frontend_UI SHALL expand the row to show the list of assigned subjects with their details
7. FOR EACH assigned subject in the expanded row, THE Frontend_UI SHALL display subject code, subject name, program, semester, section, and TCH
8. WHEN a Coordinator types in the Search_Box, THE Frontend_UI SHALL filter the Data_Table to show only rows matching the search term in employee code or name
9. THE Frontend_UI SHALL display a loading indicator WHILE fetching allocation overview data from the Backend_API
10. WHEN the Backend_API returns an error, THE Frontend_UI SHALL display an error message with a retry button

### Requirement 6: Dashboard Styling and Layout

**User Story:** As a Coordinator, I want the Dashboard to follow the existing application design patterns, so that the interface feels consistent and familiar.

#### Acceptance Criteria

1. THE Frontend_UI SHALL use the `glass-card` CSS class for the main dashboard container
2. THE Frontend_UI SHALL use the `data-table` CSS class for all tables
3. THE Frontend_UI SHALL use badge classes `badge-success`, `badge-warning`, and `badge-danger` for status indicators
4. THE Frontend_UI SHALL use the existing page layout pattern with `page-container`, `page-header`, `page-title`, and `page-subtitle` classes
5. THE Frontend_UI SHALL use icons from the `lucide-react` library for visual elements
6. THE Stats_Bar SHALL use a grid layout with equal-width stat cards displaying count and label
7. THE Search_Box SHALL include a search icon positioned on the left side of the input field

### Requirement 7: Navigation Integration

**User Story:** As a Coordinator, I want to access the Dashboard from the main navigation menu, so that I can easily navigate to it from any page.

#### Acceptance Criteria

1. THE Frontend_UI SHALL add a navigation item labeled "Pref Review" to the coordinator navigation menu
2. THE navigation item SHALL be positioned between the "Allocation" and "Review" items in the menu
3. WHEN a Coordinator clicks the "Pref Review" navigation item, THE Frontend_UI SHALL navigate to `/admin/preference-review`
4. THE navigation item SHALL use an appropriate icon from the `lucide-react` library
5. WHEN the current route is `/admin/preference-review`, THE navigation item SHALL display with active styling

### Requirement 8: Active Cycle Context

**User Story:** As a Coordinator, I want the Dashboard to show data for the currently active academic cycle, so that I see relevant and current information.

#### Acceptance Criteria

1. THE Backend_API SHALL filter preference overview data to include only subjects from the Active_Cycle
2. THE Backend_API SHALL filter allocation overview data to include only allocations from the Active_Cycle
3. WHEN no Active_Cycle exists, THE Backend_API SHALL return an empty list with HTTP 200
4. THE Frontend_UI SHALL display the active cycle's academic year and semester at the top of the Dashboard
5. WHEN no Active_Cycle exists, THE Frontend_UI SHALL display a message indicating no active cycle is configured
