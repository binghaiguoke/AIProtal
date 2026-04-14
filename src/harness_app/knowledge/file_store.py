from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from harness_app.knowledge.models import KnowledgeFileRecord


class KnowledgeFileStore:
    def __init__(self, uploads_root: Path) -> None:
        self._uploads_root = uploads_root
        self._uploads_root.mkdir(parents=True, exist_ok=True)
        self._manifest_path = self._uploads_root / "manifest.json"

    def save_file(self, file_name: str, content: bytes) -> KnowledgeFileRecord:
        extension = Path(file_name).suffix.lower()
        file_id = uuid4().hex
        safe_name = Path(file_name).name
        stored_name = f"{file_id}{extension}"
        stored_path = self._uploads_root / stored_name
        stored_path.write_bytes(content)
        record = KnowledgeFileRecord(
            file_id=file_id,
            file_name=safe_name,
            stored_path=str(stored_path),
            source_path=self._to_source_path(stored_path),
            extension=extension,
            size_bytes=len(content),
            uploaded_at=datetime.now(UTC),
            notes=[],
        )
        manifest = self._read_manifest()
        manifest[file_id] = {
            "file_name": safe_name,
            "uploaded_at": record.uploaded_at.isoformat(),
        }
        self._write_manifest(manifest)
        return record

    def list_files(self) -> list[KnowledgeFileRecord]:
        manifest = self._read_manifest()
        records: list[KnowledgeFileRecord] = []
        for path in sorted(self._uploads_root.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
            if not path.is_file() or path.name == self._manifest_path.name:
                continue
            stat = path.stat()
            file_id = path.stem
            meta = manifest.get(file_id, {})
            uploaded_at = meta.get("uploaded_at")
            records.append(
                KnowledgeFileRecord(
                    file_id=file_id,
                    file_name=str(meta.get("file_name", path.name)),
                    stored_path=str(path),
                    source_path=self._to_source_path(path),
                    extension=path.suffix.lower(),
                    size_bytes=stat.st_size,
                    uploaded_at=datetime.fromisoformat(uploaded_at) if uploaded_at else datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                    notes=[],
                )
            )
        return records

    def delete_file(self, file_id: str) -> bool:
        manifest = self._read_manifest()
        for path in self._uploads_root.glob(f"{file_id}.*"):
            if path.is_file():
                path.unlink()
                if file_id in manifest:
                    manifest.pop(file_id, None)
                    self._write_manifest(manifest)
                return True
        return False

    def _to_source_path(self, path: Path) -> str:
        try:
            return path.relative_to(self._uploads_root.parent.parent).as_posix()
        except ValueError:
            return path.name

    def _read_manifest(self) -> dict[str, dict[str, str]]:
        if not self._manifest_path.exists():
            return {}
        try:
            return json.loads(self._manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write_manifest(self, manifest: dict[str, dict[str, str]]) -> None:
        self._manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding="utf-8")
