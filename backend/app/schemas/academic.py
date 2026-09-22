from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UnitBase(BaseModel):
    unit_number: int
    title: str
    topics: str

class UnitCreate(UnitBase):
    pass

class UnitResponse(UnitBase):
    id: int
    course_id: int

    class Config:
        from_attributes = True

class CourseOutcomeBase(BaseModel):
    code: str
    description: str
    target_bloom_level: Optional[str] = "Apply"

class CourseOutcomeCreate(CourseOutcomeBase):
    pass

class CourseOutcomeResponse(CourseOutcomeBase):
    id: int
    course_id: int

    class Config:
        from_attributes = True

class CourseBase(BaseModel):
    code: str
    name: str
    department: Optional[str] = "Computer Science & Engineering"
    semester: Optional[str] = "Semester V"
    academic_year: Optional[str] = "2025-2026"
    description: Optional[str] = None
    faculty_id: Optional[int] = None
    analysis_status: Optional[str] = "Pending"

class CourseCreate(CourseBase):
    units: Optional[List[UnitCreate]] = []
    course_outcomes: Optional[List[CourseOutcomeCreate]] = []

class CourseUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[str] = None
    academic_year: Optional[str] = None
    description: Optional[str] = None
    faculty_id: Optional[int] = None
    analysis_status: Optional[str] = None

class CourseResponse(CourseBase):
    id: int
    analysis_status: str = "Pending"
    analysis_data: Optional[dict] = None
    created_at: Optional[datetime] = None
    units: List[UnitResponse] = []
    course_outcomes: List[CourseOutcomeResponse] = []

    class Config:
        from_attributes = True

class CourseAnalysisResponse(BaseModel):
    course_id: int
    code: str
    title: str
    department: str
    semester: str
    academic_year: str
    units: List[dict]
    course_outcomes: List[dict]
    bloom_distribution_detected: dict
    topic_unit_mapping: List[dict]
    co_unit_mapping: List[dict]
    source_documents: List[str]
    status: str

class CourseAnalysisApprovalRequest(BaseModel):
    units: List[UnitCreate]
    course_outcomes: List[CourseOutcomeCreate]
    auto_approve: bool = True

class FacultyProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str
    department: str
    role: str
    assigned_courses: List[CourseResponse] = []

class FacultyProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
