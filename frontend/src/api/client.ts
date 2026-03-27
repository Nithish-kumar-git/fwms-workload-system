import axios from 'axios';

// Construct baseURL: use VITE_API_URL if set, otherwise fallback to relative '/api'
const baseURL = import.meta.env.VITE_API_URL 
    ? `${import.meta.env.VITE_API_URL}/api`
    : '/api';

const api = axios.create({
    baseURL,
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
    },
});

// JWT Bearer token interceptor — JWT is the ONLY identity signal
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
        params.delete('token');
        const clean = params.toString();
        const newUrl = window.location.pathname + (clean ? `?${clean}` : '');
        window.history.replaceState({}, '', newUrl);
    }
}

// Response interceptor: log auth failures
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response) {
            const status = error.response.status;
            if (status === 401 || status === 403) {
                console.warn(`Auth error ${status} on ${error.config?.url}`);
                // DO NOT clear localStorage — let AuthContext handle logout
            }
        } else if (error.request) {
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
export const runAllocation = (data: { academic_year: string; semester_id: number; program_id: number | null }) =>
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
    semester_id: number;
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

export const updateStaffEmail = (id: number, email: string) =>
    api.patch(`/admin/staff/${id}/email`, { email });

export const updateStaffRole = (id: number, role: string) =>
    api.patch(`/admin/staff/${id}/role`, { role });

export const deactivateStaff = (id: number) =>
    api.patch(`/admin/staff/${id}/deactivate`);

// ─── Academic Cycles ───
export const createCycle = (data: {
    academic_year: string;
    semester_id: number;
    start_date?: string;
    end_date?: string;
}) => api.post('/cycles', data);

export const activateCycle = (cycle_id: number) =>
    api.post('/cycles/activate', { cycle_id });

export const listCycles = () => api.get('/cycles');

export const getActiveCycle = () => api.get('/cycles/active');

// ─── Pipeline & Approval ───
export const getPipelineStatus = () => api.get('/reports/pipeline-status');
export const approveWorkload = () => api.post('/reports/approve-workload');

// ─── Exports (snapshot-enforced) ───
export const downloadMasterWorkload = () =>
    api.get('/reports/export/master-workload.xlsx', { responseType: 'blob' });
export const downloadWorkloadPdf = () =>
    api.get('/reports/export/workload.pdf', { responseType: 'blob' });

// ─── Auth ───
export const getCurrentUser = () => api.get('/auth/me');
export const logout = () => api.post('/auth/logout');

export default api;
