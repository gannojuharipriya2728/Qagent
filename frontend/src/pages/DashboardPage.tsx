import React, { useEffect, useState } from 'react';
import { 
  Sparkles, UploadCloud, BookOpen, FileText, Layers, ArrowRight, Plus, GraduationCap
} from 'lucide-react';
import { api, type Course, type QuestionPaper } from '../api/client';
import { CreateCourseModal } from '../components/CreateCourseModal';

interface DashboardPageProps {
  onNavigate: (page: string, params?: any) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [papers, setPapers] = useState<QuestionPaper[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showCourseModal, setShowCourseModal] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const [coursesRes, papersRes, statsRes] = await Promise.all([
        api.get('/courses'),
        api.get('/papers'),
        api.get('/admin/stats').catch(() => ({ data: {} }))
      ]);
      setCourses(coursesRes.data);
      setPapers(papersRes.data);
      setStats(statsRes.data);
    } catch (e) {
      console.error('Failed to load dashboard:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCourseCreated = async () => {
    await loadDashboardData();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Welcome Banner */}
      <div className="relative overflow-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white rounded-3xl p-6 sm:p-8 shadow-xl border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="space-y-2 text-center md:text-left relative z-10">
          <div className="inline-flex items-center space-x-1.5 bg-blue-500/15 text-blue-300 px-3 py-1 rounded-full text-xs font-semibold border border-blue-500/30">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>Multi-Agent Academic Engine Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white font-sans">
            Academic Assessment Control Center
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 max-w-xl leading-relaxed">
            Autonomous RAG generation of university examination papers grounded in authenticated syllabi, Bloom's Taxonomy, and Course Outcomes.
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-2.5 relative z-10">
          <button
            onClick={() => setShowCourseModal(true)}
            className="px-4 py-2.5 bg-slate-900/90 hover:bg-slate-800 text-white rounded-xl text-xs font-bold border border-slate-700/80 flex items-center space-x-1.5 transition-all shadow-xs cursor-pointer hover:border-slate-600"
          >
            <Plus className="w-4 h-4 text-blue-400" />
            <span>Add Course</span>
          </button>

          <button
            onClick={() => onNavigate('resources')}
            className="px-4 py-2.5 bg-slate-900/90 hover:bg-slate-800 text-white rounded-xl text-xs font-bold border border-slate-700/80 flex items-center space-x-2 transition-all shadow-xs cursor-pointer hover:border-slate-600"
          >
            <UploadCloud className="w-4 h-4 text-blue-400" />
            <span>Upload Syllabus</span>
          </button>

          <button
            onClick={() => onNavigate('generate')}
            className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold flex items-center space-x-2 transition-all shadow-md shadow-blue-500/25 cursor-pointer active:scale-98"
          >
            <Sparkles className="w-4 h-4 text-blue-200" />
            <span>Generate Paper</span>
          </button>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs flex items-center space-x-4 hover-card-lift">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl border border-blue-100/80">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Curriculum Courses</span>
            <div className="text-xl font-extrabold text-slate-900 mt-0.5">
              {isLoading ? '...' : `${courses.length} Active`}
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs flex items-center space-x-4 hover-card-lift">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl border border-indigo-100/80">
            <UploadCloud className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">RAG Documents</span>
            <div className="text-xl font-extrabold text-slate-900 mt-0.5">
              {isLoading ? '...' : `${stats?.total_resources || courses.reduce((acc, c) => acc + (c.units?.length ? 2 : 1), 0)} Uploaded`}
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs flex items-center space-x-4 hover-card-lift">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-xl border border-purple-100/80">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Vector Chunks</span>
            <div className="text-xl font-extrabold text-slate-900 mt-0.5">
              {isLoading ? '...' : `${stats?.vector_store_documents || 15} Chunks`}
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs flex items-center space-x-4 hover-card-lift">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl border border-emerald-100/80">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Generated Papers</span>
            <div className="text-xl font-extrabold text-slate-900 mt-0.5">
              {isLoading ? '...' : `${papers.length} Papers`}
            </div>
          </div>
        </div>

      </div>

      {/* Main Split: Courses & Recent Papers */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Active Courses List */}
        <div className="lg:col-span-1 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <GraduationCap className="w-4 h-4 text-blue-600" />
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Academic Curriculum</h2>
            </div>
            <button
              onClick={() => setShowCourseModal(true)}
              className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center space-x-1 px-2.5 py-1 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors border border-blue-200/60 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add</span>
            </button>
          </div>

          {isLoading ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-28 rounded-2xl skeleton-shimmer border border-slate-200/60" />
              ))}
            </div>
          ) : courses.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-6 text-center space-y-2">
              <p className="text-xs text-slate-500 font-medium">No academic courses found.</p>
              <button
                onClick={() => setShowCourseModal(true)}
                className="text-xs font-bold text-blue-600 hover:underline"
              >
                + Create First Course
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {courses.map((c) => (
                <div 
                  key={c.id} 
                  className="bg-white border border-slate-200/80 rounded-2xl p-4.5 shadow-xs hover-card-lift border-l-4 border-l-blue-600"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-extrabold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-100">
                      {c.code}
                    </span>
                    <span className="text-[11px] font-semibold text-slate-400">{c.semester}</span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 truncate">{c.name}</h3>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">{c.description}</p>
                  
                  <div className="flex items-center justify-between mt-3 pt-2.5 border-t border-slate-100 text-[11px] text-slate-500 font-medium">
                    <div className="flex items-center space-x-2">
                      <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-700 font-semibold">{c.units?.length || 5} Units</span>
                      <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-700 font-semibold">{c.course_outcomes?.length || 3} COs</span>
                    </div>
                    <button
                      onClick={() => onNavigate('generate', { prefillCourseId: c.id })}
                      className="font-bold text-blue-600 hover:text-blue-700 flex items-center space-x-1 cursor-pointer"
                    >
                      <span>Generate</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Generated Question Papers */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <FileText className="w-4 h-4 text-indigo-600" />
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Recent Generated Papers</h2>
            </div>
            <button
              onClick={() => onNavigate('papers')}
              className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center space-x-1 cursor-pointer"
            >
              <span>View All</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-20 rounded-2xl skeleton-shimmer border border-slate-200/60" />
              ))}
            </div>
          ) : papers.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-3xl p-10 text-center space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto border border-blue-100">
                <Sparkles className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-slate-900">No question papers generated yet</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  Select a course from the curriculum and run the 5-Agent RAG workflow to synthesize your first university exam paper.
                </p>
              </div>
              <button
                onClick={() => onNavigate('generate')}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold shadow-sm shadow-blue-500/20 cursor-pointer"
              >
                Create First Exam Paper
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {papers.slice(0, 6).map((p) => (
                <div 
                  key={p.id}
                  onClick={() => onNavigate('paper_view', { paperId: p.id })}
                  className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-xs hover-card-lift cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-extrabold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
                        {p.course_code || 'CS301'}
                      </span>
                      <h4 className="text-xs font-bold text-slate-900 truncate">{p.title}</h4>
                    </div>
                    <div className="flex items-center space-x-2.5 text-xs text-slate-500">
                      <span className="truncate">{p.examination_name}</span>
                      <span>•</span>
                      <span className="font-semibold text-slate-700">{p.total_marks} Marks</span>
                      <span>•</span>
                      <span>{p.questions?.length || 0} Questions</span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4 self-end sm:self-center shrink-0">
                    <div className="text-right">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Syllabus Coverage</span>
                      <span className="text-xs font-extrabold text-emerald-600">{p.syllabus_coverage_score}%</span>
                    </div>
                    <div className="p-2 rounded-xl bg-slate-50 hover:bg-blue-50 text-slate-400 hover:text-blue-600 transition-colors border border-slate-200/60">
                      <ArrowRight className="w-4 h-4" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

        </div>

      </div>

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

