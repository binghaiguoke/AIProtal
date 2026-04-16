# MyPortal 项目功能分析报告

## 项目概述

MyPortal 是一个基于 **FastAPI + Vue 3** 的 AI Agent Harness 项目，采用分层架构设计，集成了本地知识库 (RAG)、LLM 调用、工具系统、可观测性等核心能力。

### 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.11+, FastAPI, Pydantic |
| **前端** | Vue 3, TypeScript, Vite |
| **向量存储** | FAISS |
| **LLM** | GLM-5 (支持配置) |
| **文档处理** | PyPDF, python-docx, python-pptx |
| **OCR** | 可选 OCR 回退 |

---

## 架构分层

```
┌─────────────────────────────────────────────────────────────┐
│                      Access Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ API Gateway │  │Session Access│  │  Observer Access    │ │
│  │  (FastAPI)  │  │   (Service)  │  │    (Service)        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Contracts Layer                          │
│  - API Models  - Runtime Models  - Tooling Models           │
│  - Memory Models  - Foundation Models  - UI Models          │
├─────────────────────────────────────────────────────────────┤
│                   Orchestration Layer                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Planner  │  │  Router  │  │ Workflow │  │ Decision │   │
│  │ (计划)   │  │ (路由)   │  │ (工作流) │  │ (决策)   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                     Runtime Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │RuntimeEngine│  │ LLM Client  │  │   Knowledge Service │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     Tooling Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Tool    │  │  Plugin  │  │   MCP    │  │ Knowledge│   │
│  │ Registry │  │  System  │  │ Integration│  │  Tools   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                     Memory Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │Session Store│  │Context Builder│  │   Compression     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   Foundation Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Config  │  │ Guardrails│  │ Observer │  │  Access  │   │
│  │  Center  │  │ (护栏)   │  │(可观测性)│  │ Control  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 已实现功能

### 1. 会话管理 (Session Management)

**状态**: ✅ 已实现

| 功能 | 说明 |
|------|------|
| 创建会话 | `POST /sessions` |
| 获取会话详情 | `GET /sessions/{session_id}` |
| 获取会话历史 | `GET /sessions/{session_id}/history` |
| 消息存储 | 支持 user/assistant 角色存储 |

**代码位置**:
- `src/harness_app/access/session_access/service.py`
- `src/harness_app/memory/conversation_memory/store.py`

---

### 2. Agent 对话 (Agent Response)

**状态**: ✅ 已实现

| 功能 | 说明 |
|------|------|
| 消息处理 | `POST /agent/respond` |
| 工具调用 | 支持自动工具选择和执行 |
| LLM 集成 | GLM-5 客户端 |
| 上下文构建 | 自动构建对话上下文 |

**代码位置**:
- `src/harness_app/runtime/core/engine.py`
- `src/harness_app/runtime/llm/glm5_client.py`

---

### 3. 知识库系统 (Knowledge Base / RAG)

**状态**: ✅ 已实现

| 功能 | 说明 |
|------|------|
| 文件上传 | 支持 PDF, DOCX, PPTX, MD, TXT |
| 文档解析 | 文本提取 + OCR 回退 |
| 文本分块 | Markdown 分块器 |
| 向量嵌入 | HashingEmbedder (简化版) |
| 向量存储 | FAISS |
| 语义搜索 | `POST /knowledge/search` |
| 文件管理 | 列表、删除 |
| 索引重建 | `POST /knowledge/reindex` |

**代码位置**:
- `src/harness_app/knowledge/service.py`
- `src/harness_app/knowledge/faiss_store.py`
- `src/harness_app/knowledge/chunker.py`

---

### 4. 可观测性 (Observability)

**状态**: ✅ 已实现

| 功能 | 说明 |
|------|------|
| Trace 追踪 | 请求全链路追踪 |
| 事件记录 | 关键节点事件记录 |
| LLM Flow | LLM 调用流程记录 |
| 工具指标 | 工具调用统计 |
| 审计日志 | 操作审计 |

**API 端点**:
- `GET /sessions/{session_id}/traces`
- `GET /traces/{trace_id}`
- `GET /traces/{trace_id}/llm-flow`
- `GET /sessions/{session_id}/llm-flows`

**代码位置**:
- `src/harness_app/foundation/observability/observer.py`

---

### 5. 工具系统 (Tooling System)

**状态**: ⚠️ 部分实现 (Mock 级别)

| 工具 | 状态 | 说明 |
|------|------|------|
| `read_file` | ⚠️ Mock | 仅返回模拟结果 |
| `run_shell` | ⚠️ Mock | 仅返回模拟结果 |
| `web_search` | ⚠️ Mock | 仅返回模拟结果 |
| `faiss_search` | ✅ 实现 | 知识库搜索 |
| `brief` | ⚠️ Mock | 仅返回模拟结果 |

**代码位置**:
- `src/harness_app/tooling/tool_adapters/basic_tools.py`
- `src/harness_app/tooling/tool_adapters/knowledge_tools.py`

---

### 6. 编排系统 (Orchestration)

**状态**: ⚠️ 基础实现

| 组件 | 状态 | 说明 |
|------|------|------|
| Planner | ⚠️ 基础 | 简单关键词匹配策略 |
| Router | ⚠️ 基础 | 固定路由逻辑 |
| Workflow | ⚠️ 占位 | 状态标记，无实际工作流 |
| Decision Engine | ⚠️ 基础 | 关键词触发工具选择 |

**代码位置**:
- `src/harness_app/orchestration/orchestrator.py`
- `src/harness_app/orchestration/planner/planner.py`

---

### 7. 前端界面 (Frontend)

**状态**: ✅ 已实现

| 页面 | 功能 |
|------|------|
| Chat 页面 | 对话交互、Trace 查看、LLM Flow 查看 |
| Knowledge Base | 文件上传、搜索、LLM 分析 |

**代码位置**:
- `portal-front/src/App.vue`
- `portal-front/src/views/KnowledgeBasePage.vue`

---

## 功能占位与待开发项

### 🔴 高优先级 (核心功能缺失)

#### 1. 真实工具实现

| 工具 | 当前状态 | 需要实现 |
|------|----------|----------|
| `read_file` | Mock | 真实文件系统读取 |
| `run_shell` | Mock | 真实 Shell 执行 + 安全限制 |
| `web_search` | Mock | 集成搜索引擎 API |
| `write_file` | ❌ 缺失 | 文件写入工具 |
| `edit_file` | ❌ 缺失 | 文件编辑工具 |

**代码位置**: `src/harness_app/tooling/tool_adapters/basic_tools.py`

#### 2. 真实 LLM 客户端

| 功能 | 当前状态 | 需要实现 |
|------|----------|----------|
| GLM-5 调用 | ⚠️ 框架 | 完整的 HTTP API 调用 |
| 流式响应 | ❌ 缺失 | SSE 流式输出 |
| 多 Provider | ❌ 缺失 | OpenAI, Anthropic 等 |
| Token 计算 | ❌ 缺失 | Token 使用量统计 |

**代码位置**: `src/harness_app/runtime/llm/glm5_client.py`

#### 3. 真实嵌入模型

| 功能 | 当前状态 | 需要实现 |
|------|----------|----------|
| HashingEmbedder | ⚠️ 临时 | 真实 Embedding API |
| 向量维度 | 固定 128 | 可配置维度 |

**代码位置**: `src/harness_app/knowledge/embedder.py`

---

### 🟡 中优先级 (功能增强)

#### 4. MCP 集成完善

| 功能 | 当前状态 | 需要实现 |
|------|----------|----------|
| MCP Client | ⚠️ Mock | 真实 MCP 协议实现 |
| MCP 服务器发现 | ❌ 缺失 | 自动发现 MCP 服务 |
| MCP 工具调用 | ❌ 缺失 | 标准 MCP 调用流程 |

**代码位置**: `src/harness_app/tooling/mcp_integration/client.py`

#### 5. Plugin 系统完善

| 功能 | 当前状态 | 需要实现 |
|------|----------|----------|
| Plugin Loader | ⚠️ Mock | 动态加载外部插件 |
| Plugin 生命周期 | ❌ 缺失 | 安装/卸载/启用/禁用 |
| Plugin 市场 | ❌ 缺失 | 插件仓库集成 |

**代码位置**: `src/harness_app/tooling/plugin_system/loader.py`

#### 6. 工作流引擎

| 功能 | 当前状态 | 需要实现 |
|------|----------|----------|
| WorkflowEngine | ⚠️ 占位 | 真实工作流执行 |
| 状态机 | ❌ 缺失 | 复杂状态流转 |
| 并行执行 | ❌ 缺失 | 多步骤并行 |

**代码位置**: `src/harness_app/orchestration/workflow/workflow.py`

#### 7. 智能编排增强

| 功能 | 当前状态 | 需要实现 |
|------|----------|----------|
| Planner | ⚠️ 关键词 | LLM-based 计划生成 |
| Router | ⚠️ 固定 | 智能路由决策 |
| Decision Engine | ⚠️ 简单 | 意图识别 + 工具推荐 |

---

### 🟢 低优先级 (优化完善)

#### 8. 访问控制完善

| 功能 | 当前状态 | 需要实现 |
|------|----------|----------|
| PermissionPolicy | ⚠️ 简单 | RBAC 权限模型 |
| 用户认证 | ❌ 缺失 | JWT/OAuth 集成 |
| API 限流 | ❌ 缺失 | Rate Limiting |

**代码位置**: `src/harness_app/foundation/access_control/policy.py`

#### 9. 护栏系统完善

| 功能 | 当前状态 | 需要实现 |
|------|----------|----------|
| Guardrails | ⚠️ 简单 | 内容安全检测 |
| 敏感词过滤 | ⚠️ 基础 | 完整敏感词库 |
| 输出审核 | ❌ 缺失 | 输出内容审核 |

**代码位置**: `src/harness_app/foundation/guardrails/guardrails.py`

#### 10. 评估系统

| 功能 | 当前状态 | 需要实现 |
|------|----------|----------|
| Scoring | ⚠️ 占位 | 响应质量评估 |
| 人工反馈 | ❌ 缺失 | 点赞/点踩反馈 |
| A/B 测试 | ❌ 缺失 | 模型对比测试 |

**代码位置**: `src/harness_app/foundation/evaluation/scoring.py`

#### 11. 上下文压缩

| 功能 | 当前状态 | 需要实现 |
|------|----------|----------|
| Compression | ⚠️ 占位 | 消息历史压缩 |
| 摘要生成 | ❌ 缺失 | 长对话摘要 |

**代码位置**: `src/harness_app/memory/compression/compact.py`

#### 12. 前端功能增强

| 功能 | 当前状态 | 需要实现 |
|------|----------|----------|
| 主题切换 | ❌ 缺失 | 暗黑/亮色模式 |
| 代码高亮 | ❌ 缺失 | Markdown 代码块 |
| 文件预览 | ❌ 缺失 | 知识库文件预览 |
| 实时推送 | ❌ 缺失 | WebSocket 流式 |

---

## API 端点清单

### 已实现端点

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/sessions` | 创建会话 |
| GET | `/sessions/{id}` | 获取会话详情 |
| GET | `/sessions/{id}/history` | 获取会话历史 |
| GET | `/sessions/{id}/traces` | 获取会话 Trace |
| GET | `/sessions/{id}/llm-flows` | 获取会话 LLM Flow |
| GET | `/traces/{id}` | 获取 Trace 详情 |
| GET | `/traces/{id}/llm-flow` | 获取 LLM Flow 详情 |
| POST | `/agent/respond` | Agent 对话 |
| POST | `/knowledge/search` | 知识库搜索 |
| GET | `/knowledge/files` | 获取文件列表 |
| POST | `/knowledge/upload` | 上传文件 |
| POST | `/knowledge/reindex` | 重建索引 |
| DELETE | `/knowledge/files/{id}` | 删除文件 |

