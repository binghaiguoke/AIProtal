from __future__ import annotations

from harness_app.contracts.memory.models import RuntimeContextBundle
from harness_app.memory.context_builder.builder import ContextBuilder


class ContextManager:
    def __init__(self, builder: ContextBuilder) -> None:
        self._builder = builder

    def build(self, session_id: str) -> RuntimeContextBundle:
        return self._builder.build(session_id)
