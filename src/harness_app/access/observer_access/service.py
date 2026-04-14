from __future__ import annotations

from harness_app.contracts.api.models import (
    LlmCallFlowResponse,
    LlmCallStepResponse,
    TraceDetailResponse,
    TraceEventResponse,
    ToolMetricResponse,
)
from harness_app.foundation.observability.observer import LlmCallRecord, ObservationRecord, Observer


class ObserverAccessService:
    def __init__(self, observer: Observer) -> None:
        self._observer = observer

    def get_trace(self, trace_id: str) -> TraceDetailResponse | None:
        record = self._observer.get_trace(trace_id)
        if record is None:
            return None
        return self._to_response(record)

    def list_session_traces(self, session_id: str) -> list[TraceDetailResponse]:
        return [self._to_response(record) for record in self._observer.list_session_traces(session_id)]

    def get_llm_flow(self, trace_id: str) -> LlmCallFlowResponse | None:
        record = self._observer.get_llm_call(trace_id)
        if record is None:
            return None
        return self._to_llm_flow_response(record)

    def list_session_llm_flows(self, session_id: str) -> list[LlmCallFlowResponse]:
        return [self._to_llm_flow_response(record) for record in self._observer.list_session_llm_calls(session_id)]

    def _to_response(self, record: ObservationRecord) -> TraceDetailResponse:
        return TraceDetailResponse(
            trace_id=record.trace_id,
            session_id=record.session_id,
            latency_ms=record.latency_ms,
            score=record.score,
            metrics=record.metrics,
            events=[TraceEventResponse(kind=event.kind, detail=event.detail) for event in record.events],
            audit_log=list(record.audit_log),
            tool_metrics=[
                ToolMetricResponse(tool_name=metric.tool_name, calls=metric.calls)
                for metric in record.tool_metrics
            ],
        )

    def _to_llm_flow_response(self, record: LlmCallRecord) -> LlmCallFlowResponse:
        return LlmCallFlowResponse(
            trace_id=record.trace_id,
            session_id=record.session_id,
            provider=record.provider,
            model=record.model,
            endpoint=record.endpoint,
            provider_trace_id=record.provider_trace_id,
            status=record.status,
            latency_ms=record.latency_ms,
            request_preview=record.request_preview,
            response_preview=record.response_preview,
            error=record.error,
            steps=[LlmCallStepResponse(kind=step.kind, detail=step.detail) for step in record.steps],
        )
