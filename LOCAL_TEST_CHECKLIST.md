# Local Testing Checklist - Faculty Subject Allocation System

## Pre-Flight Status ✅

### Seed Data Verification
- ✅ **Academic Cycle**: 2025-2026 EVEN (migration 010)
- ✅ **Faculty**: 28 staff members (migrations 004, 007)
- ✅ **Programs**: MCA (PG), BCA (UG) (migration 006)
- ✅ **Subjects**: 100+ subjects with curriculum data (migration 006)
- ✅ **Subject Offerings**: MCA + BCA offerings for 2025-2026 EVEN (migration 006)

### Code Quality Checks
- ✅ **No hardcoded URLs**: All API calls use relative paths via `/api`
- ✅ **Proper async/await**: All async operations properly handled
- ✅ **Token handling**: JWT stored in localStorage, Bearer token in headers
- ✅ **Error handling**: All API calls have try/catch or .catch() handlers

---

## Startup Commands

### 1. Start the Full Stack

```bash
docker-compose up --build
```

This will:
- Build and start PostgreSQL database
- Run all 17 migrations in sequence (including seed data)
- Start FastAPI backend on port 8000
- Start Vite frontend dev server on port 5173

### 2. Verify Services

```bash
# Check all containers are running
docker-compose ps

# Check backend logs
docker-compose logs backend

# Check database logs
docker-compose logs db
```

### 3. Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Environment Variables Status

Your `.env` file is configured for local development:

✅ **Required variables present**:
- `DATABASE_URL` - PostgreSQL connection
- `SECRET_KEY` - JWT signing (32+ chars)
- `GOOGLE_CLIENT_ID` - OAuth (placeholder)
- `GOOGLE_CLIENT_SECRET` - OAuth (placeholder)
- `GOOGLE_REDIRECT_URI` - OAuth callback
- `DEV_AUTH_BYPASS=true` - Development mode enabled

⚠️ **OAuth Note**: Google OAuth credentials are placeholders. With `DEV_AUTH_BYPASS=true`, you can test without real OAuth.

---

## Manual Test Script

### Phase 1: Authentication & User Roles (5 min)

#### Test 1.1: HOD Login (DEV_AUTH_BYPASS)
- [ ] Navigate to http://localhost:5173
- [ ] Click "Login with Google"
- [ ] Verify redirect to dashboard
- [ ] Check navbar shows user name and role
- [ ] Verify HOD-specific menu items visible (Cycles, Windows, Staff, Final Approval)

**Expected**: HOD user (Dr. S. Gokila, MCT44) logged in with full access

#### Test 1.2: Faculty Login
- [ ] Logout from HOD account
- [ ] Login as faculty member
- [ ] Verify faculty dashboard shows preferences section
- [ ] Verify limited menu (only Preferences, Dashboard)

**Expected**: Faculty user sees restricted view

#### Test 1.3: Coordinator Login
- [ ] Logout and login as coordinator
- [ ] Verify coordinator menu items (Allocation, Review, Reports)
- [ ] Verify no access to HOD-only features

**Expected**: Coordinator has allocation management access

---

### Phase 2: Academic Cycle Management (3 min)

#### Test 2.1: View Active Cycle
- [ ] Login as HOD
- [ ] Navigate to "Cycles" page
- [ ] Verify 2025-2026 EVEN cycle exists and is marked ACTIVE
- [ ] Check cycle details (start/end dates if present)

**Expected**: Active cycle displayed with green indicator

#### Test 2.2: Create New Cycle
- [ ] Click "Create New Cycle"
- [ ] Enter academic year: 2025-2026
- [ ] Select semester type: ODD
- [ ] Submit form
- [ ] Verify new cycle appears in list

**Expected**: New cycle created successfully

#### Test 2.3: Activate Different Cycle
- [ ] Click "Activate" on the newly created cycle
- [ ] Verify confirmation message
- [ ] Check that new cycle is now marked ACTIVE
- [ ] Verify previous cycle is no longer active

**Expected**: Only one cycle active at a time

---

### Phase 3: Staff Management (5 min)

#### Test 3.1: View Staff List
- [ ] Navigate to "Staff" page
- [ ] Verify 28 staff members displayed
- [ ] Check columns: Name, Email, Emp Code, Designation, Shift, TCH Norm
- [ ] Verify HOD (Dr. S. Gokila) visible in list

