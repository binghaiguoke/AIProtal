from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolCallSpec(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    caller_id: str
    session_id: str


class ToolResult(BaseModel):
    tool_name: str
    content: str
    is_error: bool = False
