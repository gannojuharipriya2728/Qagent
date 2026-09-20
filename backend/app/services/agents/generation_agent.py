from typing import Dict, Any, Optional
import logging
from backend.app.services.llm.factory import get_llm_provider
from backend.app.services.agents.requirement_agent import PlannedQuestionSlot
from backend.app.services.agents.retrieval_agent import RetrievalResult

logger = logging.getLogger("qagent.generation_agent")

class QuestionGenerationAgent:
    """
    Agent 3: Question Generation Agent
    Synthesizes academic university examination questions grounded strictly in
    retrieved syllabus & textbook context using the OpenRouter AI model (NVIDIA Nemotron).
    """

    SYSTEM_PROMPT = """You are an expert university examination paper setter, curriculum analyst, Bloom's Taxonomy specialist, and academic assessment designer.
Your task is to generate a descriptive, rigorous university-level exam question grounded STRICTLY in the provided academic resources.

CRITICAL GENERATION RULES:
1. GROUNDED IN RAG CONTEXT: Generate questions strictly from the supplied Retrieved Context. Do not introduce concepts outside this course.
2. BLOOM'S TAXONOMY CORRESPONDENCE:
   - Remember: define, state, list, name, recall, identify
   - Understand: explain, describe, summarize, discuss, illustrate, distinguish
   - Apply: apply, compute, solve, demonstrate, construct, implement
   - Analyze: analyze, compare, contrast, deconstruct, differentiate, investigate
   - Evaluate: evaluate, justify, assess, critique, defend, appraise
   - Create: design, formulate, develop, devise, propose, synthesize
3. MARKS & MULTI-PART STRUCTURE:
   - For short questions (<= 2 marks): Write a concise, focused question.
   - For medium questions (3 to 5 marks): Require explanation and analytical depth.
   - For long questions (>= 10 marks): Structure into sub-parts (a) and (b) exploring foundational theory and applied design/analysis.
4. ABSOLUTELY FORBIDDEN:
   - NO placeholder tags like [Source], [Topic], [Concept], [Insert], {source}, undefined, null.
   - NO incomplete sentences or fragmented syntax.
   - NO generic meta-commentary inside the question text.
5. STRICT JSON OUTPUT: Return ONLY a valid JSON object matching the requested schema.
"""

    @staticmethod
    async def generate_question(
        slot: PlannedQuestionSlot,
        retrieval: RetrievalResult,
        course_name: str,
        override_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        llm = None
        user_prompt = f"""Generate an examination question based on the following specifications and retrieved academic context:

SPECIFICATIONS:
- Course: {course_name}
- Section: {slot.section_name}
- Question Number: {slot.question_number}
- Unit: {slot.unit_number}
- Marks: {slot.marks}
- Difficulty: {slot.difficulty}
- Target Bloom Level: {slot.bloom_level}
- Target Course Outcome: {slot.course_outcome}
- Question Type: {slot.question_type}

RETRIEVED ACADEMIC CONTEXT:
{retrieval.assembled_context}

OUTPUT JSON SCHEMA:
{{
  "question_text": "Complete question text",
  "unit": {slot.unit_number},
  "marks": {slot.marks},
  "difficulty": "{slot.difficulty}",
  "bloom_level": "{slot.bloom_level}",
  "course_outcome": "{slot.course_outcome}",
  "question_type": "{slot.question_type}",
  "source_topics": ["List of key academic topics tested"],
  "reasoning": "Concise explanation of syllabus and Bloom alignment"
}}
"""

        try:
            llm = get_llm_provider(override_provider)
            result = await llm.generate_json(
                prompt=user_prompt,
                system_prompt=QuestionGenerationAgent.SYSTEM_PROMPT,
                max_tokens=1024
            )
            
            # Populate and enforce ground-truth slot parameters
            q_text = result.get("question_text") or result.get("question") or ""
            result["question_text"] = q_text
            result["question"] = q_text
            result["unit"] = slot.unit_number
            result["marks"] = slot.marks
            result["bloom_level"] = result.get("bloom_level") or slot.bloom_level
            result["course_outcome"] = result.get("course_outcome") or result.get("co") or slot.course_outcome
            result["co"] = result["course_outcome"]
            result["difficulty"] = result.get("difficulty") or slot.difficulty
            result["source_documents"] = retrieval.source_documents
            result["sources"] = retrieval.source_documents
            if not result.get("source_topics"):
                result["source_topics"] = retrieval.source_topics

            return result

        except Exception as e:
            logger.error(f"OpenRouter AI question generation failed for Unit {slot.unit_number}: {e}")
            raise RuntimeError(
                f"OpenRouter AI generation failed for Unit {slot.unit_number} (CO: {slot.course_outcome}). "
                f"Error: {e}. Please verify OPENROUTER_API_KEY, model availability, quota, or network connectivity."
            )