**Expected**: Complete staff roster displayed

#### Test 3.2: Create New Staff
- [ ] Click "Add Staff"
- [ ] Fill form:
  - Name: Test Faculty
  - Email: test.faculty@hindustanuniv.ac.in
  - Emp Code: TEST01
  - Designation: Assistant Professor
  - Shift: SHIFT1
  - TCH Norm: 40
- [ ] Submit form
- [ ] Verify new staff appears in list

**Expected**: New staff member created

#### Test 3.3: Update Staff Details
- [ ] Click "Edit" on Test Faculty
- [ ] Change designation to "Associate Professor"
- [ ] Change TCH Norm to 36
- [ ] Save changes
- [ ] Verify updates reflected in list

**Expected**: Staff details updated successfully

#### Test 3.4: Deactivate Staff
- [ ] Click "Deactivate" on Test Faculty
- [ ] Confirm deactivation
- [ ] Verify staff marked as inactive or removed from active list

**Expected**: Staff deactivated successfully

---

### Phase 4: Preference Window Management (5 min)

#### Test 4.1: Open Preference Window
- [ ] Navigate to "Windows" page
- [ ] Verify current status shows "CLOSED"
- [ ] Click "Open Window"
- [ ] Select academic year: 2025-2026
- [ ] Select semester type: EVEN
- [ ] Set start time: Current date/time
- [ ] Set end time: 7 days from now
- [ ] Submit form
- [ ] Verify window status changes to "OPEN"

**Expected**: Preference window opened for 2025-2026 EVEN

#### Test 4.2: Verify Window Visibility for Faculty
- [ ] Logout and login as faculty
- [ ] Navigate to "Preferences" page
- [ ] Verify banner shows "Window is OPEN"
- [ ] Verify subject offerings are visible
- [ ] Check that preference submission is enabled

**Expected**: Faculty can see open window and available subjects

#### Test 4.3: Close Preference Window
- [ ] Logout and login as HOD
- [ ] Navigate to "Windows" page
- [ ] Click "Close Window"
- [ ] Confirm closure
- [ ] Verify status changes to "CLOSED"

**Expected**: Window closed successfully

---

### Phase 5: Faculty Preference Submission (10 min)

#### Test 5.1: View Available Subjects
- [ ] Login as faculty (e.g., MCT48 - Dr. Sathish Kumar M)
- [ ] Navigate to "Preferences" page
- [ ] Verify subject offerings displayed with:
  - Subject code and name
  - Program, semester, section
  - Credits and TCH
- [ ] Verify offerings filtered by faculty eligibility

**Expected**: Only eligible subjects shown

#### Test 5.2: Submit First Preference
- [ ] Select a subject offering from dropdown
- [ ] Enter preference number: 1
- [ ] Click "Submit Preference"
- [ ] Verify success message
- [ ] Check preference appears in "My Preferences" table

**Expected**: Preference #1 submitted successfully

#### Test 5.3: Submit Multiple Preferences
- [ ] Submit preference #2 for different subject
- [ ] Submit preference #3 for another subject
- [ ] Verify all 3 preferences visible in table
- [ ] Check preferences sorted by preference number

**Expected**: Multiple preferences tracked correctly

#### Test 5.4: Duplicate Preference Validation
- [ ] Try to submit preference #1 again (same number)
- [ ] Verify error message: "Preference number already used"
- [ ] Try to submit same subject with different number
- [ ] Verify error message: "Subject already selected"

**Expected**: Duplicate prevention working

#### Test 5.5: Delete Preference
- [ ] Click "Delete" on preference #2
- [ ] Verify confirmation or immediate deletion
- [ ] Check preference removed from table
- [ ] Verify preference #2 slot now available

**Expected**: Preference deleted successfully

#### Test 5.6: Window Closed Behavior
- [ ] Login as HOD and close preference window
- [ ] Logout and login as faculty
- [ ] Navigate to Preferences page
- [ ] Verify banner shows "Window is CLOSED"
- [ ] Verify preference submission disabled
- [ ] Check existing preferences still visible (read-only)

**Expected**: Faculty cannot submit when window closed

---

### Phase 6: Allocation Execution (5 min)

#### Test 6.1: Run Allocation Algorithm
- [ ] Login as coordinator
- [ ] Navigate to "Allocation" page
- [ ] Verify active cycle displayed (2025-2026 EVEN)
- [ ] Click "Run Allocation"
- [ ] Wait for processing (may take 10-30 seconds)
- [ ] Verify success message with allocation count

