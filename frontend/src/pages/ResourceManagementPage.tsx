import React, { useState, useEffect } from 'react';
import { 
  UploadCloud, Trash2, Search, Filter, Eye, CheckCircle2, AlertCircle, Clock, Plus, X, Layers
} from 'lucide-react';
import { api, type Resource, type Course } from '../api/client';
import { CreateCourseModal } from '../components/CreateCourseModal';

export const ResourceManagementPage: React.FC = () => {
  const [resources, setResources] = useState<Resource[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | ''>('');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Course creation modal state
  const [showCourseModal, setShowCourseModal] = useState(false);

  // Upload modal state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadCourseId, setUploadCourseId] = useState<number | ''>('');
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDocType, setUploadDocType] = useState('textbook');
  const [uploadUnit, setUploadUnit] = useState<number | ''>('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');

  // Chunk Inspect Modal
  const [inspectResource, setInspectResource] = useState<Resource | null>(null);

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
        setUploadCourseId(courseList.data[0].id);
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

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !uploadCourseId) return;

    setIsUploading(true);
    setUploadError('');

    const formData = new FormData();
    formData.append('course_id', String(uploadCourseId));
    formData.append('title', uploadTitle || uploadFile.name);
    formData.append('document_type', uploadDocType);
    if (uploadUnit) {
      formData.append('unit_number', String(uploadUnit));
    }
    formData.append('file', uploadFile);

    try {
      await api.post('/resources/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setShowUploadModal(false);
      setUploadFile(null);
      setUploadTitle('');
      loadData();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Upload and chunking failed. Please ensure file is valid.');
    } finally {
      setIsUploading(false);
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

  const filteredResources = resources.filter(r => 
    r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.file_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.document_type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Academic Resource Hub & RAG Vector Store</h1>
          <p className="text-xs text-slate-500 mt-1">Upload syllabi, textbooks, and past papers for automated chunking and vector indexing</p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 self-start sm:self-auto">
          <button
            onClick={() => setShowCourseModal(true)}
            className="px-4 py-2.5 bg-white hover:bg-slate-50 text-slate-800 rounded-xl text-xs font-bold border border-slate-300 shadow-xs flex items-center space-x-1.5 transition-all"
          >
            <Plus className="w-4 h-4 text-blue-600" />
            <span>+ Add Course</span>
          </button>

          <button
            onClick={() => setShowUploadModal(true)}
            className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold shadow-md shadow-blue-500/20 flex items-center space-x-2 transition-all"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Academic Document</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white border border-slate-200 rounded-3xl p-4.5 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search resources, topics, files..."
            className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 font-medium"
          />
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400 shrink-0" />
          <select
            value={selectedCourseId}
            onChange={(e) => setSelectedCourseId(e.target.value ? Number(e.target.value) : '')}
            className="px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-semibold text-slate-800 focus:outline-none cursor-pointer"
          >
            <option value="">All Courses ({courses.length})</option>
            {courses.map(c => (
              <option key={c.id} value={c.id}>{c.code} — {c.name}</option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => setShowCourseModal(true)}
            title="Create New Academic Course"
            className="p-2.5 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-2xl text-xs font-bold transition-colors shrink-0 cursor-pointer"
          >
            + New
          </button>
        </div>
      </div>

      {/* Resource Table */}
      <div className="bg-white border border-slate-200 rounded-3xl shadow-xs overflow-hidden">
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
                      {res.unit_number ? `Unit ${res.unit_number}` : 'All Units'}
                    </td>

                    <td className="py-4 px-3">
                      <span className="font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-100">
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
                        <span className="inline-flex items-center text-blue-700 font-bold bg-blue-50 px-2.5 py-1 rounded-full border border-blue-200">
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
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-xl transition-colors border border-blue-200 cursor-pointer"
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

      {/* Upload Document Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl border border-slate-200 space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 bg-blue-50 text-blue-600 rounded-xl border border-blue-100">
                  <UploadCloud className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900">Upload Academic Document</h3>
              </div>
              <button 
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-slate-700 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {uploadError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl font-medium">
                {uploadError}
              </div>
            )}

            <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Target Course</label>
                <select
                  value={uploadCourseId}
                  onChange={(e) => setUploadCourseId(Number(e.target.value))}
                  required
                  className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-medium"
                >
                  {courses.map(c => (
                    <option key={c.id} value={c.id}>{c.code} — {c.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Document Title</label>
                <input
                  type="text"
                  required
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  placeholder="e.g. Unit 3 Standard Reference Chapter"
                  className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Document Type</label>
                  <select
                    value={uploadDocType}
                    onChange={(e) => setUploadDocType(e.target.value)}
                    className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-medium"
                  >
                    <option value="textbook">Textbook Chapter</option>
                    <option value="syllabus">Curriculum Syllabus</option>
                    <option value="previous_paper">Past Question Paper</option>
                    <option value="notes">Lecture Notes</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Target Unit</label>
                  <select
                    value={uploadUnit}
                    onChange={(e) => setUploadUnit(e.target.value ? Number(e.target.value) : '')}
                    className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-medium"
                  >
                    <option value="">General / All Units</option>
                    {courses.find(c => c.id === uploadCourseId)?.units?.map((u) => (
                      <option key={u.unit_number} value={u.unit_number}>
                        Unit {u.unit_number}{u.title ? ` — ${u.title.length > 25 ? u.title.slice(0, 25) + '...' : u.title}` : ''}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Select File (.PDF, .DOCX, .TXT)</label>
                <input
                  type="file"
                  required
                  accept=".pdf,.docx,.txt,.doc,.md"
                  onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full p-2 border border-slate-300 rounded-xl text-xs bg-slate-50"
                />
              </div>

              <button
                type="submit"
                disabled={isUploading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold shadow-md shadow-blue-500/20 disabled:opacity-50 transition-all text-xs"
              >
                {isUploading ? 'Chunking & Vectorizing...' : 'Upload & Process with RAG'}
              </button>
            </form>
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
                    <span className="font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
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
