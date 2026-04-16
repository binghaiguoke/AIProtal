from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class PluginToolConfig:
    name: str
    kind: str
    template: str


@dataclass(slots=True)
class McpToolConfig:
    name: str
    transport: str
    template: str


@dataclass(slots=True)
class LlmBackendConfig:
    provider: str = "siliconflow"
    model: str = "Pro/zai-org/GLM-5"
    api_base_url: str = "https://api.siliconflow.cn/v1"
    api_key: str = ""
    timeout_seconds: float = 60.0
    temperature: float = 0.2
    max_tokens: int = 2048


@dataclass(slots=True)
class KnowledgeBaseConfig:
    source_paths: list[str] = field(
        default_factory=lambda: [
            "README.md",
            "MYPORTAL_FUNCTION_ANALYSIS.zh-CN.md",
            "portal-front/README.md",
        ]
    )
    default_top_k: int = 4
    chunk_size: int = 1200
    chunk_overlap: int = 150
    vector_dim: int = 768
    build_on_start: bool = False
    uploads_dir: str = "data/knowledge_uploads"
    allowed_extensions: list[str] = field(default_factory=lambda: [".docx", ".pptx", ".pdf"])
    max_upload_size_mb: int = 25
    enable_ocr_fallback: bool = True


@dataclass(slots=True)
class MyPortalSettings:
    app_name: str = "MyPortal Agent Harness"
    default_strategy: str = "react"
    llm: LlmBackendConfig = field(default_factory=LlmBackendConfig)
    knowledge_base: KnowledgeBaseConfig = field(default_factory=KnowledgeBaseConfig)
    cors_allowed_origins: list[str] = field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://localhost:5173",
            "http://localhost:5174",
        ]
    )
    allowed_tools: list[str] = field(
        default_factory=lambda: [
            "read_file",
            "run_shell",
            "web_search",
            "faiss_search",
            "brief",
            "portal_status",
            "mcp_echo",
        ]
    )
    plugin_tools: list[PluginToolConfig] = field(
        default_factory=lambda: [
            PluginToolConfig(
                name="portal_status",
                kind="status",
                template="[portal_status] topic={topic} status=ready",
            )
        ]
    )
    mcp_tools: list[McpToolConfig] = field(
        default_factory=lambda: [
            McpToolConfig(
                name="mcp_echo",
                transport="stub",
                template="[mcp_echo] payload={payload}",
            )
        ]
    )

    @property
    def project_root(self) -> Path:
        return _project_root()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip().strip("'\"")
    if not key:
        return None
    return key, value


def _load_dotenv_file() -> None:
    env_file = os.getenv("MYPORTAL_ENV_FILE")
    env_path = Path(env_file) if env_file else _project_root() / ".env"
    if not env_path.exists() or not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_env_line(line)
        if parsed is None:
            continue
        key, value = parsed
        # 使用 setdefault 保持向后兼容，但优先使用非空值
        existing = os.environ.get(key)
        if not existing:
            os.environ[key] = value


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return default
    items = [item.strip() for item in value.split(",")]
    return [item for item in items if item]


def load_settings() -> MyPortalSettings:
    _load_dotenv_file()
    return MyPortalSettings(
        cors_allowed_origins=_env_list(
            "MYPORTAL_CORS_ALLOWED_ORIGINS",
            [
                "http://127.0.0.1:5173",
                "http://127.0.0.1:5174",
                "http://localhost:5173",
                "http://localhost:5174",
            ],
        ),
        llm=LlmBackendConfig(
            provider=os.getenv("MYPORTAL_LLM_PROVIDER", "siliconflow"),
            model=os.getenv("MYPORTAL_LLM_MODEL", "Pro/zai-org/GLM-5"),
            api_base_url=os.getenv("MYPORTAL_LLM_API_BASE_URL", "https://api.siliconflow.cn/v1").rstrip("/"),
            api_key=os.getenv("MYPORTAL_LLM_API_KEY", os.getenv("ZHIPUAI_API_KEY", "")),
            timeout_seconds=_env_float("MYPORTAL_LLM_TIMEOUT_SECONDS", 60.0),
            temperature=_env_float("MYPORTAL_LLM_TEMPERATURE", 0.2),
            max_tokens=_env_int("MYPORTAL_LLM_MAX_TOKENS", 2048),
        ),
        knowledge_base=KnowledgeBaseConfig(
            source_paths=_env_list(
                "MYPORTAL_KNOWLEDGE_SOURCE_PATHS",
                [
                    "README.md",
                    "MYPORTAL_FUNCTION_ANALYSIS.zh-CN.md",
                    "portal-front/README.md",
                ],
            ),
            default_top_k=_env_int("MYPORTAL_KNOWLEDGE_TOP_K", 4),
            chunk_size=_env_int("MYPORTAL_KNOWLEDGE_CHUNK_SIZE", 1200),
            chunk_overlap=_env_int("MYPORTAL_KNOWLEDGE_CHUNK_OVERLAP", 150),
            vector_dim=_env_int("MYPORTAL_KNOWLEDGE_VECTOR_DIM", 768),
            build_on_start=bool(int(os.getenv("MYPORTAL_KNOWLEDGE_BUILD_ON_START", "0"))),
            uploads_dir=os.getenv("MYPORTAL_KNOWLEDGE_UPLOADS_DIR", "data/knowledge_uploads"),
            allowed_extensions=_env_list(
                "MYPORTAL_KNOWLEDGE_ALLOWED_EXTENSIONS",
                [".docx", ".pptx", ".pdf"],
            ),
            max_upload_size_mb=_env_int("MYPORTAL_KNOWLEDGE_MAX_UPLOAD_SIZE_MB", 25),
            enable_ocr_fallback=bool(int(os.getenv("MYPORTAL_KNOWLEDGE_ENABLE_OCR_FALLBACK", "1"))),
        ),
    )