**Expected**: Allocation completes with results

#### Test 6.2: View Allocation Results
- [ ] Check allocation results table shows:
  - Subject code and name
  - Assigned faculty name
  - Program, semester, section
  - Match type (preference-based or fallback)
- [ ] Verify at least some allocations are preference-based
- [ ] Check for any unallocated subjects

**Expected**: Allocations displayed with match types

#### Test 6.3: Re-run Allocation
- [ ] Click "Run Allocation" again
- [ ] Verify system handles re-run gracefully
- [ ] Check if results change or remain stable

**Expected**: Re-run works without errors

---

### Phase 7: Allocation Review & Override (10 min)

#### Test 7.1: View Allocations as Coordinator
- [ ] Navigate to "Review" page
- [ ] Verify all allocations displayed in table
- [ ] Check columns: Subject, Current Faculty, Program, Semester, Section
- [ ] Verify freeze status indicator

**Expected**: Complete allocation list visible

#### Test 7.2: Override Single Allocation
- [ ] Click "Override" on any allocation
- [ ] Select different faculty from dropdown
- [ ] Confirm override
- [ ] Verify success message
- [ ] Check allocation updated with new faculty

**Expected**: Manual override successful

#### Test 7.3: Freeze Allocations
- [ ] Click "Freeze Allocations" button
- [ ] Confirm freeze action
- [ ] Verify success message
- [ ] Check freeze indicator changes to "FROZEN"
- [ ] Verify override buttons disabled

**Expected**: Allocations frozen, no further edits allowed

#### Test 7.4: Unfreeze Allocations
- [ ] Click "Unfreeze Allocations" button
- [ ] Confirm unfreeze action
- [ ] Verify success message
- [ ] Check freeze indicator changes to "UNFROZEN"
- [ ] Verify override buttons re-enabled

**Expected**: Allocations unfrozen, edits allowed again

---

### Phase 8: Workload Reports (5 min)

#### Test 8.1: View Faculty Workload
- [ ] Navigate to "Reports" page
- [ ] Verify faculty workload table displays:
  - Faculty name and emp code
  - Total TCH assigned
  - TCH norm
  - Workload percentage
  - Subject count
- [ ] Check workload calculations are correct
- [ ] Verify color coding (red for overload, green for balanced)

**Expected**: Workload summary accurate

#### Test 8.2: Download Excel Report
- [ ] Click "Download Excel" button
- [ ] Verify file downloads (workload_YYYY-MM-DD.xlsx)
- [ ] Open Excel file
- [ ] Check data matches web display
- [ ] Verify formatting and headers

**Expected**: Excel export works correctly

#### Test 8.3: Download PDF Report
- [ ] Click "Download PDF" button
- [ ] Verify file downloads (workload_YYYY-MM-DD.pdf)
- [ ] Open PDF file
- [ ] Check data matches web display
- [ ] Verify formatting and readability

**Expected**: PDF export works correctly

---

### Phase 9: HOD Final Approval (5 min)

#### Test 9.1: View Pipeline Status
- [ ] Login as HOD
- [ ] Navigate to "Final Approval" page
- [ ] Verify pipeline status shows:
  - Preference window status
  - Allocation status
  - Freeze status
  - Approval status
- [ ] Check all prerequisite steps completed

**Expected**: Pipeline status accurate

#### Test 9.2: Approve Workload
- [ ] Click "Approve Workload" button
- [ ] Confirm approval action
- [ ] Verify success message
- [ ] Check approval status changes to "APPROVED"
- [ ] Verify approval timestamp displayed

**Expected**: Workload approved and locked

#### Test 9.3: Download Master Workload
- [ ] Click "Download Master Workload (Excel)"
- [ ] Verify file downloads with cycle prefix (2025-2026_EVEN_master_workload.xlsx)
- [ ] Open Excel file
- [ ] Verify comprehensive workload data
- [ ] Check all faculty and subjects included

**Expected**: Master workload export successful

#### Test 9.4: Verify Approval Immutability
- [ ] Navigate to "Review" page
- [ ] Verify allocations are frozen
- [ ] Try to override an allocation
- [ ] Verify operation blocked or warning shown

**Expected**: Approved workload cannot be modified

---

### Phase 10: State Transition Validation (5 min)

