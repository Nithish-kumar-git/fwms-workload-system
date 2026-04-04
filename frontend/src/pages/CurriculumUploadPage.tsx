import { useEffect, useState } from 'react';
import { Plus, Trash2, RefreshCw, BookOpen, Users, HelpCircle, Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import Modal from '../components/Modal';
import {
    getSubjectOfferings, createSubjectOffering, deleteSubjectOffering,
    getSubjectPrograms, getSubjectSections, getSubjectSemesters,
    createSection, createProgram, deleteSection, deleteProgram,
    parseCurriculumFile, confirmCurriculumImport
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
    const [activeTab, setActiveTab] = useState<'offerings' | 'programs' | 'upload' | 'help'>('offerings');

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

    // Upload state
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [parsedSubjects, setParsedSubjects] = useState<any[]>([]);
    const [uploadStep, setUploadStep] = useState<'select' | 'preview' | 'result'>('select');
    const [importResult, setImportResult] = useState<any>(null);

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

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setUploadFile(file);
        }
    };

    const handleParseFile = async () => {
        if (!uploadFile) {
            addToast('Please select a file first', 'error');
            return;
        }
        
        try {
            const res = await parseCurriculumFile(uploadFile);
            setParsedSubjects(res.data.subjects);
            setUploadStep('preview');
            addToast(res.data.message, 'success');
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Failed to parse file', 'error');
        }
    };

    const handleConfirmImport = async () => {
        try {
            const res = await confirmCurriculumImport(parsedSubjects);
            setImportResult(res.data);
            setUploadStep('result');
            addToast(res.data.message, res.data.failed > 0 ? 'warning' : 'success');
            loadData(); // Refresh offerings list
        } catch (err: any) {
            addToast(err.response?.data?.detail || 'Failed to import subjects', 'error');
        }
    };

    const handleResetUpload = () => {
        setUploadFile(null);
        setParsedSubjects([]);
        setUploadStep('select');
        setImportResult(null);
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
                    onClick={() => setActiveTab('upload')}
                    style={{
                        padding: '0.75rem 1.5rem',
                        background: 'transparent',
                        border: 'none',
                        borderBottom: activeTab === 'upload' ? '2px solid #2563eb' : '2px solid transparent',
                        color: activeTab === 'upload' ? '#2563eb' : '#6b7280',
                        fontWeight: activeTab === 'upload' ? 600 : 500,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                    }}
                >
                    <Upload size={18} />Bulk Upload
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
                <div style={{display:'flex', flexDirection:'column', gap:'24px'}}>
                    {/* EXPLAINER */}
                    <div style={{background:'#f0f9ff', border:'1px solid #bae6fd', borderRadius:'10px', padding:'14px 18px'}}>
                        <div style={{fontWeight:'600', color:'#0369a1', fontSize:'14px', marginBottom:'4px'}}>How Programs & Sections Work</div>
                        <div style={{color:'#0c4a6e', fontSize:'13px'}}>
                            Programs (e.g. MCA(General), BCA(Cyber)) and Sections (e.g. A, B, C) are independent. When you add a subject offering, you combine a Program + Section + Semester together.
                            Add the program and section here first, then use the Subject Offerings tab to assign subjects to them.
                        </div>
                    </div>

                    {/* PROGRAMS SECTION */}
                    <div className="glass-card" style={{padding:'20px'}}>
                        <h3 style={{fontSize:'16px', fontWeight:'700', marginBottom:'16px', color:'#1d4ed8'}}>📚 Programs</h3>
                        {/* Add Program form - horizontal layout */}
                        <div style={{display:'flex', gap:'10px', marginBottom:'16px', flexWrap:'wrap'}}>
                            <input 
                                placeholder="Program name, e.g. MCA(AI) or BCA(Data Science)"
                                value={newProgram.name}
                                onChange={(e) => setNewProgram({ ...newProgram, name: e.target.value })}
                                style={{flex:2, minWidth:'200px', padding:'8px 12px', border:'1px solid #e5e7eb', borderRadius:'8px'}}
                            />
                            <select 
                                value={newProgram.ug_pg} 
                                onChange={(e) => setNewProgram({ ...newProgram, ug_pg: e.target.value })}
                                style={{flex:1, minWidth:'100px', padding:'8px 12px', border:'1px solid #e5e7eb', borderRadius:'8px'}}
                            >
                                <option value="UG">UG (Undergraduate)</option>
                                <option value="PG">PG (Postgraduate)</option>
                            </select>
                            <button 
                                onClick={handleAddProgram} 
                                style={{padding:'8px 16px', background:'#1d4ed8', color:'white', borderRadius:'8px', border:'none', cursor:'pointer'}}
                            >
                                + Add Program
                            </button>
                        </div>
                        {/* Programs list */}
                        <div style={{display:'flex', flexWrap:'wrap', gap:'8px'}}>
                            {programs.map(p => (
                                <div key={p.id} style={{display:'flex', alignItems:'center', gap:'8px', background:'#f8fafc', border:'1px solid #e2e8f0', borderRadius:'8px', padding:'6px 12px'}}>
                                    <span style={{fontWeight:'600', fontSize:'14px'}}>{p.name}</span>
                                    <span style={{fontSize:'11px', background: p.ug_pg==='PG' ? '#dbeafe':'#dcfce7', color: p.ug_pg==='PG' ? '#1d4ed8':'#166534', padding:'2px 6px', borderRadius:'4px'}}>
                                        {p.ug_pg}
                                    </span>
                                    <button 
                                        onClick={() => handleDeleteProgram(p.id, p.name)} 
                                        style={{color:'#ef4444', background:'none', border:'none', cursor:'pointer', fontSize:'16px'}}
                                    >
                                        ×
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* SECTIONS SECTION */}
                    <div className="glass-card" style={{padding:'20px'}}>
                        <h3 style={{fontSize:'16px', fontWeight:'700', marginBottom:'16px', color:'#7c3aed'}}>🏷 Sections</h3>
                        {/* Add Section form */}
                        <div style={{display:'flex', gap:'10px', marginBottom:'16px', flexWrap:'wrap'}}>
                            <input 
                                placeholder="Section label, e.g. F or A+B+C+D"
                                value={newSection.label}
                                onChange={(e) => setNewSection({ ...newSection, label: e.target.value })}
                                style={{flex:2, minWidth:'150px', padding:'8px 12px', border:'1px solid #e5e7eb', borderRadius:'8px'}}
                            />
                            <select 
                                value={newSection.shift} 
                                onChange={(e) => setNewSection({ ...newSection, shift: Number(e.target.value) })}
                                style={{flex:1, minWidth:'120px', padding:'8px 12px', border:'1px solid #e5e7eb', borderRadius:'8px'}}
                            >
                                <option value={1}>Shift 1 (Morning)</option>
                                <option value={2}>Shift 2 (Afternoon)</option>
                            </select>
                            <button 
                                onClick={handleAddSection} 
                                style={{padding:'8px 16px', background:'#7c3aed', color:'white', borderRadius:'8px', border:'none', cursor:'pointer'}}
                            >
                                + Add Section
                            </button>
                        </div>
                        {/* Sections grouped by shift */}
                        <div style={{marginBottom:'12px'}}>
                            <div style={{fontWeight:'600', fontSize:'13px', color:'#6b7280', marginBottom:'8px'}}>SHIFT 1 SECTIONS</div>
                            <div style={{display:'flex', flexWrap:'wrap', gap:'8px'}}>
                                {sections.filter(s => s.shift === 1).map(s => (
                                    <div key={s.id} style={{display:'flex', alignItems:'center', gap:'6px', background:'#eff6ff', border:'1px solid #bfdbfe', borderRadius:'8px', padding:'6px 12px'}}>
                                        <span style={{fontWeight:'700', fontSize:'14px', color:'#1d4ed8'}}>{s.label}</span>
                                        <button 
                                            onClick={() => handleDeleteSection(s.id, s.label)} 
                                            style={{color:'#ef4444', background:'none', border:'none', cursor:'pointer', fontSize:'16px'}}
                                        >
                                            ×
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div>
                            <div style={{fontWeight:'600', fontSize:'13px', color:'#6b7280', marginBottom:'8px'}}>SHIFT 2 SECTIONS</div>
                            <div style={{display:'flex', flexWrap:'wrap', gap:'8px'}}>
                                {sections.filter(s => s.shift === 2).map(s => (
                                    <div key={s.id} style={{display:'flex', alignItems:'center', gap:'6px', background:'#faf5ff', border:'1px solid #e9d5ff', borderRadius:'8px', padding:'6px 12px'}}>
                                        <span style={{fontWeight:'700', fontSize:'14px', color:'#7c3aed'}}>{s.label}</span>
                                        <button 
                                            onClick={() => handleDeleteSection(s.id, s.label)} 
                                            style={{color:'#ef4444', background:'none', border:'none', cursor:'pointer', fontSize:'16px'}}
                                        >
                                            ×
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* TAB 3: Bulk Upload */}
            {activeTab === 'upload' && (
                <div>
                    {uploadStep === 'select' && (
                        <div className="glass-card" style={{ padding: '2rem' }}>
                            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>Upload Curriculum File</h3>
                            <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
                                Upload an Excel (.xlsx) or Word (.docx) file containing subject data. The file should have columns for:
                                Course Code, Course Name, L, T, P, Credits, Category, Program, Semester, Section, Shift, Student Strength, Curriculum Year.
                            </p>
                            
                            <div style={{ marginBottom: '1.5rem' }}>
                                <input
                                    type="file"
                                    accept=".xlsx,.xls,.docx,.doc"
                                    onChange={handleFileSelect}
                                    style={{
                                        padding: '0.75rem',
                                        border: '2px dashed #d1d5db',
                                        borderRadius: '0.5rem',
                                        width: '100%',
                                        cursor: 'pointer'
                                    }}
                                />
                            </div>

                            {uploadFile && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', padding: '0.75rem', background: '#f3f4f6', borderRadius: '0.5rem' }}>
                                    <FileText size={20} color="#6b7280" />
                                    <span style={{ color: '#374151', fontWeight: 500 }}>{uploadFile.name}</span>
                                    <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>({(uploadFile.size / 1024).toFixed(1)} KB)</span>
                                </div>
                            )}

                            <button
                                onClick={handleParseFile}
                                disabled={!uploadFile}
                                className="btn btn-primary"
                                style={{ opacity: uploadFile ? 1 : 0.5 }}
                            >
                                <Upload size={16} />Parse File
                            </button>
                        </div>
                    )}

                    {uploadStep === 'preview' && (
                        <div>
                            <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                                <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem' }}>Preview Parsed Subjects</h3>
                                <p style={{ color: '#6b7280', marginBottom: '1rem' }}>
                                    Found {parsedSubjects.length} subjects. Review and confirm to import.
                                </p>
                                <div style={{ display: 'flex', gap: '1rem' }}>
                                    <button onClick={handleConfirmImport} className="btn btn-primary">
                                        <CheckCircle size={16} />Confirm Import
                                    </button>
                                    <button onClick={handleResetUpload} className="btn btn-outline">
                                        Cancel
                                    </button>
                                </div>
                            </div>

                            <div className="glass-card" style={{ overflow: 'hidden' }}>
                                <div className="overflow-x-auto">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>Code</th><th>Name</th><th>Program</th><th>Semester</th>
                                                <th>Section</th><th>L</th><th>T</th><th>P</th><th>Credits</th>
                                                <th>Category</th><th>Regulation</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {parsedSubjects.map((s, idx) => (
                                                <tr key={idx}>
                                                    <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{s.course_code}</td>
                                                    <td>{s.course_name}</td>
                                                    <td>{s.program_name}</td>
                                                    <td><span className="badge badge-info">{s.semester_label}</span></td>
                                                    <td><span className="badge badge-warning">{s.section_label}</span></td>
                                                    <td>{s.l}</td>
                                                    <td>{s.t}</td>
                                                    <td>{s.p}</td>
                                                    <td>{s.credits}</td>
                                                    <td>{s.course_category}</td>
                                                    <td><span className="badge badge-success">{s.curriculum_year}</span></td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}

                    {uploadStep === 'result' && importResult && (
                        <div>
                            <div className="glass-card" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                                    {importResult.failed === 0 ? (
                                        <CheckCircle size={48} color="#10b981" />
                                    ) : (
                                        <AlertCircle size={48} color="#f59e0b" />
                                    )}
                                    <div>
                                        <h3 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '0.25rem' }}>Import Complete</h3>
                                        <p style={{ color: '#6b7280' }}>{importResult.message}</p>
                                    </div>
                                </div>

                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                                    <div style={{ padding: '1rem', background: '#d1fae5', borderRadius: '0.5rem' }}>
                                        <div style={{ fontSize: '2rem', fontWeight: 700, color: '#065f46' }}>{importResult.imported}</div>
                                        <div style={{ color: '#047857', fontSize: '0.875rem' }}>Successfully Imported</div>
                                    </div>
                                    <div style={{ padding: '1rem', background: '#fee2e2', borderRadius: '0.5rem' }}>
                                        <div style={{ fontSize: '2rem', fontWeight: 700, color: '#991b1b' }}>{importResult.failed}</div>
                                        <div style={{ color: '#dc2626', fontSize: '0.875rem' }}>Failed</div>
                                    </div>
                                </div>

                                {importResult.errors && importResult.errors.length > 0 && (
                                    <div style={{ marginBottom: '1.5rem' }}>
                                        <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: '#dc2626' }}>Errors:</h4>
                                        <div style={{ maxHeight: '200px', overflowY: 'auto', background: '#fef2f2', padding: '1rem', borderRadius: '0.5rem' }}>
                                            {importResult.errors.map((err: string, idx: number) => (
                                                <div key={idx} style={{ fontSize: '0.875rem', color: '#991b1b', marginBottom: '0.25rem' }}>
                                                    • {err}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                <button onClick={handleResetUpload} className="btn btn-primary">
                                    Upload Another File
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* TAB 4: How to Use */}
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
