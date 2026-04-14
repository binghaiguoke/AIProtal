<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KnowledgeBasePage from './views/KnowledgeBasePage.vue'

import {
  createSession,
  fetchTrace,
  fetchHistory,
  fetchLlmFlow,
  fetchSessionLlmFlows,
  fetchTraces,
  getApiBaseUrl,
  sendMessage,
  type LlmCallFlowResponse,
  type SessionHistoryItem,
  type TraceDetailResponse,
} from './api'

type TimelineItem = {
  id: string
  title: string
  detail: string
  source: 'trace' | 'llm' | 'tool'
}

const userId = ref('bingh')
const draft = ref('')
const sessionId = ref('')
const traceId = ref('')
const messages = ref<SessionHistoryItem[]>([])
const traces = ref<TraceDetailResponse[]>([])
const llmFlows = ref<LlmCallFlowResponse[]>([])
const activeTrace = ref<TraceDetailResponse | null>(null)
const activeLlmFlow = ref<LlmCallFlowResponse | null>(null)
const toolResults = ref<string[]>([])
const isCreatingSession = ref(false)
const isSending = ref(false)
const errorMessage = ref('')
const currentView = ref<'chat' | 'knowledge'>('chat')

const apiBaseUrl = getApiBaseUrl()

const canSend = computed(() => Boolean(sessionId.value.trim()) && Boolean(draft.value.trim()) && !isSending.value)
const processTimeline = computed<TimelineItem[]>(() => {
  const items: TimelineItem[] = []

  if (activeTrace.value) {
    for (const [index, event] of activeTrace.value.events.entries()) {
      items.push({
        id: `trace-${index}-${event.kind}`,
        title: event.kind,
        detail: event.detail,
        source: 'trace',
      })
    }
  }

  if (toolResults.value.length > 0) {
    for (const [index, result] of toolResults.value.entries()) {
      items.push({
        id: `tool-${index}`,
        title: 'tool_result',
        detail: result,
        source: 'tool',
      })
    }
  }

  if (activeLlmFlow.value) {
    for (const [index, step] of activeLlmFlow.value.steps.entries()) {
      items.push({
        id: `llm-${index}-${step.kind}`,
        title: step.kind,
        detail: step.detail,
        source: 'llm',
      })
    }
  }

  return items
})

async function refreshSessionState() {
  if (!sessionId.value) {
    return
  }
  const [history, traceItems, flowItems] = await Promise.all([
    fetchHistory(sessionId.value),
    fetchTraces(sessionId.value),
    fetchSessionLlmFlows(sessionId.value),
  ])
  messages.value = history
  traces.value = [...traceItems].reverse()
  llmFlows.value = [...flowItems].reverse()
  activeTrace.value = traces.value[0] || null
  activeLlmFlow.value = llmFlows.value[0] || null
}

async function selectTrace(trace: TraceDetailResponse) {
  activeTrace.value = trace
  traceId.value = trace.trace_id
  try {
    activeLlmFlow.value = await fetchLlmFlow(trace.trace_id)
  } catch {
    activeLlmFlow.value = null
  }
}

async function handleCreateSession() {
  errorMessage.value = ''
  isCreatingSession.value = true
  try {
    const session = await createSession(userId.value.trim() || 'guest')
    sessionId.value = session.session_id
    messages.value = []
    traces.value = []
    llmFlows.value = []
    activeTrace.value = null
    activeLlmFlow.value = null
    toolResults.value = []
    traceId.value = ''
    draft.value = ''
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to create session'
  } finally {
    isCreatingSession.value = false
  }
}

async function handleSendMessage() {
  if (!canSend.value) {
    return
  }
  errorMessage.value = ''
  isSending.value = true
  const outgoingMessage = draft.value.trim()
  try {
    messages.value = [
      ...messages.value,
      {
        role: 'user',
        content: outgoingMessage,
      },
    ]
    const response = await sendMessage({
      userId: userId.value.trim() || 'guest',
      sessionId: sessionId.value,
      message: outgoingMessage,
    })
    traceId.value = response.trace_id
    toolResults.value = response.tool_results
    messages.value = [
      ...messages.value,
      {
        role: 'assistant',
        content: response.reply,
      },
    ]
    draft.value = ''
    const [trace, flow] = await Promise.all([
      fetchTrace(response.trace_id),
      fetchLlmFlow(response.trace_id),
    ])
    traces.value = [trace, ...traces.value.filter((item) => item.trace_id !== trace.trace_id)]
    llmFlows.value = [flow, ...llmFlows.value.filter((item) => item.trace_id !== flow.trace_id)]
    activeTrace.value = trace
    activeLlmFlow.value = flow
    void refreshSessionState()
  } catch (error) {
    messages.value = messages.value.filter(
      (message, index) => !(index === messages.value.length - 1 && message.role === 'user' && message.content === outgoingMessage),
    )
    errorMessage.value = error instanceof Error ? error.message : 'Failed to send message'
  } finally {
    isSending.value = false
  }
}

