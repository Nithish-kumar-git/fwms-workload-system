import { useEffect, useState } from 'react';
import { getDepartmentSummary } from '../api/client';
import { Users, BookOpen, AlertTriangle, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';

interface DeptSummary {
    total_subject_offerings: number;
    allocated_subjects: number;
    unallocated_subjects: number;
    total_faculty: number;
    average_workload: number;
    faculty_overloaded: number;
    faculty_underloaded: number;
    faculty_balanced: number;
}

export default function DashboardPage() {
    const [data, setData] = useState<DeptSummary | null>(null);
    const [loading, setLoading] = useState(true);

    const [error, setError] = useState('');
    const { toasts, addToast, removeToast } = useToast();

    const loadData = () => {
        setLoading(true);
        setError('');
        getDepartmentSummary()
            .then((r) => setData(r.data))
            .catch((err: any) => {
                const detail = err.response?.data?.detail || 'Failed to load dashboard data';
                setError(detail);
                setData(null);
                addToast(detail, 'error');
            })
            .finally(() => setLoading(false));
    };

    useEffect(() => { loadData(); }, []);

    if (loading) return (
        <div className="page-container">
            <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: '3rem' }}>Loading dashboard data...</p>
        </div>
    );

    if (error) return (
        <div className="page-container">
            <ToastContainer toasts={toasts} onRemove={removeToast} />
            <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                <AlertCircle size={32} style={{ color: '#f87171', marginBottom: '0.75rem' }} />
                <p style={{ color: '#f87171', fontWeight: 600, marginBottom: '0.5rem' }}>{error}</p>
                <button onClick={loadData} className="btn btn-primary" style={{ marginTop: '0.5rem' }}>
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
                    <h1 className="page-title">Dashboard</h1>
                    <p className="page-subtitle">Faculty Workload Management System — Overview</p>
                </div>
            </div>

            {data ? (
                <div className="stat-grid">
                    <div className="glass-card stat-card flex flex-col items-[#f5f5f7] justify-center relative overflow-hidden group">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="p-2.5 bg-blue-500/10 dark:bg-blue-500/20 rounded-xl text-blue-600 dark:text-blue-400">
                                <BookOpen size={22} strokeWidth={2.5} />
                            </div>
                            <div className="stat-label !mt-0 !text-sm">Total Offerings</div>
                        </div>
                        <div className="stat-value text-blue-600 dark:text-blue-400">{data.total_subject_offerings}</div>
                    </div>

                    <div className="glass-card stat-card flex flex-col justify-center relative overflow-hidden group">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="p-2.5 bg-emerald-500/10 dark:bg-emerald-500/20 rounded-xl text-emerald-600 dark:text-emerald-400">
                                <CheckCircle size={22} strokeWidth={2.5} />
                            </div>
                            <div className="stat-label !mt-0 !text-sm">Allocated</div>
                        </div>
                        <div className="stat-value text-emerald-600 dark:text-emerald-400">{data.allocated_subjects}</div>
                    </div>

                    <div className="glass-card stat-card flex flex-col justify-center relative overflow-hidden group">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="p-2.5 bg-amber-500/10 dark:bg-amber-500/20 rounded-xl text-amber-600 dark:text-amber-400">
                                <AlertTriangle size={22} strokeWidth={2.5} />
                            </div>
                            <div className="stat-label !mt-0 !text-sm">Unallocated</div>
                        </div>
                        <div className="stat-value text-amber-600 dark:text-amber-400">{data.unallocated_subjects}</div>
                    </div>

                    <div className="glass-card stat-card flex flex-col justify-center relative overflow-hidden group">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="p-2.5 bg-purple-500/10 dark:bg-purple-500/20 rounded-xl text-purple-600 dark:text-purple-400">
                                <Users size={22} strokeWidth={2.5} />
                            </div>
                            <div className="stat-label !mt-0 !text-sm">Faculty</div>
                        </div>
                        <div className="stat-value text-purple-600 dark:text-purple-400">{data.total_faculty}</div>
                    </div>

                    <div className="glass-card stat-card flex flex-col justify-center">
                        <div className="stat-label mb-2">Balanced</div>
                        <div className="stat-value text-emerald-600 dark:text-emerald-400">{data.faculty_balanced}</div>
                    </div>

                    <div className="glass-card stat-card flex flex-col justify-center">
                        <div className="stat-label mb-2">Overloaded</div>
                        <div className="stat-value text-red-500 dark:text-red-400">{data.faculty_overloaded}</div>
                    </div>

                    <div className="glass-card stat-card flex flex-col justify-center">
                        <div className="stat-label mb-2">Underloaded</div>
                        <div className="stat-value text-amber-500 dark:text-amber-400">{data.faculty_underloaded}</div>
                    </div>

                    <div className="glass-card stat-card flex flex-col justify-center">
                        <div className="stat-label mb-2">Avg Workload (TCH)</div>
                        <div className="stat-value text-gray-800 dark:text-gray-100">{data.average_workload}</div>
                    </div>
                </div>
            ) : (
                <div className="glass-card p-12 text-center flex flex-col items-center justify-center">
                    <div className="p-4 bg-gray-500/5 rounded-full mb-4">
                        <AlertCircle size={32} className="text-gray-400" />
                    </div>
                    <p className="text-gray-500 dark:text-gray-400 font-medium">No data available. Run allocation first.</p>
                </div>
            )}
        </div>
    );
}
