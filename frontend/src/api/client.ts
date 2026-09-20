import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('academic_auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Type Definitions
export interface User {
  id: number;
  email: string;
  full_name: string;
  department: string;
  role: string;
  is_active: boolean;
}

export interface Unit {
  id?: number;
  unit_number: number;
  title: string;
  topics: string;
}

export interface CourseOutcome {
  id?: number;
  code: string;
  description: string;
  target_bloom_level: string;
}

export interface UnitCreate {
  unit_number: number;
  title: string;
  topics: string;
}

export interface CourseOutcomeCreate {
  code: string;
  description: string;
  target_bloom_level?: string;
}

export interface CourseCreate {
  code: string;
  name: string;
  department?: string;
  semester?: string;
  academic_year?: string;
  description?: string;
  units?: UnitCreate[];
  course_outcomes?: CourseOutcomeCreate[];
}

export interface Course {
  id: number;
  code: string;
  name: string;
  department: string;
  semester: string;
  academic_year: string;
  description?: string;
  units: Unit[];
  course_outcomes: CourseOutcome[];
}

export interface ResourceChunk {
  id: number;
  chunk_index: number;
  content: string;
  page_number?: number;
  unit_number?: number;
  topic?: string;
  token_count: number;
}

export interface Resource {
  id: number;
  course_id: number;
  title: string;
  file_name: string;
  file_type: string;
  document_type: string;
  unit_number?: number;
  file_size_bytes: number;
  status: string;
  chunk_count: number;
  error_message?: string;
  created_at?: string;
  chunks?: ResourceChunk[];
}

export interface SectionRule {
  name: string;
  total_questions: number;
  questions_to_answer: number;
  marks_per_question: number;
  question_type: string;
  unit_distribution?: number[];
  bloom_levels?: string[];
}

export interface GenerationRequest {
  course_id: number;
  title: string;
  examination_name: string;
  institution_name: string;
  duration_minutes: number;
  total_marks: number;
  instructions?: string;
  sections: SectionRule[];
  difficulty_distribution: Record<string, number>;
  bloom_distribution: Record<string, number>;
  target_course_outcomes?: string[];
  similarity_threshold?: number;
  top_k_sources?: number;
}

export interface SourceDocument {
  document_name: string;
  document_type: string;
  page: number;
  topic: string;
  similarity_score: number;
  chunk_id: string;
}

export interface QuestionValidation {
  is_valid: boolean;
  syllabus_alignment_score: number;
  co_alignment_score: number;
  difficulty_match_score: number;
  bloom_alignment_score: number;
  is_duplicate: boolean;
  duplicate_similarity_score: number;
  feedback_notes?: string;
}

export interface Question {
  id: number;
  section_name: string;
  question_number: number;
  sub_question_letter?: string;
  question_text: string;
  marks: number;
  unit_number: number;
  bloom_level: string;
  course_outcome: string;
  difficulty: string;
  question_type: string;
  source_topics: string[];
  source_documents: SourceDocument[];
  generation_reasoning?: string;
  is_revised: boolean;
  revision_count: number;
  validation?: QuestionValidation;
}

export interface QuestionPaper {
  id: number;
  course_id: number;
  course_code?: string;
  course_name?: string;
  title: string;
  examination_name: string;
  institution_name: string;
  duration_minutes: number;
  total_marks: number;
  instructions?: string;
  difficulty_distribution?: Record<string, any>;
  bloom_distribution?: Record<string, any>;
  syllabus_coverage_score: number;
  status: string;
  created_at?: string;
  questions: Question[];
}

export interface AgentStepLog {
  step_name: string;
  agent_name: string;
  status: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

export interface GenerationResponse {
  session_id: number;
  paper_id: number;
  status: string;
  duration_seconds: number;
  steps_log: AgentStepLog[];
}

export interface PaperAnalytics {
  total_questions: number;
  total_marks_calculated: number;
  marks_sum_valid: boolean;
  unit_coverage: Record<string, number>;
  overall_syllabus_coverage: number;
  bloom_distribution_actual: Record<string, number>;
  bloom_distribution_target: Record<string, number>;
  difficulty_distribution_actual: Record<string, number>;
  difficulty_distribution_target: Record<string, number>;
  co_distribution: Record<string, number>;
}
