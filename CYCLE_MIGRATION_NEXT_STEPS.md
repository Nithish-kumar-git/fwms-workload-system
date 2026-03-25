# Cycle Architecture Migration - Next Steps

## ✅ COMPLETED

1. **Database Migration** (Migration 021)
   - Created `academic_year` table
   - Created new `cycle` table (semester-specific)
   - Migrated all data from old `academic_cycle` table
   - Updated `subject_offering`, `faculty_preference`, `allocation` tables
   - Removed `semester_type` column from `subject_offering`
   - Renamed old `academic_cycle` to `academic_cycle_old_backup`

2. **Auth & Config Fixes**
   - Created `frontend/.env` with local dev settings
   - Updated API client baseURL logic
   - Verified Dockerfile PORT syntax
   - Verified AuthContext loading state
   - Verified App.tsx route guards

3. **New Service Layer**
   - Created `app/admin/cycle_service_new.py` with semester-specific logic

## 🔄 IN PROGRESS - Backend API Updates

### Files That Need Updates:

1. **app/admin/cycle_router.py**
   - Update schemas to use `semester_id` instead of `semester_type`
   - Update CreateCycleRequest: `semester_id: int` (not `semester_type: str`)
   - Update CycleResponse to include `semester: str` field
   - Import and use `cycle_service_new` functions

2. **app/admin/cycle_service.py**
   - Replace with `cycle_service_new.py` or update existing

3. **app/preference/router.py**
   - Update to filter by active cycle's semester
   - Remove any `semester_type` references

4. **app/preference/service.py**
   - Update preference submission logic
   - Filter subject offerings by cycle's semester

5. **app/allocation/service.py**
   - Update allocation logic to work with cycle's semester
   - Remove `semester_type` filtering

6. **app/reports/service.py**
   - Update report generation to use cycle's semester
   - Remove `semester_type` parameters

7. **app/coordinator/window_router.py**
   - Update window opening logic
   - Link window to specific cycle (not ODD/EVEN)

## 🎨 Frontend Updates Needed

1. **frontend/src/pages/CyclesPage.tsx**
   - Update form to select semester (I-VI) instead of ODD/EVEN
   - Update display to show "Semester II" instead of "EVEN"
   - Update API calls to send `semester_id`

2. **frontend/src/pages/PreferencesPage.tsx**
   - Verify it filters by active cycle correctly
   - Should only show subjects for cycle's semester

3. **frontend/src/pages/AllocationPage.tsx**
   - Update to work with semester-specific cycles
   - Remove ODD/EVEN references

4. **frontend/src/pages/WindowPage.tsx**
   - Update window opening to select specific semester
   - Remove ODD/EVEN dropdown

## 🧪 Testing Checklist

- [ ] Create cycle for "2025-2026 Semester II"
- [ ] Verify only Semester II subjects appear
- [ ] Submit preferences for Semester II subjects
- [ ] Verify preferences don't show in Semester IV cycle
- [ ] Run allocation for Semester II
- [ ] Verify reports show correct semester
- [ ] Create cycle for "2025-2026 Semester IV"
- [ ] Verify both cycles can coexist
- [ ] Verify switching between cycles works

## 📝 Implementation Order

1. Update backend cycle service and router
2. Update preference APIs
3. Update allocation APIs
4. Update frontend CyclesPage
5. Update frontend PreferencesPage
6. Test end-to-end workflow
7. Update reports
8. Final validation

## ⚠️ Breaking Changes

- API contracts changed: `semester_type` → `semester_id`
- Frontend must be updated simultaneously with backend
- Old `academic_cycle` table is backed up but not used
- All ODD/EVEN logic removed

## 🔄 Rollback Plan

If issues arise:
1. Restore `academic_cycle_old_backup` table
2. Revert migration 021
3. Restore old service files
4. Redeploy previous version
