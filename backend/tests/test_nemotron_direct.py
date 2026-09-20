import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))
load_dotenv(dotenv_path=root_dir / ".env")

from app.services.llm.openrouter_provider import OpenRouterProvider
from app.services.llm.syllabus_analyzer import SyllabusAnalyzer

async def run_direct_test():
    provider = OpenRouterProvider()
    sample_text = """
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
    Classical Encryption Techniques: DES, Strength of DES, Blowfish.
    
    UNIT - II:
    Public Key Cryptography Principles, RSA algorithm, Diffie-Hellman Key Exchange.
    
    UNIT - III:
    Digital Signatures, Kerberos, PGP and S/MIME.
    
    UNIT - IV:
    IP Security (AH, ESP), Web Security (SSL, TLS).
    
    UNIT - V:
    Intruders, Viruses, Firewalls, Intrusion Detection Systems (IDS).
    """

    user_prompt = f"""
Analyze this syllabus text and extract complete academic curriculum structure:

SYLLABUS TEXT:
{sample_text}

Respond ONLY with the JSON object.
"""
    raw = await provider.generate_text(prompt=user_prompt, system_prompt=SyllabusAnalyzer.SYSTEM_PROMPT, max_tokens=4096)
    print("--- RAW TEXT FROM NEMOTRON ---")
    print(raw[:1500])
    print("...")
    print(raw[-500:] if len(raw) > 500 else raw)
    print("--- EXTRACTED JSON ---")
    extracted = provider._extract_json_from_text(raw)
    import pprint
    pprint.pprint(extracted)

if __name__ == "__main__":
    asyncio.run(run_direct_test())
