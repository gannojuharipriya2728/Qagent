from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class SectionRule(BaseModel):
    name: str = "Section A"
    total_questions: int = 10
    questions_to_answer: int = 10
    marks_per_question: int = 2
    question_type: str = "Short"  # "Short", "Descriptive", "Problem Solving"
    unit_distribution: Optional[List[int]] = None  # Specific units to target e.g. [1, 2, 3, 4, 5]
    bloom_levels: Optional[List[str]] = None

class GenerationRequest(BaseModel):
    course_id: int
    title: str = "End Semester Examination"
    examination_name: str = "University Regular Examination"
    institution_name: str = "Department of Computer Science & Engineering"
    duration_minutes: int = 180
    total_marks: int = 70
    instructions: Optional[str] = "Answer all questions in Section A and five full questions from Section B."
    
    # Sections breakdown
    sections: List[SectionRule] = [
        SectionRule(name="Section A", total_questions=10, questions_to_answer=10, marks_per_question=2, question_type="Short"),
        SectionRule(name="Section B", total_questions=5, questions_to_answer=5, marks_per_question=10, question_type="Descriptive")
    ]
    
    # Target Distributions (Percentages)
    difficulty_distribution: Dict[str, float] = {"Easy": 30.0, "Medium": 50.0, "Hard": 20.0}
    bloom_distribution: Dict[str, float] = {
        "Remember": 20.0,
        "Understand": 30.0,
        "Apply": 25.0,
        "Analyze": 15.0,
        "Evaluate": 5.0,
        "Create": 5.0
    }
    unit_weights: Optional[Dict[int, float]] = None  # {1: 20.0, 2: 20.0, 3: 20.0, 4: 20.0, 5: 20.0}
    target_course_outcomes: Optional[List[str]] = ["CO1", "CO2", "CO3", "CO4", "CO5"]
    
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
