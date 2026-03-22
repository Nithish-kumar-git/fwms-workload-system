import { Upload, FileSpreadsheet, AlertCircle } from 'lucide-react';
import { useState } from 'react';

export default function CurriculumUploadPage() {
    const [dragOver, setDragOver] = useState(false);

    return (
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem' }}>
            <div style={{ marginBottom: '2rem' }}>
                <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '0.25rem' }}>
                    Curriculum Upload
                </h1>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
                    Upload subject offerings for the current semester.
                </p>
            </div>

            {/* Upload zone */}
            <div
                className="glass-card"
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => { e.preventDefault(); setDragOver(false); }}
                style={{
                    padding: '3rem',
                    textAlign: 'center',
                    border: `2px dashed ${dragOver ? '#7c3aed' : 'rgba(255,255,255,0.1)'}`,
                    borderRadius: 'var(--radius)',
                    transition: 'border-color 0.2s',
                    cursor: 'pointer',
                }}
            >
                <Upload size={40} style={{ margin: '0 auto 1rem', color: 'var(--color-text-muted)' }} />
                <h3 style={{ fontWeight: 700, marginBottom: '0.5rem' }}>
                    Drop CSV or Excel file here
                </h3>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.8125rem', marginBottom: '1rem' }}>
                    or click to browse
                </p>
                <div style={{
                    display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
                    padding: '0.5rem 1rem', borderRadius: 'var(--radius)',
                    background: 'rgba(124, 58, 237, 0.1)', color: '#a78bfa',
                    fontSize: '0.75rem',
                }}>
                    <FileSpreadsheet size={14} />
                    Supports .csv, .xlsx
                </div>
            </div>

            {/* Info */}
            <div style={{
                marginTop: '1.5rem', padding: '1rem', borderRadius: 'var(--radius)',
                background: 'rgba(59, 130, 246, 0.1)', display: 'flex', gap: '0.75rem',
                alignItems: 'flex-start',
            }}>
                <AlertCircle size={18} style={{ color: '#60a5fa', flexShrink: 0, marginTop: '2px' }} />
                <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                    <strong style={{ color: 'var(--color-text-primary)' }}>Expected columns:</strong>
                    <br />
                    Subject Code, Subject Name, Program, Semester, Section, TCH, Shift
                    <br />
                    <span style={{ opacity: 0.7 }}>Backend endpoint will be wired in next phase.</span>
                </div>
            </div>
        </div>
    );
}
