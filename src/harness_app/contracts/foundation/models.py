from __future__ import annotations

from pydantic import BaseModel


class PermissionDecision(BaseModel):
    allowed: bool
    reason: str = ""
    requires_confirmation: bool = False


class ExecutionTrace(BaseModel):
    trace_id: str
    session_id: str
    latency_ms: int = 0
