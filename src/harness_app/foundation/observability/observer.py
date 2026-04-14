from __future__ import annotations

import time
from dataclasses import dataclass, field

from harness_app.foundation.evaluation.scoring import score_response
from harness_app.foundation.observability.telemetry import Telemetry


@dataclass(slots=True)
class TraceEvent:
    kind: str
    detail: str


@dataclass(slots=True)
class ToolMetric:
    tool_name: str
    calls: int = 0


@dataclass(slots=True)
class LlmCallStep:
    kind: str
    detail: str


@dataclass(slots=True)
class LlmCallRecord:
    trace_id: str
    session_id: str
    provider: str
    model: str
    endpoint: str
    status: str
    started_at: float
    provider_trace_id: str = ""
    request_preview: str = ""
    response_preview: str = ""
    error: str = ""
    latency_ms: int = 0
    steps: list[LlmCallStep] = field(default_factory=list)


@dataclass(slots=True)
class ObservationRecord:
    trace_id: str
    session_id: str
    latency_ms: int
    score: float
    metrics: dict[str, str] = field(default_factory=dict)
    events: list[TraceEvent] = field(default_factory=list)
    audit_log: list[str] = field(default_factory=list)
    tool_metrics: list[ToolMetric] = field(default_factory=list)


class Observer:
    def __init__(self, telemetry: Telemetry | None = None) -> None:
        self._telemetry = telemetry or Telemetry()
        self._events: dict[str, list[TraceEvent]] = {}
        self._audit_logs: dict[str, list[str]] = {}
        self._tool_metrics: dict[str, dict[str, ToolMetric]] = {}
        self._records: dict[str, ObservationRecord] = {}
        self._session_index: dict[str, list[str]] = {}
        self._llm_calls: dict[str, LlmCallRecord] = {}

    def start(self, session_id: str) -> tuple[str, float]:
        trace_id, started_at = self._telemetry.start_trace(session_id)
        self._events[trace_id] = [TraceEvent(kind="trace_started", detail=f"session={session_id}")]
        self._audit_logs[trace_id] = [f"start session={session_id}"]
        self._tool_metrics[trace_id] = {}
        return trace_id, started_at

    def record_event(self, trace_id: str, kind: str, detail: str) -> None:
        self._events.setdefault(trace_id, []).append(TraceEvent(kind=kind, detail=detail))
        self._audit_logs.setdefault(trace_id, []).append(f"{kind}:{detail}")

    def record_tool_call(self, trace_id: str, tool_name: str) -> None:
        bucket = self._tool_metrics.setdefault(trace_id, {})
        metric = bucket.get(tool_name)
        if metric is None:
            metric = ToolMetric(tool_name=tool_name, calls=0)
            bucket[tool_name] = metric
        metric.calls += 1
        self.record_event(trace_id, "tool_called", tool_name)

    def record_llm_call_start(
        self,
        trace_id: str,
        session_id: str,
        *,
        provider: str,
        model: str,
        endpoint: str,
        request_preview: str,
    ) -> None:
        self._llm_calls[trace_id] = LlmCallRecord(
            trace_id=trace_id,
            session_id=session_id,
            provider=provider,
            model=model,
            endpoint=endpoint,
            status="started",
            started_at=time.perf_counter(),
            request_preview=request_preview,
            steps=[LlmCallStep(kind="llm_call_started", detail=f"{provider}:{model}")],
        )
        self.record_event(trace_id, "llm_call_started", f"{provider}:{model}")

    def record_llm_call_success(
        self,
        trace_id: str,
        response_preview: str,
        *,
        provider_trace_id: str = "",
        model: str = "",
    ) -> None:
        record = self._llm_calls.get(trace_id)
        if record is None:
            return
        record.status = "success"
        record.response_preview = response_preview
        if provider_trace_id:
            record.provider_trace_id = provider_trace_id
        if model:
            record.model = model
        record.latency_ms = int((time.perf_counter() - record.started_at) * 1000)
        detail = f"latency_ms={record.latency_ms}"
        if provider_trace_id:
            detail = f"{detail};provider_trace_id={provider_trace_id}"
        record.steps.append(LlmCallStep(kind="llm_call_succeeded", detail=detail))
        self.record_event(trace_id, "llm_call_succeeded", detail)

    def record_llm_call_failure(self, trace_id: str, error: str) -> None:
        record = self._llm_calls.get(trace_id)
        if record is None:
            return
        record.status = "error"
        record.error = error
        record.latency_ms = int((time.perf_counter() - record.started_at) * 1000)
        record.steps.append(LlmCallStep(kind="llm_call_failed", detail=error))
        self.record_event(trace_id, "llm_call_failed", error)

    def finish(self, trace_id: str, session_id: str, started_at: float, reply: str) -> ObservationRecord:
        trace = self._telemetry.finish_trace(trace_id, session_id, started_at)
        self.record_event(trace_id, "trace_finished", f"latency_ms={trace.latency_ms}")
        record = ObservationRecord(
            trace_id=trace.trace_id,
            session_id=trace.session_id,
            latency_ms=trace.latency_ms,
            score=score_response(reply),
            metrics={"reply_length": str(len(reply))},
            events=list(self._events.get(trace_id, [])),
            audit_log=list(self._audit_logs.get(trace_id, [])),
            tool_metrics=list(self._tool_metrics.get(trace_id, {}).values()),
        )
        self._records[trace_id] = record
        self._session_index.setdefault(session_id, []).append(trace_id)
        return record

    def get_trace(self, trace_id: str) -> ObservationRecord | None:
        return self._records.get(trace_id)

    def list_session_traces(self, session_id: str) -> list[ObservationRecord]:
        trace_ids = self._session_index.get(session_id, [])
        return [self._records[trace_id] for trace_id in trace_ids if trace_id in self._records]

    def get_llm_call(self, trace_id: str) -> LlmCallRecord | None:
        return self._llm_calls.get(trace_id)

    def list_session_llm_calls(self, session_id: str) -> list[LlmCallRecord]:
        trace_ids = self._session_index.get(session_id, [])
        return [self._llm_calls[trace_id] for trace_id in trace_ids if trace_id in self._llm_calls]
