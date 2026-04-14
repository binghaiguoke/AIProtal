from __future__ import annotations

from harness_app.contracts.runtime.models import ExecutionPlan


class AgentRouter:
    def select_executor(self, plan: ExecutionPlan) -> str:
        return "react" if plan.strategy == "react" else "default"
