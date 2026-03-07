import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, BookOpen, Settings, FileText, LogOut, Clock, CalendarDays, Users } from 'lucide-react';
import { logout } from '../api/client';

const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/preferences', label: 'Preferences', icon: BookOpen },
    { path: '/admin/window', label: 'Window', icon: Clock },
    { path: '/admin/cycles', label: 'Cycles', icon: CalendarDays },
    { path: '/admin/staff', label: 'Staff', icon: Users },
    { path: '/admin/allocation', label: 'Allocation', icon: Settings },
    { path: '/admin/review', label: 'Review', icon: FileText },
    { path: '/admin/reports', label: 'Reports', icon: FileText },
];

export default function Navbar() {
    const location = useLocation();
    const navigate = useNavigate();

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
                    <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-blue-600 to-blue-400 dark:from-blue-400 dark:to-blue-300 bg-clip-text text-transparent">
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
                                    className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[13px] font-medium transition-all duration-300 ${isActive
                                            ? 'bg-black/5 dark:bg-white/10 text-blue-600 dark:text-blue-400 shadow-sm'
                                            : 'text-gray-500 dark:text-gray-400 hover:bg-black/5 dark:hover:bg-white/10 hover:text-gray-900 dark:hover:text-gray-200'
                                        }`}
                                >
                                    <Icon size={15} strokeWidth={isActive ? 2.5 : 2} />
                                    {item.label}
                                </Link>
                            );
                        })}
                    </div>
                </div>
                <button onClick={handleLogout} className="btn btn-outline text-[13px] py-1.5 px-4 font-medium">
                    <LogOut size={15} />
                    Logout
                </button>
            </nav>
        </div>
    );
}
