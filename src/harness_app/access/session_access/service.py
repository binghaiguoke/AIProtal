from __future__ import annotations

from harness_app.contracts.api.models import SessionDetailResponse, SessionHistoryItem
from harness_app.memory.conversation_memory.store import SessionStore


class SessionAccessService:
    def __init__(self, store: SessionStore) -> None:
        self._store = store

    def get_session_owner(self, session_id: str) -> str | None:
        return self._store.get_owner(session_id)

    def get_session_detail(self, session_id: str) -> SessionDetailResponse | None:
        owner = self._store.get_owner(session_id)
        if owner is None:
            return None
        turns = self._store.get_turns(session_id)
        return SessionDetailResponse(
            session_id=session_id,
            user_id=owner,
            message_count=len(turns),
            history=[
                SessionHistoryItem(role=turn.role, content=turn.content, parts=list(turn.parts))
                for turn in turns
            ],
        )

    def get_history(self, session_id: str) -> list[SessionHistoryItem] | None:
        detail = self.get_session_detail(session_id)
        if detail is None:
            return None
        return detail.history
