import { useEffect, useState } from 'react';
import { getAdminAllocations, overrideAllocation, freezeAllocation, unfreezeAllocation } from '../api/client';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import Modal from '../components/Modal';
import { Lock, Unlock, RefreshCw, AlertCircle } from 'lucide-react';

interface Allocation {
    allocation_id: number;
    staff_id: number;
    staff_name: string;
    emp_code: string;
    designation: string;
    subject_offering_id: number;
    subject_code: string;
    subject_name: string;
    section_label: string;
    semester_label: string;
    program_name: string;
    l_assigned: number;
    t_assigned: number;
    p_assigned: number;
    ltp_total: number;
}

interface StaffMember {
    id: number;
    name: string;
    emp_code: string;
    designation: string;
}

type GroupedAllocations = Record<string, Record<string, Record<string, Allocation[]>>>;

function groupAllocations(allocs: Allocation[]): GroupedAllocations {
    const groups: GroupedAllocations = {};
    for (const a of allocs) {
        const prog = a.program_name || 'Unknown';
        const sem = a.semester_label || 'Unknown';
        const sec = a.section_label || 'Unknown';
        if (!groups[prog]) groups[prog] = {};
        if (!groups[prog][sem]) groups[prog][sem] = {};
        if (!groups[prog][sem][sec]) groups[prog][sem][sec] = [];
        groups[prog][sem][sec].push(a);
    }
    return groups;
}

