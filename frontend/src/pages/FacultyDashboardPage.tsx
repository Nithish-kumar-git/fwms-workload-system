import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMyPreferences, getPrefWindowStatus, getCurrentUser, getFacultyWorkload } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { BookOpen, CheckCircle2, Clock, ArrowRight, GraduationCap } from 'lucide-react';
import WindowStatusBanner from '../components/WindowStatusBanner';

interface Preference {
    id: number;
    preference_number: number;
    subject_code: string;
    subject_name: string;
    program: string;
    semester: string;
    section: string;
    tch: number;
}

interface AssignedSubject {
    course_code: string;
    course_name: string;
    program: string;
    semester: string;
    section: string;
    tch: number;
}

export default function FacultyDashboardPage() {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [preferences, setPreferences] = useState<Preference[]>([]);
    const [windowOpen, setWindowOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [mySubjects, setMySubjects] = useState<AssignedSubject[]>([]);
    
    console.log('USER CT DATA:', JSON.stringify({is_ct: user?.is_class_teacher, prog: user?.ct_program, sec: user?.ct_section, sem: user?.ct_semester}));

    useEffect(() => {
        const load = async () => {
            try {
                const [prefRes, windowRes] = await Promise.all([
                    getMyPreferences(),
                    getPrefWindowStatus(),
                ]);
                setPreferences(prefRes.data || []);
                setWindowOpen(windowRes.data?.is_open ?? false);
            } catch {
                // Silently handle — show empty state
            }

            // Load assigned subjects
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
                setMySubjects([]);
            }

            setLoading(false);
        };
        load();
    }, []);

    const totalTCH = mySubjects.reduce((sum, s) => sum + s.tch, 0);
    const maxPrefs = 5;
    const submitted = preferences.length;
    const progress = Math.round((submitted / maxPrefs) * 100);

    if (loading) return (
        <div className="page-container">
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '3rem' }}>Loading dashboard...</p>
        </div>
    );

    return (
        <div className="page-container">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Welcome{user ? `, ${user.name}` : ''}</h1>
                    <p className="page-subtitle">Faculty Dashboard — Your preferences and assignments</p>
                </div>
            </div>

            <WindowStatusBanner />

            {/* CT Info Card */}
            {user?.is_class_teacher && (
                <div style={{background:'#fefce8', border:'1px solid #fbbf24',borderLeft: '4px solid #f59e0b',borderRadius:'10px', padding:'16px 20px', marginBottom:'16px'}}>
                    <div style={{fontWeight:'700', color:'#92400e', fontSize:'14px', marginBottom:'8px'}}>📋 You are Class Teacher for:</div>
                    <div style={{color:'#78350f', fontSize:'17px', fontWeight:'700'}}>
                        {user.ct_program} — Section {user.ct_section} — Semester {user.ct_semester}
                        {user.ct_shift ? ` — Shift ${user.ct_shift}` : ''}
                        {user.ct_curriculum_year ? ` (${user.ct_curriculum_year} Regulation)` : ''}
                    </div>
                    <div style={{color:'#b45309', fontSize:'12px', marginTop:'8px', fontStyle:'italic'}}>⚠ Your Preference #1 must be for a subject in this class</div>
                </div>
            )}

            {/* Preference Progress + Quick Action */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                {/* Progress Card */}
                <div className="glass-card" style={{
                    padding: '1.5rem',
                    borderLeft: submitted >= maxPrefs
                        ? '4px solid #16a34a'
                        : '4px solid #2563eb',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                        <div style={{
                            padding: '0.5rem', borderRadius: '0.75rem',
                            background: submitted >= maxPrefs ? '#f0fdf4' : '#eff6ff',
                            color: submitted >= maxPrefs ? '#16a34a' : '#2563eb',
                            display: 'flex',
                        }}>
                            {submitted >= maxPrefs
                                ? <CheckCircle2 size={22} strokeWidth={2.5} />
                                : <BookOpen size={22} strokeWidth={2.5} />
                            }
                        </div>
                        <div>
                            <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, color: '#111827', margin: 0 }}>
                                Preference Progress
                            </h3>
                            <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                                {submitted}/{maxPrefs} submitted
                            </p>
                        </div>
                    </div>
                    {/* Progress bar */}
                    <div style={{
                        height: '8px', borderRadius: '4px', background: '#e5e7eb',
                        overflow: 'hidden',
                    }}>
                        <div style={{
                            height: '100%', borderRadius: '4px',
                            width: `${progress}%`,
                            background: submitted >= maxPrefs
                                ? 'linear-gradient(90deg, #16a34a, #22c55e)'
                                : 'linear-gradient(90deg, #2563eb, #3b82f6)',
                            transition: 'width 0.5s ease',
                        }} />
                    </div>
                    {submitted >= maxPrefs && (
                        <p style={{ fontSize: '0.75rem', color: '#16a34a', marginTop: '0.5rem', fontWeight: 500 }}>
                            ✓ All preferences submitted
                        </p>
                    )}
                </div>

                {/* Quick Action Card */}
                <div className="glass-card" style={{
                    padding: '1.5rem',
                    display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                }} onClick={() => navigate('/preferences')}>
                    <div style={{
                        padding: '0.625rem', borderRadius: '0.75rem',
                        background: windowOpen ? '#eff6ff' : '#f3f4f6',
                        color: windowOpen ? '#2563eb' : '#9ca3af',
                        display: 'flex', marginBottom: '0.75rem',
                    }}>
                        {windowOpen
                            ? <ArrowRight size={24} strokeWidth={2.5} />
                            : <Clock size={24} strokeWidth={2} />
                        }
                    </div>
                    <h3 style={{
                        fontSize: '0.9375rem', fontWeight: 600, margin: 0, marginBottom: '0.25rem',
                        color: windowOpen ? '#111827' : '#9ca3af',
                    }}>
                        {windowOpen ? 'Go to Preferences' : 'Window Closed'}
                    </h3>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {windowOpen
                            ? submitted < maxPrefs ? 'Submit your subject preferences' : 'View or modify preferences'
                            : 'Preference window is not open'
                        }
                    </p>
                </div>
            </div>

            {/* My Submitted Preferences */}
            {preferences.length > 0 && (
                <div className="glass-card" style={{ marginBottom: '1.5rem', overflow: 'hidden' }}>
                    <div style={{
                        padding: '1.25rem 1.5rem',
                        borderBottom: '1px solid #e5e7eb',
                        display: 'flex', alignItems: 'center', gap: '0.75rem',
                    }}>
                        <div style={{
                            padding: '0.5rem', background: '#f0fdf4', borderRadius: '0.75rem',
                            color: '#16a34a', display: 'flex',
                        }}>
                            <CheckCircle2 size={20} strokeWidth={2.5} />
                        </div>
                        <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#111827', margin: 0 }}>
                            My Submitted Preferences
                        </h2>
                    </div>
                    <div style={{ overflowX: 'auto' }}>
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th style={{ width: '60px' }}>Pref #</th>
                                    <th>Subject Code</th>
                                    <th>Subject Name</th>
                                    <th>Program</th>
                                    <th>Semester</th>
                                    <th>Section</th>
                                    <th>TCH</th>
                                </tr>
                            </thead>
                            <tbody>
                                {preferences
                                    .sort((a, b) => a.preference_number - b.preference_number)
                                    .map((p) => (
                                    <tr key={p.id}>
                                        <td>
                                            <span style={{
                                                background: '#eff6ff', color: '#2563eb',
                                                padding: '0.125rem 0.5rem', borderRadius: '6px',
                                                fontSize: '0.8125rem', fontWeight: 600,
                                            }}>
                                                {p.preference_number}
                                            </span>
                                        </td>
                                        <td style={{ fontFamily: 'monospace', fontWeight: 500, color: '#111827' }}>
                                            {p.subject_code}
                                        </td>
                                        <td style={{ color: '#374151' }}>{p.subject_name}</td>
                                        <td>
                                            <span style={{
                                                background: '#f3f4f6', color: '#374151',
                                                padding: '0.125rem 0.5rem', borderRadius: '6px',
                                                fontSize: '0.8125rem',
                                            }}>
                                                {p.program}
                                            </span>
                                        </td>
                                        <td style={{ color: '#374151' }}>{p.semester}</td>
                                        <td style={{ color: '#374151' }}>{p.section}</td>
                                        <td style={{ fontWeight: 600, color: '#2563eb' }}>{p.tch}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* My Assigned Subjects */}
            <div className="glass-card" style={{ overflow: 'hidden' }}>
                <div style={{
                    padding: '1.25rem 1.5rem',
                    borderBottom: '1px solid #e5e7eb',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{
                            padding: '0.5rem', background: '#eff6ff', borderRadius: '0.75rem',
                            color: '#2563eb', display: 'flex',
                        }}>
                            <GraduationCap size={20} strokeWidth={2.5} />
                        </div>
                        <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#111827', margin: 0 }}>
                            My Assigned Subjects
                        </h2>
                    </div>
                    {mySubjects.length > 0 && (
                        <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280' }}>
                            {mySubjects.length} subject{mySubjects.length !== 1 ? 's' : ''} · {totalTCH} TCH
                        </span>
                    )}
                </div>

                {mySubjects.length === 0 ? (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>
                        No subjects assigned yet.
                    </div>
                ) : (
                    <div style={{ overflowX: 'auto' }}>
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Subject Code</th>
                                    <th>Subject Name</th>
                                    <th>Program</th>
                                    <th>Semester</th>
                                    <th>Section</th>
                                    <th>TCH</th>
                                </tr>
                            </thead>
                            <tbody>
                                {mySubjects.map((s, i) => (
                                    <tr key={i}>
                                        <td style={{ fontFamily: 'monospace', fontWeight: 500, color: '#111827' }}>{s.course_code}</td>
                                        <td style={{ color: '#374151' }}>{s.course_name}</td>
                                        <td>
                                            <span style={{
                                                background: '#eff6ff', color: '#2563eb',
                                                padding: '0.125rem 0.625rem', borderRadius: '6px',
                                                fontSize: '0.8125rem', fontWeight: 500,
                                            }}>
                                                {s.program}
                                            </span>
                                        </td>
                                        <td style={{ color: '#374151' }}>{s.semester}</td>
                                        <td style={{ color: '#374151' }}>{s.section}</td>
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
        </div>
    );
}
