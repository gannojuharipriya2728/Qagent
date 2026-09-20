import asyncio
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))
load_dotenv(dotenv_path=root_dir / ".env")

from app.services.llm.openrouter_provider import OpenRouterProvider
from app.services.llm.syllabus_analyzer import SyllabusAnalyzer

async def main():
    sample_syllabus_text = """
    JAWAHARLAL NEHRU TECHNOLOGICAL UNIVERSITY HYDERABAD
    IV Year B.Tech. IT I-Sem
    COURSE CODE: IT701PC
    COURSE TITLE: INFORMATION SECURITY
    
    Course Outcomes:
    CO1: Demonstrate the knowledge of cryptography, network security concepts and applications.
    CO2: Ability to apply security principles in system design.
    CO3: Ability to identify and investigate vulnerabilities and security threats.
    
    UNIT - I:
    Security Attacks: Interruption, Interception, Modification and Fabrication.
    Security Services: Confidentiality, Authentication, Integrity, Non-repudiation, Access Control and Availability.
    Classical Encryption Techniques: DES, Strength of DES, Blowfish.
    
    UNIT - II:
    Public Key Cryptography Principles, RSA algorithm, Key Management, Diffie-Hellman Key Exchange.
    Message Authentication and Hash Functions: MACs, SHA-512, HMAC.
    
    UNIT - III:
    Digital Signatures, Kerberos, X.509 Directory Authentication Service.
    Email Security: Pretty Good Privacy (PGP) and S/MIME.
    
    UNIT - IV:
    IP Security: Overview, IP Security Architecture, AH, ESP.
    Web Security: SSL, TLS, SET.
    
    UNIT - V:
    Intruders, Viruses and related threats, Firewalls, Firewall Design Principles, Intrusion Detection Systems (IDS).
    """

    provider = OpenRouterProvider()
    t0 = time.time()
    print("Calling OpenRouter with syllabus prompt...")
    
    user_prompt = f"""Extract the structured curriculum strictly according to this JSON schema:
{{
  "course": {{
    "code": "Course Code",
    "title": "Course Title",
    "department": "Department",
    "semester": "Semester",
    "academic_year": "Academic Year",
    "description": "Short Description",
    "objectives": ["Obj 1", "Obj 2"]
  }},
  "units": [
    {{
      "unit_number": 1,
      "title": "Unit Title",
      "topics": ["Topic 1", "Topic 2"],
      "description": "Short description of unit"
    }}
  ],
  "course_outcomes": [
    {{
      "code": "CO1",
      "description": "CO Description",
      "bloom_level": "Understand",
      "bloom_source": "explicit or inferred"
    }}
  ]
}}

SYLLABUS TEXT:
{sample_syllabus_text}

Output ONLY the JSON object. Do not include markdown preamble or commentary.
"""

    raw_text = await provider.generate_text(
        prompt=user_prompt,
        system_prompt=SyllabusAnalyzer.SYSTEM_PROMPT,
        temperature=0.1,
        max_tokens=4096
    )
    dt = time.time() - t0
    print(f"Received raw text in {dt:.2f}s:")
    print("-------------------- RAW --------------------")
    print(raw_text[:1500])
    print("---------------------------------------------")
    
    parsed = provider._extract_json_from_text(raw_text)
    print("-------------------- PARSED -----------------")
    import pprint
    pprint.pprint(parsed)
    print("---------------------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
