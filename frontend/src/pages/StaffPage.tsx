import { useEffect, useState } from 'react';
import { getStaffList, createStaff, updateStaff, deactivateStaff } from '../api/client';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import Modal from '../components/Modal';
import { UserPlus, Pencil, UserX, Search, AlertCircle, RefreshCw, Shield, Mail } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Staff {
    id: number;
    emp_code: string;
    name: string;
    email: string;
    designation: string;
    shift: string;
    tch_norm: number;
    role: string;
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
    shift: 'SHIFT1', tch_norm: 40, role: 'faculty', is_class_teacher: false,
    ct_program: '', ct_section: '', ct_semester: '', ct_shift: '',
};

export default function StaffPage() {
    const navigate = useNavigate();
    const [staff, setStaff] = useState<Staff[]>([]);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);
    const [showAdd, setShowAdd] = useState(false);
    const [editId, setEditId] = useState<number | null>(null);
    const [form, setForm] = useState(EMPTY_FORM);
    const [submitting, setSubmitting] = useState(false);
    const { toasts, addToast, removeToast } = useToast();

    const [error, setError] = useState('');
    
    // Role assignment modal
    const [showRoleModal, setShowRoleModal] = useState(false);
    const [selectedStaffId, setSelectedStaffId] = useState<number | null>(null);
    const [selectedRole, setSelectedRole] = useState('faculty');

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
            tch_norm: s.tch_norm || 16, role: s.role || 'faculty',
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
                role: form.role,
                is_coordinator: form.role !== 'faculty',
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

    const openRoleModal = (staffId: number, currentRole: string) => {
        setSelectedStaffId(staffId);
        setSelectedRole(currentRole);
        setShowRoleModal(true);
    };

    const handleRoleUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedStaffId) return;
        setSubmitting(true);
        try {
            const res = await fetch(`/api/admin/staff/${selectedStaffId}/role`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
                },
                body: JSON.stringify({ role: selectedRole })
            });
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Role update failed');
            }
            addToast('Role updated successfully', 'success');
            setShowRoleModal(false);
            load();
        } catch (err: any) {
            addToast(err.message || 'Role update failed', 'error');
        } finally {
            setSubmitting(false);
        }
    };

    const setField = (key: string, val: unknown) => setForm((prev) => ({ ...prev, [key]: val }));

    const formFields = (
        <div className="flex flex-col gap-5">
            <div className="flex flex-wrap gap-4">
                <div className="flex-1 min-w-[120px]">
                    <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem', display: 'block', marginBottom: '0.25rem' }}>Emp Code</label>
                    <input className="form-input w-full" value={form.emp_code} onChange={(e) => setField('emp_code', e.target.value)} disabled={!!editId} />
                </div>
                <div className="flex-[2] min-w-[200px]">
                    <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem', display: 'block', marginBottom: '0.25rem' }}>Name</label>
                    <input className="form-input w-full" value={form.name} onChange={(e) => setField('name', e.target.value)} />
                </div>
                <div className="flex-[2] min-w-[200px]">
                    <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem', display: 'block', marginBottom: '0.25rem' }}>Email</label>
                    <input className="form-input w-full" type="email" value={form.email} onChange={(e) => setField('email', e.target.value)} disabled={!!editId} />
                </div>
            </div>
            <div className="flex flex-wrap gap-4 items-end">
                <div className="w-48">
                    <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem', display: 'block', marginBottom: '0.25rem' }}>Designation</label>
                    <select className="form-select w-full" value={form.designation} onChange={(e) => setField('designation', e.target.value)}>
                        <option>Assistant Professor</option>
                        <option>Associate Professor</option>
                        <option>Professor</option>
                        <option>HOD</option>
                    </select>
                </div>
                <div className="w-36">
                    <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem', display: 'block', marginBottom: '0.25rem' }}>Shift</label>
                    <select className="form-select w-full" value={form.shift} onChange={(e) => setField('shift', e.target.value)}>
                        <option>SHIFT1</option>
                        <option>SHIFT2</option>
                        <option>SHIFT1+SHIFT2</option>
                    </select>
                </div>
                <div className="w-24">
                    <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem', display: 'block', marginBottom: '0.25rem' }}>TCH</label>
                    <input className="form-input w-full" type="number" value={form.tch_norm} onChange={(e) => setField('tch_norm', +e.target.value)} />
                </div>
                <div className="flex items-center gap-6 pb-2 ml-2">
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                        <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280' }}>Role</span>
                        <select className="form-select" value={form.role} onChange={(e) => setField('role', e.target.value)}>
                            <option value="faculty">Faculty</option>
                            <option value="tt_coordinator">TT Coordinator</option>
                            <option value="hod">HOD</option>
                        </select>
                    </label>
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">
                        <input type="checkbox" className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" checked={form.is_class_teacher} onChange={(e) => setField('is_class_teacher', e.target.checked)} />
                        Class Teacher
                    </label>
                </div>
            </div>
            {form.is_class_teacher && (
                <div className="flex flex-wrap gap-4 pt-4 border-t border-gray-100">
                    <div className="flex-1 min-w-[100px]"><label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem', display: 'block', marginBottom: '0.25rem' }}>Program</label><input className="form-input w-full" value={form.ct_program} onChange={(e) => setField('ct_program', e.target.value)} /></div>
                    <div className="flex-1 min-w-[100px]"><label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem', display: 'block', marginBottom: '0.25rem' }}>Section</label><input className="form-input w-full" value={form.ct_section} onChange={(e) => setField('ct_section', e.target.value)} /></div>
                    <div className="flex-1 min-w-[100px]"><label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem', display: 'block', marginBottom: '0.25rem' }}>Semester</label><input className="form-input w-full" value={form.ct_semester} onChange={(e) => setField('ct_semester', e.target.value)} /></div>
                    <div className="flex-1 min-w-[100px]"><label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem', display: 'block', marginBottom: '0.25rem' }}>Shift</label><input className="form-input w-full" value={form.ct_shift} onChange={(e) => setField('ct_shift', e.target.value)} /></div>
                </div>
            )}
            <div className="pt-4 border-t border-gray-100 mt-2 flex justify-end">
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                    {submitting ? 'Saving...' : editId ? 'Update Faculty' : 'Create Faculty'}
                </button>
            </div>
        </div>
    );

    if (loading) return (
        <div className="page-container">
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '3rem' }}>Loading staff records...</p>
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
                    <h1 className="page-title">Staff Management</h1>
                    <p className="page-subtitle">{staff.length} faculty members</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input className="form-input pl-9 w-64" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} />
                    </div>
                    <button onClick={() => navigate('/hod/staff-emails')} className="btn btn-outline">
                        <Mail size={16} /> Manage Emails
                    </button>
                    <button onClick={openAdd} className="btn btn-primary">
                        <UserPlus size={16} /> Add Faculty
                    </button>
                </div>
            </div>

            <Modal isOpen={showAdd} onClose={() => setShowAdd(false)} title="Add Faculty">
                <form onSubmit={handleAdd}>{formFields}</form>
            </Modal>

            <Modal isOpen={editId !== null} onClose={() => setEditId(null)} title="Edit Faculty">
                <form onSubmit={handleEdit}>{formFields}</form>
            </Modal>

            <Modal isOpen={showRoleModal} onClose={() => setShowRoleModal(false)} title="Assign Role">
                <form onSubmit={handleRoleUpdate}>
                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', paddingLeft: '0.25rem', display: 'block', marginBottom: '0.5rem' }}>
                            Select Role
                        </label>
                        <select
                            className="form-select w-full"
                            value={selectedRole}
                            onChange={(e) => setSelectedRole(e.target.value)}
                        >
                            <option value="faculty">Faculty</option>
                            <option value="tt_coordinator">TT Coordinator</option>
                            <option value="hod">HOD</option>
                        </select>
                        <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.5rem' }}>
                            Coordinators can manage windows, allocations, and reports. HODs have full system access.
                        </p>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
                        <button type="button" onClick={() => setShowRoleModal(false)} className="btn btn-outline" disabled={submitting}>
                            Cancel
                        </button>
                        <button type="submit" className="btn btn-primary" disabled={submitting}>
                            <Shield size={16} /> {submitting ? 'Updating...' : 'Update Role'}
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
                                <td style={{ fontFamily: 'monospace', fontWeight: 600, color: '#111827' }}>{s.emp_code}</td>
                                <td style={{ color: '#111827' }}>{s.name}</td>
                                <td style={{ fontSize: '0.8125rem', color: '#6b7280' }}>{s.email}</td>
                                <td>{s.designation}</td>
                                <td><span className="badge badge-info">{s.shift}</span></td>
                                <td>{s.tch_norm}</td>
                                <td>
                                    <span className={`badge ${s.role === 'hod' ? 'badge-danger' : s.role === 'tt_coordinator' ? 'badge-warning' : 'badge-success'}`} style={{ marginRight: '0.25rem' }}>
                                        {s.role === 'hod' ? 'HOD' : s.role === 'tt_coordinator' ? 'Coordinator' : 'Faculty'}
                                    </span>
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
                                        <button onClick={() => openEdit(s)} className="btn btn-outline" style={{ padding: '0.25rem 0.5rem' }} title="Edit">
                                            <Pencil size={14} />
                                        </button>
                                        <button onClick={() => openRoleModal(s.id, s.role)} className="btn btn-outline" style={{ padding: '0.25rem 0.5rem' }} title="Assign Role">
                                            <Shield size={14} />
                                        </button>
                                        {s.is_active && (
                                            <button onClick={() => handleDeactivate(s.id, s.name)} className="btn btn-danger" style={{ padding: '0.25rem 0.5rem' }} title="Deactivate">
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
