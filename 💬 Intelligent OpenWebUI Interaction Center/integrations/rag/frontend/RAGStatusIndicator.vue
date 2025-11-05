<!--
RAG Status Indicator Component
RAG系统状态指示器 - 用于OpenWebUI状态栏

功能：
1. 显示索引状态
2. 显示文档数量
3. 系统健康检查
4. 实时状态更新
-->

<template>
  <div class="rag-status-indicator">
    <!-- 状态图标 -->
    <div 
      class="rag-status-icon"
      :class="statusClass"
      @click="showDetails = !showDetails"
      :title="statusText"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <circle v-if="status === 'ok'" cx="12" cy="12" r="10"></circle>
        <path v-else-if="status === 'warning'" d="M12 2L2 7v10l10 5 10-5V7L12 2z"></path>
        <path v-else d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
      </svg>
    </div>

    <!-- 详情面板 -->
    <div v-if="showDetails" class="rag-status-details">
      <div class="rag-status-details-header">
        <h4>RAG系统状态</h4>
        <button @click="showDetails = false" class="rag-status-close">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="rag-status-details-content">
        <!-- 索引状态 -->
        <div class="rag-status-section">
          <div class="rag-status-section-title">索引状态</div>
          <div class="rag-status-item">
            <span class="rag-status-label">文档数量:</span>
            <span class="rag-status-value">{{ indexInfo.index_docs || 0 }}</span>
          </div>
          <div class="rag-status-item">
            <span class="rag-status-label">索引维度:</span>
            <span class="rag-status-value">{{ indexInfo.dimension || 'N/A' }}</span>
          </div>
          <div class="rag-status-item">
            <span class="rag-status-label">模型状态:</span>
            <span class="rag-status-value" :class="indexInfo.model_ok ? 'rag-status-ok' : 'rag-status-error'">
              {{ indexInfo.model_ok ? '正常' : '异常' }}
            </span>
          </div>
          <div class="rag-status-item">
            <span class="rag-status-label">索引状态:</span>
            <span class="rag-status-value" :class="indexInfo.index_matrix_ok ? 'rag-status-ok' : 'rag-status-error'">
              {{ indexInfo.index_matrix_ok ? '正常' : '异常' }}
            </span>
          </div>
        </div>

        <!-- 知识图谱状态 -->
        <div class="rag-status-section">
          <div class="rag-status-section-title">知识图谱</div>
          <div class="rag-status-item">
            <span class="rag-status-label">节点数:</span>
            <span class="rag-status-value">{{ kgStats.nodes || 0 }}</span>
          </div>
          <div class="rag-status-item">
            <span class="rag-status-label">边数:</span>
            <span class="rag-status-value">{{ kgStats.edges || 0 }}</span>
          </div>
        </div>

        <!-- 系统信息 -->
        <div class="rag-status-section">
          <div class="rag-status-section-title">系统信息</div>
          <div class="rag-status-item">
            <span class="rag-status-label">API地址:</span>
            <span class="rag-status-value">{{ apiUrl }}</span>
          </div>
          <div class="rag-status-item">
            <span class="rag-status-label">最后更新:</span>
            <span class="rag-status-value">{{ lastUpdate }}</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="rag-status-actions">
          <button @click="refreshStatus" class="rag-status-button" :disabled="isRefreshing">
            <svg v-if="!isRefreshing" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <polyline points="23 4 23 10 17 10"></polyline>
              <polyline points="1 20 1 14 7 14"></polyline>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
            <span v-else class="rag-spinner-small"></span>
            {{ isRefreshing ? '刷新中...' : '刷新' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

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
  updateInterval: {
    type: Number,
    default: 30000  // 30秒
  }
})

// 响应式数据
const showDetails = ref(false)
const indexInfo = ref({})
const kgStats = ref({})
const lastUpdate = ref('')
const isRefreshing = ref(false)
const status = ref('ok')  // ok, warning, error

let updateTimer = null

// 计算状态
const statusClass = computed(() => {
  return {
    'rag-status-ok': status.value === 'ok',
    'rag-status-warning': status.value === 'warning',
    'rag-status-error': status.value === 'error'
  }
})

