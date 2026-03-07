import { useEffect, useState } from 'react';
import { getMyPreferences, submitPreference, deletePreference, getPreferenceStatus, getPrefWindowStatus } from '../api/client';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import { Trash2, Clock, AlertCircle, RefreshCw } from 'lucide-react';

interface Preference {
    id: number;
    preference_number: number;
    subject_code: string;
    subject_name: string;
    program: string;
    semester: string;
    section: string;
    tch: number;
}

interface PrefStatus {
    submitted: number;
    remaining: number;
    is_complete: boolean;
}

export default function PreferencesPage() {
    const [preferences, setPreferences] = useState<Preference[]>([]);
    const [status, setStatus] = useState<PrefStatus | null>(null);
    const [windowOpen, setWindowOpen] = useState(true);
    const [windowRemaining, setWindowRemaining] = useState(0);
    const [loading, setLoading] = useState(true);
    const [offeringId, setOfferingId] = useState('');
    const [prefNum, setPrefNum] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const { toasts, addToast, removeToast } = useToast();

    const [error, setError] = useState('');

    const loadData = async () => {
        setError('');
        try {
            const [prefsRes, statusRes, winRes] = await Promise.all([
                getMyPreferences(),
                getPreferenceStatus(),
                getPrefWindowStatus(),
            ]);
            setPreferences(prefsRes.data.preferences || []);
            setStatus(statusRes.data);
            setWindowOpen(winRes.data.is_open);
            setWindowRemaining(winRes.data.remaining_seconds || 0);
        } catch (err: any) {
            const detail = err.response?.data?.detail || 'Could not connect to server. Check your login.';
            setError(detail);
            addToast(detail, 'error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadData(); }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!offeringId || !prefNum) return;
        setSubmitting(true);
        try {
            await submitPreference({
                subject_offering_id: parseInt(offeringId),
                preference_number: parseInt(prefNum),
            });
            addToast(`Preference ${prefNum} submitted`, 'success');
            setOfferingId('');
            setPrefNum('');
            loadData();
        } catch (err: any) {
            const msg = err.response?.data?.detail || 'Submission failed';
            addToast(msg, 'error');
        } finally {
            setSubmitting(false);
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await deletePreference(id);
            addToast('Preference removed', 'success');
            loadData();
        } catch {
            addToast('Failed to remove preference', 'error');
        }
    };

    if (loading) return (
        <div className="page-container">
            <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: '3rem' }}>Loading preferences...</p>
        </div>
    );

    if (error) return (
        <div className="page-container">
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
                    <h1 className="page-title">My Preferences</h1>
                    <p className="page-subtitle">Select up to 5 subject preferences ranked 1–5</p>
                </div>
                {status && (
                    <span className={`badge ${status.is_complete ? 'badge-success' : 'badge-warning'}`}>
                        {status.submitted}/5 submitted
                    </span>
                )}
            </div>

            {/* Window Status Banner */}
            {!windowOpen && (
                <div className="glass-panel px-6 py-4 mb-6 border-l-4 border-l-red-400 dark:border-l-red-500 flex items-center gap-3">
                    <Clock size={20} className="text-red-400 dark:text-red-500" />
                    <span className="text-red-800 dark:text-red-200 text-[13px] font-medium">
                        Preference submission window is currently <strong className="font-bold">closed</strong>. Contact your coordinator.
                    </span>
                </div>
            )}
            {windowOpen && windowRemaining > 0 && (
                <div className="glass-panel px-6 py-4 mb-6 border-l-4 border-l-emerald-400 dark:border-l-emerald-500 flex items-center gap-3">
                    <Clock size={20} className="text-emerald-500 dark:text-emerald-400" />
                    <span className="text-emerald-800 dark:text-emerald-200 text-[13px] font-medium">
                        Window closes in <strong className="font-bold">{Math.floor(windowRemaining / 3600)}h {Math.floor((windowRemaining % 3600) / 60)}m</strong>
                    </span>
                </div>
            )}

            {/* Submit Form */}
            <div className="glass-panel p-6 mb-8">
                <h3 className="text-base font-semibold mb-4 text-gray-900 dark:text-gray-100">Submit Preference</h3>
                <form onSubmit={handleSubmit} className="flex gap-4 items-end flex-wrap">
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1">
                            Subject Offering ID
                        </label>
                        <input
                            type="number" className="form-input w-40" value={offeringId}
                            onChange={(e) => setOfferingId(e.target.value)}
                            placeholder="e.g. 42"
                        />
                    </div>
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1">
                            Preference Number
                        </label>
                        <select className="form-select w-32" value={prefNum} onChange={(e) => setPrefNum(e.target.value)}>
                            <option value="">Select</option>
                            {[1, 2, 3, 4, 5].map((n) => (
                                <option key={n} value={n}>{n}</option>
                            ))}
                        </select>
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={submitting || !windowOpen}>
                        {!windowOpen ? 'Window Closed' : submitting ? 'Submitting...' : 'Submit'}
                    </button>
                </form>
            </div>

            {/* Current Preferences Table */}
            <div className="glass-panel overflow-hidden mb-8">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Pref #</th>
                            <th>Code</th>
                            <th>Subject</th>
                            <th>Program</th>
                            <th>Sem</th>
                            <th>Section</th>
                            <th>TCH</th>
                            <th style={{ width: '60px' }}></th>
                        </tr>
                    </thead>
                    <tbody>
                        {preferences.length === 0 ? (
                            <tr>
                                <td colSpan={8} style={{ textAlign: 'center', color: 'var(--color-text-muted)', padding: '2rem' }}>
                                    No preferences submitted yet
                                </td>
                            </tr>
                        ) : (
                            preferences.map((p) => (
                                <tr key={p.id}>
                                    <td><span className="badge badge-info">{p.preference_number}</span></td>
                                    <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{p.subject_code}</td>
                                    <td>{p.subject_name}</td>
                                    <td>{p.program}</td>
                                    <td>{p.semester}</td>
                                    <td>{p.section}</td>
                                    <td>{p.tch}</td>
                                    <td>
                                        <button onClick={() => handleDelete(p.id)} className="btn btn-danger" style={{ padding: '0.25rem 0.5rem' }}>
                                            <Trash2 size={14} />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
