from __future__ import annotations

from harness_app.foundation.guardrails.filters import sanitize_output


class Guardrails:
    def sanitize_reply(self, text: str) -> str:
        return sanitize_output(text)
