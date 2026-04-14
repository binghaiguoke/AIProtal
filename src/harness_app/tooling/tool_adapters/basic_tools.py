from __future__ import annotations

from harness_app.contracts.tooling.models import ToolCallSpec, ToolResult


def read_file_tool(spec: ToolCallSpec) -> ToolResult:
    path = str(spec.arguments.get("path", ""))
    return ToolResult(tool_name=spec.tool_name, content=f"[read_file] path={path}")


def run_shell_tool(spec: ToolCallSpec) -> ToolResult:
    command = str(spec.arguments.get("command", ""))
    return ToolResult(tool_name=spec.tool_name, content=f"[run_shell] command={command}")


def web_search_tool(spec: ToolCallSpec) -> ToolResult:
    query = str(spec.arguments.get("query", ""))
    return ToolResult(tool_name=spec.tool_name, content=f"[web_search] query={query}")


def brief_tool(spec: ToolCallSpec) -> ToolResult:
    topic = str(spec.arguments.get("topic", "general"))
    return ToolResult(tool_name=spec.tool_name, content=f"[brief] topic={topic}")
