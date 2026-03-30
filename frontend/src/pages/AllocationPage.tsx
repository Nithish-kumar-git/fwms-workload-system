import { useState, useEffect } from 'react';
import { runAllocation, runAllocationForAllSemesters, getActiveCycle } from '../api/client';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import { Play, CheckCircle, AlertTriangle, AlertCircle, Calendar, Zap } from 'lucide-react';

interface AllocResult {
    success: boolean;
    message: string;
    subjects_total: number;
    subjects_assigned: number;
    subjects_unassigned: number;
    faculty_overloaded: number;
    faculty_underloaded: number;
    faculty_balanced: number;
    allocations: any[];
    unallocated: any[];
}

export default function AllocationPage() {
    const [result, setResult] = useState<AllocResult | null>(null);
    const [running, setRunning] = useState(false);
    const [loadingCycle, setLoadingCycle] = useState(true);
    const [cycleError, setCycleError] = useState('');

    const [cycleYear, setCycleYear] = useState('');
    const [cycleSem, setCycleSem] = useState<number>(0); // Now stores semester_id (1-6)
    const [programId, setProgramId] = useState<number | null>(null);

    const { toasts, addToast, removeToast } = useToast();

    useEffect(() => {
        getActiveCycle()
            .then(res => {
                const ac = res.data;
                setCycleYear(ac.academic_year);
                setCycleSem(ac.semester_id); // Now returns semester_id (1-6)
            })
            .catch(err => {
                const msg = err.response?.data?.detail || 'Failed to load active academic cycle';
                setCycleError(msg);
                addToast(msg, 'error');
            })
            .finally(() => setLoadingCycle(false));
    }, []);

    const handleRun = async () => {
        if (!cycleYear || !cycleSem) {
            addToast('No active academic cycle found', 'error');
            return;
        }
        setRunning(true);
        setResult(null);
        try {
            const res = await runAllocation({
                academic_year: cycleYear,
                semester_id: cycleSem,
                program_id: programId,
            });
            setResult(res.data);
            
            // Show summary toast
            const summary = `Allocation complete: ${res.data.subjects_assigned} assigned, ${res.data.subjects_unassigned} unallocated`;
            addToast(summary, res.data.subjects_unassigned > 0 ? 'info' : 'success');
        } catch (err: any) {
            const msg = err.response?.data?.detail || 'Allocation failed';
            addToast(msg, 'error');
        } finally {
            setRunning(false);
        }
    };

    const handleRunAll = async () => {
        if (!cycleYear) {
            addToast('No active academic cycle found', 'error');
            return;
        }
        setRunning(true);
        setResult(null);
        try {
            const res = await runAllocationForAllSemesters({
                academic_year: cycleYear,
            });
            setResult(res.data);
            
            // Show summary toast
            const summary = `All open semesters allocated: ${res.data.subjects_assigned} assigned, ${res.data.subjects_unassigned} unallocated`;
            addToast(summary, res.data.subjects_unassigned > 0 ? 'info' : 'success');
        } catch (err: any) {
            const msg = err.response?.data?.detail || 'Allocation failed';
            addToast(msg, 'error');
        } finally {
            setRunning(false);
        }
    };

    if (loadingCycle) return (
        <div className="page-container">
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '3rem' }}>Loading active cycle context...</p>
        </div>
    );

    if (cycleError) return (
        <div className="page-container">
            <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                <AlertCircle size={32} style={{ color: '#dc2626', marginBottom: '0.75rem' }} />
                <p style={{ color: '#dc2626', fontWeight: 600, marginBottom: '0.5rem' }}>{cycleError}</p>
                <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>An active academic cycle must be set up before running allocations.</p>
            </div>
        </div>
    );

    return (
        <div className="page-container">
            <ToastContainer toasts={toasts} onRemove={removeToast} />

            <div className="page-header" style={{ alignItems: 'flex-start' }}>
                <div>
                    <h1 className="page-title">Allocation Engine</h1>
                    <p className="page-subtitle">Run automatic subject-to-faculty allocation for the active cycle</p>
                </div>
            </div>

            {/* Config Card */}
            <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#111827' }}>
                    <Calendar size={18} className="text-blue-600" />
                    Allocation Scope
                </h3>
                <div className="flex gap-6 flex-wrap items-end">
                    <div className="flex flex-col gap-1.5">
                        <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem' }}>
                            Academic Year (Active Cycle)
                        </label>
                        <input className="form-input w-40" style={{ background: '#f9fafb', color: '#9ca3af', cursor: 'not-allowed' }} value={cycleYear} disabled />
                    </div>
                    <div className="flex flex-col gap-1.5">
                        <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem' }}>
                            Semester (Active Cycle)
                        </label>
                        <input className="form-input w-40" style={{ background: '#f9fafb', color: '#9ca3af', cursor: 'not-allowed' }} value={cycleSem ? `Semester ${cycleSem}` : ''} disabled />
                    </div>
                    <div className="flex flex-col gap-1.5">
                        <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem' }}>
                            Target Program Filter
                        </label>
                        <select
                            className="form-select w-56"
                            value={programId === null ? '' : programId.toString()}
                            onChange={(e) => setProgramId(e.target.value === '' ? null : parseInt(e.target.value))}
                            disabled={running}
                        >
                            <option value="">All Programs (Entire Cycle)</option>
                            <option value="1">MCA</option>
                            <option value="2">BCA</option>
                        </select>
                    </div>
                    <div className="ml-2">
                        <button onClick={handleRunAll} className="btn" disabled={running} style={{ background: '#16a34a', color: '#fff', marginBottom: '0.75rem', width: '100%', padding: '0.75rem 1.25rem', fontSize: '0.9375rem', fontWeight: 600 }}>
                            {running ? (
                                <span className="flex items-center gap-2">
                                    <div className="spinner w-4 h-4 border-2" /> Running...
                                </span>
                            ) : (
                                <><Zap size={18} /> Run All Open Semesters</>
                            )}
                        </button>
                        <button onClick={handleRun} className="btn btn-primary" disabled={running} style={{ width: '100%' }}>
                            {running ? (
                                <span className="flex items-center gap-2">
                                    <div className="spinner w-4 h-4 border-2" /> Running...
                                </span>
                            ) : (
                                <><Play size={16} /> Run Single Semester</>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {running && !result && (
                <div className="glass-card" style={{ padding: '3rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
                    <div className="spinner" style={{ width: '32px', height: '32px' }} />
                    <p style={{ color: '#6b7280' }}>Processing preferences and applying constraints...</p>
                </div>
            )}

            {result && !running && (
                <>
                    {/* Stats */}
                    <div className="stat-grid" style={{ marginBottom: '1.5rem' }}>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="stat-value text-blue-600">{result.subjects_total}</div>
                            <div className="stat-label">Offerings in Scope</div>
                        </div>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="flex items-center gap-2 mb-2">
                                <CheckCircle size={16} className="text-green-600" strokeWidth={2.5} />
                                <div className="stat-label !mt-0 !text-[13px]">Assigned</div>
                            </div>
                            <div className="stat-value text-green-600">{result.subjects_assigned}</div>
                        </div>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="flex items-center gap-2 mb-2">
                                <AlertTriangle size={16} className="text-amber-500" strokeWidth={2.5} />
                                <div className="stat-label !mt-0 !text-[13px]">Unassigned</div>
                            </div>
                            <div className="stat-value text-amber-500">{result.subjects_unassigned}</div>
                        </div>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="stat-value text-green-600">{result.faculty_balanced}</div>
                            <div className="stat-label">Balanced Faculty</div>
                        </div>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="stat-value text-red-600">{result.faculty_overloaded}</div>
                            <div className="stat-label">Overloaded Faculty</div>
                        </div>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="stat-value text-amber-500">{result.faculty_underloaded}</div>
                            <div className="stat-label">Underloaded Faculty</div>
                        </div>
                    </div>

                    {/* Allocations Table */}
                    <div className="glass-card" style={{ overflow: 'hidden', marginBottom: '1.5rem' }}>
                        <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
                            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: '#111827' }}>Allocations ({result.allocations.length})</h3>
                        </div>
                        {result.allocations.length === 0 ? (
                            <p style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>No allocations were made in this run.</p>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Faculty</th><th>Emp Code</th><th>Subject</th>
                                            <th>Program</th><th>Sem</th><th>Sec</th>
                                            <th>L</th><th>T</th><th>P</th><th>TCH</th><th>Stage</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {result.allocations.slice(0, 100).map((a: any, i: number) => (
                                            <tr key={i}>
                                                <td style={{ fontWeight: 500, color: '#111827' }}>{a.staff_name}</td>
                                                <td style={{ fontFamily: 'monospace', color: '#6b7280', fontSize: '0.8125rem' }}>{a.emp_code}</td>
                                                <td style={{ color: '#374151' }}>{a.subject_code} <span style={{ color: '#d1d5db', margin: '0 0.25rem' }}>—</span> {a.subject_name}</td>
                                                <td>{a.program_name}</td>
                                                <td>{a.semester_label}</td>
                                                <td>{a.section_label}</td>
                                                <td style={{ color: '#6b7280' }}>{a.l_assigned}</td>
                                                <td style={{ color: '#6b7280' }}>{a.t_assigned}</td>
                                                <td style={{ color: '#6b7280' }}>{a.p_assigned}</td>
                                                <td style={{ fontWeight: 600, color: '#2563eb' }}>{a.tch}</td>
                                                <td>
                                                    <span className={`badge ${a.allocation_stage?.startsWith('PREF') ? 'badge-success' : 'badge-warning'} text-[11px] px-2 py-0.5`}>
                                                        {a.allocation_stage || 'Unknown'}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                        {result.allocations.length > 100 && (
                            <div style={{ padding: '1rem', textAlign: 'center', borderTop: '1px solid #e5e7eb', background: '#f9fafb' }}>
                                <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>
                                    Showing first 100 results. Go to Review page to see all.
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Unallocated */}
                    {result.unallocated.length > 0 && (
                        <div className="glass-card" style={{ overflow: 'hidden' }}>
                            <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid #e5e7eb', background: '#fef3c7' }}>
                                <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <AlertTriangle size={18} />
                                    Unallocated Subjects ({result.unallocated.length})
                                </h3>
                                <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.8125rem', color: '#92400e' }}>
                                    These subjects require manual assignment by the coordinator.
                                </p>
                            </div>
                            <table className="data-table">
                                <thead>
                                    <tr><th>Subject</th><th>Program</th><th>Sem</th><th>Sec</th><th>TCH</th><th>Reason</th></tr>
                                </thead>
                                <tbody>
                                    {result.unallocated.map((u: any, i: number) => (
                                        <tr key={i}>
                                            <td style={{ fontFamily: 'monospace' }}>{u.subject_code}</td>
                                            <td>{u.program_name}</td>
                                            <td>{u.semester_label}</td>
                                            <td>{u.section_label}</td>
                                            <td>{u.tch}</td>
                                            <td style={{ color: '#dc2626', fontSize: '0.8125rem' }}>{u.reason}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