### 待实现端点

| 方法 | 端点 | 功能 | 优先级 |
|------|------|------|--------|
| POST | `/auth/login` | 用户登录 | 🔴 |
| POST | `/auth/logout` | 用户登出 | 🔴 |
| GET | `/tools` | 工具列表 | 🟡 |
| POST | `/tools/execute` | 执行工具 | 🟡 |
| GET | `/plugins` | 插件列表 | 🟡 |
| POST | `/plugins/install` | 安装插件 | 🟡 |
| DELETE | `/plugins/{id}` | 卸载插件 | 🟡 |
| GET | `/workflows` | 工作流列表 | 🟡 |
| POST | `/workflows/execute` | 执行工作流 | 🟡 |

---

## 配置文件

### 当前配置项 (`.env.example`)

```bash
# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# LLM
LLM_PROVIDER=glm5
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.glm5.example.com
LLM_MODEL=glm5-chat

# Knowledge Base
KNOWLEDGE_UPLOADS_DIR=uploads
KNOWLEDGE_SOURCE_PATHS=docs,knowledge
KNOWLEDGE_CHUNK_SIZE=800
KNOWLEDGE_CHUNK_OVERLAP=100
KNOWLEDGE_VECTOR_DIM=128
KNOWLEDGE_DEFAULT_TOP_K=4
KNOWLEDGE_MAX_UPLOAD_SIZE_MB=50
KNOWLEDGE_ALLOWED_EXTENSIONS=.pdf,.docx,.pptx,.md,.txt
KNOWLEDGE_ENABLE_OCR_FALLBACK=false
KNOWLEDGE_BUILD_ON_START=true

# Tools
ALLOWED_TOOLS=read_file,run_shell,web_search,faiss_search,brief

# Plugins (JSON array)
PLUGIN_TOOLS=[]

# MCP Tools (JSON array)
MCP_TOOLS=[]
```

