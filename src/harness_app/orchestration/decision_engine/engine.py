from __future__ import annotations


class DecisionEngine:
    def should_use_tools(self, message: str) -> bool:
        lowered = message.lower()
        return any(
            token in lowered
            for token in ("search", "read", "run", "status", "mcp", "faiss", "rag", "文档", "检索", "搜索", "查找")
        )

    def decide_tool_names(self, message: str) -> list[str]:
        lowered = message.lower()
        tools: list[str] = []
        if any(token in lowered for token in ("search", "faiss", "rag", "文档", "检索", "搜索", "查找")):
            tools.append("faiss_search")
        if "read" in lowered:
            tools.append("read_file")
        if "run" in lowered:
            tools.append("run_shell")
        if "status" in lowered:
            tools.append("portal_status")
        if "mcp" in lowered:
            tools.append("mcp_echo")
        return tools
