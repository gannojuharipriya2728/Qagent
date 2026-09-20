import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.academic import Course, Unit, CourseOutcome
from backend.app.models.resource import Resource, ResourceChunk
from backend.app.schemas.resource import ResourceResponse, ResourceDetailResponse
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.services.rag.document_processor import DocumentProcessor
from backend.app.services.rag.chunker import AcademicChunker
from backend.app.services.rag.vector_store import vector_store
from backend.app.services.llm.syllabus_analyzer import SyllabusAnalyzer

from backend.app.services.storage import get_storage_service
import time

router = APIRouter(prefix="/resources", tags=["Academic Resources"])

@router.get("", response_model=List[ResourceResponse])
async def list_resources(course_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Resource)
    if course_id:
        stmt = stmt.where(Resource.course_id == course_id)
    stmt = stmt.order_by(Resource.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{resource_id}", response_model=ResourceDetailResponse)
async def get_resource(resource_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Resource).options(selectinload(Resource.chunks)).where(Resource.id == resource_id)
    resource = (await db.execute(stmt)).scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found.")
    return resource

@router.post("/upload", response_model=ResourceResponse)
async def upload_resource(
    course_id: int = Form(...),
    title: str = Form(...),
    document_type: str = Form("textbook"),  # "syllabus", "textbook", "previous_paper", "notes"
    unit_number: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify course
    stmt_c = select(Course).where(Course.id == course_id)
    course = (await db.execute(stmt_c)).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail=f"Course with ID {course_id} not found.")

    # Validate file extension
    filename = file.filename or "uploaded_resource.pdf"
    ext = filename.split(".")[-1].lower()
    if ext not in ["pdf", "docx", "txt", "doc", "md"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type .{ext}. Please upload a PDF, DOCX, or TXT file."
        )

    storage_service = get_storage_service()
    timestamp = int(time.time())
    storage_key = f"courses/{course_id}/{timestamp}_{filename}"

    # Save via storage service
    await storage_service.upload_file(file.file, storage_key, content_type=file.content_type or "application/octet-stream")
    local_path = await storage_service.get_local_path(storage_key)
    file_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0

    resource = Resource(
        course_id=course_id,
        title=title,
        file_name=filename,
        file_path=local_path,
        storage_key=storage_key,
        file_type=ext,
        document_type=document_type,
        unit_number=unit_number,
        file_size_bytes=file_size,
        status="Processing",
        uploaded_by=current_user.id
    )
    db.add(resource)
    await db.commit()
    await db.refresh(resource)

    # Trigger processing & vectorization
    try:
        doc = DocumentProcessor.process_file(local_path, ext)
        chunker = AcademicChunker(chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)
        chunks = chunker.chunk_document(doc.pages, default_unit=unit_number)

        contents = []
        metadatas = []
        doc_ids = []

        for c in chunks:
            chunk_model = ResourceChunk(
                resource_id=resource.id,
                chunk_index=c.chunk_index,
                content=c.content,
                page_number=c.page_number,
                unit_number=c.unit_number or unit_number,
                topic=c.topic,
                token_count=c.token_count
            )
            db.add(chunk_model)

            contents.append(c.content)
            metadatas.append({
                "resource_id": resource.id,
                "course_id": course_id,
                "course_code": course.code,
                "file_name": filename,
                "document_type": document_type,
                "unit_number": c.unit_number or unit_number,
                "page_number": c.page_number,
                "topic": c.topic,
                "chunk_index": c.chunk_index
            })
            doc_ids.append(f"res_{resource.id}_chunk_{c.chunk_index}")

        await db.flush()

        # Add to Vector Store
        await vector_store.add_documents(
            contents=contents,
            metadatas=metadatas,
            doc_ids=doc_ids
        )

        # If syllabus document, check if course units are empty and enrich automatically
        if document_type == "syllabus":
            stmt_u = select(Unit).where(Unit.course_id == course_id)
            existing_units = (await db.execute(stmt_u)).scalars().all()
            if not existing_units:
                full_text = "\n\n".join([p.text for p in doc.pages if p.text])
                if full_text:
                    try:
                        extracted = await SyllabusAnalyzer.analyze_syllabus_text(full_text)
                        for u_data in extracted.get("units", []):
                            u = Unit(
                                course_id=course_id,
                                unit_number=u_data.get("unit_number", 1),
                                title=u_data.get("title", f"Unit {u_data.get('unit_number', 1)}"),
                                topics=u_data.get("topics", "") if isinstance(u_data.get("topics"), str) else ", ".join(u_data.get("topics", []))
                            )
                            db.add(u)
                        for co_data in extracted.get("course_outcomes", []):
                            co = CourseOutcome(
                                course_id=course_id,
                                code=co_data.get("code", "CO1"),
                                description=co_data.get("description", ""),
                                target_bloom_level=co_data.get("bloom_level", "Apply")
                            )
                            db.add(co)
                    except Exception:
                        pass

        resource.status = "Processed"
        resource.chunk_count = len(chunks)
        await db.commit()
        await db.refresh(resource)

    except Exception as e:
        resource.status = "Failed"
        resource.error_message = str(e)
        await db.commit()
        await db.refresh(resource)

    return resource

@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Resource).where(Resource.id == resource_id)
    resource = (await db.execute(stmt)).scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found.")

    # Remove from vector store
    vector_store.delete_by_resource_id(resource_id)

    # Remove file via storage service
    storage_service = get_storage_service()
    if resource.storage_key:
        await storage_service.delete_file(resource.storage_key)
    elif resource.file_path and os.path.exists(resource.file_path):
        try:
            os.remove(resource.file_path)
        except Exception:
            pass

    await db.delete(resource)
    await db.commit()
    return {"message": "Resource deleted successfully."}

@router.get("/{resource_id}/download")
async def download_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Resource).where(Resource.id == resource_id)
    resource = (await db.execute(stmt)).scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found.")

    storage_service = get_storage_service()
    key_to_use = resource.storage_key or resource.file_path
    try:
        data = await storage_service.download_bytes(key_to_use)
    except Exception:
        # Fallback to direct local path
        if resource.file_path and os.path.exists(resource.file_path):
            with open(resource.file_path, "rb") as f:
                data = f.read()
        else:
            raise HTTPException(status_code=404, detail="Resource file content not found in storage.")

    from fastapi.responses import Response
    content_type = "application/pdf" if resource.file_type == "pdf" else "application/octet-stream"
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{resource.file_name}"'}
    )

