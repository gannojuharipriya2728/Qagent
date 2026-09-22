import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, TokenResponse, UserResponse
from app.schemas.academic import FacultyProfileResponse, FacultyProfileUpdate, CourseResponse
from app.api.deps import get_current_user

logger = logging.getLogger("qagent.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])
faculty_router = APIRouter(prefix="/faculty", tags=["Faculty"])

@router.post("/register", response_model=TokenResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    logger.info("REGISTER_ROUTE_ENTERED")
    try:
        logger.info("REGISTER_SCHEMA_VALIDATED")
        logger.info("REGISTER_DB_SESSION_AVAILABLE")
        
        stmt = select(User).where(User.email == user_in.email)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        logger.info("REGISTER_USER_LOOKUP_COMPLETE")
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address is already registered."
            )

        hashed_pwd = get_password_hash(user_in.password)
        logger.info("REGISTER_PASSWORD_HASH_COMPLETE")

        user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            department=user_in.department,
            semester=user_in.semester or "Semester V",
            role=user_in.role or "faculty",
            hashed_password=hashed_pwd,
            is_active=True
        )
        db.add(user)
        logger.info("REGISTER_USER_CREATED")
        
        await db.commit()
        logger.info("REGISTER_COMMIT_COMPLETE")
        await db.refresh(user)

        token = create_access_token(subject=user.id, role=user.role)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("REGISTER_FAILED")
        await db.rollback()
        raise

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == credentials.email)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user account is currently deactivated."
        )

    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

@router.get("/faculty/profile", response_model=FacultyProfileResponse)
@faculty_router.get("/profile", response_model=FacultyProfileResponse)
async def get_faculty_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.info("FACULTY_PROFILE_ENTERED")
    logger.info("AUTH_USER_RESOLVED")
    logger.info("AUTH_USER_ID", extra={"user_id": current_user.id})
    logger.info("AUTH_USER_EMAIL", extra={"user_email": current_user.email})
    
    try:
        logger.info("FACULTY_PROFILE_QUERY_START")
        from app.models.academic import Course
        from sqlalchemy.orm import selectinload
        from sqlalchemy import or_

        conditions = [Course.faculty_id == current_user.id]
        if current_user.department and current_user.department.strip():
            conditions.append(Course.department == current_user.department.strip())

        stmt = select(Course).options(
            selectinload(Course.units),
            selectinload(Course.course_outcomes)
        ).where(or_(*conditions)).order_by(Course.code)
        
        result = await db.execute(stmt)
        courses = result.scalars().unique().all()
        logger.info("FACULTY_PROFILE_QUERY_COMPLETE", extra={"courses_count": len(courses)})

        logger.info("FACULTY_PROFILE_RESPONSE_BUILD_START")
        validated_courses = []
        for c in courses:
            try:
                validated_courses.append(CourseResponse.model_validate(c))
            except Exception as val_err:
                logger.warning(f"Error validating course {getattr(c, 'code', 'unknown')}: {val_err}")
                validated_courses.append(CourseResponse(
                    id=c.id,
                    code=c.code or "UNKNOWN",
                    name=c.name or "Course",
                    department=c.department or current_user.department or "Computer Science & Engineering",
                    semester=c.semester or "Semester V",
                    academic_year=c.academic_year or "2025-2026",
                    description=c.description,
                    faculty_id=c.faculty_id,
                    analysis_status=c.analysis_status or "Pending",
                    units=[],
                    course_outcomes=[]
                ))

        response = FacultyProfileResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name or "Faculty Member",
            department=current_user.department or "Computer Science & Engineering",
            semester=getattr(current_user, "semester", "Semester V") or "Semester V",
            role=current_user.role or "Faculty",
            faculty_id=f"FAC-{current_user.id:04d}",
            assigned_courses=validated_courses,
            courses_assigned=validated_courses
        )
        logger.info("FACULTY_PROFILE_RESPONSE_BUILD_COMPLETE")
        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("FACULTY_PROFILE_FAILED")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load faculty profile: {str(exc)}"
        )

@router.put("/faculty/profile", response_model=FacultyProfileResponse)
@faculty_router.put("/profile", response_model=FacultyProfileResponse)
async def update_faculty_profile(
    profile_in: FacultyProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        from app.models.academic import Course
        from sqlalchemy.orm import selectinload
        from sqlalchemy import or_
        
        if profile_in.full_name is not None:
            current_user.full_name = profile_in.full_name.strip()
        if profile_in.department is not None:
            current_user.department = profile_in.department.strip()
        if profile_in.semester is not None:
            current_user.semester = profile_in.semester.strip()
        
        await db.commit()
        await db.refresh(current_user)

        conditions = [Course.faculty_id == current_user.id]
        if current_user.department and current_user.department.strip():
            conditions.append(Course.department == current_user.department.strip())

        stmt = select(Course).options(
            selectinload(Course.units),
            selectinload(Course.course_outcomes)
        ).where(or_(*conditions)).order_by(Course.code)
        
        result = await db.execute(stmt)
        courses = result.scalars().unique().all()

        validated_courses = []
        for c in courses:
            try:
                validated_courses.append(CourseResponse.model_validate(c))
            except Exception:
                validated_courses.append(CourseResponse(
                    id=c.id,
                    code=c.code or "UNKNOWN",
                    name=c.name or "Course",
                    department=c.department or current_user.department or "Computer Science & Engineering",
                    semester=c.semester or "Semester V",
                    academic_year=c.academic_year or "2025-2026",
                    description=c.description,
                    faculty_id=c.faculty_id,
                    analysis_status=c.analysis_status or "Pending",
                    units=[],
                    course_outcomes=[]
                ))

        return FacultyProfileResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name or "Faculty Member",
            department=current_user.department or "Computer Science & Engineering",
            semester=getattr(current_user, "semester", "Semester V") or "Semester V",
            role=current_user.role or "Faculty",
            faculty_id=f"FAC-{current_user.id:04d}",
            assigned_courses=validated_courses,
            courses_assigned=validated_courses
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("FACULTY_PROFILE_UPDATE_FAILED")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update faculty profile: {str(exc)}"
        )

