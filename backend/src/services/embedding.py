import numpy as np
import pickle
from dataclasses import dataclass
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from .chunking import Chunk

@dataclass
class EmbeddedChunk:
    chunk_id: int
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any]

class EmbeddingPipeline:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self._load_sbert_model()

    def _load_sbert_model(self):
        try:
            print(f"model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            print(f"tải model thành công ({self.model.get_sentence_embedding_dimension()} dims)")
        except Exception as e:
            print(f"Lỗi khi tải model: {e}")
            raise

    def embed_text(self, text: str, is_query: bool = False) -> np.ndarray:
        return self.model.encode(text, convert_to_numpy=True)

    def embed_batch(self, texts: List[str], batch_size: int = 32, show_progress: bool = True) -> np.ndarray:
        return self.model.encode(texts, batch_size=batch_size, show_progress_bar=show_progress, convert_to_numpy=True)

    def embed_chunks(self, chunks: List[Chunk]) -> List[EmbeddedChunk]:
        print(f"\n Bắt đầu embedding {len(chunks)} chunks...")
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embed_batch(texts, batch_size=32)
        embedded_chunks = [
            EmbeddedChunk(
                chunk_id=idx,
                content=chunk.content,
                embedding=embedding,
                metadata=chunk.metadata
            ) for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        print(f"Hoàn thành embedding! Shape mỗi embedding: {embeddings[0].shape}")
        return embedded_chunks

    def save_embeddings(self, embedded_chunks: List[EmbeddedChunk], filepath: str):
        with open(filepath, 'wb') as f:
            pickle.dump(embedded_chunks, f)
        print(f"lưu {len(embedded_chunks)} embedded chunks vào {filepath}")

    def load_embeddings(self, filepath: str) -> List[EmbeddedChunk]:
        with open(filepath, 'rb') as f:
            embedded_chunks = pickle.load(f)
        print(f"load {len(embedded_chunks)} embedded chunks từ {filepath}")
        return embedded_chunks

