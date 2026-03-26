# File Contents and API Test Results

## 1. frontend/src/pages/ReviewPage.tsx

```typescript
import { useEffect, useState } from 'react';
import { getAdminAllocations, overrideAllocation, freezeAllocation, unfreezeAllocation } from '../api/client';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import Modal from '../components/Modal';
import { Lock, Unlock, RefreshCw, AlertCircle } from 'lucide-react';

interface Allocation {
    allocation_id: number;
    staff_id: number;
    staff_name: string;
    emp_code: string;
    designation: string;
    subject_offering_id: number;
    subject_code: string;
    subject_name: string;
    section_label: string;
    semester_label: string;
    program_name: string;
    l_assigned: number;
    t_assigned: number;
    p_assigned: number;
    ltp_total: number;
}

type GroupedAllocations = Record<string, Record<string, Record<string, Allocation[]>>>;

function groupAllocations(allocs: Allocation[]): GroupedAllocations {
    const groups: GroupedAllocations = {};
    for (const a of allocs) {
        const prog = a.program_name || 'Unknown';
        const sem = a.semester_label || 'Unknown';
        const sec = a.section_label || 'Unknown';
        if (!groups[prog]) groups[prog] = {};
        if (!groups[prog][sem]) groups[prog][sem] = {};
        if (!groups[prog][sem][sec]) groups[prog][sem][sec] = [];
        groups[prog][sem][sec].push(a);
    }
    return groups;
}

export default function ReviewPage() {
    const [allocations, setAllocations] = useState<Allocation[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selected, setSelected] = useState<Allocation | null>(null);
    const [newStaffId, setNewStaffId] = useState('');
    const [overriding, setOverriding] = useState(false);
    const { toasts, addToast, removeToast } = useToast();

    const loadData = async () => {
        setLoading(true);
        setError('');
        try {
            const res = await getAdminAllocations();
            setAllocations(res.data.allocations || []);
        } catch (err: any) {
            const detail = err.response?.data?.detail || 'Failed to load allocations';
            setError(detail);
            addToast(detail, 'error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadData(); }, []);

    const handleOverride = async () => {
        if (!selected || !newStaffId) return;
        setOverriding(true);
        try {
            await overrideAllocation(selected.allocation_id, parseInt(newStaffId));
            addToast('Allocation overridden successfully', 'success');
            setSelected(null);
            setNewStaffId('');
            loadData();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Override failed', 'error');
        } finally {
            setOverriding(false);
        }
    };

    const handleFreeze = async () => {
        try {
            await freezeAllocation();
            addToast('Allocation frozen', 'success');
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Freeze failed', 'error');
        }
    };

    const handleUnfreeze = async () => {
        try {
            await unfreezeAllocation();
            addToast('Allocation unfrozen', 'success');
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Unfreeze failed', 'error');
        }
    };

    if (loading) return (
        <div className="page-container">
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '3rem' }}>Loading allocations...</p>
        </div>
    );

    if (error) return (
        <div className="page-container">
            <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                <AlertCircle size={32} style={{ color: '#dc2626', marginBottom: '0.75rem' }} />
                <p style={{ color: '#dc2626', fontWeight: 600, marginBottom: '0.5rem' }}>{error}</p>
                <button onClick={loadData} className="btn btn-primary" style={{ marginTop: '0.5rem' }}>
                    <RefreshCw size={16} /> Retry
                </button>
            </div>
        </div>
    );

    const grouped = groupAllocations(allocations);
    const programs = Object.keys(grouped).sort();

    return (
        <div className="page-container">
            <ToastContainer toasts={toasts} onRemove={removeToast} />

            <div className="page-header">
                <div>
                    <h1 className="page-title">Allocation Review</h1>
                    <p className="page-subtitle">
                        {allocations.length} allocations across {programs.length} program{programs.length !== 1 ? 's' : ''}
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button onClick={loadData} className="btn btn-outline"><RefreshCw size={16} />Refresh</button>
                    <button onClick={handleFreeze} className="btn btn-danger"><Lock size={16} />Freeze</button>
                    <button onClick={handleUnfreeze} className="btn btn-success"><Unlock size={16} />Unfreeze</button>
                </div>
            </div>

            {allocations.length === 0 ? (
                <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                    <p style={{ color: '#6b7280' }}>No allocations found. Run the allocation engine first.</p>
                </div>
            ) : (
                programs.map((prog) => {
                    const semesters = Object.keys(grouped[prog]).sort();
                    return (
                        <div key={prog} className="mb-8">
                            <h2 className="text-lg font-semibold mb-4 text-blue-600 pl-1">
                                {prog}
                            </h2>
                            {semesters.map((sem) => {
                                const sections = Object.keys(grouped[prog][sem]).sort();
                                return sections.map((sec) => {
                                    const allocs = grouped[prog][sem][sec];
                                    return (
                                        <div key={`${prog}-${sem}-${sec}`} className="glass-card" style={{ overflow: 'hidden', marginBottom: '1.5rem' }}>
                                            <div style={{ padding: '0.75rem 1.25rem', borderBottom: '1px solid #e5e7eb', background: '#f9fafb', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                                                <span className="badge badge-info">{sem}</span>
                                                <span className="badge badge-warning">{sec}</span>
                                                <span style={{ color: '#6b7280', fontSize: '0.8125rem', fontWeight: 500, marginLeft: 'auto' }}>
                                                    {allocs.length} subject{allocs.length !== 1 ? 's' : ''}
                                                </span>
                                            </div>
                                            <div className="overflow-x-auto">
                                                <table className="data-table">
                                                    <thead>
                                                        <tr>
                                                            <th>Faculty</th><th>Emp Code</th><th>Subject</th>
                                                            <th>L</th><th>T</th><th>P</th><th>LTP</th><th>Action</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {allocs.map((a) => (
                                                            <tr key={a.allocation_id}>
                                                                <td style={{ fontWeight: 500, color: '#111827' }}>{a.staff_name}</td>
                                                                <td style={{ fontFamily: 'monospace', color: '#6b7280', fontSize: '0.8125rem' }}>{a.emp_code}</td>
                                                                <td style={{ color: '#374151' }}>{a.subject_code} <span style={{ color: '#d1d5db', margin: '0 0.25rem' }}>—</span> {a.subject_name}</td>
                                                                <td style={{ color: '#6b7280' }}>{a.l_assigned}</td>
                                                                <td style={{ color: '#6b7280' }}>{a.t_assigned}</td>
                                                                <td style={{ color: '#6b7280' }}>{a.p_assigned}</td>
                                                                <td style={{ fontWeight: 600, color: '#2563eb' }}>{a.ltp_total}</td>
                                                                <td>
                                                                    <button onClick={() => setSelected(a)} className="btn btn-outline text-[13px] py-1 px-3">
                                                                        Override
                                                                    </button>
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    );
                                });
                            })}
                        </div>
                    );
                })
            )}

            {/* Override Modal */}
            <Modal isOpen={!!selected} onClose={() => setSelected(null)} title="Override Allocation">
                {selected && (
                    <div>
                        <p style={{ color: '#6b7280', fontSize: '0.875rem', marginBottom: '1rem' }}>
                            Reassign <strong>{selected.subject_code}</strong> from <strong>{selected.staff_name}</strong> to:
                        </p>
                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                                New Staff ID
                            </label>
                            <input
                                type="number" className="form-input" value={newStaffId}
                                onChange={(e) => setNewStaffId(e.target.value)}
                                placeholder="Enter staff ID" style={{ width: '100%' }}
                            />
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                            <button onClick={() => setSelected(null)} className="btn btn-outline">Cancel</button>
                            <button onClick={handleOverride} className="btn btn-primary" disabled={overriding || !newStaffId}>
                                {overriding ? 'Overriding...' : 'Confirm Override'}
                            </button>
                        </div>
                    </div>
                )}
            </Modal>
        </div>
    );
}
```

