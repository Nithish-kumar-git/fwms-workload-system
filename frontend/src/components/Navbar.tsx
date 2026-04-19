import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard, BookOpen, Settings, FileText, LogOut,
    Clock, CalendarDays, Users, Shield, Upload, CheckCircle, ClipboardList,
} from 'lucide-react';
import { logout } from '../api/client';
import { useAuth } from '../context/AuthContext';

const hodItems = [
    { path: '/hod-dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/preferences', label: 'My Preferences', icon: BookOpen },
    { path: '/hod/staff', label: 'Staff Management', icon: Users },
    { path: '/hod/curriculum', label: 'Curriculum Upload', icon: Upload },
    { path: '/hod/approval', label: 'Final Approval', icon: CheckCircle },
    { path: '/admin/reports', label: 'Reports', icon: FileText },
];

const coordinatorItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/preferences', label: 'My Preferences', icon: BookOpen },
    { path: '/admin/window', label: 'Window', icon: Clock },
    { path: '/admin/cycles', label: 'Cycles', icon: CalendarDays },
    { path: '/admin/subjects', label: 'Subjects', icon: Upload },
    { path: '/admin/allocation', label: 'Allocation', icon: Settings },
    { path: '/admin/preference-review', label: 'Pref Review', icon: ClipboardList },
    { path: '/admin/review', label: 'Review', icon: FileText },
    { path: '/admin/reports', label: 'Reports', icon: FileText },
];

const facultyItems = [
    { path: '/faculty-dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/preferences', label: 'Preferences', icon: BookOpen },
];

function getNavItems(role: string) {
    switch (role) {
        case 'hod': return hodItems;
        case 'tt_coordinator': return coordinatorItems;
        default: return facultyItems;
    }
}

function getRoleBadge(role: string) {
    switch (role) {
        case 'hod':
            return { label: 'HOD', bg: 'bg-purple-50', text: 'text-purple-600', icon: Shield };
        case 'tt_coordinator':
            return { label: 'Coordinator', bg: 'bg-blue-50', text: 'text-blue-600', icon: Settings };
        default:
            return { label: 'Faculty', bg: 'bg-green-50', text: 'text-green-600', icon: BookOpen };
    }
}

export default function Navbar() {
    const location = useLocation();
    const navigate = useNavigate();
    const { user } = useAuth();

    const role = user?.role ?? 'faculty';
    const navItems = getNavItems(role);
    const badge = getRoleBadge(role);

    const handleLogout = async () => {
        try {
            await logout();
        } catch {
            // ignore
        }
        localStorage.removeItem('jwt_token');
        navigate('/login');
    };

    return (
        <div className="px-6 pt-4 pb-2 sticky top-0 z-50 max-w-[1400px] mx-auto w-full">
            <nav className="glass-panel flex items-center justify-between px-6 py-2.5">
                <div className="flex items-center gap-8">
                    <span className="font-bold text-lg tracking-tight text-[#2563eb]">
                        FWMS
                    </span>
                    <div className="flex items-center gap-1.5">
                        {navItems.map((item) => {
                            const isActive = location.pathname.startsWith(item.path);
                            const Icon = item.icon;
                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-[13px] font-medium transition-all duration-200 ${isActive
                                            ? 'bg-blue-50 text-[#2563eb] shadow-sm'
                                            : 'text-gray-500 hover:bg-gray-100 hover:text-gray-800'
                                        }`}
                                >
                                    <Icon size={15} strokeWidth={isActive ? 2.5 : 2} />
                                    {item.label}
                                </Link>
                            );
                        })}
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    {user && (
                        <span className="text-[12px] text-gray-400 font-medium">
                            {user.name}
                            <span className={`ml-1.5 px-1.5 py-0.5 rounded text-[11px] uppercase ${badge.bg} ${badge.text}`}>
                                {badge.label}
                            </span>
                        </span>
                    )}
                    <button onClick={handleLogout} className="btn btn-outline text-[13px] py-1.5 px-4 font-medium">
                        <LogOut size={15} />
                        Logout
                    </button>
                </div>
            </nav>
        </div>
    );
}
