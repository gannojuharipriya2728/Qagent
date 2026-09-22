import React, { useState, useEffect } from 'react';
import { 
  Sparkles, ArrowRight, ArrowLeft, CheckCircle2, AlertCircle, Plus, Trash2, 
  BookOpen, Layers, Target, Database, LayoutTemplate, Check
} from 'lucide-react';
import { api, type Course, type GenerationRequest, type SectionRule, type AgentStepLog } from '../api/client';
import { AgentWorkflowTracker } from '../components/AgentWorkflowTracker';
import { CreateCourseModal } from '../components/CreateCourseModal';

interface GeneratePaperWizardProps {
  prefillCourseId?: number;
  onGenerationComplete: (paperId: number) => void;
}

interface ExamTemplate {
  name: string;
  type: string;
  duration: number;
  totalMarks: number;
  instructions: string;
  sections: SectionRule[];
}

const EXAM_TEMPLATES: ExamTemplate[] = [
  {
    name: 'Mid Examination / Mid-I (20 Marks)',
    type: 'Mid-I',
    duration: 60,
    totalMarks: 20,
    instructions: 'Answer any FOUR questions out of FIVE. All questions carry equal marks (5 Marks each).',
    sections: [
      {
        name: 'Section A',
        total_questions: 5,
        questions_to_answer: 4,
        marks_per_question: 5,
        question_type: 'Descriptive / Analytical',
        internal_choice: true,
        has_sub_questions: false,
        evaluated_marks: 20
      }
    ]
  },
  {
    name: 'End Semester University Examination (70 Marks)',
    type: 'Semester Examination',
    duration: 180,
    totalMarks: 70,
    instructions: 'Answer all questions in Section A. Answer any FIVE full questions from Section B.',
    sections: [
      {
        name: 'Section A (Compulsory)',
        total_questions: 10,
        questions_to_answer: 10,
        marks_per_question: 2,
        question_type: 'Short Answer (Conceptual)',
        internal_choice: false,
        has_sub_questions: false,
        evaluated_marks: 20
      },
      {
        name: 'Section B (Descriptive)',
        total_questions: 5,
        questions_to_answer: 5,
        marks_per_question: 10,
        question_type: 'Descriptive / Long Answer',
        internal_choice: true,
        has_sub_questions: true,
        sub_question_parts: [
          { part: 'a', marks: 5 },
          { part: 'b', marks: 5 }
        ],
        evaluated_marks: 50
      }
    ]
  },
  {
    name: 'Unit Test / Class Test (25 Marks)',
    type: 'Unit Test',
    duration: 45,
    totalMarks: 25,
    instructions: 'Answer all questions. Part A carries 5 marks and Part B carries 20 marks.',
    sections: [
      {
        name: 'Part A (Short Questions)',
        total_questions: 5,
        questions_to_answer: 5,
        marks_per_question: 1,
        question_type: 'Objective / Short',
        internal_choice: false,
        evaluated_marks: 5
      },
      {
        name: 'Part B (Descriptive)',
        total_questions: 5,
        questions_to_answer: 4,
        marks_per_question: 5,
        question_type: 'Descriptive',
        internal_choice: true,
        evaluated_marks: 20
      }
    ]
  },
  {
    name: 'Lab / Practical Examination (50 Marks)',
    type: 'Lab Examination',
    duration: 180,
    totalMarks: 50,
    instructions: 'Conduct the assigned practical experiment, write algorithm, execute program and attend viva.',
    sections: [
      {
        name: 'Write-up & Execution',
        total_questions: 1,
        questions_to_answer: 1,
        marks_per_question: 30,
        question_type: 'Practical / Coding',
        evaluated_marks: 30
      },
      {
        name: 'Viva Voce & Record',
        total_questions: 2,
        questions_to_answer: 2,
        marks_per_question: 10,
        question_type: 'Oral / Viva',
        evaluated_marks: 20
      }
    ]
  },
  {
    name: 'Quiz / Objective Assessment (20 Marks)',
    type: 'Quiz',
    duration: 30,
    totalMarks: 20,
    instructions: 'Answer all 20 objective questions. Each question carries 1 mark.',
    sections: [
      {
        name: 'Multiple Choice / Short Questions',
        total_questions: 20,
        questions_to_answer: 20,
        marks_per_question: 1,
        question_type: 'Multiple Choice / Short',
        evaluated_marks: 20
      }
    ]
  },
  {
    name: 'Custom Examination Pattern',
    type: 'Custom',
    duration: 90,
    totalMarks: 30,
    instructions: 'Answer the questions according to section specifications.',
    sections: [
      {
        name: 'Section 1',
        total_questions: 6,
        questions_to_answer: 5,
        marks_per_question: 6,
        question_type: 'Descriptive',
        internal_choice: true,
        evaluated_marks: 30
      }
    ]
  }
];

