from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class QuestionPaper(Base):
    __tablename__ = "question_papers"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=False)
    examination_name = Column(String(255), default="Semester End Examination")
    institution_name = Column(String(255), default="Department of Computer Science & Engineering")
    duration_minutes = Column(Integer, default=180)
    total_marks = Column(Integer, nullable=False)
    section_config = Column(JSON, nullable=True)  # Structure of sections (A, B, etc.)
    instructions = Column(Text, nullable=True)
    difficulty_distribution = Column(JSON, nullable=True)  # {"Easy": 30, "Medium": 50, "Hard": 20}
    bloom_distribution = Column(JSON, nullable=True)
    syllabus_coverage_score = Column(Float, default=0.0)
    status = Column(String(50), default="Generated")  # "Draft", "Generated", "Validated", "Approved"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    course = relationship("Course", back_populates="question_papers")
    questions = relationship("Question", back_populates="question_paper", cascade="all, delete-orphan", order_by="Question.question_number")
    generation_sessions = relationship("GenerationSession", back_populates="question_paper", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("question_papers.id"), nullable=False)
    section_name = Column(String(50), default="Section A")
    question_number = Column(Integer, nullable=False)
    sub_question_letter = Column(String(10), nullable=True)  # a, b, c, etc.
    question_text = Column(Text, nullable=False)
    marks = Column(Integer, nullable=False)
    unit_number = Column(Integer, nullable=False)
    bloom_level = Column(String(50), nullable=False)  # "Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"
    course_outcome = Column(String(50), nullable=False)  # "CO1", "CO2", etc.
    difficulty = Column(String(50), default="Medium")  # "Easy", "Medium", "Hard"
    question_type = Column(String(50), default="Descriptive")  # "Short", "Descriptive", "Problem Solving", "Case Study"
    
    # Explainability & RAG Source Provenance
    source_topics = Column(JSON, nullable=True)  # ["B-Trees", "Indexing"]
    source_documents = Column(JSON, nullable=True)  # [{"document_name": "...", "page": 45, "chunk_id": 12, "similarity_score": 0.89}]
    generation_reasoning = Column(Text, nullable=True)
    is_revised = Column(Boolean, default=False)
    revision_count = Column(Integer, default=0)

    question_paper = relationship("QuestionPaper", back_populates="questions")
    validation_results = relationship("ValidationResult", back_populates="question", cascade="all, delete-orphan")

class GenerationSession(Base):
    __tablename__ = "generation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("question_papers.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="InProgress")  # "InProgress", "Completed", "Failed"
    steps_log = Column(JSON, default=list)  # Audit log of each agent's execution step
    duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    question_paper = relationship("QuestionPaper", back_populates="generation_sessions")

class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    is_valid = Column(Boolean, default=True)
    syllabus_alignment_score = Column(Float, default=1.0)
    co_alignment_score = Column(Float, default=1.0)
    difficulty_match_score = Column(Float, default=1.0)
    bloom_alignment_score = Column(Float, default=1.0)
    is_duplicate = Column(Boolean, default=False)
    duplicate_similarity_score = Column(Float, default=0.0)
    feedback_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    question = relationship("Question", back_populates="validation_results")
