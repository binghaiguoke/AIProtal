from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class KnowledgeDocument:
    source_path: str
    content: str
    title: str
    source_type: str = "static"
    extraction_notes: list[str] | None = None


@dataclass(slots=True)
class KnowledgeChunk:
    source_path: str
    title: str
    chunk_id: str
    content: str
    source_type: str = "static"


@dataclass(slots=True)
class KnowledgeSearchHit:
    source_path: str
    title: str
    chunk_id: str
    content: str
    score: float
    source_type: str = "static"


@dataclass(slots=True)
class ExtractionResult:
    content: str
    notes: list[str]
    used_ocr: bool = False


@dataclass(slots=True)
class KnowledgeFileRecord:
    file_id: str
    file_name: str
    stored_path: str
    source_path: str
    extension: str
    size_bytes: int
    uploaded_at: datetime
    extracted_text_length: int = 0
    status: str = "stored"
    notes: list[str] | None = None


@dataclass(slots=True)
class KnowledgeIndexStatus:
    indexed_chunk_count: int
    indexed_document_count: int
    uploaded_file_count: int
    rebuilt_at: datetime | None = None


@dataclass(slots=True)
class StoredKnowledgeFile:
    record: KnowledgeFileRecord
    original_file_name: str | None = None
