# PROGRESS REPORT - Cycle Architecture Investigation

## 1. FILE CONTENTS

### frontend/src/pages/WindowPage.tsx
```typescript
import { useState, useEffect } from 'react';
import { openPrefWindow, closePrefWindow, getPrefWindowStatus } from '../api/client';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import { Clock, DoorOpen, DoorClosed, RefreshCw, AlertCircle, Settings } from 'lucide-react';

export default function WindowPage() {
    const [status, setStatus] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const { toasts, addToast, removeToast } = useToast();
    const [year, setYear] = useState('2025-2026');
    const [semesterId, setSemesterId] = useState(2); // Default to Semester II
    const [startTime, setStartTime] = useState('');
    const [endTime, setEndTime] = useState('');
    const [error, setError] = useState('');

    const loadStatus = () => {
        setLoading(true);
        setError('');
        getPrefWindowStatus()
            .then((r) => setStatus(r.data))
            .catch((err: any) => {
                const detail = err.response?.data?.detail || 'Failed to load window status';
                setError(detail);
                addToast(detail, 'error');
            })
            .finally(() => setLoading(false));
    };

    useEffect(() => { loadStatus(); }, []);

    useEffect(() => {
        if (!status?.is_open || status.remaining_seconds <= 0) return;
        const interval = setInterval(() => {
            setStatus((prev: any) => prev ? { ...prev, remaining_seconds: Math.max(0, prev.remaining_seconds - 1) } : prev);
        }, 1000);
        return () => clearInterval(interval);
    }, [status?.is_open]);

    const formatTime = (seconds: number) => {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        return `${h}h ${m}m ${s}s`;
    };

    const handleOpen = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!startTime || !endTime) return;
        setSubmitting(true);
        try {
            await openPrefWindow({
                academic_year: year, semester_id: semesterId,
                start_time: new Date(startTime).toISOString(),
                end_time: new Date(endTime).toISOString(),
            });
            addToast('Preference window opened', 'success');
            loadStatus();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Failed to open window', 'error');
        } finally { setSubmitting(false); }
    };

    const handleClose = async () => {
        setSubmitting(true);
        try {
            await closePrefWindow();
            addToast('Preference window closed', 'success');
            loadStatus();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Failed to close', 'error');
        } finally { setSubmitting(false); }
    };

    if (loading) return (
        <div className="page-container">
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '3rem' }}>Loading window status...</p>
        </div>
    );

    if (error) return (
        <div className="page-container">
            <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                <AlertCircle size={32} style={{ color: '#dc2626', marginBottom: '0.75rem' }} />
                <p style={{ color: '#dc2626', fontWeight: 600, marginBottom: '0.5rem' }}>{error}</p>
                <button onClick={loadStatus} className="btn btn-primary" style={{ marginTop: '0.5rem' }}>
                    <RefreshCw size={16} /> Retry
                </button>
            </div>
        </div>
    );

    return (
        <div className="page-container">
            <ToastContainer toasts={toasts} onRemove={removeToast} />
            <div className="page-header">
                <div>
                    <h1 className="page-title">Preference Window</h1>
                    <p className="page-subtitle">Control the faculty preference submission cycle</p>
                </div>
                <button onClick={loadStatus} className="btn btn-outline"><RefreshCw size={16} />Refresh</button>
            </div>

            {/* Current Status Card */}
            <div className="glass-card" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
                <div className="flex items-center gap-4 mb-6">
                    {status?.is_open ? (
                        <>
                            <div className="p-3 bg-green-50 rounded-full text-green-600">
                                <DoorOpen size={28} strokeWidth={2.5} />
                            </div>
                            <span className="badge badge-success px-4 py-1.5 text-sm">WINDOW OPEN</span>
                        </>
                    ) : (
                        <>
                            <div className="p-3 bg-red-50 rounded-full text-red-600">
                                <DoorClosed size={28} strokeWidth={2.5} />
                            </div>
                            <span className="badge badge-danger px-4 py-1.5 text-sm">WINDOW CLOSED</span>
                        </>
                    )}
                </div>

                {status?.is_open && (
                    <div className="stat-grid" style={{ marginBottom: '1.5rem' }}>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="flex items-center gap-2 mb-2">
                                <Clock size={16} className="text-blue-600" strokeWidth={2.5} />
                                <div className="stat-label !mt-0 !text-[13px]">Remaining</div>
                            </div>
                            <div className="stat-value text-blue-600 font-mono tracking-tight">{formatTime(status.remaining_seconds)}</div>
                        </div>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="stat-label mb-1">Start Time</div>
                            <div style={{ fontSize: '0.875rem', fontWeight: 500, color: '#111827' }}>{status.start_time}</div>
                        </div>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="stat-label mb-1">End Time</div>
                            <div style={{ fontSize: '0.875rem', fontWeight: 500, color: '#111827' }}>{status.end_time}</div>
                        </div>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="stat-label mb-1">Year / Semester</div>
                            <div style={{ fontSize: '0.875rem', fontWeight: 500, color: '#111827' }}>{status.academic_year} / Semester {status.semester_id}</div>
                        </div>
                    </div>
                )}

                {status?.is_open && (
                    <button onClick={handleClose} className="btn btn-danger" disabled={submitting}>
                        <DoorClosed size={16} />
                        {submitting ? 'Closing...' : 'Close Window Now'}
                    </button>
                )}
            </div>

            {/* Open Window Form */}
            {!status?.is_open && (
                <div className="glass-card" style={{ padding: '2rem' }}>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#111827' }}>
                        <Settings size={18} style={{ color: '#9ca3af' }} /> Open New Window
                    </h3>
                    <form onSubmit={handleOpen} className="flex flex-col gap-6">
                        <div className="flex gap-6 flex-wrap">
                            <div className="flex flex-col gap-1.5">
                                <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem' }}>Academic Year</label>
                                <input className="form-input w-40" value={year} onChange={(e) => setYear(e.target.value)} />
                            </div>
                            <div className="flex flex-col gap-1.5">
                                <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem' }}>Semester</label>
                                <select className="form-select w-32" value={semesterId} onChange={(e) => setSemesterId(Number(e.target.value))}>
                                    <option value={1}>I</option>
                                    <option value={2}>II</option>
                                    <option value={3}>III</option>
                                    <option value={4}>IV</option>
                                    <option value={5}>V</option>
                                    <option value={6}>VI</option>
                                </select>
                            </div>
                            <div className="flex flex-col gap-1.5">
                                <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem' }}>Start Time</label>
                                <input type="datetime-local" className="form-input" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
                            </div>
                            <div className="flex flex-col gap-1.5">
                                <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem' }}>End Time</label>
                                <input type="datetime-local" className="form-input" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
                            </div>
                        </div>
                        <div className="pt-2 border-t border-gray-100">
                            <button type="submit" className="btn btn-primary mt-4" disabled={submitting || !startTime || !endTime}>
                                <DoorOpen size={16} />
                                {submitting ? 'Opening...' : 'Open Window'}
                            </button>
                        </div>
                    </form>
                </div>
            )}
        </div>
    );
}
```


