from __future__ import annotations

from typing import Callable

from harness_app.contracts.tooling.models import ToolCallSpec, ToolResult

ToolHandler = Callable[[ToolCallSpec], ToolResult]


class ToolRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, name: str, handler: ToolHandler) -> None:
        self._handlers[name] = handler

    def list_tools(self) -> list[str]:
        return sorted(self._handlers)

    def execute(self, spec: ToolCallSpec) -> ToolResult:
        handler = self._handlers.get(spec.tool_name)
        if handler is None:
            return ToolResult(tool_name=spec.tool_name, content="Unknown tool", is_error=True)
        return handler(spec)
