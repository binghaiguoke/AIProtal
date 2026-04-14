from __future__ import annotations

import faiss
import numpy as np


class FaissStore:
    def __init__(self, vector_dim: int) -> None:
        self._vector_dim = vector_dim
        self._index = faiss.IndexFlatIP(vector_dim)

    def build(self, vectors: np.ndarray) -> None:
        self._index.reset()
        if len(vectors) == 0:
            return
        self._index.add(vectors.astype(np.float32))

    def search(self, vector: np.ndarray, top_k: int) -> tuple[np.ndarray, np.ndarray]:
        if self._index.ntotal == 0:
            return np.zeros((1, 0), dtype=np.float32), np.zeros((1, 0), dtype=np.int64)
        normalized_top_k = max(1, min(top_k, self._index.ntotal))
        return self._index.search(vector.reshape(1, self._vector_dim).astype(np.float32), normalized_top_k)

    @property
    def count(self) -> int:
        return int(self._index.ntotal)
