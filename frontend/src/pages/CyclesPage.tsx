import { useEffect, useState } from 'react';
import { createCycle, activateCycle, listCycles } from '../api/client';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import { CalendarDays, CheckCircle, Plus } from 'lucide-react';

interface Cycle {
    id: number;
    academic_year: string;
    semester_type: string;
    start_date: string | null;
    end_date: string | null;
    is_active: boolean;
    created_at: string;
}

export default function CyclesPage() {
    const [cycles, setCycles] = useState<Cycle[]>([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const { toasts, addToast, removeToast } = useToast();
    const [year, setYear] = useState('2025-2026');
    const [semType, setSemType] = useState('EVEN');
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
            await createCycle({ academic_year: year, semester_type: semType });
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
                        <span><strong style={{ color: '#111827' }}>{activeCycle.academic_year}</strong> · {activeCycle.semester_type}</span>
                        {activeCycle.start_date && <span>From: {activeCycle.start_date}</span>}
                        {activeCycle.end_date && <span>To: {activeCycle.end_date}</span>}
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
                            <label style={{ display: 'block', fontSize: '0.8125rem', color: '#6b7280', marginBottom: '0.375rem', fontWeight: 500 }}>Semester Type</label>
                            <select className="form-select" value={semType} onChange={(e) => setSemType(e.target.value)} style={{ width: '120px' }}>
                                <option value="EVEN">EVEN</option>
                                <option value="ODD">ODD</option>
                            </select>
                        </div>
                        <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? 'Creating...' : 'Create'}</button>
                        <button type="button" onClick={() => setShowForm(false)} className="btn btn-outline">Cancel</button>
                    </form>
                </div>
            )}

            <div className="glass-card" style={{ overflow: 'hidden' }}>
                <table className="data-table">
                    <thead><tr><th>ID</th><th>Academic Year</th><th>Semester</th><th>Start Date</th><th>End Date</th><th>Status</th><th>Created</th><th>Action</th></tr></thead>
                    <tbody>
                        {cycles.map((c) => (
                            <tr key={c.id}>
                                <td>{c.id}</td>
                                <td style={{ fontWeight: 600, color: '#111827' }}>{c.academic_year}</td>
                                <td><span className="badge badge-info">{c.semester_type}</span></td>
                                <td>{c.start_date || '—'}</td><td>{c.end_date || '—'}</td>
                                <td>{c.is_active ? <span className="badge badge-success">Active</span> : <span className="badge badge-warning">Inactive</span>}</td>
                                <td style={{ fontSize: '0.8125rem', color: '#6b7280' }}>{c.created_at?.slice(0, 10)}</td>
                                <td>{!c.is_active && <button onClick={() => handleActivate(c.id)} className="btn btn-success" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}><CalendarDays size={14} /> Activate</button>}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