### frontend/src/pages/CyclesPage.tsx
```typescript
import { useEffect, useState } from 'react';
import { createCycle, activateCycle, listCycles } from '../api/client';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import { CalendarDays, CheckCircle, Plus } from 'lucide-react';

interface Cycle {
    id: number;
    academic_year: string;
    semester_id: number;
    semester_name: string;
    status: string;
    opened_at: string | null;
    closed_at: string | null;
    allocated_at: string | null;
    frozen_at: string | null;
    is_active: boolean;
    created_at: string;
}

export default function CyclesPage() {
    const [cycles, setCycles] = useState<Cycle[]>([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const { toasts, addToast, removeToast } = useToast();
    const [year, setYear] = useState('2025-2026');
    const [semesterId, setSemesterId] = useState(2); // Default to Semester II
    const [showForm, setShowForm] = useState(false);

    const loadCycles = () => {
        listCycles()
            .then((r) => setCycles(r.data))
            .catch(() => addToast('Failed to load cycles', 'error'))
            .finally(() => setLoading(false));
    };

    useEffect(() => { loadCycles(); }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            await createCycle({ academic_year: year, semester_id: semesterId });
            addToast('Cycle created', 'success');
            setShowForm(false);
            loadCycles();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Failed to create', 'error');
        } finally { setSubmitting(false); }
    };

    const handleActivate = async (id: number) => {
        try {
            await activateCycle(id);
            addToast('Cycle activated', 'success');
            loadCycles();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Activation failed', 'error');
        }
    };

    if (loading) return <div className="page-container"><p style={{ color: '#6b7280' }}>Loading...</p></div>;

    const activeCycle = cycles.find((c) => c.is_active);

    return (
        <div className="page-container">
            <ToastContainer toasts={toasts} onRemove={removeToast} />
            <div className="page-header">
                <div>
                    <h1 className="page-title">Academic Cycles</h1>
                    <p className="page-subtitle">Manage academic year and semester cycles</p>
                </div>
                <button onClick={() => setShowForm(!showForm)} className="btn btn-primary"><Plus size={16} /> New Cycle</button>
            </div>

            {activeCycle && (
                <div className="glass-card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.5rem', borderLeft: '4px solid #16a34a' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                        <CheckCircle size={20} style={{ color: '#16a34a' }} />
                        <span className="badge badge-success" style={{ fontSize: '0.875rem', padding: '0.375rem 0.75rem' }}>ACTIVE CYCLE</span>
                    </div>
                    <div style={{ display: 'flex', gap: '2rem', fontSize: '0.875rem', color: '#6b7280' }}>
                        <span><strong style={{ color: '#111827' }}>{activeCycle.academic_year}</strong> · Semester {activeCycle.semester_name}</span>
                        <span>Status: <strong style={{ color: '#111827' }}>{activeCycle.status}</strong></span>
                        {activeCycle.opened_at && <span>Opened: {new Date(activeCycle.opened_at).toLocaleDateString()}</span>}
                    </div>
                </div>
            )}

            {showForm && (
                <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem', color: '#111827' }}>Create New Cycle</h3>
                    <form onSubmit={handleCreate} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.8125rem', color: '#6b7280', marginBottom: '0.375rem', fontWeight: 500 }}>Academic Year</label>
                            <input className="form-input" value={year} onChange={(e) => setYear(e.target.value)} style={{ width: '150px' }} />
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.8125rem', color: '#6b7280', marginBottom: '0.375rem', fontWeight: 500 }}>Semester</label>
                            <select className="form-select" value={semesterId} onChange={(e) => setSemesterId(Number(e.target.value))} style={{ width: '120px' }}>
                                <option value={1}>I</option>
                                <option value={2}>II</option>
                                <option value={3}>III</option>
                                <option value={4}>IV</option>
                                <option value={5}>V</option>
                                <option value={6}>VI</option>
                            </select>
                        </div>
                        <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? 'Creating...' : 'Create'}</button>
                        <button type="button" onClick={() => setShowForm(false)} className="btn btn-outline">Cancel</button>
                    </form>
                </div>
            )}

            <div className="glass-card" style={{ overflow: 'hidden' }}>
                <table className="data-table">
                    <thead><tr><th>ID</th><th>Academic Year</th><th>Semester</th><th>Status</th><th>Opened</th><th>Closed</th><th>Active</th><th>Created</th><th>Action</th></tr></thead>
                    <tbody>
                        {cycles.map((c) => (
                            <tr key={c.id}>
                                <td>{c.id}</td>
                                <td style={{ fontWeight: 600, color: '#111827' }}>{c.academic_year}</td>
                                <td><span className="badge badge-info">Semester {c.semester_name}</span></td>
                                <td><span className={`badge ${c.status === 'OPEN' ? 'badge-success' : c.status === 'FROZEN' ? 'badge-error' : 'badge-warning'}`}>{c.status}</span></td>
                                <td style={{ fontSize: '0.8125rem', color: '#6b7280' }}>{c.opened_at ? new Date(c.opened_at).toLocaleDateString() : '—'}</td>
                                <td style={{ fontSize: '0.8125rem', color: '#6b7280' }}>{c.closed_at ? new Date(c.closed_at).toLocaleDateString() : '—'}</td>
                                <td>{c.is_active ? <span className="badge badge-success">Yes</span> : <span className="badge badge-warning">No</span>}</td>
                                <td style={{ fontSize: '0.8125rem', color: '#6b7280' }}>{c.created_at?.slice(0, 10)}</td>
                                <td>{!c.is_active && c.status !== 'FROZEN' && <button onClick={() => handleActivate(c.id)} className="btn btn-success" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}><CalendarDays size={14} /> Activate</button>}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
```


