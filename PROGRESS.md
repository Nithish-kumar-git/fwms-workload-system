# Coordinator Preference Review Dashboard - Implementation Progress

## STEP 1: File Analysis Complete

### Files Read and Key Findings:

1. **frontend/src/App.tsx**
   - Coordinator routes use `/admin/*` prefix
   - Existing route: `/admin/review` → ReviewPage (allocation override)
   - Auth guard: `RequireCoordinator` (allows tt_coordinator OR hod roles)
   - Will add new route: `/admin/preference-review`

2. **frontend/src/api/client.ts**
   - Base URL pattern: `${VITE_API_URL}/api` or `/api`
   - JWT token in localStorage: `jwt_token`
   - Bearer token in Authorization header
   - Existing API functions follow pattern: `export const functionName = () => api.get('/endpoint')`

3. **frontend/src/pages/AllocationPage.tsx**
   - Table pattern: `<table className="data-table">` with `<thead>` and `<tbody>`
   - Glass card: `<div className="glass-card">`
   - Stats grid: `<div className="stat-grid">` with `<div className="stat-card glass-card">`
   - Badge classes: `badge badge-success`, `badge badge-warning`, `badge-danger`
   - Loading state: centered text with spinner
   - Error state: glass-card with AlertCircle icon

4. **frontend/src/pages/StaffEmailsPage.tsx**
   - Search pattern: `<Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />`
   - Modal usage: `<Modal isOpen={...} onClose={...} title="...">`
   - Toast pattern: `useToast()` hook with `addToast(message, type)`

5. **frontend/src/pages/ReviewPage.tsx**
   - Existing page for allocation override (NOT preference review)
   - Uses grouped data structure by program/semester/section
   - Table with override buttons

6. **frontend/src/components/Navbar.tsx**
   - Coordinator nav items array: `coordinatorItems`
   - Current items: Dashboard, My Preferences, Window, Cycles, Subjects, Allocation, Review, Reports
   - Will add: "Pref Review" between "Allocation" and "Review"
   - Icon imports from 'lucide-react'

### Existing API Endpoints (from client.ts):
- Preferences: `/preferences/me`, `/preferences/status`
- Allocation: `/admin/allocations`
- Staff: `/admin/staff/list`
- Reports: `/reports/faculty-workload`, `/reports/subject-summary`

### Auth/Role Check:
- Coordinator pages use `RequireCoordinator` guard
- Allows both `tt_coordinator` and `hod` roles
- JWT token required in Authorization header

## Next Steps:
- Add backend endpoints to app/reports/router.py
- Add API functions to client.ts
- Create CoordinatorReviewPage.tsx
- Add route to App.tsx
- Add nav link to Navbar.tsx
