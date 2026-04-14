from __future__ import annotations

from harness_app.contracts.runtime.models import ExecutionPlan


class BasicPlanner:
    def create_plan(self, message: str) -> ExecutionPlan:
        lowered = message.lower()
        steps = [
            {"name": "understand_request", "status": "pending"},
            {"name": "gather_context", "status": "pending"},
            {"name": "produce_response", "status": "pending"},
        ]
        if any(token in lowered for token in ("search", "faiss", "rag", "文档", "检索", "搜索", "查找")):
            steps.insert(2, {"name": "use_search_tool", "status": "optional"})
        return ExecutionPlan(goal=message, strategy="react", steps=steps)
