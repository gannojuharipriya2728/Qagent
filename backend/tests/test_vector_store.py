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


@pytest.mark.asyncio
async def test_embedding_space_is_stable_across_indexing_batches():
    """
    A vector indexed before a later upload must stay comparable with queries
    embedded after it.

    Feature positions used to be assigned by corpus rank, so indexing a second
    document re-numbered the dimensions and left every already-stored vector in
    an abandoned coordinate space.
    """
    from app.services.rag.embeddings import embedding_engine

    target = (
        "Deadlock detection and recovery algorithms in operating systems. "
        "A deadlock occurs when processes hold resources and wait indefinitely."
    )
    stored = (await embedding_engine.embed_documents([target]))[0]

    await embedding_engine.embed_documents([
        "Relational algebra normalization functional dependency schema design",
        "Transmission control protocol congestion window routing network layer",
        "Binary search tree traversal heap sort graph adjacency shortest path",
    ])

    re_embedded = embedding_engine.get_local_embedding(target)

    assert len(stored) == embedding_engine.dimension
    assert len(re_embedded) == embedding_engine.dimension
    # Same text, same dimensions: only the IDF weighting may drift.
    non_zero = [i for i, v in enumerate(stored) if v != 0.0]
    assert non_zero, "expected a non-empty vector"
    for i in non_zero:
        assert re_embedded[i] != 0.0, f"dimension {i} was abandoned after refitting"


@pytest.mark.asyncio
async def test_feature_index_is_deterministic_across_processes():
    """Dimensions must not depend on PYTHONHASHSEED or insertion order."""
    from app.services.rag.embeddings import LightweightTfidfVectorizer

    a = LightweightTfidfVectorizer(max_features=1536)
    b = LightweightTfidfVectorizer(max_features=1536)
    a.fit(["alpha beta gamma", "delta epsilon"])
    b.fit(["delta epsilon", "alpha beta gamma", "zeta eta theta"])

    for term in ["deadlock", "normalization", "scheduling", "bloom_taxonomy"]:
        assert a.feature_index(term) == b.feature_index(term)
        assert 0 <= a.feature_index(term) < 1536