### app/preference/window_router.py
```python
"""
FastAPI router for preference window management.
Coordinator endpoints for opening/closing the preference submission window.

Endpoints:
  POST /api/pref-window/open     Open preference window
  POST /api/pref-window/close    Close preference window
  GET  /api/pref-window/status   Get current window status
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import logging

from app.auth.dependencies import get_current_coordinator_id
from app.preference.window_service import (
    open_preference_window,
    close_preference_window,
    get_window_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pref-window", tags=["preference-window"])


# --- Schemas ---

class OpenWindowRequest(BaseModel):
    start_time: str = Field(..., description="ISO datetime")
    end_time: str = Field(..., description="ISO datetime")
    academic_year: str | None = Field(None, description="e.g. 2025-2026")
    semester_id: int | None = Field(None, description="Semester ID (1-6)")
    cycle_id: int | None = Field(None)


class WindowResponse(BaseModel):
    success: bool
    message: str
    window_id: int | None = None


class WindowStatusResponse(BaseModel):
    is_open: bool
    status: str = 'CLOSED'  # 'OPEN', 'CLOSED', 'SCHEDULED'
    window_id: int | None = None
    start_time: str | None = None
    end_time: str | None = None
    remaining_seconds: int = 0
    academic_year: str | None = None
    semester_id: int | None = None


# --- Endpoints ---

@router.post("/open", response_model=WindowResponse)
async def open_window(
    body: OpenWindowRequest,
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Open a preference submission window. Coordinator-only."""
    result = open_preference_window(
        coordinator_id=coordinator_id,
        start_time=body.start_time,
        end_time=body.end_time,
        academic_year=body.academic_year,
        semester_id=body.semester_id,
        cycle_id=body.cycle_id,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return WindowResponse(**result)


@router.post("/close", response_model=WindowResponse)
async def close_window(
    coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Close the active preference window. Coordinator-only."""
    result = close_preference_window(coordinator_id=coordinator_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return WindowResponse(**result)


@router.get("/status", response_model=WindowStatusResponse)
async def window_status():
    """Get current preference window status. Public endpoint."""
    return WindowStatusResponse(**get_window_status())
```


