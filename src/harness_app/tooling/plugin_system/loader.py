from __future__ import annotations

from typing import Iterable

from harness_app.contracts.tooling.models import ToolCallSpec, ToolResult
from harness_app.foundation.config_center.settings import PluginToolConfig


class PluginLoader:
    def __init__(self, definitions: Iterable[PluginToolConfig]) -> None:
        self._definitions = list(definitions)

    def register(self, registry) -> None:
        for definition in self._definitions:
            registry.register(definition.name, self._build_handler(definition))

    def _build_handler(self, definition: PluginToolConfig):
        def _handler(spec: ToolCallSpec) -> ToolResult:
            topic = str(spec.arguments.get("topic", "overview"))
            content = definition.template.format(topic=topic)
            return ToolResult(tool_name=definition.name, content=content)

        return _handler