const statusText = computed(() => {
  const texts = {
    'ok': 'RAG系统正常',
    'warning': 'RAG系统警告',
    'error': 'RAG系统错误'
  }
  return texts[status.value] || '未知状态'
})

// 获取状态信息
const fetchStatus = async () => {
  try {
    // 获取索引信息
    const indexResponse = await fetch(`${props.apiUrl}/index/info`, {
      headers: {
        ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
      }
    })

    if (indexResponse.ok) {
      indexInfo.value = await indexResponse.json()
    }

    // 获取知识图谱统计
    const kgResponse = await fetch(
      `${props.apiUrl}/kg/query?query_type=statistics`,
      {
        headers: {
          ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
        }
      }
    )

    if (kgResponse.ok) {
      const kgResult = await kgResponse.json()
      if (kgResult.statistics) {
        kgStats.value = {
          nodes: kgResult.statistics.total_nodes || 0,
          edges: kgResult.statistics.total_edges || 0
        }
      }
    }

    // 更新状态
    updateStatus()

    // 更新最后更新时间
    lastUpdate.value = new Date().toLocaleTimeString('zh-CN')

  } catch (error) {
    console.error('获取RAG状态错误:', error)
    status.value = 'error'
  }
}

// 更新状态
const updateStatus = () => {
  const modelOk = indexInfo.value.model_ok
  const indexOk = indexInfo.value.index_matrix_ok
  const hasDocs = (indexInfo.value.index_docs || 0) > 0

  if (modelOk && indexOk && hasDocs) {
    status.value = 'ok'
  } else if (hasDocs && (modelOk || indexOk)) {
    status.value = 'warning'
  } else {
    status.value = 'error'
  }
}

// 刷新状态
const refreshStatus = async () => {
  isRefreshing.value = true
  await fetchStatus()
  isRefreshing.value = false
}

// 启动定时更新
const startAutoUpdate = () => {
  if (updateTimer) {
    clearInterval(updateTimer)
  }
  updateTimer = setInterval(fetchStatus, props.updateInterval)
}

// 停止定时更新
const stopAutoUpdate = () => {
  if (updateTimer) {
    clearInterval(updateTimer)
    updateTimer = null
  }
}

// 初始化
onMounted(async () => {
  await fetchStatus()
  startAutoUpdate()
})

onUnmounted(() => {
  stopAutoUpdate()
})
</script>

<style scoped>
.rag-status-indicator {
  position: relative;
}

.rag-status-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.rag-status-icon:hover {
  background: var(--bg-hover, rgba(0, 0, 0, 0.05));
}

.rag-status-ok {
  color: var(--success-color, #10b981);
}

.rag-status-warning {
  color: var(--warning-color, #f59e0b);
}

.rag-status-error {
  color: var(--error-color, #ef4444);
}

.rag-status-details {
  position: absolute;
  bottom: 100%;
  right: 0;
  margin-bottom: 8px;
  width: 320px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.rag-status-details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid var(--border-color, #e5e5e5);
}

.rag-status-details-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.rag-status-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: var(--text-secondary, #666);
}

.rag-status-details-content {
  padding: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.rag-status-section {
  margin-bottom: 16px;
}

.rag-status-section:last-child {
  margin-bottom: 0;
}

.rag-status-section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary, #666);
  margin-bottom: 8px;
  text-transform: uppercase;
}

.rag-status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  font-size: 13px;
}

.rag-status-label {
  color: var(--text-secondary, #666);
}

.rag-status-value {
  color: var(--text-primary, #333);
  font-weight: 500;
}

.rag-status-value.rag-status-ok {
  color: var(--success-color, #10b981);
}

.rag-status-value.rag-status-error {
  color: var(--error-color, #ef4444);
}

.rag-status-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color, #e5e5e5);
}

.rag-status-button {
  width: 100%;
  padding: 8px;
  background: var(--primary-color, #3b82f6);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.rag-status-button:hover:not(:disabled) {
  opacity: 0.9;
}

.rag-status-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.rag-spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

