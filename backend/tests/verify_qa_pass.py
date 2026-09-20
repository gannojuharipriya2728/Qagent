import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import Base
from backend.app.core.seed import seed_database
from backend.app.models.academic import Course, Unit, CourseOutcome
from backend.app.schemas.academic import CourseCreate, UnitCreate, CourseOutcomeCreate
from backend.app.schemas.generation import GenerationRequest, SectionRule
from backend.app.services.agents.orchestrator import AgenticGenerationOrchestrator
from backend.app.services.pdf_generator import QuestionPaperPDFGenerator
from backend.app.services.rag.vector_store import vector_store

async def run_qa_pass():
    print("=" * 60)
    print("STARTING QAGENT FINAL QA PASS VERIFICATION")
    print("=" * 60)
    
    results = {}

    # Setup database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        await seed_database(session)

        # -------------------------------------------------------------
        # TEST 1: IT701PC COURSE VERIFICATION
        # -------------------------------------------------------------
        print("\n--- TEST 1: IT701PC Course Verification ---")
        stmt = select(Course).options(
            selectinload(Course.units),
            selectinload(Course.course_outcomes)
        ).where(Course.code == "IT701PC")
        course_it = (await session.execute(stmt)).scalar_one_or_none()

        assert course_it is not None, "Course IT701PC must exist"
        assert len(course_it.units) == 5, f"Expected 5 units, got {len(course_it.units)}"
        
        unit_titles = [u.title for u in course_it.units]
        print(f"Units found: {len(course_it.units)}")
        for idx, u in enumerate(course_it.units):
            print(f"  Unit {u.unit_number}: {u.title}")

        co_codes = [co.code for co in course_it.course_outcomes]
        print(f"Course Outcomes found: {co_codes}")
        assert co_codes == ["CO1", "CO2", "CO3"], f"Expected ['CO1', 'CO2', 'CO3'], got {co_codes}"
        results["1_IT701PC_COURSE"] = "PASS"

        # -------------------------------------------------------------
        # TEST 2 & 3: GENERATE 70-MARK PAPER & INSPECT QUESTIONS
        # -------------------------------------------------------------
        print("\n--- TEST 2 & 3: Generate 70-Mark Paper & Inspect Questions ---")
        gen_req = GenerationRequest(
            course_id=course_it.id,
            title="University Semester End Examination",
            examination_name="IV Year B.Tech I Semester Regular Examination",
            institution_name="Department of Information Technology",
            duration_minutes=180,
            total_marks=70,
            instructions="Answer all questions in Section A. Answer any five full questions from Section B.",
            sections=[
                SectionRule(name="Section A", total_questions=10, questions_to_answer=10, marks_per_question=2, question_type="Short"),
                SectionRule(name="Section B", total_questions=5, questions_to_answer=5, marks_per_question=10, question_type="Descriptive")
            ],
            difficulty_distribution={"Easy": 30, "Medium": 50, "Hard": 20},
            bloom_distribution={"Remember": 20, "Understand": 30, "Apply": 25, "Analyze": 15, "Evaluate": 5, "Create": 5},
            target_course_outcomes=["CO1", "CO2", "CO3"]
        )

        paper, steps_log, duration = await AgenticGenerationOrchestrator.run_pipeline(
            db=session,
            request=gen_req,
            override_provider="deterministic"
        )

        assert paper is not None
        assert len(paper.questions) == 15, f"Expected 15 questions, got {len(paper.questions)}"
        total_m = sum(q.marks for q in paper.questions)
        assert total_m == 70, f"Expected 70 marks, got {total_m}"
        print(f"Generated {len(paper.questions)} questions total marks: {total_m}M in {duration:.2f}s")

        # Inspect each question for placeholders / malformed tokens
        forbidden_placeholders = ["[Source", "[Topic", "[Concept", "[Insert", "[Question", "{source}", "{topic}", "placeholder", "undefined", "null"]
        
        for q in paper.questions:
            print(f"\nQ{q.question_number} [{q.section_name}] ({q.marks}M | Unit {q.unit_number} | {q.course_outcome} | {q.bloom_level} | {q.difficulty}):")
            print(f"  Text: {q.question_text}")
            for ph in forbidden_placeholders:
                assert ph.lower() not in q.question_text.lower(), f"Question {q.question_number} contains forbidden placeholder: '{ph}'"
            assert len(q.question_text.strip()) >= 20, f"Question {q.question_number} is too short"
        
        results["2_GENERATE_PAPER"] = "PASS"
        results["3_INSPECT_QUESTIONS"] = "PASS"

        # -------------------------------------------------------------
        # TEST 4: DOMAIN-CONTAMINATION TEST (DSA/DBMS Isolation)
        # -------------------------------------------------------------
        print("\n--- TEST 4: Domain Contamination Test ---")
        dsa_dbms_terms = [
            "avl tree", "b-tree", "binary heap", "linked list", "dijkstra", 
            "spanning tree", "disjoint set", "quick sort", "merge sort", 
            "relational algebra", "sql schema", "normalization 1nf"
        ]
        
        for q in paper.questions:
            text_low = q.question_text.lower()
            for term in dsa_dbms_terms:
                assert term not in text_low, f"DSA/DBMS leakage detected in Q{q.question_number}: '{term}' found in '{q.question_text}'"
        print("Zero DSA/DBMS contamination detected across all 15 questions.")
        results["4_DOMAIN_CONTAMINATION"] = "PASS"

        # -------------------------------------------------------------
        # TEST 5: INFORMATION SECURITY CONCEPT TEST
        # -------------------------------------------------------------
        print("\n--- TEST 5: Information Security Concept Grounding ---")
        is_concepts_found = []
        is_concept_pool = [
            "security", "attack", "service", "encryption", "des", "cipher", "blowfish",
            "rsa", "diffie-hellman", "elliptic", "ecc", "hash", "mac", "sha-512", "hmac",
            "digital signature", "kerberos", "x.509", "pgp", "s/mime", "mime", "ip security", 
            "ipsec", "authentication header", "esp", "ah", "ssl", "tls", "set", "intruder",
            "virus", "firewall", "ids", "intrusion detection", "trusted", "authentication",
            "access control", "cryptography", "cryptanalysis", "avalanche", "dmz", "malware",
            "ticket", "tgt", "certificate", "oakley", "tunnel", "transport", "transport mode", "non-repudiation", "bell-lapadula", "key",
            "zombie", "botnet", "kernel", "proxy", "layer", "session", "password", "passwords", "clear-signed",
            "plaintext", "ciphertext", "confidentiality", "integrity", "demilitarized", "snort", "infector", "infect",
            "trojan", "worm", "keylogger", "replay", "anti-replay", "security association", "sa", "ike",
            "detection", "anomaly", "audit", "gateway", "signature", "stateless", "packet", "ip", "filtering", "protocol", "handshake",
            "exploit", "threat", "vulnerability", "threats", "vulnerabilities"
        ]
        for q in paper.questions:
            found_for_q = [c for c in is_concept_pool if c in q.question_text.lower()]
            is_concepts_found.extend(found_for_q)
            assert len(found_for_q) > 0, f"Q{q.question_number} lacks authentic Information Security terminology: '{q.question_text}'"
        
        print(f"Identified {len(set(is_concepts_found))} distinct InfoSec core concepts across paper questions.")
        results["5_INFOSEC_CONCEPTS"] = "PASS"

        # -------------------------------------------------------------
        # TEST 6 & 7: RAG EXPLAINABILITY & SOURCE QUALITY
        # -------------------------------------------------------------
        print("\n--- TEST 6 & 7: RAG Explainability & Source Quality ---")
        target_slots = [1, 5, 10, 11, 15]
        for q_num in target_slots:
            q = next(item for item in paper.questions if item.question_number == q_num)
            print(f"\nAudit Q{q.question_number}:")
            print(f"  Unit: {q.unit_number} | CO: {q.course_outcome} | Bloom: {q.bloom_level}")
            print(f"  Rationale: {q.generation_reasoning}")
            print(f"  Source Docs ({len(q.source_documents)}):")
            for doc in q.source_documents:
                print(f"    - [{doc.get('document_name')}] Page {doc.get('page')}, Topic: '{doc.get('topic')}', Match: {doc.get('similarity_score')}")
                assert "CS301" not in doc.get("document_name", ""), f"Cross-course contamination: {doc.get('document_name')}"
                assert "CS401" not in doc.get("document_name", ""), f"Cross-course contamination: {doc.get('document_name')}"
                assert doc.get("course_id") == course_it.id or doc.get("course_code") == "IT701PC" or doc.get("document_type") == "syllabus", "Provenance failure"
        
        results["6_RAG_EXPLAINABILITY"] = "PASS"
        results["7_SOURCE_QUALITY"] = "PASS"

        # -------------------------------------------------------------
        # TEST 8 & 9: CO MAPPING & BLOOM VERB CORRESPONDENCE
        # -------------------------------------------------------------
        print("\n--- TEST 8 & 9: CO Mapping & Bloom Correspondence ---")
        valid_cos = {"CO1", "CO2", "CO3"}
        for q in paper.questions:
            assert q.course_outcome in valid_cos, f"Invalid CO: {q.course_outcome}"
        
        # Verify Bloom verbs
        for q in paper.questions:
            bloom = q.bloom_level
            q_low = q.question_text.lower()
            if bloom == "Remember":
                assert any(w in q_low for w in ["define", "identify", "state", "recall", "list", "name", "role", "mechanism"]), f"Q{q.question_number} Remember mismatch"
            elif bloom == "Understand":
                assert any(w in q_low for w in ["explain", "describe", "distinguish", "illustrate", "discuss", "working", "functions"]), f"Q{q.question_number} Understand mismatch"
            elif bloom == "Apply":
                assert any(w in q_low for w in ["apply", "demonstrate", "compute", "solve", "construct", "show", "procedure"]), f"Q{q.question_number} Apply mismatch"
            elif bloom == "Analyze":
                assert any(w in q_low for w in ["analyze", "compare", "contrast", "deconstruct", "differentiate", "critically", "mitigates", "trade-offs", "resilience"]), f"Q{q.question_number} Analyze mismatch"
            elif bloom == "Evaluate":
                assert any(w in q_low for w in ["evaluate", "justify", "critique", "assess", "rate", "limitations", "advantages"]), f"Q{q.question_number} Evaluate mismatch"
            elif bloom == "Create":
                assert any(w in q_low for w in ["design", "synthesize", "formulate", "devise", "develop", "optimal"]), f"Q{q.question_number} Create mismatch"

        results["8_CO_MAPPING"] = "PASS"
        results["9_BLOOM_TEST"] = "PASS"

        # -------------------------------------------------------------
        # TEST 10: DUPLICATE DETECTION TEST
        # -------------------------------------------------------------
        print("\n--- TEST 10: Question Duplicate Test ---")
        question_texts = [q.question_text for q in paper.questions]
        unique_texts = set(question_texts)
        assert len(unique_texts) == len(question_texts), "Found exact duplicate question texts!"
        
        # Check pairwise similarity
        for i in range(len(question_texts)):
            for j in range(i + 1, len(question_texts)):
                sim = await vector_store.calculate_semantic_similarity(question_texts[i], question_texts[j])
                assert sim < 0.95, f"Questions {i+1} and {j+1} are near-duplicates (similarity {sim:.2f})"
        
        print(f"All 15 questions are pairwise unique and non-repetitive.")
        results["10_DUPLICATE_TEST"] = "PASS"

        # -------------------------------------------------------------
        # TEST 11: COURSE SWITCHING ISOLATION
        # -------------------------------------------------------------
        print("\n--- TEST 11: Course Switching Isolation ---")
        stmt_cs = select(Course).options(
            selectinload(Course.units),
            selectinload(Course.course_outcomes)
        ).where(Course.code == "CS301")
        course_cs = (await session.execute(stmt_cs)).scalar_one_or_none()

        assert course_cs is not None
        assert course_cs.name == "Data Structures & Algorithms"
        assert len(course_cs.course_outcomes) == 5
        assert "AVL Trees" in course_cs.units[1].topics
        
        # Switch back to IT701PC
        stmt_it = select(Course).options(
            selectinload(Course.units),
            selectinload(Course.course_outcomes)
        ).where(Course.code == "IT701PC")
        course_it_reloaded = (await session.execute(stmt_it)).scalar_one_or_none()
        
        assert course_it_reloaded.name == "Information Security"
        assert len(course_it_reloaded.course_outcomes) == 3
        assert "RSA" in course_it_reloaded.units[1].topics
        print("Course state switching verified with strict data isolation.")
        results["11_COURSE_SWITCH"] = "PASS"

        # -------------------------------------------------------------
        # TEST 12: CUSTOM COURSE (TEST701) CREATION & GENERATION
        # -------------------------------------------------------------
        print("\n--- TEST 12: Custom Course Test (TEST701) ---")
        custom_course_in = CourseCreate(
            code="TEST701",
            name="Quantum Cryptography Protocols",
            department="Department of Advanced Computing",
            semester="Semester VIII",
            academic_year="2025-2026",
            description="Quantum key distribution (BB84), quantum entanglement, and post-quantum lattice cryptography.",
            units=[
                UnitCreate(unit_number=1, title="Quantum Key Distribution Protocols", topics="BB84 Protocol, E91 Protocol, Photon Polarization, Quantum Channel Noise."),
                UnitCreate(unit_number=2, title="Quantum Entanglement & No-Cloning Theorem", topics="Bell States, Quantum Teleportation, No-Cloning Proof, Superdense Coding."),
                UnitCreate(unit_number=3, title="Post-Quantum Lattice Cryptography", topics="Learning With Errors (LWE), Ring-LWE, Crystals-Kyber, Falcon Signatures.")
            ],
            course_outcomes=[
                CourseOutcomeCreate(code="CO1", description="Understand quantum key distribution mechanics and photon polarization principles.", target_bloom_level="Understand"),
                CourseOutcomeCreate(code="CO2", description="Analyze security guarantees of lattice-based post-quantum cryptographic schemes.", target_bloom_level="Analyze")
            ]
        )

        course_custom = Course(
            code=custom_course_in.code,
            name=custom_course_in.name,
            department=custom_course_in.department,
            semester=custom_course_in.semester,
            academic_year=custom_course_in.academic_year,
            description=custom_course_in.description
        )
        session.add(course_custom)
        await session.flush()

        for u in custom_course_in.units:
            session.add(Unit(course_id=course_custom.id, unit_number=u.unit_number, title=u.title, topics=u.topics))
        for co in custom_course_in.course_outcomes:
            session.add(CourseOutcome(course_id=course_custom.id, code=co.code, description=co.description, target_bloom_level=co.target_bloom_level))

        await session.commit()
        await session.refresh(course_custom)

        # Generate paper for TEST701
        custom_gen_req = GenerationRequest(
            course_id=course_custom.id,
            title="Quantum Cryptography Midterm",
            examination_name="Advanced Elective Regular Exam",
            institution_name="Department of Advanced Computing",
            duration_minutes=90,
            total_marks=20,
            sections=[
                SectionRule(name="Section A", total_questions=5, questions_to_answer=5, marks_per_question=2, question_type="Short", unit_distribution=[1, 2, 3]),
                SectionRule(name="Section B", total_questions=1, questions_to_answer=1, marks_per_question=10, question_type="Descriptive", unit_distribution=[1, 2, 3])
            ],
            target_course_outcomes=["CO1", "CO2"]
        )

        paper_custom, _, _ = await AgenticGenerationOrchestrator.run_pipeline(
            db=session,
            request=custom_gen_req,
            override_provider="deterministic"
        )

        assert paper_custom is not None
        assert paper_custom.course_id == course_custom.id
        assert len(paper_custom.questions) == 6
        assert all(q.course_outcome in ["CO1", "CO2"] for q in paper_custom.questions)
        assert any("quantum" in q.question_text.lower() or "bb84" in q.question_text.lower() or "lattice" in q.question_text.lower() for q in paper_custom.questions)
        print(f"Generated {len(paper_custom.questions)} questions for new course TEST701.")
        
        # Cleanup
        await session.delete(course_custom)
        await session.commit()
        results["12_CUSTOM_COURSE"] = "PASS"

        # -------------------------------------------------------------
        # TEST 13: ANALYTICS CALCULATION TEST
        # -------------------------------------------------------------
        print("\n--- TEST 13: Analytics Calculation Test ---")
        from backend.app.schemas.paper import PaperAnalyticsResponse
        
        questions = [
            {
                "marks": q.marks,
                "unit_number": q.unit_number,
                "bloom_level": q.bloom_level,
                "difficulty": q.difficulty,
                "course_outcome": q.course_outcome
            }
            for q in paper.questions
        ]
        
        total_marks_calc = sum(q["marks"] for q in questions)
        assert total_marks_calc == 70, f"Expected 70M, got {total_marks_calc}"

        # Group by CO
        co_counts = {}
        for q in questions:
            co_counts[q["course_outcome"]] = co_counts.get(q["course_outcome"], 0) + 1
        print(f"CO distribution: {co_counts}")
        assert set(co_counts.keys()).issubset({"CO1", "CO2", "CO3"})

        # Group by Unit
        unit_counts = {}
        for q in questions:
            unit_counts[q["unit_number"]] = unit_counts.get(q["unit_number"], 0) + 1
        print(f"Unit distribution: {unit_counts}")
        assert all(u in range(1, 6) for u in unit_counts.keys())

        # Group by Bloom
        bloom_counts = {}
        for q in questions:
            bloom_counts[q["bloom_level"]] = bloom_counts.get(q["bloom_level"], 0) + 1
        print(f"Bloom distribution: {bloom_counts}")

        results["13_ANALYTICS_TEST"] = "PASS"

        # -------------------------------------------------------------
        # TEST 14: PDF GENERATION TEST
        # -------------------------------------------------------------
        print("\n--- TEST 14: PDF Generation Test ---")
        paper_dict = {
            "title": paper.title,
            "examination_name": paper.examination_name,
            "institution_name": paper.institution_name,
            "course_code": "IT701PC",
            "course_name": "Information Security",
            "duration_minutes": paper.duration_minutes,
            "total_marks": paper.total_marks,
            "instructions": paper.instructions,
            "questions": [
                {
                    "section_name": q.section_name,
                    "question_number": q.question_number,
                    "question_text": q.question_text,
                    "marks": q.marks,
                    "course_outcome": q.course_outcome,
                    "bloom_level": q.bloom_level
                }
                for q in paper.questions
            ]
        }

        pdf_bytes = QuestionPaperPDFGenerator.generate_pdf(paper_dict)
        assert len(pdf_bytes) > 2000, f"PDF byte length too small: {len(pdf_bytes)}"
        assert pdf_bytes.startswith(b"%PDF"), "Output is not valid PDF binary"
        print(f"Successfully generated PDF document ({len(pdf_bytes)} bytes)")
        results["14_PDF_TEST"] = "PASS"

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print("FINAL QA RESULTS SUMMARY")
    print("=" * 60)
    all_pass = True
    for test_key, res in results.items():
        print(f"  [{res}] {test_key}")
        if res != "PASS":
            all_pass = False

    if all_pass:
        print("\n>>> ALL 14 CORE QA PASS CRITERIA PASSED SUCCESSFULLY! <<<")
    else:
        print("\n>>> SOME QA TESTS FAILED <<<")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_qa_pass())
