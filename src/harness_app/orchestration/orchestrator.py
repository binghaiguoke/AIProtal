from __future__ import annotations

from dataclasses import dataclass

from harness_app.contracts.runtime.models import ExecutionPlan
from harness_app.orchestration.decision_engine.engine import DecisionEngine
from harness_app.orchestration.planner.planner import BasicPlanner
from harness_app.orchestration.router.router import AgentRouter
from harness_app.orchestration.workflow.workflow import WorkflowEngine, WorkflowState


@dataclass(slots=True)
class OrchestrationBundle:
    plan: ExecutionPlan
    executor_name: str
    workflow_states: list[WorkflowState]
    tool_names: list[str]


class Orchestrator:
    def __init__(
        self,
        planner: BasicPlanner,
        router: AgentRouter,
        workflow_engine: WorkflowEngine,
        decision_engine: DecisionEngine,
    ) -> None:
        self._planner = planner
        self._router = router
        self._workflow_engine = workflow_engine
        self._decision_engine = decision_engine

    def build_bundle(self, message: str) -> OrchestrationBundle:
        plan = self._planner.create_plan(message)
        executor_name = self._router.select_executor(plan)
        workflow_states = self._workflow_engine.mark_executing(self._workflow_engine.initialize())
        tool_names = self._decision_engine.decide_tool_names(message) if self._decision_engine.should_use_tools(message) else []
        return OrchestrationBundle(
            plan=plan,
            executor_name=executor_name,
            workflow_states=workflow_states,
            tool_names=tool_names,
        )

    def complete(self, states: list[WorkflowState]) -> list[WorkflowState]:
        return self._workflow_engine.mark_complete(states)
