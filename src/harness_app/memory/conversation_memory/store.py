from __future__ import annotations

from uuid import uuid4

from harness_app.contracts.memory.models import ConversationTurn
from harness_app.contracts.ui.models import MessagePart


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, list[ConversationTurn]] = {}
        self._owners: dict[str, str] = {}

    def create_session(self, user_id: str) -> str:
        session_id = uuid4().hex[:12]
        self._sessions[session_id] = []
        self._owners[session_id] = user_id
        return session_id

    def append_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        *,
        parts: list[MessagePart] | None = None,
    ) -> None:
        self._sessions.setdefault(session_id, []).append(
            ConversationTurn(role=role, content=content, parts=parts or [])
        )

    def get_turns(self, session_id: str) -> list[ConversationTurn]:
        return list(self._sessions.get(session_id, []))

    def get_owner(self, session_id: str) -> str | None:
        return self._owners.get(session_id)
