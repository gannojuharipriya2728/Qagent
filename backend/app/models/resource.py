from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.core.database import Base

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    storage_key = Column(String(500), nullable=True)  # S3 / Object storage key or normalized path
    file_type = Column(String(50), nullable=False)  # "pdf", "docx", "txt"
    document_type = Column(String(50), nullable=False)  # "syllabus", "textbook", "previous_paper", "notes"
    unit_number = Column(Integer, nullable=True)  # Optional mapping to specific unit or None for general
    file_size_bytes = Column(Integer, default=0)
    status = Column(String(50), default="Uploaded")  # "Uploaded", "Processing", "Processed", "Failed"
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    course = relationship("Course", back_populates="resources")
    chunks = relationship("ResourceChunk", back_populates="resource", cascade="all, delete-orphan")

class ResourceChunk(Base):
    __tablename__ = "resource_chunks"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    unit_number = Column(Integer, nullable=True)
    topic = Column(String(255), nullable=True)
    token_count = Column(Integer, default=0)
    embedding_id = Column(String(100), nullable=True)  # Vector store identifier

    resource = relationship("Resource", back_populates="chunks")
