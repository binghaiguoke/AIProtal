from __future__ import annotations

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from harness_app.bootstrap.app_factory import create_application_services
from harness_app.contracts.api.models import (
    AgentRequest,
    AgentResponse,
    CreateSessionRequest,
    KnowledgeDeleteResponse,
    KnowledgeFileListResponse,
    KnowledgeFileResponse,
    KnowledgeReindexResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSourceItem,
    KnowledgeUploadResponse,
    LlmCallFlowResponse,
    SessionDetailResponse,
    SessionHistoryItem,
    SessionResponse,
    TraceDetailResponse,
)
from harness_app.foundation.config_center.settings import load_settings


def create_app() -> FastAPI:
    settings = load_settings()
    services = create_application_services()
    engine = services.runtime_engine
    session_service = services.session_access
    observer_service = services.observer_access
    knowledge_service = services.knowledge_service
    app = FastAPI(title="MyPortal Agent Harness")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/sessions", response_model=SessionResponse)
    def create_session(payload: CreateSessionRequest) -> SessionResponse:
        session_id = engine.create_session(payload.user_id)
        return SessionResponse(session_id=session_id, user_id=payload.user_id, status="created")

    @app.get("/sessions/{session_id}", response_model=SessionDetailResponse)
    def get_session(session_id: str) -> SessionDetailResponse:
        detail = session_service.get_session_detail(session_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="session not found")
        return detail

    @app.get("/sessions/{session_id}/history", response_model=list[SessionHistoryItem])
    def get_session_history(session_id: str) -> list[SessionHistoryItem]:
        history = session_service.get_history(session_id)
        if history is None:
            raise HTTPException(status_code=404, detail="session not found")
        return history

    @app.get("/sessions/{session_id}/traces", response_model=list[TraceDetailResponse])
    def get_session_traces(session_id: str) -> list[TraceDetailResponse]:
        if session_service.get_session_owner(session_id) is None:
            raise HTTPException(status_code=404, detail="session not found")
        return observer_service.list_session_traces(session_id)

    @app.get("/traces/{trace_id}", response_model=TraceDetailResponse)
    def get_trace(trace_id: str) -> TraceDetailResponse:
        trace = observer_service.get_trace(trace_id)
        if trace is None:
            raise HTTPException(status_code=404, detail="trace not found")
        return trace

    @app.get("/traces/{trace_id}/llm-flow", response_model=LlmCallFlowResponse)
    def get_trace_llm_flow(trace_id: str) -> LlmCallFlowResponse:
        flow = observer_service.get_llm_flow(trace_id)
        if flow is None:
            raise HTTPException(status_code=404, detail="llm flow not found")
        return flow

    @app.get("/sessions/{session_id}/llm-flows", response_model=list[LlmCallFlowResponse])
    def get_session_llm_flows(session_id: str) -> list[LlmCallFlowResponse]:
        if session_service.get_session_owner(session_id) is None:
            raise HTTPException(status_code=404, detail="session not found")
        return observer_service.list_session_llm_flows(session_id)

    @app.post("/agent/respond", response_model=AgentResponse)
    def respond(payload: AgentRequest) -> AgentResponse:
        if not payload.message.strip():
            raise HTTPException(status_code=400, detail="message cannot be empty")
        return engine.handle_request(payload)

    @app.post("/knowledge/search", response_model=KnowledgeSearchResponse)
    def search_knowledge(payload: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
        if not payload.query.strip():
            raise HTTPException(status_code=400, detail="query cannot be empty")
        hits = knowledge_service.search(payload.query, payload.top_k)
        answer = knowledge_service.build_readable_answer(payload.query, hits)
        answer_scope = "uploaded_files" if any(hit.source_type == "upload" for hit in hits) else "default"
        return KnowledgeSearchResponse(
            query=payload.query,
            total_hits=len(hits),
            indexed_chunk_count=knowledge_service.indexed_chunk_count,
            answer=answer,
            answer_scope=answer_scope,
            sources=[
                KnowledgeSourceItem(
                    source_path=hit.source_path,
                    title=hit.title,
                    chunk_id=hit.chunk_id,
                    score=hit.score,
                    content=hit.content,
                )
                for hit in hits
            ],
        )

    @app.get("/knowledge/files", response_model=KnowledgeFileListResponse)
    def list_knowledge_files() -> KnowledgeFileListResponse:
        files = knowledge_service.list_files()
        return KnowledgeFileListResponse(
            files=[
                KnowledgeFileResponse(
                    file_id=item.file_id,
                    file_name=item.file_name,
                    source_path=item.source_path,
                    extension=item.extension,
                    size_bytes=item.size_bytes,
                    uploaded_at=item.uploaded_at,
                    extracted_text_length=item.extracted_text_length,
                    status=item.status,
                    notes=item.notes or [],
                )
                for item in files
            ]
        )

    @app.post("/knowledge/upload", response_model=KnowledgeUploadResponse)
    async def upload_knowledge_files(files: list[UploadFile] = File(...)) -> KnowledgeUploadResponse:
        uploaded_items: list[KnowledgeFileResponse] = []
        for file in files:
            data = await file.read()
            try:
                record, extraction = knowledge_service.save_upload(file.filename or "upload.bin", data)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            uploaded_items.append(
                KnowledgeFileResponse(
                    file_id=record.file_id,
                    file_name=record.file_name,
                    source_path=record.source_path,
                    extension=record.extension,
                    size_bytes=record.size_bytes,
                    uploaded_at=record.uploaded_at,
                    extracted_text_length=record.extracted_text_length,
                    status=record.status,
                    notes=extraction.notes,
                )
            )
        return KnowledgeUploadResponse(
            files=uploaded_items,
            indexed_chunk_count=knowledge_service.indexed_chunk_count,
        )

    @app.post("/knowledge/reindex", response_model=KnowledgeReindexResponse)
    def rebuild_knowledge_index() -> KnowledgeReindexResponse:
        status = knowledge_service.rebuild_index()
        return KnowledgeReindexResponse(
            indexed_chunk_count=status.indexed_chunk_count,
            indexed_document_count=status.indexed_document_count,
            uploaded_file_count=status.uploaded_file_count,
            rebuilt_at=status.rebuilt_at,
        )

    @app.delete("/knowledge/files/{file_id}", response_model=KnowledgeDeleteResponse)
    def delete_knowledge_file(file_id: str) -> KnowledgeDeleteResponse:
        deleted = knowledge_service.delete_file(file_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="knowledge file not found")
        return KnowledgeDeleteResponse(file_id=file_id, deleted=True)

    return app


app = create_app()


def run() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8080)
