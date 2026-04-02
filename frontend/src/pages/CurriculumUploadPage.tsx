import { useEffect, useState } from 'react';
import { Plus, Trash2, RefreshCw, BookOpen, Users, HelpCircle } from 'lucide-react';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import Modal from '../components/Modal';
import {
    getSubjectOfferings, createSubjectOffering, deleteSubjectOffering,
    getSubjectPrograms, getSubjectSections, getSubjectSemesters,
    createSection, createProgram, deleteSection, deleteProgram
} from '../api/client';

interface Offering {
    id: number;
    code: string;
    name: string;
    program_name: string;
    semester_label: string;
    section_label: string;
    shift: number;
    l: number;
    t: number;
    p: number;
    tch: number;
    credits: number;
    course_category: string;
    student_strength: number;
    curriculum_year: string;
}

interface Program {
    id: number;
    name: string;
    ug_pg: string;
}

interface Section {
    id: number;
    label: string;
    shift: number;
}

interface Semester {
    id: number;
    label: string;
}

export default function CurriculumUploadPage() {
    const [activeTab, setActiveTab] = useState<'offerings' | 'programs' | 'help'>('offerings');

    const [offerings, setOfferings] = useState<Offering[]>([]);
    const [programs, setPrograms] = useState<Program[]>([]);
    const [sections, setSections] = useState<Section[]>([]);
    const [semesters, setSemesters] = useState<Semester[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAddForm, setShowAddForm] = useState(false);
    const [filterSemester, setFilterSemester] = useState<number | null>(null);
    const [filterProgram, setFilterProgram] = useState<number | null>(null);
    const { toasts, addToast, removeToast } = useToast();

    const [formData, setFormData] = useState({
        course_code: '',
        course_name: '',
        program_id: 0,
        semester_id: 0,
        section_id: 0,
        shift: 1,
        l: 0,
        t: 0,
        p: 0,
        credits: 0,
        course_category: 'CC',
        student_strength: 0,
        curriculum_year: '2022',
    });

    const [newProgram, setNewProgram] = useState({ name: '', ug_pg: 'UG' });
    const [newSection, setNewSection] = useState({ label: '', shift: 1 });

    const loadData = async () => {
        setLoading(true);
        try {
            const [offeringsRes, programsRes, sectionsRes, semestersRes] = await Promise.all([
                getSubjectOfferings(filterSemester || undefined, filterProgram || undefined),
                getSubjectPrograms(),
                getSubjectSections(),
                getSubjectSemesters(),
            ]);
            setOfferings(offeringsRes.data);
            setPrograms(programsRes.data);
            setSections(sectionsRes.data);
            setSemesters(semestersRes.data);
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Failed to load data', 'error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadData(); }, [filterSemester, filterProgram]);

    const handleAddOffering = async () => {
        if (!formData.course_code || !formData.course_name || !formData.program_id || !formData.semester_id || !formData.section_id) {
            addToast('Please fill all required fields', 'error');
            return;
        }
        try {
            await createSubjectOffering(formData);
            addToast('Subject offering created successfully', 'success');
            setShowAddForm(false);
            setFormData({
                course_code: '', course_name: '', program_id: 0, semester_id: 0,
                section_id: 0, shift: 1, l: 0, t: 0, p: 0, credits: 0,
                course_category: 'CC', student_strength: 0, curriculum_year: '2022',
            });
            loadData();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Failed to create offering', 'error');
        }
    };

    const handleDeleteOffering = async (id: number) => {
        if (!confirm('Are you sure you want to remove this subject offering?')) return;
        try {
            const res = await deleteSubjectOffering(id);
            addToast(res.data.message || 'Subject removed', 'success');
            loadData();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Failed to delete offering', 'error');
        }
    };

    const handleAddProgram = async () => {
        if (!newProgram.name) {
            addToast('Please enter program name', 'error');
            return;
        }
        try {
            await createProgram(newProgram);
            addToast('Program created successfully', 'success');
            setNewProgram({ name: '', ug_pg: 'UG' });
            loadData();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Failed to create program', 'error');
        }
    };

    const handleAddSection = async () => {
        if (!newSection.label) {
            addToast('Please enter section label', 'error');
            return;
        }
        try {
            await createSection(newSection);
            addToast('Section created successfully', 'success');
            setNewSection({ label: '', shift: 1 });
            loadData();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Failed to create section', 'error');
        }
    };

    const handleDeleteProgram = async (id: number, name: string) => {
        if (!confirm(`Delete program "${name}"? This will fail if the program is used in any active subject offerings.`)) {
            return;
        }
        try {
            await deleteProgram(id);
            addToast('Program deleted successfully', 'success');
            loadData();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Failed to delete program', 'error');
        }
    };

    const handleDeleteSection = async (id: number, label: string) => {
        if (!confirm(`Delete section "${label}"? This will fail if the section is used in any active subject offerings.`)) {
            return;
        }
        try {
            await deleteSection(id);
            addToast('Section deleted successfully', 'success');
            loadData();
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Failed to delete section', 'error');
        }
    };

    return (
        <div className="page-container">
            <ToastContainer toasts={toasts} onRemove={removeToast} />

            <div className="page-header">
                <div>
                    <h1 className="page-title">Subject Management</h1>
                    <p className="page-subtitle">Manage subject offerings, programs, and sections</p>
                </div>
                <button onClick={loadData} className="btn btn-outline">
                    <RefreshCw size={16} />Refresh
                </button>
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid #e5e7eb' }}>
                <button
                    onClick={() => setActiveTab('offerings')}
                    style={{
                        padding: '0.75rem 1.5rem',
                        background: 'transparent',
                        border: 'none',
                        borderBottom: activeTab === 'offerings' ? '2px solid #2563eb' : '2px solid transparent',
                        color: activeTab === 'offerings' ? '#2563eb' : '#6b7280',
                        fontWeight: activeTab === 'offerings' ? 600 : 500,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                    }}
                >
                    <BookOpen size={18} />Subject Offerings
                </button>
                <button
                    onClick={() => setActiveTab('programs')}
                    style={{
                        padding: '0.75rem 1.5rem',
                        background: 'transparent',
                        border: 'none',
                        borderBottom: activeTab === 'programs' ? '2px solid #2563eb' : '2px solid transparent',
                        color: activeTab === 'programs' ? '#2563eb' : '#6b7280',
                        fontWeight: activeTab === 'programs' ? 600 : 500,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                    }}
                >
                    <Users size={18} />Programs & Sections
                </button>
                <button
                    onClick={() => setActiveTab('help')}
                    style={{
                        padding: '0.75rem 1.5rem',
                        background: 'transparent',
                        border: 'none',
                        borderBottom: activeTab === 'help' ? '2px solid #2563eb' : '2px solid transparent',
                        color: activeTab === 'help' ? '#2563eb' : '#6b7280',
                        fontWeight: activeTab === 'help' ? 600 : 500,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                    }}
                >
                    <HelpCircle size={18} />How to Use
                </button>
            </div>

            {/* TAB 1: Subject Offerings */}
            {activeTab === 'offerings' && (
                <div>
                    <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', alignItems: 'center' }}>
                        <select
                            className="form-input"
                            value={filterSemester || ''}
                            onChange={(e) => setFilterSemester(e.target.value ? Number(e.target.value) : null)}
                            style={{ width: '200px' }}
                        >
                            <option value="">All Semesters</option>
                            {semesters.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
                        </select>
                        <select
                            className="form-input"
                            value={filterProgram || ''}
                            onChange={(e) => setFilterProgram(e.target.value ? Number(e.target.value) : null)}
                            style={{ width: '250px' }}
                        >
                            <option value="">All Programs</option>
                            {programs.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                        </select>
                        <button onClick={() => setShowAddForm(true)} className="btn btn-primary" style={{ marginLeft: 'auto' }}>
                            <Plus size={16} />Add Subject
                        </button>
                    </div>

                    {loading ? (
                        <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                            <p style={{ color: '#6b7280' }}>Loading offerings...</p>
                        </div>
                    ) : offerings.length === 0 ? (
                        <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
                            <p style={{ color: '#6b7280' }}>No subject offerings found. Add one to get started.</p>
                        </div>
                    ) : (
                        <div className="glass-card" style={{ overflow: 'hidden' }}>
                            <div className="overflow-x-auto">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Code</th><th>Name</th><th>Program</th><th>Semester</th>
                                            <th>Section</th><th>Shift</th><th>L</th><th>T</th><th>P</th>
                                            <th>TCH</th><th>Category</th><th>Regulation</th><th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {offerings.map(o => (
                                            <tr key={o.id}>
                                                <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{o.code}</td>
                                                <td>{o.name}</td>
                                                <td>{o.program_name}</td>
                                                <td><span className="badge badge-info">{o.semester_label}</span></td>
                                                <td><span className="badge badge-warning">{o.section_label}</span></td>
                                                <td>{o.shift}</td>
                                                <td>{o.l}</td>
                                                <td>{o.t}</td>
                                                <td>{o.p}</td>
                                                <td style={{ fontWeight: 600, color: '#2563eb' }}>{o.tch}</td>
                                                <td>{o.course_category}</td>
                                                <td><span className="badge badge-success">{o.curriculum_year}</span></td>
                                                <td>
                                                    <button onClick={() => handleDeleteOffering(o.id)} className="btn btn-danger text-[13px] py-1 px-3">
                                                        <Trash2 size={14} />Remove
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* TAB 2: Programs & Sections */}
            {activeTab === 'programs' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                    {/* Add Program */}
                    <div className="glass-card" style={{ padding: '1.5rem' }}>
                        <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>Add Program</h3>
                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                                Program Name
                            </label>
                            <input
                                type="text"
                                className="form-input"
                                value={newProgram.name}
                                onChange={(e) => setNewProgram({ ...newProgram, name: e.target.value })}
                                placeholder="e.g., MCA(AI)"
                            />
                        </div>
                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                                Type
                            </label>
                            <select
                                className="form-input"
                                value={newProgram.ug_pg}
                                onChange={(e) => setNewProgram({ ...newProgram, ug_pg: e.target.value })}
                            >
                                <option value="UG">UG</option>
                                <option value="PG">PG</option>
                            </select>
                        </div>
                        <button onClick={handleAddProgram} className="btn btn-primary" style={{ width: '100%' }}>
                            <Plus size={16} />Add Program
                        </button>

                        <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #e5e7eb' }}>
                            <h4 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem', color: '#6b7280' }}>
                                Existing Programs ({programs.length})
                            </h4>
                            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                                {programs.map(p => (
                                    <div key={p.id} style={{ padding: '0.5rem', borderBottom: '1px solid #f3f4f6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            <span style={{ fontWeight: 500 }}>{p.name}</span>
                                            <span className="badge badge-info">{p.ug_pg}</span>
                                        </div>
                                        <button
                                            onClick={() => handleDeleteProgram(p.id, p.name)}
                                            className="btn btn-danger"
                                            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Add Section */}
                    <div className="glass-card" style={{ padding: '1.5rem' }}>
                        <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>Add Section</h3>
                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                                Section Label
                            </label>
                            <input
                                type="text"
                                className="form-input"
                                value={newSection.label}
                                onChange={(e) => setNewSection({ ...newSection, label: e.target.value })}
                                placeholder="e.g., F or A+B+C+D"
                            />
                        </div>
                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                                Shift
                            </label>
                            <select
                                className="form-input"
                                value={newSection.shift}
                                onChange={(e) => setNewSection({ ...newSection, shift: Number(e.target.value) })}
                            >
                                <option value={1}>Shift 1</option>
                                <option value={2}>Shift 2</option>
                            </select>
                        </div>
                        <button onClick={handleAddSection} className="btn btn-primary" style={{ width: '100%' }}>
                            <Plus size={16} />Add Section
                        </button>

                        <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #e5e7eb' }}>
                            <h4 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem', color: '#6b7280' }}>
                                Existing Sections ({sections.length})
                            </h4>
                            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                                {sections.map(s => (
                                    <div key={s.id} style={{ padding: '0.5rem', borderBottom: '1px solid #f3f4f6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            <span style={{ fontWeight: 500 }}>{s.label}</span>
                                            <span className="badge badge-warning">Shift {s.shift}</span>
                                        </div>
                                        <button
                                            onClick={() => handleDeleteSection(s.id, s.label)}
                                            className="btn btn-danger"
                                            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* TAB 3: How to Use */}
            {activeTab === 'help' && (
                <div className="glass-card" style={{ padding: '2rem' }}>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' }}>How to Use Subject Management</h3>
                    
                    <div style={{ marginBottom: '1.5rem' }}>
                        <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: '#2563eb' }}>
                            Before Opening Preference Window
                        </h4>
                        <p style={{ color: '#6b7280', lineHeight: '1.6' }}>
                            Add all subject offerings here before opening the preference window. Faculty can only select from subjects that exist in the system.
                        </p>
                    </div>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: '#2563eb' }}>
                            What is a Subject Offering?
                        </h4>
                        <p style={{ color: '#6b7280', lineHeight: '1.6' }}>
                            Each offering represents one subject for one specific program, semester, and section combination. 
                            For example, "Data Structures" for "MCA(General)" in "Semester II" for "Section A" is one offering.
                        </p>
                    </div>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: '#2563eb' }}>
                            Handling Electives
                        </h4>
                        <p style={{ color: '#6b7280', lineHeight: '1.6' }}>
                            For elective subjects offered to multiple classes, add each as a separate offering. 
                            For example, if "Cloud Computing" is an elective for both MCA(General) and MCA(BD), create two separate offerings.
                        </p>
                    </div>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: '#2563eb' }}>
                            Removing Subjects
                        </h4>
                        <p style={{ color: '#6b7280', lineHeight: '1.6' }}>
                            If a subject has existing preferences or allocations, removing it will archive it (hidden from new preferences but history preserved). 
                            If no preferences or allocations exist, it will be permanently deleted.
                        </p>
                    </div>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: '#2563eb' }}>
                            Adding Programs and Sections
                        </h4>
                        <p style={{ color: '#6b7280', lineHeight: '1.6' }}>
                            Before adding subject offerings, make sure the required programs and sections exist. 
                            Use the "Programs & Sections" tab to add new programs (e.g., MCA(AI)) or sections (e.g., F, A+B+C+D) first.
                        </p>
                    </div>

                    <div style={{ padding: '1rem', background: '#eff6ff', borderRadius: '0.5rem', borderLeft: '4px solid #2563eb' }}>
                        <p style={{ color: '#1e40af', fontSize: '0.875rem', fontWeight: 500 }}>
                            💡 Tip: Use filters in the Subject Offerings tab to view offerings by semester or program for easier management.
                        </p>
                    </div>
                </div>
            )}

            {/* Add Subject Modal */}
            <Modal isOpen={showAddForm} onClose={() => setShowAddForm(false)} title="Add Subject Offering">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                            Course Code *
                        </label>
                        <input
                            type="text"
                            className="form-input"
                            value={formData.course_code}
                            onChange={(e) => setFormData({ ...formData, course_code: e.target.value })}
                            placeholder="e.g., CCA42802"
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                            Course Name *
                        </label>
                        <input
                            type="text"
                            className="form-input"
                            value={formData.course_name}
                            onChange={(e) => setFormData({ ...formData, course_name: e.target.value })}
                            placeholder="e.g., Data Structures"
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                            Program *
                        </label>
                        <select
                            className="form-input"
                            value={formData.program_id}
                            onChange={(e) => setFormData({ ...formData, program_id: Number(e.target.value) })}
                        >
                            <option value={0}>Select Program</option>
                            {programs.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                        </select>
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                            Semester *
                        </label>
                        <select
                            className="form-input"
                            value={formData.semester_id}
                            onChange={(e) => setFormData({ ...formData, semester_id: Number(e.target.value) })}
                        >
                            <option value={0}>Select Semester</option>
                            {semesters.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
                        </select>
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                            Section *
                        </label>
                        <select
                            className="form-input"
                            value={formData.section_id}
                            onChange={(e) => setFormData({ ...formData, section_id: Number(e.target.value) })}
                        >
                            <option value={0}>Select Section</option>
                            {sections.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
                        </select>
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                            Shift *
                        </label>
                        <select
                            className="form-input"
                            value={formData.shift}
                            onChange={(e) => setFormData({ ...formData, shift: Number(e.target.value) })}
                        >
                            <option value={1}>Shift 1</option>
                            <option value={2}>Shift 2</option>
                        </select>
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                            L (Lecture Hours) *
                        </label>
                        <input
                            type="number"
                            className="form-input"
                            value={formData.l}
                            onChange={(e) => setFormData({ ...formData, l: Number(e.target.value) })}
                            min={0}
                            max={10}
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                            T (Tutorial Hours) *
                        </label>
                        <input
                            type="number"
                            className="form-input"
                            value={formData.t}
                            onChange={(e) => setFormData({ ...formData, t: Number(e.target.value) })}
                            min={0}
                            max={10}
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                            P (Practical Hours) *
                        </label>
                        <input
                            type="number"
                            className="form-input"
                            value={formData.p}
                            onChange={(e) => setFormData({ ...formData, p: Number(e.target.value) })}
                            min={0}
                            max={10}
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                            Credits *
                        </label>
                        <input
                            type="number"
                            className="form-input"
                            value={formData.credits}
                            onChange={(e) => setFormData({ ...formData, credits: Number(e.target.value) })}
                            min={0}
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                            Course Category *
                        </label>
                        <select
                            className="form-input"
                            value={formData.course_category}
                            onChange={(e) => setFormData({ ...formData, course_category: e.target.value })}
                        >
                            <option value="CC">CC - Core Course</option>
                            <option value="DE">DE - Discipline Elective</option>
                            <option value="BS">BS - Basic Science</option>
                            <option value="HS">HS - Humanities & Social Science</option>
                            <option value="NC">NC - Non-Credit</option>
                            <option value="VA">VA - Value Added</option>
                            <option value="AE">AE - Audit Elective</option>
                            <option value="SE">SE - Skill Enhancement</option>
                            <option value="RP">RP - Research Project</option>
                        </select>
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                            Student Strength *
                        </label>
                        <input
                            type="number"
                            className="form-input"
                            value={formData.student_strength}
                            onChange={(e) => setFormData({ ...formData, student_strength: Number(e.target.value) })}
                            min={0}
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#6b7280', marginBottom: '0.375rem' }}>
                            Curriculum / Regulation Year *
                        </label>
                        <select
                            className="form-input"
                            value={formData.curriculum_year}
                            onChange={(e) => setFormData({ ...formData, curriculum_year: e.target.value })}
                        >
                            <option value="2022">2022 Regulation (MCA current)</option>
                            <option value="2023">2023-24 Regulation (BCA current)</option>
                            <option value="2024">2024 Regulation</option>
                            <option value="2025">2025 Regulation</option>
                            <option value="2026">2026 Regulation (new batches)</option>
                        </select>
                    </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                    <button onClick={() => setShowAddForm(false)} className="btn btn-outline">Cancel</button>
                    <button onClick={handleAddOffering} className="btn btn-primary">Add Subject</button>
                </div>
            </Modal>
        </div>
    );
}
