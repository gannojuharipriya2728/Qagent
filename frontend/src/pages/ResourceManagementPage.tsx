import React, { useState, useEffect } from 'react';
import { 
  UploadCloud, Trash2, Search, Filter, Eye, CheckCircle2, AlertCircle, Clock, Plus, X, Layers,
  BookOpen, Sparkles, ArrowRight
} from 'lucide-react';
import { api, type Resource, type Course } from '../api/client';
import { CreateCourseModal } from '../components/CreateCourseModal';

interface ResourceManagementPageProps {
  onNavigateAnalysis?: (courseId: number) => void;
}

export const ResourceManagementPage: React.FC<ResourceManagementPageProps> = ({
  onNavigateAnalysis
}) => {
  const [resources, setResources] = useState<Resource[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | ''>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeUnitTab, setActiveUnitTab] = useState<string>('all'); // 'all', 'general', '1', '2', '3', '4', '5'
  
  // Course creation modal state
  const [showCourseModal, setShowCourseModal] = useState(false);

  // Upload modal state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadCourseId, setUploadCourseId] = useState<number | ''>('');
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDocType, setUploadDocType] = useState('syllabus');
  const [uploadUnit, setUploadUnit] = useState<number | ''>('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStepIndex, setUploadStepIndex] = useState(0);
  const [uploadError, setUploadError] = useState('');

  // Chunk Inspect Modal
  const [inspectResource, setInspectResource] = useState<Resource | null>(null);

  const UPLOAD_STEPS = [
    'Uploading document...',
    'Processing PDF layout & pages...',
    'Extracting academic content...',
    'Creating semantic chunks...',
    'Generating vector embeddings...',
    'Analyzing syllabus units & COs...',
    'Completed & Indexed!'
  ];

  useEffect(() => {
    loadData();
  }, [selectedCourseId]);

  const loadData = async () => {
    try {
      const [resList, courseList] = await Promise.all([
        api.get('/resources', { params: selectedCourseId ? { course_id: selectedCourseId } : {} }),
        api.get('/courses')
      ]);
      setResources(resList.data);
      setCourses(courseList.data);
      if (courseList.data.length > 0 && uploadCourseId === '') {
        setUploadCourseId(selectedCourseId || courseList.data[0].id);
      }
    } catch (e) {
      console.error('Failed to load resources:', e);
    }
  };

  const handleCourseCreated = async (newCourse: Course) => {
    try {
      const courseList = await api.get('/courses');
      setCourses(courseList.data);
      setSelectedCourseId(newCourse.id);
      setUploadCourseId(newCourse.id);
    } catch (e) {
      console.error('Failed to refresh courses:', e);
    }
  };

  const handleOpenUploadForUnit = (unitNum?: number) => {
    if (unitNum !== undefined) {
      setUploadUnit(unitNum);
    } else {
      setUploadUnit('');
    }
    if (selectedCourseId) {
      setUploadCourseId(selectedCourseId);
    } else if (courses.length > 0) {
      setUploadCourseId(courses[0].id);
    }
    setShowUploadModal(true);
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !uploadCourseId) return;

    setIsUploading(true);
    setUploadStepIndex(0);
    setUploadError('');

    const currentCourse = courses.find(c => c.id === uploadCourseId);
    const targetTitle = uploadTitle.trim() || `${currentCourse?.name || 'Subject'} - ${uploadDocType.toUpperCase()}`;

    const formData = new FormData();
    formData.append('course_id', String(uploadCourseId));
    formData.append('title', targetTitle);
    formData.append('document_type', uploadDocType);
    if (uploadUnit !== '') {
      formData.append('unit_number', String(uploadUnit));
    }
    formData.append('file', uploadFile);

    // Progress interval animation
    const progressTimer = setInterval(() => {
      setUploadStepIndex(prev => (prev < UPLOAD_STEPS.length - 2 ? prev + 1 : prev));
    }, 600);

    try {
      await api.post('/resources/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      clearInterval(progressTimer);
      setUploadStepIndex(UPLOAD_STEPS.length - 1);
      
      setTimeout(() => {
        setShowUploadModal(false);
        setUploadFile(null);
        setUploadTitle('');
        setIsUploading(false);
        loadData();
      }, 700);
    } catch (err: any) {
      clearInterval(progressTimer);
      setIsUploading(false);
      setUploadError(err.response?.data?.detail || 'Upload and chunking failed. Please ensure file is valid.');
    }
  };

  const handleDeleteResource = async (id: number) => {
    if (!confirm('Are you sure you want to delete this resource and remove all its indexed vector chunks?')) return;
    try {
      await api.delete(`/resources/${id}`);
      loadData();
    } catch (e) {
      alert('Failed to delete resource');
    }
  };

  const handleInspectChunks = async (res: Resource) => {
    try {
      const fullRes = await api.get(`/resources/${res.id}`);
      setInspectResource(fullRes.data);
    } catch (e) {
      alert('Could not load chunk details');
    }
  };

  const filteredResources = resources.filter(r => {
    const matchesSearch = r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.file_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.document_type.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (!matchesSearch) return false;

    if (activeUnitTab === 'all') return true;
    if (activeUnitTab === 'general') return !r.unit_number;
    return String(r.unit_number) === activeUnitTab;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Course Resources & Knowledge Grounding</h1>
          <p className="text-xs text-slate-500 mt-1">
            Upload syllabi, textbooks, lecture notes, and past papers (Unit-wise or General) for RAG vector indexing
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 self-start sm:self-auto">
          {selectedCourseId && onNavigateAnalysis && (
            <button
              onClick={() => onNavigateAnalysis(Number(selectedCourseId))}
              className="px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-500/20 flex items-center space-x-1.5 transition-all"
            >
              <Sparkles className="w-4 h-4 text-indigo-200" />
              <span>Academic Analysis</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}

          <button
            onClick={() => setShowCourseModal(true)}
            className="px-4 py-2.5 bg-white hover:bg-slate-50 text-slate-800 rounded-xl text-xs font-bold border border-slate-300 shadow-sm flex items-center space-x-1.5 transition-all"
          >
            <Plus className="w-4 h-4 text-indigo-600" />
            <span>+ Create Course</span>
          </button>

          <button
            onClick={() => handleOpenUploadForUnit()}
            className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-500/20 flex items-center space-x-2 transition-all"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Filter and Course Selection Bar */}
      <div className="bg-white border border-slate-200 rounded-3xl p-4.5 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search resources, topics, files..."
            className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 font-medium"
          />
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400 shrink-0" />
          <select
            value={selectedCourseId}
            onChange={(e) => {
              const val = e.target.value ? Number(e.target.value) : '';
              setSelectedCourseId(val);
              if (val) setUploadCourseId(val);
            }}
            className="px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-semibold text-slate-800 focus:outline-none cursor-pointer"
          >
            <option value="">All Courses ({courses.length})</option>
            {courses.map(c => (
              <option key={c.id} value={c.id}>{c.code} — {c.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Upload Modes & Unit Tabs */}
      <div className="bg-white border border-slate-200/90 rounded-3xl p-4 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-3">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
            Upload Modes & Unit Classification
          </span>
          <span className="text-[11px] text-slate-400">
            Upload unit-specific chapters or general course-wide materials
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setActiveUnitTab('all')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              activeUnitTab === 'all'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
            }`}
          >
            All Resources ({resources.length})
          </button>

          <button
            onClick={() => setActiveUnitTab('general')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              activeUnitTab === 'general'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
            }`}
          >
            General / Course Level
          </button>

          {[1, 2, 3, 4, 5].map((u) => {
            const count = resources.filter(r => r.unit_number === u).length;
            return (
              <button
                key={u}
                onClick={() => setActiveUnitTab(String(u))}
                className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
                  activeUnitTab === String(u)
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                }`}
              >
                <span>Unit {u}</span>
                {count > 0 && (
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                    activeUnitTab === String(u) ? 'bg-indigo-800 text-indigo-100' : 'bg-slate-300 text-slate-800'
                  }`}>
                    {count}
                  </span>
                )}
              </button>
            );
          })}

          <div className="ml-auto">
            <button
              onClick={() => handleOpenUploadForUnit(activeUnitTab !== 'all' && activeUnitTab !== 'general' ? Number(activeUnitTab) : undefined)}
              className="px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Upload to {activeUnitTab === 'all' ? 'Course' : activeUnitTab === 'general' ? 'General' : `Unit ${activeUnitTab}`}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Resource Table */}
      <div className="bg-white border border-slate-200 rounded-3xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-700 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3.5 px-4.5">Document Title & File</th>
                <th className="py-3.5 px-3">Type</th>
                <th className="py-3.5 px-3">Unit Target</th>
                <th className="py-3.5 px-3">Chunks</th>
                <th className="py-3.5 px-3">RAG Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredResources.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400 space-y-2">
                    <div className="w-10 h-10 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-2">
                      <Search className="w-5 h-5" />
                    </div>
                    <div className="font-bold text-slate-700">No academic resources found</div>
                    <p className="text-xs text-slate-400">Upload a syllabus or textbook chapter to start vector retrieval.</p>
                  </td>
                </tr>
              ) : (
                filteredResources.map((res) => (
                  <tr key={res.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-4 px-4.5">
                      <div className="font-bold text-slate-900">{res.title}</div>
                      <div className="text-[11px] text-slate-500 font-mono mt-0.5">{res.file_name} • {(res.file_size_bytes / 1024).toFixed(1)} KB</div>
                    </td>

                    <td className="py-4 px-3">
                      <span className="capitalize font-semibold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg">
                        {res.document_type.replace('_', ' ')}
                      </span>
                    </td>

                    <td className="py-4 px-3 font-semibold text-slate-800">
                      {res.unit_number ? `Unit ${res.unit_number}` : 'General / All Units'}
                    </td>

                    <td className="py-4 px-3">
                      <span className="font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-full border border-indigo-100">
                        {res.chunk_count} Chunks
                      </span>
                    </td>

                    <td className="py-4 px-3">
                      {res.status === 'Processed' && (
                        <span className="inline-flex items-center text-emerald-700 font-bold bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                          <CheckCircle2 className="w-3 h-3 mr-1" /> Vectorized
                        </span>
                      )}
                      {res.status === 'Processing' && (
                        <span className="inline-flex items-center text-indigo-700 font-bold bg-indigo-50 px-2.5 py-1 rounded-full border border-indigo-200">
                          <Clock className="w-3 h-3 mr-1" /> Processing...
                        </span>
                      )}
                      {res.status === 'Failed' && (
                        <span className="inline-flex items-center text-rose-700 font-bold bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200" title={res.error_message}>
                          <AlertCircle className="w-3 h-3 mr-1" /> Failed
                        </span>
                      )}
                    </td>

                    <td className="py-4 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleInspectChunks(res)}
                          title="Inspect Extracted Chunks"
                          className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-xl transition-colors border border-indigo-200 cursor-pointer"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>

                        <button
                          onClick={() => handleDeleteResource(res.id)}
                          title="Delete Resource"
                          className="p-2 text-rose-600 hover:bg-rose-50 rounded-xl transition-colors border border-rose-200 cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upload Document / Syllabus Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl border border-slate-200 space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl border border-indigo-100">
                  <UploadCloud className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Upload Syllabus & Resources</h3>
                  <p className="text-[11px] text-slate-500">Autonomous RAG indexing and curriculum analysis</p>
                </div>
              </div>
              {!isUploading && (
                <button 
                  onClick={() => setShowUploadModal(false)}
                  className="text-slate-400 hover:text-slate-700 p-1"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>

            {uploadError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl font-medium flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}

            {isUploading ? (
              <div className="p-5 bg-slate-50 border border-slate-200/90 rounded-2xl space-y-4 text-xs">
                <div className="flex items-center space-x-2 text-indigo-700 font-extrabold">
                  <Sparkles className="w-4 h-4 animate-spin text-indigo-600" />
                  <span>Syllabus RAG Processing Pipeline</span>
                </div>

                <div className="space-y-2">
                  {UPLOAD_STEPS.map((stepName, sIdx) => {
                    const isDone = uploadStepIndex > sIdx;
                    const isCurrent = uploadStepIndex === sIdx;
                    return (
                      <div 
                        key={sIdx}
                        className={`flex items-center space-x-2.5 p-2 rounded-xl text-xs font-semibold transition-all ${
                          isDone 
                            ? 'bg-emerald-50 text-emerald-800' 
                            : isCurrent 
                            ? 'bg-indigo-50 text-indigo-900 ring-1 ring-indigo-200' 
                            : 'text-slate-400'
                        }`}
                      >
                        <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                          isDone 
                            ? 'bg-emerald-600 text-white' 
                            : isCurrent 
                            ? 'bg-indigo-600 text-white animate-pulse' 
                            : 'bg-slate-200 text-slate-600'
                        }`}>
                          {isDone ? '✓' : sIdx + 1}
                        </div>
                        <span className="truncate">{stepName}</span>
                      </div>
                    );
                  })}
                </div>

                <p className="text-[11px] text-slate-500 text-center italic">
                  Autonomous agents are parsing sections, extracting topics, and creating vector embeddings...
                </p>
              </div>
            ) : (
              <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
                {/* Subject Selector */}
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Subject</label>
                  <select
                    value={uploadCourseId}
                    onChange={(e) => setUploadCourseId(Number(e.target.value))}
                    required
                    className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-bold"
                  >
                    {courses.map(c => (
                      <option key={c.id} value={c.id}>{c.name} ({c.code})</option>
                    ))}
                  </select>
                </div>

                {/* Subject ID Display */}
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Subject ID</label>
                  <div className="p-2.5 bg-slate-100 border border-slate-200 rounded-xl text-slate-800 font-mono font-bold">
                    {courses.find(c => c.id === uploadCourseId)?.code || 'AIML601'}
                  </div>
                </div>

                {/* What are you uploading? */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-bold text-slate-700 mb-1">What are you uploading?</label>
                    <select
                      value={uploadDocType}
                      onChange={(e) => setUploadDocType(e.target.value)}
                      className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-semibold"
                    >
                      <option value="syllabus">Syllabus PDF</option>
                      <option value="textbook">Textbook Chapter</option>
                      <option value="previous_paper">Previous Question Paper</option>
                      <option value="notes">Lecture Notes</option>
                      <option value="handout">Course Handout</option>
                    </select>
                  </div>
                  <div>
                    <label className="block font-bold text-slate-700 mb-1">Target Unit Scope</label>
                    <select
                      value={uploadUnit}
                      onChange={(e) => setUploadUnit(e.target.value ? Number(e.target.value) : '')}
                      className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-semibold"
                    >
                      <option value="">Full Syllabus / All Units</option>
                      <option value="1">Unit 1</option>
                      <option value="2">Unit 2</option>
                      <option value="3">Unit 3</option>
                      <option value="4">Unit 4</option>
                      <option value="5">Unit 5</option>
                    </select>
                  </div>
                </div>

                {/* Title */}
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Document Title</label>
                  <input
                    type="text"
                    value={uploadTitle}
                    onChange={(e) => setUploadTitle(e.target.value)}
                    placeholder="e.g. Official University Syllabus 2026"
                    className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-medium"
                  />
                </div>

                {/* Upload File */}
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Upload PDF / Document</label>
                  <input
                    type="file"
                    required
                    accept=".pdf,.docx,.doc,.txt,.ppt,.pptx,.md"
                    onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
                    className="w-full p-2 border border-slate-300 rounded-xl text-xs bg-slate-50 cursor-pointer"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isUploading}
                  className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold shadow-md shadow-indigo-500/20 disabled:opacity-50 transition-all text-xs cursor-pointer flex items-center justify-center space-x-2"
                >
                  <UploadCloud className="w-4 h-4" />
                  <span>Upload Syllabus</span>
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Chunk Inspect Modal */}
      {inspectResource && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-3xl p-6 max-w-2xl w-full shadow-2xl border border-slate-200 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-slate-200">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 bg-purple-50 text-purple-600 rounded-xl border border-purple-100">
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Extracted Vector Chunks</h3>
                  <p className="text-xs text-slate-500">{inspectResource.title} ({inspectResource.chunks?.length || 0} Chunks)</p>
                </div>
              </div>
              <button 
                onClick={() => setInspectResource(null)}
                className="text-slate-400 hover:text-slate-700 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4 space-y-3">
              {inspectResource.chunks?.map((c) => (
                <div key={c.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
                      Chunk #{c.chunk_index + 1}
                    </span>
                    <div className="text-slate-500 space-x-2">
                      <span>Page: <strong>{c.page_number || 1}</strong></span>
                      <span>•</span>
                      <span>Unit: <strong>{c.unit_number || 'General'}</strong></span>
                      <span>•</span>
                      <span>Tokens: <strong>{c.token_count}</strong></span>
                    </div>
                  </div>
                  {c.topic && (
                    <div className="text-xs font-semibold text-slate-800">
                      Topic: {c.topic}
                    </div>
                  )}
                  <p className="text-xs text-slate-600 whitespace-pre-line leading-relaxed">
                    {c.content}
                  </p>
                </div>
              ))}
            </div>

            <div className="pt-3 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setInspectResource(null)}
                className="px-4 py-2 bg-slate-900 text-white rounded-xl text-xs font-semibold hover:bg-slate-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Course Modal */}
      <CreateCourseModal
        isOpen={showCourseModal}
        onClose={() => setShowCourseModal(false)}
        onCourseCreated={handleCourseCreated}
        existingCourses={courses}
      />

    </div>
  );
};
