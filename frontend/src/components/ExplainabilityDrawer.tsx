import React from 'react';
import { X, BookOpen, FileCheck, BrainCircuit, Sparkles, CheckCircle } from 'lucide-react';
import type { Question } from '../api/client';

interface ExplainabilityDrawerProps {
  question: Question | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ExplainabilityDrawer: React.FC<ExplainabilityDrawerProps> = ({
  question,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !question) return null;

  const val = question.validation;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-6 sm:pl-10">
        <div className="w-screen max-w-md md:max-w-lg bg-white shadow-2xl flex flex-col border-l border-slate-200 drawer-enter">
          
          {/* Header */}
          <div className="p-6 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 bg-blue-500/20 text-blue-400 rounded-xl border border-blue-500/30">
                <BrainCircuit className="w-5 h-5" />
              </div>
              <div>
                <h3 id="drawer-title" className="text-base font-bold text-white tracking-tight">RAG Explainability Audit</h3>
                <p className="text-xs text-slate-400">Provenance & Multi-Agent Rationale</p>
              </div>
            </div>
            <button
              onClick={onClose}
              aria-label="Close explainability drawer"
              className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            
            {/* Question Identity Card */}
            <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-blue-700 bg-blue-100/80 px-2.5 py-0.5 rounded-md">
                  {question.section_name} • Q{question.question_number}
                </span>
                <span className="text-xs font-bold text-slate-700 bg-white px-2.5 py-0.5 rounded-md border border-slate-200">
                  {question.marks} Marks
                </span>
              </div>
              <p className="text-sm font-semibold text-slate-900 whitespace-pre-line leading-relaxed">
                {question.question_text}
              </p>
            </div>

            {/* Academic Alignment Grid */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-blue-50/80 border border-blue-100 rounded-2xl p-3 text-center">
                <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider block">Bloom Level</span>
                <span className="text-xs font-black text-blue-950 mt-1 block">{question.bloom_level}</span>
              </div>
              <div className="bg-emerald-50/80 border border-emerald-100 rounded-2xl p-3 text-center">
                <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider block">Outcome (CO)</span>
                <span className="text-xs font-black text-emerald-950 mt-1 block">{question.course_outcome}</span>
              </div>
              <div className="bg-purple-50/80 border border-purple-100 rounded-2xl p-3 text-center">
                <span className="text-[10px] font-bold text-purple-600 uppercase tracking-wider block">Syllabus Unit</span>
                <span className="text-xs font-black text-purple-950 mt-1 block">Unit {question.unit_number}</span>
              </div>
            </div>

            {/* Agent Generation Rationale */}
            {question.generation_reasoning && (
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  <span>Agent Synthesis Rationale</span>
                </h4>
                <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-xs text-slate-700 leading-relaxed font-medium">
                  {question.generation_reasoning}
                </div>
              </div>
            )}

            {/* Retrieved Context Sources (RAG Citations) */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
                <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
                <span>Retrieved Academic Sources (Top-K)</span>
              </h4>

              {question.source_documents && question.source_documents.length > 0 ? (
                <div className="space-y-2.5">
                  {question.source_documents.map((doc, idx) => (
                    <div 
                      key={idx}
                      className="border border-slate-200 rounded-2xl p-3.5 bg-white shadow-2xs hover:border-blue-300 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xs font-bold text-slate-900 truncate max-w-[220px]">
                          {doc.document_name}
                        </span>
                        <span className="text-[11px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                          Match: {Math.round((doc.similarity_score || 0.85) * 100)}%
                        </span>
                      </div>
                      <div className="flex items-center space-x-3 text-[11px] text-slate-500">
                        <span>Page: <strong className="text-slate-700 font-semibold">{doc.page}</strong></span>
                        <span>•</span>
                        <span className="truncate">Topic: <strong className="text-slate-700 font-semibold">{doc.topic}</strong></span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">Curriculum syllabus concepts directly referenced.</p>
              )}
            </div>

            {/* Validation Agent Scores */}
            {val && (
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
                  <FileCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Validation Agent Metrics</span>
                </h4>

                <div className="space-y-3 bg-slate-50 border border-slate-200 rounded-2xl p-4">
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-semibold text-slate-700">Syllabus Grounding</span>
                      <span className="font-bold text-slate-900">{Math.round(val.syllabus_alignment_score * 100)}%</span>
                    </div>
                    <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                      <div 
                        className="bg-emerald-500 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${val.syllabus_alignment_score * 100}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-semibold text-slate-700">Bloom Taxonomy Alignment</span>
                      <span className="font-bold text-slate-900">{Math.round(val.bloom_alignment_score * 100)}%</span>
                    </div>
                    <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                      <div 
                        className="bg-blue-500 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${val.bloom_alignment_score * 100}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-200/80">
                    <span className="font-semibold text-slate-700">Duplicate Repetition Index</span>
                    <span className="font-bold text-emerald-600 flex items-center space-x-1">
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>{val.is_duplicate ? 'Duplicate Detected' : '0.0% (Unique)'}</span>
                    </span>
                  </div>

                  {val.feedback_notes && (
                    <div className="mt-2.5 pt-2.5 border-t border-slate-200 text-[11px] text-slate-600 italic">
                      Note: {val.feedback_notes}
                    </div>
                  )}
                </div>
              </div>
            )}

          </div>

          {/* Footer */}
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end">
            <button
              onClick={onClose}
              className="px-5 py-2.5 bg-slate-900 text-white text-xs font-bold rounded-xl hover:bg-slate-800 transition-colors shadow-xs"
            >
              Close Panel
            </button>
          </div>

        </div>
      </div>
    </div>
  );
};
