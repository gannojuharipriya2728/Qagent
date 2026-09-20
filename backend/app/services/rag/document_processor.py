import os
import re
from typing import List, Dict, Any
from pypdf import PdfReader
from docx import Document

class ProcessedDocument:
    def __init__(self, full_text: str, pages: List[Dict[str, Any]], metadata: Dict[str, Any]):
        self.full_text = full_text
        self.pages = pages  # [{"page_number": int, "text": str}]
        self.metadata = metadata

class DocumentProcessor:
    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        # Remove null bytes, fix excessive newlines and whitespace
        text = text.replace('\x00', ' ')
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @classmethod
    def process_pdf(cls, file_path: str) -> ProcessedDocument:
        pages = []
        full_text_parts = []
        
        try:
            reader = PdfReader(file_path)
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                cleaned = cls.clean_text(page_text)
                if cleaned:
                    pages.append({"page_number": idx + 1, "text": cleaned})
                    full_text_parts.append(cleaned)
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

        full_text = "\n\n".join(full_text_parts)
        return ProcessedDocument(
            full_text=full_text,
            pages=pages,
            metadata={"page_count": len(pages), "file_type": "pdf"}
        )

    @classmethod
    def process_docx(cls, file_path: str) -> ProcessedDocument:
        pages = []
        full_text_parts = []
        
        try:
            doc = Document(file_path)
            # Estimate pages/sections based on paragraph counts
            current_page_text = []
            page_num = 1
            
            for para in doc.paragraphs:
                text = cls.clean_text(para.text)
                if text:
                    current_page_text.append(text)
                    if len(current_page_text) >= 15:  # ~1 page estimation
                        page_content = "\n".join(current_page_text)
                        pages.append({"page_number": page_num, "text": page_content})
                        full_text_parts.append(page_content)
                        current_page_text = []
                        page_num += 1
            
            if current_page_text:
                page_content = "\n".join(current_page_text)
                pages.append({"page_number": page_num, "text": page_content})
                full_text_parts.append(page_content)
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")

        full_text = "\n\n".join(full_text_parts)
        return ProcessedDocument(
            full_text=full_text,
            pages=pages,
            metadata={"page_count": len(pages), "file_type": "docx"}
        )

    @classmethod
    def process_txt(cls, file_path: str) -> ProcessedDocument:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read TXT file: {str(e)}")

        cleaned = cls.clean_text(content)
        # Split into logical sections/pages of ~500 words
        paragraphs = cleaned.split("\n\n")
        pages = []
        current_chunk = []
        current_word_count = 0
        page_num = 1

        for p in paragraphs:
            p_clean = p.strip()
            if not p_clean:
                continue
            words = len(p_clean.split())
            current_chunk.append(p_clean)
            current_word_count += words
            if current_word_count >= 300:
                pages.append({"page_number": page_num, "text": "\n\n".join(current_chunk)})
                current_chunk = []
                current_word_count = 0
                page_num += 1

        if current_chunk:
            pages.append({"page_number": page_num, "text": "\n\n".join(current_chunk)})

        return ProcessedDocument(
            full_text=cleaned,
            pages=pages,
            metadata={"page_count": len(pages), "file_type": "txt"}
        )

    @classmethod
    def process_file(cls, file_path: str, file_type: str) -> ProcessedDocument:
        ext = file_type.lower().replace(".", "")
        if ext == "pdf":
            return cls.process_pdf(file_path)
        elif ext in ["docx", "doc"]:
            return cls.process_docx(file_path)
        elif ext in ["txt", "md", "csv"]:
            return cls.process_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_type}. Supported: PDF, DOCX, TXT")
