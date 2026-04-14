from __future__ import annotations

from harness_app.contracts.memory.models import ConversationTurn


def compact_turns(turns: list[ConversationTurn], limit: int = 6) -> list[ConversationTurn]:
    return turns[-limit:]
