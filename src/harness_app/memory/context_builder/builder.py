from __future__ import annotations

from harness_app.contracts.memory.models import RuntimeContextBundle
from harness_app.memory.compression.compact import compact_turns
from harness_app.memory.conversation_memory.store import SessionStore


class ContextBuilder:
    def __init__(self, store: SessionStore) -> None:
        self._store = store

    def build(self, session_id: str) -> RuntimeContextBundle:
        turns = compact_turns(self._store.get_turns(session_id))
        return RuntimeContextBundle(
            system_prompt=(
                "You are MyPortal, a six-layer AI Agent Harness runtime. "
                "Use safe tools, concise planning, and observable execution."
            ),
            messages=[turn.model_dump() for turn in turns],
            memory_refs=[f"session:{session_id}"],
        )
