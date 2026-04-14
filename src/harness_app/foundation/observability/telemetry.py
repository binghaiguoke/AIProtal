from __future__ import annotations

import time
from uuid import uuid4

from harness_app.contracts.foundation.models import ExecutionTrace


class Telemetry:
    def start_trace(self, session_id: str) -> tuple[str, float]:
        return uuid4().hex[:12], time.perf_counter()

    def finish_trace(self, trace_id: str, session_id: str, started_at: float) -> ExecutionTrace:
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        return ExecutionTrace(trace_id=trace_id, session_id=session_id, latency_ms=latency_ms)