---

## 2. app/admin/router.py

```python
"""
FastAPI router for admin / coordinator endpoints.
Spec reference: final_system_specification.md (Admin Override System)

All endpoints require coordinator authentication.

Endpoints:
  GET    /api/admin/allocations          Review all allocations
  PUT    /api/admin/allocation/{id}      Override allocation (reassign staff)
  POST   /api/admin/reassign             Move subject between faculty
  POST   /api/admin/allocation/freeze    Lock allocations
  POST   /api/admin/allocation/unfreeze  Unlock allocations (emergency)
  GET    /api/admin/workload-summary     Faculty workload report
"""

from fastapi import APIRouter, Depends, HTTPException
import logging

from app.auth.dependencies import get_current_coordinator_id
from app.admin.schemas import (
    AllocationReviewResponse, AllocationDetail,
    OverrideRequest, OverrideResponse,
    ReassignRequest, ReassignResponse,
    FreezeResponse,
    WorkloadSummaryResponse, WorkloadSummaryRecord,
)
from app.admin import service as admin_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/allocations", response_model=AllocationReviewResponse)
async def list_allocations(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    List all allocations with full staff + subject details.
    Used by the admin dashboard to inspect allocation results.
    """
    allocs = admin_service.list_allocations()
    return AllocationReviewResponse(
        total=len(allocs),
        allocations=[AllocationDetail(**a) for a in allocs],
    )


@router.put("/allocation/{allocation_id}", response_model=OverrideResponse)
async def override_allocation(
    allocation_id: int,
    request: OverrideRequest,
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Override an allocation: reassign a subject to a different faculty.
    Validates shift compatibility, workload capacity, and multi-section constraint.
    """
    result = admin_service.override_allocation(
        allocation_id=allocation_id,
        new_staff_id=request.new_staff_id,
        actor_id=coordinator_id,
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return OverrideResponse(**result)


@router.post("/reassign", response_model=ReassignResponse)
async def reassign_subject(
    request: ReassignRequest,
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Move a subject offering from one faculty to another.
    Validates constraints and updates workload summaries.
    """
    result = admin_service.reassign_subject(
        subject_offering_id=request.subject_offering_id,
        from_staff_id=request.from_staff_id,
        to_staff_id=request.to_staff_id,
        actor_id=coordinator_id,
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return ReassignResponse(**result)


@router.post("/allocation/freeze", response_model=FreezeResponse)
async def freeze_allocation(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Freeze all allocations. Prevents preference submission and re-runs.
    """
    result = admin_service.freeze_allocation(actor_id=coordinator_id)
    return FreezeResponse(**result)


@router.post("/allocation/unfreeze", response_model=FreezeResponse)
async def unfreeze_allocation(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """
    Emergency unfreeze. Re-enables modifications.
    """
    result = admin_service.unfreeze_allocation(actor_id=coordinator_id)
    return FreezeResponse(**result)


@router.get("/workload-summary", response_model=WorkloadSummaryResponse)
async def get_workload_summary(
    coordinator_id: int = Depends(get_current_coordinator_id),
    academic_year: str | None = None,
    semester_type: str | None = None,
):
    """
    Get workload summary for all faculty.
    Used for the final workload report (deviation analysis).
    
    Query parameters:
    - academic_year: Optional, defaults to active cycle
    - semester_type: Optional, defaults to active cycle
    """
    result = admin_service.get_workload_summary(
        academic_year=academic_year,
        semester_type=semester_type
    )
    result["records"] = [WorkloadSummaryRecord(**r) for r in result["records"]]
    return WorkloadSummaryResponse(**result)
```

