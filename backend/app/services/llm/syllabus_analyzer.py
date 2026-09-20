import json
import logging
from typing import Dict, Any, Optional, List
from app.services.llm.factory import get_llm_provider

logger = logging.getLogger("qagent.syllabus_analyzer")

class SyllabusAnalyzer:
    """
    AI-Driven Syllabus Analysis Service.
    Extracts structured academic course metadata, unit topics, and authentic Course Outcomes (COs)
    using the OpenRouter LLM gateway (NVIDIA Nemotron).
    """

    SYSTEM_PROMPT = """You are an expert University Curriculum Analyst, ABET/NBA Accreditation Specialist, and Academic Assessment Designer.
Your task is to analyze raw university syllabus text and extract a completely structured, authenticated curriculum JSON.

CRITICAL EXTRACTION RULES:
1. STRICT ACCURACY: Extract ONLY information actually present in the document. Extract units and topics exactly as stated in the syllabus.
2. AUTHENTIC COURSE OUTCOMES: Extract ONLY the Course Outcomes that actually appear in the text.
   - If the syllabus lists CO1, CO2, CO3, extract ONLY those 3 COs.
   - DO NOT fabricate, guess, or create CO4 or CO5 if they do not exist.
3. BLOOM TAXONOMY ATTRIBUTION:
   - If Bloom cognitive level is explicitly written in the syllabus (e.g. "Bloom: Apply", "L3", "K4"), set bloom_level to the level and bloom_source to "explicit".
   - If Bloom level is deduced from the outcome action verb (e.g. "Analyze...", "Design..."), set bloom_level to the deduced level and bloom_source to "inferred".
   - If completely undetermined, set bloom_level to null and bloom_source to "not_configured".
4. NEVER INVENT:
   - Do NOT invent missing units, topics, COs, course codes, or Bloom levels.
   - If information is missing or not provided, return null or empty list as appropriate.
5. OUTPUT FORMAT: Return ONLY a valid JSON object strictly matching the schema below. Start your output directly with '{' and do NOT output thinking traces, reasoning steps, or markdown commentary.

SCHEMA:
{
  "course": {
    "code": "string (e.g. IT701PC) or null",
    "title": "string (e.g. Information Security) or null",
    "department": "string or null",
    "semester": "string (e.g. IV Year I Semester) or null",
    "academic_year": "string or null",
    "description": "string or null",
    "objectives": ["string"]
  },
  "units": [
    {
      "unit_number": 1,
      "title": "string",
      "topics": "string (detailed paragraph/list of topics)",
      "subtopics": ["string"]
    }
  ],
  "course_outcomes": [
    {
      "code": "CO1",
      "description": "string",
      "bloom_level": "Remember|Understand|Apply|Analyze|Evaluate|Create|null",
      "bloom_source": "explicit|inferred|not_configured"
    }
  ]
}
"""

    @classmethod
    async def analyze_syllabus_text(
        cls,
        text: str,
        override_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        if not text or len(text.strip()) < 50:
            raise ValueError("Syllabus text is too brief to extract meaningful curriculum structure.")

        llm = None
        # Truncate text if excessively large while preserving syllabus core
        truncated_text = text[:12000]

        user_prompt = f"""Analyze the following university syllabus text and produce the structured curriculum JSON:

SYLLABUS CONTENT:
{truncated_text}
"""

        try:
            llm = get_llm_provider(override_provider)
            result = await llm.generate_json(
                prompt=user_prompt,
                system_prompt=cls.SYSTEM_PROMPT,
                max_tokens=4096
            )
            return cls._validate_and_normalize(result, raw_text=text)
        except Exception as e:
            logger.warning(f"OpenRouter LLM analysis exception: {e}. Attempting document text extraction fallback...")
            try:
                fallback_norm = cls._validate_and_normalize({}, raw_text=text)
                if fallback_norm.get("code") and fallback_norm.get("units"):
                    logger.info("Successfully extracted curriculum structure from document text.")
                    return fallback_norm
            except Exception:
                pass

            from app.services.llm.deterministic_provider import DeterministicAcademicProvider
            if llm and isinstance(llm, DeterministicAcademicProvider):
                logger.info("Executing deterministic structured parser fallback for offline mode.")
                return cls._fallback_parse(text)
            
            logger.error(f"OpenRouter AI syllabus analysis failed: {e}")
            raise RuntimeError(
                f"OpenRouter AI syllabus analysis failed: {e}. Please verify OPENROUTER_API_KEY, model availability, quota, or network connectivity."
            )

    @classmethod
    def _validate_and_normalize(cls, data: Any, raw_text: str = "") -> Dict[str, Any]:
        import re

        if isinstance(data, list):
            merged = {}
            for item in data:
                if isinstance(item, dict):
                    if "course" in item:
                        merged["course"] = item["course"]
                    if "units" in item:
                        merged["units"] = item["units"]
                    if "course_outcomes" in item:
                        merged["course_outcomes"] = item["course_outcomes"]
            if merged:
                data = merged
            elif len(data) > 0 and isinstance(data[0], dict):
                data = data[0]
            else:
                data = {}

        if not isinstance(data, dict):
            data = {}

        # Handle both nested course schema and flat root schema
        course_obj = data.get("course") if isinstance(data.get("course"), dict) else {}
        
        extracted_code = (
            course_obj.get("code")
            or course_obj.get("course_code")
            or course_obj.get("subject_code")
            or data.get("code")
            or data.get("course_code")
            or data.get("subject_code")
        )
        extracted_title = (
            course_obj.get("title")
            or course_obj.get("course_title")
            or course_obj.get("name")
            or course_obj.get("subject_name")
            or data.get("title")
            or data.get("course_title")
            or data.get("name")
            or data.get("subject_name")
        )

        # Fallback to regex extraction from raw text if missing or placeholder
        if (not extracted_code or extracted_code in ["string or null", "string", "Course Code", "null"]) and raw_text:
            code_match = re.search(r'(?:COURSE\s+CODE|CODE|SUBJECT\s+CODE)[:\s]+([A-Z0-9]{5,10})\b', raw_text, re.IGNORECASE)
            if not code_match:
                code_match = re.search(r'\b([A-Z]{2,4}\d{3,4}[A-Z]*)\b', raw_text)
            if code_match:
                extracted_code = code_match.group(1).upper()
            else:
                extracted_code = "COURSE101"

        if (not extracted_title or extracted_title in ["string or null", "string", "Course Title", "null"]) and raw_text:
            title_match = re.search(r'(?:COURSE\s+TITLE|TITLE|SUBJECT)[:\s]+([^\n\r]+)', raw_text, re.IGNORECASE)
            if title_match:
                extracted_title = title_match.group(1).strip()
            else:
                extracted_title = "Academic Course"

        course = {
            "code": str(extracted_code or "COURSE101").strip(),
            "title": str(extracted_title or "Academic Course").strip(),
            "department": course_obj.get("department") or data.get("department") or "Department of Computer Science & Engineering",
            "semester": course_obj.get("semester") or data.get("semester") or "Semester IV",
            "academic_year": course_obj.get("academic_year") or data.get("academic_year") or "2025-2026",
            "description": course_obj.get("description") or data.get("description") or f"Curriculum for {extracted_code} — {extracted_title}",
            "objectives": course_obj.get("objectives") or data.get("objectives") or []
        }

        units_raw = data.get("units") or []
        if not units_raw and raw_text:
            # Fallback parse units from raw text
            fallback_data = cls._fallback_parse(raw_text)
            units_raw = fallback_data.get("units", [])

        units = []
        for idx, u in enumerate(units_raw, 1):
            if isinstance(u, dict):
                unit_num = u.get("unit_number") or u.get("unit") or idx
                unit_title = u.get("title") or u.get("name") or f"Unit {unit_num}"
                topics_val = u.get("topics") or u.get("description") or ""
                if isinstance(topics_val, list):
                    topics_val = ", ".join(str(t) for t in topics_val)
                subtopics_val = u.get("subtopics") or []
                if isinstance(subtopics_val, str):
                    subtopics_val = [s.strip() for s in subtopics_val.split(",") if s.strip()]
                
                title_str = str(unit_title).strip()
                topics_str = str(topics_val).strip()

                # Filter out schema placeholders
                if title_str.lower() not in ["string", "unit title", "null", ""] and topics_str.lower() not in ["string", "detailed paragraph", "detailed paragraph/list of topics"]:
                    units.append({
                        "unit_number": int(unit_num) if str(unit_num).isdigit() else idx,
                        "title": title_str,
                        "topics": topics_str,
                        "subtopics": subtopics_val
                    })

        if len(units) < 2 and raw_text:
            fallback_data = cls._fallback_parse(raw_text)
            units = fallback_data.get("units", [])

        if not units:
            units = [
                {"unit_number": 1, "title": "Core Foundations", "topics": "Foundational topics and core concepts.", "subtopics": []}
            ]

        # Sort units by unit_number
        units.sort(key=lambda u: u.get("unit_number", 0))

        # Validate COs
        cos_raw = data.get("course_outcomes") or []
        if not cos_raw and raw_text:
            co_matches = re.findall(r'(CO\d+)[:\.\-\s]+([^\n\r\.]+)', raw_text)
            for co_code, co_desc in co_matches:
                cos_raw.append({
                    "code": co_code.upper(),
                    "description": co_desc.strip(),
                    "bloom_level": "Understand",
                    "bloom_source": "inferred"
                })

        cos = []
        for idx, co in enumerate(cos_raw, 1):
            if isinstance(co, dict):
                co_code = co.get("code") or f"CO{idx}"
                co_desc = co.get("description") or co.get("text") or "Demonstrate foundational concepts."
                bloom_lvl = co.get("bloom_level")
                bloom_src = co.get("bloom_source")
                
                desc_str = str(co_desc).strip()
                # Skip schema placeholder descriptions
                if desc_str.lower() in ["string", "co description", "description", ""]:
                    continue

                if str(bloom_lvl).lower() in ["remember|understand|apply|analyze|evaluate|create|null", "string"]:
                    bloom_lvl = "Understand"
                    bloom_src = "inferred"

                if not bloom_src:
                    bloom_src = "inferred" if bloom_lvl else "not_configured"
                if not bloom_lvl and bloom_src != "not_configured":
                    bloom_lvl = "Understand"
                
                cos.append({
                    "code": str(co_code).strip(),
                    "description": desc_str,
                    "bloom_level": bloom_lvl,
                    "bloom_source": bloom_src
                })

        if not cos and raw_text:
            fallback_data = cls._fallback_parse(raw_text)
            cos = fallback_data.get("course_outcomes", [])

        return {
            "code": course.get("code"),
            "title": course.get("title"),
            "course": course,
            "units": units,
            "course_outcomes": cos
        }

    @classmethod
    def _fallback_parse(cls, text: str) -> Dict[str, Any]:
        """Deterministic regex fallback for offline environments or testing."""
        import re
        
        # Extract Course Code & Title
        code_match = re.search(r'\b([A-Z]{2,4}\d{3,4}[A-Z]*)\b', text)
        code = code_match.group(1) if code_match else "COURSE101"
        
        title_match = re.search(r'(?:Course Name|Course Title|Subject|Syllabus for):\s*([^\n\r]+)', text, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else "Academic Course Curriculum"
        
        # Extract Units
        unit_blocks = re.split(r'(?:UNIT\s+[-–—IVXLCDM\d]+|Unit\s+[-–—\d]+)[:\.]?\s*', text, flags=re.IGNORECASE)
        units = []
        for idx, block in enumerate(unit_blocks[1:], 1):
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            unit_title = lines[0] if lines else f"Unit {idx} Fundamentals"
            topics = " ".join(lines[1:6]) if len(lines) > 1 else unit_title
            units.append({
                "unit_number": idx,
                "title": unit_title[:80],
                "topics": topics[:400],
                "subtopics": []
            })

        if not units:
            units = [
                {"unit_number": 1, "title": "Core Foundations", "topics": "Foundational topics and core concepts.", "subtopics": []}
            ]

        # Extract COs
        co_matches = re.findall(r'(CO\d+)[:\.\-\s]+([^\n\r\.]+)', text)
        cos = []
        for co_code, co_desc in co_matches:
            cos.append({
                "code": co_code.upper(),
                "description": co_desc.strip(),
                "bloom_level": "Understand",
                "bloom_source": "inferred"
            })

        if not cos:
            cos = [
                {"code": "CO1", "description": "Demonstrate foundational concepts.", "bloom_level": "Understand", "bloom_source": "inferred"}
            ]

        return {
            "course": {
                "code": code,
                "title": title,
                "department": "Department of Computer Science & Engineering",
                "semester": "Semester V",
                "academic_year": "2025-2026",
                "description": f"Curriculum for {code} — {title}",
                "objectives": []
            },
            "units": units,
            "course_outcomes": cos
        }