export const GeneratePaperWizard: React.FC<GeneratePaperWizardProps> = ({
  prefillCourseId,
  onGenerationComplete
}) => {
  const [step, setStep] = useState(1);
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(prefillCourseId || null);
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [showCourseModal, setShowCourseModal] = useState(false);

  const [examType, setExamType] = useState('Mid-I');
  const [customExamType, setCustomExamType] = useState('');
  const title = 'University Examination Paper';
  const [examName, setExamName] = useState('Mid Subjective Examination — 2026');
  const [institutionName, setInstitutionName] = useState('Department of Computer Science & Engineering');
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [instructions, setInstructions] = useState('Answer any FOUR questions out of FIVE.');

  // Sections (Dynamic Paper Pattern Builder)
  const [sections, setSections] = useState<SectionRule[]>([
    {
      name: 'Section A',
      total_questions: 5,
      questions_to_answer: 4,
      marks_per_question: 5,
      question_type: 'Descriptive / Analytical',
      internal_choice: true,
      has_sub_questions: false,
      sub_question_parts: [],
      evaluated_marks: 20
    }
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

  // Resource Stats
  const [courseResourcesCount, setCourseResourcesCount] = useState<number>(0);
  const [courseSyllabusCount, setCourseSyllabusCount] = useState<number>(0);
  const [coursePastPaperCount, setCoursePastPaperCount] = useState<number>(0);

  // Generation State
  const [isGenerating, setIsGenerating] = useState(false);
  const [stepsLog, setStepsLog] = useState<AgentStepLog[]>([]);
  const [generationDuration, setGenerationDuration] = useState<number | undefined>();
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = async () => {
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
    }
  };

  const fetchCourseDetails = async (courseId: number) => {
    setSelectedCourse(null);
    try {
      const fullRes = await api.get(`/courses/${courseId}`);
      setSelectedCourse(fullRes.data);
      if (fullRes.data.department) {
        setInstitutionName(`Department of ${fullRes.data.department}`);
      }
      await loadCourseResources(courseId);
    } catch (err) {
      console.error(`Failed to load course ${courseId}:`, err);
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

  const handleSelectCourse = async (courseId: number) => {
    setSelectedCourseId(courseId);
    await fetchCourseDetails(courseId);
  };

  const handleApplyTemplate = (tpl: ExamTemplate) => {
    setExamType(tpl.type);
    setDurationMinutes(tpl.duration);
    setInstructions(tpl.instructions);
    setExamName(`${tpl.name} — ${selectedCourse?.academic_year || '2026'}`);
    setSections(JSON.parse(JSON.stringify(tpl.sections)));
  };

  // Live Evaluated Total: Sum of (questions_to_answer * marks_per_question)
  const calculateCalculatedMarks = () => {
    return sections.reduce((acc, sec) => {
      const attempt = Number(sec.questions_to_answer || 0);
      const marks = Number(sec.marks_per_question || 0);
      return acc + (attempt * marks);
    }, 0);
  };

  const calculatedTotalMarks = calculateCalculatedMarks();

  const handleAddSection = () => {
    const newSecNum = sections.length + 1;
    const newSection: SectionRule = {
      name: `Section ${String.fromCharCode(64 + newSecNum)}`,
      total_questions: 5,
      questions_to_answer: 4,
      marks_per_question: 5,
      question_type: 'Descriptive / Analytical',
      internal_choice: true,
      has_sub_questions: false,
      sub_question_parts: [],
      evaluated_marks: 20
    };
    const updated = [...sections, newSection];
    setSections(updated);
  };

  const handleDeleteSection = (index: number) => {
    if (sections.length <= 1) {
      alert('Examination must have at least one section.');
      return;
    }
    const updated = sections.filter((_, idx) => idx !== index);
    setSections(updated);
  };

  const handleUpdateSection = (index: number, field: keyof SectionRule, value: any) => {
    const updated = [...sections];
    updated[index] = { ...updated[index], [field]: value };
    
    // Recalculate section evaluated marks
    if (field === 'questions_to_answer' || field === 'marks_per_question') {
      const attempt = Number(field === 'questions_to_answer' ? value : updated[index].questions_to_answer);
      const marks = Number(field === 'marks_per_question' ? value : updated[index].marks_per_question);
      updated[index].evaluated_marks = attempt * marks;
    }

    setSections(updated);
  };

  const handleToggleSubQuestions = (index: number, enabled: boolean) => {
    const updated = [...sections];
    updated[index].has_sub_questions = enabled;
    if (enabled && (!updated[index].sub_question_parts || updated[index].sub_question_parts?.length === 0)) {
      const totalM = updated[index].marks_per_question || 5;
      const partA = Math.ceil(totalM / 2);
      const partB = totalM - partA;
      updated[index].sub_question_parts = [
        { part: 'a', marks: partA },
        { part: 'b', marks: partB }
      ];
    }
    setSections(updated);
  };

  const handleSubPartChange = (secIdx: number, partIdx: number, marks: number) => {
    const updated = [...sections];
    if (updated[secIdx].sub_question_parts) {
      updated[secIdx].sub_question_parts![partIdx].marks = marks;
      setSections(updated);
    }
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

  const validatePattern = (): string | null => {
    for (let i = 0; i < sections.length; i++) {
      const sec = sections[i];
      if (sec.total_questions < sec.questions_to_answer) {
        return `${sec.name}: Questions provided (${sec.total_questions}) cannot be less than questions to attempt (${sec.questions_to_answer}).`;
      }
      if (sec.marks_per_question <= 0) {
        return `${sec.name}: Marks per question must be greater than 0.`;
      }
      if (sec.has_sub_questions && sec.sub_question_parts && sec.sub_question_parts.length > 0) {
        const subSum = sec.sub_question_parts.reduce((a, b) => a + Number(b.marks || 0), 0);
        if (subSum !== sec.marks_per_question) {
          return `${sec.name}: Sub-question parts sum (${subSum}M) does not equal question marks (${sec.marks_per_question}M).`;
        }
      }
    }
    if (calculatedTotalMarks <= 0) {
      return 'Grand total evaluated marks must be greater than 0.';
    }
    return null;
  };

  const handleStartGeneration = async () => {
    if (!selectedCourse) return;
    const validationError = validatePattern();
    if (validationError) {
      setErrorMsg(validationError);
      return;
    }

    setIsGenerating(true);
    setStepsLog([]);
    setErrorMsg('');

    const resolvedExamType = examType === 'Custom' && customExamType ? customExamType : examType;

    const payload: GenerationRequest = {
      course_id: selectedCourse.id,
      title: title || `${selectedCourse.name} Examination`,
      examination_name: examName,
      exam_type: resolvedExamType,
      institution_name: institutionName,
      duration_minutes: durationMinutes,
      total_marks: calculatedTotalMarks,
      instructions: instructions || `Answer the specified questions from each section. Total Marks: ${calculatedTotalMarks}.`,
      sections: sections.map(s => ({
        ...s,
        evaluated_marks: s.questions_to_answer * s.marks_per_question
      })),
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
    { num: 1, title: 'Course Workspace', desc: 'Select Course' },
    { num: 2, title: 'Exam Headers', desc: 'Pattern & Duration' },
    { num: 3, title: 'Pattern Builder', desc: 'Sections & Choices' },
    { num: 4, title: 'Distributions', desc: 'CO & Bloom' },
    { num: 5, title: 'AI Synthesis', desc: '5-Agent Pipeline' }
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      
      {/* Stepper Header */}
      <div className="bg-white border border-slate-200/80 rounded-3xl p-5 sm:p-6 shadow-sm">
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
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/30 ring-2 ring-indigo-500/20 scale-105'
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
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-2xl font-semibold flex items-center space-x-2.5 shadow-sm">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* STEP 1: Course Workspace Selection */}
      {step === 1 && (
        <div className="bg-white border border-slate-200/80 rounded-3xl p-6 sm:p-8 shadow-sm space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-extrabold text-indigo-600 uppercase tracking-wider">Step 01</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 mt-1">Course Workspace Selection</h2>
            <p className="text-xs text-slate-500">Choose the active academic course for question paper formulation</p>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-bold text-slate-800 uppercase tracking-wider">
                Select Academic Course
              </label>
              <button
                type="button"
                onClick={() => setShowCourseModal(true)}
                className="text-xs font-bold text-indigo-600 hover:text-indigo-700 flex items-center space-x-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>+ Create New Course</span>
              </button>
            </div>

            {courses.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {courses.map((c) => {
                  const isSelected = selectedCourseId === c.id;
                  return (
                    <div
                      key={c.id}
                      onClick={() => handleSelectCourse(c.id)}
                      className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                        isSelected 
                          ? 'bg-indigo-50/80 border-indigo-500 shadow-sm ring-2 ring-indigo-500/20' 
                          : 'bg-slate-50/60 border-slate-200/80 hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${isSelected ? 'bg-indigo-600 text-white' : 'bg-slate-200 text-slate-700'}`}>
                          {c.code}
                        </span>
                        <span className="text-[11px] text-slate-500 font-medium">Sem: {c.semester}</span>
                      </div>
                      <h4 className="font-bold text-slate-900 text-xs truncate mt-1">{c.name}</h4>
                      <p className="text-[11px] text-slate-500 mt-1">
                        {c.department ? `${c.department} • ` : ''}{c.units?.length || 0} Units • {c.course_outcomes?.length || 0} COs
                      </p>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
                <p className="text-sm text-slate-500 mb-2">No courses found.</p>
                <button
                  type="button"
                  onClick={() => setShowCourseModal(true)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold"
                >
                  Create Your First Course
                </button>
              </div>
            )}
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(2)}
              disabled={!selectedCourse}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-300 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-500/20 flex items-center space-x-2 cursor-pointer transition-all"
            >
              <span>Next: Examination Headers</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: Examination Type & Templates */}
      {step === 2 && (
        <div className="bg-white border border-slate-200/80 rounded-3xl p-6 sm:p-8 shadow-sm space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-extrabold text-indigo-600 uppercase tracking-wider">Step 02</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 mt-1">Examination Type & Pattern Presets</h2>
            <p className="text-xs text-slate-500">
              Select an examination type or pre-fill with an optional template (you can customize all sections and marks next)
            </p>
          </div>

          {/* Quick Preset Templates */}
          <div>
            <label className="block text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <LayoutTemplate className="w-3.5 h-3.5 text-indigo-600" />
              <span>Optional Exam Pattern Presets (Pre-fills configuration)</span>
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
              {EXAM_TEMPLATES.map((tpl, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleApplyTemplate(tpl)}
                  className="p-3 text-left rounded-xl border border-slate-200 hover:border-indigo-400 bg-slate-50/60 hover:bg-indigo-50/40 transition-all text-xs group"
                >
                  <span className="font-bold text-slate-800 group-hover:text-indigo-900 block truncate">{tpl.name}</span>
                  <span className="text-[10px] text-slate-500">{tpl.totalMarks} Marks • {tpl.duration} Mins</span>
                </button>
              ))}
            </div>
          </div>

          {/* Form Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs pt-2">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Examination Type</label>
              <select
                value={examType}
                onChange={(e) => setExamType(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-semibold text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              >
                <option value="Mid-I">Mid Examination / Mid-I</option>
                <option value="Mid-II">Mid-II Examination</option>
                <option value="Internal Examination">Internal Examination</option>
                <option value="Semester Examination">Semester / End Semester Examination</option>
                <option value="Unit Test">Unit Test / Class Test</option>
                <option value="Lab Examination">Lab / Practical Examination</option>
                <option value="Assignment">Assignment</option>
                <option value="Quiz">Quiz / Objective Test</option>
                <option value="Model Examination">Model Examination</option>
                <option value="Custom">Custom Examination Type</option>
              </select>
            </div>

            {examType === 'Custom' && (
              <div>
                <label className="block font-bold text-slate-700 mb-1">Custom Exam Type Name</label>
                <input
                  type="text"
                  placeholder="e.g., Remedial Assessment"
                  value={customExamType}
                  onChange={(e) => setCustomExamType(e.target.value)}
                  className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-medium text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>
            )}

            <div>
              <label className="block font-bold text-slate-700 mb-1">Examination Title Header</label>
              <input
                type="text"
                value={examName}
                onChange={(e) => setExamName(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-medium text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Institution / Department</label>
              <input
                type="text"
                value={institutionName}
                onChange={(e) => setInstitutionName(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-medium text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Duration (Minutes)</label>
              <input
                type="number"
                min="10"
                max="300"
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(Number(e.target.value))}
                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-medium text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block font-bold text-slate-700 mb-1">General Instructions</label>
              <input
                type="text"
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-medium text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold flex items-center space-x-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
            <button
              onClick={() => setStep(3)}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-500/20 flex items-center space-x-2"
            >
              <span>Next: Pattern Builder</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Dynamic Paper Pattern Builder */}
      {step === 3 && (
        <div className="bg-white border border-slate-200/80 rounded-3xl p-6 sm:p-8 shadow-sm space-y-6">
          <div className="border-b border-slate-100 pb-4 flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-extrabold text-indigo-600 uppercase tracking-wider">Step 03</span>
              </div>
              <h2 className="text-lg font-bold text-slate-900 mt-1">Dynamic Paper Pattern Builder</h2>
              <p className="text-xs text-slate-500">
                Define sections, questions provided, questions to attempt, marks per question, and sub-questions.
              </p>
            </div>
            <button
              type="button"
              onClick={handleAddSection}
              className="px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Section</span>
            </button>
          </div>

          <div className="space-y-5">
            {sections.map((sec, idx) => {
              const evaluatedSecMarks = Number(sec.questions_to_answer || 0) * Number(sec.marks_per_question || 0);
              return (
                <div key={idx} className="p-5 bg-slate-50/80 border border-slate-200/90 rounded-2xl space-y-4 shadow-2xs">
                  {/* Section Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold px-2 py-0.5 bg-indigo-600 text-white rounded">
                        #{idx + 1}
                      </span>
                      <input
                        type="text"
                        value={sec.name}
                        onChange={(e) => handleUpdateSection(idx, 'name', e.target.value)}
                        className="font-bold text-sm text-slate-900 bg-transparent border-b border-slate-300 focus:border-indigo-600 focus:outline-none"
                      />
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-bold px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full">
                        Evaluated: {sec.questions_to_answer} × {sec.marks_per_question}M = {evaluatedSecMarks} Marks
                      </span>
                      {sections.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleDeleteSection(idx)}
                          className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
                          title="Delete Section"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Section Grid Controls */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div>
                      <label className="block text-slate-600 font-bold mb-1">Questions Provided</label>
                      <input
                        type="number"
                        min="1"
                        value={sec.total_questions}
                        onChange={(e) => handleUpdateSection(idx, 'total_questions', Number(e.target.value))}
                        className="w-full p-2 bg-white border border-slate-300 rounded-xl font-bold text-slate-900 text-xs"
                      />
                    </div>

                    <div>
                      <label className="block text-slate-600 font-bold mb-1">Questions to Attempt</label>
                      <input
                        type="number"
                        min="1"
                        max={sec.total_questions}
                        value={sec.questions_to_answer}
                        onChange={(e) => handleUpdateSection(idx, 'questions_to_answer', Number(e.target.value))}
                        className="w-full p-2 bg-white border border-slate-300 rounded-xl font-bold text-slate-900 text-xs"
                      />
                    </div>

                    <div>
                      <label className="block text-slate-600 font-bold mb-1">Marks / Question</label>
                      <input
                        type="number"
                        min="1"
                        value={sec.marks_per_question}
                        onChange={(e) => handleUpdateSection(idx, 'marks_per_question', Number(e.target.value))}
                        className="w-full p-2 bg-white border border-slate-300 rounded-xl font-bold text-slate-900 text-xs"
                      />
                    </div>

                    <div>
                      <label className="block text-slate-600 font-bold mb-1">Question Type</label>
                      <select
                        value={sec.question_type}
                        onChange={(e) => handleUpdateSection(idx, 'question_type', e.target.value)}
                        className="w-full p-2 bg-white border border-slate-300 rounded-xl font-semibold text-slate-900 text-xs"
                      >
                        <option value="Short">Short Answer (Conceptual)</option>
                        <option value="Descriptive / Analytical">Descriptive / Analytical</option>
                        <option value="Problem Solving">Problem Solving / Mathematical</option>
                        <option value="Practical / Coding">Practical / Coding</option>
                      </select>
                    </div>
                  </div>

                  {/* Internal Choice & Sub-Questions Controls */}
                  <div className="pt-2 border-t border-slate-200/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                    <label className="inline-flex items-center gap-2 cursor-pointer font-medium text-slate-700">
                      <input
                        type="checkbox"
                        checked={sec.internal_choice || false}
                        onChange={(e) => handleUpdateSection(idx, 'internal_choice', e.target.checked)}
                        className="w-4 h-4 text-indigo-600 rounded border-slate-300"
                      />
                      <span>Internal Choice (e.g. Answer any {sec.questions_to_answer} of {sec.total_questions} or OR choices)</span>
                    </label>

                    <label className="inline-flex items-center gap-2 cursor-pointer font-medium text-slate-700">
                      <input
                        type="checkbox"
                        checked={sec.has_sub_questions || false}
                        onChange={(e) => handleToggleSubQuestions(idx, e.target.checked)}
                        className="w-4 h-4 text-indigo-600 rounded border-slate-300"
                      />
                      <span>Split into Sub-questions (a, b)</span>
                    </label>
                  </div>

                  {/* Sub-question Split Details */}
                  {sec.has_sub_questions && sec.sub_question_parts && (
                    <div className="bg-white p-3 rounded-xl border border-indigo-100 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold text-indigo-900 uppercase tracking-wider">
                          Sub-question Structure: Must sum to {sec.marks_per_question} Marks
                        </span>
                        <span className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                          sec.sub_question_parts.reduce((a, b) => a + Number(b.marks || 0), 0) === sec.marks_per_question
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}>
                          Sum: {sec.sub_question_parts.reduce((a, b) => a + Number(b.marks || 0), 0)} / {sec.marks_per_question}M
                        </span>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        {sec.sub_question_parts.map((p, pIdx) => (
                          <div key={pIdx} className="flex items-center gap-2 p-2 bg-slate-50 rounded-lg border border-slate-200">
                            <span className="font-bold text-xs text-slate-700">Part ({p.part}):</span>
                            <input
                              type="number"
                              min="1"
                              value={p.marks}
                              onChange={(e) => handleSubPartChange(idx, pIdx, Number(e.target.value))}
                              className="w-14 p-1 text-center bg-white border border-slate-300 rounded font-bold text-xs"
                            />
                            <span className="text-xs text-slate-500">Marks</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* Total Marks Live Evaluation Card */}
            <div className={`p-4 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs ${
              calculatedTotalMarks > 0 ? 'bg-emerald-50/70 border-emerald-200' : 'bg-rose-50/70 border-rose-200'
            }`}>
              <div className="space-y-0.5">
                <span className="font-bold text-slate-800 text-xs">
                  Grand Total Evaluated Marks: <strong className="text-slate-950 text-sm">{calculatedTotalMarks} Marks</strong>
                </span>
                <p className="text-[11px] text-slate-500">
                  Calculated automatically: Sum of (Questions to Attempt × Marks per Question)
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-bold px-3 py-1.5 rounded-xl bg-emerald-100 text-emerald-900 text-xs flex items-center gap-1.5">
                  <Check className="w-4 h-4 text-emerald-600" />
                  Blueprint Valid ({calculatedTotalMarks} Marks)
                </span>
              </div>
            </div>
          </div>

          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(2)}
              className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold flex items-center space-x-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
            <button
              onClick={() => {
                const err = validatePattern();
                if (err) {
                  setErrorMsg(err);
                } else {
                  setErrorMsg('');
                  setStep(4);
                }
              }}
              disabled={calculatedTotalMarks <= 0}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-300 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-500/20 flex items-center space-x-2"
            >
              <span>Next: Academic Distribution</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: Course Outcome & Bloom's Taxonomy Distribution */}
      {step === 4 && (
        <div className="bg-white border border-slate-200/80 rounded-3xl p-6 sm:p-8 shadow-sm space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-extrabold text-indigo-600 uppercase tracking-wider">Step 04</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 mt-1">Course Outcome & Cognitive Calibration</h2>
            <p className="text-xs text-slate-500">Configure Bloom's taxonomy depth and verify syllabus outcome coverage</p>
          </div>

          <div className="space-y-6 text-xs">
            {/* Target Course Outcomes Display */}
            <div className="space-y-3">
              <h3 className="font-extrabold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5 text-indigo-600" />
                <span>Target Course Outcomes in Scope ({selectedCourse?.course_outcomes?.length || 0} COs)</span>
              </h3>
              {selectedCourse?.course_outcomes && selectedCourse.course_outcomes.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {selectedCourse.course_outcomes.map((co) => (
                    <div key={co.code} className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-start gap-2.5">
                      <span className="font-bold text-xs bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded">
                        {co.code}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-[11px] text-slate-700 leading-snug">{co.description}</p>
                        <span className="text-[10px] text-slate-400 font-medium">Target: {co.target_bloom_level || 'Understand'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">No explicit COs defined; general outcomes will be mapped automatically.</p>
              )}
            </div>

            {/* Difficulty Calibration */}
            <div className="space-y-3 pt-2">
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
                      className="text-[11px] font-bold text-indigo-600 hover:underline cursor-pointer"
                    >
                      Reset Standard
                    </button>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 bg-emerald-50/70 border border-emerald-200/80 rounded-2xl">
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
                <div className="p-3 bg-blue-50/70 border border-blue-200/80 rounded-2xl">
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
                <div className="p-3 bg-rose-50/70 border border-rose-200/80 rounded-2xl">
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

            {/* Bloom's Taxonomy Cognitive Levels */}
            <div className="space-y-3 pt-2">
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
                      className="text-[11px] font-bold text-indigo-600 hover:underline cursor-pointer"
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
                      className="w-16 p-1 bg-white border border-slate-300 rounded text-center text-xs font-extrabold focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(3)}
              className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold flex items-center space-x-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
            <button
              onClick={() => setStep(5)}
              disabled={calculateDiffSum() !== 100 || calculateBloomSum() !== 100}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-300 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-500/20 flex items-center space-x-2"
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
            <div className="bg-white border border-slate-200/80 rounded-3xl p-6 sm:p-8 shadow-sm space-y-6">
              <div className="border-b border-slate-100 pb-4 flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-extrabold text-indigo-600 uppercase tracking-wider">Step 05</span>
                  </div>
                  <h2 className="text-lg font-bold text-slate-900 mt-1">Pre-Flight Review & 5-Agent Pipeline</h2>
                  <p className="text-xs text-slate-500">Review syllabus grounding and initiate autonomous question formulation</p>
                </div>
                <span className="text-xs font-extrabold text-indigo-700 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-200">
                  Ready to Synthesize
                </span>
              </div>

              {/* Pre-generation Summary Card */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 bg-slate-50/80 border border-slate-200/80 rounded-2xl space-y-2.5">
                  <h3 className="font-extrabold text-slate-800 uppercase tracking-wider text-[11px] flex items-center space-x-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
                    <span>Academic Course</span>
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
                      <span className="font-extrabold text-indigo-700">{selectedCourse?.units?.length || 0} Units</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Exam Type:</span>
                      <span className="font-extrabold text-indigo-700">{examType}</span>
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
                      <span className="text-slate-500">Syllabus Grounding:</span>
                      <span className="font-extrabold text-emerald-700">
                        {courseSyllabusCount > 0 ? `${courseSyllabusCount} Syllabus Source(s) ✓` : 'Curriculum Grounded ✓'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Indexed Resources:</span>
                      <span className="font-bold text-slate-800">{courseResourcesCount} Reference Document(s)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Past Question Papers:</span>
                      <span className="font-bold text-slate-800">{coursePastPaperCount} Reference Paper(s)</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-slate-50/80 border border-slate-200/80 rounded-2xl space-y-2.5 md:col-span-2">
                  <h3 className="font-extrabold text-slate-800 uppercase tracking-wider text-[11px] flex items-center space-x-1.5">
                    <Layers className="w-3.5 h-3.5 text-purple-600" />
                    <span>Blueprint Schema & Evaluated Total</span>
                  </h3>
                  <div className="space-y-1.5 text-slate-700">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Grand Total Evaluated:</span>
                      <span className="font-extrabold text-slate-900">{calculatedTotalMarks} Marks ({durationMinutes} Minutes)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Section Breakdown:</span>
                      <span className="font-bold text-slate-800">
                        {sections.map(s => `${s.name}: ${s.questions_to_answer}Q × ${s.marks_per_question}M = ${s.questions_to_answer * s.marks_per_question}M`).join(' + ')}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-between pt-4 border-t border-slate-100">
                <button
                  onClick={() => setStep(4)}
                  className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold flex items-center space-x-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back</span>
                </button>
                <button
                  onClick={handleStartGeneration}
                  className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-500/25 flex items-center space-x-2 active:scale-98"
                >
                  <Sparkles className="w-4 h-4 text-indigo-200" />
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
        onCourseCreated={(c) => {
          loadCourses();
          setSelectedCourseId(c.id);
          fetchCourseDetails(c.id);
        }}
        existingCourses={courses}
      />

    </div>
  );
};
