import { useEffect, useState } from 'react';
import { getDepartmentSummary, getFacultyWorkload, getCurrentUser } from '../api/client';
import { Users, BookOpen, AlertTriangle, CheckCircle, AlertCircle, RefreshCw, GraduationCap } from 'lucide-react';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import WindowStatusBanner from '../components/WindowStatusBanner';

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

interface AssignedSubject {
    course_code: string;
    course_name: string;
    program: string;
    semester: string;
    section: string;
    tch: number;
}

export default function DashboardPage() {
    const [data, setData] = useState<DeptSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [mySubjects, setMySubjects] = useState<AssignedSubject[]>([]);
    const [subjectsLoading, setSubjectsLoading] = useState(true);
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

    const loadMySubjects = async () => {
        setSubjectsLoading(true);
        try {
            const [userRes, workloadRes] = await Promise.all([
                getCurrentUser(),
                getFacultyWorkload(),
            ]);
            const staffId = userRes.data?.staff_id ?? userRes.data?.id;
            const records = workloadRes.data?.records || [];
            const myRecord = records.find((r: any) => r.staff_id === staffId);
            setMySubjects(myRecord?.subjects_assigned || []);
        } catch {
            // Silently fail — panel just won't show data
            setMySubjects([]);
        } finally {
            setSubjectsLoading(false);
        }
    };

    useEffect(() => {
        loadData();
        loadMySubjects();
    }, []);

    if (loading) return (
        <div className="page-container">
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '3rem' }}>Loading dashboard data...</p>
        </div>
    );

    if (error) return (
        <div className="page-container">
            <ToastContainer toasts={toasts} onRemove={removeToast} />
            <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                <AlertCircle size={32} style={{ color: '#dc2626', marginBottom: '0.75rem' }} />
                <p style={{ color: '#dc2626', fontWeight: 600, marginBottom: '0.5rem' }}>{error}</p>
                <button onClick={loadData} className="btn btn-primary" style={{ marginTop: '0.5rem' }}>
                    <RefreshCw size={16} /> Retry
                </button>
            </div>
        </div>
    );

    const totalTCH = mySubjects.reduce((sum, s) => sum + s.tch, 0);

    return (
        <div className="page-container">
            <ToastContainer toasts={toasts} onRemove={removeToast} />
            <div className="page-header">
                <div>
                    <h1 className="page-title">Dashboard</h1>
                    <p className="page-subtitle">Faculty Workload Management System — Overview</p>
                </div>
            </div>

            <WindowStatusBanner />

            {/* My Assigned Subjects Panel */}
            <div className="glass-card" style={{ marginBottom: '1.5rem', overflow: 'hidden' }}>
                <div style={{
                    padding: '1.25rem 1.5rem',
                    borderBottom: '1px solid #e5e7eb',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{
                            padding: '0.5rem',
                            background: '#eff6ff',
                            borderRadius: '0.75rem',
                            color: '#2563eb',
                            display: 'flex',
                        }}>
                            <GraduationCap size={20} strokeWidth={2.5} />
                        </div>
                        <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#111827', margin: 0 }}>
                            My Assigned Subjects
                        </h2>
                    </div>
                    {mySubjects.length > 0 && (
                        <span style={{
                            fontSize: '0.8125rem',
                            fontWeight: 500,
                            color: '#6b7280',
                        }}>
                            {mySubjects.length} subject{mySubjects.length !== 1 ? 's' : ''} · {totalTCH} TCH
                        </span>
                    )}
                </div>

                {subjectsLoading ? (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>
                        Loading assigned subjects...
                    </div>
                ) : mySubjects.length === 0 ? (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>
                        No subjects assigned yet.
                    </div>
                ) : (
                    <div style={{ overflowX: 'auto' }}>
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Program</th>
                                    <th>Semester</th>
                                    <th>Section</th>
                                    <th>Subject Code</th>
                                    <th>Subject Name</th>
                                    <th>TCH</th>
                                </tr>
                            </thead>
                            <tbody>
                                {mySubjects.map((s, i) => (
                                    <tr key={i}>
                                        <td>
                                            <span style={{
                                                background: '#eff6ff',
                                                color: '#2563eb',
                                                padding: '0.125rem 0.625rem',
                                                borderRadius: '6px',
                                                fontSize: '0.8125rem',
                                                fontWeight: 500,
                                            }}>
                                                {s.program}
                                            </span>
                                        </td>
                                        <td style={{ color: '#374151' }}>{s.semester}</td>
                                        <td style={{ color: '#374151' }}>{s.section}</td>
                                        <td style={{ fontFamily: 'monospace', fontWeight: 500, color: '#111827' }}>{s.course_code}</td>
                                        <td style={{ color: '#374151' }}>{s.course_name}</td>
                                        <td style={{ fontWeight: 600, color: '#2563eb' }}>{s.tch}</td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot>
                                <tr>
                                    <td colSpan={5} style={{ textAlign: 'right', fontWeight: 600, color: '#374151' }}>
                                        Total TCH
                                    </td>
                                    <td style={{ fontWeight: 700, color: '#2563eb', fontSize: '1rem' }}>{totalTCH}</td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                )}
            </div>

            {data ? (
                <div className="stat-grid">
                    <div className="glass-card stat-card flex flex-col justify-center">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="p-2.5 bg-blue-50 rounded-xl text-blue-600">
                                <BookOpen size={22} strokeWidth={2.5} />
                            </div>
                            <div className="stat-label !mt-0 !text-sm">Total Offerings</div>
                        </div>
                        <div className="stat-value text-blue-600">{data.total_subject_offerings}</div>
                    </div>

                    <div className="glass-card stat-card flex flex-col justify-center">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="p-2.5 bg-green-50 rounded-xl text-green-600">
                                <CheckCircle size={22} strokeWidth={2.5} />
                            </div>
                            <div className="stat-label !mt-0 !text-sm">Allocated</div>
                        </div>
                        <div className="stat-value text-green-600">{data.allocated_subjects}</div>
                    </div>

                    <div className="glass-card stat-card flex flex-col justify-center">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="p-2.5 bg-amber-50 rounded-xl text-amber-600">
                                <AlertTriangle size={22} strokeWidth={2.5} />
                            </div>
                            <div className="stat-label !mt-0 !text-sm">Unallocated</div>
                        </div>
                        <div className="stat-value text-amber-600">{data.unallocated_subjects}</div>
                    </div>

                    <div className="glass-card stat-card flex flex-col justify-center">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="p-2.5 bg-purple-50 rounded-xl text-purple-600">
                                <Users size={22} strokeWidth={2.5} />
                            </div>
                            <div className="stat-label !mt-0 !text-sm">Faculty</div>
                        </div>
                        <div className="stat-value text-purple-600">{data.total_faculty}</div>
                    </div>

                    <div className="glass-card stat-card flex flex-col justify-center">
                        <div className="stat-label mb-2">Balanced</div>
                        <div className="stat-value text-green-600">{data.faculty_balanced}</div>
                    </div>

                    <div className="glass-card stat-card flex flex-col justify-center">
                        <div className="stat-label mb-2">Overloaded</div>
                        <div className="stat-value text-red-600">{data.faculty_overloaded}</div>
                    </div>

                    <div className="glass-card stat-card flex flex-col justify-center">
                        <div className="stat-label mb-2">Underloaded</div>
                        <div className="stat-value text-amber-500">{data.faculty_underloaded}</div>
                    </div>

                    <div className="glass-card stat-card flex flex-col justify-center">
                        <div className="stat-label mb-2">Avg Workload (TCH)</div>
                        <div className="stat-value text-gray-800">{data.average_workload}</div>
                    </div>
                </div>
            ) : (
                <div className="glass-card p-12 text-center flex flex-col items-center justify-center">
                    <div className="p-4 bg-gray-50 rounded-full mb-4">
                        <AlertCircle size={32} className="text-gray-400" />
                    </div>
                    <p className="text-gray-500 font-medium">No data available. Run allocation first.</p>
                </div>
            )}
        </div>
    );
}
