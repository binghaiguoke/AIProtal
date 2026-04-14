from __future__ import annotations

from pathlib import Path

from harness_app.knowledge.models import ExtractionResult


class OcrFallback:
    def __init__(self, enabled: bool) -> None:
        self._enabled = enabled

    def extract_text(self, path: Path) -> ExtractionResult:
        if not self._enabled:
            return ExtractionResult(content="", notes=["OCR fallback disabled by configuration."], used_ocr=False)

        return ExtractionResult(
            content="",
            notes=[
                f"OCR fallback is not configured for {path.name}. "
                "Install and wire a local OCR engine to extract image-based content."
            ],
            used_ocr=False,
        )
