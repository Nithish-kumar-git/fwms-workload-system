import { useEffect, useState } from 'react';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import { 
    Search, 
    ChevronDown, 
    ChevronUp, 
    AlertCircle, 
    RefreshCw,
    Users,
    CheckCircle,
    AlertTriangle,
    XCircle,
    Calendar
} from 'lucide-react';
import { fetchPreferenceOverview, fetchAllocationOverview, getActiveCycle } from '../api/client';
import type { PreferenceOverviewResponse, AllocationOverviewResponse, PreferenceRecord, AllocationRecord } from '../api/client';

type TabType = 'preferences' | 'allocations';

export default function PreferenceReviewDashboardPage() {
    const [activeTab, setActiveTab] = useState<TabType>('preferences');
    const [prefData, setPrefData] = useState<PreferenceOverviewResponse | null>(null);
    const [allocData, setAllocData] = useState<AllocationOverviewResponse | null>(null);
    const [search, setSearch] = useState('');
    const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
    const [loading, setLoading] = useState(true);
    const [activeCycle, setActiveCycle] = useState<{ academic_year: string; semester_id: number } | null>(null);
    const [error, setError] = useState('');
    const { toasts, addToast, removeToast } = useToast();

    const loadActiveCycle = async () => {
        try {
            const res = await getActiveCycle();
            setActiveCycle(res.data);
        } catch (err: any) {
            const msg = err.response?.data?.detail || 'Failed to load active cycle';
            setError(msg);
            addToast(msg, 'error');
        }
    };

    const loadPreferenceData = async () => {
        try {
            const res = await fetchPreferenceOverview();
            setPrefData(res.data);
        } catch (err: any) {
            const msg = err.response?.data?.detail || 'Failed to load preference data';
            setError(msg);
            addToast(msg, 'error');
        }
    };

    const loadAllocationData = async () => {
        try {
            const res = await fetchAllocationOverview();
            setAllocData(res.data);
        } catch (err: any) {
            const msg = err.response?.data?.detail || 'Failed to load allocation data';
            setError(msg);
            addToast(msg, 'error');
        }
    };

    const loadAll = async () => {
        setLoading(true);
        setError('');
        await Promise.all([
            loadActiveCycle(),
            loadPreferenceData(),
            loadAllocationData()
        ]);
        setLoading(false);
    };

    useEffect(() => {
        loadAll();
    }, []);

    const toggleRow = (staffId: number) => {
        const newExpanded = new Set(expandedRows);
        if (newExpanded.has(staffId)) {
            newExpanded.delete(staffId);
        } else {
            newExpanded.add(staffId);
        }
        setExpandedRows(newExpanded);
    };

    const filterPreferences = (records: PreferenceRecord[]) => {
        if (!search) return records;
        const q = search.toLowerCase();
        return records.filter(r => 
            r.emp_code.toLowerCase().includes(q) || 
            r.name.toLowerCase().includes(q)
        );
    };

    const filterAllocations = (records: AllocationRecord[]) => {
        if (!search) return records;
        const q = search.toLowerCase();
        return records.filter(r => 
            r.emp_code.toLowerCase().includes(q) || 
            r.name.toLowerCase().includes(q)
        );
    };

    if (loading) {
        return (
            <div className="page-container">
                <p style={{ color: '#6b7280', textAlign: 'center', padding: '3rem' }}>
                    Loading dashboard data...
                </p>
            </div>
        );
    }

    if (error && !prefData && !allocData) {
        return (
            <div className="page-container">
                <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                    <AlertCircle size={32} style={{ color: '#dc2626', marginBottom: '0.75rem' }} />
                    <p style={{ color: '#dc2626', fontWeight: 600, marginBottom: '0.5rem' }}>{error}</p>
                    <button onClick={loadAll} className="btn btn-primary" style={{ marginTop: '0.5rem' }}>
                        <RefreshCw size={16} /> Retry
                    </button>
                </div>
            </div>
        );
    }

    const filteredPrefRecords = prefData ? filterPreferences(prefData.records) : [];
    const filteredAllocRecords = allocData ? filterAllocations(allocData.records) : [];

    return (
        <div className="page-container">
            <ToastContainer toasts={toasts} onRemove={removeToast} />

            <div className="page-header">
                <div>
                    <h1 className="page-title">Preference Review Dashboard</h1>
                    <p className="page-subtitle">
                        Monitor faculty preference submissions and allocation results
                    </p>
                </div>
            </div>

            {/* Active Cycle Display */}
            {activeCycle ? (
                <div className="glass-card" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <Calendar size={18} style={{ color: '#2563eb' }} />
                    <span style={{ fontSize: '0.9375rem', color: '#374151' }}>
                        <strong style={{ color: '#111827' }}>Active Cycle:</strong> {activeCycle.academic_year} - Semester {activeCycle.semester_id}
                    </span>
                </div>
            ) : (
                <div className="glass-card" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', background: '#fef3c7' }}>
                    <AlertTriangle size={18} style={{ color: '#f59e0b' }} />
                    <span style={{ fontSize: '0.9375rem', color: '#92400e' }}>
                        No active cycle configured
                    </span>
                </div>
            )}

            {/* Tab Navigation */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '2px solid #e5e7eb' }}>
                <button
                    onClick={() => setActiveTab('preferences')}
                    className="btn"
                    style={{
                        background: activeTab === 'preferences' ? '#2563eb' : 'transparent',
                        color: activeTab === 'preferences' ? 'white' : '#6b7280',
                        borderRadius: '8px 8px 0 0',
                        borderBottom: activeTab === 'preferences' ? '2px solid #2563eb' : 'none',
                        marginBottom: '-2px',
                        boxShadow: 'none'
                    }}
                >
                    Preference Submissions
                </button>
                <button
                    onClick={() => setActiveTab('allocations')}
                    className="btn"
                    style={{
                        background: activeTab === 'allocations' ? '#2563eb' : 'transparent',
                        color: activeTab === 'allocations' ? 'white' : '#6b7280',
                        borderRadius: '8px 8px 0 0',
                        borderBottom: activeTab === 'allocations' ? '2px solid #2563eb' : 'none',
                        marginBottom: '-2px',
                        boxShadow: 'none'
                    }}
                >
                    Allocation Results
                </button>
            </div>

            {/* Preference Submissions Tab */}
            {activeTab === 'preferences' && prefData && (
                <>
                    {/* Stats Bar */}
                    <div className="stat-grid" style={{ marginBottom: '1.5rem' }}>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="flex items-center gap-2 mb-2">
                                <Users size={16} className="text-blue-600" strokeWidth={2.5} />
                                <div className="stat-label !mt-0 !text-[13px]">Total Faculty</div>
                            </div>
                            <div className="stat-value text-blue-600">{prefData.total_faculty}</div>
                        </div>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="flex items-center gap-2 mb-2">
                                <CheckCircle size={16} className="text-green-600" strokeWidth={2.5} />
                                <div className="stat-label !mt-0 !text-[13px]">Submitted</div>
                            </div>
                            <div className="stat-value text-green-600">{prefData.submitted_count}</div>
                        </div>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="flex items-center gap-2 mb-2">
                                <AlertTriangle size={16} className="text-amber-500" strokeWidth={2.5} />
                                <div className="stat-label !mt-0 !text-[13px]">Partial</div>
                            </div>
                            <div className="stat-value text-amber-500">{prefData.partial_count}</div>
                        </div>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="flex items-center gap-2 mb-2">
                                <XCircle size={16} className="text-red-600" strokeWidth={2.5} />
                                <div className="stat-label !mt-0 !text-[13px]">Not Submitted</div>
                            </div>
                            <div className="stat-value text-red-600">{prefData.not_submitted_count}</div>
                        </div>
                    </div>

                    {/* Search Box */}
                    <div style={{ marginBottom: '1rem' }}>
                        <div className="relative" style={{ maxWidth: '400px' }}>
                            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                className="form-input pl-9 w-full"
                                placeholder="Search by employee code or name..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                            />
                        </div>
                    </div>

                    {/* Data Table */}
                    <div className="glass-card" style={{ overflow: 'hidden', marginBottom: '1.5rem' }}>
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th style={{ width: '40px' }}></th>
                                    <th>Employee Code</th>
                                    <th>Name</th>
                                    <th>Available Subjects</th>
                                    <th>Submitted Preferences</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredPrefRecords.length === 0 ? (
                                    <tr>
                                        <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>
                                            No faculty records found
                                        </td>
                                    </tr>
                                ) : (
                                    filteredPrefRecords.map((record) => (
                                        <>
                                            <tr
                                                key={record.staff_id}
                                                onClick={() => toggleRow(record.staff_id)}
                                                style={{ cursor: 'pointer' }}
                                            >
                                                <td>
                                                    {expandedRows.has(record.staff_id) ? (
                                                        <ChevronUp size={16} style={{ color: '#6b7280' }} />
                                                    ) : (
                                                        <ChevronDown size={16} style={{ color: '#6b7280' }} />
                                                    )}
                                                </td>
                                                <td style={{ fontFamily: 'monospace', fontWeight: 600, color: '#111827' }}>
                                                    {record.emp_code}
                                                </td>
                                                <td style={{ color: '#111827' }}>{record.name}</td>
                                                <td style={{ color: '#374151' }}>{record.total_subjects}</td>
                                                <td style={{ color: '#374151' }}>{record.submitted_preferences}</td>
                                                <td>
                                                    <span
                                                        className={`badge ${
                                                            record.status === 'Submitted'
                                                                ? 'badge-success'
                                                                : record.status === 'Partial'
                                                                ? 'badge-warning'
                                                                : 'badge-danger'
                                                        }`}
                                                    >
                                                        {record.status}
                                                    </span>
                                                </td>
                                            </tr>
                                            {expandedRows.has(record.staff_id) && (
                                                <tr>
                                                    <td colSpan={6} style={{ background: '#f9fafb', padding: '1rem 1.25rem' }}>
                                                        {record.preferences.length === 0 ? (
                                                            <p style={{ color: '#6b7280', fontSize: '0.875rem', margin: 0 }}>
                                                                No preferences submitted yet
                                                            </p>
                                                        ) : (
                                                            <div style={{ display: 'grid', gap: '0.75rem' }}>
                                                                <div style={{ fontWeight: 600, fontSize: '0.875rem', color: '#111827', marginBottom: '0.25rem' }}>
                                                                    Submitted Preferences:
                                                                </div>
                                                                {record.preferences.map((pref, idx) => (
                                                                    <div
                                                                        key={idx}
                                                                        style={{
                                                                            display: 'grid',
                                                                            gridTemplateColumns: '60px 120px 1fr 100px 80px 80px 60px',
                                                                            gap: '1rem',
                                                                            fontSize: '0.8125rem',
                                                                            padding: '0.5rem',
                                                                            background: 'white',
                                                                            borderRadius: '6px',
                                                                            border: '1px solid #e5e7eb'
                                                                        }}
                                                                    >
                                                                        <span style={{ color: '#6b7280', fontWeight: 500 }}>Rank {pref.preference_rank}</span>
                                                                        <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#111827' }}>
                                                                            {pref.subject_code}
                                                                        </span>
                                                                        <span style={{ color: '#374151' }}>{pref.subject_name}</span>
                                                                        <span style={{ color: '#6b7280' }}>{pref.program}</span>
                                                                        <span style={{ color: '#6b7280' }}>{pref.semester}</span>
                                                                        <span style={{ color: '#6b7280' }}>{pref.section}</span>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </td>
                                                </tr>
                                            )}
                                        </>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </>
            )}

            {/* Allocation Results Tab */}
            {activeTab === 'allocations' && allocData && (
                <>
                    {/* Stats Bar */}
                    <div className="stat-grid" style={{ marginBottom: '1.5rem' }}>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="flex items-center gap-2 mb-2">
                                <Users size={16} className="text-blue-600" strokeWidth={2.5} />
                                <div className="stat-label !mt-0 !text-[13px]">Total Faculty</div>
                            </div>
                            <div className="stat-value text-blue-600">{allocData.total_faculty}</div>
                        </div>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="flex items-center gap-2 mb-2">
                                <AlertCircle size={16} className="text-red-600" strokeWidth={2.5} />
                                <div className="stat-label !mt-0 !text-[13px]">Overloaded</div>
                            </div>
                            <div className="stat-value text-red-600">{allocData.overloaded_count}</div>
                        </div>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="flex items-center gap-2 mb-2">
                                <CheckCircle size={16} className="text-green-600" strokeWidth={2.5} />
                                <div className="stat-label !mt-0 !text-[13px]">Balanced</div>
                            </div>
                            <div className="stat-value text-green-600">{allocData.balanced_count}</div>
                        </div>
                        <div className="stat-card glass-card flex flex-col justify-center">
                            <div className="flex items-center gap-2 mb-2">
                                <AlertTriangle size={16} className="text-amber-500" strokeWidth={2.5} />
                                <div className="stat-label !mt-0 !text-[13px]">Underloaded</div>
                            </div>
                            <div className="stat-value text-amber-500">{allocData.underloaded_count}</div>
                        </div>
                    </div>

                    {/* Search Box */}
                    <div style={{ marginBottom: '1rem' }}>
                        <div className="relative" style={{ maxWidth: '400px' }}>
                            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                className="form-input pl-9 w-full"
                                placeholder="Search by employee code or name..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                            />
                        </div>
                    </div>

                    {/* Data Table */}
                    <div className="glass-card" style={{ overflow: 'hidden', marginBottom: '1.5rem' }}>
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th style={{ width: '40px' }}></th>
                                    <th>Employee Code</th>
                                    <th>Name</th>
                                    <th>Total TCH</th>
                                    <th>Assigned Subjects Count</th>
                                    <th>Workload Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredAllocRecords.length === 0 ? (
                                    <tr>
                                        <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>
                                            No faculty records found
                                        </td>
                                    </tr>
                                ) : (
                                    filteredAllocRecords.map((record) => (
                                        <>
                                            <tr
                                                key={record.staff_id}
                                                onClick={() => toggleRow(record.staff_id)}
                                                style={{ cursor: 'pointer' }}
                                            >
                                                <td>
                                                    {expandedRows.has(record.staff_id) ? (
                                                        <ChevronUp size={16} style={{ color: '#6b7280' }} />
                                                    ) : (
                                                        <ChevronDown size={16} style={{ color: '#6b7280' }} />
                                                    )}
                                                </td>
                                                <td style={{ fontFamily: 'monospace', fontWeight: 600, color: '#111827' }}>
                                                    {record.emp_code}
                                                </td>
                                                <td style={{ color: '#111827' }}>{record.name}</td>
                                                <td style={{ fontWeight: 600, color: '#2563eb' }}>{record.total_tch}</td>
                                                <td style={{ color: '#374151' }}>{record.assigned_subjects_count}</td>
                                                <td>
                                                    <span
                                                        className={`badge ${
                                                            record.workload_status === 'Overloaded'
                                                                ? 'badge-danger'
                                                                : record.workload_status === 'Balanced'
                                                                ? 'badge-success'
                                                                : 'badge-warning'
                                                        }`}
                                                    >
                                                        {record.workload_status}
                                                    </span>
                                                </td>
                                            </tr>
                                            {expandedRows.has(record.staff_id) && (
                                                <tr>
                                                    <td colSpan={6} style={{ background: '#f9fafb', padding: '1rem 1.25rem' }}>
                                                        {record.assigned_subjects.length === 0 ? (
                                                            <p style={{ color: '#6b7280', fontSize: '0.875rem', margin: 0 }}>
                                                                No subjects assigned yet
                                                            </p>
                                                        ) : (
                                                            <div style={{ display: 'grid', gap: '0.75rem' }}>
                                                                <div style={{ fontWeight: 600, fontSize: '0.875rem', color: '#111827', marginBottom: '0.25rem' }}>
                                                                    Assigned Subjects:
                                                                </div>
                                                                {record.assigned_subjects.map((subj, idx) => (
                                                                    <div
                                                                        key={idx}
                                                                        style={{
                                                                            display: 'grid',
                                                                            gridTemplateColumns: '120px 1fr 100px 80px 80px 60px',
                                                                            gap: '1rem',
                                                                            fontSize: '0.8125rem',
                                                                            padding: '0.5rem',
                                                                            background: 'white',
                                                                            borderRadius: '6px',
                                                                            border: '1px solid #e5e7eb'
                                                                        }}
                                                                    >
                                                                        <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#111827' }}>
                                                                            {subj.subject_code}
                                                                        </span>
                                                                        <span style={{ color: '#374151' }}>{subj.subject_name}</span>
                                                                        <span style={{ color: '#6b7280' }}>{subj.program}</span>
                                                                        <span style={{ color: '#6b7280' }}>{subj.semester}</span>
                                                                        <span style={{ color: '#6b7280' }}>{subj.section}</span>
                                                                        <span style={{ fontWeight: 600, color: '#2563eb' }}>TCH: {subj.tch}</span>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </td>
                                                </tr>
                                            )}
                                        </>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </div>
    );
}
