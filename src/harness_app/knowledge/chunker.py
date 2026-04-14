from __future__ import annotations

import re

from harness_app.knowledge.models import KnowledgeChunk, KnowledgeDocument

_HEADING_PATTERN = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)


class MarkdownChunker:
    def __init__(self, *, max_chars: int = 1200, overlap_chars: int = 150) -> None:
        self._max_chars = max_chars
        self._overlap_chars = overlap_chars

    def chunk_documents(self, documents: list[KnowledgeDocument]) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []
        for document in documents:
            chunks.extend(self._chunk_document(document))
        return chunks

    def _chunk_document(self, document: KnowledgeDocument) -> list[KnowledgeChunk]:
        sections = self._split_sections(document)
        chunks: list[KnowledgeChunk] = []
        for section_index, (title, content) in enumerate(sections):
            windows = self._split_long_content(content.strip())
            for window_index, window_content in enumerate(windows):
                if not window_content:
                    continue
                chunk_id = f"{document.source_path}#{section_index}-{window_index}"
                chunks.append(
                    KnowledgeChunk(
                        source_path=document.source_path,
                        title=title,
                        chunk_id=chunk_id,
                        content=window_content,
                        source_type=document.source_type,
                    )
                )
        return chunks

    def _split_sections(self, document: KnowledgeDocument) -> list[tuple[str, str]]:
        matches = list(_HEADING_PATTERN.finditer(document.content))
        if not matches:
            return [(document.title, document.content.strip())]

        sections: list[tuple[str, str]] = []
        lead_in = document.content[: matches[0].start()].strip()
        if lead_in:
            sections.append((document.title, lead_in))

        for index, match in enumerate(matches):
            section_title = match.group(2).strip()
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(document.content)
            section_body = document.content[start:end].strip()
            if section_body:
                sections.append((section_title, section_body))

        return sections or [(document.title, document.content.strip())]

    def _split_long_content(self, content: str) -> list[str]:
        if len(content) <= self._max_chars:
            return [content]

        chunks: list[str] = []
        start = 0
        while start < len(content):
            end = min(len(content), start + self._max_chars)
            window = content[start:end].strip()
            if window:
                chunks.append(window)
            if end >= len(content):
                break
            start = max(end - self._overlap_chars, start + 1)
        return chunks
