import { useEffect, useState } from 'react';
import { getStaffList, createStaff, updateStaff, deactivateStaff } from '../api/client';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import Modal from '../components/Modal';
import { UserPlus, Pencil, UserX, Search, AlertCircle, RefreshCw } from 'lucide-react';

interface Staff {
    id: number;
    emp_code: string;
    name: string;
    email: string;
    designation: string;
    shift: string;
    tch_norm: number;
    is_coordinator: boolean;
    is_active: boolean;
    is_class_teacher: boolean;
    ct_program: string | null;
    ct_section: string | null;
    ct_semester: string | null;
    ct_shift: string | null;
}

const EMPTY_FORM = {
    emp_code: '', name: '', email: '', designation: 'Assistant Professor',
    shift: 'SHIFT1', tch_norm: 16, is_coordinator: false, is_class_teacher: false,
    ct_program: '', ct_section: '', ct_semester: '', ct_shift: '',
};

export default function StaffPage() {
    const [staff, setStaff] = useState<Staff[]>([]);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);
    const [showAdd, setShowAdd] = useState(false);
    const [editId, setEditId] = useState<number | null>(null);
    const [form, setForm] = useState(EMPTY_FORM);
    const [submitting, setSubmitting] = useState(false);
    const { toasts, addToast, removeToast } = useToast();

    const [error, setError] = useState('');

    const load = () => {
        setLoading(true);
        setError('');
        getStaffList()
            .then((r) => setStaff(r.data))
            .catch((err: any) => {
                const detail = err.response?.data?.detail || 'Failed to load staff';
                setError(detail);
                addToast(detail, 'error');
            })
            .finally(() => setLoading(false));
    };

    useEffect(() => { load(); }, []);

    const filtered = staff.filter((s) => {
        const q = search.toLowerCase();
        return (
            !q ||
            s.name?.toLowerCase().includes(q) ||
            s.emp_code?.toLowerCase().includes(q) ||
            s.email?.toLowerCase().includes(q) ||
            s.designation?.toLowerCase().includes(q)
        );
    });

    const openAdd = () => { setForm(EMPTY_FORM); setShowAdd(true); };
    const openEdit = (s: Staff) => {
        setForm({
            emp_code: s.emp_code || '', name: s.name || '', email: s.email || '',
            designation: s.designation || '', shift: s.shift || 'SHIFT1',
            tch_norm: s.tch_norm || 16, is_coordinator: s.is_coordinator,
            is_class_teacher: s.is_class_teacher,
            ct_program: s.ct_program || '', ct_section: s.ct_section || '',
            ct_semester: s.ct_semester || '', ct_shift: s.ct_shift || '',
        });
        setEditId(s.id);
    };

    const handleAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            await createStaff({
                ...form,
                ct_program: form.ct_program || undefined,
                ct_section: form.ct_section || undefined,
                ct_semester: form.ct_semester || undefined,
                ct_shift: form.ct_shift || undefined,
            });
            addToast('Faculty created', 'success');
            setShowAdd(false);
            load();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Create failed', 'error');
        } finally { setSubmitting(false); }
    };

    const handleEdit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editId) return;
        setSubmitting(true);
        try {
            await updateStaff(editId, {
                name: form.name, designation: form.designation,
                shift: form.shift, tch_norm: form.tch_norm,
                is_coordinator: form.is_coordinator,
                is_class_teacher: form.is_class_teacher,
                ct_program: form.ct_program || null,
                ct_section: form.ct_section || null,
                ct_semester: form.ct_semester || null,
                ct_shift: form.ct_shift || null,
            });
            addToast('Faculty updated', 'success');
            setEditId(null);
            load();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Update failed', 'error');
        } finally { setSubmitting(false); }
    };

    const handleDeactivate = async (id: number, name: string) => {
        if (!confirm(`Deactivate ${name}?`)) return;
        try {
            await deactivateStaff(id);
            addToast(`${name} deactivated`, 'success');
            load();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Deactivation failed', 'error');
        }
    };

    const setField = (key: string, val: unknown) => setForm((prev) => ({ ...prev, [key]: val }));

    const formFields = (
        <div className="flex flex-col gap-5">
            <div className="flex flex-wrap gap-4">
                <div className="flex-1 min-w-[120px]">
                    <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1 mb-1 block">Emp Code</label>
                    <input className="form-input w-full" value={form.emp_code} onChange={(e) => setField('emp_code', e.target.value)} disabled={!!editId} />
                </div>
                <div className="flex-[2] min-w-[200px]">
                    <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1 mb-1 block">Name</label>
                    <input className="form-input w-full" value={form.name} onChange={(e) => setField('name', e.target.value)} />
                </div>
                <div className="flex-[2] min-w-[200px]">
                    <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1 mb-1 block">Email</label>
                    <input className="form-input w-full" type="email" value={form.email} onChange={(e) => setField('email', e.target.value)} disabled={!!editId} />
                </div>
            </div>
            <div className="flex flex-wrap gap-4 items-end">
                <div className="w-48">
                    <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1 mb-1 block">Designation</label>
                    <select className="form-select w-full" value={form.designation} onChange={(e) => setField('designation', e.target.value)}>
                        <option>Assistant Professor</option>
                        <option>Associate Professor</option>
                        <option>Professor</option>
                        <option>HOD</option>
                    </select>
                </div>
                <div className="w-36">
                    <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1 mb-1 block">Shift</label>
                    <select className="form-select w-full" value={form.shift} onChange={(e) => setField('shift', e.target.value)}>
                        <option>SHIFT1</option>
                        <option>SHIFT2</option>
                        <option>SHIFT1+SHIFT2</option>
                    </select>
                </div>
                <div className="w-24">
                    <label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1 mb-1 block">TCH</label>
                    <input className="form-input w-full" type="number" value={form.tch_norm} onChange={(e) => setField('tch_norm', +e.target.value)} />
                </div>
                <div className="flex items-center gap-6 pb-2 ml-2">
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-200 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-white/20 dark:bg-black/20" checked={form.is_coordinator} onChange={(e) => setField('is_coordinator', e.target.checked)} />
                        Coordinator
                    </label>
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-200 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-white/20 dark:bg-black/20" checked={form.is_class_teacher} onChange={(e) => setField('is_class_teacher', e.target.checked)} />
                        Class Teacher
                    </label>
                </div>
            </div>
            {form.is_class_teacher && (
                <div className="flex flex-wrap gap-4 pt-4 border-t border-black/5 dark:border-white/5">
                    <div className="flex-1 min-w-[100px]"><label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1 mb-1 block">Program</label><input className="form-input w-full" value={form.ct_program} onChange={(e) => setField('ct_program', e.target.value)} /></div>
                    <div className="flex-1 min-w-[100px]"><label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1 mb-1 block">Section</label><input className="form-input w-full" value={form.ct_section} onChange={(e) => setField('ct_section', e.target.value)} /></div>
                    <div className="flex-1 min-w-[100px]"><label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1 mb-1 block">Semester</label><input className="form-input w-full" value={form.ct_semester} onChange={(e) => setField('ct_semester', e.target.value)} /></div>
                    <div className="flex-1 min-w-[100px]"><label className="text-[13px] font-medium text-gray-500 dark:text-gray-400 pl-1 mb-1 block">Shift</label><input className="form-input w-full" value={form.ct_shift} onChange={(e) => setField('ct_shift', e.target.value)} /></div>
                </div>
            )}
            <div className="pt-4 border-t border-black/5 dark:border-white/5 mt-2 flex justify-end">
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                    {submitting ? 'Saving...' : editId ? 'Update Faculty' : 'Create Faculty'}
                </button>
            </div>
        </div>
    );

    if (loading) return (
        <div className="page-container">
            <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: '3rem' }}>Loading staff records...</p>
        </div>
    );

    if (error) return (
        <div className="page-container">
            <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                <AlertCircle size={32} style={{ color: '#f87171', marginBottom: '0.75rem' }} />
                <p style={{ color: '#f87171', fontWeight: 600, marginBottom: '0.5rem' }}>{error}</p>
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
                    <h1 className="page-title">Staff Management</h1>
                    <p className="page-subtitle">{staff.length} faculty members</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input className="form-input pl-9 w-64" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} />
                    </div>
                    <button onClick={openAdd} className="btn btn-primary drop-shadow-sm">
                        <UserPlus size={16} /> Add Faculty
                    </button>
                </div>
            </div>

            {/* Add Modal */}
            <Modal isOpen={showAdd} onClose={() => setShowAdd(false)} title="Add Faculty">
                <form onSubmit={handleAdd}>{formFields}</form>
            </Modal>

            {/* Edit Modal */}
            <Modal isOpen={editId !== null} onClose={() => setEditId(null)} title="Edit Faculty">
                <form onSubmit={handleEdit}>{formFields}</form>
            </Modal>

            {/* Staff Table */}
            <div className="glass-panel overflow-hidden mb-8">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Emp Code</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Designation</th>
                            <th>Shift</th>
                            <th>TCH</th>
                            <th>Roles</th>
                            <th>Status</th>
                            <th style={{ width: '100px' }}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filtered.map((s) => (
                            <tr key={s.id} style={{ opacity: s.is_active ? 1 : 0.5 }}>
                                <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{s.emp_code}</td>
                                <td>{s.name}</td>
                                <td style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>{s.email}</td>
                                <td>{s.designation}</td>
                                <td><span className="badge badge-info">{s.shift}</span></td>
                                <td>{s.tch_norm}</td>
                                <td>
                                    {s.is_coordinator && <span className="badge badge-warning" style={{ marginRight: '0.25rem' }}>Coord</span>}
                                    {s.is_class_teacher && <span className="badge badge-info">CT</span>}
                                </td>
                                <td>
                                    {s.is_active
                                        ? <span className="badge badge-success">Active</span>
                                        : <span className="badge badge-danger">Inactive</span>
                                    }
                                </td>
                                <td>
                                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                                        <button onClick={() => openEdit(s)} className="btn btn-outline" style={{ padding: '0.25rem 0.5rem' }}>
                                            <Pencil size={14} />
                                        </button>
                                        {s.is_active && (
                                            <button onClick={() => handleDeactivate(s.id, s.name)} className="btn btn-danger" style={{ padding: '0.25rem 0.5rem' }}>
                                                <UserX size={14} />
                                            </button>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
