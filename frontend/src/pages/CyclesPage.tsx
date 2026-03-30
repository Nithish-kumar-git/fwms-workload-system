import { useEffect, useState } from 'react';
import { createCycle, activateCycle, listCycles, activateSemesterGroup } from '../api/client';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import { CalendarDays, CheckCircle, Plus, Layers } from 'lucide-react';

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

    const handleActivateGroup = async (group: 'ODD' | 'EVEN') => {
        try {
            const result = await activateSemesterGroup({ academic_year: year, semester_group: group });
            addToast(result.data.message || `${group} semesters activated`, 'success');
            loadCycles();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Group activation failed', 'error');
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

            {/* Open Semester Group Section */}
            <div className="glass-card" style={{ padding: '2rem', marginBottom: '1.5rem', background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.03) 0%, rgba(147, 197, 253, 0.03) 100%)' }}>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem', color: '#111827' }}>Open Semester Group</h2>
                <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '1.5rem' }}>
                    Opening a group closes all currently open semesters and opens 3 at once
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    {/* ODD Button */}
                    <button
                        onClick={() => handleActivateGroup('ODD')}
                        className="glass-card"
                        style={{
                            padding: '1.5rem',
                            border: '2px solid #e5e7eb',
                            borderRadius: '12px',
                            cursor: 'pointer',
                            transition: 'all 0.2s ease',
                            background: '#fff',
                            textAlign: 'left',
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.borderColor = '#3b82f6';
                            e.currentTarget.style.background = 'rgba(59, 130, 246, 0.05)';
                            e.currentTarget.style.transform = 'translateY(-2px)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.borderColor = '#e5e7eb';
                            e.currentTarget.style.background = '#fff';
                            e.currentTarget.style.transform = 'translateY(0)';
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                            <span style={{ fontSize: '2rem' }}>📚</span>
                            <span style={{ fontSize: '1.125rem', fontWeight: 700, color: '#111827' }}>Open ODD Semesters</span>
                        </div>
                        <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
                            Semesters I, III, V
                        </p>
                        <p style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                            Opens 3 cycles simultaneously for odd semester group
                        </p>
                    </button>

                    {/* EVEN Button */}
                    <button
                        onClick={() => handleActivateGroup('EVEN')}
                        className="glass-card"
                        style={{
                            padding: '1.5rem',
                            border: '2px solid #e5e7eb',
                            borderRadius: '12px',
                            cursor: 'pointer',
                            transition: 'all 0.2s ease',
                            background: '#fff',
                            textAlign: 'left',
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.borderColor = '#3b82f6';
                            e.currentTarget.style.background = 'rgba(59, 130, 246, 0.05)';
                            e.currentTarget.style.transform = 'translateY(-2px)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.borderColor = '#e5e7eb';
                            e.currentTarget.style.background = '#fff';
                            e.currentTarget.style.transform = 'translateY(0)';
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                            <span style={{ fontSize: '2rem' }}>📚</span>
                            <span style={{ fontSize: '1.125rem', fontWeight: 700, color: '#111827' }}>Open EVEN Semesters</span>
                        </div>
                        <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
                            Semesters II, IV, VI
                        </p>
                        <p style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                            Opens 3 cycles simultaneously for even semester group
                        </p>
                    </button>
                </div>
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
                <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
                    <h3 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 600, color: '#6b7280' }}>
                        Status Overview — use buttons above to open groups
                    </h3>
                </div>
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
                                <td>{!c.is_active && c.status !== 'FROZEN' && <button onClick={() => handleActivate(c.id)} className="btn btn-success" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}><CalendarDays size={14} /> Activate (single only)</button>}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
