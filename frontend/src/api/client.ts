import axios from 'axios';
 
const envApiUrl = import.meta.env.VITE_API_BASE_URL;
const RAW_API_URL = typeof envApiUrl === 'string' && envApiUrl.trim() !== ''
  ? envApiUrl.trim()
  : (import.meta.env.DEV ? 'http://localhost:8000' : '');

export const API_BASE_URL = RAW_API_URL.endsWith('/api')
  ? RAW_API_URL
  : (RAW_API_URL ? `${RAW_API_URL.replace(/\/$/, '')}/api` : '/api');

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const AUTH_TOKEN_KEY = 'academic_auth_token';

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/** Endpoints whose 401 means "those credentials are wrong", not "your session ended". */
const CREDENTIAL_ENDPOINTS = ['/auth/login', '/auth/register'];

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const url: string = error?.config?.url ?? '';
    const isCredentialCheck = CREDENTIAL_ENDPOINTS.some((path) => url.startsWith(path));

    // An expired or revoked token otherwise leaves the UI stuck on screens that
    // silently fail every request. Drop it and return to the signed-out state.
    if (status === 401 && !isCredentialCheck && localStorage.getItem(AUTH_TOKEN_KEY)) {
      localStorage.removeItem(AUTH_TOKEN_KEY);
      window.dispatchEvent(new CustomEvent('qagent:session-expired'));
    }
    return Promise.reject(error);
  },
);

/**
 * Reads the role claim out of the stored JWT.
 *
 * For deciding what to render only — every privileged route is enforced again
 * on the server, which is the check that actually matters.
 */
export function getStoredUserRole(): string | null {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (!token) return null;
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const claims = JSON.parse(atob(normalized));
    return typeof claims.role === 'string' ? claims.role : null;
  } catch {
    return null;
  }
}

// Type Definitions
export interface User {
  id: number;
  email: string;
  full_name: string;
  department: string;
  semester?: string;
  role: string;
  is_active: boolean;
}

export interface FacultyProfile {
  id: number;
  email: string;
  full_name: string;
  department: string;
  semester?: string;
  role: string;
  faculty_id?: string;
  courses_assigned: {
    id: number;
    code: string;
    name: string;
    semester: string;
    academic_year: string;
  }[];
}

export interface FacultyProfileUpdate {
  full_name?: string;
  department?: string;
  semester?: string;
}

export type Subject = Course;

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

export interface CourseUpdate {
  code?: string;
  name?: string;
  department?: string;
  semester?: string;
  academic_year?: string;
  description?: string;
}

export interface Course {
  id: number;
  code: string;
  name: string;
  department: string;
  semester: string;
  academic_year: string;
  description?: string;
  faculty_id?: number;
  analysis_status?: string;
  analysis_data?: any;
  units: Unit[];
  course_outcomes: CourseOutcome[];
}

export interface CourseAnalysisResponse {
  course_id: number;
  course_code: string;
  course_name: string;
  department: string;
  semester: string;
  academic_year: string;
  analysis_status: string;
  units: {
    unit_number: number;
    title: string;
    topics: string;
    key_concepts?: string[];
    source_documents?: string[];
  }[];
  course_outcomes: {
    code: string;
    description: string;
    target_bloom_level: string;
    source_confidence?: string;
  }[];
  bloom_recommendations: {
    level: string;
    recommended_percentage: number;
  }[];
  topic_unit_mapping?: Record<string, string[]>;
  co_unit_mapping?: Record<string, number[]>;
}

export interface CourseAnalysisApprovalRequest {
  units: {
    unit_number: number;
    title: string;
    topics: string;
  }[];
  course_outcomes: {
    code: string;
    description: string;
    target_bloom_level?: string;
  }[];
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

export interface SubQuestionPart {
  part: string;
  marks: number;
}

export interface SectionRule {
  name: string;
  total_questions: number;
  questions_to_answer: number;
  marks_per_question: number;
  question_type: string;
  internal_choice?: boolean;
  has_sub_questions?: boolean;
  sub_question_parts?: SubQuestionPart[];
  evaluated_marks?: number;
  unit_distribution?: number[];
  bloom_levels?: string[];
}

export interface GenerationRequest {
  course_id: number;
  title: string;
  examination_name: string;
  exam_type?: string;
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
  sub_questions?: { part: string; question_text: string; marks: number }[];
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
  exam_type?: string;
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
