import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import FacultyDashboardPage from './pages/FacultyDashboardPage';
import HODDashboardPage from './pages/HODDashboardPage';
import PreferencesPage from './pages/PreferencesPage';
import AllocationPage from './pages/AllocationPage';
import ReviewPage from './pages/ReviewPage';
import ReportsPage from './pages/ReportsPage';
import WindowPage from './pages/WindowPage';
import CyclesPage from './pages/CyclesPage';
import StaffPage from './pages/StaffPage';
import StaffEmailsPage from './pages/StaffEmailsPage';
import CurriculumUploadPage from './pages/CurriculumUploadPage';
import FinalApprovalPage from './pages/FinalApprovalPage';
import PreferenceReviewDashboardPage from './pages/PreferenceReviewDashboardPage';

/* ── Auth guard: redirects to /login if not authenticated ── */
function RequireAuth() {
    const { user, loading } = useAuth();
    const [demoBannerDismissed, setDemoBannerDismissed] = useState(false);

    if (loading) {
        return (
            <div style={{
                minHeight: '100vh', display: 'flex', alignItems: 'center',
                justifyContent: 'center', color: 'var(--color-text-muted)',
            }}>
                Loading...
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    const isDemoMode = user.email === 'demo@fwms-demo.com';
    const showDemoBanner = isDemoMode && !demoBannerDismissed;
    const bannerHeight = 40; // pixels

    return (
        <>
            {showDemoBanner && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    width: '100%',
                    height: `${bannerHeight}px`,
                    backgroundColor: '#f59e0b',
                    color: '#000',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '14px',
                    fontWeight: 'bold',
                    zIndex: 9999,
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                }}>
                    <span>👁️ Demo Mode — Exploring as HOD. Some actions are view-only.</span>
                    <button
                        onClick={() => setDemoBannerDismissed(true)}
                        style={{
                            position: 'absolute',
                            right: '16px',
                            background: 'transparent',
                            border: 'none',
                            fontSize: '18px',
                            fontWeight: 'bold',
                            cursor: 'pointer',
                            color: '#000',
                            padding: '4px 8px',
                            lineHeight: 1,
                        }}
                        aria-label="Dismiss demo banner"
                    >
                        ✕
                    </button>
                </div>
            )}
            <div style={{ paddingTop: showDemoBanner ? `${bannerHeight}px` : 0 }}>
                <Navbar />
                <Outlet />
            </div>
        </>
    );
}

/* ── HOD-only guard ── */
function RequireHOD() {
    const { user, loading } = useAuth();
    if (loading) {
        return (
            <div style={{
                minHeight: '100vh', display: 'flex', alignItems: 'center',
                justifyContent: 'center', color: 'var(--color-text-muted)',
            }}>
                Loading...
            </div>
        );
    }
    if (user?.role !== 'hod') return <Navigate to="/" replace />;
    return <Outlet />;
}

/* ── Coordinator-only guard (tt_coordinator OR hod) ── */
function RequireCoordinator() {
    const { user, loading } = useAuth();
    if (loading) {
        return (
            <div style={{
                minHeight: '100vh', display: 'flex', alignItems: 'center',
                justifyContent: 'center', color: 'var(--color-text-muted)',
            }}>
                Loading...
            </div>
        );
    }
    if (user?.role !== 'tt_coordinator' && user?.role !== 'hod') {
        return <Navigate to="/" replace />;
    }
    return <Outlet />;
}

/* ── Faculty-only guard ── */
function RequireFaculty() {
    const { user, loading } = useAuth();
    if (loading) {
        return (
            <div style={{
                minHeight: '100vh', display: 'flex', alignItems: 'center',
                justifyContent: 'center', color: 'var(--color-text-muted)',
            }}>
                Loading...
            </div>
        );
    }
    if (user?.role !== 'faculty') return <Navigate to="/" replace />;
    return <Outlet />;
}

/* ── Root redirect: route to correct dashboard by role ── */
function RootRedirect() {
    const { user, loading } = useAuth();
    if (loading) {
        return (
            <div style={{
                minHeight: '100vh', display: 'flex', alignItems: 'center',
                justifyContent: 'center', color: 'var(--color-text-muted)',
            }}>
                Loading...
            </div>
        );
    }
    if (!user) return <Navigate to="/login" replace />;

    switch (user.role) {
        case 'hod': return <Navigate to="/hod-dashboard" replace />;
        case 'tt_coordinator': return <Navigate to="/dashboard" replace />;
        default: return <Navigate to="/faculty-dashboard" replace />;
    }
}

export default function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <Routes>
                    <Route path="/login" element={<LoginPage />} />

                    {/* Authenticated routes */}
                    <Route element={<RequireAuth />}>

                        {/* Faculty dashboard - faculty only */}
                        <Route element={<RequireFaculty />}>
                            <Route path="/faculty-dashboard" element={<FacultyDashboardPage />} />
                        </Route>

                        {/* Preferences - accessible by faculty, coordinators, and HOD (they teach too) */}
                        <Route path="/preferences" element={<PreferencesPage />} />

                        {/* Coordinator-only routes (tt_coordinator + hod) */}
                        <Route element={<RequireCoordinator />}>
                            <Route path="/dashboard" element={<DashboardPage />} />
                            <Route path="/admin/allocation" element={<AllocationPage />} />
                            <Route path="/admin/preference-review" element={<PreferenceReviewDashboardPage />} />
                            <Route path="/admin/review" element={<ReviewPage />} />
                            <Route path="/admin/reports" element={<ReportsPage />} />
                            <Route path="/admin/window" element={<WindowPage />} />
                            <Route path="/admin/cycles" element={<CyclesPage />} />
                            <Route path="/admin/subjects" element={<CurriculumUploadPage />} />
                        </Route>

                        {/* HOD-only routes */}
                        <Route element={<RequireHOD />}>
                            <Route path="/hod-dashboard" element={<HODDashboardPage />} />
                            <Route path="/hod/staff" element={<StaffPage />} />
                            <Route path="/hod/staff-emails" element={<StaffEmailsPage />} />
                            <Route path="/hod/curriculum" element={<CurriculumUploadPage />} />
                            <Route path="/hod/approval" element={<FinalApprovalPage />} />
                        </Route>
                    </Route>

                    {/* Root and catch-all: role-aware redirect */}
                    <Route path="/" element={<RootRedirect />} />
                    <Route path="*" element={<RootRedirect />} />
                </Routes>
            </AuthProvider>
        </BrowserRouter>
    );
}
