<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import {
  createSession,
  deleteKnowledgeFile,
  fetchKnowledgeFiles,
  rebuildKnowledgeIndex,
  searchKnowledge,
  sendMessage,
  uploadKnowledgeFiles,
  type KnowledgeFileResponse,
  type KnowledgeReindexResponse,
  type KnowledgeSearchResponse,
  type KnowledgeSourceItem,
} from '../api'

const MAX_SOURCE_CHARS = 2400

function buildKnowledgeLlmMessage(response: KnowledgeSearchResponse): string {
  const lines: string[] = []
  lines.push('请根据下方「用户问题」与「知识库已取回的片段」作答。')
  lines.push('- 优先依据片段内容，不要编造片段中不存在的结论。')
  lines.push('- 若证据不足请明确说明。')
  lines.push('- 引用时请写出 source_path。')
  lines.push('')
  lines.push('【用户问题】')
  lines.push(response.query)
  lines.push('')
  lines.push('【本地知识库可读摘要】（规则生成，仅供参考）')
  lines.push(response.answer.trim() || '（无）')
  lines.push('')
  lines.push(`【知识库片段】（共 ${response.sources.length} 条）`)
  for (const [i, s] of response.sources.entries()) {
    const body =
      s.content.length > MAX_SOURCE_CHARS
        ? `${s.content.slice(0, MAX_SOURCE_CHARS)}\n…（已截断）`
        : s.content
    lines.push(`--- 片段 ${i + 1} ---`)
    lines.push(`source_path: ${s.source_path}`)
    lines.push(`title: ${s.title}`)
    lines.push(`chunk_id: ${s.chunk_id}`)
    lines.push(`score: ${s.score}`)
    lines.push('content:')
    lines.push(body)
    lines.push('')
  }
  if (response.sources.length === 0) {
    lines.push('（本次无命中片段）')
  }
  return lines.join('\n')
}

const selectedFiles = ref<File[]>([])
const knowledgeFiles = ref<KnowledgeFileResponse[]>([])
const searchQuery = ref('')
const searchResults = ref<KnowledgeSourceItem[]>([])
const selectedResultIndex = ref(0)
const lastSearchResponse = ref<KnowledgeSearchResponse | null>(null)
const uploadMessage = ref('')
const searchMessage = ref('')
const errorMessage = ref('')
const indexStatus = ref<KnowledgeReindexResponse | null>(null)
const isUploading = ref(false)
const isSearching = ref(false)
const isRebuilding = ref(false)
const analyzeWithLlm = ref(true)
const kbSessionId = ref('')
const llmAnalysisReply = ref('')
const llmAnalysisError = ref('')
const isAnalyzing = ref(false)

const canUpload = computed(() => selectedFiles.value.length > 0 && !isUploading.value)
const canSearch = computed(
  () => Boolean(searchQuery.value.trim()) && !isSearching.value && !isAnalyzing.value,
)
const canReanalyze = computed(
  () =>
    Boolean(lastSearchResponse.value) &&
    !isSearching.value &&
    !isAnalyzing.value &&
    analyzeWithLlm.value,
)
const selectedResult = computed(() => searchResults.value[selectedResultIndex.value] || null)
const prettySearchResponse = computed(() =>
  lastSearchResponse.value ? JSON.stringify(lastSearchResponse.value, null, 2) : '',
)

async function refreshFiles() {
  const response = await fetchKnowledgeFiles()
  knowledgeFiles.value = response.files
}

async function handleFileSelection(event: Event) {
  const target = event.target as HTMLInputElement
  selectedFiles.value = Array.from(target.files || [])
}

async function handleUpload() {
  if (!canUpload.value) {
    return
  }
  errorMessage.value = ''
  uploadMessage.value = ''
  isUploading.value = true
  try {
    const response = await uploadKnowledgeFiles(selectedFiles.value)
    uploadMessage.value = `已上传 ${response.files.length} 个文件，当前索引 chunk 数：${response.indexed_chunk_count}`
    selectedFiles.value = []
    await refreshFiles()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '上传失败'
  } finally {
    isUploading.value = false
  }
}

async function runLlmAnalysis(response: KnowledgeSearchResponse) {
  llmAnalysisError.value = ''
  llmAnalysisReply.value = ''
  isAnalyzing.value = true
  try {
    if (!kbSessionId.value) {
      const session = await createSession('portal-knowledge')
      kbSessionId.value = session.session_id
    }
    const message = buildKnowledgeLlmMessage(response)
    const agent = await sendMessage({
      userId: 'portal-knowledge',
      sessionId: kbSessionId.value,
      message,
      skipTools: true,
    })
    llmAnalysisReply.value = agent.reply
  } catch (error) {
    llmAnalysisError.value = error instanceof Error ? error.message : '大模型分析失败'
  } finally {
    isAnalyzing.value = false
  }
}

