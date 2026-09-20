import math
import numpy as np
from typing import List, Optional
import httpx
from sklearn.feature_extraction.text import TfidfVectorizer
from backend.app.core.config import settings

class EmbeddingEngine:
    def __init__(self):
        # Academic-tailored local vectorizer for instant local semantic search
        self.local_vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=1536,
            sublinear_tf=True,
            stop_words='english'
        )
        self._is_fitted = False
        self._corpus_cache: List[str] = [
            "computer science data structures algorithms operating systems database syllabus unit question bloom outcome taxonomy"
        ]
        self._fit_vectorizer()

    def _fit_vectorizer(self):
        try:
            self.local_vectorizer.fit(self._corpus_cache)
            self._is_fitted = True
        except Exception:
            pass

    def adapt_corpus(self, texts: List[str]):
        if texts:
            self._corpus_cache.extend(texts)
            if len(self._corpus_cache) > 2000:
                self._corpus_cache = self._corpus_cache[-1500:]
            self._fit_vectorizer()

    def get_local_embedding(self, text: str) -> List[float]:
        if not self._is_fitted:
            self._fit_vectorizer()
        
        vec = self.local_vectorizer.transform([text]).toarray()[0]
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    async def embed_query(self, query: str) -> List[float]:
        return self.get_local_embedding(query)

    async def embed_documents(self, documents: List[str]) -> List[List[float]]:
        self.adapt_corpus(documents)
        embeddings = []
        for doc in documents:
            emb = await self.embed_query(doc)
            embeddings.append(emb)
        return embeddings

embedding_engine = EmbeddingEngine()
