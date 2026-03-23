# API Request Schemas - Quick Reference

## POST /api/allocation/run

### Endpoint
```
POST /api/allocation/run
```

### Authentication
**Required**: Coordinator role (Bearer token)

### Request Body Schema

```json
{
  "academic_year": "string | null (optional)",
  "semester_type": "string | null (optional)",
  "academic_cycle_id": "integer | null (optional)",
  "program_id": "integer | null (optional)",
  "semester_id": "integer | null (REQUIRED)"
}
```

### Required Fields
- **semester_id**: `integer` (REQUIRED) - The ID of the semester to allocate

### Optional Fields
- **academic_year**: `string | null` - Academic year (e.g., "2025-2026") - Not used, resolved from active cycle
- **semester_type**: `string | null` - Semester type (e.g., "EVEN", "ODD") - Not used, resolved from active cycle
- **academic_cycle_id**: `integer | null` - Academic cycle ID - Not used, resolved from active cycle
- **program_id**: `integer | null` - Filter by specific program (rarely used)

### Sample Valid Request

**Minimal (Recommended)**:
```json
{
  "semester_id": 1
}
```

**With All Fields** (not necessary):
```json
{
  "academic_year": "2025-2026",
  "semester_type": "EVEN",
  "academic_cycle_id": 1,
  "program_id": null,
  "semester_id": 1
}
```

### cURL Example
```bash
curl -X POST https://your-domain.com/api/allocation/run \
  -H "Authorization: Bearer <coordinator-token>" \
  -H "Content-Type: application/json" \
  -d '{"semester_id": 1}'
```

### Response Schema (Success)
```json
{
  "success": true,
  "message": "Allocation complete for Semester I: 364 assigned, 147 unassigned",
  "semester_id": 1,
  "semester_label": "I",
  "subjects_total": 511,
  "subjects_assigned": 364,
  "subjects_unassigned": 147,
  "faculty_overloaded": 45,
  "faculty_underloaded": 12,
  "faculty_balanced": 23,
  "allocations": [
    {
      "staff_id": 1,
      "staff_name": "Dr. John Doe",
      "emp_code": "EMP001",
      "subject_offering_id": 100,
      "subject_code": "CS101",
      "subject_name": "Introduction to Programming",
      "section_label": "A",
      "semester_label": "I",
      "program_name": "Computer Science",
      "l_assigned": 3,
      "t_assigned": 1,
      "p_assigned": 2,
      "tch": 6,
      "preference_number": 1,
      "allocation_stage": "PREF_1"
    }
    // ... more allocations
  ],
  "unallocated": [
    {
      "subject_offering_id": 200,
      "subject_code": "CS201",
      "subject_name": "Data Structures",
      "section_label": "B",
      "semester_label": "I",
      "program_name": "Computer Science",
      "tch": 6,
      "reason": "No compatible faculty with available capacity (even with 20% overload)"
    }
    // ... more unallocated
  ],
  "workload_summary": [
    {
      "staff_id": 1,
      "emp_code": "EMP001",
      "name": "Dr. John Doe",
      "designation": "Professor",
      "tch_norm": 40,
      "tch_assigned": 48,
      "deviation": 8,
      "status": "OVERLOADED"
    }
    // ... more faculty
  ]
}
```

### Error Responses

**Missing semester_id**:
```json
{
  "success": false,
  "message": "semester_id is required for allocation. Please specify which semester to allocate."
}
```

**Wrong state**:
```json
{
  "success": false,
  "message": "Cannot run allocation: Semester must be CLOSED (currently OPEN)"
}
```

**Frozen semester**:
```json
{
  "success": false,
  "message": "Cannot run allocation: Semester is FROZEN (finalized by HOD). No modifications allowed."
}
```

---

## POST /api/preferences

### Endpoint
```
POST /api/preferences
```

### Authentication
**Required**: Faculty role (Bearer token)

### Request Body Schema

```json
{
  "subject_offering_id": "integer (REQUIRED)",
  "preference_number": "integer (REQUIRED, 1-5)"
}
```

### Required Fields
- **subject_offering_id**: `integer` (REQUIRED) - The ID of the subject offering to prefer
- **preference_number**: `integer` (REQUIRED) - Preference rank, must be between 1 and 5 (inclusive)

### Field Constraints
- **preference_number**: 
  - Minimum: 1
  - Maximum: 5
  - Must be unique per faculty (cannot reuse same number)
  - Must be unique per subject offering (two faculty cannot use same number for same subject)

### Sample Valid Requests

**Preference 1** (highest priority):
```json
{
  "subject_offering_id": 100,
  "preference_number": 1
}
```

