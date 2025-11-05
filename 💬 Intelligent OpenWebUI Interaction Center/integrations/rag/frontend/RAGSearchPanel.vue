<!--
RAG Search Panel Component
RAG搜索面板组件 - 用于OpenWebUI

功能：
1. 实时搜索RAG知识库
2. 展示搜索结果
3. 插入知识到聊天
4. 查看知识详情
-->

<template>
  <div class="rag-search-panel">
    <!-- 搜索输入框 -->
    <div class="rag-search-header">
      <div class="rag-search-input-wrapper">
        <input
          v-model="searchQuery"
          @input="handleSearchInput"
          @keyup.enter="performSearch"
          type="text"
          class="rag-search-input"
          placeholder="搜索RAG知识库..."
          :disabled="isSearching"
        />
        <button
          @click="performSearch"
          class="rag-search-button"
          :disabled="isSearching || !searchQuery.trim()"
        >
          <svg v-if="!isSearching" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
          <span v-else class="rag-spinner"></span>
        </button>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="searchResults.length > 0" class="rag-search-results">
      <div class="rag-results-header">
        <span class="rag-results-count">
          找到 {{ searchResults.length }} 个相关结果
        </span>
        <button @click="clearResults" class="rag-clear-button">清除</button>
      </div>

      <div class="rag-results-list">
        <div
          v-for="(result, index) in searchResults"
          :key="result.id || index"
          class="rag-result-item"
          @click="selectResult(result)"
        >
          <div class="rag-result-header">
            <span class="rag-result-score">
              相似度: {{ (result.score * 100).toFixed(1) }}%
            </span>
            <button
              @click.stop="insertToChat(result)"
              class="rag-insert-button"
              title="插入到聊天"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M12 5v14M5 12h14"></path>
              </svg>
            </button>
          </div>
          <div class="rag-result-content">
            <div class="rag-result-snippet" v-html="highlightText(result.snippet, searchQuery)"></div>
            <div v-if="result.source" class="rag-result-source">
              来源: {{ result.source }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!isSearching && hasSearched" class="rag-empty-state">
      <p>未找到相关结果</p>
      <button @click="performSearch" class="rag-retry-button">重试</button>
    </div>

    <!-- 初始提示 -->
    <div v-else-if="!hasSearched" class="rag-initial-state">
      <p>输入关键词搜索RAG知识库</p>
      <p class="rag-hint">支持语义搜索和关键词搜索</p>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="rag-error-state">
      <p>{{ error }}</p>
      <button @click="clearError" class="rag-dismiss-button">关闭</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// Props
const props = defineProps({
  apiUrl: {
    type: String,
    default: 'http://127.0.0.1:8011'
  },
  apiKey: {
    type: String,
    default: null
  },
  maxResults: {
    type: Number,
    default: 10
  },
  similarityThreshold: {
    type: Number,
    default: 0.5
  }
})

// Emits
const emit = defineEmits(['result-selected', 'insert-to-chat'])

// 响应式数据
const searchQuery = ref('')
const searchResults = ref([])
const isSearching = ref(false)
const hasSearched = ref(false)
const error = ref(null)
const debounceTimer = ref(null)

// 执行搜索
const performSearch = async () => {
  if (!searchQuery.value.trim()) {
    return
  }

  isSearching.value = true
  error.value = null
  hasSearched.value = true

  try {
    const response = await fetch(`${props.apiUrl}/rag/search`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
      },
      params: new URLSearchParams({
        query: searchQuery.value,
        top_k: props.maxResults.toString(),
        threshold: props.similarityThreshold.toString()
      })
    })

    if (!response.ok) {
      throw new Error(`搜索失败: ${response.statusText}`)
    }

    const data = await response.json()
    searchResults.value = data.items || []
  } catch (err) {
    error.value = err.message || '搜索失败，请稍后重试'
    console.error('RAG搜索错误:', err)
  } finally {
    isSearching.value = false
  }
}

// 处理搜索输入（防抖）
const handleSearchInput = () => {
  if (debounceTimer.value) {
    clearTimeout(debounceTimer.value)
  }
  debounceTimer.value = setTimeout(() => {
    if (searchQuery.value.trim().length >= 2) {
      performSearch()
    }
  }, 300)
}

// 选择结果
const selectResult = (result) => {
  emit('result-selected', result)
}

// 插入到聊天
const insertToChat = (result) => {
  emit('insert-to-chat', {
    text: result.snippet,
    source: result.source,
    score: result.score
  })
}

// 高亮文本
const highlightText = (text, query) => {
  if (!text || !query) return text
  const regex = new RegExp(`(${query})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}

// 清除结果
const clearResults = () => {
  searchResults.value = []
  hasSearched.value = false
  searchQuery.value = ''
}

// 清除错误
const clearError = () => {
  error.value = null
}
</script>

<style scoped>
.rag-search-panel {
  padding: 16px;
  background: var(--bg-secondary, #f5f5f5);
  border-radius: 8px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.rag-search-header {
  margin-bottom: 16px;
}

.rag-search-input-wrapper {
  display: flex;
  gap: 8px;
}

.rag-search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 6px;
  font-size: 14px;
}

.rag-search-input:focus {
  outline: none;
  border-color: var(--primary-color, #3b82f6);
}

.rag-search-button {
  padding: 8px 16px;
  background: var(--primary-color, #3b82f6);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.rag-search-button:hover:not(:disabled) {
  opacity: 0.9;
}

.rag-search-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.rag-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.rag-search-results {
  flex: 1;
  overflow-y: auto;
}

.rag-results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 12px;
  color: var(--text-secondary, #666);
}

.rag-clear-button {
  background: none;
  border: none;
  color: var(--text-secondary, #666);
  cursor: pointer;
  font-size: 12px;
  padding: 4px 8px;
}

.rag-clear-button:hover {
  color: var(--text-primary, #333);
}

.rag-results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rag-result-item {
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid var(--border-color, #e5e5e5);
  cursor: pointer;
  transition: all 0.2s;
}

.rag-result-item:hover {
  border-color: var(--primary-color, #3b82f6);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.rag-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.rag-result-score {
  font-size: 12px;
  color: var(--text-secondary, #666);
}

.rag-insert-button {
  background: var(--primary-color, #3b82f6);
  color: white;
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.rag-insert-button:hover {
  opacity: 0.9;
}

.rag-result-content {
  font-size: 14px;
  line-height: 1.5;
}

.rag-result-snippet {
  color: var(--text-primary, #333);
  margin-bottom: 8px;
}

.rag-result-snippet mark {
  background: yellow;
  padding: 0 2px;
}

.rag-result-source {
  font-size: 12px;
  color: var(--text-secondary, #666);
  margin-top: 4px;
}

.rag-empty-state,
.rag-initial-state,
.rag-error-state {
  padding: 32px;
  text-align: center;
  color: var(--text-secondary, #666);
}

.rag-hint {
  font-size: 12px;
  margin-top: 8px;
}

.rag-retry-button,
.rag-dismiss-button {
  margin-top: 16px;
  padding: 8px 16px;
  background: var(--primary-color, #3b82f6);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.rag-retry-button:hover,
.rag-dismiss-button:hover {
  opacity: 0.9;
}

.rag-error-state {
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 6px;
  color: #c33;
}
</style>