---

## 3. app/admin/service.py

(File is 516 lines - showing first part)

```python
"""
Admin service for allocation review, override, reassignment, and freeze.
PHASE 3: Enhanced HOD control with strict state validation and workload management.

All operations are coordinator/HOD-only and logged to audit_log.
All SQL uses parameterized queries.
"""

from sqlalchemy import text
from app.db.session import get_transaction
import logging

logger = logging.getLogger(__name__)

# PHASE 3: Maximum overload allowed (20% above norm)
MAX_OVERLOAD_PERCENT = 0.20


def _is_shift_compatible(staff_shift: str, offering_shift: int) -> bool:
    """Check shift compatibility (reused from allocation service)."""
    if not staff_shift or not offering_shift:
        return True
    s = str(staff_shift).upper().strip()
    if "SHIFT1+SHIFT2" in s or "BOTH" in s:
        return True
    if "2" in s and offering_shift == 1:
        return False
    if "1" in s and offering_shift == 2:
        return False
    return True


# ============================================================================
# STEP 1: Allocation Review
# ============================================================================

def list_allocations(academic_year: str = "2025-2026", semester_id: int = 2) -> list[dict]:
    """
    List all allocations with full staff + subject details.
    """
    with get_transaction() as session:
        rows = session.execute(
            text("""
                SELECT a.id, a.staff_id, s.name, s.emp_code, s.designation,
                       a.subject_offering_id, sub.code, sub.name,
                       sec.label AS section_label, sem.label AS semester_label,
                       p.name AS program_name,
                       a.l_assigned, a.t_assigned, a.p_assigned, a.ltp_total,
                       a.allocated_at
                FROM allocation a
                JOIN staff s ON s.id = a.staff_id
                JOIN subject_offering so ON so.id = a.subject_offering_id
                JOIN subject sub ON sub.id = so.subject_id
                JOIN section sec ON sec.id = so.section_id
                JOIN semester sem ON sem.id = so.semester_id
                JOIN program p ON p.id = so.program_id
                JOIN cycle c ON c.id = a.cycle_id
                WHERE c.academic_year = :year AND c.semester_id = :sem_id
                ORDER BY p.name, sem.label, sec.label, sub.code
            """),
            {"year": academic_year, "sem_id": semester_id}
        ).fetchall()
    
    return [
        {
            "allocation_id": r[0], "staff_id": r[1], "staff_name": r[2],
            "emp_code": r[3], "designation": r[4],
            "subject_offering_id": r[5], "subject_code": r[6],
            "subject_name": r[7], "section_label": r[8],
            "semester_label": r[9], "program_name": r[10],
            "l_assigned": r[11], "t_assigned": r[12],
            "p_assigned": r[13], "ltp_total": r[14],
            "allocated_at": r[15],
        }
        for r in rows
    ]
```

(Remaining 450+ lines contain override_allocation, reassign_subject, freeze/unfreeze, workload_summary functions)

---

## API Test Results

### HOD Token
```
{"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNiIsImVtYWlsIjoibWN0NDRAaGluZHVzdGFudW5pdi5hYy5pbiIsIm5hbWUiOiJEci4gUy4gR29raWxhIiwicm9sZSI6ImhvZCIsImlhdCI6MTc3NDUxOTM0NiwiZXhwIjoxNzc0NTMzNzQ2fQ.vrVoC3HHWKZMtxy-cxaTIFVGP6PGoCcYecySQmQgZ5s","staff_id":16,"email":"mct44@hindustanuniv.ac.in","name":"Dr. S. Gokila","role":"hod"}
```

### GET /api/admin/review
```
{"detail":"Not Found"}
```

### GET /api/admin/allocations
```
Internal Server Error
```

### GET /api/coordinator/allocations
```
{"detail":"Not Found"}
```
