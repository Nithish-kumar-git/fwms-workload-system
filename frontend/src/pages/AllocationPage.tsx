import { useState, useEffect } from 'react';
import { runAllocation, getActiveCycle } from '../api/client';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import { Play, CheckCircle, AlertTriangle, AlertCircle, Calendar } from 'lucide-react';

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

    // Cycle state
    const [cycleYear, setCycleYear] = useState('');
    const [cycleSem, setCycleSem] = useState('');
    const [programId, setProgramId] = useState<number | null>(null);

    const { toasts, addToast, removeToast } = useToast();

    // Fetch active cycle on load to enforce consistency
    useEffect(() => {
        getActiveCycle()
            .then(res => {
                const ac = res.data;
                setCycleYear(ac.academic_year);
                setCycleSem(ac.semester_type);
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
        // Clear previous results to show loading state feels responsive
        setResult(null);
        try {
            const res = await runAllocation({
                academic_year: cycleYear,
                semester_type: cycleSem,
                program_id: programId,
            });
            setResult(res.data);
            addToast(`Allocation complete: ${res.data.subjects_assigned} assigned`, 'success');
        } catch (err: any) {
            const msg = err.response?.data?.detail || 'Allocation failed';
            addToast(msg, 'error');
        } finally {
            setRunning(false);
        }
    };

    if (loadingCycle) return (
        <div className="page-container">
            <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: '3rem' }}>Loading active cycle context...</p>
        </div>
    );

    if (cycleError) return (
        <div className="page-container">
            <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                <AlertCircle size={32} style={{ color: '#f87171', marginBottom: '0.75rem' }} />
                <p style={{ color: '#f87171', fontWeight: 600, marginBottom: '0.5rem' }}>{cycleError}</p>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>An active academic cycle must be set up before running allocations.</p>
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
            <div className="glass-panel p-6 mb-8">
                <h3 className="text-base font-semibold mb-6 flex items-center gap-2 text-gray-900 dark:text-gray-100">
                    <Calendar size={18} className="text-blue-500" />
                    Allocation Scope
                </h3>
                <div className="flex gap-6 flex-wrap items-end">
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1">
                            Academic Year (Active Cycle)
                        </label>
                        <input className="form-input w-40 bg-black/5 dark:bg-white/5 opacity-80 cursor-not-allowed" value={cycleYear} disabled />
                    </div>
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1">
                            Semester Type (Active Cycle)
                        </label>
                        <input className="form-input w-40 bg-black/5 dark:bg-white/5 opacity-80 cursor-not-allowed" value={cycleSem} disabled />
                    </div>
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1">
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
                        <button onClick={handleRun} className="btn btn-primary" disabled={running}>
                            {running ? (
                                <span className="flex items-center gap-2">
                                    <div className="spinner w-4 h-4 border-2" /> Running...
                                </span>
                            ) : (
                                <><Play size={16} /> Run Allocation Engine</>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Results loading placeholder */}
            {running && !result && (
                <div className="glass-card" style={{ padding: '3rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
                    <div className="spinner" style={{ width: '32px', height: '32px' }} />
                    <p style={{ color: 'var(--color-text-muted)' }}>Processing preferences and applying constraints...</p>
                </div>
            )}

            {result && !running && (
                <>
                    {/* Stats */}
                    <div className="stat-grid mb-8">
                        <div className="stat-card glass-panel flex flex-col justify-center">
                            <div className="stat-value text-blue-600 dark:text-blue-400">{result.subjects_total}</div>
                            <div className="stat-label">Offerings in Scope</div>
                        </div>
                        <div className="stat-card glass-panel flex flex-col justify-center relative overflow-hidden group">
                            <div className="flex items-center gap-2 mb-2">
                                <CheckCircle size={16} className="text-emerald-500" strokeWidth={2.5} />
                                <div className="stat-label !mt-0 !text-[13px]">Assigned</div>
                            </div>
                            <div className="stat-value text-emerald-600 dark:text-emerald-400">{result.subjects_assigned}</div>
                        </div>
                        <div className="stat-card glass-panel flex flex-col justify-center relative overflow-hidden group">
                            <div className="flex items-center gap-2 mb-2">
                                <AlertTriangle size={16} className="text-amber-500" strokeWidth={2.5} />
                                <div className="stat-label !mt-0 !text-[13px]">Unassigned</div>
                            </div>
                            <div className="stat-value text-amber-600 dark:text-amber-400">{result.subjects_unassigned}</div>
                        </div>
                        <div className="stat-card glass-panel flex flex-col justify-center">
                            <div className="stat-value text-emerald-600 dark:text-emerald-400">{result.faculty_balanced}</div>
                            <div className="stat-label">Balanced Faculty</div>
                        </div>
                        <div className="stat-card glass-panel flex flex-col justify-center">
                            <div className="stat-value text-red-500 dark:text-red-400">{result.faculty_overloaded}</div>
                            <div className="stat-label">Overloaded Faculty</div>
                        </div>
                        <div className="stat-card glass-panel flex flex-col justify-center">
                            <div className="stat-value text-amber-500 dark:text-amber-400">{result.faculty_underloaded}</div>
                            <div className="stat-label">Underloaded Faculty</div>
                        </div>
                    </div>

                    {/* Allocations Table */}
                    <div className="glass-panel overflow-hidden mb-8">
                        <div className="px-5 py-4 border-b border-black/5 dark:border-white/5 bg-black/[0.02] dark:bg-white/[0.02]">
                            <h3 className="text-base font-semibold m-0 text-gray-900 dark:text-gray-100">Allocations ({result.allocations.length})</h3>
                        </div>
                        {result.allocations.length === 0 ? (
                            <p className="text-center p-8 text-gray-500 dark:text-gray-400">No allocations were made in this run.</p>
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
                                                <td className="font-medium text-gray-900 dark:text-gray-100">{a.staff_name}</td>
                                                <td className="font-mono text-gray-500 text-[13px]">{a.emp_code}</td>
                                                <td className="text-gray-700 dark:text-gray-300">{a.subject_code} <span className="text-gray-400 mx-1">—</span> {a.subject_name}</td>
                                                <td className="text-gray-600">{a.program_name}</td>
                                                <td className="text-gray-600">{a.semester_label}</td>
                                                <td className="text-gray-600">{a.section_label}</td>
                                                <td className="text-gray-500">{a.l_assigned}</td><td className="text-gray-500">{a.t_assigned}</td><td className="text-gray-500">{a.p_assigned}</td>
                                                <td className="font-semibold text-blue-600 dark:text-blue-400">{a.tch}</td>
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
                            <div className="p-4 text-center border-t border-black/5 dark:border-white/5 bg-black/[0.01]">
                                <span className="text-gray-500 text-sm">
                                    Showing first 100 results. Go to Review page to see all.
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Unallocated */}
                    {result.unallocated.length > 0 && (
                        <div className="glass-card" style={{ overflow: 'auto' }}>
                            <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--color-border)' }}>
                                <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: '#fbbf24' }}>
                                    Unallocated ({result.unallocated.length})
                                </h3>
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
                                            <td style={{ color: '#f87171', fontSize: '0.8125rem' }}>{u.reason}</td>
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
