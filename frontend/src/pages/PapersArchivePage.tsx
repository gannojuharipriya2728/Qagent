import React, { useState, useEffect } from 'react';
import { 
  FileText, Search, Download, Trash2, ArrowRight, Calendar
} from 'lucide-react';
import { api, type QuestionPaper } from '../api/client';

interface PapersArchivePageProps {
  onSelectPaper: (paperId: number) => void;
  onNavigateGenerate: () => void;
}

export const PapersArchivePage: React.FC<PapersArchivePageProps> = ({
  onSelectPaper,
  onNavigateGenerate
}) => {
  const [papers, setPapers] = useState<QuestionPaper[]>([]);
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadPapers();
  }, []);

  const loadPapers = async () => {
    try {
      const res = await api.get('/papers');
      setPapers(res.data);
    } catch (e) {
      console.error('Failed to load papers:', e);
    }
  };

  const handleDeletePaper = async (paperId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this question paper?')) return;
    try {
      await api.delete(`/papers/${paperId}`);
      loadPapers();
    } catch (e) {
      alert('Failed to delete paper');
    }
  };

  const handleDownloadPDF = (paperId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
    window.open(`${apiBase}/papers/${paperId}/pdf`, '_blank');
  };

  const filtered = papers.filter(p => 
    p.title.toLowerCase().includes(search.toLowerCase()) ||
    (p.course_code && p.course_code.toLowerCase().includes(search.toLowerCase())) ||
    p.examination_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Question Papers Archive</h1>
          <p className="text-xs text-slate-500 mt-1">Access, export, and inspect previously generated university examination papers</p>
        </div>

        <button
          onClick={onNavigateGenerate}
          className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold shadow-md shadow-blue-500/20 flex items-center space-x-2 transition-all self-start sm:self-auto"
        >
          <span>Generate New Paper</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="bg-white border border-slate-200 rounded-3xl p-4.5 shadow-xs flex items-center justify-between">
        <div className="relative w-full sm:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search papers by course, title, or exam..."
            className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 font-medium"
          />
        </div>
        <span className="text-xs text-slate-500 font-bold hidden sm:inline bg-slate-100 px-3 py-1.5 rounded-xl">
          Total: {papers.length} Papers
        </span>
      </div>

      {/* Paper Cards List */}
      {filtered.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-3xl p-14 text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-2">
            <FileText className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">No question papers found</h3>
          <p className="text-xs text-slate-500">Run the question paper generator to build your first examination paper.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((p) => (
            <div
              key={p.id}
              onClick={() => onSelectPaper(p.id)}
              className="bg-white border border-slate-200 rounded-3xl p-5.5 shadow-xs hover-card-lift cursor-pointer transition-all flex flex-col justify-between space-y-4 group"
            >
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-black text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-md border border-blue-100">
                    {p.course_code || 'CS301'}
                  </span>
                  <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-100">
                    {p.syllabus_coverage_score}% Coverage
                  </span>
                </div>

                <h3 className="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-2 leading-snug">
                  {p.title}
                </h3>
                <p className="text-xs text-slate-500 line-clamp-1">{p.examination_name}</p>

                <div className="grid grid-cols-2 gap-2 pt-2 text-[11px] text-slate-600 border-t border-slate-100">
                  <div>Max Marks: <strong className="text-slate-900 font-bold">{p.total_marks}M</strong></div>
                  <div>Questions: <strong className="text-slate-900 font-bold">{p.questions?.length || 0}</strong></div>
                  <div>Duration: <strong className="text-slate-900 font-bold">{p.duration_minutes}m</strong></div>
                  <div className="flex items-center space-x-1">
                    <Calendar className="w-3 h-3 text-slate-400" />
                    <span>{p.created_at ? new Date(p.created_at).toLocaleDateString() : 'Recent'}</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <button
                  onClick={(e) => handleDownloadPDF(p.id, e)}
                  title="Download PDF"
                  className="px-3 py-1.5 bg-slate-50 hover:bg-blue-50 text-slate-700 hover:text-blue-700 rounded-xl transition-colors border border-slate-200 flex items-center space-x-1.5 text-xs font-bold cursor-pointer"
                >
                  <Download className="w-3.5 h-3.5 text-blue-600" />
                  <span>PDF</span>
                </button>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={(e) => handleDeletePaper(p.id, e)}
                    title="Delete Paper"
                    className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors cursor-pointer"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>

                  <span className="p-1.5 text-blue-600 group-hover:translate-x-1 transition-transform">
                    <ArrowRight className="w-4 h-4" />
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

    </div>
  );
};
