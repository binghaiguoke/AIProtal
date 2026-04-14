export interface SessionResponse {
  session_id: string
  user_id: string
  status: string
}

export interface SessionHistoryItem {
  role: 'user' | 'assistant' | string
  content: string
}

export interface TraceDetailResponse {
  trace_id: string
  session_id: string
  latency_ms: number
  score: number
  metrics: Record<string, string>
  events: TraceEventResponse[]
  audit_log: string[]
  tool_metrics: ToolMetricResponse[]
}

export interface TraceEventResponse {
  kind: string
  detail: string
}

export interface ToolMetricResponse {
  tool_name: string
  calls: number
}

export interface AgentResponse {
  session_id: string
  reply: string
  plan_strategy: string
  tool_results: string[]
  trace_id: string
}

export interface LlmCallStepResponse {
  kind: string
  detail: string
}

export interface LlmCallFlowResponse {
  trace_id: string
  session_id: string
  provider: string
  model: string
  endpoint: string
  provider_trace_id: string
  status: string
  latency_ms: number
  request_preview: string
  response_preview: string
  error: string
  steps: LlmCallStepResponse[]
}

export interface KnowledgeSourceItem {
  source_path: string
  title: string
  chunk_id: string
  score: number
  content: string
}

export interface KnowledgeSearchResponse {
  query: string
  total_hits: number
  indexed_chunk_count: number
  sources: KnowledgeSourceItem[]
}

export interface KnowledgeFileResponse {
  file_id: string
  file_name: string
  source_path: string
  extension: string
  size_bytes: number
  uploaded_at: string
  extracted_text_length: number
  status: string
  notes: string[]
}

export interface KnowledgeFileListResponse {
  files: KnowledgeFileResponse[]
}

export interface KnowledgeUploadResponse {
  files: KnowledgeFileResponse[]
  indexed_chunk_count: number
}

export interface KnowledgeReindexResponse {
  indexed_chunk_count: number
  indexed_document_count: number
  uploaded_file_count: number
  rebuilt_at: string | null
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8080').replace(/\/$/, '')

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers || {})
  if (!(init?.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers,
    ...init,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed with status ${response.status}`)
  }

  return response.json() as Promise<T>
}

export function getApiBaseUrl(): string {
  return API_BASE_URL
}

export function createSession(userId: string): Promise<SessionResponse> {
  return request<SessionResponse>('/sessions', {
    method: 'POST',
    body: JSON.stringify({
      user_id: userId,
      metadata: {
        source: 'portal-front',
      },
    }),
  })
}

export function sendMessage(payload: {
  userId: string
  sessionId: string
  message: string
}): Promise<AgentResponse> {
  return request<AgentResponse>('/agent/respond', {
    method: 'POST',
    body: JSON.stringify({
      user_id: payload.userId,
      session_id: payload.sessionId,
      message: payload.message,
      channel: 'web',
      metadata: {
        source: 'portal-front',
      },
    }),
  })
}

export function fetchHistory(sessionId: string): Promise<SessionHistoryItem[]> {
  return request<SessionHistoryItem[]>(`/sessions/${sessionId}/history`)
}

export function fetchTraces(sessionId: string): Promise<TraceDetailResponse[]> {
  return request<TraceDetailResponse[]>(`/sessions/${sessionId}/traces`)
}

export function fetchTrace(traceId: string): Promise<TraceDetailResponse> {
  return request<TraceDetailResponse>(`/traces/${traceId}`)
}

export function fetchLlmFlow(traceId: string): Promise<LlmCallFlowResponse> {
  return request<LlmCallFlowResponse>(`/traces/${traceId}/llm-flow`)
}

export function fetchSessionLlmFlows(sessionId: string): Promise<LlmCallFlowResponse[]> {
  return request<LlmCallFlowResponse[]>(`/sessions/${sessionId}/llm-flows`)
}

export function fetchKnowledgeFiles(): Promise<KnowledgeFileListResponse> {
  return request<KnowledgeFileListResponse>('/knowledge/files')
}

export function searchKnowledge(query: string, topK = 5): Promise<KnowledgeSearchResponse> {
  return request<KnowledgeSearchResponse>('/knowledge/search', {
    method: 'POST',
    body: JSON.stringify({
      query,
      top_k: topK,
    }),
  })
}

export function rebuildKnowledgeIndex(): Promise<KnowledgeReindexResponse> {
  return request<KnowledgeReindexResponse>('/knowledge/reindex', {
    method: 'POST',
  })
}

export function uploadKnowledgeFiles(files: File[]): Promise<KnowledgeUploadResponse> {
  const formData = new FormData()
  for (const file of files) {
    formData.append('files', file)
  }
  return request<KnowledgeUploadResponse>('/knowledge/upload', {
    method: 'POST',
    body: formData,
  })
}

export function deleteKnowledgeFile(fileId: string): Promise<{ file_id: string; deleted: boolean }> {
  return request<{ file_id: string; deleted: boolean }>(`/knowledge/files/${fileId}`, {
    method: 'DELETE',
  })
}
