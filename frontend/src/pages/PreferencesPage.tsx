import { useEffect, useState, useMemo } from 'react';
import { getMyPreferences, submitPreference, deletePreference, getPreferenceStatus, getPrefWindowStatus, getSubjectSummary } from '../api/client';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import { Clock, AlertCircle, RefreshCw, Search, Filter, BookOpen, CheckCircle2, XCircle, X } from 'lucide-react';

interface Preference {
    id: number;
    preference_number: number;
    subject_offering_id?: number;
    subject_code: string;
    subject_name: string;
    program: string;
    semester: string;
    section: string;
    tch: number;
    curriculum_year?: string;
}

interface PrefStatus {
    total_submitted: number;
    remaining: number;
    is_complete: boolean;
}

interface SubjectOffering {
    subject_offering_id: number;
    course_code: string;
    course_name: string;
    program: string;
    semester: string;
    section: string;
    shift: number;
    tch: number;
    allocated: boolean;
    faculty_name: string | null;
    curriculum_year: string;
}

export default function PreferencesPage() {
    const [preferences, setPreferences] = useState<Preference[]>([]);
    const [status, setStatus] = useState<PrefStatus | null>(null);
    const [windowOpen, setWindowOpen] = useState(true);
    const [windowRemaining, setWindowRemaining] = useState(0);
    const [loading, setLoading] = useState(true);
    const [offeringId, setOfferingId] = useState('');
    const [prefNum, setPrefNum] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const { toasts, addToast, removeToast } = useToast();
    const [error, setError] = useState('');
    const [duplicateError, setDuplicateError] = useState('');

    const [offerings, setOfferings] = useState<SubjectOffering[]>([]);
    const [offeringsLoading, setOfferingsLoading] = useState(true);
    const [filterProgram, setFilterProgram] = useState('');
    const [filterSemester, setFilterSemester] = useState('');
    const [searchText, setSearchText] = useState('');
    const [showInfoBanner, setShowInfoBanner] = useState(true);

    // ── IDs and pref numbers already used ──
    const usedOfferingIds = useMemo(
        () => new Set(preferences.map((p) => p.subject_offering_id)),
        [preferences]
    );
    const usedPrefNumbers = useMemo(
        () => new Set(preferences.map((p) => p.preference_number)),
        [preferences]
    );
    const availablePrefNumbers = useMemo(
        () => [1, 2, 3, 4, 5].filter((n) => !usedPrefNumbers.has(n)),
        [usedPrefNumbers]
    );

    // ── Selected offering details (for the summary chip) ──
    const selectedOffering = useMemo(
        () => offerings.find((o) => String(o.subject_offering_id) === offeringId) || null,
        [offerings, offeringId]
    );

    const loadData = async () => {
        setError('');
        try {
            const [prefsRes, statusRes, winRes] = await Promise.all([
                getMyPreferences(),
                getPreferenceStatus(),
                getPrefWindowStatus(),
            ]);
            setPreferences(Array.isArray(prefsRes.data) ? prefsRes.data : prefsRes.data.preferences || []);
            setStatus(statusRes.data);
            setWindowOpen(winRes.data.is_open);
            setWindowRemaining(winRes.data.remaining_seconds || 0);
        } catch (err: any) {
            const status = err.response?.status;
            const detail = status === 403 
                ? 'Session expired - please login again'
                : err.response?.data?.detail || 'Could not connect to server. Check your login.';
            setError(detail);
            addToast(detail, 'error');
        } finally {
            setLoading(false);
        }
    };

    const loadOfferings = async () => {
        setOfferingsLoading(true);
        try {
            const res = await getSubjectSummary();
            console.log('Subject Summary API Response:', res.data);
            console.log('Records count:', res.data.records?.length || 0);
            setOfferings(res.data.records || []);
        } catch (err) {
            console.error('Failed to load subject offerings:', err);
        } finally {
            setOfferingsLoading(false);
        }
    };

    useEffect(() => { loadData(); loadOfferings(); }, []);

    // ── Auto-select next available pref number when offering is clicked ──
    useEffect(() => {
        if (offeringId && !prefNum && availablePrefNumbers.length > 0) {
            setPrefNum(String(availablePrefNumbers[0]));
        }
    }, [offeringId]);

    const programs = useMemo(() =>
        [...new Set(offerings.map((o) => o.program))].sort(),
        [offerings]
    );
    
    // Dynamic semester options - only show semesters that have data
    const semesters = useMemo(() => {
        const available = [...new Set(offerings.map((o) => o.semester))].sort();
        return available;
    }, [offerings]);

    const filteredOfferings = useMemo(() => {
        let result = offerings;
        if (filterProgram) result = result.filter((o) => o.program === filterProgram);
        if (filterSemester) result = result.filter((o) => o.semester === filterSemester);
        if (searchText) {
            const q = searchText.toLowerCase();
            result = result.filter((o) =>
                o.course_code.toLowerCase().includes(q) ||
                o.course_name.toLowerCase().includes(q)
            );
        }
        return result;
    }, [offerings, filterProgram, filterSemester, searchText]);

    const grouped = useMemo(() => {
        const map: Record<string, Record<string, SubjectOffering[]>> = {};
        for (const o of filteredOfferings) {
            if (!map[o.program]) map[o.program] = {};
            if (!map[o.program][o.semester]) map[o.program][o.semester] = [];
            map[o.program][o.semester].push(o);
        }
        return map;
    }, [filteredOfferings]);

    // ── Duplicate guard ──
    const validateSelection = (oid: string, pn: string): string | null => {
        const oidNum = parseInt(oid);
        const pnNum = parseInt(pn);
        if (usedOfferingIds.has(oidNum)) {
            const existing = preferences.find((p) => p.subject_offering_id === oidNum);
            return `This subject (${existing?.subject_name || oid}) is already selected as Preference ${existing?.preference_number}.`;
        }
        if (usedPrefNumbers.has(pnNum)) {
            const existing = preferences.find((p) => p.preference_number === pnNum);
            return `Preference ${pnNum} is already assigned to ${existing?.subject_name || 'another subject'}.`;
        }
        return null;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!offeringId || !prefNum) return;

        const dupMsg = validateSelection(offeringId, prefNum);
        if (dupMsg) {
            setDuplicateError(dupMsg);
            addToast(dupMsg, 'error');
            return;
        }

        setSubmitting(true);
        setDuplicateError('');
        try {
            await submitPreference({
                subject_offering_id: parseInt(offeringId),
                preference_number: parseInt(prefNum),
            });
            addToast('Preference saved successfully', 'success');
            setOfferingId('');
            setPrefNum('');
            await loadData();  // Refresh preferences and status immediately
            loadOfferings();
        } catch (err: any) {
            const msg = err.response?.data?.detail || 'Submission failed';
            addToast(msg, 'error');
            setDuplicateError(msg);
        } finally {
            setSubmitting(false);
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await deletePreference(id);
            addToast('Preference removed — you can now modify your selections', 'success');
            await loadData();
            await loadOfferings();

            const formEl = document.getElementById('submit-form');
            if (formEl) {
                formEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                formEl.style.transition = 'box-shadow 0.3s ease, border-color 0.3s ease';
                formEl.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.25)';
                formEl.style.borderColor = 'rgba(37, 99, 235, 0.4)';
                setTimeout(() => {
                    formEl.style.boxShadow = '';
                    formEl.style.borderColor = '';
                }, 1500);
            }
        } catch {
            addToast('Failed to remove preference', 'error');
        }
    };

    const allFilled = preferences.length >= 5;

    const handleRowClick = (o: SubjectOffering) => {
        if (allFilled) return;
        if (usedOfferingIds.has(o.subject_offering_id)) return;
        setOfferingId(String(o.subject_offering_id));
        setDuplicateError('');
        document.getElementById('submit-form')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    };

    const canSubmit = !!offeringId && !!prefNum && windowOpen && !submitting && !status?.is_complete;
    const submitLabel = !windowOpen
        ? 'Window Closed'
        : status?.is_complete
            ? 'All 5 Submitted'
            : submitting
                ? 'Submitting...'
                : !offeringId
                    ? 'Select a Subject'
                    : !prefNum
                        ? 'Pick Preference #'
                        : 'Submit Preference';

    if (loading) return (
        <div className="page-container">
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '3rem' }}>Loading preferences...</p>
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

    return (
        <div className="page-container">
            <ToastContainer toasts={toasts} onRemove={removeToast} />

            <div className="page-header">
                <div>
                    <h1 className="page-title">My Preferences</h1>
                    <p className="page-subtitle">Select up to 5 subject preferences ranked 1–5</p>
                </div>
                {status && (
                    <span className={`badge ${status.is_complete ? 'badge-success' : 'badge-warning'}`}>
                        {status.total_submitted}/5 submitted
                    </span>
                )}
            </div>

            {/* Info Banner */}
            {showInfoBanner && (
                <div className="glass-card" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', borderLeft: '4px solid #3b82f6', display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(59, 130, 246, 0.05)' }}>
                    <AlertCircle size={18} style={{ color: '#3b82f6', flexShrink: 0 }} />
                    <span style={{ color: '#374151', fontSize: '0.8125rem', flex: 1 }}>
                        Showing subjects from all currently open semesters. Give 5 preferences per semester.
                    </span>
                    <button
                        onClick={() => setShowInfoBanner(false)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280', padding: '2px', lineHeight: 0 }}
                        title="Dismiss"
                    >
                        <X size={16} />
                    </button>
                </div>
            )}

            {/* Window Status Banner */}
            {!windowOpen && (
                <div className="glass-card" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', borderLeft: '4px solid #dc2626', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <Clock size={20} style={{ color: '#dc2626' }} />
                    <span style={{ color: '#374151', fontSize: '0.8125rem', fontWeight: 500 }}>
                        Preference submission window is currently <strong>closed</strong>. Contact your coordinator.
                    </span>
                </div>
            )}
            {windowOpen && windowRemaining > 0 && (
                <div className="glass-card" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', borderLeft: '4px solid #16a34a', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <Clock size={20} style={{ color: '#16a34a' }} />
                    <span style={{ color: '#374151', fontSize: '0.8125rem', fontWeight: 500 }}>
                        Window closes in <strong>{Math.floor(windowRemaining / 3600)}h {Math.floor((windowRemaining % 3600) / 60)}m</strong>
                    </span>
                </div>
            )}

            {/* ── Selected Preferences Summary (above catalog) ── */}
            <div className="glass-card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.9375rem', color: '#111827' }}>Your Preferences</span>
                    <span style={{ fontWeight: 700, fontSize: '1.125rem', color: status?.is_complete ? '#16a34a' : '#dc2626' }}>
                        {status?.total_submitted ?? 0} / 5
                    </span>
                </div>

                {/* Progress bar */}
                <div style={{ display: 'flex', gap: '0.375rem', marginBottom: '0.75rem' }}>
                    {[1, 2, 3, 4, 5].map((i) => {
                        const filled = preferences.some((p) => p.preference_number === i);
                        return (
                            <div key={i} style={{
                                flex: 1, height: 6, borderRadius: 3,
                                background: filled ? '#16a34a' : '#e5e7eb',
                                transition: 'background 0.4s ease',
                            }} />
                        );
                    })}
                </div>

                {/* Preference slot cards */}
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {[1, 2, 3, 4, 5].map((n) => {
                        const pref = preferences.find((p) => p.preference_number === n);
                        return (
                            <div
                                key={n}
                                style={{
                                    flex: '1 1 140px',
                                    padding: '0.625rem 0.75rem',
                                    borderRadius: '8px',
                                    border: pref ? '1px solid rgba(22, 163, 74, 0.25)' : '1px dashed #d1d5db',
                                    background: pref ? 'rgba(22, 163, 74, 0.04)' : '#fafafa',
                                    minWidth: 0,
                                    display: 'flex', alignItems: 'center', gap: '0.5rem',
                                }}
                            >
                                <span style={{
                                    width: 22, height: 22, borderRadius: '50%',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    fontSize: '0.6875rem', fontWeight: 700, flexShrink: 0,
                                    background: pref ? '#16a34a' : '#e5e7eb',
                                    color: pref ? '#fff' : '#9ca3af',
                                }}>
                                    {n}
                                </span>
                                {pref ? (
                                    <div style={{ minWidth: 0, flex: 1 }}>
                                        <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#111827', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                            {pref.subject_name}
                                        </div>
                                        <div style={{ fontSize: '0.6875rem', color: '#6b7280', fontFamily: 'monospace', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                            <span>{pref.subject_code}</span>
                                            {(() => {
                                                // Derive curriculum_year from subject_code if NULL
                                                let currYear = pref.curriculum_year;
                                                if (!currYear || currYear === 'null') {
                                                    const prefix = pref.subject_code.substring(0, 3);
                                                    if (['CCA', 'CCM', 'CMA', 'CEL'].includes(prefix)) {
                                                        currYear = '2022';
                                                    } else if (['ACA', 'ACY', 'ACM', 'GMA', 'GLS', 'GGE', 'ABB', 'ASS'].includes(prefix)) {
                                                        currYear = '2023';
                                                    } else {
                                                        currYear = '2022'; // default
                                                    }
                                                }
                                                return (
                                                    <span style={{fontSize:'9px', background:'#f0fdf4', color:'#166534', padding:'1px 5px', borderRadius:'8px', border:'1px solid #bbf7d0', fontWeight:'600'}}>
                                                        {currYear}
                                                    </span>
                                                );
                                            })()}
                                        </div>
                                    </div>
                                ) : (
                                    <span style={{ fontSize: '0.75rem', color: '#9ca3af', fontStyle: 'italic' }}>Empty</span>
                                )}
                                {pref && windowOpen && (
                                    <button
                                        onClick={() => handleDelete(pref.id)}
                                        style={{
                                            background: 'none', border: 'none', cursor: 'pointer',
                                            color: '#dc2626', padding: '2px', flexShrink: 0, lineHeight: 0,
                                        }}
                                        title="Remove"
                                    >
                                        <XCircle size={14} />
                                    </button>
                                )}
                            </div>
                        );
                    })}
                </div>

                {status?.is_complete && (
                    <div style={{ marginTop: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.8125rem', color: '#16a34a' }}>
                        <CheckCircle2 size={15} /> All preferences submitted
                    </div>
                )}
            </div>

            {/* Subject Catalog Browser */}
            <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <BookOpen size={20} className="text-blue-600" />
                        <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: '#111827' }}>Subject Catalog</h3>
                        <span className="badge badge-info" style={{ marginLeft: '0.25rem' }}>{filteredOfferings.length} subjects</span>
                    </div>
                    <button onClick={loadOfferings} className="btn btn-outline" style={{ padding: '0.375rem 0.75rem', fontSize: '0.8125rem' }}>
                        <RefreshCw size={14} /> Refresh
                    </button>
                </div>

                {/* Semester Filter Tabs */}
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                    <button
                        onClick={() => setFilterSemester('')}
                        style={{
                            padding: '0.5rem 1rem',
                            borderRadius: '20px',
                            border: filterSemester === '' ? '2px solid #2563eb' : '1px solid #e5e7eb',
                            background: filterSemester === '' ? 'rgba(37, 99, 235, 0.1)' : '#fff',
                            color: filterSemester === '' ? '#2563eb' : '#6b7280',
                            fontWeight: filterSemester === '' ? 600 : 500,
                            fontSize: '0.8125rem',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                        }}
                    >
                        All Semesters
                    </button>
                    {semesters.map((sem) => (
                        <button
                            key={sem}
                            onClick={() => setFilterSemester(sem)}
                            style={{
                                padding: '0.5rem 1rem',
                                borderRadius: '20px',
                                border: filterSemester === sem ? '2px solid #2563eb' : '1px solid #e5e7eb',
                                background: filterSemester === sem ? 'rgba(37, 99, 235, 0.1)' : '#fff',
                                color: filterSemester === sem ? '#2563eb' : '#6b7280',
                                fontWeight: filterSemester === sem ? 600 : 500,
                                fontSize: '0.8125rem',
                                cursor: 'pointer',
                                transition: 'all 0.2s',
                            }}
                        >
                            Semester {sem}
                        </button>
                    ))}
                </div>

                {/* Filters Row */}
                <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
                    <Filter size={14} style={{ color: '#9ca3af' }} />
                    <select
                        id="filter-program"
                        className="form-select"
                        value={filterProgram}
                        onChange={(e) => setFilterProgram(e.target.value)}
                        style={{ minWidth: '160px', fontSize: '0.875rem' }}
                    >
                        <option value="">All Programs</option>
                        {programs.map((p) => <option key={p} value={p}>{p}</option>)}
                    </select>
                    <div style={{ position: 'relative', flex: '1 1 200px', minWidth: '180px' }}>
                        <Search size={14} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af', pointerEvents: 'none' }} />
                        <input
                            id="filter-search"
                            type="text"
                            className="form-input"
                            placeholder="Search code or name..."
                            value={searchText}
                            onChange={(e) => setSearchText(e.target.value)}
                            style={{ paddingLeft: '2rem', fontSize: '0.875rem', width: '100%' }}
                        />
                    </div>
                    {(filterProgram || filterSemester || searchText) && (
                        <button
                            className="btn btn-outline"
                            onClick={() => { setFilterProgram(''); setFilterSemester(''); setSearchText(''); }}
                            style={{ padding: '0.375rem 0.75rem', fontSize: '0.8125rem' }}
                        >
                            Clear
                        </button>
                    )}
                </div>

                {/* Subject List */}
                {offeringsLoading ? (
                    <p style={{ color: '#6b7280', textAlign: 'center', padding: '2rem' }}>Loading subject catalog...</p>
                ) : filteredOfferings.length === 0 ? (
                    <p style={{ color: '#6b7280', textAlign: 'center', padding: '2rem' }}>No subjects match the current filters.</p>
                ) : (
                    <div style={{ maxHeight: '480px', overflowY: 'auto', borderRadius: '10px', border: '1px solid #e5e7eb' }}>
                        {Object.keys(grouped).sort().map((prog) => (
                            <div key={prog}>
                                {Object.keys(grouped[prog]).sort().map((sem) => (
                                    <div key={`${prog}-${sem}`}>
                                        <div style={{
                                            padding: '0.5rem 1rem',
                                            background: '#f9fafb',
                                            borderBottom: '1px solid #e5e7eb',
                                            display: 'flex', alignItems: 'center', gap: '0.5rem',
                                            position: 'sticky', top: 0, zIndex: 1,
                                        }}>
                                            <span className="badge badge-info" style={{ fontSize: '0.6875rem' }}>{prog}</span>
                                            <span className="badge badge-warning" style={{ fontSize: '0.6875rem' }}>{sem}</span>
                                            <span style={{ fontSize: '0.75rem', color: '#6b7280', marginLeft: 'auto' }}>
                                                {grouped[prog][sem].length} subject{grouped[prog][sem].length !== 1 ? 's' : ''}
                                            </span>
                                        </div>

                                        {grouped[prog][sem].map((o, idx) => {
                                            const isSelected = offeringId === String(o.subject_offering_id);
                                            const isAlreadyUsed = usedOfferingIds.has(o.subject_offering_id);
                                            const isDisabled = allFilled || isAlreadyUsed;
                                            const matchedPref = isAlreadyUsed
                                                ? preferences.find((p) => p.subject_offering_id === o.subject_offering_id)
                                                : null;

                                            return (
                                            <div
                                                key={`${prog}-${sem}-${o.course_code}-${o.section}-${idx}`}
                                                onClick={() => handleRowClick(o)}
                                                style={{
                                                    padding: '0.75rem 1rem',
                                                    borderBottom: '1px solid #f3f4f6',
                                                    display: 'flex', alignItems: 'center', gap: '1rem',
                                                    transition: 'all 0.15s ease',
                                                    cursor: isDisabled ? 'not-allowed' : 'pointer',
                                                    opacity: isDisabled ? 0.5 : 1,
                                                    borderLeft: isSelected
                                                        ? '3px solid #2563eb'
                                                        : isAlreadyUsed
                                                            ? '3px solid #16a34a'
                                                            : '3px solid transparent',
                                                    background: isSelected
                                                        ? 'rgba(37, 99, 235, 0.05)'
                                                        : isAlreadyUsed
                                                            ? 'rgba(22, 163, 74, 0.03)'
                                                            : undefined,
                                                }}
                                                onMouseEnter={(e) => { if (!isSelected && !isDisabled) (e.currentTarget as HTMLDivElement).style.background = '#f3f4f6'; }}
                                                onMouseLeave={(e) => { if (!isSelected && !isDisabled) (e.currentTarget as HTMLDivElement).style.background = ''; }}
                                            >
                                                <div style={{ flex: 1, minWidth: 0 }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                                                        <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '0.875rem', color: isAlreadyUsed ? '#6b7280' : '#111827' }}>
                                                            {o.course_code}
                                                        </span>
                                                        <span style={{ color: '#d1d5db' }}>•</span>
                                                        <span style={{ fontSize: '0.875rem', fontWeight: 500, color: isAlreadyUsed ? '#6b7280' : '#374151' }}>{o.course_name}</span>
                                                    </div>
                                                    <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.75rem', color: '#6b7280', alignItems: 'center' }}>
                                                        <span>ID {o.subject_offering_id}</span>
                                                        <span>Sec {o.section}</span>
                                                        <span
                                                            style={{
                                                                padding: '2px 8px',
                                                                borderRadius: '12px',
                                                                fontSize: '0.6875rem',
                                                                fontWeight: 600,
                                                                background: o.shift === 1 ? 'rgba(37, 99, 235, 0.1)' : 'rgba(249, 115, 22, 0.1)',
                                                                color: o.shift === 1 ? '#2563eb' : '#f97316',
                                                            }}
                                                        >
                                                            Shift {o.shift}
                                                        </span>
                                                        <span>TCH {o.tch}</span>
                                                        {(() => {
                                                            // Derive curriculum_year from course_code if NULL
                                                            let currYear = o.curriculum_year;
                                                            if (!currYear || currYear === 'null') {
                                                                const prefix = o.course_code.substring(0, 3);
                                                                if (['CCA', 'CCM', 'CMA', 'CEL'].includes(prefix)) {
                                                                    currYear = '2022';
                                                                } else if (['ACA', 'ACY', 'ACM', 'GMA', 'GLS', 'GGE', 'ABB', 'ASS'].includes(prefix)) {
                                                                    currYear = '2023';
                                                                } else {
                                                                    currYear = '2022'; // default
                                                                }
                                                            }
                                                            return (
                                                                <span style={{fontSize:'11px', background:'#f0fdf4', color:'#166534',padding:'2px 8px', borderRadius:'12px', border:'1px solid #bbf7d0',fontWeight:'600'}}>
                                                                    {currYear} Reg
                                                                </span>
                                                            );
                                                        })()}
                                                        {o.allocated && o.faculty_name && (
                                                            <span style={{ color: '#16a34a' }}>✓ {o.faculty_name}</span>
                                                        )}
                                                        {!o.allocated && !isAlreadyUsed && (
                                                            <span style={{ color: '#f59e0b' }}>Unallocated</span>
                                                        )}
                                                    </div>
                                                </div>
                                                {isAlreadyUsed && matchedPref && (
                                                    <span className="badge badge-success" style={{ flexShrink: 0, fontSize: '0.6875rem' }}>
                                                        Pref {matchedPref.preference_number}
                                                    </span>
                                                )}
                                                {isSelected && !isAlreadyUsed && (
                                                    <span className="badge badge-info" style={{ flexShrink: 0 }}>Selected</span>
                                                )}
                                            </div>
                                            );
                                        })}
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Submit Form — hidden when all 5 filled */}
            {allFilled ? (
                <div id="submit-form" className="glass-card" style={{
                    padding: '1.5rem', marginBottom: '1.5rem',
                    borderColor: 'rgba(22, 163, 74, 0.3)',
                    background: 'rgba(22, 163, 74, 0.04)',
                    textAlign: 'center',
                }}>
                    <CheckCircle2 size={36} style={{ color: '#16a34a', marginBottom: '0.75rem' }} />
                    <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#16a34a', marginBottom: '0.375rem' }}>
                        All 5 Preferences Submitted
                    </h3>
                    <p style={{ fontSize: '0.8125rem', color: '#6b7280', margin: 0 }}>
                        Your preferences are locked. Remove a preference above to make changes.
                    </p>
                </div>
            ) : (
                <div id="submit-form" className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem', color: '#111827' }}>Submit Preference</h3>

                    {/* Selected subject chip */}
                    {selectedOffering && (
                        <div style={{
                            display: 'flex', alignItems: 'center', gap: '0.75rem',
                            padding: '0.75rem 1rem', borderRadius: '8px',
                            background: 'rgba(37, 99, 235, 0.05)', border: '1px solid rgba(37, 99, 235, 0.2)',
                            marginBottom: '1rem',
                        }}>
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#111827', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <span>{selectedOffering.course_code} — {selectedOffering.course_name}</span>
                                    {(() => {
                                        // Derive curriculum_year from course_code if NULL
                                        let currYear = selectedOffering.curriculum_year;
                                        if (!currYear || currYear === 'null') {
                                            const prefix = selectedOffering.course_code.substring(0, 3);
                                            if (['CCA', 'CCM', 'CMA', 'CEL'].includes(prefix)) {
                                                currYear = '2022';
                                            } else if (['ACA', 'ACY', 'ACM', 'GMA', 'GLS', 'GGE', 'ABB', 'ASS'].includes(prefix)) {
                                                currYear = '2023';
                                            } else {
                                                currYear = '2022'; // default
                                            }
                                        }
                                        return (
                                            <span style={{fontSize:'10px', background:'#f0fdf4', color:'#166534', padding:'2px 7px', borderRadius:'10px', border:'1px solid #bbf7d0', fontWeight:'600'}}>
                                                {currYear} Reg
                                            </span>
                                        );
                                    })()}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
                                    {selectedOffering.program} • {selectedOffering.semester} • Sec {selectedOffering.section} • Shift {selectedOffering.shift}
                                </div>
                            </div>
                            <button
                                onClick={() => setOfferingId('')}
                                style={{
                                    background: 'none', border: 'none', cursor: 'pointer',
                                    color: '#6b7280', padding: '4px', lineHeight: 0,
                                }}
                                title="Clear selection"
                            >
                                <XCircle size={18} />
                            </button>
                        </div>
                    )}

                    {/* Duplicate error */}
                    {duplicateError && (
                        <div style={{
                            padding: '0.75rem 1rem', borderRadius: '8px',
                            background: 'rgba(220, 38, 38, 0.05)', border: '1px solid rgba(220, 38, 38, 0.2)',
                            marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem',
                        }}>
                            <AlertCircle size={16} style={{ color: '#dc2626', flexShrink: 0 }} />
                            <span style={{ fontSize: '0.8125rem', color: '#dc2626' }}>{duplicateError}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end' }}>
                        <div style={{ flex: 1 }}>
                            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                                Preference Number
                            </label>
                            <select
                                className="form-select"
                                value={prefNum}
                                onChange={(e) => setPrefNum(e.target.value)}
                                disabled={!offeringId || availablePrefNumbers.length === 0}
                                style={{ width: '100%' }}
                            >
                                <option value="">Select...</option>
                                {availablePrefNumbers.map((n) => (
                                    <option key={n} value={n}>Preference {n}</option>
                                ))}
                            </select>
                        </div>
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={!canSubmit}
                            style={{ padding: '0.625rem 1.5rem' }}
                        >
                            {submitLabel}
                        </button>
                    </form>

                    {!offeringId && (
                        <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.75rem', textAlign: 'center' }}>
                            Click a subject from the catalog above to select it
                        </p>
                    )}
                </div>
            )}
        </div>
    );
}
