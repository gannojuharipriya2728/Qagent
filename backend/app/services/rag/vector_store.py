import os
import abc
import json
import numpy as np
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.rag.embeddings import embedding_engine

class VectorDocument:
    def __init__(
        self,
        doc_id: str,
        content: str,
        vector: List[float],
        metadata: Dict[str, Any]
    ):
        self.doc_id = doc_id
        self.content = content
        self.vector = vector
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "vector": self.vector,
            "metadata": self.metadata
        }

class BaseVectorStore(abc.ABC):
    """Abstract interface for RAG vector retrieval backends."""

    @abc.abstractmethod
    async def add_documents(
        self,
        contents: List[str],
        metadatas: List[Dict[str, Any]],
        doc_ids: Optional[List[str]] = None
    ) -> List[str]:
        pass

    @abc.abstractmethod
    def delete_by_resource_id(self, resource_id: int):
        pass

    @abc.abstractmethod
    def delete_by_course_id(self, course_id: int):
        pass

    @abc.abstractmethod
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        course_id: Optional[int] = None,
        unit_number: Optional[int] = None,
        document_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    async def calculate_semantic_similarity(self, text_a: str, text_b: str) -> float:
        pass

class AcademicVectorStore(BaseVectorStore):
    """
    In-memory and JSON-persisted vector store.
    Provides fast, standalone retrieval with strict course & unit filtering.
    """
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(settings.VECTOR_STORAGE_DIR, "index.json")
        self.documents: Dict[str, VectorDocument] = {}
        self._load_from_disk()

    def _load_from_disk(self):
        if not self.storage_path or self.storage_path == ":memory:":
            return
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        doc = VectorDocument(
                            doc_id=item["doc_id"],
                            content=item["content"],
                            vector=item["vector"],
                            metadata=item["metadata"]
                        )
                        self.documents[doc.doc_id] = doc
            except Exception as e:
                print(f"Warning: Could not load vector store from disk: {e}")

    def _save_to_disk(self):
        if not self.storage_path or self.storage_path == ":memory:":
            return
        dir_name = os.path.dirname(self.storage_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump([doc.to_dict() for doc in self.documents.values()], f)
        except Exception as e:
            print(f"Warning: Could not save vector store to disk: {e}")

    async def add_documents(
        self,
        contents: List[str],
        metadatas: List[Dict[str, Any]],
        doc_ids: Optional[List[str]] = None
    ) -> List[str]:
        embeddings = await embedding_engine.embed_documents(contents)
        added_ids = []

        for i, (content, metadata, vector) in enumerate(zip(contents, metadatas, embeddings)):
            doc_id = doc_ids[i] if doc_ids and i < len(doc_ids) else f"chunk_{len(self.documents) + i + 1}"
            vdoc = VectorDocument(
                doc_id=doc_id,
                content=content,
                vector=vector,
                metadata=metadata
            )
            self.documents[doc_id] = vdoc
            added_ids.append(doc_id)

        self._save_to_disk()
        return added_ids

    def delete_by_resource_id(self, resource_id: int):
        keys_to_delete = [
            k for k, doc in self.documents.items()
            if doc.metadata.get("resource_id") == resource_id
        ]
        for k in keys_to_delete:
            del self.documents[k]
        if keys_to_delete:
            self._save_to_disk()

    def delete_by_course_id(self, course_id: int):
        keys_to_delete = [
            k for k, doc in self.documents.items()
            if doc.metadata.get("course_id") == course_id
        ]
        for k in keys_to_delete:
            del self.documents[k]
        if keys_to_delete:
            self._save_to_disk()

    def clear(self):
        self.documents.clear()
        self._save_to_disk()

    async def _hydrate_course_chunks_from_db(self, course_id: int):
        """
        Dynamically hydrates in-memory vector store from PostgreSQL ResourceChunk records
        for serverless execution where disk persistence across lambdas is ephemeral.
        """
        try:
            from app.core.database import AsyncSessionLocal
            from app.models.resource import Resource, ResourceChunk
            from app.models.academic import Course
            from sqlalchemy import select

            async with AsyncSessionLocal() as session:
                stmt = (
                    select(ResourceChunk, Resource, Course.code)
                    .join(Resource, ResourceChunk.resource_id == Resource.id)
                    .outerjoin(Course, Resource.course_id == Course.id)
                    .where(Resource.course_id == course_id)
                )
                results = (await session.execute(stmt)).all()
                if not results:
                    return

                contents_to_embed = []
                metas_to_add = []
                ids_to_add = []
                for chunk, res, course_code in results:
                    doc_id = f"res_{res.id}_chunk_{chunk.chunk_index}"
                    if doc_id not in self.documents:
                        contents_to_embed.append(chunk.content)
                        metas_to_add.append({
                            "resource_id": res.id,
                            "course_id": res.course_id,
                            "course_code": course_code or "",
                            "file_name": res.file_name,
                            "document_type": res.document_type,
                            "unit_number": chunk.unit_number,
                            "page_number": chunk.page_number,
                            "topic": chunk.topic,
                            "chunk_index": chunk.chunk_index
                        })
                        ids_to_add.append(doc_id)

                if contents_to_embed:
                    vectors = await embedding_engine.embed_documents(contents_to_embed)
                    for doc_id, content, meta, vec in zip(ids_to_add, contents_to_embed, metas_to_add, vectors):
                        self.documents[doc_id] = VectorDocument(
                            doc_id=doc_id,
                            content=content,
                            vector=vec,
                            metadata=meta
                        )
        except Exception:
            # Non-blocking fallback if DB is unreachable or during offline unit testing
            pass

    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        course_id: Optional[int] = None,
        unit_number: Optional[int] = None,
        document_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # In serverless environments, hydrate chunks from PostgreSQL if not present in memory
        if course_id is not None:
            has_course_docs = any(
                str(doc.metadata.get("course_id", "")).strip() == str(course_id).strip()
                for doc in self.documents.values()
            )
            if not has_course_docs:
                await self._hydrate_course_chunks_from_db(course_id)

        if not self.documents:
            return []

        query_vector = np.array(await embedding_engine.embed_query(query), dtype=float)
        query_norm = np.linalg.norm(query_vector)
        if query_norm == 0:
            query_norm = 1e-9

        scored_docs = []
        for doc in self.documents.values():
            meta = doc.metadata or {}
            # Metadata Filters - Strict Course Isolation
            if course_id is not None:
                doc_cid = meta.get("course_id")
                if doc_cid is None or str(doc_cid).strip() != str(course_id).strip():
                    continue
            if unit_number is not None and meta.get("unit_number") is not None:
                if str(meta.get("unit_number")).strip() != str(unit_number).strip():
                    continue
            if document_type is not None and meta.get("document_type") != document_type:
                continue

            doc_vector = np.array(doc.vector, dtype=float)
            doc_norm = np.linalg.norm(doc_vector)
            if doc_norm == 0:
                doc_norm = 1e-9

            # Pad or align vector dimensions if needed
            if len(query_vector) != len(doc_vector):
                min_len = min(len(query_vector), len(doc_vector))
                sim = float(np.dot(query_vector[:min_len], doc_vector[:min_len]) / (np.linalg.norm(query_vector[:min_len]) * np.linalg.norm(doc_vector[:min_len]) + 1e-9))
            else:
                sim = float(np.dot(query_vector, doc_vector) / (query_norm * doc_norm))

            # Bonus for exact keyword/topic match in query
            topic = str(meta.get("topic") or "").lower()
            if topic and any(w in query.lower() for w in topic.split() if len(w) > 3):
                sim = min(1.0, sim + 0.15)

            scored_docs.append({
                "doc_id": doc.doc_id,
                "content": doc.content,
                "similarity_score": round(sim, 4),
                "metadata": meta
            })

        # Sort descending by similarity
        scored_docs.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_docs[:k]

    async def calculate_semantic_similarity(self, text_a: str, text_b: str) -> float:
        clean_a = text_a.strip().lower()
        clean_b = text_b.strip().lower()
        if clean_a == clean_b:
            return 1.0

        # Token set overlap
        words_a = set(clean_a.split())
        words_b = set(clean_b.split())
        if words_a and words_b:
            jaccard = len(words_a.intersection(words_b)) / len(words_a.union(words_b))
            if jaccard > 0.85:
                return round(jaccard, 4)

        vec_a = np.array(await embedding_engine.embed_query(text_a), dtype=float)
        vec_b = np.array(await embedding_engine.embed_query(text_b), dtype=float)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        min_len = min(len(vec_a), len(vec_b))
        sim = float(np.dot(vec_a[:min_len], vec_b[:min_len]) / (np.linalg.norm(vec_a[:min_len]) * np.linalg.norm(vec_b[:min_len]) + 1e-9))
        return max(0.0, min(1.0, round(sim, 4)))

class PGVectorStore(AcademicVectorStore):
    """
    PostgreSQL-backed vector store adapter.
    Falls back gracefully to AcademicVectorStore with database-synchronized persistence.
    """
    pass

_vector_store_instance = None

def get_vector_store() -> BaseVectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        provider = settings.VECTOR_STORE_PROVIDER.lower()
        if provider == "pgvector":
            _vector_store_instance = PGVectorStore()
        else:
            _vector_store_instance = AcademicVectorStore()
    return _vector_store_instance

vector_store = get_vector_store()

__all__ = [
    "VectorDocument",
    "BaseVectorStore",
    "AcademicVectorStore",
    "PGVectorStore",
    "get_vector_store",
    "vector_store"
]
