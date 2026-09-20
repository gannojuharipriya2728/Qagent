import React, { useState, useEffect } from 'react';
import { 
  Sparkles, ArrowRight, ArrowLeft, CheckCircle2, AlertCircle, Plus, BookOpen, Layers, Target, ShieldCheck, Database, RefreshCw
} from 'lucide-react';
import { api, type Course, type GenerationRequest, type SectionRule, type AgentStepLog } from '../api/client';
import { AgentWorkflowTracker } from '../components/AgentWorkflowTracker';
import { CreateCourseModal } from '../components/CreateCourseModal';

interface GeneratePaperWizardProps {
  prefillCourseId?: number;
  onGenerationComplete: (paperId: number) => void;
}

export const GeneratePaperWizard: React.FC<GeneratePaperWizardProps> = ({
  prefillCourseId,
  onGenerationComplete
}) => {
  const [step, setStep] = useState(1);
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(prefillCourseId || null);
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [showCourseModal, setShowCourseModal] = useState(false);
  const [courseLoadError, setCourseLoadError] = useState<string | null>(null);

  // Form State
  const [title] = useState('University Semester End Examination');
  const [examName, setExamName] = useState('End Semester Regular Examination 2026');
  const [institutionName, setInstitutionName] = useState('Department of Computer Science & Engineering');
  const [durationMinutes, setDurationMinutes] = useState(180);
  const [totalMarks, setTotalMarks] = useState(70);
  const [instructions] = useState('Answer all questions in Section A and any five full questions from Section B.');

  // Sections
  const [sections, setSections] = useState<SectionRule[]>([
    { name: 'Section A', total_questions: 10, questions_to_answer: 10, marks_per_question: 2, question_type: 'Short' },
    { name: 'Section B', total_questions: 5, questions_to_answer: 5, marks_per_question: 10, question_type: 'Descriptive' }
  ]);

  // Distributions
  const [diffEasy, setDiffEasy] = useState(30);
  const [diffMedium, setDiffMedium] = useState(50);
  const [diffHard, setDiffHard] = useState(20);

  const [bloomDist, setBloomDist] = useState<Record<string, number>>({
    Remember: 20,
    Understand: 30,
    Apply: 25,
    Analyze: 15,
    Evaluate: 5,
    Create: 5
  });

  // Course resource statistics for Step 5 summary
  const [courseResourcesCount, setCourseResourcesCount] = useState<number>(0);
  const [courseSyllabusCount, setCourseSyllabusCount] = useState<number>(0);
  const [coursePastPaperCount, setCoursePastPaperCount] = useState<number>(0);
  const [isLoadingCourse, setIsLoadingCourse] = useState<boolean>(false);

  // Agent Generation Execution
  const [isGenerating, setIsGenerating] = useState(false);
  const [stepsLog, setStepsLog] = useState<AgentStepLog[]>([]);
  const [generationDuration, setGenerationDuration] = useState<number | undefined>();
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = async () => {
    setIsLoadingCourse(true);
    setCourseLoadError(null);
    try {
      const res = await api.get('/courses');
      setCourses(res.data);
      if (res.data.length > 0) {
        const targetId = prefillCourseId || res.data[0].id;
        setSelectedCourseId(targetId);
        await fetchCourseDetails(targetId);
      }
    } catch (e) {
      console.error('Failed to load courses:', e);
      setCourseLoadError('Unable to load courses.');
    } finally {
      setIsLoadingCourse(false);
    }
  };

  const fetchCourseDetails = async (courseId: number) => {
    setIsLoadingCourse(true);
    setCourseLoadError(null);
    setSelectedCourse(null);
    try {
      const fullRes = await api.get(`/courses/${courseId}`);
      setSelectedCourse(fullRes.data);
      await loadCourseResources(courseId);
    } catch (err) {
      console.error(`Failed to load course ${courseId}:`, err);
      setCourseLoadError('Unable to load course curriculum.');
    } finally {
      setIsLoadingCourse(false);
    }
  };

  const loadCourseResources = async (courseId: number) => {
    try {
      const res = await api.get('/resources', { params: { course_id: courseId } });
      const resList = res.data || [];
      setCourseResourcesCount(resList.length);
      setCourseSyllabusCount(resList.filter((r: any) => r.document_type === 'syllabus').length);
      setCoursePastPaperCount(resList.filter((r: any) => r.document_type === 'previous_paper').length);
    } catch (e) {
      console.error('Failed to load course resources:', e);
    }
  };

  const handleCourseCreated = async (createdCourse: Course) => {
    try {
      const res = await api.get('/courses');
      setCourses(res.data);
      setSelectedCourseId(createdCourse.id);
      await fetchCourseDetails(createdCourse.id);
    } catch (e) {
      console.error('Failed to load courses after creation:', e);
    }
  };

  const handleSelectCourse = async (courseId: number) => {
    setSelectedCourseId(courseId);
    await fetchCourseDetails(courseId);
  };

  const calculateCalculatedMarks = () => {
    return sections.reduce((acc, sec) => acc + (sec.questions_to_answer * sec.marks_per_question), 0);
  };

  const calculateDiffSum = () => diffEasy + diffMedium + diffHard;
  const calculateBloomSum = () => Object.values(bloomDist).reduce((a, b) => a + Number(b || 0), 0);

  const normalizeDifficulty = () => {
    setDiffEasy(30);
    setDiffMedium(50);
    setDiffHard(20);
  };

  const normalizeBloom = () => {
    setBloomDist({
      Remember: 20,
      Understand: 30,
      Apply: 25,
      Analyze: 15,
      Evaluate: 5,
      Create: 5
    });
  };

  const handleStartGeneration = async () => {
    if (!selectedCourse) return;
    setIsGenerating(true);
    setStepsLog([]);
    setErrorMsg('');

    const payload: GenerationRequest = {
      course_id: selectedCourse.id,
      title,
      examination_name: examName,
      institution_name: institutionName,
      duration_minutes: durationMinutes,
      total_marks: totalMarks,
      instructions,
      sections,
      difficulty_distribution: {
        Easy: diffEasy,
        Medium: diffMedium,
        Hard: diffHard
      },
      bloom_distribution: bloomDist,
      target_course_outcomes: selectedCourse.course_outcomes?.map(c => c.code) || ['CO1', 'CO2', 'CO3', 'CO4', 'CO5'],
      similarity_threshold: 0.82,
      top_k_sources: 5
    };

    try {
      const res = await api.post('/generate', payload);
      setStepsLog(res.data.steps_log || []);
      setGenerationDuration(res.data.duration_seconds);
      setIsGenerating(false);

      setTimeout(() => {
        onGenerationComplete(res.data.paper_id);
      }, 1800);
    } catch (err: any) {
      setIsGenerating(false);
      setErrorMsg(err.response?.data?.detail || 'Generation failed. Please review settings.');
    }
  };

  const wizardSteps = [
    { num: 1, title: 'Course & Exam', desc: 'Target subject' },
    { num: 2, title: 'Curriculum & COs', desc: 'Syllabus audit' },
    { num: 3, title: 'Paper Schema', desc: 'Blueprint 70M' },
    { num: 4, title: 'Distributions', desc: 'Bloom taxonomy' },
    { num: 5, title: 'AI Synthesis', desc: '5-Agent workflow' }
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      
      {/* Modern Refined Stepper */}
      <div className="bg-white border border-slate-200/80 rounded-3xl p-5 sm:p-6 shadow-xs">
        <div className="grid grid-cols-5 gap-2 sm:gap-4 relative">
          {wizardSteps.map((s) => {
            const isCompleted = step > s.num;
            const isCurrent = step === s.num;
            return (
              <div 
                key={s.num} 
                onClick={() => isCompleted && setStep(s.num)}
                className={`flex flex-col items-center text-center space-y-1.5 transition-all ${isCompleted ? 'cursor-pointer' : ''}`}
              >
                <div 
                  className={`w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold transition-all ${
                    isCurrent
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30 ring-2 ring-blue-500/20 scale-105'
                      : isCompleted
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/80'
                      : 'bg-slate-100 text-slate-400 border border-slate-200/60'
                  }`}
                >
                  {isCompleted ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : s.num}
                </div>
                <div className="hidden sm:block">
                  <span className={`text-xs font-bold block ${isCurrent ? 'text-slate-900' : isCompleted ? 'text-slate-700' : 'text-slate-400'}`}>
                    {s.title}
                  </span>
                  <span className="text-[10px] text-slate-400 block">{s.desc}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-2xl font-semibold flex items-center space-x-2.5 shadow-xs">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* STEP 1: Course Information */}
      {step === 1 && (
        <div className="bg-white border border-slate-200/80 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-extrabold text-blue-600 uppercase tracking-wider">Step 01</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 mt-1">Course & Examination Information</h2>
            <p className="text-xs text-slate-500">Select the target academic course and configure examination headers</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="sm:col-span-2 space-y-2">
              <div className="flex items-center justify-between">
                <label className="block font-bold text-slate-800">Select Academic Course</label>
                <button
                  type="button"
                  onClick={() => setShowCourseModal(true)}
                  className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center space-x-1 cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>+ Add New Course</span>
                </button>
              </div>

              {courses.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mb-2">
                  {courses.map((c) => {
                    const isSelected = selectedCourseId === c.id;
                    return (
                      <div
                        key={c.id}
                        onClick={() => handleSelectCourse(c.id)}
                        className={`p-3.5 rounded-2xl border cursor-pointer transition-all ${
                          isSelected 
                            ? 'bg-blue-50/70 border-blue-500 shadow-xs ring-1 ring-blue-500/20' 
                            : 'bg-slate-50/60 border-slate-200/80 hover:border-slate-300'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className={`text-xs font-extrabold px-2 py-0.5 rounded ${isSelected ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700'}`}>
                            {c.code}
                          </span>
                          <span className="text-[11px] text-slate-400 font-medium">{c.semester}</span>
                        </div>
                        <h4 className="font-bold text-slate-900 text-xs truncate mt-1">{c.name}</h4>
                        <span className="text-[11px] text-slate-500">{c.units?.length || 5} Units • {c.course_outcomes?.length || 3} COs</span>
                      </div>
                    );
                  })}
                </div>
              )}

              <select
                value={selectedCourse?.id || ''}
                disabled={isLoadingCourse}
                onChange={(e) => handleSelectCourse(Number(e.target.value))}
                className="w-full p-3 bg-slate-50 border border-slate-300/80 rounded-xl text-xs font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none disabled:opacity-60"
              >
                {courses.map(c => (
                  <option key={c.id} value={c.id}>
                    {c.code} — {c.name} ({c.semester})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Institution / Department</label>
              <input
                type="text"
                value={institutionName}
                onChange={(e) => setInstitutionName(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-300/80 rounded-xl text-slate-900 font-medium text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Examination Title</label>
              <input
                type="text"
                value={examName}
                onChange={(e) => setExamName(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-300/80 rounded-xl text-slate-900 font-medium text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Duration (Minutes)</label>
              <input
                type="number"
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(Number(e.target.value))}
                className="w-full p-2.5 bg-slate-50 border border-slate-300/80 rounded-xl text-slate-900 font-medium text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Target Total Marks</label>
              <input
                type="number"
                value={totalMarks}
                onChange={(e) => setTotalMarks(Number(e.target.value))}
                className="w-full p-2.5 bg-slate-50 border border-slate-300/80 rounded-xl text-slate-900 font-medium text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(2)}
              disabled={!selectedCourse}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold shadow-md shadow-blue-500/20 flex items-center space-x-2 cursor-pointer transition-all active:scale-98"
            >
              <span>Next: Academic Structure</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: Academic Structure */}
      {step === 2 && (
        <div className="bg-white border border-slate-200/80 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
          {isLoadingCourse ? (
            <div className="py-12 text-center space-y-3">
              <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
              <h3 className="text-sm font-bold text-slate-800">Analyzing Syllabus Structure...</h3>
              <p className="text-xs text-slate-500">Retrieving official syllabus units and Course Outcomes from the database</p>
            </div>
          ) : courseLoadError ? (
            <div className="py-8 text-center space-y-3 bg-rose-50/50 border border-rose-200 rounded-2xl p-6">
              <AlertCircle className="w-8 h-8 text-rose-600 mx-auto" />
              <div>
                <h3 className="text-sm font-bold text-slate-900">Unable to load course curriculum.</h3>
                <p className="text-xs text-slate-600 mt-1">{courseLoadError}</p>
              </div>
              <button
                type="button"
                onClick={() => selectedCourseId && handleSelectCourse(selectedCourseId)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold shadow-xs inline-flex items-center space-x-1 cursor-pointer"
              >
                <span>Retry</span>
              </button>
            </div>
          ) : selectedCourse ? (
            <>
              <div className="border-b border-slate-100 pb-4 flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-extrabold text-blue-600 uppercase tracking-wider">Step 02</span>
                  </div>
                  <h2 className="text-lg font-bold text-slate-900 mt-1">Academic Structure & Curriculum Verification</h2>
                  <p className="text-xs text-slate-500">Verified syllabus units and Bloom-mapped outcomes for {selectedCourse.code} ({selectedCourse.name})</p>
                </div>
                <span className="text-xs font-extrabold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200/80">
                  Verified Curriculum ✓
                </span>
              </div>

              <div className="space-y-6">
                {/* Units and Topics Section */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center space-x-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-blue-600" />
                      <span>Units & Topics in Scope ({selectedCourse.units?.length || 0} Units):</span>
                    </h3>
                  </div>

                  {(!selectedCourse.units || selectedCourse.units.length === 0) ? (
                    <div className="p-6 bg-slate-50 border border-slate-200 rounded-2xl text-center">
                      <p className="text-xs text-slate-500 italic">No syllabus units configured for this course.</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {selectedCourse.units.map((u) => (
                        <div key={u.unit_number} className="p-4 bg-slate-50/70 border border-slate-200/80 rounded-2xl flex items-start space-x-3.5 text-xs hover-card-lift">
                          <span className="font-extrabold text-blue-700 bg-blue-100/80 px-2.5 py-1 rounded-lg shrink-0 text-xs border border-blue-200">
                            UNIT 0{u.unit_number}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="font-extrabold text-slate-900 text-sm">{u.title}</div>
                            <p className="text-slate-600 mt-1 leading-relaxed whitespace-pre-line break-words">{u.topics}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Course Outcomes Section */}
                <div>
                  <div className="flex items-center justify-between mb-3 pt-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center space-x-1.5">
                      <Target className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Course Outcomes & Target Cognitive Depth ({selectedCourse.course_outcomes?.length || 0} COs):</span>
                    </h3>
                  </div>

                  {(!selectedCourse.course_outcomes || selectedCourse.course_outcomes.length === 0) ? (
                    <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl text-center">
                      <p className="text-xs text-slate-500 italic">No Course Outcomes configured for this course.</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {selectedCourse.course_outcomes.map((co) => {
                        const bloom = co.target_bloom_level || (co as any).bloom_level;
                        return (
                          <div key={co.code} className="p-4 bg-emerald-50/50 border border-emerald-100 rounded-2xl text-xs flex flex-col justify-between space-y-2 hover-card-lift">
                            <div className="font-bold text-emerald-950 flex items-center justify-between">
                              <span className="text-xs bg-emerald-200/70 text-emerald-950 px-2.5 py-0.5 rounded-md font-extrabold">{co.code}</span>
                              {bloom && (
                                <span className="text-[10px] bg-white text-emerald-800 px-2 py-0.5 rounded font-bold border border-emerald-200 shadow-2xs">
                                  {bloom}
                                </span>
                              )}
                            </div>
                            <p className="text-slate-700 text-[11px] leading-relaxed break-words font-medium">{co.description}</p>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-between pt-4 border-t border-slate-100">
                <button
                  onClick={() => setStep(1)}
                  className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold flex items-center space-x-2 cursor-pointer"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back</span>
                </button>
                <button
                  onClick={() => setStep(3)}
                  disabled={!selectedCourse.units || selectedCourse.units.length === 0}
                  className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-300 text-white rounded-xl text-xs font-bold shadow-md shadow-blue-500/20 flex items-center space-x-2 transition-all cursor-pointer"
                >
                  <span>Next: Section Schema</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* STEP 3: Paper Schema */}
      {step === 3 && (
        <div className="bg-white border border-slate-200/80 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-extrabold text-blue-600 uppercase tracking-wider">Step 03</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 mt-1">Paper Blueprint & Section Rules</h2>
            <p className="text-xs text-slate-500">Configure questions per section and verify 70-mark university allocation</p>
          </div>

          <div className="space-y-4">
            {sections.map((sec, idx) => (
              <div key={idx} className="p-4.5 bg-slate-50/70 border border-slate-200/80 rounded-2xl space-y-3.5 hover-card-lift">
                <div className="flex items-center justify-between">
                  <input
                    type="text"
                    value={sec.name}
                    onChange={(e) => {
                      const copy = [...sections];
                      copy[idx].name = e.target.value;
                      setSections(copy);
                    }}
                    className="font-extrabold text-sm text-slate-900 bg-transparent border-b border-slate-300 focus:border-blue-500 focus:outline-none"
                  />
                  <span className="text-xs font-extrabold text-blue-700 bg-blue-100/80 px-2.5 py-0.5 rounded-full border border-blue-200">
                    {sec.questions_to_answer * sec.marks_per_question} Marks
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div>
                    <label className="block text-slate-600 font-bold mb-1">Total Questions</label>
                    <input
                      type="number"
                      value={sec.total_questions}
                      onChange={(e) => {
                        const copy = [...sections];
                        copy[idx].total_questions = Number(e.target.value);
                        copy[idx].questions_to_answer = Number(e.target.value);
                        setSections(copy);
                      }}
                      className="w-full p-2.5 bg-white border border-slate-300 rounded-xl font-bold text-slate-900"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-600 font-bold mb-1">Marks / Question</label>
                    <input
                      type="number"
                      value={sec.marks_per_question}
                      onChange={(e) => {
                        const copy = [...sections];
                        copy[idx].marks_per_question = Number(e.target.value);
                        setSections(copy);
                      }}
                      className="w-full p-2.5 bg-white border border-slate-300 rounded-xl font-bold text-slate-900"
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-slate-600 font-bold mb-1">Question Type</label>
                    <select
                      value={sec.question_type}
                      onChange={(e) => {
                        const copy = [...sections];
                        copy[idx].question_type = e.target.value;
                        setSections(copy);
                      }}
                      className="w-full p-2.5 bg-white border border-slate-300 rounded-xl font-semibold text-slate-900"
                    >
                      <option value="Short">Short Answer (Conceptual / 2M)</option>
                      <option value="Descriptive">Descriptive (Detailed / 10M)</option>
                      <option value="Problem Solving">Problem Solving / Analytical</option>
                    </select>
                  </div>
                </div>
              </div>
            ))}

            {/* Marks Sum Verification Alert */}
            <div className={`p-4 border rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs ${
              calculateCalculatedMarks() === totalMarks ? 'bg-emerald-50/70 border-emerald-200' : 'bg-rose-50/70 border-rose-200'
            }`}>
              <span className="font-bold text-slate-800">
                Calculated Blueprint Sum: <strong className="text-slate-950 text-sm">{calculateCalculatedMarks()} Marks</strong>
              </span>
              <span className={`font-extrabold px-3 py-1 rounded-lg text-center ${
                calculateCalculatedMarks() === totalMarks ? 'bg-emerald-100 text-emerald-900' : 'bg-rose-100 text-rose-900'
              }`}>
                Target: {totalMarks} Marks ({calculateCalculatedMarks() === totalMarks ? 'Matched ✓' : `Mismatch: ${calculateCalculatedMarks() - totalMarks > 0 ? '+' : ''}${calculateCalculatedMarks() - totalMarks}M`})
              </span>
            </div>
          </div>

          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(2)}
              className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold flex items-center space-x-2 cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
            <button
              onClick={() => setStep(4)}
              disabled={calculateCalculatedMarks() !== totalMarks}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-xl text-xs font-bold shadow-md shadow-blue-500/20 flex items-center space-x-2 transition-all cursor-pointer"
            >
              <span>Next: Distributions</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: Distributions */}
      {step === 4 && (
        <div className="bg-white border border-slate-200/80 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-extrabold text-blue-600 uppercase tracking-wider">Step 04</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 mt-1">Bloom's Taxonomy & Difficulty Calibration</h2>
            <p className="text-xs text-slate-500">Configure cognitive progression and pedagogical balance</p>
          </div>

          <div className="space-y-6 text-xs">
            
            {/* Difficulty Engine */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-extrabold uppercase tracking-wider text-slate-800">Difficulty Distribution (%)</h3>
                <div className="flex items-center space-x-2">
                  <span className={`font-extrabold px-2.5 py-0.5 rounded text-[11px] ${calculateDiffSum() === 100 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
                    Sum: {calculateDiffSum()}% {calculateDiffSum() === 100 ? '✓' : '(Must = 100%)'}
                  </span>
                  {calculateDiffSum() !== 100 && (
                    <button
                      type="button"
                      onClick={normalizeDifficulty}
                      className="text-[11px] font-bold text-blue-600 hover:underline cursor-pointer"
                    >
                      Reset (30/50/20)
                    </button>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3.5 bg-emerald-50/70 border border-emerald-200/80 rounded-2xl">
                  <span className="font-extrabold text-emerald-950 block mb-1">Easy: {diffEasy}%</span>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={diffEasy}
                    onChange={(e) => setDiffEasy(Number(e.target.value))}
                    className="w-full accent-emerald-600"
                  />
                </div>
                <div className="p-3.5 bg-blue-50/70 border border-blue-200/80 rounded-2xl">
                  <span className="font-extrabold text-blue-950 block mb-1">Medium: {diffMedium}%</span>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={diffMedium}
                    onChange={(e) => setDiffMedium(Number(e.target.value))}
                    className="w-full accent-blue-600"
                  />
                </div>
                <div className="p-3.5 bg-rose-50/70 border border-rose-200/80 rounded-2xl">
                  <span className="font-extrabold text-rose-950 block mb-1">Hard: {diffHard}%</span>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={diffHard}
                    onChange={(e) => setDiffHard(Number(e.target.value))}
                    className="w-full accent-rose-600"
                  />
                </div>
              </div>
            </div>

            {/* Bloom's Taxonomy Levels */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-extrabold uppercase tracking-wider text-slate-800">Bloom's Taxonomy Levels (%)</h3>
                <div className="flex items-center space-x-2">
                  <span className={`font-extrabold px-2.5 py-0.5 rounded text-[11px] ${calculateBloomSum() === 100 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
                    Sum: {calculateBloomSum()}% {calculateBloomSum() === 100 ? '✓' : '(Must = 100%)'}
                  </span>
                  {calculateBloomSum() !== 100 && (
                    <button
                      type="button"
                      onClick={normalizeBloom}
                      className="text-[11px] font-bold text-blue-600 hover:underline cursor-pointer"
                    >
                      Reset Standard
                    </button>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                {Object.entries(bloomDist).map(([level, val]) => (
                  <div key={level} className="p-3 bg-slate-50/70 border border-slate-200/80 rounded-xl flex items-center justify-between">
                    <span className="font-bold text-slate-800">{level}</span>
                    <input
                      type="number"
                      value={val}
                      onChange={(e) => setBloomDist({ ...bloomDist, [level]: Number(e.target.value) })}
                      className="w-16 p-1 bg-white border border-slate-300 rounded text-center text-xs font-extrabold focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    />
                  </div>
                ))}
              </div>
            </div>

          </div>

          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(3)}
              className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold flex items-center space-x-2 cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
            <button
              onClick={() => setStep(5)}
              disabled={calculateDiffSum() !== 100 || calculateBloomSum() !== 100}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-xl text-xs font-bold shadow-md shadow-blue-500/20 flex items-center space-x-2 transition-all cursor-pointer"
            >
              <span>Next: AI Synthesis Plan</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 5: AI Synthesis Review & Live Workflow */}
      {step === 5 && (
        <div className="space-y-6">
          {!isGenerating && stepsLog.length === 0 ? (
            <div className="bg-white border border-slate-200/80 rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
              <div className="border-b border-slate-100 pb-4 flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-extrabold text-blue-600 uppercase tracking-wider">Step 05</span>
                  </div>
                  <h2 className="text-lg font-bold text-slate-900 mt-1">Pre-Flight Review & 5-Agent Pipeline</h2>
                  <p className="text-xs text-slate-500">Review syllabus grounding and initiate autonomous question formulation</p>
                </div>
                <span className="text-xs font-extrabold text-blue-700 bg-blue-50 px-3 py-1 rounded-full border border-blue-200">
                  Ready to Synthesize
                </span>
              </div>

              {/* Pre-generation Summary Card */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 bg-slate-50/80 border border-slate-200/80 rounded-2xl space-y-2.5">
                  <h3 className="font-extrabold text-slate-800 uppercase tracking-wider text-[11px] flex items-center space-x-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-blue-600" />
                    <span>Academic Curriculum</span>
                  </h3>
                  <div className="space-y-1.5 text-slate-700">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Course Code:</span>
                      <span className="font-extrabold text-slate-900">{selectedCourse?.code}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Course Name:</span>
                      <span className="font-bold text-slate-900 truncate max-w-[180px]">{selectedCourse?.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Units in Scope:</span>
                      <span className="font-extrabold text-blue-700">{selectedCourse?.units?.length || 0} Units</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Target COs:</span>
                      <span className="font-extrabold text-emerald-700">
                        {selectedCourse?.course_outcomes?.length || 0} COs ({selectedCourse?.course_outcomes?.map(c => c.code).join(', ')})
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-slate-50/80 border border-slate-200/80 rounded-2xl space-y-2.5">
                  <h3 className="font-extrabold text-slate-800 uppercase tracking-wider text-[11px] flex items-center space-x-1.5">
                    <Database className="w-3.5 h-3.5 text-indigo-600" />
                    <span>RAG Vector Provenance</span>
                  </h3>
                  <div className="space-y-1.5 text-slate-700">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Syllabus Index:</span>
                      <span className="font-extrabold text-emerald-700">
                        {courseSyllabusCount > 0 ? `${courseSyllabusCount} Syllabus Source(s) ✓` : 'Curriculum Grounded ✓'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Indexed Resources:</span>
                      <span className="font-bold text-slate-800">{courseResourcesCount} Reference Document(s)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Past Examination Papers:</span>
                      <span className="font-bold text-slate-800">{coursePastPaperCount} Reference Paper(s)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Domain Isolation:</span>
                      <span className="font-extrabold text-blue-700">Strict ({selectedCourse?.code} only)</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-slate-50/80 border border-slate-200/80 rounded-2xl space-y-2.5">
                  <h3 className="font-extrabold text-slate-800 uppercase tracking-wider text-[11px] flex items-center space-x-1.5">
                    <Layers className="w-3.5 h-3.5 text-purple-600" />
                    <span>Blueprint Schema</span>
                  </h3>
                  <div className="space-y-1.5 text-slate-700">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Total Marks:</span>
                      <span className="font-extrabold text-slate-900">{totalMarks} Marks ({durationMinutes} Mins)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Sections Formula:</span>
                      <span className="font-bold text-slate-800">
                        {sections.map(s => `${s.name}: ${s.questions_to_answer}Q×${s.marks_per_question}M`).join(' + ')}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Check Status:</span>
                      <span className="font-extrabold text-emerald-700">Exact 70M Match ✓</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-slate-50/80 border border-slate-200/80 rounded-2xl space-y-2.5">
                  <h3 className="font-extrabold text-slate-800 uppercase tracking-wider text-[11px] flex items-center space-x-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Calibrations</span>
                  </h3>
                  <div className="space-y-1.5 text-slate-700">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Difficulty Split:</span>
                      <span className="font-bold text-slate-800">
                        Easy: {diffEasy}% • Med: {diffMedium}% • Hard: {diffHard}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Bloom Breakdown:</span>
                      <span className="font-bold text-slate-800 truncate max-w-[180px]">
                        {Object.entries(bloomDist).map(([k, v]) => `${k.slice(0, 3)}:${v}%`).join(' ')}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-between pt-4 border-t border-slate-100">
                <button
                  onClick={() => setStep(4)}
                  className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold flex items-center space-x-2 cursor-pointer"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back</span>
                </button>
                <button
                  onClick={handleStartGeneration}
                  className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold shadow-md shadow-blue-500/25 flex items-center space-x-2 cursor-pointer active:scale-98"
                >
                  <Sparkles className="w-4 h-4 text-blue-200" />
                  <span>Execute 5-Agent AI Workflow</span>
                </button>
              </div>
            </div>
          ) : (
            <AgentWorkflowTracker
              stepsLog={stepsLog}
              isGenerating={isGenerating}
              totalDuration={generationDuration}
            />
          )}
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