### app/preference/window_service.py
```python
"""
Preference window service — manages the preference submission window lifecycle.
Uses the existing selection_window table and window_transactions module.

Convenience layer that provides:
  - open_preference_window: creates + opens a window in one step
  - close_preference_window: closes the active window
  - get_window_status: returns current window state with remaining time
  - is_window_open: guard check for preference submissions
"""

from sqlalchemy import text
from app.db.session import get_transaction
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def open_preference_window(
    coordinator_id: int,
    start_time: str,
    end_time: str,
    academic_year: str | None = None,
    semester_id: int | None = None,
    cycle_id: int | None = None,
) -> dict:
    """
    Open a preference submission window.
    Follows the frozen lifecycle: DRAFT → SCHEDULED → OPEN.
    Only one OPEN window allowed per academic_year + semester_id.
    """
    with get_transaction() as session:
        # Check for existing OPEN window
        existing = session.execute(
            text("""
                SELECT id FROM selection_window
                WHERE status = 'OPEN'
                LIMIT 1
            """),
        ).fetchone()

        if existing is not None:
            return {
                "success": False,
                "message": f"An open window already exists (id={existing[0]}). Close it first.",
            }

        resolved_cycle_id = None
        # 1. Use explicit ID
        if cycle_id is not None:
            resolved_cycle_id = cycle_id
        # 2. Lookup by year/semester
        elif academic_year and semester_id:
            cycle_row = session.execute(
                text("""
                    SELECT id FROM cycle
                    WHERE academic_year = :year AND semester_id = :sem_id
                    ORDER BY id DESC LIMIT 1
                """),
                {"year": academic_year, "sem_id": semester_id},
            ).fetchone()
            resolved_cycle_id = cycle_row[0] if cycle_row else None
        
        # 3. Fallback to active cycle
        if resolved_cycle_id is None:
            from app.admin.cycle_service_new import get_active_cycle
            active = get_active_cycle()
            if active:
                resolved_cycle_id = active["id"]
                academic_year = active["academic_year"]
                semester_id = active["semester_id"]
            else:
                return {"success": False, "message": "Failed to resolve cycle scope"}

                
        # ---- LIFECYCLE STEP 1: Insert as DRAFT ----
        result = session.execute(
            text("""
                INSERT INTO selection_window
                    (name, batch_id, specialization_id, start_time, end_time,
                     status, max_subjects_per_staff, cycle_id,
                     allocation_locked)
                VALUES (
                    :name, 1, 1, :start_time, :end_time,
                    'DRAFT', 5, :cycle_id, false
                )
                RETURNING id
            """),
            {
                "name": f"Preference Window {academic_year} Sem-{semester_id}",
                "start_time": start_time,
                "end_time": end_time,
                "cycle_id": resolved_cycle_id,
            },
        )
        window_id = result.scalar()

        # Audit: WINDOW_CREATED
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'WINDOW_CREATED', :details)
            """),
            {
                "actor": coordinator_id,
                "details": (
                    f'{{"window_id": {window_id}, '
                    f'"academic_year": "{academic_year}", '
                    f'"semester_id": {semester_id}}}'
                ),
            },
        )

        # ---- LIFECYCLE STEP 2: Transition DRAFT → SCHEDULED ----
        session.execute(
            text("""
                UPDATE selection_window
                SET status = 'SCHEDULED', updated_at = now()
                WHERE id = :id
            """),
            {"id": window_id},
        )

        # Audit: WINDOW_SCHEDULED
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'WINDOW_SCHEDULED', :details)
            """),
            {
                "actor": coordinator_id,
                "details": (
                    f'{{"window_id": {window_id}, '
                    f'"start_time": "{start_time}", '
                    f'"end_time": "{end_time}"}}'
                ),
            },
        )

        # ---- LIFECYCLE STEP 3: Transition SCHEDULED → OPEN ----
        session.execute(
            text("""
                UPDATE selection_window
                SET status = 'OPEN', updated_at = now()
                WHERE id = :id
            """),
            {"id": window_id},
        )

        # Audit: WINDOW_OPENED
        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'WINDOW_OPENED', :details)
            """),
            {
                "actor": coordinator_id,
                "details": (
                    f'{{"window_id": {window_id}, '
                    f'"academic_year": "{academic_year}", '
                    f'"semester_id": {semester_id}, '
                    f'"start_time": "{start_time}", '
                    f'"end_time": "{end_time}"}}'
                ),
            },
        )

        session.commit()

    logger.info(f"Preference window opened: id={window_id} (DRAFT→SCHEDULED→OPEN)")
    return {
        "success": True,
        "message": "Preference window opened",
        "window_id": window_id,
    }



def close_preference_window(coordinator_id: int) -> dict:
    """Close the currently open preference window."""
    with get_transaction() as session:
        window = session.execute(
            text("SELECT id FROM selection_window WHERE status = 'OPEN' LIMIT 1")
        ).fetchone()

        if window is None:
            return {"success": False, "message": "No open window found"}

        window_id = window[0]
        session.execute(
            text("UPDATE selection_window SET status = 'CLOSED' WHERE id = :id"),
            {"id": window_id},
        )

        session.execute(
            text("""
                INSERT INTO audit_log (actor_staff_id, action_type, details)
                VALUES (:actor, 'WINDOW_CLOSED', :details)
            """),
            {
                "actor": coordinator_id,
                "details": f'{{"window_id": {window_id}}}',
            },
        )

        session.commit()

    logger.info(f"Preference window closed: id={window_id}")
    return {"success": True, "message": "Preference window closed", "window_id": window_id}


def get_window_status() -> dict:
    """
    Get the current preference window status.
    Returns is_open, timing details, and remaining time.
    """
    with get_transaction() as session:
        row = session.execute(
            text("""
                SELECT sw.id, sw.status, sw.start_time, sw.end_time,
                       ay.name AS academic_year, c.semester_id
                FROM selection_window sw
                LEFT JOIN cycle c ON c.id = sw.cycle_id
                LEFT JOIN academic_year ay ON ay.id = c.academic_year_id
                WHERE sw.status = 'OPEN'
                ORDER BY sw.id DESC LIMIT 1
            """),
        ).fetchone()

    if row is None:
        return {
            "is_open": False,
            "status": "CLOSED",
            "window_id": None,
            "start_time": None,
            "end_time": None,
            "remaining_seconds": 0,
            "academic_year": None,
            "semester_id": None,
        }

    now = datetime.now(timezone.utc)
    end_time = row[3]
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    remaining = max(0, int((end_time - now).total_seconds()))

    return {
        "is_open": True,
        "status": row[1],  # 'OPEN', 'CLOSED', 'SCHEDULED'
        "window_id": row[0],
        "start_time": str(row[2]),
        "end_time": str(row[3]),
        "remaining_seconds": remaining,
        "academic_year": row[4],
        "semester_id": row[5],
    }


def is_window_open() -> bool:
    """Quick check: is there an open preference window?"""
    status = get_window_status()
    return status["is_open"]
```


