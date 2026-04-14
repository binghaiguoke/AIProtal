from __future__ import annotations

from harness_app.contracts.tooling.models import ToolCallSpec, ToolResult
from harness_app.knowledge.service import LocalKnowledgeService


def build_faiss_search_tool(knowledge_service: LocalKnowledgeService, default_top_k: int):
    def faiss_search_tool(spec: ToolCallSpec) -> ToolResult:
        query = str(spec.arguments.get("query", "")).strip()
        requested_top_k = int(spec.arguments.get("top_k", default_top_k) or default_top_k)
        hits = knowledge_service.search(query, requested_top_k)
        if not hits:
            return ToolResult(
                tool_name=spec.tool_name,
                content=f"[faiss_search] query={query}\nNo grounded sources found.",
            )

        lines = [f"[faiss_search] query={query} results={len(hits)}"]
        for index, hit in enumerate(hits, start=1):
            lines.extend(
                [
                    f"[{index}] source={hit.source_path} title={hit.title} chunk_id={hit.chunk_id} score={hit.score:.4f}",
                    hit.content,
                ]
            )
        return ToolResult(tool_name=spec.tool_name, content="\n".join(lines))

    return faiss_search_tool
