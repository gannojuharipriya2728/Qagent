from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ResourceChunkResponse(BaseModel):
    id: int
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    unit_number: Optional[int] = None
    topic: Optional[str] = None
    token_count: int = 0

    class Config:
        from_attributes = True

class ResourceResponse(BaseModel):
    id: int
    course_id: int
    title: str
    file_name: str
    file_type: str
    document_type: str
    storage_key: Optional[str] = None
    unit_number: Optional[int] = None
    file_size_bytes: int
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ResourceDetailResponse(ResourceResponse):
    chunks: List[ResourceChunkResponse] = []