onMounted(() => {
  void handleCreateSession()
})
</script>

<template>
  <div class="chat-shell">
    <aside class="sidebar">
      <div class="brand">
        <p class="eyebrow">portal-front</p>
        <h1>{{ currentView === 'chat' ? 'Chat Console' : 'Knowledge Base' }}</h1>
        <p class="muted">
          {{ currentView === 'chat' ? 'Vue 前端页面已接入 MyPortal FastAPI 聊天服务。' : '上传文件、重建索引并查询本地知识库。' }}
        </p>
      </div>

      <section class="panel">
        <div class="view-toggle">
          <button
            class="secondary-button"
            :class="currentView === 'chat' ? 'secondary-button-active' : ''"
            @click="currentView = 'chat'"
          >
            Chat
          </button>
          <button
            class="secondary-button"
            :class="currentView === 'knowledge' ? 'secondary-button-active' : ''"
            @click="currentView = 'knowledge'"
          >
            Knowledge
          </button>
        </div>
      </section>

      <section v-if="currentView === 'chat'" class="panel">
        <label class="field-label" for="userId">User ID</label>
        <input id="userId" v-model="userId" class="text-input" placeholder="请输入用户标识" />

        <button class="primary-button" :disabled="isCreatingSession" @click="handleCreateSession">
          {{ isCreatingSession ? '创建中...' : '新建会话' }}
        </button>

        <div class="meta-list">
          <div>
            <span class="meta-label">API</span>
            <code>{{ apiBaseUrl }}</code>
          </div>
          <div>
            <span class="meta-label">Session</span>
            <code>{{ sessionId || '未创建' }}</code>
          </div>
          <div>
            <span class="meta-label">Latest Trace</span>
            <code>{{ traceId || '暂无' }}</code>
          </div>
        </div>
      </section>

      <section v-if="currentView === 'chat'" class="panel">
        <h2>最近 Traces</h2>
        <ul class="trace-list">
          <li
            v-for="trace in traces.slice(0, 5)"
            :key="trace.trace_id"
            class="trace-card"
            :class="trace.trace_id === traceId ? 'trace-card-active' : ''"
            @click="selectTrace(trace)"
          >
            <strong>{{ trace.trace_id }}</strong>
            <span>{{ trace.latency_ms }} ms</span>
            <span>score={{ trace.score }}</span>
          </li>
          <li v-if="traces.length === 0" class="empty-state">当前还没有 trace</li>
        </ul>
      </section>

      <section v-if="currentView === 'chat'" class="panel">
        <h2>LLM 调用</h2>
        <div v-if="activeLlmFlow" class="llm-flow-summary">
          <div>
            <span class="meta-label">Provider</span>
            <code>{{ activeLlmFlow.provider }}</code>
          </div>
          <div>
            <span class="meta-label">Model</span>
            <code>{{ activeLlmFlow.model }}</code>
          </div>
          <div>
            <span class="meta-label">Status</span>
            <code>{{ activeLlmFlow.status }}</code>
          </div>
          <div>
            <span class="meta-label">Latency</span>
            <code>{{ activeLlmFlow.latency_ms }} ms</code>
          </div>
          <div>
            <span class="meta-label">Provider Trace</span>
            <code>{{ activeLlmFlow.provider_trace_id || '暂无' }}</code>
          </div>
        </div>
        <p v-else class="empty-state">当前还没有 LLM 调用记录。</p>
      </section>
    </aside>

    <main v-if="currentView === 'chat'" class="chat-main">
      <section class="panel messages-panel">
        <div class="panel-header">
          <div>
            <h2>聊天记录</h2>
            <p class="muted">消息会通过 `/agent/respond` 与后端聊天流程关联。</p>
          </div>
        </div>

        <div class="messages">
          <article
            v-for="(message, index) in messages"
            :key="`${message.role}-${index}`"
            class="message"
            :class="message.role === 'user' ? 'message-user' : 'message-assistant'"
          >
            <div class="message-role">{{ message.role === 'user' ? '你' : 'MyPortal' }}</div>
            <pre class="message-content">{{ message.content }}</pre>
          </article>
          <div v-if="messages.length === 0" class="empty-state">
            当前还没有消息，直接发送第一条内容即可开始聊天。
          </div>
        </div>
      </section>

      <section class="panel composer-panel">
        <label class="field-label" for="draft">输入消息</label>
        <textarea
          id="draft"
          v-model="draft"
          class="composer"
          rows="5"
          placeholder="例如：你好，请记住我的名字，并告诉我你能做什么。"
          @keydown.ctrl.enter.prevent="handleSendMessage"
        />

        <div class="composer-actions">
          <p class="muted">按 `Ctrl + Enter` 可快速发送。</p>
          <button class="primary-button" :disabled="!canSend" @click="handleSendMessage">
            {{ isSending ? '发送中...' : '发送消息' }}
          </button>
        </div>

        <div v-if="toolResults.length > 0" class="tool-results">
          <h3>本轮工具结果</h3>
          <ul>
            <li v-for="(result, index) in toolResults" :key="index">
              <code>{{ result }}</code>
            </li>
          </ul>
        </div>

        <div v-if="processTimeline.length > 0" class="timeline-panel">
          <h3>过程时间线</h3>
          <ul class="timeline-list">
            <li v-for="item in processTimeline" :key="item.id" class="timeline-item">
              <span class="timeline-source" :class="`timeline-source-${item.source}`">{{ item.source }}</span>
              <div class="timeline-content">
                <strong>{{ item.title }}</strong>
                <span>{{ item.detail }}</span>
              </div>
            </li>
          </ul>
        </div>

        <div v-if="activeTrace" class="trace-details">
          <h3>本轮过程信息</h3>
          <div class="trace-detail-grid">
            <div>
              <span class="meta-label">Trace</span>
              <code>{{ activeTrace.trace_id }}</code>
            </div>
            <div>
              <span class="meta-label">Score</span>
              <code>{{ activeTrace.score }}</code>
            </div>
            <div>
              <span class="meta-label">Latency</span>
              <code>{{ activeTrace.latency_ms }} ms</code>
            </div>
            <div>
              <span class="meta-label">Metrics</span>
              <code>{{ JSON.stringify(activeTrace.metrics) }}</code>
            </div>
          </div>

          <ul class="trace-step-list">
            <li v-for="(event, index) in activeTrace.events" :key="`${event.kind}-${index}`">
              <strong>{{ event.kind }}</strong>
              <span>{{ event.detail }}</span>
            </li>
          </ul>

          <div v-if="activeTrace.audit_log.length > 0" class="trace-audit">
            <h3>审计日志</h3>
            <ul class="trace-step-list">
              <li v-for="(entry, index) in activeTrace.audit_log" :key="`${entry}-${index}`">
                <span>{{ entry }}</span>
              </li>
            </ul>
          </div>
        </div>

        <div v-if="activeLlmFlow" class="llm-details">
          <h3>最近一轮模型调用轨迹</h3>
          <div class="llm-detail-grid">
            <div>
              <span class="meta-label">Endpoint</span>
              <code>{{ activeLlmFlow.endpoint }}</code>
            </div>
            <div>
              <span class="meta-label">Request Preview</span>
              <code>{{ activeLlmFlow.request_preview || '暂无' }}</code>
            </div>
            <div>
              <span class="meta-label">Response Preview</span>
              <code>{{ activeLlmFlow.response_preview || '暂无' }}</code>
            </div>
            <div>
              <span class="meta-label">Error</span>
              <code>{{ activeLlmFlow.error || '无' }}</code>
            </div>
          </div>

          <ul class="llm-step-list">
            <li v-for="(step, index) in activeLlmFlow.steps" :key="`${step.kind}-${index}`">
              <strong>{{ step.kind }}</strong>
              <span>{{ step.detail }}</span>
            </li>
          </ul>
        </div>

        <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      </section>
    </main>

    <main v-else class="chat-main">
      <KnowledgeBasePage />
    </main>
  </div>
</template>
