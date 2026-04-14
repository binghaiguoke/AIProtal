from __future__ import annotations

from harness_app.contracts.tooling.models import ToolCallSpec, ToolResult
from harness_app.foundation.access_control.policy import PermissionPolicy
from harness_app.tooling.tool_registry.registry import ToolRegistry


class ToolHub:
    def __init__(self, registry: ToolRegistry, policy: PermissionPolicy) -> None:
        self._registry = registry
        self._policy = policy

    def execute(self, spec: ToolCallSpec) -> ToolResult:
        decision = self._policy.evaluate(spec.tool_name)
        if not decision.allowed:
            return ToolResult(tool_name=spec.tool_name, content=decision.reason, is_error=True)
        return self._registry.execute(spec)
