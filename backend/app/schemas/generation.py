from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class SubQuestionPart(BaseModel):
    part: str = "a"
    marks: int = 5

class SectionRule(BaseModel):
    name: str = "Section A"
    total_questions: int = 5
    questions_to_answer: int = 4
    marks_per_question: int = 5
    question_type: str = "Descriptive"  # "Short", "Descriptive", "Analytical", "Problem Solving", "Case Study"
    internal_choice: bool = False
    has_sub_questions: bool = False
    sub_question_parts: Optional[List[SubQuestionPart]] = None
    unit_distribution: Optional[List[int]] = None  # Specific units to target e.g. [1, 2, 3, 4, 5]
    bloom_levels: Optional[List[str]] = None

    @property
    def evaluated_marks(self) -> int:
        return self.questions_to_answer * self.marks_per_question

class GenerationRequest(BaseModel):
    course_id: int
    exam_type: str = "Semester Examination"  # "Mid-I", "Mid-II", "Internal Examination", "Semester Examination", "Unit Test", "Lab Examination", "Quiz", "Custom"
    title: str = "Semester Examination"
    examination_name: str = "University Regular Examination"
    institution_name: str = "Department of Computer Science & Engineering"
    academic_year: Optional[str] = "2026-2027"
    semester: Optional[str] = "Semester VII"
    duration_minutes: int = 180
    total_marks: int = 70
    instructions: Optional[str] = None
    
    # Sections breakdown
    sections: List[SectionRule] = Field(default_factory=lambda: [
        SectionRule(name="Section A", total_questions=5, questions_to_answer=4, marks_per_question=5, question_type="Descriptive")
    ])
    
    # Target Distributions (Percentages or Marks)
    difficulty_distribution: Dict[str, float] = Field(default_factory=lambda: {"Easy": 30.0, "Medium": 50.0, "Hard": 20.0})
    bloom_distribution: Dict[str, float] = Field(default_factory=lambda: {
        "Remember": 20.0,
        "Understand": 30.0,
        "Apply": 25.0,
        "Analyze": 15.0,
        "Evaluate": 5.0,
        "Create": 5.0
    })
    co_distribution: Optional[Dict[str, float]] = None
    unit_weights: Optional[Dict[int, float]] = None
    target_course_outcomes: Optional[List[str]] = None
    
    # RAG Settings
    similarity_threshold: float = 0.82
    top_k_sources: int = 5

class AgentStepLog(BaseModel):
    step_name: str
    agent_name: str
    status: str  # "started", "completed", "failed", "retrying"
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str

class GenerationSessionResponse(BaseModel):
    session_id: int
    paper_id: Optional[int] = None
    status: str
    duration_seconds: float
    steps_log: List[Dict[str, Any]]
