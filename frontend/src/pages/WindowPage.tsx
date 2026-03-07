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
    const [semType, setSemType] = useState('EVEN');
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

    // Live countdown
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
                academic_year: year,
                semester_type: semType,
                start_time: new Date(startTime).toISOString(),
                end_time: new Date(endTime).toISOString(),
            });
            addToast('Preference window opened', 'success');
            loadStatus();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Failed to open window', 'error');
        } finally {
            setSubmitting(false);
        }
    };

    const handleClose = async () => {
        setSubmitting(true);
        try {
            await closePrefWindow();
            addToast('Preference window closed', 'success');
            loadStatus();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Failed to close', 'error');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) return (
        <div className="page-container">
            <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: '3rem' }}>Loading window status...</p>
        </div>
    );

    if (error) return (
        <div className="page-container">
            <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                <AlertCircle size={32} style={{ color: '#f87171', marginBottom: '0.75rem' }} />
                <p style={{ color: '#f87171', fontWeight: 600, marginBottom: '0.5rem' }}>{error}</p>
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
            <div className="glass-panel p-8 mb-8">
                <div className="flex items-center gap-4 mb-6">
                    {status?.is_open ? (
                        <>
                            <div className="p-3 bg-emerald-500/10 dark:bg-emerald-500/20 rounded-full text-emerald-500">
                                <DoorOpen size={28} strokeWidth={2.5} />
                            </div>
                            <div>
                                <span className="badge badge-success px-4 py-1.5 text-sm shadow-sm">
                                    WINDOW OPEN
                                </span>
                            </div>
                        </>
                    ) : (
                        <>
                            <div className="p-3 bg-red-500/10 dark:bg-red-500/20 rounded-full text-red-500">
                                <DoorClosed size={28} strokeWidth={2.5} />
                            </div>
                            <div>
                                <span className="badge badge-danger px-4 py-1.5 text-sm shadow-sm">
                                    WINDOW CLOSED
                                </span>
                            </div>
                        </>
                    )}
                </div>

                {status?.is_open && (
                    <div className="stat-grid mb-6">
                        <div className="stat-card glass-panel flex flex-col justify-center relative overflow-hidden">
                            <div className="flex items-center gap-2 mb-2">
                                <Clock size={16} className="text-blue-500" strokeWidth={2.5} />
                                <div className="stat-label !mt-0 !text-[13px]">Remaining</div>
                            </div>
                            <div className="stat-value text-blue-600 dark:text-blue-400 font-mono tracking-tight">
                                {formatTime(status.remaining_seconds)}
                            </div>
                        </div>
                        <div className="stat-card glass-panel flex flex-col justify-center">
                            <div className="stat-label mb-1">Start Time</div>
                            <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{status.start_time}</div>
                        </div>
                        <div className="stat-card glass-panel flex flex-col justify-center">
                            <div className="stat-label mb-1">End Time</div>
                            <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{status.end_time}</div>
                        </div>
                        <div className="stat-card glass-panel flex flex-col justify-center">
                            <div className="stat-label mb-1">Year / Semester</div>
                            <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{status.academic_year} / {status.semester_type}</div>
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
                <div className="glass-panel p-8">
                    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                        <Settings size={18} className="text-gray-400" />
                        Open New Window
                    </h3>
                    <form onSubmit={handleOpen} className="flex flex-col gap-6">
                        <div className="flex gap-6 flex-wrap">
                            <div className="flex flex-col gap-1.5">
                                <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1">
                                    Academic Year
                                </label>
                                <input className="form-input w-40" value={year} onChange={(e) => setYear(e.target.value)} />
                            </div>
                            <div className="flex flex-col gap-1.5">
                                <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1">
                                    Semester Type
                                </label>
                                <select className="form-select w-32" value={semType} onChange={(e) => setSemType(e.target.value)}>
                                    <option value="EVEN">EVEN</option>
                                    <option value="ODD">ODD</option>
                                </select>
                            </div>
                            <div className="flex flex-col gap-1.5">
                                <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1">
                                    Start Time
                                </label>
                                <input type="datetime-local" className="form-input" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
                            </div>
                            <div className="flex flex-col gap-1.5">
                                <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1">
                                    End Time
                                </label>
                                <input type="datetime-local" className="form-input" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
                            </div>
                        </div>
                        <div className="pt-2 border-t border-black/5 dark:border-white/5">
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
