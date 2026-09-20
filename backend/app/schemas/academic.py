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

class CourseCreate(CourseBase):
    units: Optional[List[UnitCreate]] = []
    course_outcomes: Optional[List[CourseOutcomeCreate]] = []

class CourseResponse(CourseBase):
    id: int
    created_at: Optional[datetime] = None
    units: List[UnitResponse] = []
    course_outcomes: List[CourseOutcomeResponse] = []

    class Config:
        from_attributes = True