async function handleSearch() {
  if (!canSearch.value) {
    return
  }
  errorMessage.value = ''
  searchMessage.value = ''
  llmAnalysisError.value = ''
  if (!analyzeWithLlm.value) {
    llmAnalysisReply.value = ''
  }
  isSearching.value = true
  try {
    const response = await searchKnowledge(searchQuery.value.trim(), 5)
    lastSearchResponse.value = response
    searchResults.value = response.sources
    selectedResultIndex.value = 0
    searchMessage.value = `命中 ${response.total_hits} 条结果，当前索引 chunk 数：${response.indexed_chunk_count}`
    if (analyzeWithLlm.value) {
      await runLlmAnalysis(response)
    }
  } catch (error) {
    lastSearchResponse.value = null
    searchResults.value = []
    llmAnalysisReply.value = ''
    errorMessage.value = error instanceof Error ? error.message : '检索失败'
  } finally {
    isSearching.value = false
  }
}

async function handleReanalyze() {
  const snapshot = lastSearchResponse.value
  if (!snapshot || !canReanalyze.value) {
    return
  }
  errorMessage.value = ''
  await runLlmAnalysis(snapshot)
}

async function handleRebuild() {
  errorMessage.value = ''
  isRebuilding.value = true
  try {
    indexStatus.value = await rebuildKnowledgeIndex()
    await refreshFiles()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '重建索引失败'
  } finally {
    isRebuilding.value = false
  }
}

async function handleDelete(fileId: string) {
  errorMessage.value = ''
  try {
    await deleteKnowledgeFile(fileId)
    await refreshFiles()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '删除文件失败'
  }
}

onMounted(() => {
  void refreshFiles()
})
</script>

