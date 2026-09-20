from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.academic import Course
from backend.app.models.resource import Resource, ResourceChunk
from backend.app.models.paper import QuestionPaper, Question, GenerationSession
from backend.app.schemas.auth import UserResponse
from backend.app.api.deps import get_admin_user
from backend.app.services.rag.vector_store import vector_store

router = APIRouter(prefix="/admin", tags=["Administration"])

@router.get("/stats")
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one() or 0
    total_courses = (await db.execute(select(func.count(Course.id)))).scalar_one() or 0
    total_resources = (await db.execute(select(func.count(Resource.id)))).scalar_one() or 0
    total_chunks = (await db.execute(select(func.count(ResourceChunk.id)))).scalar_one() or 0
    total_papers = (await db.execute(select(func.count(QuestionPaper.id)))).scalar_one() or 0
    total_questions = (await db.execute(select(func.count(Question.id)))).scalar_one() or 0
    failed_resources = (await db.execute(select(func.count(Resource.id)).where(Resource.status == "Failed"))).scalar_one() or 0

    return {
        "total_users": total_users,
        "total_courses": total_courses,
        "total_resources": total_resources,
        "total_chunks": total_chunks,
        "total_papers": total_papers,
        "total_questions": total_questions,
        "failed_resources": failed_resources,
        "vector_store_documents": len(vector_store.documents),
        "system_status": "Operational",
        "rag_engine": "Active"
    }

@router.get("/users", response_model=List[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    stmt = select(User).order_by(User.id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.patch("/users/{user_id}/toggle-status")
async def toggle_user_status(user_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    user.is_active = not user.is_active
    await db.commit()
    await db.refresh(user)
    return {"message": f"User status changed to {'Active' if user.is_active else 'Deactivated'}", "is_active": user.is_active}
