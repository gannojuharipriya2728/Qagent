import React, { useState, useEffect } from 'react';
import { api, type CourseAnalysisResponse, type CourseAnalysisApprovalRequest } from '../api/client';
import { 
  Sparkles, 
  CheckCircle2, 
  Edit3, 
  RefreshCw, 
  BookOpen, 
  Target, 
  PieChart, 
  ArrowRight, 
  AlertCircle,
  FileText,
  GraduationCap
} from 'lucide-react';

interface AcademicAnalysisPageProps {
  courseId: number;
  onApproveSuccess?: () => void;
  onNavigateExam?: () => void;
  onNavigateBack?: () => void;
}

export const AcademicAnalysisPage: React.FC<AcademicAnalysisPageProps> = ({
  courseId,
  onApproveSuccess,
  onNavigateExam,
  onNavigateBack
}) => {
  const [analysis, setAnalysis] = useState<CourseAnalysisResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [approving, setApproving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editedUnits, setEditedUnits] = useState<any[]>([]);
  const [editedCOs, setEditedCOs] = useState<any[]>([]);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (courseId) {
      fetchAnalysis();
    }
  }, [courseId]);

  const fetchAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/courses/${courseId}/analysis`);
      setAnalysis(res.data);
      setEditedUnits(res.data.units || []);
      setEditedCOs(res.data.course_outcomes || []);
    } catch (err: any) {
      console.error('Error fetching course analysis:', err);
      setError(err.response?.data?.detail || 'Failed to load course analysis. You can trigger an automatic analysis below.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    try {
      setAnalyzing(true);
      setError(null);
      const res = await api.post(`/courses/${courseId}/analyze`);
      setAnalysis(res.data);
      setEditedUnits(res.data.units || []);
      setEditedCOs(res.data.course_outcomes || []);
      setSuccessMessage('Curriculum analyzed successfully from uploaded resources!');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      console.error('Analysis failed:', err);
      setError(err.response?.data?.detail || 'Failed to analyze course resources');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleApprove = async () => {
    try {
      setApproving(true);
      const payload: CourseAnalysisApprovalRequest = {
        units: editedUnits.map((u, idx) => ({
          unit_number: u.unit_number || idx + 1,
          title: u.title || `Unit ${idx + 1}`,
          topics: u.topics || '',
        })),
        course_outcomes: editedCOs.map((co, idx) => ({
          code: co.code || `CO${idx + 1}`,
          description: co.description || '',
          target_bloom_level: co.target_bloom_level || 'Understand',
        })),
      };

      await api.post(`/courses/${courseId}/analysis/approve`, payload);
      setSuccessMessage('Curriculum analysis approved! This is now the official course configuration.');
      setIsEditing(false);
      fetchAnalysis();
      if (onApproveSuccess) onApproveSuccess();
    } catch (err: any) {
      console.error('Failed to approve analysis:', err);
      alert(err.response?.data?.detail || 'Failed to approve analysis');
    } finally {
      setApproving(false);
    }
  };

  const handleUnitChange = (index: number, field: string, value: any) => {
    const updated = [...editedUnits];
    updated[index] = { ...updated[index], [field]: value };
    setEditedUnits(updated);
  };

  const handleCOChange = (index: number, field: string, value: any) => {
    const updated = [...editedCOs];
    updated[index] = { ...updated[index], [field]: value };
    setEditedCOs(updated);
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-slate-600 font-medium text-sm">Loading Academic Content Analysis...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-8 rounded-3xl shadow-xl relative overflow-hidden mb-8">
        <div className="absolute right-0 top-0 translate-x-12 -translate-y-8 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/30 border border-indigo-400/30 text-indigo-200 text-xs font-medium mb-3">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              Automated Document & Curriculum Intelligence
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-2">
              Academic Content Analysis
            </h1>
            <p className="text-indigo-200 text-sm max-w-xl">
              AI-extracted syllabus structure, topics, and course outcomes grounded in your uploaded academic documents.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-white rounded-xl text-sm font-semibold shadow-md transition-all"
            >
              <RefreshCw className={`w-4 h-4 ${analyzing ? 'animate-spin' : ''}`} />
              {analyzing ? 'Analyzing Documents...' : 'Re-Run AI Analysis'}
            </button>
            {onNavigateBack && (
              <button
                onClick={onNavigateBack}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-sm font-medium transition-colors"
              >
                Back
              </button>
            )}
          </div>
        </div>
      </div>

      {successMessage && (
        <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-2xl flex items-center gap-3 animate-fade-in text-sm font-medium">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          {successMessage}
        </div>
      )}

      {error && !analysis && (
        <div className="bg-amber-50 border border-amber-200 text-amber-800 p-6 rounded-2xl mb-8">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-sm">No Existing Analysis Found</p>
              <p className="text-xs text-amber-700 mt-1 mb-4">
                Please make sure you have uploaded course resources or syllabus documents, then trigger AI analysis.
              </p>
              <button
                onClick={handleRunAnalysis}
                disabled={analyzing}
                className="inline-flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold"
              >
                <Sparkles className="w-3.5 h-3.5" />
                {analyzing ? 'Analyzing...' : 'Run Analysis Now'}
              </button>
            </div>
          </div>
        </div>
      )}

      {analysis && (
        <div className="space-y-8">
          {/* Status & Course Info Bar */}
          <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full sm:w-auto">
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase">Course</span>
                <p className="text-sm font-bold text-slate-800">{analysis.course_code}</p>
                <p className="text-xs text-slate-600 truncate max-w-[150px]">{analysis.course_name}</p>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase">Department</span>
                <p className="text-sm font-medium text-slate-800">{analysis.department || 'General'}</p>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase">Semester / AY</span>
                <p className="text-sm font-medium text-slate-800">{analysis.semester} • {analysis.academic_year}</p>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase">Analysis Status</span>
                <div>
                  <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full mt-0.5 ${
                    analysis.analysis_status === 'approved' 
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' 
                      : 'bg-amber-100 text-amber-800 border border-amber-300'
                  }`}>
                    {analysis.analysis_status === 'approved' ? (
                      <><CheckCircle2 className="w-3 h-3" /> Approved by Faculty</>
                    ) : (
                      <><AlertCircle className="w-3 h-3" /> Pending Approval</>
                    )}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 self-end sm:self-center">
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 border border-slate-300 hover:border-indigo-400 text-slate-700 hover:text-indigo-700 rounded-xl text-xs font-medium transition-colors"
              >
                <Edit3 className="w-3.5 h-3.5" />
                {isEditing ? 'Done Editing' : 'Edit Analysis'}
              </button>
              <button
                onClick={handleApprove}
                disabled={approving}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-800 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                {approving ? 'Approving...' : 'Approve Analysis'}
              </button>
            </div>
          </div>

          {/* Units Breakdown */}
          <div className="bg-white border border-slate-200/80 rounded-3xl p-6 sm:p-8 shadow-sm">
            <h2 className="text-base font-bold text-slate-900 mb-6 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-indigo-600" />
              Syllabus Units & Topics ({editedUnits.length})
            </h2>

            <div className="space-y-4">
              {editedUnits.map((unit, idx) => (
                <div key={idx} className="p-5 rounded-2xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors">
                  {isEditing ? (
                    <div className="space-y-3">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-bold text-indigo-600 uppercase">Unit {unit.unit_number || idx + 1}:</span>
                        <input
                          type="text"
                          value={unit.title}
                          onChange={(e) => handleUnitChange(idx, 'title', e.target.value)}
                          className="flex-1 px-3 py-1.5 rounded-lg border border-slate-300 text-sm font-semibold"
                          placeholder="Unit Title"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-slate-500 uppercase">Topics</label>
                        <textarea
                          rows={3}
                          value={unit.topics}
                          onChange={(e) => handleUnitChange(idx, 'topics', e.target.value)}
                          className="w-full mt-1 px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-mono"
                          placeholder="Comma-separated topics"
                        />
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-bold text-slate-900">
                          Unit {unit.unit_number || idx + 1}: {unit.title}
                        </h3>
                        {unit.source_documents && unit.source_documents.length > 0 && (
                          <span className="text-xs text-slate-400 flex items-center gap-1">
                            <FileText className="w-3 h-3" /> {unit.source_documents.length} Source doc(s)
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed bg-white p-3 rounded-xl border border-slate-100">
                        {unit.topics}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Course Outcomes (COs) */}
          <div className="bg-white border border-slate-200/80 rounded-3xl p-6 sm:p-8 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Target className="w-5 h-5 text-indigo-600" />
                Course Outcomes (COs) ({editedCOs.length})
              </h2>
              <span className="text-xs text-slate-500">
                Grounded in uploaded documents • Faculty review required
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {editedCOs.map((co, idx) => {
                const isExplicit = co.source_confidence === 'explicit' || co.source_confidence === 'High';
                return (
                  <div key={idx} className="p-5 rounded-2xl border border-slate-200/80 bg-slate-50/40 relative">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-mono font-bold px-2 py-0.5 bg-indigo-100 text-indigo-800 rounded">
                        {co.code}
                      </span>
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                        isExplicit ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                      }`}>
                        {isExplicit ? 'Explicit in Syllabus' : 'AI-Proposed'}
                      </span>
                    </div>

                    {isEditing ? (
                      <div className="space-y-2 mt-2">
                        <textarea
                          rows={2}
                          value={co.description}
                          onChange={(e) => handleCOChange(idx, 'description', e.target.value)}
                          className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-900"
                        />
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-500">Target Bloom:</span>
                          <select
                            value={co.target_bloom_level || 'Understand'}
                            onChange={(e) => handleCOChange(idx, 'target_bloom_level', e.target.value)}
                            className="text-xs border border-slate-300 rounded px-2 py-1"
                          >
                            <option>Remember</option>
                            <option>Understand</option>
                            <option>Apply</option>
                            <option>Analyze</option>
                            <option>Evaluate</option>
                            <option>Create</option>
                          </select>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <p className="text-xs text-slate-700 leading-relaxed mb-3">
                          {co.description}
                        </p>
                        <div className="flex items-center gap-2 text-[11px] text-slate-500">
                          <GraduationCap className="w-3.5 h-3.5 text-indigo-500" />
                          <span>Cognitive Target: <b>{co.target_bloom_level || 'Understand'}</b></span>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Bloom's Taxonomy Recommendations */}
          {analysis.bloom_recommendations && analysis.bloom_recommendations.length > 0 && (
            <div className="bg-white border border-slate-200/80 rounded-3xl p-6 sm:p-8 shadow-sm">
              <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
                <PieChart className="w-5 h-5 text-indigo-600" />
                Recommended Cognitive Level Distribution (Bloom's Taxonomy)
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
                {analysis.bloom_recommendations.map((rec, idx) => (
                  <div key={idx} className="p-3 rounded-2xl bg-indigo-50/50 border border-indigo-100 text-center">
                    <p className="text-xs font-semibold text-slate-600">{rec.level}</p>
                    <p className="text-lg font-bold text-indigo-700 mt-1">{rec.recommended_percentage}%</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Bottom Action Card */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-gradient-to-r from-indigo-50 to-slate-50 p-6 rounded-3xl border border-indigo-100 shadow-sm">
            <div className="text-xs text-slate-600">
              <p className="font-semibold text-slate-800 mb-0.5">Ready to create question papers?</p>
              <p>Once you approve the academic analysis, you can build dynamic, customizable examination papers.</p>
            </div>
            <div className="flex items-center gap-3 w-full sm:w-auto">
              <button
                onClick={handleApprove}
                disabled={approving}
                className="flex-1 sm:flex-initial px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-md transition-colors"
              >
                {approving ? 'Approving...' : 'Approve Analysis'}
              </button>
              {onNavigateExam && (
                <button
                  onClick={onNavigateExam}
                  className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-md transition-colors"
                >
                  <span>Create Examination</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
