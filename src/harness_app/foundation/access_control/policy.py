from __future__ import annotations

from harness_app.contracts.foundation.models import PermissionDecision


class PermissionPolicy:
    def __init__(self, allowed_tools: list[str]) -> None:
        self._allowed_tools = set(allowed_tools)

    def evaluate(self, tool_name: str) -> PermissionDecision:
        if tool_name in self._allowed_tools:
            return PermissionDecision(allowed=True)
        return PermissionDecision(allowed=False, reason=f"tool '{tool_name}' is not allowed")
