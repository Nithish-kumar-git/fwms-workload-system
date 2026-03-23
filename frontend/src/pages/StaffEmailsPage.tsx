import { useEffect, useState } from 'react';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import Modal from '../components/Modal';
import { Mail, Pencil, Search, AlertCircle, RefreshCw, Save, X } from 'lucide-react';

interface Staff {
    id: number;
    emp_code: string;
    name: string;
    email: string;
    role: string;
    is_active: boolean;
}

export default function StaffEmailsPage() {
    const [staff, setStaff] = useState<Staff[]>([]);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);
    const [editId, setEditId] = useState<number | null>(null);
    const [editEmail, setEditEmail] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const { toasts, addToast, removeToast } = useToast();
    const [error, setError] = useState('');

    const load = async () => {
        setLoading(true);
        setError('');
        try {
            const res = await fetch('/api/admin/staff/emails', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('jwt_token')}` }
            });
            if (!res.ok) throw new Error('Failed to load staff');
            const data = await res.json();
            setStaff(data);
        } catch (err: any) {
            const detail = err.message || 'Failed to load staff';
            setError(detail);
            addToast(detail, 'error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, []);

    const filtered = staff.filter((s) => {
        const q = search.toLowerCase();
        return (
            !q ||
            s.name?.toLowerCase().includes(q) ||
            s.emp_code?.toLowerCase().includes(q) ||
            s.email?.toLowerCase().includes(q)
        );
    });

    const openEdit = (s: Staff) => {
        setEditId(s.id);
        setEditEmail(s.email || '');
    };

    const handleUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editId) return;
        setSubmitting(true);
        try {
            const res = await fetch(`/api/admin/staff/${editId}/email`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
                },
                body: JSON.stringify({ email: editEmail })
            });
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Update failed');
            }
            addToast('Email updated successfully', 'success');
            setEditId(null);
            load();
        } catch (err: any) {
            addToast(err.message || 'Update failed', 'error');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) return (
        <div className="page-container">
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '3rem' }}>Loading staff emails...</p>
        </div>
    );

    if (error) return (
        <div className="page-container">
            <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                <AlertCircle size={32} style={{ color: '#dc2626', marginBottom: '0.75rem' }} />
                <p style={{ color: '#dc2626', fontWeight: 600, marginBottom: '0.5rem' }}>{error}</p>
                <button onClick={load} className="btn btn-primary" style={{ marginTop: '0.5rem' }}>
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
                    <h1 className="page-title">Staff Email Management</h1>
                    <p className="page-subtitle">Update staff emails for Google Sign-In authentication</p>
                </div>
                <div className="relative">
                    <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input className="form-input pl-9 w-64" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} />
                </div>
            </div>

            <Modal isOpen={editId !== null} onClose={() => setEditId(null)} title="Update Email Address">
                <form onSubmit={handleUpdate}>
                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem', display: 'block', marginBottom: '0.5rem' }}>
                            Email Address
                        </label>
                        <input
                            type="email"
                            className="form-input w-full"
                            value={editEmail}
                            onChange={(e) => setEditEmail(e.target.value)}
                            placeholder="faculty@hindustanuniv.ac.in"
                            required
                        />
                        <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.5rem' }}>
                            This email will be used for Google Sign-In authentication
                        </p>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
                        <button type="button" onClick={() => setEditId(null)} className="btn btn-outline" disabled={submitting}>
                            <X size={16} /> Cancel
                        </button>
                        <button type="submit" className="btn btn-primary" disabled={submitting}>
                            <Save size={16} /> {submitting ? 'Updating...' : 'Update Email'}
                        </button>
                    </div>
                </form>
            </Modal>

            <div className="glass-card" style={{ overflow: 'hidden', marginBottom: '1.5rem' }}>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Emp Code</th>
                            <th>Name</th>
                            <th>Current Email</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th style={{ width: '80px' }}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filtered.map((s) => (
                            <tr key={s.id} style={{ opacity: s.is_active ? 1 : 0.5 }}>
                                <td style={{ fontFamily: 'monospace', fontWeight: 600, color: '#111827' }}>{s.emp_code}</td>
                                <td style={{ color: '#111827' }}>{s.name}</td>
                                <td>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <Mail size={14} style={{ color: '#6b7280' }} />
                                        <span style={{ fontSize: '0.8125rem', color: '#374151' }}>{s.email || '—'}</span>
                                    </div>
                                </td>
                                <td>
                                    <span className={`badge ${s.role === 'hod' ? 'badge-danger' : s.role === 'tt_coordinator' ? 'badge-warning' : 'badge-success'}`}>
                                        {s.role === 'hod' ? 'HOD' : s.role === 'tt_coordinator' ? 'Coordinator' : 'Faculty'}
                                    </span>
                                </td>
                                <td>
                                    {s.is_active
                                        ? <span className="badge badge-success">Active</span>
                                        : <span className="badge badge-danger">Inactive</span>
                                    }
                                </td>
                                <td>
                                    <button onClick={() => openEdit(s)} className="btn btn-outline" style={{ padding: '0.25rem 0.5rem' }}>
                                        <Pencil size={14} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
