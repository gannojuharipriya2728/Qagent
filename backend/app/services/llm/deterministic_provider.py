import re
import json
import random
from typing import Dict, Any, Optional, List
from app.services.llm.base import BaseLLMProvider

BLOOM_ACTION_VERBS = {
    "Remember": ["Define", "State the core properties of", "Identify", "Recall the key principles of"],
    "Understand": ["Explain in detail", "Describe the working of", "Discuss the operational role of", "Illustrate"],
    "Apply": ["Demonstrate the practical application of", "Compute and demonstrate", "Apply the principles of", "Construct a model for"],
    "Analyze": ["Critically analyze", "Analyze the security vulnerabilities of", "Deconstruct the operation of", "Differentiate between the mechanisms of"],
    "Evaluate": ["Justify the operational necessity of", "Evaluate the effectiveness of", "Assess the architectural resilience of", "Critique"],
    "Create": ["Design a comprehensive system utilizing", "Formulate an optimal security framework for", "Devise a robust architecture incorporating", "Synthesize"]
}

class DeterministicAcademicProvider(BaseLLMProvider):
    """
    High-quality offline academic question generator that extracts grounded concepts
    from retrieved syllabus/textbook chunks, applying pedagogical Bloom's verbs and CO mappings.
    """
    
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.4) -> str:
        return "Deterministic academic text grounded in syllabus context."

    def _extract_key_concepts(self, context: str) -> List[str]:
        if not context:
            return []
        
        # 1. Clean non-ASCII characters, isolate sentence boundaries, and normalize whitespace
        sanitized_context = re.sub(r'[^\x20-\x7E\n]', ' ', context)
        # Prevent capitalized start of new sentence from gluing to previous word
        sanitized_context = re.sub(r'[\.\?\!;]\s+', '\n', sanitized_context)
        sanitized_context = re.sub(r'[ \t]+', ' ', sanitized_context)
        
        noise_patterns = [
            r'past examination reference',
            r'section [ab]',
            r'short questions',
            r'descriptive questions',
            r'course:\s*',
            r'jntuh',
            r'page\s*\d+',
            r'figure\s*\d+',
            r'table\s*\d+',
            r'marks\]',
            r'^\d+[\.\)]',
            r'^[a-z][\.\)]',
            r'mod [a-z0-9]+',
            r'=\s*\d+',
            r'gcd\(',
            r'phi\(',
            r'xor',
            r'window of size',
            r'between any two',
            r'[<>=_\\~|\^]',
            r'is detected',
            r'service reports',
            r'summary of',
            r'given below',
            r'program modification',
            r'hence find',
            r'allows\b'
        ]
        
        stop_words = {
            "unit", "chapter", "page", "table", "figure", "source", "curriculum",
            "syllabus", "topics", "section", "question", "retrieved", "context",
            "course", "subject", "marks", "bloom", "outcome", "easy", "medium", "hard",
            "past question paper", "past examination reference", "the nature", "nature",
            "firstly", "secondly", "utility", "secure", "requirements", "overview",
            "principles", "techniques", "mechanisms", "applications", "characteristics",
            "functions", "operations", "communication", "implementation", "features",
            "according", "factor", "phases", "it", "this", "that", "these", "those",
            "retrieved academic context", "academic context", "output json schema",
            "specifications", "target bloom level", "question number", "target course outcome",
            "question type", "question_type", "section name", "question text", "source topics",
            "reasoning", "complete question text"
        }
        
        transition_words = {
            "it", "this", "that", "these", "those", "there", "here", "when", "where",
            "which", "while", "then", "thus", "hence", "also", "such", "various",
            "following", "another", "used", "uses", "gives", "shows", "a", "an", "the",
            "in", "on", "at", "to", "for", "with", "by", "of", "and", "or"
        }
        
        concepts = []
        
        # 1. Extract high-confidence topics from source metadata headers
        topic_matches = re.findall(r'Topic:\s*([^\]\|\n]+)', sanitized_context)
        for tm in topic_matches:
            clean_tm = tm.strip(" ,.-:#*()[]{}'\"")
            if 3 < len(clean_tm) < 80 and not any(re.search(pat, clean_tm, re.IGNORECASE) for pat in noise_patterns):
                for sub in re.split(r'[,;&/]', clean_tm):
                    sub_c = sub.strip(" ,.-:#*()[]{}'\"")
                    if 3 < len(sub_c) < 50 and sub_c.lower() not in stop_words:
                        concepts.append(sub_c)

        # 2. Extract structured topics preceding colons (standard syllabus headings)
        colon_headers = re.findall(r'(?:^|\n)([A-Z][a-zA-Z0-9\s\/\-]{2,45}):\s*', sanitized_context)
        for ch in colon_headers:
            clean_ch = re.sub(r'^(UNIT|Section|Chapter|Part)\s+[IVXLCDM\d]+\s*', '', ch, flags=re.IGNORECASE).strip(" ,.-:#*()[]{}'\"")
            if 3 < len(clean_ch) < 45 and not any(re.search(pat, clean_ch, re.IGNORECASE) for pat in noise_patterns):
                if clean_ch.lower() not in stop_words and not clean_ch.lower().startswith(("unit", "chapter", "section", "part")):
                    concepts.append(clean_ch)

        # 3. Extract capitalized multi-word terms & acronyms
        terms = re.findall(r'\b[A-Z][a-zA-Z0-9\-]*(?:\s+[A-Z][a-zA-Z0-9\-]*)+\b', sanitized_context)
        for t in terms:
            clean_t = t.strip(" ,.-:#*()[]{}'\"")
            if 4 < len(clean_t) < 50 and not any(re.search(pat, clean_t, re.IGNORECASE) for pat in noise_patterns):
                words = clean_t.split()
                if words and words[0].lower() not in transition_words and words[-1].lower() not in transition_words:
                    if clean_t.lower() not in stop_words and not clean_t.lower().startswith(("unit ", "chapter ", "section ")):
                        concepts.append(clean_t)

        # 4. Standard domain acronyms and core security concepts if present in context
        domain_terms = [
            "DES", "Blowfish", "RSA", "Diffie-Hellman", "ECC", "SHA-512", "HMAC", "Kerberos",
            "X.509", "PGP", "S/MIME", "IPsec", "AH", "ESP", "SSL", "TLS", "SET", "IDS",
            "DMZ", "DAC", "MAC", "Firewall", "Intrusion Detection", "Digital Signature",
            "Public Key Cryptography", "Message Authentication", "Hash Functions",
            "Access Control", "Security Attacks", "Classical Encryption", "Authentication Header",
            "AVL Tree", "B-Tree", "Binary Heap", "Dijkstra", "BCNF", "3NF", "2PL",
            "BB84", "Quantum Key Distribution", "Lattice Cryptography"
        ]
        for term in domain_terms:
            if re.search(r'\b' + re.escape(term) + r'\b', sanitized_context, re.IGNORECASE):
                concepts.append(term)

        # Deduplicate & filter
        unique = []
        for term in domain_terms:
            if re.search(r'\b' + re.escape(term) + r'\b', sanitized_context, re.IGNORECASE) and term not in unique:
                unique.append(term)

        for c in concepts:
            c_clean = re.sub(r'^[0-9\.\-\*\#\s\(\)a-zA-Z]+[\.\)]', '', c).strip(" ,.-:#*'")
            c_clean = re.sub(r'[\[\]\{\}\(\)]', '', c_clean).strip()
            c_clean = re.sub(r'\s+', ' ', c_clean).strip()
            
            # Strip trailing/leading transition words
            words = c_clean.split()
            while words and words[-1].lower() in transition_words:
                words.pop()
            while words and words[0].lower() in transition_words:
                words.pop(0)
            c_clean = " ".join(words)

            if len(c_clean) >= 3 and c_clean.lower() not in stop_words and c_clean not in unique:
                if not any(sw in c_clean.lower() for sw in ["retrieved academic", "academic context", "output json", "specifications", "downloader", "question type", "question number", "target bloom", "course outcome"]):
                    if not c_clean.lower().startswith(("unit", "chapter", "section", "part")):
                        words = c_clean.split()
                        if all(len(w) > 1 or w in ["A", "I"] for w in words):
                            if any(w[0].isupper() for w in words) and all(w[0].isupper() or w in ["and", "of", "in", "for", "to", "the", "&", "-"] or w.isdigit() for w in words):
                                if not c_clean.lower().startswith(("either", "whether", "and", "or", "to", "for", "with", "case", "captures", "used", "past", "according")):
                                    unique.append(c_clean)

        return unique

    async def generate_json(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        bloom_match = re.search(r'Bloom.*?:\s*([A-Za-z]+)', prompt, re.IGNORECASE)
        co_match = re.search(r'Course Outcome.*?:\s*(CO[0-9]+)', prompt, re.IGNORECASE)
        marks_match = re.search(r'Marks.*?:\s*([0-9]+)', prompt, re.IGNORECASE)
        unit_match = re.search(r'Unit.*?:\s*([0-9]+)', prompt, re.IGNORECASE)
        difficulty_match = re.search(r'Difficulty.*?:\s*([A-Za-z]+)', prompt, re.IGNORECASE)
        qtype_match = re.search(r'Question Type.*?:\s*([A-Za-z\s]+)', prompt, re.IGNORECASE)
        course_match = re.search(r'Course.*?:\s*([^\n]+)', prompt, re.IGNORECASE)

        bloom_level = bloom_match.group(1).capitalize() if bloom_match else "Understand"
        if bloom_level not in BLOOM_ACTION_VERBS:
            bloom_level = "Understand"
            
        co = co_match.group(1).upper() if co_match else "CO1"
        marks = int(marks_match.group(1)) if marks_match else 10
        unit = int(unit_match.group(1)) if unit_match else 1
        difficulty = difficulty_match.group(1).capitalize() if difficulty_match else "Medium"
        qtype = qtype_match.group(1).strip() if qtype_match else "Descriptive"
        course_name = course_match.group(1).strip() if course_match else "Academic Course"

        context = ""
        context_match = re.search(r'RETRIEVED ACADEMIC CONTEXT:\s*([\s\S]*?)(?:OUTPUT JSON SCHEMA:|$)', prompt, re.IGNORECASE)
        if context_match:
            context = context_match.group(1).strip()
        else:
            context = prompt

        concepts = self._extract_key_concepts(context)
        
        # Select distinct concepts for this question slot
        if concepts:
            random.shuffle(concepts)
            primary_concept = concepts[0]
            secondary_concept = concepts[1] if len(concepts) > 1 else f"{primary_concept} Architecture"
        else:
            primary_concept = f"Unit {unit} Core Principles"
            secondary_concept = f"Unit {unit} Advanced Systems"

        verb_list = BLOOM_ACTION_VERBS.get(bloom_level, BLOOM_ACTION_VERBS["Understand"])
        verb = random.choice(verb_list)

        # Well-formed, pedagogically sound questions
        templates_short = [
            f"{verb} {primary_concept} and state its significance in {course_name}.",
            f"{verb} {primary_concept} and describe its key operational characteristics.",
            f"{verb} {primary_concept} and outline its practical applications."
        ]

        templates_medium = [
            f"{verb} {primary_concept}. Provide an illustrative explanation and discuss its practical implementation in {course_name}.",
            f"{verb} {primary_concept}. Analyze its primary advantages, limitations, and operational trade-offs."
        ]

        templates_long = [
            f"(a) {verb} {primary_concept}.\n(b) Compare and contrast {primary_concept} with {secondary_concept} in terms of operational complexity, architectural guarantees, and implementation trade-offs.",
            f"(a) {verb} {primary_concept}.\n(b) Critically evaluate the resilience and performance of {secondary_concept} under adversarial conditions.",
            f"(a) {verb} {primary_concept}.\n(b) Design an optimal architecture incorporating {secondary_concept} to resolve real-world deployment challenges."
        ]

        if marks <= 2:
            question_text = random.choice(templates_short)
        elif marks <= 5:
            question_text = random.choice(templates_medium)
        else:
            question_text = random.choice(templates_long)

        source_topics = [primary_concept]
        if secondary_concept and secondary_concept != primary_concept:
            source_topics.append(secondary_concept)

        return {
            "question_text": question_text,
            "unit": unit,
            "marks": marks,
            "difficulty": difficulty,
            "bloom_level": bloom_level,
            "course_outcome": co,
            "question_type": qtype,
            "source_topics": source_topics,
            "reasoning": f"Synthesized using academic concept '{primary_concept}' grounded in retrieved {course_name} resources with {bloom_level} Bloom verb '{verb}' aligned to {co}."
        }
