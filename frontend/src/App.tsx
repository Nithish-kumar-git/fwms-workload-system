import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import PreferencesPage from './pages/PreferencesPage';
import AllocationPage from './pages/AllocationPage';
import ReviewPage from './pages/ReviewPage';
import ReportsPage from './pages/ReportsPage';
import WindowPage from './pages/WindowPage';
import CyclesPage from './pages/CyclesPage';
import StaffPage from './pages/StaffPage';

function Layout() {
  return (
    <>
      <Navbar />
      <Outlet />
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/preferences" element={<PreferencesPage />} />
          <Route path="/admin/allocation" element={<AllocationPage />} />
          <Route path="/admin/review" element={<ReviewPage />} />
          <Route path="/admin/reports" element={<ReportsPage />} />
          <Route path="/admin/window" element={<WindowPage />} />
          <Route path="/admin/cycles" element={<CyclesPage />} />
          <Route path="/admin/staff" element={<StaffPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