export default function ReviewPage() {
    const [allocations, setAllocations] = useState<Allocation[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selected, setSelected] = useState<Allocation | null>(null);
    const [newStaffId, setNewStaffId] = useState('');
    const [overriding, setOverriding] = useState(false);
    const [staffList, setStaffList] = useState<StaffMember[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedStaffId, setSelectedStaffId] = useState<number | null>(null);
    const { toasts, addToast, removeToast } = useToast();

    const loadData = async () => {
        setLoading(true);
        setError('');
        try {
            const res = await getAdminAllocations();
            setAllocations(res.data.allocations || []);
        } catch (err: any) {
            const detail = err.response?.data?.detail || 'Failed to load allocations';
            setError(detail);
            addToast(detail, 'error');
        } finally {
            setLoading(false);
        }
    };

    const loadStaffList = async () => {
        try {
            const res = await fetch('/api/admin/staff/list', {
                credentials: 'include',
            });
            if (res.ok) {
                const data = await res.json();
                setStaffList(data);
            }
        } catch (err) {
            console.error('Failed to load staff list:', err);
        }
    };

    useEffect(() => { loadData(); loadStaffList(); }, []);

    const handleOverride = async () => {
        if (!selected || !selectedStaffId) {
            addToast('Please select a staff member', 'error');
            return;
        }
        setOverriding(true);
        try {
            console.log(`Overriding allocation ${selected.allocation_id} to staff ${selectedStaffId}`);
            await overrideAllocation(selected.allocation_id, selectedStaffId);
            addToast('Allocation overridden successfully', 'success');
            setSelected(null);
            setSelectedStaffId(null);
            setSearchTerm('');
            loadData();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Override failed', 'error');
        } finally {
            setOverriding(false);
        }
    };

    const handleFreeze = async () => {
        try {
            await freezeAllocation();
            addToast('Allocation frozen', 'success');
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Freeze failed', 'error');
        }
    };

    const handleUnfreeze = async () => {
        try {
            await unfreezeAllocation();
            addToast('Allocation unfrozen', 'success');
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Unfreeze failed', 'error');
        }
    };

    if (loading) return (
        <div className="page-container">
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '3rem' }}>Loading allocations...</p>
        </div>
    );

    if (error) return (
        <div className="page-container">
            <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                <AlertCircle size={32} style={{ color: '#dc2626', marginBottom: '0.75rem' }} />
                <p style={{ color: '#dc2626', fontWeight: 600, marginBottom: '0.5rem' }}>{error}</p>
                <button onClick={loadData} className="btn btn-primary" style={{ marginTop: '0.5rem' }}>
                    <RefreshCw size={16} /> Retry
                </button>
            </div>
        </div>
    );

    const grouped = groupAllocations(allocations);
    const programs = Object.keys(grouped).sort();

    return (
        <div className="page-container">
            <ToastContainer toasts={toasts} onRemove={removeToast} />

            <div className="page-header">
                <div>
                    <h1 className="page-title">Allocation Review</h1>
                    <p className="page-subtitle">
                        {allocations.length} allocations across {programs.length} program{programs.length !== 1 ? 's' : ''}
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button onClick={loadData} className="btn btn-outline"><RefreshCw size={16} />Refresh</button>
                    <button onClick={handleFreeze} className="btn btn-danger"><Lock size={16} />Freeze</button>
                    <button onClick={handleUnfreeze} className="btn btn-success"><Unlock size={16} />Unfreeze</button>
                </div>
            </div>

            {allocations.length === 0 ? (
                <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                    <p style={{ color: '#6b7280' }}>No allocations found. Run the allocation engine first.</p>
                </div>
            ) : (
                programs.map((prog) => {
                    const semesters = Object.keys(grouped[prog]).sort();
                    return (
                        <div key={prog} className="mb-8">
                            <h2 className="text-lg font-semibold mb-4 text-blue-600 pl-1">
                                {prog}
                            </h2>
                            {semesters.map((sem) => {
                                const sections = Object.keys(grouped[prog][sem]).sort();
                                return sections.map((sec) => {
                                    const allocs = grouped[prog][sem][sec];
                                    return (
                                        <div key={`${prog}-${sem}-${sec}`} className="glass-card" style={{ overflow: 'hidden', marginBottom: '1.5rem' }}>
                                            <div style={{ padding: '0.75rem 1.25rem', borderBottom: '1px solid #e5e7eb', background: '#f9fafb', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                                                <span className="badge badge-info">{sem}</span>
                                                <span className="badge badge-warning">{sec}</span>
                                                <span style={{ color: '#6b7280', fontSize: '0.8125rem', fontWeight: 500, marginLeft: 'auto' }}>
                                                    {allocs.length} subject{allocs.length !== 1 ? 's' : ''}
                                                </span>
                                            </div>
                                            <div className="overflow-x-auto">
                                                <table className="data-table">
                                                    <thead>
                                                        <tr>
                                                            <th>Faculty</th><th>Emp Code</th><th>Subject</th>
                                                            <th>L</th><th>T</th><th>P</th><th>LTP</th><th>Action</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {allocs.map((a) => (
                                                            <tr key={a.allocation_id}>
                                                                <td style={{ fontWeight: 500, color: '#111827' }}>{a.staff_name}</td>
                                                                <td style={{ fontFamily: 'monospace', color: '#6b7280', fontSize: '0.8125rem' }}>{a.emp_code}</td>
                                                                <td style={{ color: '#374151' }}>{a.subject_code} <span style={{ color: '#d1d5db', margin: '0 0.25rem' }}>—</span> {a.subject_name}</td>
                                                                <td style={{ color: '#6b7280' }}>{a.l_assigned}</td>
                                                                <td style={{ color: '#6b7280' }}>{a.t_assigned}</td>
                                                                <td style={{ color: '#6b7280' }}>{a.p_assigned}</td>
                                                                <td style={{ fontWeight: 600, color: '#2563eb' }}>{a.ltp_total}</td>
                                                                <td>
                                                                    <button onClick={() => setSelected(a)} className="btn btn-outline text-[13px] py-1 px-3">
                                                                        Override
                                                                    </button>
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    );
                                });
                            })}
                        </div>
                    );
                })
            )}

            {/* Override Modal */}
            <Modal isOpen={!!selected} onClose={() => { setSelected(null); setSearchTerm(''); setSelectedStaffId(null); }} title="Override Allocation">
                {selected && (
                    <div>
                        <p style={{ color: '#6b7280', fontSize: '0.875rem', marginBottom: '1rem' }}>
                            Reassign <strong>{selected.subject_code}</strong> from <strong>{selected.staff_name}</strong> to:
                        </p>
                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                                Select Staff Member
                            </label>
                            <input
                                type="text"
                                className="form-input"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Search by name or emp code..."
                                style={{ width: '100%', marginBottom: '0.5rem' }}
                            />
                            <div style={{ 
                                maxHeight: '200px', 
                                overflowY: 'auto', 
                                border: '1px solid #e5e7eb', 
                                borderRadius: '0.375rem',
                                backgroundColor: '#fff'
                            }}>
                                {staffList
                                    .filter(staff => 
                                        searchTerm === '' ||
                                        staff.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                        staff.emp_code.toLowerCase().includes(searchTerm.toLowerCase())
                                    )
                                    .map(staff => (
                                        <div
                                            key={staff.id}
                                            onClick={() => {
                                                setSelectedStaffId(staff.id);
                                                setSearchTerm(`${staff.emp_code} - ${staff.name}`);
                                            }}
                                            style={{
                                                padding: '0.5rem',
                                                cursor: 'pointer',
                                                backgroundColor: selectedStaffId === staff.id ? '#eff6ff' : 'transparent',
                                                borderBottom: '1px solid #f3f4f6'
                                            }}
                                            onMouseEnter={(e) => {
                                                if (selectedStaffId !== staff.id) {
                                                    e.currentTarget.style.backgroundColor = '#f9fafb';
                                                }
                                            }}
                                            onMouseLeave={(e) => {
                                                if (selectedStaffId !== staff.id) {
                                                    e.currentTarget.style.backgroundColor = 'transparent';
                                                }
                                            }}
                                        >
                                            <div style={{ fontWeight: 500, fontSize: '0.875rem' }}>
                                                {staff.emp_code} - {staff.name}
                                            </div>
                                            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                                                {staff.designation}
                                            </div>
                                        </div>
                                    ))
                                }
                            </div>
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                            <button onClick={() => { setSelected(null); setSearchTerm(''); setSelectedStaffId(null); }} className="btn btn-outline">Cancel</button>
                            <button onClick={handleOverride} className="btn btn-primary" disabled={overriding || !selectedStaffId}>
                                {overriding ? 'Overriding...' : 'Confirm Override'}
                            </button>
                        </div>
                    </div>
                )}
            </Modal>
        </div>
    );
}