**Preference 2**:
```json
{
  "subject_offering_id": 105,
  "preference_number": 2
}
```

**Preference 5** (lowest priority):
```json
{
  "subject_offering_id": 150,
  "preference_number": 5
}
```

### cURL Example
```bash
curl -X POST https://your-domain.com/api/preferences \
  -H "Authorization: Bearer <faculty-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_offering_id": 100,
    "preference_number": 1
  }'
```

### Response Schema (Success)
```json
{
  "success": true,
  "message": "Preference 1 submitted successfully",
  "preference_id": 42
}
```

### Error Responses

**Invalid preference number** (HTTP 409):
```json
{
  "detail": "Preference number must be between 1 and 5"
}
```

**Preference number already used** (HTTP 409):
```json
{
  "detail": "You have already used preference number 1"
}
```

**Another faculty already used this number** (HTTP 409):
```json
{
  "detail": "Another faculty has already assigned preference 1 to this subject"
}
```

**Duplicate subject** (HTTP 409):
```json
{
  "detail": "You have already submitted a preference for this subject offering"
}
```

**Shift incompatibility** (HTTP 403):
```json
{
  "detail": "SHIFT2 faculty cannot select SHIFT1 subjects"
}
```

**Class teacher violation** (HTTP 403):
```json
{
  "detail": "Class teacher must give preference 1 to their own class. Mismatch: program (CSE vs ECE)"
}
```

**Wrong semester state** (HTTP 400):
```json
{
  "detail": "Preferences can ONLY be submitted when semester is OPEN (currently CLOSED)"
}
```

**Maximum preferences reached** (HTTP 409):
```json
{
  "detail": "Maximum 5 preferences already submitted"
}
```

**Subject offering not found** (HTTP 404):
```json
{
  "detail": "Subject offering not found or inactive"
}
```

---

## Validation Rules Summary

### POST /api/allocation/run
1. **semester_id** is REQUIRED
2. Semester must be in **CLOSED** state
3. Semester cannot be **FROZEN**
4. Semester cannot be **ALLOCATED** (must reopen first)
5. Must have coordinator role

### POST /api/preferences
1. **PREF-01**: preference_number must be 1-5
2. **PREF-02**: No two faculty can use same preference_number for same subject
3. **PREF-03**: Faculty cannot reuse same preference_number
4. **PREF-DUP**: Faculty cannot submit multiple preferences for same subject
5. **SHIFT-01**: Faculty shift must match subject shift
6. **CT-01**: Class teacher preference 1 must match their assigned class
7. **STATE**: Semester must be in **OPEN** state
8. **MAX**: Maximum 5 preferences per faculty

---

## Quick Comparison

| Aspect | POST /api/allocation/run | POST /api/preferences |
|--------|-------------------------|----------------------|
| **Auth** | Coordinator | Faculty |
| **Required Fields** | `semester_id` | `subject_offering_id`, `preference_number` |
| **State Required** | CLOSED | OPEN |
| **Idempotent** | Yes (clears old allocations) | No (creates new preference) |
| **Body Can Be Empty** | Yes (defaults to null) | No (fields required) |
| **Typical Response Time** | 2-5 seconds | < 100ms |

---

## Testing Examples

### Test Allocation
```bash
# 1. Open semester
curl -X POST https://your-domain.com/api/semester/1/open \
  -H "Authorization: Bearer <coordinator-token>"

# 2. Submit preferences (as faculty)
curl -X POST https://your-domain.com/api/preferences \
  -H "Authorization: Bearer <faculty-token>" \
  -H "Content-Type: application/json" \
  -d '{"subject_offering_id": 100, "preference_number": 1}'

# 3. Close semester
curl -X POST https://your-domain.com/api/semester/1/close \
  -H "Authorization: Bearer <coordinator-token>"

# 4. Run allocation
curl -X POST https://your-domain.com/api/allocation/run \
  -H "Authorization: Bearer <coordinator-token>" \
  -H "Content-Type: application/json" \
  -d '{"semester_id": 1}'
```

### Test Preference Validation
```bash
# Submit preference 1
curl -X POST https://your-domain.com/api/preferences \
  -H "Authorization: Bearer <faculty-token>" \
  -H "Content-Type: application/json" \
  -d '{"subject_offering_id": 100, "preference_number": 1}'

# Try to reuse preference 1 (should fail)
curl -X POST https://your-domain.com/api/preferences \
  -H "Authorization: Bearer <faculty-token>" \
  -H "Content-Type: application/json" \
  -d '{"subject_offering_id": 105, "preference_number": 1}'
# Expected: HTTP 409 "You have already used preference number 1"
```

---

**END OF API REQUEST SCHEMAS**

