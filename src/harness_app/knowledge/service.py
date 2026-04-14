from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

from harness_app.foundation.config_center.settings import KnowledgeBaseConfig
from harness_app.knowledge.chunker import MarkdownChunker
from harness_app.knowledge.embedder import HashingEmbedder
from harness_app.knowledge.extractors import DocumentTextExtractor
from harness_app.knowledge.faiss_store import FaissStore
from harness_app.knowledge.file_store import KnowledgeFileStore
from harness_app.knowledge.loader import DocumentLoader
from harness_app.knowledge.models import (
    ExtractionResult,
    KnowledgeChunk,
    KnowledgeFileRecord,
    KnowledgeIndexStatus,
    KnowledgeSearchHit,
)
from harness_app.knowledge.ocr import OcrFallback


class LocalKnowledgeService:
    def __init__(self, project_root: Path, config: KnowledgeBaseConfig) -> None:
        self._config = config
        uploads_root = project_root / config.uploads_dir
        self._file_store = KnowledgeFileStore(uploads_root)
        self._extractor = DocumentTextExtractor(OcrFallback(config.enable_ocr_fallback))
        self._loader = DocumentLoader(project_root, config.source_paths, self._file_store, self._extractor)
        self._chunker = MarkdownChunker(
            max_chars=config.chunk_size,
            overlap_chars=config.chunk_overlap,
        )
        self._embedder = HashingEmbedder(vector_dim=config.vector_dim)
        self._store = FaissStore(vector_dim=config.vector_dim)
        self._chunks: list[KnowledgeChunk] = []
        self._indexed_document_count = 0
        self._rebuilt_at: datetime | None = None
        self._lock = Lock()
        self._is_ready = False

    def build_index(self) -> int:
        with self._lock:
            documents = self._loader.load()
            self._indexed_document_count = len(documents)
            self._chunks = self._chunker.chunk_documents(documents)
            vectors = self._embedder.encode_texts([chunk.content for chunk in self._chunks])
            self._store.build(vectors)
            self._is_ready = True
            self._rebuilt_at = datetime.now(UTC)
            return len(self._chunks)

    def rebuild_index(self) -> KnowledgeIndexStatus:
        self.build_index()
        return self.get_index_status()

    def search(self, query: str, top_k: int | None = None) -> list[KnowledgeSearchHit]:
        if not query.strip():
            return []

        if not self._is_ready:
            self.build_index()

        effective_top_k = top_k or self._config.default_top_k
        vector = self._embedder.encode_text(query)
        scores, indices = self._store.search(vector, effective_top_k)
        hits: list[KnowledgeSearchHit] = []
        for score, index in zip(scores[0], indices[0], strict=False):
            if index < 0 or index >= len(self._chunks):
                continue
            chunk = self._chunks[int(index)]
            hits.append(
                KnowledgeSearchHit(
                    source_path=chunk.source_path,
                    title=chunk.title,
                    chunk_id=chunk.chunk_id,
                    content=chunk.content,
                    score=float(score),
                )
            )
        return hits

    def save_upload(self, file_name: str, content: bytes) -> tuple[KnowledgeFileRecord, ExtractionResult]:
        extension = Path(file_name).suffix.lower()
        normalized_extensions = {item.lower() for item in self._config.allowed_extensions}
        if extension not in normalized_extensions:
            raise ValueError(f"Unsupported file extension: {extension}")

        max_size_bytes = self._config.max_upload_size_mb * 1024 * 1024
        if len(content) > max_size_bytes:
            raise ValueError(f"File exceeds {self._config.max_upload_size_mb} MB limit")

        file_record = self._file_store.save_file(file_name, content)
        extraction = self._extractor.extract(Path(file_record.stored_path))
        file_record.extracted_text_length = len(extraction.content)
        file_record.status = "indexed" if extraction.content.strip() else "stored"
        file_record.notes = extraction.notes
        self.build_index()
        return file_record, extraction

    def list_files(self) -> list[KnowledgeFileRecord]:
        records = self._file_store.list_files()
        for record in records:
            extraction = self._extractor.extract(Path(record.stored_path))
            record.extracted_text_length = len(extraction.content)
            record.status = "indexed" if extraction.content.strip() else "stored"
            record.notes = extraction.notes
        return records

    def delete_file(self, file_id: str) -> bool:
        deleted = self._file_store.delete_file(file_id)
        if deleted:
            self.build_index()
        return deleted

    def get_index_status(self) -> KnowledgeIndexStatus:
        return KnowledgeIndexStatus(
            indexed_chunk_count=len(self._chunks),
            indexed_document_count=self._indexed_document_count,
            uploaded_file_count=len(self._file_store.list_files()),
            rebuilt_at=self._rebuilt_at,
        )

    @property
    def indexed_chunk_count(self) -> int:
        return len(self._chunks)
