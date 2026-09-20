from typing import List, Dict, Any, Optional
from app.services.rag.vector_store import vector_store
from app.services.agents.requirement_agent import PlannedQuestionSlot

class RetrievalResult:
    def __init__(
        self,
        assembled_context: str,
        source_documents: List[Dict[str, Any]],
        source_topics: List[str]
    ):
        self.assembled_context = assembled_context
        self.source_documents = source_documents
        self.source_topics = source_topics

class RAGRetrievalAgent:
    """
    Agent 2: Retrieval Agent
    Performs metadata-filtered semantic search over academic resources to supply grounded context.
    """

    @staticmethod
    async def retrieve_context_for_slot(
        slot: PlannedQuestionSlot,
        course_id: int,
        unit_topics: Optional[str] = None,
        top_k: int = 5
    ) -> RetrievalResult:
        query_parts = [
            f"Unit {slot.unit_number}",
            slot.bloom_level,
            slot.course_outcome,
            slot.question_type
        ]
        if unit_topics:
            query_parts.append(unit_topics)

        query = " ".join(query_parts)

        # 1. Search with Unit Filter
        chunks = await vector_store.similarity_search(
            query=query,
            k=top_k,
            course_id=course_id,
            unit_number=slot.unit_number
        )

        # 2. If fewer than 2 chunks found for specific unit, widen search to whole course
        if len(chunks) < 2:
            general_chunks = await vector_store.similarity_search(
                query=query,
                k=top_k,
                course_id=course_id
            )
            # Combine unique chunks
            seen_ids = {c["doc_id"] for c in chunks}
            for gc in general_chunks:
                if gc["doc_id"] not in seen_ids:
                    chunks.append(gc)
                    seen_ids.add(gc["doc_id"])

        # Format retrieved context
        context_blocks = []
        source_documents = []
        source_topics = []

        for c in chunks:
            meta = c.get("metadata", {})
            doc_name = meta.get("file_name", "Academic Resource")
            page = meta.get("page_number", 1)
            topic = meta.get("topic") or f"Unit {slot.unit_number} Subject Matter"
            score = c.get("similarity_score", 0.85)

            context_blocks.append(f"[Source: {doc_name} | Unit: {slot.unit_number} | Page: {page} | Topic: {topic}]\n{c['content']}")
            
            source_documents.append({
                "document_name": doc_name,
                "document_type": meta.get("document_type", "textbook"),
                "page": page,
                "topic": topic,
                "similarity_score": score,
                "chunk_id": c.get("doc_id"),
                "course_id": meta.get("course_id") or course_id,
                "course_code": meta.get("course_code")
            })

            if topic and topic not in source_topics:
                source_topics.append(topic)

        # Fallback if vector store has no chunks yet (e.g. before uploads)
        if not context_blocks:
            default_topic = unit_topics if unit_topics else f"Fundamental Concepts in Unit {slot.unit_number}"
            context_blocks.append(f"[Curriculum Syllabus: Unit {slot.unit_number}]\n{default_topic}")
            source_topics.append(default_topic)
            source_documents.append({
                "document_name": "Official Course Syllabus",
                "document_type": "syllabus",
                "page": 1,
                "topic": default_topic,
                "similarity_score": 1.0,
                "chunk_id": "syllabus_core",
                "course_id": course_id,
                "course_code": None
            })

        assembled = "\n\n---\n\n".join(context_blocks)
        return RetrievalResult(
            assembled_context=assembled,
            source_documents=source_documents,
            source_topics=source_topics
        )
