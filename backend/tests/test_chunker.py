import pytest
from backend.app.services.rag.chunker import AcademicChunker

def test_academic_chunker_basic():
    chunker = AcademicChunker(chunk_size=50, chunk_overlap=10)
    pages = [
        {
            "page_number": 1,
            "text": "Unit 1: Linear Data Structures. An array is a collection of elements stored at contiguous memory locations. Stacks follow LIFO order while Queues follow FIFO order."
        },
        {
            "page_number": 2,
            "text": "Unit 2: Binary Search Trees. A BST maintains the property that the left child is smaller than parent and right child is greater. AVL trees maintain balance factors between -1 and +1."
        }
    ]
    chunks = chunker.chunk_document(pages)
    assert len(chunks) >= 2
    assert chunks[0].unit_number == 1
    assert chunks[1].unit_number == 2
    assert "Array" in chunks[0].content or "Linear" in chunks[0].content
