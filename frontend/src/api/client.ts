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

export const runAllocationForAllSemesters = (data: { academic_year: string }) =>
    api.post('/allocation/run-all', data);

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

// ─── Coordinator Dashboard ───
export interface PreferenceDetail {
    subject_code: string;
    subject_name: string;
    program: string;
    semester: string;
    section: string;
    preference_rank: number;
}

export interface PreferenceRecord {
    staff_id: number;
    emp_code: string;
    name: string;
    total_subjects: number;
    submitted_preferences: number;
    status: 'Submitted' | 'Partial' | 'Not Submitted';
    preferences: PreferenceDetail[];
}

export interface PreferenceOverviewResponse {
    total_faculty: number;
    submitted_count: number;
    partial_count: number;
    not_submitted_count: number;
    records: PreferenceRecord[];
}

export interface AssignedSubject {
    subject_code: string;
    subject_name: string;
    program: string;
    semester: string;
    section: string;
    tch: number;
}

export interface AllocationRecord {
    staff_id: number;
    emp_code: string;
    name: string;
    total_tch: number;
    assigned_subjects_count: number;
    workload_status: 'Overloaded' | 'Balanced' | 'Underloaded';
    assigned_subjects: AssignedSubject[];
}

export interface AllocationOverviewResponse {
    total_faculty: number;
    overloaded_count: number;
    balanced_count: number;
    underloaded_count: number;
    records: AllocationRecord[];
}

export const fetchPreferenceOverview = (): Promise<{ data: PreferenceOverviewResponse }> =>
    api.get('/reports/coordinator/preference-overview');

export const fetchAllocationOverview = (): Promise<{ data: AllocationOverviewResponse }> =>
    api.get('/reports/coordinator/allocation-overview');

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
export const getStaffList = () => api.get('/admin/staff/list');

export const createStaff = (data: {
    emp_code: string; name: string; email: string;
    designation?: string; shift?: string; tch_norm?: number;
    is_coordinator?: boolean; is_class_teacher?: boolean;
    ct_program?: string; ct_section?: string; ct_semester?: string; ct_shift?: string;
    ct_curriculum_year?: string;
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

export const getCycleHistory = () => api.get('/cycles/history');

export const getActiveCycle = () => api.get('/cycles/active');

export const activateSemesterGroup = (data: {
    academic_year: string;
    semester_group: 'ODD' | 'EVEN';
}) => api.post('/cycles/activate-group', data);

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

// ─── Subject Management ───
export const getSubjectOfferings = (semesterId?: number, programId?: number) =>
    api.get('/subjects/offerings', { params: { semester_id: semesterId, program_id: programId } });

export const createSubjectOffering = (data: any) => api.post('/subjects/offerings', data);

export const deleteSubjectOffering = (id: number) => api.delete(`/subjects/offerings/${id}`);

export const getSubjectPrograms = () => api.get('/subjects/programs');

export const getSubjectSections = () => api.get('/subjects/sections');

export const getSubjectSemesters = () => api.get('/subjects/semesters');

export const createSection = (data: any) => api.post('/subjects/sections', data);

export const createProgram = (data: any) => api.post('/subjects/programs', data);

export const deleteSection = (id: number) => api.delete(`/subjects/sections/${id}`);

export const deleteProgram = (id: number) => api.delete(`/subjects/programs/${id}`);

// ─── Curriculum Upload ───
export const parseCurriculumFile = (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/curriculum/parse', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
};

export const confirmCurriculumImport = (subjects: any[]) =>
    api.post('/curriculum/confirm', { subjects });

export default api;
