# Retrieval-Augmented Generation (RAG) Pipeline

## 1. Pipeline Overview
The academic RAG pipeline processes unstructured educational resources into searchable vector embeddings with rich provenance tracking.

```
Document Upload (PDF, DOCX, TXT)
              │
              ▼
[Text Extraction & Unicode Normalization]
              │
              ▼
[Sliding Window Chunking (600 tokens, 100 overlap)]
              │
              ▼
[Metadata Tagging (Unit, Page, Topic, Doc Type)]
              │
              ▼
[Vector Embedding & Persistent Indexing]
              │
              ▼
[Metadata-Filtered Top-K Cosine Retrieval]
              │
              ▼
[Provenance-Tracked Context Grounding]
```

## 2. Text Extraction & Cleaning
- **PDF**: Handled by `pypdf`, extracting raw text per physical page to preserve exact page numbers for explainability.
- **DOCX**: Handled by `python-docx`, grouping paragraph segments with estimated page markers.
- **TXT / Markdown**: Normalized line breaks, filtered null bytes, and segmented into semantic blocks.

## 3. Chunking & Metadata Enrichment
Each chunk retains structured metadata:
```json
{
  "resource_id": 1,
  "course_id": 1,
  "course_code": "CS301",
  "file_name": "CS301_DSA_University_Textbook.pdf",
  "document_type": "textbook",
  "unit_number": 2,
  "page_number": 5,
  "topic": "AVL Trees & Balance Factors",
  "chunk_index": 1
}
```

## 4. Vector Store & Semantic Search
- **Embedding Generation**: High-speed local normalized TF-IDF semantic vectorizer with cosine similarity.
- **Similarity Scoring**: Cosine similarity between query and chunk vectors, enriched with topic boost.
- **Explainability**: Every generated question retains the exact source document ID, page, and chunk score displayed in the "Why this question?" UI drawer.
