from __future__ import annotations

import hashlib
import math
import re

import numpy as np

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_\-\u4e00-\u9fff]+")


class HashingEmbedder:
    def __init__(self, vector_dim: int = 768) -> None:
        self._vector_dim = vector_dim

    @property
    def vector_dim(self) -> int:
        return self._vector_dim

    def encode_texts(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._vector_dim), dtype=np.float32)
        return np.vstack([self.encode_text(text) for text in texts]).astype(np.float32)

    def encode_text(self, text: str) -> np.ndarray:
        vector = np.zeros(self._vector_dim, dtype=np.float32)
        tokens = _TOKEN_PATTERN.findall(text.lower())
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
            bucket = int.from_bytes(digest[:8], byteorder="little") % self._vector_dim
            signed = 1.0 if digest[8] % 2 == 0 else -1.0
            weight = 1.0 + math.log1p(len(token))
            vector[bucket] += signed * weight

        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector /= norm
        return vector
