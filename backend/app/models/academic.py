from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    department = Column(String(100), default="Computer Science & Engineering")
    semester = Column(String(50), default="Semester V")
    academic_year = Column(String(50), default="2025-2026")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    units = relationship("Unit", back_populates="course", cascade="all, delete-orphan")
    course_outcomes = relationship("CourseOutcome", back_populates="course", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="course", cascade="all, delete-orphan")
    question_papers = relationship("QuestionPaper", back_populates="course", cascade="all, delete-orphan")

class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    unit_number = Column(Integer, nullable=False)  # 1, 2, 3, 4, 5
    title = Column(String(255), nullable=False)
    topics = Column(Text, nullable=False)  # comma or newline separated syllabus topics

    course = relationship("Course", back_populates="units")

class CourseOutcome(Base):
    __tablename__ = "course_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    code = Column(String(20), nullable=False)  # CO1, CO2, CO3...
    description = Column(Text, nullable=False)
    target_bloom_level = Column(String(50), default="Apply")

    course = relationship("Course", back_populates="course_outcomes")
