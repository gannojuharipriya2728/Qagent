import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, TokenResponse, UserResponse
from app.api.deps import get_current_user

logger = logging.getLogger("qagent.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])

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
