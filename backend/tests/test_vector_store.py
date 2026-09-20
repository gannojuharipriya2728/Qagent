import pytest
from app.services.rag.vector_store import AcademicVectorStore

@pytest.mark.asyncio
async def test_vector_store_indexing_and_search():
    store = AcademicVectorStore(storage_path="./data/test_vector_store.json")
    
    docs = [
        "Dynamic programming 0/1 knapsack problem with optimal substructure.",
        "Dijkstra algorithm for single source shortest path in non-negative weighted graphs.",
        "Boyce-Codd Normal Form BCNF eliminating redundant functional dependencies."
    ]
    metas = [
        {"course_id": 1, "unit_number": 5, "topic": "Dynamic Programming"},
        {"course_id": 1, "unit_number": 4, "topic": "Graph Algorithms"},
        {"course_id": 2, "unit_number": 3, "topic": "BCNF Normalization"}
    ]
    
    await store.add_documents(contents=docs, metadatas=metas)
    
    # Search for Knapsack
    results = await store.similarity_search("knapsack dynamic programming", k=2, course_id=1)
    assert len(results) > 0
    assert results[0]["metadata"]["topic"] == "Dynamic Programming"
