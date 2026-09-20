import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.generation import GenerationRequest, AgentStepLog
from app.models.academic import Course, Unit, CourseOutcome
from app.models.paper import QuestionPaper, Question, GenerationSession, ValidationResult
from app.services.agents.requirement_agent import RequirementAnalyzerAgent
from app.services.agents.retrieval_agent import RAGRetrievalAgent
from app.services.agents.generation_agent import QuestionGenerationAgent
from app.services.agents.validation_agent import ValidationAgent
from app.services.agents.revision_agent import RevisionAgent

class AgenticGenerationOrchestrator:
    @staticmethod
    async def run_pipeline(
        db: AsyncSession,
        request: GenerationRequest,
        user_id: Optional[int] = None,
        override_provider: Optional[str] = None
    ) -> tuple[QuestionPaper, List[Dict[str, Any]], float]:
        start_time = time.time()
        steps_log: List[Dict[str, Any]] = []

        def log_step(step_name: str, agent_name: str, status: str, message: str, details: Optional[Dict[str, Any]] = None):
            steps_log.append({
                "step_name": step_name,
                "agent_name": agent_name,
                "status": status,
                "message": message,
                "details": details or {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        # 1. Fetch Course details, Units, and COs
        log_step(
            step_name="Course Verification",
            agent_name="Environment Initializer",
            status="started",
            message=f"Verifying course ID {request.course_id}..."
        )
        stmt = select(Course).where(Course.id == request.course_id)
        result = await db.execute(stmt)
        course = result.scalar_one_or_none()
        if not course:
            raise ValueError(f"Course ID {request.course_id} not found.")

        stmt_units = select(Unit).where(Unit.course_id == course.id).order_by(Unit.unit_number)
        units_result = await db.execute(stmt_units)
        units = units_result.scalars().all()
        unit_map = {u.unit_number: u.topics for u in units}
        available_unit_nums = [u.unit_number for u in units] if units else [1, 2, 3, 4, 5]

        stmt_cos = select(CourseOutcome).where(CourseOutcome.course_id == course.id)
        cos_result = await db.execute(stmt_cos)
        cos = cos_result.scalars().all()
        available_cos = [c.code for c in cos] if cos else ["CO1", "CO2", "CO3"]
        if request.target_course_outcomes:
            filtered_cos = [c for c in available_cos if c in request.target_course_outcomes]
            if filtered_cos:
                available_cos = filtered_cos

        log_step(
            step_name="Course Verification",
            agent_name="Environment Initializer",
            status="completed",
            message=f"Loaded course '{course.code} — {course.name}' with {len(units)} units and {len(available_cos)} Course Outcomes: {', '.join(available_cos)}."
        )

        # 2. Agent 1: Requirement Analysis
        log_step(
            step_name="Requirement Analysis",
            agent_name="Agent 1 — Requirement Analyzer",
            status="started",
            message="Analyzing exam blueprint, section quotas, Bloom distribution, and marks allocation..."
        )
        planned_slots = RequirementAnalyzerAgent.analyze_and_plan(
            request=request,
            available_units=available_unit_nums,
            available_cos=available_cos
        )
        log_step(
            step_name="Requirement Analysis",
            agent_name="Agent 1 — Requirement Analyzer",
            status="completed",
            message=f"Created blueprint with {len(planned_slots)} question slots across {len(request.sections)} sections.",
            details={"slots_count": len(planned_slots)}
        )

        # 3. Agent 2 to Agent 5: Retrieval, Generation, Validation, Revision Loop
        generated_questions_data = []
        accepted_question_texts: List[str] = []
        unit_coverage_counts: Dict[int, int] = {u: 0 for u in available_unit_nums}

        for slot in planned_slots:
            # Agent 2: Retrieval
            log_step(
                step_name=f"RAG Retrieval (Q{slot.question_number})",
                agent_name="Agent 2 — Retrieval Agent",
                status="started",
                message=f"Retrieving vector chunks for Unit {slot.unit_number} ({slot.bloom_level} / {slot.course_outcome})..."
            )
            unit_topics = unit_map.get(slot.unit_number, f"Unit {slot.unit_number} curriculum")
            retrieval_res = await RAGRetrievalAgent.retrieve_context_for_slot(
                slot=slot,
                course_id=course.id,
                unit_topics=unit_topics,
                top_k=request.top_k_sources
            )
            log_step(
                step_name=f"RAG Retrieval (Q{slot.question_number})",
                agent_name="Agent 2 — Retrieval Agent",
                status="completed",
                message=f"Retrieved {len(retrieval_res.source_documents)} context sources from textbooks/syllabus.",
                details={"sources": [s["document_name"] for s in retrieval_res.source_documents]}
            )

            # Agent 3: Generation
            log_step(
                step_name=f"Question Generation (Q{slot.question_number})",
                agent_name="Agent 3 — Generation Agent",
                status="started",
                message=f"Formulating {slot.marks}-mark {slot.question_type} question using pedagogical {slot.bloom_level} action verbs..."
            )
            q_data = await QuestionGenerationAgent.generate_question(
                slot=slot,
                retrieval=retrieval_res,
                course_name=course.name,
                override_provider=override_provider
            )
            log_step(
                step_name=f"Question Generation (Q{slot.question_number})",
                agent_name="Agent 3 — Generation Agent",
                status="completed",
                message=f"Generated draft question for Unit {slot.unit_number} ({slot.course_outcome})."
            )

            # Agent 4: Validation
            log_step(
                step_name=f"Question Validation (Q{slot.question_number})",
                agent_name="Agent 4 — Validation Agent",
                status="started",
                message=f"Checking Bloom taxonomy, Course Outcome alignment, and duplicate similarity..."
            )
            val_res = await ValidationAgent.validate_question(
                slot=slot,
                generated_data=q_data,
                existing_questions=accepted_question_texts,
                similarity_threshold=request.similarity_threshold
            )

            # Agent 5: Revision if invalid (up to 3 attempts)
            attempt = 1
            max_revisions = 3
            while not val_res.is_valid and attempt <= max_revisions:
                log_step(
                    step_name=f"Revision Triggered (Q{slot.question_number} Attempt {attempt}/{max_revisions})",
                    agent_name="Agent 5 — Revision Agent",
                    status="retrying",
                    message=f"Validation notice: {val_res.feedback_notes}. Retrying generation with targeted repair..."
                )
                q_data, val_res = await RevisionAgent.revise_question(
                    slot=slot,
                    previous_data=q_data,
                    validation_result=val_res,
                    course_id=course.id,
                    course_name=course.name,
                    unit_topics=unit_topics,
                    existing_questions=accepted_question_texts,
                    attempt_number=attempt,
                    override_provider=override_provider
                )
                attempt += 1

            if not val_res.is_valid and override_provider != "deterministic" and settings.LLM_PROVIDER == "openrouter":
                raise RuntimeError(
                    f"Question generation failed validation after {max_revisions} attempts for Q{slot.question_number} "
                    f"(Unit {slot.unit_number}, {slot.bloom_level}, {slot.course_outcome}): {val_res.feedback_notes}"
                )

            log_step(
                step_name=f"Question Validation (Q{slot.question_number})",
                agent_name="Agent 4 — Validation Agent",
                status="completed",
                message=f"Validation passed: Syllabus {int(val_res.syllabus_alignment_score*100)}%, Bloom {int(val_res.bloom_alignment_score*100)}%."
            )

            # Accept question
            accepted_question_texts.append(q_data["question_text"])
            unit_coverage_counts[slot.unit_number] = unit_coverage_counts.get(slot.unit_number, 0) + 1
            
            # Store package
            q_data["slot"] = slot
            q_data["validation"] = val_res
            generated_questions_data.append(q_data)

        # 4. Syllabus Coverage Calculation & AI Paper Synthesis
        covered_units_count = sum(1 for u, count in unit_coverage_counts.items() if count > 0)
        overall_coverage = round((covered_units_count / len(available_unit_nums)) * 100.0 if available_unit_nums else 100.0, 1)

        # AI Synthesis Review
        log_step(
            step_name="AI Paper Synthesis & Quality Review",
            agent_name="Agent 5 — Paper Synthesis Reviewer",
            status="started",
            message="Analyzing whole-paper syllabus balance, cognitive progression, and section consistency..."
        )

        co_counts = {}
        bloom_counts = {}
        for item in generated_questions_data:
            co = item.get("course_outcome", "CO1")
            bl = item.get("bloom_level", "Understand")
            co_counts[co] = co_counts.get(co, 0) + 1
            bloom_counts[bl] = bloom_counts.get(bl, 0) + 1

        log_step(
            step_name="AI Paper Synthesis & Quality Review",
            agent_name="Agent 5 — Paper Synthesis Reviewer",
            status="completed",
            message=f"Paper synthesis verified: {overall_coverage}% syllabus coverage, {len(generated_questions_data)} validated questions, marks sum {request.total_marks}M.",
            details={
                "syllabus_coverage": overall_coverage,
                "co_distribution": co_counts,
                "bloom_distribution": bloom_counts,
                "unit_coverage": unit_coverage_counts
            }
        )

        # 5. Persist Question Paper to Database
        paper = QuestionPaper(
            course_id=course.id,
            created_by=user_id,
            title=request.title,
            examination_name=request.examination_name,
            institution_name=request.institution_name,
            duration_minutes=request.duration_minutes,
            total_marks=request.total_marks,
            instructions=request.instructions,
            difficulty_distribution=request.difficulty_distribution,
            bloom_distribution=request.bloom_distribution,
            syllabus_coverage_score=overall_coverage,
            status="Generated"
        )
        db.add(paper)
        await db.flush()

        # Add Questions
        for item in generated_questions_data:
            slot: PlannedQuestionSlot = item["slot"]
            val_res: ValidationResultData = item["validation"]

            q_model = Question(
                paper_id=paper.id,
                section_name=slot.section_name,
                question_number=slot.question_number,
                question_text=item["question_text"],
                marks=slot.marks,
                unit_number=slot.unit_number,
                bloom_level=item.get("bloom_level") or slot.bloom_level,
                course_outcome=item.get("course_outcome") or slot.course_outcome,
                difficulty=item.get("difficulty") or slot.difficulty,
                question_type=slot.question_type,
                source_topics=item.get("source_topics", []),
                source_documents=item.get("source_documents", []),
                generation_reasoning=item.get("reasoning", ""),
                is_revised=item.get("is_revised", False),
                revision_count=item.get("revision_count", 0)
            )
            db.add(q_model)
            await db.flush()

            # Add Validation Result
            val_model = ValidationResult(
                question_id=q_model.id,
                is_valid=val_res.is_valid,
                syllabus_alignment_score=val_res.syllabus_alignment_score,
                co_alignment_score=val_res.co_alignment_score,
                difficulty_match_score=val_res.difficulty_match_score,
                bloom_alignment_score=val_res.bloom_alignment_score,
                is_duplicate=val_res.is_duplicate,
                duplicate_similarity_score=val_res.duplicate_similarity_score,
                feedback_notes=val_res.feedback_notes
            )
            db.add(val_model)

        total_duration = round(time.time() - start_time, 2)

        # Add Generation Session
        session_record = GenerationSession(
            paper_id=paper.id,
            user_id=user_id,
            status="Completed",
            steps_log=steps_log,
            duration_seconds=total_duration
        )
        db.add(session_record)
        await db.commit()

        # Reload with questions eager-loaded
        from sqlalchemy.orm import selectinload
        stmt_reload = select(QuestionPaper).options(
            selectinload(QuestionPaper.questions)
        ).where(QuestionPaper.id == paper.id)
        loaded_paper = (await db.execute(stmt_reload)).scalar_one()

        return loaded_paper, steps_log, total_duration
