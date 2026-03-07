import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
    },
});

// JWT Bearer token interceptor
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('jwt_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Capture JWT from OAuth callback redirect (?token=...)
if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (token) {
        localStorage.setItem('jwt_token', token);
        // Clean URL
        window.history.replaceState({}, '', window.location.pathname);
    }
}

// Response interceptor: handle auth failures + network errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response) {
            const status = error.response.status;
            // Auth failure → clear token, redirect to login
            if (status === 401 || status === 403) {
                localStorage.removeItem('jwt_token');
                if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
                    window.location.href = '/login';
                }
            }
        } else if (error.request) {
            // Network error — server unreachable
            console.error('Server unavailable:', error.message);
        }
        return Promise.reject(error);
    }
);

// ─── Preferences ───
export const submitPreference = (data: {
    subject_offering_id: number;
    preference_number: number;
}) => api.post('/preferences', data);

export const getMyPreferences = () => api.get('/preferences/me');

export const deletePreference = (id: number) => api.delete(`/preferences/${id}`);

export const getPreferenceStatus = () => api.get('/preferences/status');

// ─── Allocation ───
export const runAllocation = (data: { academic_year: string; semester_type: string; program_id: number | null }) =>
    api.post('/allocation/run', data);

// ─── Admin ───
export const getAdminAllocations = () => api.get('/admin/allocations');

export const overrideAllocation = (id: number, newStaffId: number) =>
    api.put(`/admin/allocation/${id}`, { new_staff_id: newStaffId });

export const reassignSubject = (data: {
    subject_offering_id: number;
    from_staff_id: number;
    to_staff_id: number;
}) => api.post('/admin/reassign', data);

export const freezeAllocation = () => api.post('/admin/allocation/freeze');
export const unfreezeAllocation = () => api.post('/admin/allocation/unfreeze');

export const getWorkloadSummary = () => api.get('/admin/workload-summary');

// ─── Reports ───
export const getFacultyWorkload = () => api.get('/reports/faculty-workload');
export const getSubjectSummary = () => api.get('/reports/subject-summary');
export const getDepartmentSummary = () => api.get('/reports/department-summary');

export const downloadExcel = () =>
    api.get('/reports/export/workload.xlsx', { responseType: 'blob' });

export const downloadPdf = () =>
    api.get('/reports/export/workload.pdf', { responseType: 'blob' });

// ─── Preference Window ───
export const openPrefWindow = (data: {
    academic_year: string;
    semester_type: string;
    start_time: string;
    end_time: string;
}) => api.post('/pref-window/open', data);

export const closePrefWindow = () => api.post('/pref-window/close');

export const getPrefWindowStatus = () => api.get('/pref-window/status');

// ─── Staff Management ───
export const getStaffList = () => api.get('/admin/staff');

export const createStaff = (data: {
    emp_code: string; name: string; email: string;
    designation?: string; shift?: string; tch_norm?: number;
    is_coordinator?: boolean; is_class_teacher?: boolean;
    ct_program?: string; ct_section?: string; ct_semester?: string; ct_shift?: string;
}) => api.post('/admin/staff', data);

export const updateStaff = (id: number, data: Record<string, unknown>) =>
    api.put(`/admin/staff/${id}`, data);

export const deactivateStaff = (id: number) =>
    api.patch(`/admin/staff/${id}/deactivate`);

// ─── Academic Cycles ───
export const createCycle = (data: {
    academic_year: string;
    semester_type: string;
    start_date?: string;
    end_date?: string;
}) => api.post('/cycles', data);

export const activateCycle = (cycle_id: number) =>
    api.post('/cycles/activate', { cycle_id });

export const listCycles = () => api.get('/cycles');

export const getActiveCycle = () => api.get('/cycles/active');

// ─── Auth ───
export const getCurrentUser = () => api.get('/auth/me');
export const logout = () => api.post('/auth/logout');

export default api;
