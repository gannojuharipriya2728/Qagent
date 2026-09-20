import re
from typing import List, Dict, Any, Optional

class ChunkResult:
    def __init__(self, chunk_index: int, content: str, page_number: Optional[int], unit_number: Optional[int], topic: Optional[str], token_count: int):
        self.chunk_index = chunk_index
        self.content = content
        self.page_number = page_number
        self.unit_number = unit_number
        self.topic = topic
        self.token_count = token_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_index": self.chunk_index,
            "content": self.content,
            "page_number": self.page_number,
            "unit_number": self.unit_number,
            "topic": self.topic,
            "token_count": self.token_count
        }

class AcademicChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size  # target words/tokens per chunk
        self.chunk_overlap = chunk_overlap

    def _infer_unit_and_topic(self, text: str, default_unit: Optional[int] = None) -> tuple[Optional[int], Optional[str]]:
        # Check for Unit patterns e.g. "Unit 1", "UNIT-I", "Module 3", "Chapter 2"
        unit_match = re.search(r'(?:unit|module|chapter)\s*[-:]?\s*([0-9ivx]+)', text, re.IGNORECASE)
        unit_num = default_unit
        if unit_match:
            val = unit_match.group(1).lower()
            roman_map = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6}
            if val in roman_map:
                unit_num = roman_map[val]
            elif val.isdigit():
                unit_num = int(val)

        # Extract top heading or topic
        topic = None
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines[:3]:
            # If line is short and looks like a heading
            if 3 < len(line) < 80 and not line.endswith('.'):
                topic = line.replace('#', '').strip()
                break
        
        if not topic and lines:
            words = lines[0].split()[:6]
            topic = " ".join(words)

        return unit_num, topic

    def chunk_document(self, pages: List[Dict[str, Any]], default_unit: Optional[int] = None) -> List[ChunkResult]:
        chunks: List[ChunkResult] = []
        chunk_idx = 0

        for page_data in pages:
            page_num = page_data.get("page_number", 1)
            page_text = page_data.get("text", "")
            if not page_text.strip():
                continue

            words = page_text.split()
            if len(words) <= self.chunk_size:
                unit_num, topic = self._infer_unit_and_topic(page_text, default_unit)
                chunks.append(ChunkResult(
                    chunk_index=chunk_idx,
                    content=page_text.strip(),
                    page_number=page_num,
                    unit_number=unit_num,
                    topic=topic,
                    token_count=len(words)
                ))
                chunk_idx += 1
            else:
                # Sliding window chunking
                start = 0
                while start < len(words):
                    end = min(start + self.chunk_size, len(words))
                    chunk_words = words[start:end]
                    chunk_text = " ".join(chunk_words)
                    
                    unit_num, topic = self._infer_unit_and_topic(chunk_text, default_unit)
                    chunks.append(ChunkResult(
                        chunk_index=chunk_idx,
                        content=chunk_text.strip(),
                        page_number=page_num,
                        unit_number=unit_num,
                        topic=topic,
                        token_count=len(chunk_words)
                    ))
                    chunk_idx += 1

                    if end == len(words):
                        break
                    start += (self.chunk_size - self.chunk_overlap)

        return chunks