#### Test 10.1: Invalid State Transitions
- [ ] Try to open preference window while allocations frozen
- [ ] Verify error message or prevention
- [ ] Try to run allocation while window still open
- [ ] Verify error message or prevention

**Expected**: Invalid transitions blocked

#### Test 10.2: Valid State Flow
- [ ] Create new cycle (2026-2027 ODD)
- [ ] Activate new cycle
- [ ] Open preference window for new cycle
- [ ] Submit preferences as faculty
- [ ] Close window
- [ ] Run allocation
- [ ] Freeze allocations
- [ ] Approve workload

**Expected**: Complete workflow executes smoothly

---

### Phase 11: Multi-User Concurrent Testing (5 min)

#### Test 11.1: Multiple Faculty Preferences
- [ ] Open 2-3 browser windows/tabs
- [ ] Login as different faculty in each
- [ ] Submit preferences simultaneously
- [ ] Verify no conflicts or errors
- [ ] Check all preferences saved correctly

**Expected**: Concurrent submissions handled

#### Test 11.2: Coordinator + Faculty Interaction
- [ ] Faculty submits preferences (window open)
- [ ] Coordinator runs allocation immediately after
- [ ] Verify allocation includes latest preferences
- [ ] Check no race conditions

**Expected**: Real-time data consistency

---

### Phase 12: Error Handling & Edge Cases (5 min)

#### Test 12.1: Network Error Simulation
- [ ] Stop backend container: `docker-compose stop backend`
- [ ] Try to submit preference in frontend
- [ ] Verify error message displayed
- [ ] Check no silent failures
- [ ] Restart backend: `docker-compose start backend`

**Expected**: Graceful error handling

#### Test 12.2: Invalid Data Submission
- [ ] Try to submit preference with invalid offering ID
- [ ] Try to create cycle with past dates
- [ ] Try to activate non-existent cycle
- [ ] Verify all show appropriate error messages

**Expected**: Validation errors caught and displayed

#### Test 12.3: Database Constraint Violations
- [ ] Try to create duplicate cycle (same year + semester)
- [ ] Try to submit duplicate preference number
- [ ] Verify database constraints enforced
- [ ] Check error messages are user-friendly

**Expected**: Constraints prevent invalid data

---

## Test Data Reference

### Test Users (with DEV_AUTH_BYPASS=true)

**HOD**:
- Dr. S. Gokila (MCT44) - `mct44@faculty.local`

**Coordinators**:
- Dr. S. Gokila (MCT44) - also coordinator

**Faculty** (sample):
- Dr. Sathish Kumar M (MCT48) - `mct48@faculty.local`
- Dr. Angelina Benita D (MCT49) - `mct49@faculty.local`
- Mrs. Vinitha Sushila Devi S (MCT54) - `mct54@faculty.local`

### Test Cycle
- Academic Year: 2025-2026
- Semester Type: EVEN
- Status: ACTIVE

---

## Success Criteria

✅ **All 12 phases pass without critical errors**
✅ **State transitions follow defined workflow**
✅ **Data persistence verified across restarts**
✅ **Multi-user scenarios work correctly**
✅ **Error handling is graceful and informative**
✅ **Reports generate accurate data**
✅ **Approval workflow enforces immutability**

---

## Troubleshooting

### Backend won't start
- Check `.env` file has all required variables
- Verify `SECRET_KEY` is 32+ characters
- Check PostgreSQL container is running: `docker-compose ps`

### Frontend can't connect to backend
- Verify backend is running on port 8000
- Check CORS settings in `app/main.py`
- Verify Vite proxy configuration in `frontend/vite.config.ts`

### Database migrations fail
- Check migration sequence in `docker-compose.yml`
- Verify no duplicate migration numbers
- Check PostgreSQL logs: `docker-compose logs db`

### OAuth not working
- With `DEV_AUTH_BYPASS=true`, OAuth is bypassed
- For real OAuth, configure valid Google credentials in `.env`
- Update `GOOGLE_REDIRECT_URI` to match your domain

---

## Post-Test Actions

After successful testing:
1. Review any errors or warnings in logs
2. Document any unexpected behavior
3. Verify all data persists after container restart
4. Check database state: `docker-compose exec db psql -U postgres -d faculty_allocation`
5. Run production readiness checklist if deploying

---

**Estimated Total Test Time**: 60-70 minutes
**Last Updated**: 2026-03-21
