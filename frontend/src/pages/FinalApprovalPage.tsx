import { CheckCircle, XCircle, AlertCircle, FileSpreadsheet, FileText, Lock, RefreshCw, ShieldCheck } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';
import { getPipelineStatus, approveWorkload, downloadMasterWorkload, downloadWorkloadPdf } from '../api/client';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';

interface PipelineStatus {
    preferences_submitted: boolean;
    allocation_complete: boolean;
    hod_approved: boolean;
    snapshot_id: number | null;
    academic_year: string | null;
    semester_type: string | null; // Legacy field (may still be returned by backend)
    semester_id: number | null; // New field
    is_locked: boolean;
}

export default function FinalApprovalPage() {
    const [status, setStatus] = useState<PipelineStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [approving, setApproving] = useState(false);
    const [downloading, setDownloading] = useState('');
    const { toasts, addToast, removeToast } = useToast();

    const loadStatus = useCallback(async () => {
        setLoading(true);
        try {
            const res = await getPipelineStatus();
            setStatus(res.data);
        } catch {
            addToast('Failed to load pipeline status', 'error');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadStatus(); }, [loadStatus]);

    const handleApprove = async () => {
        if (!confirm('This action will FREEZE the workload. No more changes will be allowed.\n\nContinue?')) return;
        setApproving(true);
        try {
            const res = await approveWorkload();
            if (res.data?.already_existed) {
                addToast('Workload was already approved and frozen.', 'info');
            } else {
                addToast('Workload approved and frozen!', 'success');
            }
            await loadStatus();
        } catch (err: any) {
            const detail = err.response?.data?.detail || 'Approval failed';
            addToast(detail, 'error');
        } finally {
            setApproving(false);
        }
    };

    const handleDownload = async (type: 'excel' | 'pdf') => {
        setDownloading(type);
        try {
            const res = type === 'excel' ? await downloadMasterWorkload() : await downloadWorkloadPdf();
            const url = URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            const ay = status?.academic_year || 'workload';
            const st = status?.semester_id ? `Sem${status.semester_id}` : (status?.semester_type || '');
            link.download = type === 'excel'
                ? `Master_Workload_${ay}_${st}.xlsx`
                : `Master_Workload_${ay}_${st}.pdf`;
            link.click();
            URL.revokeObjectURL(url);
            addToast(`${type.toUpperCase()} downloaded`, 'success');
        } catch (err: any) {
            const detail = err.response?.data?.detail || `${type.toUpperCase()} download failed`;
            addToast(detail, 'error');
        } finally {
            setDownloading('');
        }
    };

    const StageRow = ({ label, done, locked }: { label: string; done: boolean; locked?: boolean }) => (
        <div style={{
            display: 'flex', alignItems: 'center', gap: '0.75rem',
            padding: '0.75rem 1rem', borderRadius: '8px',
            background: done
                ? 'linear-gradient(135deg, rgba(16,185,129,0.15), rgba(16,185,129,0.05))'
                : 'rgba(255,255,255,0.03)',
            border: done ? '1px solid rgba(16,185,129,0.3)' : '1px solid rgba(255,255,255,0.08)',
        }}>
            {done
                ? <CheckCircle size={20} style={{ color: '#10b981', flexShrink: 0 }} />
                : locked
                    ? <Lock size={20} style={{ color: '#f59e0b', flexShrink: 0 }} />
                    : <XCircle size={20} style={{ color: '#6b7280', flexShrink: 0 }} />
            }
            <span style={{ fontWeight: 600, color: done ? '#10b981' : '#9ca3af' }}>{label}</span>
        </div>
    );

    if (loading) return (
        <div className="page-container">
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '3rem' }}>Loading pipeline status...</p>
        </div>
    );

    return (
        <div className="page-container">
            <ToastContainer toasts={toasts} onRemove={removeToast} />

            <div className="page-header">
                <div>
                    <h1 className="page-title">Final Approval</h1>
                    <p className="page-subtitle">
                        {status?.academic_year} {status?.semester_id ? `Semester ${status.semester_id}` : status?.semester_type}
                    </p>
                </div>
                <button onClick={loadStatus} className="btn btn-outline" disabled={loading}>
                    <RefreshCw size={16} /> Refresh
                </button>
            </div>

            {/* Pipeline Status */}
            <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                <h3 style={{ fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <ShieldCheck size={20} /> Pipeline Status
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <StageRow label="Faculty Preferences Submitted" done={status?.preferences_submitted ?? false} />
                    <StageRow label="Coordinator Allocation Complete" done={status?.allocation_complete ?? false} />
                    <StageRow
                        label={status?.is_locked ? "HOD Approved & Frozen" : "HOD Approval"}
                        done={status?.hod_approved ?? false}
                        locked={status?.is_locked}
                    />
                </div>
            </div>

            {/* Approval Action */}
            {!status?.hod_approved && (
                <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                    <h3 style={{ fontWeight: 700, marginBottom: '0.75rem' }}>Approve & Freeze</h3>
                    <p style={{ color: '#9ca3af', fontSize: '0.875rem', marginBottom: '1rem' }}>
                        Once approved, all data is frozen into an immutable snapshot.
                        No further changes will be allowed to preferences or allocations.
                    </p>
                    {!status?.allocation_complete && (
                        <div style={{
                            padding: '0.75rem', borderRadius: '8px',
                            background: 'rgba(239,68,68,0.1)',
                            border: '1px solid rgba(239,68,68,0.3)',
                            color: '#f87171', fontSize: '0.8125rem', marginBottom: '1rem',
                            display: 'flex', alignItems: 'center', gap: '0.5rem',
                        }}>
                            <AlertCircle size={16} />
                            Allocation must be complete before approval. Check for unassigned subjects.
                        </div>
                    )}
                    <button
                        className="btn btn-primary"
                        disabled={!status?.allocation_complete || approving}
                        onClick={handleApprove}
                        style={{
                            padding: '0.75rem 2rem', fontSize: '0.875rem', gap: '0.5rem',
                            background: status?.allocation_complete
                                ? 'linear-gradient(135deg, #059669, #10b981)' : undefined,
                            border: 'none', opacity: status?.allocation_complete ? 1 : 0.5,
                        }}
                    >
                        <Lock size={18} />
                        {approving ? 'Freezing...' : 'Approve & Freeze Workload'}
                    </button>
                </div>
            )}

            {/* Frozen confirmation */}
            {status?.hod_approved && (
                <div className="glass-card" style={{
                    padding: '1.5rem', marginBottom: '1.5rem',
                    background: 'linear-gradient(135deg, rgba(16,185,129,0.1), rgba(6,78,59,0.05))',
                    border: '1px solid rgba(16,185,129,0.4)',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                        <Lock size={20} style={{ color: '#10b981' }} />
                        <span style={{ fontWeight: 700, color: '#10b981', fontSize: '1rem' }}>
                            Workload Frozen
                        </span>
                    </div>
                    <p style={{ color: '#9ca3af', fontSize: '0.8125rem' }}>
                        Snapshot #{status.snapshot_id} — data is locked and immutable.
                    </p>
                </div>
            )}

            {/* Download buttons */}
            <div className="glass-card" style={{ padding: '1.5rem' }}>
                <h3 style={{ fontWeight: 700, marginBottom: '1rem' }}>Export</h3>
                {!status?.hod_approved && (
                    <p style={{ color: '#f59e0b', fontSize: '0.8125rem', marginBottom: '1rem' }}>
                        Downloads are disabled until the workload is approved and frozen.
                    </p>
                )}
                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                    <button
                        className="btn btn-success"
                        disabled={!status?.hod_approved || !!downloading}
                        onClick={() => handleDownload('excel')}
                        style={{ padding: '0.75rem 1.5rem', gap: '0.5rem' }}
                    >
                        <FileSpreadsheet size={18} />
                        {downloading === 'excel' ? 'Generating...' : 'Master Workload Excel'}
                    </button>
                    <button
                        className="btn btn-primary"
                        disabled={!status?.hod_approved || !!downloading}
                        onClick={() => handleDownload('pdf')}
                        style={{ padding: '0.75rem 1.5rem', gap: '0.5rem' }}
                    >
                        <FileText size={18} />
                        {downloading === 'pdf' ? 'Generating...' : 'Workload PDF'}
                    </button>
                </div>
            </div>
        </div>
    );
}
