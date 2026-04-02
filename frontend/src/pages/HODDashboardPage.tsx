import { useAuth } from '../context/AuthContext';
import { Users, BookOpen, CheckCircle, BarChart3, Heart } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function HODDashboardPage() {
    const { user } = useAuth();

    const cards = [
        {
            title: 'My Preferences',
            desc: 'Submit your subject teaching preferences',
            icon: Heart,
            path: '/preferences',
            color: '#dc2626',
        },
        {
            title: 'Staff Management',
            desc: 'Add, edit, or deactivate faculty members',
            icon: Users,
            path: '/hod/staff',
            color: '#7c3aed',
        },
        {
            title: 'Curriculum Upload',
            desc: 'Upload subject offerings for the semester',
            icon: BookOpen,
            path: '/hod/curriculum',
            color: '#2563eb',
        },
        {
            title: 'Final Approval',
            desc: 'Review and approve workload allocations',
            icon: CheckCircle,
            path: '/hod/approval',
            color: '#059669',
        },
        {
            title: 'Reports & Exports',
            desc: 'View workload reports and export data',
            icon: BarChart3,
            path: '/admin/reports',
            color: '#d97706',
        },
    ];

    return (
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
            <div style={{ marginBottom: '2rem' }}>
                <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '0.25rem' }}>
                    HOD Dashboard
                </h1>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
                    Welcome, {user?.name ?? 'HOD'}. System management overview.
                </p>
            </div>

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

            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
                gap: '1.25rem',
            }}>
                {cards.map((card) => {
                    const Icon = card.icon;
                    return (
                        <Link
                            key={card.path}
                            to={card.path}
                            className="glass-card"
                            style={{
                                padding: '1.5rem',
                                textDecoration: 'none',
                                color: 'inherit',
                                transition: 'transform 0.15s, box-shadow 0.15s',
                            }}
                            onMouseOver={(e) => {
                                (e.currentTarget as HTMLElement).style.transform = 'translateY(-2px)';
                            }}
                            onMouseOut={(e) => {
                                (e.currentTarget as HTMLElement).style.transform = '';
                            }}
                        >
                            <div style={{
                                width: '2.5rem', height: '2.5rem', borderRadius: '0.625rem',
                                background: card.color,
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                marginBottom: '1rem',
                            }}>
                                <Icon size={20} color="white" />
                            </div>
                            <h3 style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '0.25rem' }}>
                                {card.title}
                            </h3>
                            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>
                                {card.desc}
                            </p>
                        </Link>
                    );
                })}
            </div>
        </div>
    );
}
