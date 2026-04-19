# Design Document: Coordinator Preference Review Dashboard

## Overview

The Coordinator Preference Review Dashboard provides TT Coordinators and HODs with a centralized interface to monitor faculty preference submission status and review allocation results. The feature consists of two backend API endpoints that aggregate preference and allocation data, and a React frontend page with tabbed views for preference tracking and allocation review.

This design leverages existing database tables (`faculty_preference`, `allocation`, `subject_offering`, `staff`) and follows established patterns from the reports module for data aggregation and the StaffEmailsPage for UI layout and styling.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  PreferenceReviewDashboardPage.tsx                     │ │
│  │  - Tab navigation (Preferences / Allocations)          │ │
│  │  - Stats bars with summary metrics                     │ │
│  │  - Searchable data tables with expandable rows         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP GET
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                Backend API (FastAPI)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  app/reports/router.py                                 │ │
│  │  - GET /api/reports/coordinator/preference-overview    │ │
│  │  - GET /api/reports/coordinator/allocation-overview    │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  app/reports/service.py                                │ │
│  │  - get_preference_overview()                           │ │
│  │  - get_allocation_overview()                           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ SQL Queries
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database (PostgreSQL)                     │
│  - staff                                                     │
│  - faculty_preference                                        │
│  - allocation                                                │
│  - subject_offering                                          │
│  - cycle (for active cycle context)                          │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Page Load**: Frontend fetches active cycle context from `/api/cycles/active`
2. **Preference Tab**: Frontend calls `/api/reports/coordinator/preference-overview` → Backend aggregates preference submission status per faculty → Frontend displays stats and table
3. **Allocation Tab**: Frontend calls `/api/reports/coordinator/allocation-overview` → Backend aggregates allocation results per faculty → Frontend displays stats and table
4. **Search**: Client-side filtering of table rows by employee code or name
5. **Row Expansion**: Client-side toggle to show/hide detailed subject lists

## Components and Interfaces

### Backend Components

#### 1. Service Layer (`app/reports/service.py`)

**Function: `get_preference_overview()`**

```python
def get_preference_overview() -> dict:
    """
    Aggregate preference submission status for all active faculty.
    
    Returns:
        {
            "total_faculty": int,
            "submitted_count": int,
            "partial_count": int,
            "not_submitted_count": int,
            "records": [
                {
                    "staff_id": int,
                    "emp_code": str,
                    "name": str,
                    "total_subjects": int,
                    "submitted_preferences": int,
                    "status": "Submitted" | "Partial" | "Not Submitted",
                    "preferences": [
                        {
                            "subject_code": str,
                            "subject_name": str,
                            "program": str,
                            "semester": str,
                            "section": str,
                            "preference_rank": int
                        }
                    ]
                }
            ]
        }
    """
```

**Implementation Strategy**:
- Query active cycle to get `semester_id` and `academic_year`
- Get all active faculty from `staff` table where `is_active = true`
- For each faculty:
  - Count total available subjects from `subject_offering` filtered by active cycle
  - Count submitted preferences from `faculty_preference` joined with `subject_offering`
  - Calculate status: "Submitted" if all subjects have preferences, "Partial" if some, "Not Submitted" if none
  - Fetch preference details with subject information for expandable row display

**Function: `get_allocation_overview()`**

```python
def get_allocation_overview() -> dict:
    """
    Aggregate allocation results for all active faculty.
    
    Returns:
        {
            "total_faculty": int,
            "overloaded_count": int,
            "balanced_count": int,
            "underloaded_count": int,
            "records": [
                {
                    "staff_id": int,
                    "emp_code": str,
                    "name": str,
                    "total_tch": int,
                    "assigned_subjects_count": int,
                    "workload_status": "Overloaded" | "Balanced" | "Underloaded",
                    "assigned_subjects": [
                        {
                            "subject_code": str,
                            "subject_name": str,
                            "program": str,
                            "semester": str,
                            "section": str,
                            "tch": int
                        }
                    ]
                }
            ]
        }
    """
```