### app/admin/cycle_router.py
```python
"""
FastAPI router for academic cycle management.
Coordinator endpoints for creating, activating, and listing academic cycles.

Endpoints:
  POST /api/cycles          Create new cycle
  POST /api/cycles/activate Activate a cycle
  GET  /api/cycles          List all cycles
  GET  /api/cycles/active   Get current active cycle
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import logging

from app.auth.dependencies import get_current_coordinator_id
from app.admin.cycle_service_new import (
    create_cycle,
    activate_cycle,
    list_cycles,
    get_active_cycle,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cycles", tags=["academic-cycles"])


# --- Schemas ---

class CreateCycleRequest(BaseModel):
    academic_year: str = Field(..., description="e.g. 2025-2026")
    semester_id: int = Field(..., description="Semester ID (1-6 for I-VI)")
    start_date: str | None = None
    end_date: str | None = None


class ActivateCycleRequest(BaseModel):
    cycle_id: int


class CycleResponse(BaseModel):
    id: int
    academic_year: str
    semester_id: int
    semester_name: str
    status: str
    opened_at: str | None = None
    closed_at: str | None = None
    allocated_at: str | None = None
    frozen_at: str | None = None
    is_active: bool
    created_at: str


class ActionResponse(BaseModel):
    success: bool
    message: str
    cycle_id: int | None = None


# --- Endpoints ---

@router.post("", response_model=ActionResponse)
async def create_cycle_endpoint(
    body: CreateCycleRequest,
    _coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Create a new academic cycle. Coordinator-only."""
    result = create_cycle(
        academic_year=body.academic_year,
        semester_id=body.semester_id,
        start_date=body.start_date,
        end_date=body.end_date,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return ActionResponse(**result)


@router.post("/activate", response_model=ActionResponse)
async def activate_cycle_endpoint(
    body: ActivateCycleRequest,
    _coordinator_id: int = Depends(get_current_coordinator_id),
):
    """Activate an academic cycle. Coordinator-only."""
    result = activate_cycle(body.cycle_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return ActionResponse(**result)


@router.get("", response_model=list[CycleResponse])
async def list_cycles_endpoint(
    _coordinator_id: int = Depends(get_current_coordinator_id),
):
    """List all academic cycles. Coordinator-only."""
    return [CycleResponse(**c) for c in list_cycles()]


@router.get("/active", response_model=CycleResponse | None)
async def get_active_cycle_endpoint():
    """Get the currently active cycle. Public endpoint."""
    cycle = get_active_cycle()
    if cycle is None:
        raise HTTPException(status_code=404, detail="No active academic cycle")
    return CycleResponse(**cycle)
```


