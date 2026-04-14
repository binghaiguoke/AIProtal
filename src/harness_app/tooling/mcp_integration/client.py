from __future__ import annotations

from typing import Iterable

from harness_app.contracts.tooling.models import ToolCallSpec, ToolResult
from harness_app.foundation.config_center.settings import McpToolConfig


class McpClientManager:
    def __init__(self, definitions: Iterable[McpToolConfig]) -> None:
        self._definitions = list(definitions)

    def register(self, registry) -> None:
        for definition in self._definitions:
            registry.register(definition.name, self._build_handler(definition))

    def _build_handler(self, definition: McpToolConfig):
        def _handler(spec: ToolCallSpec) -> ToolResult:
            payload = str(spec.arguments.get("payload", spec.arguments.get("query", "")))
            content = definition.template.format(payload=payload)
            return ToolResult(tool_name=definition.name, content=content)

        return _handler
