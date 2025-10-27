import numpy as np
import pickle
import re
import math
import os
import json
from typing import List, Dict, Any, Literal
from dataclasses import dataclass, asdict
from collections import Counter
import tiktoken
from sentence_transformers import SentenceTransformer
from .chunking import Chunk
from .embedding import EmbeddingPipeline, EmbeddedChunk
# BM25 CLASS
class BM25:
    """
    BM25 algorithm cho keyword-based retrieval
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.corpus_size, self.avgdl = 0, 0
        self.doc_freqs, self.idf, self.doc_len, self.documents = [], {}, [], []

    def _tokenize_vietnamese(self, text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})', r' \1 ', text)
        text = re.sub(r'\b(\d+)\b', r' \1 ', text)
        return re.findall(r'\w+', text, re.UNICODE)

    def fit(self, corpus: List[str]):
        self.corpus_size = len(corpus)
        self.documents = corpus
        tokenized_corpus = [self._tokenize_vietnamese(doc) for doc in corpus]
        self.doc_len = [len(doc) for doc in tokenized_corpus]
        self.avgdl = sum(self.doc_len) / self.corpus_size
        df = {}
        for document in tokenized_corpus:
            for term in set(document):
                df[term] = df.get(term, 0) + 1
        for term, freq in df.items():
            self.idf[term] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1)
        self.doc_freqs = [Counter(doc) for doc in tokenized_corpus]

    def get_scores(self, query: str) -> np.ndarray:
        query_tokens = self._tokenize_vietnamese(query)
        scores = np.zeros(self.corpus_size)
        for token in query_tokens:
            if token not in self.idf: continue
            idf = self.idf[token]
            for idx, doc_tf in enumerate(self.doc_freqs):
                tf = doc_tf.get(token, 0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (self.doc_len[idx] / self.avgdl))
                scores[idx] += idf * (numerator / denominator)
        return scores

# HYBRID RETRIEVER
class HybridRetriever:
    """
    Hybrid Retriever kết hợp Semantic + Keyword search
    """
    def __init__(self, embedded_chunks: List[EmbeddedChunk], embedding_pipeline: EmbeddingPipeline, semantic_weight: float = 0.5, keyword_weight: float = 0.5):
        self.embedded_chunks = embedded_chunks
        self.pipeline = embedding_pipeline
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        
        self.embedding_matrix = np.vstack([ec.embedding for ec in embedded_chunks])
        self.embedding_matrix /= np.linalg.norm(self.embedding_matrix, axis=1, keepdims=True)
        
        print("Đang build BM25 index...")
        self.bm25 = BM25()
        self.bm25.fit([ec.content for ec in embedded_chunks])
        print("BM25 index ready!")

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        if scores.max() == scores.min(): return np.zeros_like(scores)
        return (scores - scores.min()) / (scores.max() - scores.min())

    def retrieve(self, query: str, top_k: int = 5, return_details: bool = False) -> List[Dict[str, Any]]:
        query_embedding = self.pipeline.embed_text(query, is_query=True)
        query_embedding /= np.linalg.norm(query_embedding)
        semantic_scores = np.dot(self.embedding_matrix, query_embedding)
        keyword_scores = self.bm25.get_scores(query)
        
        semantic_scores_norm = self._normalize_scores(semantic_scores)
        keyword_scores_norm = self._normalize_scores(keyword_scores)
        
        combined_scores = (self.semantic_weight * semantic_scores_norm + self.keyword_weight * keyword_scores_norm)
        top_indices = np.argsort(combined_scores)[::-1][:top_k]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            result = {
                "rank": rank, "chunk_id": self.embedded_chunks[idx].chunk_id,
                "content": self.embedded_chunks[idx].content, "metadata": self.embedded_chunks[idx].metadata,
                "combined_score": float(combined_scores[idx])
            }
            if return_details:
                result.update({
                    "semantic_score": float(semantic_scores[idx]),
                    "keyword_score": float(keyword_scores[idx])
                })
            results.append(result)
        return results

    def _compute_rerank_score(self, query: str, candidate: Dict) -> float:
        content, query_lower = candidate["content"].lower(), query.lower()
        score = 0.0
        if query_lower in content: score += 0.3
        
        query_words = set(re.findall(r'\w+', query_lower, re.UNICODE))
        coverage = len(query_words & set(re.findall(r'\w+', content, re.UNICODE))) / len(query_words) if query_words else 0
        score += 0.3 * coverage
        
        query_dates = re.findall(r'\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}', query_lower)
        if query_dates and any(date in content for date in query_dates): score += 0.4
        return min(score, 1.0)
        
    def retrieve_with_rerank(self, query: str, top_k: int = 5, candidate_k: int = 20) -> List[Dict[str, Any]]:
        candidates = self.retrieve(query, top_k=candidate_k, return_details=True)
        for cand in candidates:
            rerank_score = self._compute_rerank_score(query, cand)
            cand["rerank_score"] = rerank_score
            cand["final_score"] = 0.6 * cand["combined_score"] + 0.4 * cand["rerank_score"]
        candidates.sort(key=lambda x: x["final_score"], reverse=True)
        return candidates[:top_k]