### app/admin/cycle_service_new.py
```python
"""
Service layer for semester-specific cycle management.
NEW ARCHITECTURE: Cycles are per (academic_year + semester), not ODD/EVEN.

IMPORTANT: This service uses the NEW cycle table schema from migration 021:
- cycle.academic_year_id (FK to academic_year.id)
- cycle.semester_id (FK to semester.id)
- cycle.status ('OPEN', 'CLOSED', 'ALLOCATED', 'FROZEN')
"""

import logging
from sqlalchemy import text
from app.db.session import get_transaction

logger = logging.getLogger(__name__)


def create_cycle(academic_year: str, semester_id: int, start_date: str | None = None, end_date: str | None = None) -> dict:
    """
    Create a new semester-specific cycle.
    
    Args:
        academic_year: e.g. "2025-2026"
        semester_id: 1-6 (I-VI)
        start_date: Optional start date
        end_date: Optional end date
    
    Returns:
        {"success": bool, "message": str, "cycle_id": int | None}
    """
    with get_transaction() as session:
        # Ensure academic_year exists in academic_year table
        year_row = session.execute(
            text("SELECT id FROM academic_year WHERE name = :name"),
            {"name": academic_year}
        ).fetchone()
        
        if not year_row:
            # Create academic_year if it doesn't exist
            session.execute(
                text("INSERT INTO academic_year (name, start_date, end_date) VALUES (:name, :start_date, :end_date)"),
                {"name": academic_year, "start_date": start_date, "end_date": end_date}
            )
            year_row = session.execute(
                text("SELECT id FROM academic_year WHERE name = :name"),
                {"name": academic_year}
            ).fetchone()
        
        academic_year_id = year_row[0]
        
        # Check if cycle already exists
        existing = session.execute(
            text("SELECT id FROM cycle WHERE academic_year_id = :year_id AND semester_id = :sem_id"),
            {"year_id": academic_year_id, "sem_id": semester_id}
        ).fetchone()
        
        if existing:
            return {
                "success": False,
                "message": f"Cycle for {academic_year} Semester {semester_id} already exists",
                "cycle_id": None
            }
        
        # Create new cycle with status='CLOSED'
        result = session.execute(
            text("""
                INSERT INTO cycle (academic_year_id, semester_id, status)
                VALUES (:year_id, :sem_id, 'CLOSED')
                RETURNING id
            """),
            {"year_id": academic_year_id, "sem_id": semester_id}
        )
        
        cycle_id = result.fetchone()[0]
        session.commit()
        
        logger.info(f"Created cycle {cycle_id} for {academic_year} Semester {semester_id}")
        
        return {
            "success": True,
            "message": f"Cycle created for {academic_year} Semester {semester_id}",
            "cycle_id": cycle_id
        }



def activate_cycle(cycle_id: int) -> dict:
    """
    Activate a cycle (set status='OPEN').
    Only one cycle can be OPEN at a time.
    
    Returns:
        {"success": bool, "message": str}
    """
    with get_transaction() as session:
        # Check if cycle exists
        cycle = session.execute(
            text("SELECT id, status FROM cycle WHERE id = :id"),
            {"id": cycle_id}
        ).fetchone()
        
        if not cycle:
            return {"success": False, "message": "Cycle not found"}
        
        if cycle[1] == 'FROZEN':
            return {"success": False, "message": "Cannot activate a frozen cycle"}
        
        # Close all other OPEN cycles
        session.execute(
            text("UPDATE cycle SET status = 'CLOSED', closed_at = NOW() WHERE status = 'OPEN'")
        )
        
        # Open this cycle
        session.execute(
            text("UPDATE cycle SET status = 'OPEN', opened_at = NOW() WHERE id = :id"),
            {"id": cycle_id}
        )
        
        session.commit()
        
        logger.info(f"Activated cycle {cycle_id}")
        
        return {"success": True, "message": "Cycle activated"}


def list_cycles() -> list[dict]:
    """
    List all cycles with their academic year and semester details.
    Joins with academic_year and semester tables.
    
    Returns:
        List of cycle dictionaries
    """
    with get_transaction() as session:
        rows = session.execute(
            text("""
                SELECT 
                    c.id,
                    ay.name as academic_year,
                    c.semester_id,
                    s.label as semester_name,
                    c.status,
                    c.opened_at,
                    c.closed_at,
                    c.allocated_at,
                    c.frozen_at,
                    c.created_at
                FROM cycle c
                JOIN academic_year ay ON c.academic_year_id = ay.id
                JOIN semester s ON c.semester_id = s.id
                ORDER BY c.created_at DESC
            """)
        ).fetchall()
        
        return [
            {
                "id": row[0],
                "academic_year": row[1],
                "semester_id": row[2],
                "semester_name": row[3],
                "status": row[4],
                "is_active": row[4] == 'OPEN',
                "opened_at": row[5].isoformat() if row[5] else None,
                "closed_at": row[6].isoformat() if row[6] else None,
                "allocated_at": row[7].isoformat() if row[7] else None,
                "frozen_at": row[8].isoformat() if row[8] else None,
                "created_at": row[9].isoformat() if row[9] else None,
            }
            for row in rows
        ]



def get_active_cycle() -> dict | None:
    """
    Get the currently active (OPEN) cycle.
    Joins with academic_year and semester tables.
    
    Returns:
        Cycle dictionary with id, academic_year, semester_id, semester_name, status, is_active
        or None if no active cycle
    """
    with get_transaction() as session:
        row = session.execute(
            text("""
                SELECT 
                    c.id,
                    ay.name as academic_year,
                    c.semester_id,
                    s.label as semester_name,
                    c.status,
                    c.opened_at,
                    c.closed_at,
                    c.allocated_at,
                    c.frozen_at,
                    c.created_at
                FROM cycle c
                JOIN academic_year ay ON c.academic_year_id = ay.id
                JOIN semester s ON c.semester_id = s.id
                WHERE c.status = 'OPEN'
                LIMIT 1
            """)
        ).fetchone()
        
        if not row:
            return None
        
        return {
            "id": row[0],
            "academic_year": row[1],
            "semester_id": row[2],
            "semester_name": row[3],
            "status": row[4],
            "is_active": True,
            "opened_at": row[5].isoformat() if row[5] else None,
            "closed_at": row[6].isoformat() if row[6] else None,
            "allocated_at": row[7].isoformat() if row[7] else None,
            "frozen_at": row[8].isoformat() if row[8] else None,
            "created_at": row[9].isoformat() if row[9] else None,
        }
```

