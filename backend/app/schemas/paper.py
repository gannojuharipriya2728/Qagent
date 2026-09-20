from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class QuestionValidationSchema(BaseModel):
    is_valid: bool
    syllabus_alignment_score: float
    co_alignment_score: float
    difficulty_match_score: float
    bloom_alignment_score: float
    is_duplicate: bool
    duplicate_similarity_score: float
    feedback_notes: Optional[str] = None

class QuestionSchema(BaseModel):
    id: Optional[int] = None
    section_name: str
    question_number: int
    sub_question_letter: Optional[str] = None
    question_text: str
    marks: int
    unit_number: int
    bloom_level: str
    course_outcome: str
    difficulty: str
    question_type: str
    source_topics: Optional[List[str]] = []
    source_documents: Optional[List[Dict[str, Any]]] = []
    generation_reasoning: Optional[str] = None
    is_revised: bool = False
    revision_count: int = 0
    validation: Optional[QuestionValidationSchema] = None

    class Config:
        from_attributes = True

class QuestionUpdateRequest(BaseModel):
    question_text: Optional[str] = None
    marks: Optional[int] = None
    bloom_level: Optional[str] = None
    course_outcome: Optional[str] = None
    difficulty: Optional[str] = None

class QuestionRegenerateRequest(BaseModel):
    additional_instructions: Optional[str] = None
    preferred_bloom_level: Optional[str] = None
    preferred_difficulty: Optional[str] = None

class QuestionPaperResponse(BaseModel):
    id: int
    course_id: int
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    title: str
    examination_name: str
    institution_name: str
    duration_minutes: int
    total_marks: int
    instructions: Optional[str] = None
    difficulty_distribution: Optional[Dict[str, Any]] = None
    bloom_distribution: Optional[Dict[str, Any]] = None
    syllabus_coverage_score: float
    status: str
    created_at: Optional[datetime] = None
    questions: List[QuestionSchema] = []

    class Config:
        from_attributes = True

class PaperAnalyticsResponse(BaseModel):
    total_questions: int
    total_marks_calculated: int
    marks_sum_valid: bool
    unit_coverage: Dict[int, float]
    overall_syllabus_coverage: float
    bloom_distribution_actual: Dict[str, float]
    bloom_distribution_target: Dict[str, float]
    difficulty_distribution_actual: Dict[str, float]
    difficulty_distribution_target: Dict[str, float]
    co_distribution: Dict[str, int]