**Implementation Strategy**:
- Query active cycle to get `semester_id` and `academic_year`
- Get all active faculty from `staff` table where `is_active = true`
- For each faculty:
  - Sum total TCH from `allocation` joined with `subject_offering` filtered by active cycle
  - Count assigned subjects
  - Calculate workload status: "Overloaded" if TCH > 18, "Balanced" if 14 ≤ TCH ≤ 18, "Underloaded" if TCH < 14
  - Fetch assigned subject details for expandable row display

#### 2. Router Layer (`app/reports/router.py`)

**Endpoint: `GET /api/reports/coordinator/preference-overview`**

```python
@router.get("/coordinator/preference-overview")
async def preference_overview(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Preference submission overview for all faculty.
    Accessible by tt_coordinator and hod roles only.
    """
    data = report_service.get_preference_overview()
    return data
```

**Endpoint: `GET /api/reports/coordinator/allocation-overview`**

```python
@router.get("/coordinator/allocation-overview")
async def allocation_overview(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Allocation results overview for all faculty.
    Accessible by tt_coordinator and hod roles only.
    """
    data = report_service.get_allocation_overview()
    return data
```

**Authentication**: Both endpoints use `get_current_coordinator_id` dependency which enforces that the user has role `tt_coordinator` or `hod`. Returns HTTP 401 for unauthenticated requests and HTTP 403 for non-coordinator users.

### Frontend Components

#### 1. Page Component (`frontend/src/pages/PreferenceReviewDashboardPage.tsx`)

**Component Structure**:

```typescript
interface PreferenceRecord {
    staff_id: number;
    emp_code: string;
    name: string;
    total_subjects: number;
    submitted_preferences: number;
    status: 'Submitted' | 'Partial' | 'Not Submitted';
    preferences: Array<{
        subject_code: string;
        subject_name: string;
        program: string;
        semester: string;
        section: string;
        preference_rank: number;
    }>;
}

interface AllocationRecord {
    staff_id: number;
    emp_code: string;
    name: string;
    total_tch: number;
    assigned_subjects_count: number;
    workload_status: 'Overloaded' | 'Balanced' | 'Underloaded';
    assigned_subjects: Array<{
        subject_code: string;
        subject_name: string;
        program: string;
        semester: string;
        section: string;
        tch: number;
    }>;
}

export default function PreferenceReviewDashboardPage() {
    // State management
    const [activeTab, setActiveTab] = useState<'preferences' | 'allocations'>('preferences');
    const [prefData, setPrefData] = useState<PreferenceRecord[]>([]);
    const [allocData, setAllocData] = useState<AllocationRecord[]>([]);
    const [search, setSearch] = useState('');
    const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
    const [loading, setLoading] = useState(true);
    const [activeCycle, setActiveCycle] = useState<{year: string, semester: number} | null>(null);
    
    // Data fetching
    useEffect(() => {
        loadActiveCycle();
        loadPreferenceData();
        loadAllocationData();
    }, []);
    
    // Render tabs, stats bars, search box, and data tables
}
```

**Layout Pattern** (following StaffEmailsPage.tsx):
- Page container with `page-container` class
- Page header with `page-header`, `page-title`, `page-subtitle` classes
- Active cycle display at top
- Tab navigation buttons
- Stats bar with grid layout showing summary metrics
- Search box with icon
- Glass card containing data table
- Expandable rows for detailed subject lists

#### 2. Navigation Integration (`frontend/src/components/Navbar.tsx`)

Add navigation item to `coordinatorItems` array:

```typescript
const coordinatorItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/preferences', label: 'My Preferences', icon: BookOpen },
    { path: '/admin/window', label: 'Window', icon: Clock },
    { path: '/admin/cycles', label: 'Cycles', icon: CalendarDays },
    { path: '/admin/subjects', label: 'Subjects', icon: Upload },
    { path: '/admin/allocation', label: 'Allocation', icon: Settings },
    { path: '/admin/preference-review', label: 'Pref Review', icon: ClipboardList }, // NEW
    { path: '/admin/review', label: 'Review', icon: FileText },
    { path: '/admin/reports', label: 'Reports', icon: FileText },
];
```