<template>
  <div class="knowledge-layout">
    <section class="panel knowledge-panel">
      <div class="panel-header">
        <div>
          <h2>上传知识文件</h2>
          <p class="muted">支持 Word、PPT、PDF。优先提取文本，OCR 为 best-effort 提示模式。</p>
        </div>
      </div>

      <input
        class="text-input"
        type="file"
        accept=".docx,.pptx,.pdf"
        multiple
        @change="handleFileSelection"
      />

      <div v-if="selectedFiles.length > 0" class="file-chip-list">
        <span v-for="file in selectedFiles" :key="file.name + file.size" class="file-chip">
          {{ file.name }}
        </span>
      </div>

      <button class="primary-button" :disabled="!canUpload" @click="handleUpload">
        {{ isUploading ? '上传中...' : '上传并更新知识库' }}
      </button>

      <button class="secondary-button" :disabled="isRebuilding" @click="handleRebuild">
        {{ isRebuilding ? '重建中...' : '手动重建索引' }}
      </button>

      <p v-if="uploadMessage" class="success-text">{{ uploadMessage }}</p>
      <p v-if="indexStatus" class="muted">
        最近索引：documents={{ indexStatus.indexed_document_count }},
        files={{ indexStatus.uploaded_file_count }},
        chunks={{ indexStatus.indexed_chunk_count }}
      </p>
    </section>

    <section class="panel knowledge-panel">
      <div class="panel-header">
        <div>
          <h2>知识库检索</h2>
          <p class="muted">直接调用本地 FAISS 检索，返回来源和片段内容。</p>
        </div>
      </div>

      <textarea
        v-model="searchQuery"
        class="composer"
        rows="4"
        placeholder="例如：MyPortal 当前支持哪些能力？"
      />

      <label class="knowledge-analyze-toggle">
        <input v-model="analyzeWithLlm" type="checkbox" />
        <span>检索完成后将「提问 + 知识库片段」一并交给大模型生成回答（需配置可用模型）</span>
      </label>

      <div class="composer-actions">
        <p class="muted">检索结果会显示 source_path、score 和内容片段。</p>
        <div class="composer-actions-buttons">
          <button class="primary-button" :disabled="!canSearch" @click="handleSearch">
            {{
              isSearching
                ? analyzeWithLlm
                  ? '检索并分析中...'
                  : '检索中...'
                : '搜索知识库'
            }}
          </button>
          <button class="secondary-button" :disabled="!canReanalyze" @click="handleReanalyze">
            重新用大模型分析
          </button>
        </div>
      </div>

      <p v-if="searchMessage" class="success-text">{{ searchMessage }}</p>

      <div class="knowledge-results">
        <div class="knowledge-results-list">
          <button
            v-for="(result, index) in searchResults"
            :key="result.chunk_id"
            class="knowledge-result-card knowledge-result-button"
            :class="index === selectedResultIndex ? 'knowledge-result-active' : ''"
            @click="selectedResultIndex = index"
          >
            <div class="meta-list">
              <div>
                <span class="meta-label">Source</span>
                <code>{{ result.source_path }}</code>
              </div>
              <div>
                <span class="meta-label">Title</span>
                <code>{{ result.title }}</code>
              </div>
              <div>
                <span class="meta-label">Score</span>
                <code>{{ result.score.toFixed(4) }}</code>
              </div>
            </div>
            <pre class="message-content">{{ result.content.slice(0, 180) }}<template v-if="result.content.length > 180">...</template></pre>
          </button>
          <p v-if="searchResults.length === 0" class="empty-state">还没有检索结果。</p>
        </div>

        <div class="knowledge-result-detail">
          <div class="panel-header">
            <div>
              <h3>返回值详情</h3>
              <p class="muted">固定区域展示当前选中结果和本次接口返回值。</p>
            </div>
          </div>

          <div v-if="lastSearchResponse" class="meta-list">
            <div>
              <span class="meta-label">Query</span>
              <code>{{ lastSearchResponse.query }}</code>
            </div>
            <div>
              <span class="meta-label">Total Hits</span>
              <code>{{ lastSearchResponse.total_hits }}</code>
            </div>
            <div>
              <span class="meta-label">Indexed Chunk Count</span>
              <code>{{ lastSearchResponse.indexed_chunk_count }}</code>
            </div>
            <div>
              <span class="meta-label">Answer Scope</span>
              <code>{{ lastSearchResponse.answer_scope }}</code>
            </div>
          </div>

          <div v-if="lastSearchResponse?.answer" class="knowledge-readable-answer">
            <span class="meta-label">用户可读信息</span>
            <pre class="message-content">{{ lastSearchResponse.answer }}</pre>
          </div>

          <div v-if="isAnalyzing" class="knowledge-llm-status muted">大模型正在根据检索结果生成回答…</div>
          <div v-if="llmAnalysisError" class="knowledge-llm-error error-text">{{ llmAnalysisError }}</div>
          <div v-if="llmAnalysisReply" class="knowledge-llm-answer">
            <span class="meta-label">大模型综合分析</span>
            <pre class="message-content">{{ llmAnalysisReply }}</pre>
          </div>

          <div v-if="selectedResult" class="meta-list">
            <div>
              <span class="meta-label">Source</span>
              <code>{{ selectedResult.source_path }}</code>
            </div>
            <div>
              <span class="meta-label">Title</span>
              <code>{{ selectedResult.title }}</code>
            </div>
            <div>
              <span class="meta-label">Chunk</span>
              <code>{{ selectedResult.chunk_id }}</code>
            </div>
            <div>
              <span class="meta-label">Score</span>
              <code>{{ selectedResult.score.toFixed(4) }}</code>
            </div>
            <div>
              <span class="meta-label">Content</span>
              <pre class="message-content">{{ selectedResult.content }}</pre>
            </div>
          </div>

          <div v-if="lastSearchResponse" class="knowledge-raw-response">
            <span class="meta-label">API Response</span>
            <pre class="message-content">{{ prettySearchResponse }}</pre>
          </div>

          <p v-if="!lastSearchResponse" class="empty-state">
            还没有搜索返回值。执行一次知识库搜索后，这里会固定展示本次返回内容。
          </p>
        </div>
      </div>
    </section>

    <section class="panel knowledge-panel">
      <div class="panel-header">
        <div>
          <h2>已上传文件</h2>
          <p class="muted">文件保存在本地知识库目录中，并参与后续索引。</p>
        </div>
      </div>

      <div v-if="knowledgeFiles.length > 0" class="knowledge-file-list">
        <article v-for="item in knowledgeFiles" :key="item.file_id" class="knowledge-file-card">
          <div class="knowledge-file-header">
            <div>
              <strong>{{ item.file_name }}</strong>
              <p class="muted">{{ item.source_path }}</p>
            </div>
            <button class="secondary-button danger-button" @click="handleDelete(item.file_id)">删除</button>
          </div>

          <div class="meta-list">
            <div>
              <span class="meta-label">Status</span>
              <code>{{ item.status }}</code>
            </div>
            <div>
              <span class="meta-label">Extracted Text</span>
              <code>{{ item.extracted_text_length }}</code>
            </div>
            <div>
              <span class="meta-label">Size</span>
              <code>{{ item.size_bytes }} bytes</code>
            </div>
          </div>

          <ul v-if="item.notes.length > 0" class="note-list">
            <li v-for="note in item.notes" :key="note">{{ note }}</li>
          </ul>
        </article>
      </div>
      <p v-else class="empty-state">当前还没有上传知识文件。</p>
    </section>

    <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
  </div>
</template>