---

## 2. SQL QUERY RESULTS

### Query 1: Semester Table
```sql
SELECT id, label FROM semester ORDER BY id;
```

**Result:**
```
 id | label 
----+-------
  1 | I
  2 | II
  3 | III
  4 | IV
  5 | V
  6 | VI
(6 rows)
```

### Query 2: Cycle Table with Semester Labels
```sql
SELECT c.id, c.status, c.semester_id, s.label 
FROM cycle c 
JOIN semester s ON s.id = c.semester_id;
```

**Result:**
```
 id | status | semester_id | label 
----+--------+-------------+-------
  1 | OPEN   |           2 | II
  2 | OPEN   |           4 | IV
  3 | OPEN   |           6 | VI
(3 rows)
```

---

## 3. KEY FINDINGS

### Critical Issue: Multiple OPEN Cycles
The database currently has **3 cycles with status='OPEN'** simultaneously:
- Cycle 1: Semester II (OPEN)
- Cycle 2: Semester IV (OPEN)
- Cycle 3: Semester VI (OPEN)

This violates the business rule that **only one cycle should be OPEN at a time**.

### Architecture Mismatch
1. **window_service.py** tries to lookup cycle by `academic_year` string:
   ```python
   SELECT id FROM cycle
   WHERE academic_year = :year AND semester_id = :sem_id
   ```
   But the cycle table uses `academic_year_id` (FK), not `academic_year` string.

2. **cycle_service_new.py** correctly uses `academic_year_id`:
   ```python
   SELECT id FROM cycle WHERE academic_year_id = :year_id AND semester_id = :sem_id
   ```

### Frontend-Backend Alignment
- Frontend sends: `academic_year` (string) + `semester_id` (int)
- Backend expects: Same format
- But lookup query in window_service.py is broken

---

## 4. ROOT CAUSE

The window_service.py cycle lookup query is incorrect:
```python
# WRONG - cycle table doesn't have academic_year column
cycle_row = session.execute(
    text("""
        SELECT id FROM cycle
        WHERE academic_year = :year AND semester_id = :sem_id
        ORDER BY id DESC LIMIT 1
    """),
    {"year": academic_year, "sem_id": semester_id},
).fetchone()
```

Should be:
```python
# CORRECT - join with academic_year table
cycle_row = session.execute(
    text("""
        SELECT c.id FROM cycle c
        JOIN academic_year ay ON c.academic_year_id = ay.id
        WHERE ay.name = :year AND c.semester_id = :sem_id
        ORDER BY c.id DESC LIMIT 1
    """),
    {"year": academic_year, "sem_id": semester_id},
).fetchone()
```

---

## END OF REPORT
