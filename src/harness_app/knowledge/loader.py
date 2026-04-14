from __future__ import annotations

from pathlib import Path

from harness_app.knowledge.extractors import DocumentTextExtractor
from harness_app.knowledge.file_store import KnowledgeFileStore
from harness_app.knowledge.models import KnowledgeDocument


class DocumentLoader:
    def __init__(
        self,
        project_root: Path,
        source_paths: list[str],
        file_store: KnowledgeFileStore | None = None,
        extractor: DocumentTextExtractor | None = None,
    ) -> None:
        self._project_root = project_root
        self._source_paths = source_paths
        self._file_store = file_store
        self._extractor = extractor

    def load(self) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []
        for relative_path in self._source_paths:
            path = self._project_root / relative_path
            if not path.exists() or not path.is_file():
                continue
            documents.append(
                KnowledgeDocument(
                    source_path=relative_path.replace("\\", "/"),
                    content=path.read_text(encoding="utf-8"),
                    title=path.stem,
                    source_type="static",
                    extraction_notes=[],
                )
            )

        if self._file_store is None or self._extractor is None:
            return documents

        for file_record in self._file_store.list_files():
            path = Path(file_record.stored_path)
            if not path.exists() or not path.is_file():
                continue
            extraction = self._extractor.extract(path)
            if not extraction.content.strip():
                continue
            documents.append(
                KnowledgeDocument(
                    source_path=file_record.source_path,
                    content=extraction.content,
                    title=file_record.file_name,
                    source_type="upload",
                    extraction_notes=extraction.notes,
                )
            )
        return documents
