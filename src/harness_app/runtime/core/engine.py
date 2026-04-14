from __future__ import annotations

from harness_app.contracts.api.models import AgentRequest, AgentResponse
from harness_app.contracts.runtime.models import ExecutionResult
from harness_app.contracts.tooling.models import ToolCallSpec
from harness_app.foundation.guardrails.guardrails import Guardrails
from harness_app.foundation.observability.observer import Observer
from harness_app.knowledge.service import LocalKnowledgeService
from harness_app.memory.context_manager import ContextManager
from harness_app.memory.conversation_memory.store import SessionStore
from harness_app.orchestration.orchestrator import Orchestrator
from harness_app.runtime.llm.glm5_client import Glm5Client
from harness_app.tooling.tool_hub import ToolHub


class RuntimeEngine:
    def __init__(
        self,
        *,
        orchestrator: Orchestrator,
        context_manager: ContextManager,
        session_store: SessionStore,
        tool_hub: ToolHub,
        observer: Observer,
        guardrails: Guardrails,
        llm_client: Glm5Client,
        knowledge_service: LocalKnowledgeService,
    ) -> None:
        self._orchestrator = orchestrator
        self._context_manager = context_manager
        self._session_store = session_store
        self._tool_hub = tool_hub
        self._observer = observer
        self._guardrails = guardrails
        self._llm_client = llm_client
        self._knowledge_service = knowledge_service

    def create_session(self, user_id: str) -> str:
        return self._session_store.create_session(user_id)

    def handle_request(self, request: AgentRequest) -> AgentResponse:
        trace_id, started_at = self._observer.start(request.session_id)
        self._observer.record_event(trace_id, "request_received", request.message)
        self._session_store.append_turn(request.session_id, "user", request.message)

        bundle = self._orchestrator.build_bundle(request.message)
        self._observer.record_event(
            trace_id,
            "plan_created",
            f"strategy={bundle.plan.strategy};executor={bundle.executor_name};tools={','.join(bundle.tool_names) or 'none'}",
        )
        context = self._context_manager.build(request.session_id)
        self._observer.record_event(trace_id, "context_built", f"messages={len(context.messages)}")

        tool_results: list[str] = []
        grounded_sources: list[str] = []
        for tool_name in bundle.tool_names:
            self._observer.record_tool_call(trace_id, tool_name)
            arguments = {"query": request.message}
            if tool_name == "read_file":
                arguments = {"path": request.message}
            elif tool_name == "run_shell":
                arguments = {"command": request.message}
            elif tool_name == "faiss_search":
                arguments = {
                    "query": request.message,
                    "top_k": request.metadata.get("knowledge_top_k"),
                }
            elif tool_name == "portal_status":
                arguments = {"topic": "runtime"}
            elif tool_name == "mcp_echo":
                arguments = {"payload": request.message}
            result = self._tool_hub.execute(
                ToolCallSpec(
                    tool_name=tool_name,
                    arguments=arguments,
                    caller_id=request.user_id,
                    session_id=request.session_id,
                )
            )
            if not result.is_error:
                tool_results.append(result.content)
                if tool_name == "faiss_search":
                    grounded_sources.append(result.content)
                self._observer.record_event(trace_id, "tool_result", result.content)

        workflow_states = self._orchestrator.complete(bundle.workflow_states)
        fallback_reply = (
            f"[{bundle.plan.strategy}] executor={bundle.executor_name} goal={bundle.plan.goal}\n"
            f"context_messages={len(context.messages)}\n"
            f"workflow={','.join(state.status for state in workflow_states)}\n"
            f"tools={', '.join(tool_results) if tool_results else 'none'}"
        )
        reply = fallback_reply
        llm_messages = list(context.messages)
        llm_messages.append(
            {
                "role": "user",
                "content": (
                    f"User request: {request.message}\n"
                    f"Plan strategy: {bundle.plan.strategy}\n"
                    f"Executor: {bundle.executor_name}\n"
                    f"Workflow states: {', '.join(state.status for state in workflow_states)}\n"
                    f"Tool results: {', '.join(tool_results) if tool_results else 'none'}\n"
                    "Grounding rules:\n"
                    "- If grounded source snippets are present, answer only from those snippets.\n"
                    "- Cite source_path values when you rely on grounded snippets.\n"
                    "- If grounded snippets are insufficient, say that the local knowledge base does not contain enough evidence.\n"
                    f"Grounded source snippets:\n{'\n\n'.join(grounded_sources) if grounded_sources else 'none'}"
                ),
            }
        )
        request_preview = (
            f"system={context.system_prompt[:120]} | "
            f"messages={len(llm_messages)} | "
            f"tool_results={len(tool_results)}"
        )
        self._observer.record_llm_call_start(
            trace_id,
            request.session_id,
            provider=self._llm_client.provider,
            model=self._llm_client.model,
            endpoint=self._llm_client.endpoint,
            request_preview=request_preview,
        )
        try:
            llm_result = self._llm_client.generate(system_prompt=context.system_prompt, messages=llm_messages)
            reply = llm_result.content
            self._observer.record_llm_call_success(
                trace_id,
                reply[:500],
                provider_trace_id=llm_result.provider_trace_id,
                model=llm_result.raw_model,
            )
            self._observer.record_event(trace_id, "llm_reply_generated", f"provider={self._llm_client.provider}")
        except Exception as exc:
            self._observer.record_llm_call_failure(trace_id, str(exc))
            self._observer.record_event(trace_id, "llm_fallback", str(exc))
        reply = self._guardrails.sanitize_reply(reply)
        self._observer.record_event(trace_id, "reply_ready", reply.replace("\n", " | "))
        self._session_store.append_turn(request.session_id, "assistant", reply)
        trace = self._observer.finish(trace_id, request.session_id, started_at, reply)
        result = ExecutionResult(
            session_id=request.session_id,
            reply=reply,
            tool_results=tool_results,
            trace_id=trace.trace_id,
        )
        return AgentResponse(
            session_id=result.session_id,
            reply=result.reply,
            plan_strategy=bundle.plan.strategy,
            tool_results=result.tool_results,
            trace_id=result.trace_id,
        )
