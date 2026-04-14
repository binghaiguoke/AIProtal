from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from harness_app.contracts.ui.models import MessagePart


class AgentRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
    channel: str = "http"
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreateSessionRequest(BaseModel):
    user_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    status: str


class SessionHistoryItem(BaseModel):
    role: str
    content: str
    parts: list[MessagePart] = Field(default_factory=list)


class SessionDetailResponse(BaseModel):
    session_id: str
    user_id: str
    message_count: int
    history: list[SessionHistoryItem] = Field(default_factory=list)


class TraceEventResponse(BaseModel):
    kind: str
    detail: str


class ToolMetricResponse(BaseModel):
    tool_name: str
    calls: int


class TraceDetailResponse(BaseModel):
    trace_id: str
    session_id: str
    latency_ms: int
    score: float
    metrics: dict[str, str] = Field(default_factory=dict)
    events: list[TraceEventResponse] = Field(default_factory=list)
    audit_log: list[str] = Field(default_factory=list)
    tool_metrics: list[ToolMetricResponse] = Field(default_factory=list)


class LlmCallStepResponse(BaseModel):
    kind: str
    detail: str


class LlmCallFlowResponse(BaseModel):
    trace_id: str
    session_id: str
    provider: str
    model: str
    endpoint: str
    provider_trace_id: str = ""
    status: str
    latency_ms: int
    request_preview: str = ""
    response_preview: str = ""
    error: str = ""
    steps: list[LlmCallStepResponse] = Field(default_factory=list)


class KnowledgeSearchRequest(BaseModel):
    query: str
    top_k: int = 4


class KnowledgeSourceItem(BaseModel):
    source_path: str
    title: str
    chunk_id: str
    score: float
    content: str


class KnowledgeSearchResponse(BaseModel):
    query: str
    total_hits: int
    indexed_chunk_count: int
    sources: list[KnowledgeSourceItem] = Field(default_factory=list)


class KnowledgeFileResponse(BaseModel):
    file_id: str
    file_name: str
    source_path: str
    extension: str
    size_bytes: int
    uploaded_at: datetime
    extracted_text_length: int = 0
    status: str
    notes: list[str] = Field(default_factory=list)


class KnowledgeFileListResponse(BaseModel):
    files: list[KnowledgeFileResponse] = Field(default_factory=list)


class KnowledgeUploadResponse(BaseModel):
    files: list[KnowledgeFileResponse] = Field(default_factory=list)
    indexed_chunk_count: int


class KnowledgeReindexResponse(BaseModel):
    indexed_chunk_count: int
    indexed_document_count: int
    uploaded_file_count: int
    rebuilt_at: datetime | None = None


class KnowledgeDeleteResponse(BaseModel):
    file_id: str
    deleted: bool


class AgentResponse(BaseModel):
    session_id: str
    reply: str
    plan_strategy: str
    tool_results: list[str] = Field(default_factory=list)
    parts: list[MessagePart] = Field(default_factory=list)
    trace_id: str
