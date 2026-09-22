import math
import re
from typing import List, Dict, Optional
import numpy as np
from app.core.config import settings

class LightweightTfidfVectorizer:
    """
    Lightweight, high-performance TF-IDF vectorizer tailored for academic RAG embeddings.
    Zero dependency on heavy binary libraries like scikit-learn / scipy to stay well within
    serverless bundle size limits (<500MB on Vercel).
    """
    def __init__(self, max_features: int = 1536):
        self.max_features = max_features
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.stop_words = {
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
            "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
            "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
            "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
            "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
            "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
            "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
            "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
            "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
            "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
            "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
            "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
            "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
            "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
            "they've", "this", "those", "through", "to", "too", "under", "until", "up",
            "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
            "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
            "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
            "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
            "yourself", "yourselves"
        }

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        filtered = [w for w in words if w not in self.stop_words]
        tokens = list(filtered)
        # Add bigrams and trigrams
        for i in range(len(filtered) - 1):
            tokens.append(f"{filtered[i]}_{filtered[i+1]}")
        for i in range(len(filtered) - 2):
            tokens.append(f"{filtered[i]}_{filtered[i+1]}_{filtered[i+2]}")
        return tokens

    def fit(self, corpus: List[str]):
        df_counts: Dict[str, int] = {}
        doc_count = len(corpus)
        for doc in corpus:
            tokens = set(self._tokenize(doc))
            for t in tokens:
                df_counts[t] = df_counts.get(t, 0) + 1

        # Select top features
        sorted_features = sorted(df_counts.items(), key=lambda x: x[1], reverse=True)[:self.max_features]
        self.vocab = {feat: i for i, (feat, _) in enumerate(sorted_features)}
        self.idf = {feat: math.log((1 + doc_count) / (1 + count)) + 1.0 for feat, count in sorted_features}

    def transform(self, text: str) -> List[float]:
        vec = [0.0] * max(len(self.vocab), 1)
        if not self.vocab:
            return vec
        tokens = self._tokenize(text)
        if not tokens:
            return vec
        tf_counts: Dict[str, int] = {}
        for t in tokens:
            if t in self.vocab:
                tf_counts[t] = tf_counts.get(t, 0) + 1

        for term, count in tf_counts.items():
            idx = self.vocab[term]
            tf = 1.0 + math.log(count)
            idf = self.idf.get(term, 1.0)
            vec[idx] = tf * idf

        # L2 normalization
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


class EmbeddingEngine:
    def __init__(self):
        self.local_vectorizer = LightweightTfidfVectorizer(max_features=1536)
        self._is_fitted = False
        self._corpus_cache: List[str] = [
            "computer science data structures algorithms operating systems database syllabus unit question bloom outcome taxonomy examination university academic engineering"
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
        return self.local_vectorizer.transform(text)

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