Icon: Use `ClipboardList` from `lucide-react` for the preference review navigation item.

#### 3. Routing (`frontend/src/App.tsx`)

Add route within the `RequireCoordinator` guard:

```typescript
<Route element={<RequireCoordinator />}>
    <Route path="/dashboard" element={<DashboardPage />} />
    <Route path="/admin/allocation" element={<AllocationPage />} />
    <Route path="/admin/preference-review" element={<PreferenceReviewDashboardPage />} />
    <Route path="/admin/review" element={<ReviewPage />} />
    {/* ... other coordinator routes */}
</Route>
```

## Data Models

### Database Schema (Existing Tables)

**staff**
- `id`: BIGINT PRIMARY KEY
- `emp_code`: VARCHAR(20) UNIQUE
- `name`: VARCHAR(255)
- `email`: VARCHAR(255)
- `designation`: VARCHAR(50)
- `tch_norm`: INTEGER (default teaching contact hours norm)
- `is_active`: BOOLEAN

**faculty_preference**
- `id`: BIGINT PRIMARY KEY
- `staff_id`: BIGINT FOREIGN KEY → staff(id)
- `subject_offering_id`: BIGINT FOREIGN KEY → subject_offering(id)
- `preference_number`: INTEGER (1-5)
- `submitted_at`: TIMESTAMPTZ

**allocation**
- `id`: BIGINT PRIMARY KEY
- `staff_id`: BIGINT FOREIGN KEY → staff(id)
- `subject_offering_id`: BIGINT FOREIGN KEY → subject_offering(id)
- `l_assigned`: INTEGER
- `t_assigned`: INTEGER
- `p_assigned`: INTEGER
- `allocated_at`: TIMESTAMPTZ

**subject_offering**
- `id`: BIGINT PRIMARY KEY
- `subject_id`: BIGINT FOREIGN KEY → subject(id)
- `program_id`: BIGINT FOREIGN KEY → program(id)
- `semester_id`: BIGINT FOREIGN KEY → semester(id)
- `section_id`: BIGINT FOREIGN KEY → section(id)
- `academic_year`: VARCHAR(20)
- `is_active`: BOOLEAN

**subject**
- `id`: BIGINT PRIMARY KEY
- `code`: VARCHAR(20)
- `name`: VARCHAR(255)
- `tch`: INTEGER (teaching contact hours)

**cycle**
- `id`: BIGINT PRIMARY KEY
- `academic_year_id`: BIGINT
- `semester_id`: BIGINT
- `status`: VARCHAR(20) ('OPEN', 'ALLOCATED', 'FROZEN')

### API Response Schemas

**PreferenceOverviewResponse**
```typescript
{
    total_faculty: number;
    submitted_count: number;
    partial_count: number;
    not_submitted_count: number;
    records: Array<{
        staff_id: number;
        emp_code: string;
        name: string;
        total_subjects: number;
        submitted_preferences: number;
        status: 'Submitted' | 'Partial' | 'Not Submitted';
        preferences: Array<{
            subject_code: string;
            subject_name: string;
            program: string;
            semester: string;
            section: string;
            preference_rank: number;
        }>;
    }>;
}
```

**AllocationOverviewResponse**
```typescript
{
    total_faculty: number;
    overloaded_count: number;
    balanced_count: number;
    underloaded_count: number;
    records: Array<{
        staff_id: number;
        emp_code: string;
        name: string;
        total_tch: number;
        assigned_subjects_count: number;
        workload_status: 'Overloaded' | 'Balanced' | 'Underloaded';
        assigned_subjects: Array<{
            subject_code: string;
            subject_name: string;
            program: string;
            semester: string;
            section: string;
            tch: number;
        }>;
    }>;
}
```

## Error Handling

### Backend Error Scenarios

1. **No Active Cycle**: Return empty list with HTTP 200 (graceful degradation)
2. **Unauthenticated Request**: Return HTTP 401 with `{"detail": "Not authenticated"}`
3. **Unauthorized Role**: Return HTTP 403 with `{"detail": "Insufficient permissions"}`
4. **Database Connection Error**: Return HTTP 500 with `{"detail": "Internal server error"}`

