from __future__ import annotations

from dataclasses import dataclass

from harness_app.access.observer_access.service import ObserverAccessService
from harness_app.access.session_access.service import SessionAccessService
from harness_app.foundation.access_control.policy import PermissionPolicy
from harness_app.foundation.config_center.settings import load_settings
from harness_app.foundation.guardrails.guardrails import Guardrails
from harness_app.foundation.observability.observer import Observer
from harness_app.knowledge.service import LocalKnowledgeService
from harness_app.memory.context_builder.builder import ContextBuilder
from harness_app.memory.context_manager import ContextManager
from harness_app.memory.conversation_memory.store import SessionStore
from harness_app.orchestration.decision_engine.engine import DecisionEngine
from harness_app.orchestration.orchestrator import Orchestrator
from harness_app.orchestration.planner.planner import BasicPlanner
from harness_app.orchestration.router.router import AgentRouter
from harness_app.orchestration.workflow.workflow import WorkflowEngine
from harness_app.runtime.core.engine import RuntimeEngine
from harness_app.runtime.llm.glm5_client import Glm5Client
from harness_app.tooling.mcp_integration.client import McpClientManager
from harness_app.tooling.plugin_system.loader import PluginLoader
from harness_app.tooling.tool_adapters.basic_tools import (
    brief_tool,
    read_file_tool,
    run_shell_tool,
    web_search_tool,
)
from harness_app.tooling.tool_adapters.knowledge_tools import build_faiss_search_tool
from harness_app.tooling.tool_hub import ToolHub
from harness_app.tooling.tool_registry.registry import ToolRegistry


@dataclass(slots=True)
class ApplicationServices:
    runtime_engine: RuntimeEngine
    session_access: SessionAccessService
    observer_access: ObserverAccessService
    knowledge_service: LocalKnowledgeService


def create_application_services() -> ApplicationServices:
    settings = load_settings()
    project_root = settings.project_root
    session_store = SessionStore()
    context_builder = ContextBuilder(session_store)
    context_manager = ContextManager(context_builder)
    knowledge_service = LocalKnowledgeService(project_root, settings.knowledge_base)
    if settings.knowledge_base.build_on_start:
        knowledge_service.build_index()
    tool_registry = ToolRegistry()
    tool_registry.register("read_file", read_file_tool)
    tool_registry.register("run_shell", run_shell_tool)
    tool_registry.register("web_search", web_search_tool)
    tool_registry.register(
        "faiss_search",
        build_faiss_search_tool(knowledge_service, settings.knowledge_base.default_top_k),
    )
    tool_registry.register("brief", brief_tool)
    PluginLoader(settings.plugin_tools).register(tool_registry)
    McpClientManager(settings.mcp_tools).register(tool_registry)
    tool_hub = ToolHub(tool_registry, PermissionPolicy(settings.allowed_tools))
    orchestrator = Orchestrator(
        planner=BasicPlanner(),
        router=AgentRouter(),
        workflow_engine=WorkflowEngine(),
        decision_engine=DecisionEngine(),
    )
    observer = Observer()
    guardrails = Guardrails()
    llm_client = Glm5Client(settings.llm)

    runtime_engine = RuntimeEngine(
        orchestrator=orchestrator,
        context_manager=context_manager,
        session_store=session_store,
        tool_hub=tool_hub,
        observer=observer,
        guardrails=guardrails,
        llm_client=llm_client,
        knowledge_service=knowledge_service,
    )
    session_access = SessionAccessService(session_store)
    observer_access = ObserverAccessService(observer)
    return ApplicationServices(
        runtime_engine=runtime_engine,
        session_access=session_access,
        observer_access=observer_access,
        knowledge_service=knowledge_service,
    )
