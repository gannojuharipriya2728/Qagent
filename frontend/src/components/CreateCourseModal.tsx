import React, { useState } from 'react';
import { 
  BookOpen, Plus, Trash2, X, CheckCircle2, AlertCircle, Sparkles, Layers, GraduationCap, FileText
} from 'lucide-react';
import { api, type Course, type CourseCreate, type UnitCreate, type CourseOutcomeCreate } from '../api/client';

interface CreateCourseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCourseCreated: (newCourse: Course) => void;
  existingCourses?: Course[];
}

const BLOOM_LEVELS = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create'];

const DEFAULT_UNITS: UnitCreate[] = [
  { unit_number: 1, title: '', topics: '' },
  { unit_number: 2, title: '', topics: '' },
  { unit_number: 3, title: '', topics: '' },
  { unit_number: 4, title: '', topics: '' },
  { unit_number: 5, title: '', topics: '' }
];

const DEFAULT_COS: CourseOutcomeCreate[] = [
  { code: 'CO1', description: '', target_bloom_level: 'Understand' },
  { code: 'CO2', description: '', target_bloom_level: 'Apply' },
  { code: 'CO3', description: '', target_bloom_level: 'Analyze' }
];

const TEMPLATES = [
  {
    name: 'Information Security (IT701PC)',
    code: 'IT701PC',
    title: 'Information Security',
    department: 'Information Technology',
    semester: 'IV Year I Semester',
    description: 'Security attacks, services, classical encryption, DES, Blowfish, public key cryptography, RSA, Diffie-Hellman, ECC, digital signatures, hash functions, IP security, web security (SSL/TLS/SET), firewalls, and intrusion detection systems.',
    units: [
      { unit_number: 1, title: 'Security Attacks, Services, Mechanisms & Classical Encryption Techniques', topics: 'Security Attacks: Interruption, Interception, Modification and Fabrication. Security Services: Confidentiality, Authentication, Integrity, Non-repudiation, Access Control and Availability. Mechanisms: A model for Internet work security. Classical Encryption Techniques: DES, Strength of DES, Differential and Linear Cryptanalysis, Block Cipher Design Principles and Modes of Operation, Blowfish, Placement of Encryption Function, Traffic Confidentiality, Key Distribution, Random Number Generation.' },
      { unit_number: 2, title: 'Public Key Cryptography, Message Authentication & Hash Functions', topics: 'Public Key Cryptography Principles, RSA algorithm, Key Management, Diffie-Hellman Key Exchange, Elliptic Curve Cryptography. Message Authentication and Hash Functions: Authentication Requirements and Functions, Message Authentication, Hash Functions, MACs, SHA-512, HMAC.' },
      { unit_number: 3, title: 'Digital Signatures, Authentication Protocols & Email Security', topics: 'Digital Signatures: Authentication Protocols, Digital Signature Standard (DSS). Authentication Applications: Kerberos, X.509 Directory Authentication Service. Email Security: Pretty Good Privacy (PGP) and S/MIME.' },
      { unit_number: 4, title: 'IP Security Architecture & Web Security', topics: 'IP Security: Overview, IP Security Architecture, Authentication Header (AH), Encapsulating Security Payload (ESP), Combining Security Associations and Key Management. Web Security: Web Security Requirements, Secure Socket Layer (SSL), Transport Layer Security (TLS), Secure Electronic Transaction (SET).' },
      { unit_number: 5, title: 'Intruders, Viruses, Firewalls & Intrusion Detection Systems', topics: 'Intruders, Viruses and related threats, Firewalls, Firewall Design Principles, Trusted Systems, Intrusion Detection Systems (IDS).' }
    ],
    cos: [
      { code: 'CO1', description: 'Demonstrate the knowledge of cryptography, network security concepts and applications.', target_bloom_level: 'Understand' },
      { code: 'CO2', description: 'Ability to apply security principles in system design.', target_bloom_level: 'Apply' },
      { code: 'CO3', description: 'Ability to identify and investigate vulnerabilities and security threats and mechanisms to counter them.', target_bloom_level: 'Analyze' }
    ]
  },
  {
    name: 'Operating Systems (CS501)',
    code: 'CS501',
    title: 'Operating Systems & Concurrency',
    department: 'Computer Science & Engineering',
    semester: 'Semester V',
    description: 'Process management, CPU scheduling, synchronization primitives, deadlock handling, memory hierarchies, and storage architecture.',
    units: [
      { unit_number: 1, title: 'Processes & Threads', topics: 'Process Concept, Process Control Block (PCB), Context Switching, Thread Models, System Calls (fork, exec, wait).' },
      { unit_number: 2, title: 'CPU Scheduling & Synchronization', topics: 'Scheduling Algorithms (FCFS, SJF, Round Robin, Priority), Critical Section Problem, Mutex, Semaphores, Monitors.' },
      { unit_number: 3, title: 'Deadlocks', topics: 'Deadlock Characterization, Resource Allocation Graph, Banker\'s Algorithm, Deadlock Prevention and Detection.' },
      { unit_number: 4, title: 'Memory Management', topics: 'Paging, Segmentation, Virtual Memory, Demand Paging, Page Replacement Algorithms (LRU, FIFO, Optimal).' },
      { unit_number: 5, title: 'File Systems & I/O', topics: 'File Concept, Directory Structure, Disk Scheduling (SSTF, SCAN, C-SCAN), RAID Levels, I/O Hardware.' }
    ],
    cos: [
      { code: 'CO1', description: 'Explain process lifecycle, IPC mechanisms, and multithreading architectures.', target_bloom_level: 'Understand' },
      { code: 'CO2', description: 'Apply CPU scheduling algorithms and resolve classical synchronization problems.', target_bloom_level: 'Apply' },
      { code: 'CO3', description: 'Analyze resource allocation states using Banker\'s algorithm to prevent deadlocks.', target_bloom_level: 'Analyze' }
    ]
  }
];

