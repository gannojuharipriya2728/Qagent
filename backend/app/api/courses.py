from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.academic import Course, Unit, CourseOutcome
from backend.app.schemas.academic import (
    CourseCreate, CourseResponse, UnitCreate, UnitResponse, CourseOutcomeCreate, CourseOutcomeResponse
)
from backend.app.api.deps import get_current_user, get_current_user_optional
from backend.app.models.user import User

router = APIRouter(prefix="/courses", tags=["Academic Courses"])

@router.get("", response_model=List[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db)):
    stmt = select(Course).options(
        selectinload(Course.units),
        selectinload(Course.course_outcomes)
    ).order_by(Course.code)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=CourseResponse)
async def create_course(
    course_in: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    stmt = select(Course).where(Course.code == course_in.code)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course with code '{course_in.code}' already exists."
        )

    course = Course(
        code=course_in.code,
        name=course_in.name,
        department=course_in.department,
        semester=course_in.semester,
        academic_year=course_in.academic_year,
        description=course_in.description
    )
    db.add(course)
    await db.flush()

    for u in course_in.units:
        unit = Unit(
            course_id=course.id,
            unit_number=u.unit_number,
            title=u.title,
            topics=u.topics
        )
        db.add(unit)

    for co in course_in.course_outcomes:
        co_item = CourseOutcome(
            course_id=course.id,
            code=co.code,
            description=co.description,
            target_bloom_level=co.target_bloom_level
        )
        db.add(co_item)

    await db.commit()
    
    # Reload with relationships
    stmt_reload = select(Course).options(
        selectinload(Course.units),
        selectinload(Course.course_outcomes)
    ).where(Course.id == course.id)
    return (await db.execute(stmt_reload)).scalar_one()

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Course).options(
        selectinload(Course.units),
        selectinload(Course.course_outcomes)
    ).where(Course.id == course_id)
    course = (await db.execute(stmt)).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    return course

@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Course).where(Course.id == course_id)
    course = (await db.execute(stmt)).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    
    from backend.app.services.rag.vector_store import vector_store
    vector_store.delete_by_course_id(course_id)

    await db.delete(course)
    await db.commit()
    return {"message": f"Course '{course.name}' deleted successfully."}
