import React, { useState } from 'react';
import { 
  Download, Printer, Edit3, RefreshCw, HelpCircle, CheckCircle2
} from 'lucide-react';
import type { QuestionPaper, Question } from '../api/client';

interface QuestionPaperPreviewProps {
  paper: QuestionPaper;
  onEditQuestion: (questionId: number, newText: string, marks: number) => Promise<void>;
  onRegenerateQuestion: (questionId: number) => Promise<void>;
  onOpenExplainability: (question: Question) => void;
  onExportPDF: () => void;
}

export const QuestionPaperPreview: React.FC<QuestionPaperPreviewProps> = ({
  paper,
  onEditQuestion,
  onRegenerateQuestion,
  onOpenExplainability,
  onExportPDF
}) => {
  const [editingQId, setEditingQId] = useState<number | null>(null);
  const [editText, setEditText] = useState('');
  const [editMarks, setEditMarks] = useState(0);
  const [isRegeneratingId, setIsRegeneratingId] = useState<number | null>(null);

  const startEdit = (q: Question) => {
    setEditingQId(q.id);
    setEditText(q.question_text);
    setEditMarks(q.marks);
  };

  const handleSaveEdit = async (qId: number) => {
    await onEditQuestion(qId, editText, editMarks);
    setEditingQId(null);
  };

  const handleRegen = async (qId: number) => {
    setIsRegeneratingId(qId);
    try {
      await onRegenerateQuestion(qId);
    } finally {
      setIsRegeneratingId(null);
    }
  };

  // Group questions by section
  const sectionsMap: Record<string, Question[]> = {};
  for (const q of paper.questions || []) {
    const sec = q.section_name || 'Section A';
    if (!sectionsMap[sec]) sectionsMap[sec] = [];
    sectionsMap[sec].push(q);
  }

  return (
    <div className="space-y-6">
      
      {/* Action Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-4.5 rounded-3xl border border-slate-200/80 shadow-xs no-print">
        <div className="flex items-center space-x-2.5">
          <span className="text-xs font-extrabold text-slate-400 uppercase tracking-wider">Status:</span>
          <span className="text-xs font-extrabold bg-emerald-100 text-emerald-800 px-3 py-0.5 rounded-full border border-emerald-200 flex items-center space-x-1">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
            <span>{paper.status || 'Validated'}</span>
          </span>
          <span className="text-slate-300">•</span>
          <span className="text-xs text-slate-600 font-semibold">
            {paper.questions?.length || 0} Questions • <strong className="text-slate-900">{paper.total_marks} Marks</strong>
          </span>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={() => window.print()}
            className="px-3.5 py-2 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors flex items-center space-x-1.5 cursor-pointer"
          >
            <Printer className="w-4 h-4" />
            <span>Print</span>
          </button>

          <button
            onClick={onExportPDF}
            className="px-4.5 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 rounded-xl transition-all shadow-sm shadow-blue-500/25 flex items-center space-x-1.5 cursor-pointer active:scale-98"
          >
            <Download className="w-4 h-4" />
            <span>Download Official PDF</span>
          </button>
        </div>
      </div>

      {/* Official Exam Sheet Container */}
      <div className="exam-sheet bg-white border border-slate-200 rounded-3xl p-8 sm:p-12 shadow-sm max-w-4xl mx-auto text-slate-900 space-y-6">
        
        {/* Header Section */}
        <div className="text-center border-b-2 border-slate-900 pb-6">
          <h2 className="text-base sm:text-lg font-black tracking-wide uppercase text-slate-900 font-sans">
            {paper.institution_name || 'Department of Computer Science & Engineering'}
          </h2>
          <h3 className="text-xs sm:text-sm font-extrabold text-slate-700 mt-1 uppercase tracking-wider">
            {paper.examination_name || 'Semester End Examination'}
          </h3>

          {/* Metadata Box Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mt-5 bg-slate-50 border border-slate-300 rounded-2xl p-3.5 text-left text-xs">
            <div>
              <span className="text-slate-400 block font-bold text-[10px] uppercase tracking-wider">Course Code:</span>
              <strong className="text-slate-900 text-sm font-extrabold">{paper.course_code || 'CS301'}</strong>
            </div>
            <div>
              <span className="text-slate-400 block font-bold text-[10px] uppercase tracking-wider">Course Name:</span>
              <strong className="text-slate-900 truncate block text-xs font-bold">{paper.course_name || paper.title}</strong>
            </div>
            <div>
              <span className="text-slate-400 block font-bold text-[10px] uppercase tracking-wider">Duration:</span>
              <strong className="text-slate-900 text-xs font-bold">{paper.duration_minutes || 180} Minutes</strong>
            </div>
            <div>
              <span className="text-slate-400 block font-bold text-[10px] uppercase tracking-wider">Max Marks:</span>
              <strong className="text-slate-900 text-xs font-bold">{paper.total_marks || 70} Marks</strong>
            </div>
          </div>

          {/* Instructions */}
          <p className="text-xs text-slate-600 italic mt-3.5 text-left leading-relaxed">
            <strong className="font-bold text-slate-800 not-italic">Instructions:</strong> {paper.instructions || 'Answer all questions in Section A and any five full questions from Section B.'}
          </p>
        </div>

        {/* Questions Grouped by Section */}
        <div className="space-y-8">
          {Object.entries(sectionsMap).map(([sectionName, questions]) => (
            <div key={sectionName} className="space-y-3">
              
              <div className="text-center font-extrabold text-xs uppercase tracking-widest text-slate-800 bg-slate-100 py-1.5 rounded-xl border border-slate-200/80">
                --- {sectionName} ---
              </div>

              <div className="border border-slate-300 rounded-2xl overflow-hidden shadow-2xs">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-100/90 border-b border-slate-300 text-slate-800 font-extrabold">
                      <th className="py-2.5 px-3 w-12 text-center">Q.No</th>
                      <th className="py-2.5 px-4">Question Description</th>
                      <th className="py-2.5 px-3 w-16 text-center">Marks</th>
                      <th className="py-2.5 px-3 w-14 text-center">CO</th>
                      <th className="py-2.5 px-3 w-20 text-center">Bloom</th>
                      <th className="py-2.5 px-3 w-28 text-center no-print">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {questions.map((q) => {
                      const isEditing = editingQId === q.id;
                      const isRegenerating = isRegeneratingId === q.id;

                      return (
                        <tr key={q.id} className="hover:bg-slate-50/80 transition-colors">
                          <td className="py-3.5 px-3 font-extrabold text-center align-top text-slate-900">
                            {q.question_number}
                          </td>
                          
                          <td className="py-3.5 px-4 align-top">
                            {isEditing ? (
                              <div className="space-y-2">
                                <textarea
                                  value={editText}
                                  onChange={(e) => setEditText(e.target.value)}
                                  rows={3}
                                  className="w-full p-2.5 border border-blue-400 rounded-xl text-xs font-sans focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                                />
                                <div className="flex items-center space-x-2">
                                  <input
                                    type="number"
                                    value={editMarks}
                                    onChange={(e) => setEditMarks(Number(e.target.value))}
                                    className="w-20 p-1.5 border border-slate-300 rounded-lg text-xs font-bold"
                                    placeholder="Marks"
                                  />
                                  <button
                                    onClick={() => handleSaveEdit(q.id)}
                                    className="px-3 py-1 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-500 cursor-pointer"
                                  >
                                    Save
                                  </button>
                                  <button
                                    onClick={() => setEditingQId(null)}
                                    className="px-3 py-1 bg-slate-200 text-slate-700 rounded-lg text-xs font-bold hover:bg-slate-300 cursor-pointer"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <div>
                                <p className="whitespace-pre-line leading-relaxed text-slate-800 font-medium text-xs sm:text-[13px]">
                                  {q.question_text}
                                </p>
                                {q.is_revised && (
                                  <span className="inline-block mt-1 text-[10px] text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-semibold">
                                    Revised by Agent ({q.revision_count} {q.revision_count === 1 ? 'repair' : 'repairs'})
                                  </span>
                                )}
                              </div>
                            )}
                          </td>

                          <td className="py-3.5 px-3 text-center align-top font-black text-slate-900">
                            [{q.marks}]
                          </td>

                          <td className="py-3.5 px-3 text-center align-top font-bold text-emerald-700">
                            <span className="bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                              {q.course_outcome}
                            </span>
                          </td>

                          <td className="py-3.5 px-3 text-center align-top font-bold text-blue-700">
                            <span className="bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                              {q.bloom_level}
                            </span>
                          </td>

                          <td className="py-3.5 px-3 text-center align-top no-print">
                            <div className="flex items-center justify-center space-x-1.5">
                              <button
                                onClick={() => onOpenExplainability(q)}
                                title="Why this question? (RAG Provenance)"
                                className="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors border border-indigo-200 cursor-pointer"
                              >
                                <HelpCircle className="w-3.5 h-3.5" />
                              </button>

                              <button
                                onClick={() => startEdit(q)}
                                title="Edit Question"
                                className="p-1.5 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors border border-slate-200 cursor-pointer"
                              >
                                <Edit3 className="w-3.5 h-3.5" />
                              </button>

                              <button
                                onClick={() => handleRegen(q.id)}
                                disabled={isRegenerating}
                                title="Regenerate with Agent 3"
                                className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors border border-blue-200 disabled:opacity-50 cursor-pointer"
                              >
                                <RefreshCw className={`w-3.5 h-3.5 ${isRegenerating ? 'animate-spin' : ''}`} />
                              </button>
                            </div>
                          </td>

                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

            </div>
          ))}
        </div>

        {/* Footer Note */}
        <div className="mt-10 pt-4 border-t border-slate-300 flex justify-between items-center text-[10px] text-slate-400 font-medium">
          <span>Autonomous Examination Synthesis Standard</span>
          <span>Verified by QAgent Multi-Agent Framework</span>
        </div>

      </div>

    </div>
  );
};