---

## 开发建议

### 第一阶段：核心功能完善 (🔴)

1. **实现真实工具**
   - 文件读写工具
   - Shell 执行工具 (带安全沙箱)
   - Web 搜索工具 (集成 Serper/Bing API)

2. **完善 LLM 客户端**
   - 实现 GLM-5 HTTP API 调用
   - 添加流式响应支持
   - 添加重试和错误处理

3. **替换嵌入模型**
   - 集成真实 Embedding API
   - 支持向量维度配置

### 第二阶段：系统集成 (🟡)

1. **MCP 协议实现**
   - 标准 MCP 客户端
   - 支持 MCP 工具发现

2. **Plugin 系统**
   - 动态插件加载
   - 插件生命周期管理

3. **智能编排**
   - LLM-based Planner
   - 意图识别

### 第三阶段：优化增强 (🟢)

1. **访问控制**
   - 用户认证
   - 权限管理

2. **前端完善**
   - 流式输出
   - 主题切换
   - 代码高亮

3. **可观测性**
   - 指标收集
   - 告警系统

---

## 总结

MyPortal 项目已经搭建了一个完整的 AI Agent Harness 框架，具备以下核心能力：

✅ **已完成**:
- 分层架构设计
- 会话管理
- Agent 对话流程
- 本地知识库 (RAG)
- 可观测性系统
- 前端界面

⚠️ **部分实现**:
- 工具系统 (Mock 级别)
- 编排系统 (基础实现)
- MCP/Plugin (框架占位)

❌ **待开发**:
- 真实工具实现
- 流式响应
- 用户认证
- 智能编排

项目整体架构清晰，代码组织良好，具备良好的扩展性。建议按照优先级逐步完善核心功能。
