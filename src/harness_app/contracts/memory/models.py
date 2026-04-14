from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from harness_app.contracts.ui.models import MessagePart


class ConversationTurn(BaseModel):
    role: str
    content: str
    parts: list[MessagePart] = Field(default_factory=list)


class RuntimeContextBundle(BaseModel):
    system_prompt: str
    messages: list[dict[str, Any]] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
