from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from harness_app.contracts.ui.models import MessagePart


class ExecutionPlan(BaseModel):
    goal: str
    strategy: str
    steps: list[dict[str, Any]] = Field(default_factory=list)
    requires_human_approval: bool = False


class ExecutionResult(BaseModel):
    session_id: str
    reply: str
    tool_results: list[str] = Field(default_factory=list)
    parts: list[MessagePart] = Field(default_factory=list)
    trace_id: str