export const CreateCourseModal: React.FC<CreateCourseModalProps> = ({
  isOpen,
  onClose,
  onCourseCreated,
  existingCourses = []
}) => {
  const [activeTab, setActiveTab] = useState<'basic' | 'units' | 'cos'>('basic');

  // Form Fields
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [department, setDepartment] = useState('Computer Science & Engineering');
  const [semester, setSemester] = useState('Semester V');
  const [academicYear, setAcademicYear] = useState('2025-2026');
  const [description, setDescription] = useState('');

  // Units
  const [units, setUnits] = useState<UnitCreate[]>(DEFAULT_UNITS);

  // Course Outcomes
  const [courseOutcomes, setCourseOutcomes] = useState<CourseOutcomeCreate[]>(DEFAULT_COS);

  // State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  if (!isOpen) return null;

  const handleApplyTemplate = (tmpl: typeof TEMPLATES[0]) => {
    let candidateCode = tmpl.code;
    let counter = 2;
    while (existingCourses.some(c => c.code.toUpperCase() === candidateCode.toUpperCase())) {
      candidateCode = `${tmpl.code}-${counter}`;
      counter++;
    }
    setCode(candidateCode);
    setName(candidateCode === tmpl.code ? tmpl.title : `${tmpl.title} (Section ${String.fromCharCode(63 + counter)})`);
    setDepartment(tmpl.department);
    setSemester(tmpl.semester);
    setDescription(tmpl.description);
    setUnits(tmpl.units);
    setCourseOutcomes(tmpl.cos);
    setErrorMessage('');
  };

  const handleAddUnit = () => {
    const nextNum = units.length > 0 ? Math.max(...units.map(u => u.unit_number)) + 1 : 1;
    setUnits([
      ...units,
      {
        unit_number: nextNum,
        title: `Unit ${nextNum} Subject Matter`,
        topics: 'Add core topics, definitions, algorithms, and reference material separated by commas.'
      }
    ]);
  };

  const handleRemoveUnit = (index: number) => {
    if (units.length <= 1) {
      setErrorMessage('A course must have at least one curriculum unit.');
      return;
    }
    const updated = units.filter((_, i) => i !== index).map((u, i) => ({
      ...u,
      unit_number: i + 1
    }));
    setUnits(updated);
  };

  const handleUnitChange = (index: number, field: keyof UnitCreate, value: any) => {
    const updated = [...units];
    updated[index] = { ...updated[index], [field]: value };
    setUnits(updated);
  };

  const handleAddCO = () => {
    const nextNum = courseOutcomes.length + 1;
    setCourseOutcomes([
      ...courseOutcomes,
      {
        code: `CO${nextNum}`,
        description: `Course Outcome ${nextNum} description.`,
        target_bloom_level: 'Apply'
      }
    ]);
  };

  const handleRemoveCO = (index: number) => {
    if (courseOutcomes.length <= 1) {
      setErrorMessage('A course must have at least one Course Outcome (CO).');
      return;
    }
    const updated = courseOutcomes.filter((_, i) => i !== index).map((co, i) => ({
      ...co,
      code: `CO${i + 1}`
    }));
    setCourseOutcomes(updated);
  };

  const handleCOChange = (index: number, field: keyof CourseOutcomeCreate, value: string) => {
    const updated = [...courseOutcomes];
    updated[index] = { ...updated[index], [field]: value };
    setCourseOutcomes(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    const cleanCode = code.trim().toUpperCase();
    const cleanName = name.trim();

    if (!cleanCode) {
      setErrorMessage('Course Code is required (e.g. CS501).');
      setActiveTab('basic');
      return;
    }

    if (!cleanName) {
      setErrorMessage('Course Name is required (e.g. Operating Systems).');
      setActiveTab('basic');
      return;
    }

    // Check duplicate locally
    const duplicate = existingCourses.find(c => c.code.toUpperCase() === cleanCode);
    if (duplicate) {
      setErrorMessage(`Subject with code '${cleanCode}' is already registered (${duplicate.name}). You can click 'Overwrite Course' below or wipe all courses to start from scratch.`);
      setActiveTab('basic');
      return;
    }

    // Validate units
    for (const u of units) {
      if (!u.title.trim() || !u.topics.trim()) {
        setErrorMessage(`Unit ${u.unit_number} must have both a Title and Syllabus Topics.`);
        setActiveTab('units');
        return;
      }
    }

    // Validate COs
    for (const co of courseOutcomes) {
      if (!co.code.trim() || !co.description.trim()) {
        setErrorMessage(`Course Outcome ${co.code} must have a valid Description.`);
        setActiveTab('cos');
        return;
      }
    }

    setIsSubmitting(true);

    const payload: CourseCreate = {
      code: cleanCode,
      name: cleanName,
      department: department.trim() || 'Computer Science & Engineering',
      semester: semester.trim() || 'Semester V',
      academic_year: academicYear.trim() || '2025-2026',
      description: description.trim() || `${cleanName} academic curriculum and assessment syllabus.`,
      units: units.map(u => ({
        unit_number: u.unit_number,
        title: u.title.trim(),
        topics: u.topics.trim()
      })),
      course_outcomes: courseOutcomes.map(co => ({
        code: co.code.trim().toUpperCase(),
        description: co.description.trim(),
        target_bloom_level: co.target_bloom_level || 'Apply'
      }))
    };

    try {
      const response = await api.post('/courses', payload);
      const createdCourse: Course = response.data;
      setSuccessMessage(`Course '${cleanCode} — ${cleanName}' created successfully!`);
      
      setTimeout(() => {
        onCourseCreated(createdCourse);
        onClose();
      }, 700);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === 'string' ? detail : 'Failed to create course. Please verify inputs.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOverwriteCourse = async () => {
    const cleanCode = code.trim().toUpperCase();
    const cleanName = name.trim();
    if (!cleanCode || !cleanName) return;

    setIsSubmitting(true);
    setErrorMessage('');

    const payload: CourseCreate = {
      code: cleanCode,
      name: cleanName,
      department: department.trim() || 'Computer Science & Engineering',
      semester: semester.trim() || 'Semester V',
      academic_year: academicYear.trim() || '2025-2026',
      description: description.trim() || `${cleanName} academic curriculum and assessment syllabus.`,
      units: units.map(u => ({
        unit_number: u.unit_number,
        title: u.title.trim(),
        topics: u.topics.trim()
      })),
      course_outcomes: courseOutcomes.map(co => ({
        code: co.code.trim().toUpperCase(),
        description: co.description.trim(),
        target_bloom_level: co.target_bloom_level || 'Apply'
      }))
    };

    try {
      const response = await api.post('/courses?overwrite=true', payload);
      setSuccessMessage(`Course '${cleanCode}' updated & overwritten successfully!`);
      setTimeout(() => {
        onCourseCreated(response.data);
        onClose();
      }, 700);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to overwrite course.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetAllData = async () => {
    if (!window.confirm('Are you sure you want to delete ALL courses, syllabus units, uploaded resources, and generated papers from the database to start completely fresh? (Your user account will be preserved)')) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      await api.post('/courses/reset-all');
      setSuccessMessage('Database cleared! All previous courses and papers wiped clean.');
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to reset database.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto">
      <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-3xl w-full shadow-2xl border border-slate-200 my-8 space-y-6 flex flex-col max-h-[90vh]">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-blue-50 text-blue-600 rounded-2xl border border-blue-100">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-black text-slate-900 tracking-tight">Create Academic Course</h2>
              <p className="text-xs text-slate-500">Define course code, syllabus units, and Course Outcome mappings</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1.5 rounded-xl hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick Template Presets */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-3.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center space-x-2 font-bold text-slate-700">
            <Sparkles className="w-4 h-4 text-blue-600 shrink-0" />
            <span>Curriculum Presets:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {TEMPLATES.map((tmpl) => (
              <button
                key={tmpl.code}
                type="button"
                onClick={() => handleApplyTemplate(tmpl)}
                className="px-3 py-1.5 bg-white hover:bg-blue-50 text-slate-700 hover:text-blue-700 border border-slate-200 hover:border-blue-200 rounded-xl font-bold text-[11px] transition-all shadow-2xs cursor-pointer"
              >
                + {tmpl.name}
              </button>
            ))}
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center space-x-2 border-b border-slate-100 pb-3 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab('basic')}
            className={`px-3.5 py-2 rounded-xl font-bold flex items-center space-x-1.5 transition-all cursor-pointer ${
              activeTab === 'basic'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>1. Course Details</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('units')}
            className={`px-3.5 py-2 rounded-xl font-bold flex items-center space-x-1.5 transition-all cursor-pointer ${
              activeTab === 'units'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>2. Units & Syllabus ({units.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('cos')}
            className={`px-3.5 py-2 rounded-xl font-bold flex items-center space-x-1.5 transition-all cursor-pointer ${
              activeTab === 'cos'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <GraduationCap className="w-3.5 h-3.5" />
            <span>3. Course Outcomes ({courseOutcomes.length})</span>
          </button>
        </div>

        {/* Feedback Messages */}
        {errorMessage && (
          <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-2xl font-medium space-y-2">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span className="font-semibold">{errorMessage}</span>
            </div>
            {(errorMessage.toLowerCase().includes('already registered') || errorMessage.toLowerCase().includes('already exists')) && (
              <div className="flex flex-wrap gap-2 pt-1 border-t border-rose-200/60">
                <button
                  type="button"
                  onClick={handleOverwriteCourse}
                  disabled={isSubmitting}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold text-[11px] shadow-xs cursor-pointer disabled:opacity-50"
                >
                  ⚡ Overwrite & Save Course Details
                </button>
                <button
                  type="button"
                  onClick={handleResetAllData}
                  disabled={isSubmitting}
                  className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl font-bold text-[11px] shadow-xs cursor-pointer disabled:opacity-50"
                >
                  🗑️ Wipe All Database Data
                </button>
              </div>
            )}
          </div>
        )}

        {successMessage && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs rounded-xl font-bold flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Form Body (Scrollable) */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto space-y-4 text-xs pr-1">
          
          {/* TAB 1: Basic Information */}
          {activeTab === 'basic' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">
                    Course Code <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. CS501"
                    value={code}
                    onChange={(e) => {
                      setCode(e.target.value.toUpperCase());
                      setErrorMessage('');
                    }}
                    className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-bold focus:ring-2 focus:ring-blue-500 focus:outline-none uppercase"
                  />
                  <span className="text-[11px] text-slate-400 mt-0.5 block">Unique course identifier</span>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1">
                    Course Title / Name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Operating Systems & Concurrency"
                    value={name}
                    onChange={(e) => {
                      setName(e.target.value);
                      setErrorMessage('');
                    }}
                    className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-semibold focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Department</label>
                  <input
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Semester</label>
                  <input
                    type="text"
                    value={semester}
                    onChange={(e) => setSemester(e.target.value)}
                    className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Academic Year</label>
                  <input
                    type="text"
                    value={academicYear}
                    onChange={(e) => setAcademicYear(e.target.value)}
                    className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Course Description & Overview</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Provide a comprehensive academic overview of the course curriculum and objectives..."
                  className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none leading-relaxed"
                />
              </div>
            </div>
          )}

          {/* TAB 2: Units & Curriculum */}
          {activeTab === 'units' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-slate-800">Curriculum Units & Scope</h3>
                  <p className="text-[11px] text-slate-500">Each unit will be used for RAG grounding and blueprint slot allocation.</p>
                </div>
                <button
                  type="button"
                  onClick={handleAddUnit}
                  className="px-3 py-1.5 bg-blue-50 text-blue-600 hover:bg-blue-100 border border-blue-200 rounded-xl font-bold flex items-center space-x-1 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Unit</span>
                </button>
              </div>

              <div className="space-y-3">
                {units.map((u, idx) => (
                  <div key={idx} className="p-3.5 bg-slate-50 border border-slate-200 rounded-2xl space-y-2 relative">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="font-black text-blue-700 bg-blue-100/80 px-2.5 py-0.5 rounded-md text-xs">
                          Unit {u.unit_number}
                        </span>
                        <input
                          type="text"
                          required
                          value={u.title}
                          onChange={(e) => handleUnitChange(idx, 'title', e.target.value)}
                          placeholder="Unit Title (e.g. Trees and Self-Balancing Trees)"
                          className="font-bold text-slate-900 bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs w-64 sm:w-80"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveUnit(idx)}
                        className="text-rose-500 hover:text-rose-700 p-1 rounded-lg hover:bg-rose-50"
                        title="Delete Unit"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                        Syllabus Topics & Key Concepts (Comma / Sentence separated):
                      </label>
                      <textarea
                        rows={2}
                        required
                        value={u.topics}
                        onChange={(e) => handleUnitChange(idx, 'topics', e.target.value)}
                        placeholder="Key topics, concepts, theorems, algorithms, and models in this unit..."
                        className="w-full p-2 bg-white border border-slate-300 rounded-xl text-slate-900 text-xs focus:ring-1 focus:ring-blue-500 focus:outline-none"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: Course Outcomes (COs) */}
          {activeTab === 'cos' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-slate-800">Course Outcomes (COs) & Bloom's Target</h3>
                  <p className="text-[11px] text-slate-500">Maps question generation slots to pedagogical outcome benchmarks.</p>
                </div>
                <button
                  type="button"
                  onClick={handleAddCO}
                  className="px-3 py-1.5 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 rounded-xl font-bold flex items-center space-x-1 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Outcome</span>
                </button>
              </div>

              <div className="space-y-2.5">
                {courseOutcomes.map((co, idx) => (
                  <div key={idx} className="p-3 bg-emerald-50/40 border border-emerald-100 rounded-2xl space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center space-x-2">
                        <input
                          type="text"
                          required
                          value={co.code}
                          onChange={(e) => handleCOChange(idx, 'code', e.target.value.toUpperCase())}
                          className="w-16 font-black text-emerald-950 bg-white border border-emerald-200 rounded-lg px-2 py-1 text-xs text-center uppercase"
                        />
                        <span className="text-[11px] font-semibold text-slate-500">Target Bloom's:</span>
                        <select
                          value={co.target_bloom_level || 'Apply'}
                          onChange={(e) => handleCOChange(idx, 'target_bloom_level', e.target.value)}
                          className="bg-white border border-emerald-200 rounded-lg px-2 py-1 text-xs font-semibold text-emerald-900"
                        >
                          {BLOOM_LEVELS.map(lvl => (
                            <option key={lvl} value={lvl}>{lvl}</option>
                          ))}
                        </select>
                      </div>

                      <button
                        type="button"
                        onClick={() => handleRemoveCO(idx)}
                        className="text-rose-500 hover:text-rose-700 p-1 rounded-lg hover:bg-rose-50"
                        title="Delete Course Outcome"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    <textarea
                      rows={2}
                      required
                      value={co.description}
                      onChange={(e) => handleCOChange(idx, 'description', e.target.value)}
                      placeholder="Outcome statement e.g. Analyze asymptotic time and space complexity..."
                      className="w-full p-2 bg-white border border-slate-300 rounded-xl text-slate-900 text-xs focus:ring-1 focus:ring-emerald-500 focus:outline-none"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Footer Actions */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {activeTab !== 'basic' && (
                <button
                  type="button"
                  onClick={() => setActiveTab(activeTab === 'cos' ? 'units' : 'basic')}
                  className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold transition-all"
                >
                  Previous Tab
                </button>
              )}
              {activeTab !== 'cos' && (
                <button
                  type="button"
                  onClick={() => setActiveTab(activeTab === 'basic' ? 'units' : 'cos')}
                  className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-bold transition-all"
                >
                  Next Tab
                </button>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold transition-all"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold shadow-md shadow-blue-500/20 disabled:opacity-50 flex items-center space-x-1.5 transition-all"
              >
                {isSubmitting ? (
                  <span>Creating Course...</span>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Save Academic Course</span>
                  </>
                )}
              </button>
            </div>
          </div>

        </form>

      </div>
    </div>
  );
};