### Frontend Error Handling

1. **API Failure**: Display error message with retry button using toast notification
2. **No Active Cycle**: Display informational message "No active cycle configured"
3. **Empty Data**: Display "No faculty records found" message in table
4. **Network Timeout**: Show error toast with "Request timed out. Please try again."

### Error Recovery

- **Retry Button**: Allow users to manually retry failed API calls
- **Loading States**: Show spinner during data fetching to prevent duplicate requests
- **Graceful Degradation**: Display partial data if one endpoint fails but the other succeeds

## Testing Strategy

### Unit Tests

**Backend Service Tests** (`tests/test_reports_service.py`):
1. Test `get_preference_overview()` with no active cycle → returns empty list
2. Test `get_preference_overview()` with faculty who have submitted all preferences → status = "Submitted"
3. Test `get_preference_overview()` with faculty who have submitted some preferences → status = "Partial"
4. Test `get_preference_overview()` with faculty who have submitted no preferences → status = "Not Submitted"
5. Test `get_allocation_overview()` with no active cycle → returns empty list
6. Test `get_allocation_overview()` with faculty TCH > 18 → workload_status = "Overloaded"
7. Test `get_allocation_overview()` with faculty 14 ≤ TCH ≤ 18 → workload_status = "Balanced"
8. Test `get_allocation_overview()` with faculty TCH < 14 → workload_status = "Underloaded"

**Backend Router Tests** (`tests/test_reports_router.py`):
1. Test preference-overview endpoint with coordinator role → HTTP 200
2. Test preference-overview endpoint with faculty role → HTTP 403
3. Test preference-overview endpoint without authentication → HTTP 401
4. Test allocation-overview endpoint with coordinator role → HTTP 200
5. Test allocation-overview endpoint with faculty role → HTTP 403
6. Test allocation-overview endpoint without authentication → HTTP 401

**Frontend Component Tests** (`frontend/src/pages/__tests__/PreferenceReviewDashboardPage.test.tsx`):
1. Test page renders with loading state initially
2. Test preference tab displays stats bar with correct counts
3. Test allocation tab displays stats bar with correct counts
4. Test search box filters table rows by employee code
5. Test search box filters table rows by name
6. Test clicking row expands to show subject details
7. Test clicking expanded row collapses details
8. Test status badge colors: green for "Submitted", yellow for "Partial", red for "Not Submitted"
9. Test workload badge colors: red for "Overloaded", green for "Balanced", yellow for "Underloaded"
10. Test error state displays error message and retry button

### Integration Tests

1. **End-to-End Preference Flow**:
   - Create active cycle
   - Create faculty and subject offerings
   - Submit preferences for some faculty
   - Call preference-overview endpoint
   - Verify response contains correct submission status

2. **End-to-End Allocation Flow**:
   - Create active cycle
   - Create faculty and subject offerings
   - Run allocation
   - Call allocation-overview endpoint
   - Verify response contains correct workload status

3. **Active Cycle Context**:
   - Create multiple cycles with different statuses
   - Verify only OPEN cycle data is included in responses
   - Deactivate all cycles
   - Verify endpoints return empty lists

### Manual Testing Checklist

- [ ] Coordinator can access `/admin/preference-review` page
- [ ] Faculty cannot access `/admin/preference-review` page (redirected)
- [ ] Navigation item appears between "Allocation" and "Review"
- [ ] Navigation item shows active styling when on preference review page
- [ ] Active cycle year and semester display at top of page
- [ ] Preference tab loads and displays stats bar
- [ ] Allocation tab loads and displays stats bar
- [ ] Search box filters preference table by employee code
- [ ] Search box filters preference table by name
- [ ] Search box filters allocation table by employee code
- [ ] Search box filters allocation table by name
- [ ] Clicking preference row expands to show subject list with ranks
- [ ] Clicking allocation row expands to show assigned subjects with TCH
- [ ] Status badges display correct colors
- [ ] Workload badges display correct colors
- [ ] Error message displays when API call fails
- [ ] Retry button successfully refetches data
- [ ] Page displays "No active cycle" message when no cycle is active

