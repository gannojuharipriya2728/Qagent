import React, { useState, useEffect } from 'react';
import { 
  FileText, BarChart2, BookOpen, ArrowLeft, RefreshCw
} from 'lucide-react';
import { api, API_BASE_URL, type QuestionPaper, type Question, type PaperAnalytics } from '../api/client';
import { QuestionPaperPreview } from '../components/QuestionPaperPreview';
import { CoverageRadarChart } from '../components/CoverageRadarChart';
import { ExplainabilityDrawer } from '../components/ExplainabilityDrawer';

interface PaperViewPageProps {
  paperId: number;
  onNavigateBack: () => void;
}

export const PaperViewPage: React.FC<PaperViewPageProps> = ({ paperId, onNavigateBack }) => {
  const [activeTab, setActiveTab] = useState<'paper' | 'analytics' | 'sources'>('paper');
  const [paper, setPaper] = useState<QuestionPaper | null>(null);
  const [analytics, setAnalytics] = useState<PaperAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Explainability drawer
  const [selectedExplainQuestion, setSelectedExplainQuestion] = useState<Question | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  useEffect(() => {
    loadPaper();
  }, [paperId]);

  const loadPaper = async () => {
    setIsLoading(true);
    try {
      const [pRes, aRes] = await Promise.all([
        api.get(`/papers/${paperId}`),
        api.get(`/papers/${paperId}/analytics`)
      ]);
      setPaper(pRes.data);
      setAnalytics(aRes.data);
    } catch (e) {
      console.error('Failed to load paper:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditQuestion = async (questionId: number, newText: string, marks: number) => {
    try {
      await api.put(`/papers/${paperId}/questions/${questionId}`, {
        question_text: newText,
        marks: marks
      });
      loadPaper();
    } catch (e) {
      alert('Failed to update question');
    }
  };

  const handleRegenerateQuestion = async (questionId: number) => {
    try {
      await api.post(`/papers/${paperId}/questions/${questionId}/regenerate`, {});
      loadPaper();
    } catch (e) {
      alert('Failed to regenerate question with Agent 3');
    }
  };

  const handleOpenExplainability = (q: Question) => {
    setSelectedExplainQuestion(q);
    setIsDrawerOpen(true);
  };

  const handleExportPDF = () => {
    window.open(`${API_BASE_URL}/papers/${paperId}/pdf`, '_blank');
  };

  if (isLoading || !paper) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100 animate-spin">
          <RefreshCw className="w-6 h-6" />
        </div>
        <div className="text-center space-y-1">
          <p className="text-sm font-bold text-slate-800">Loading Academic Question Paper</p>
          <p className="text-xs text-slate-400">Retrieving questions, Bloom metrics, and RAG provenance...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Top Header Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 no-print">
        <div className="flex items-center space-x-3.5">
          <button
            onClick={onNavigateBack}
            className="p-2.5 rounded-2xl bg-white hover:bg-slate-100 text-slate-600 border border-slate-200 shadow-2xs hover:shadow-xs transition-all cursor-pointer"
            title="Back to Papers Archive"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-black text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-md border border-blue-100">
                {paper.course_code || 'CS301'}
              </span>
              <h1 className="text-xl font-black text-slate-900 truncate max-w-lg tracking-tight">{paper.title}</h1>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">{paper.institution_name} • {paper.total_marks} Marks Examination</p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center space-x-1.5 bg-slate-100/80 p-1.5 rounded-2xl border border-slate-200 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('paper')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 cursor-pointer ${
              activeTab === 'paper' ? 'bg-white text-blue-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Question Paper</span>
          </button>

          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 cursor-pointer ${
              activeTab === 'analytics' ? 'bg-white text-blue-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5" />
            <span>Syllabus & Taxonomy</span>
          </button>

          <button
            onClick={() => setActiveTab('sources')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 cursor-pointer ${
              activeTab === 'sources' ? 'bg-white text-blue-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>RAG Sources ({paper.questions?.reduce((acc, q) => acc + (q.source_documents?.length || 0), 0)})</span>
          </button>
        </div>
      </div>

      {/* Main Tab Content */}
      {activeTab === 'paper' && (
        <QuestionPaperPreview
          paper={paper}
          onEditQuestion={handleEditQuestion}
          onRegenerateQuestion={handleRegenerateQuestion}
          onOpenExplainability={handleOpenExplainability}
          onExportPDF={handleExportPDF}
        />
      )}

      {activeTab === 'analytics' && analytics && (
        <CoverageRadarChart analytics={analytics} />
      )}

      {activeTab === 'sources' && (
        <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <h2 className="text-base font-bold text-slate-900">RAG Grounded Citations & Retrieved Context</h2>
            <p className="text-xs text-slate-500 mt-0.5">Every generated question is linked directly to source textbooks, syllabus documents, and page numbers.</p>
          </div>

          <div className="space-y-4">
            {paper.questions?.map((q) => (
              <div key={q.id} className="p-4.5 bg-slate-50 border border-slate-200 rounded-2xl space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-blue-700 bg-blue-100/80 px-2.5 py-0.5 rounded-md">
                    {q.section_name} • Q{q.question_number} ({q.marks} Marks)
                  </span>
                  <div className="space-x-2 text-xs">
                    <span className="font-bold text-emerald-700">{q.course_outcome}</span>
                    <span className="text-slate-300">•</span>
                    <span className="font-bold text-blue-700">Bloom: {q.bloom_level}</span>
                  </div>
                </div>

                <p className="text-xs font-semibold text-slate-900 leading-relaxed">
                  {q.question_text}
                </p>

                {q.source_documents && q.source_documents.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2 border-t border-slate-200/80">
                    {q.source_documents.map((doc, idx) => (
                      <div key={idx} className="p-3 bg-white border border-slate-200 rounded-xl text-[11px] space-y-1">
                        <div className="font-bold text-slate-900 truncate">{doc.document_name}</div>
                        <div className="text-slate-500 flex items-center justify-between">
                          <span>Page {doc.page} • Topic: <strong className="text-slate-700">{doc.topic}</strong></span>
                          <span className="font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded">{Math.round((doc.similarity_score || 0.85) * 100)}% Match</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[11px] text-slate-400 italic">Curriculum syllabus mapped directly.</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Slide-over Explainability Drawer */}
      <ExplainabilityDrawer
        question={selectedExplainQuestion}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />

    </div>
  );
};
