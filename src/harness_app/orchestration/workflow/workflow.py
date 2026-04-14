from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WorkflowState:
    name: str
    status: str


class WorkflowEngine:
    def initialize(self) -> list[WorkflowState]:
        return [
            WorkflowState(name="init", status="ready"),
            WorkflowState(name="execute", status="ready"),
            WorkflowState(name="verify", status="ready"),
        ]

    def mark_executing(self, states: list[WorkflowState]) -> list[WorkflowState]:
        return [WorkflowState(name=state.name, status="running") for state in states]

    def mark_complete(self, states: list[WorkflowState]) -> list[WorkflowState]:
        return [WorkflowState(name=state.name, status="done") for state in states]
