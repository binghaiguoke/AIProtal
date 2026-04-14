from __future__ import annotations

from fastapi.testclient import TestClient

from harness_app.access.api_gateway.app import create_app
from harness_app.foundation.observability.observer import Observer


def test_observer_records_llm_call_flow():
    observer = Observer()
    trace_id, started_at = observer.start("session-1")
    observer.record_llm_call_start(
        trace_id,
        "session-1",
        provider="siliconflow",
        model="Pro/zai-org/GLM-5",
        endpoint="https://api.siliconflow.cn/v1/chat/completions",
        request_preview="messages=2",
    )
    observer.record_llm_call_success(
        trace_id,
        "hello from model",
        provider_trace_id="sf-trace-123",
        model="Pro/zai-org/GLM-5",
    )
    observer.finish(trace_id, "session-1", started_at, "fallback reply")

    flow = observer.get_llm_call(trace_id)

    assert flow is not None
    assert flow.status == "success"
    assert flow.provider_trace_id == "sf-trace-123"
    assert flow.endpoint.endswith("/chat/completions")
    assert flow.steps[0].kind == "llm_call_started"


def test_llm_flow_endpoints_return_trace_flow(monkeypatch):
    monkeypatch.setenv("MYPORTAL_ENV_FILE", "missing.env")
    monkeypatch.delenv("MYPORTAL_LLM_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPUAI_API_KEY", raising=False)
    client = TestClient(create_app())

    session_response = client.post("/sessions", json={"user_id": "api-user", "metadata": {}})
    session_id = session_response.json()["session_id"]
    respond_response = client.post(
        "/agent/respond",
        json={
            "user_id": "api-user",
            "session_id": session_id,
            "message": "hello model flow",
            "channel": "http",
            "metadata": {},
        },
    )
    trace_id = respond_response.json()["trace_id"]

    trace_flow_response = client.get(f"/traces/{trace_id}/llm-flow")
    session_flows_response = client.get(f"/sessions/{session_id}/llm-flows")

    assert trace_flow_response.status_code == 200
    assert session_flows_response.status_code == 200
    assert trace_flow_response.json()["trace_id"] == trace_id
    assert session_flows_response.json()[0]["session_id"] == session_id
