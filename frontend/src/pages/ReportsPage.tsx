import { useEffect, useState } from 'react';
import { getFacultyWorkload, downloadExcel, downloadPdf, getActiveCycle } from '../api/client';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import { FileSpreadsheet, FileText, AlertCircle, RefreshCw } from 'lucide-react';

interface SubjectAssignment {
    course_code: string;
    course_name: string;
    program: string;
    semester: string;
    section: string;
    l: number; t: number; p: number; tch: number;
}

interface FacultyRecord {
    staff_id: number;
    emp_code: string;
    name: string;
    designation: string;
    assigned_tch: number;
    tch_norm: number;
    deviation_hours: number;
    subjects_assigned: SubjectAssignment[];
}

export default function ReportsPage() {
    const [records, setRecords] = useState<FacultyRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [downloading, setDownloading] = useState('');
    const { toasts, addToast, removeToast } = useToast();

    const [error, setError] = useState('');

    const [cyclePrefix, setCyclePrefix] = useState('');

    const loadData = () => {
        setLoading(true);
        setError('');
        getFacultyWorkload()
            .then((r) => setRecords(r.data.records || []))
            .catch((err: any) => {
                const detail = err.response?.data?.detail || 'Failed to load report';
                setError(detail);
                addToast(detail, 'error');
            })
            .finally(() => setLoading(false));

        getActiveCycle()
            .then(r => {
                setCyclePrefix(`${r.data.academic_year}_${r.data.semester_type}_`);
            })
            .catch(err => console.error('No active cycle', err));
    };

    useEffect(() => { loadData(); }, []);

    const handleDownload = async (type: 'excel' | 'pdf') => {
        setDownloading(type);
        try {
            const res = type === 'excel' ? await downloadExcel() : await downloadPdf();
            const url = URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.download = `${cyclePrefix.replace(/-/g, '_')}workload_report.${type === 'excel' ? 'xlsx' : 'pdf'}`;
            link.click();
            URL.revokeObjectURL(url);
            addToast(`${type.toUpperCase()} downloaded`, 'success');
        } catch {
            addToast(`${type.toUpperCase()} download failed`, 'error');
        } finally {
            setDownloading('');
        }
    };

    const getDeviationBadge = (dev: number) => {
        if (dev > 0) return <span className="badge badge-danger">+{dev}</span>;
        if (dev < -2) return <span className="badge badge-warning">{dev}</span>;
        return <span className="badge badge-success">{dev}</span>;
    };

    if (loading) return (
        <div className="page-container">
            <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: '3rem' }}>Loading report data...</p>
        </div>
    );

    if (error) return (
        <div className="page-container">
            <ToastContainer toasts={toasts} onRemove={removeToast} />
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
                    <h1 className="page-title">Reports</h1>
                    <p className="page-subtitle">Faculty workload reports and export</p>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button onClick={() => handleDownload('excel')} className="btn btn-success" disabled={!!downloading}>
                        <FileSpreadsheet size={16} />
                        {downloading === 'excel' ? 'Downloading...' : 'Excel'}
                    </button>
                    <button onClick={() => handleDownload('pdf')} className="btn btn-primary" disabled={!!downloading}>
                        <FileText size={16} />
                        {downloading === 'pdf' ? 'Downloading...' : 'PDF'}
                    </button>
                </div>
            </div>

            {records.map((fac) => (
                <div key={fac.staff_id} className="glass-card" style={{ marginBottom: '1rem', overflow: 'hidden' }}>
                    <div style={{
                        padding: '1rem 1.25rem',
                        borderBottom: '1px solid var(--color-border)',
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    }}>
                        <div>
                            <span style={{ fontWeight: 700 }}>{fac.name}</span>
                            <span style={{ color: 'var(--color-text-muted)', marginLeft: '0.75rem', fontSize: '0.8125rem' }}>
                                {fac.emp_code} · {fac.designation}
                            </span>
                        </div>
                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', fontSize: '0.8125rem' }}>
                            <span>TCH: <strong>{fac.assigned_tch}</strong>/{fac.tch_norm}</span>
                            {getDeviationBadge(fac.deviation_hours)}
                        </div>
                    </div>
                    {fac.subjects_assigned.length > 0 && (
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Code</th><th>Subject</th><th>Program</th>
                                    <th>Sem</th><th>Sec</th><th>L</th><th>T</th><th>P</th><th>TCH</th>
                                </tr>
                            </thead>
                            <tbody>
                                {fac.subjects_assigned.map((s, i) => (
                                    <tr key={i}>
                                        <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{s.course_code}</td>
                                        <td>{s.course_name}</td>
                                        <td>{s.program}</td>
                                        <td>{s.semester}</td>
                                        <td>{s.section}</td>
                                        <td>{s.l}</td><td>{s.t}</td><td>{s.p}</td>
                                        <td><strong>{s.tch}</strong></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            ))}
        </div>
    );
}
