<!--
RAG File Manager Component
RAG文件管理器组件 - 用于OpenWebUI设置页面

功能：
1. 上传文件到RAG库
2. 管理已上传的文件
3. 查看文件状态
4. 删除文件
-->

<template>
  <div class="rag-file-manager">
    <div class="rag-file-manager-header">
      <h2>RAG知识库文件管理</h2>
      <div class="rag-stats">
        <span>总文档数: {{ totalDocuments }}</span>
        <span>索引大小: {{ indexSize }}</span>
      </div>
    </div>

    <!-- 文件上传区域 -->
    <div class="rag-upload-section">
      <div class="rag-upload-area" 
           @drop="handleDrop" 
           @dragover.prevent 
           @dragenter.prevent>
        <input
          ref="fileInput"
          type="file"
          multiple
          @change="handleFileSelect"
          style="display: none"
        />
        <div class="rag-upload-content">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
          <p>拖拽文件到这里或点击上传</p>
          <p class="rag-upload-hint">支持多种文件格式 (PDF, Word, Excel, 图片等)</p>
          <button @click="triggerFileInput" class="rag-upload-button">
            选择文件
          </button>
        </div>
      </div>

      <!-- 上传进度 -->
      <div v-if="uploadingFiles.length > 0" class="rag-upload-progress">
        <div v-for="file in uploadingFiles" :key="file.id" class="rag-upload-item">
          <div class="rag-upload-info">
            <span class="rag-upload-filename">{{ file.name }}</span>
            <span class="rag-upload-status">{{ file.status }}</span>
          </div>
          <div class="rag-progress-bar">
            <div class="rag-progress-fill" :style="{ width: file.progress + '%' }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 文件列表 -->
    <div class="rag-files-section">
      <div class="rag-files-header">
        <h3>已上传文件</h3>
        <div class="rag-files-actions">
          <button @click="refreshFiles" class="rag-refresh-button" :disabled="isLoading">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <polyline points="23 4 23 10 17 10"></polyline>
              <polyline points="1 20 1 14 7 14"></polyline>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
            刷新
          </button>
          <button @click="clearAllFiles" class="rag-clear-all-button" :disabled="isLoading">
            清空
          </button>
        </div>
      </div>

      <div v-if="isLoading" class="rag-loading">
        <div class="rag-spinner"></div>
        <p>加载中...</p>
      </div>

      <div v-else-if="files.length === 0" class="rag-empty">
        <p>暂无文件</p>
        <p class="rag-empty-hint">上传文件以构建知识库</p>
      </div>

      <div v-else class="rag-files-list">
        <div v-for="file in files" :key="file.id" class="rag-file-item">
          <div class="rag-file-info">
            <div class="rag-file-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
                <polyline points="13 2 13 9 20 9"></polyline>
              </svg>
            </div>
            <div class="rag-file-details">
              <div class="rag-file-name">{{ file.name }}</div>
              <div class="rag-file-meta">
                <span>大小: {{ formatFileSize(file.size) }}</span>
                <span>上传时间: {{ formatDate(file.uploaded_at) }}</span>
                <span v-if="file.status" class="rag-file-status" :class="file.status">
                  {{ file.status }}
                </span>
              </div>
            </div>
          </div>
          <div class="rag-file-actions">
            <button @click="viewFile(file)" class="rag-view-button" title="查看">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
            </button>
            <button @click="deleteFile(file)" class="rag-delete-button" title="删除">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

// Props
const props = defineProps({
  apiUrl: {
    type: String,
    default: 'http://127.0.0.1:8011'
  },
  apiKey: {
    type: String,
    default: null
  }
})

// 响应式数据
const fileInput = ref(null)
const files = ref([])
const uploadingFiles = ref([])
const isLoading = ref(false)
const totalDocuments = ref(0)
const indexSize = ref('0 KB')

// 触发文件选择
const triggerFileInput = () => {
  fileInput.value?.click()
}

// 处理文件选择
const handleFileSelect = (event) => {
  const selectedFiles = Array.from(event.target.files || [])
  uploadFiles(selectedFiles)
}

// 处理拖拽
const handleDrop = (event) => {
  const droppedFiles = Array.from(event.dataTransfer.files || [])
  uploadFiles(droppedFiles)
}

// 上传文件
const uploadFiles = async (fileList) => {
  for (const file of fileList) {
    const uploadId = Date.now() + Math.random()
    const uploadFile = {
      id: uploadId,
      name: file.name,
      size: file.size,
      progress: 0,
      status: '上传中...'
    }
    uploadingFiles.value.push(uploadFile)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const headers = {
        ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
      }

      const response = await fetch(`${props.apiUrl}/rag/ingest_file`, {
        method: 'POST',
        headers,
        body: formData,
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          uploadFile.progress = percentCompleted
        }
      })

      if (!response.ok) {
        throw new Error(`上传失败: ${response.statusText}`)
      }

      const result = await response.json()
      uploadFile.status = '完成'
      uploadFile.progress = 100

      // 添加到文件列表
      files.value.push({
        id: result.doc_id || uploadId,
        name: file.name,
        size: file.size,
        uploaded_at: new Date().toISOString(),
        status: '已索引'
      })

      // 延迟移除上传项
      setTimeout(() => {
        const index = uploadingFiles.value.findIndex(f => f.id === uploadId)
        if (index > -1) {
          uploadingFiles.value.splice(index, 1)
        }
      }, 2000)

      // 刷新统计
      await refreshStats()

    } catch (error) {
      uploadFile.status = '失败'
      console.error('文件上传错误:', error)
    }
  }
}

// 刷新文件列表
const refreshFiles = async () => {
  isLoading.value = true
  try {
    const response = await fetch(`${props.apiUrl}/index/info`, {
      headers: {
        ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
      }
    })

    if (response.ok) {
      const data = await response.json()
      // 这里需要根据实际API响应调整
      // files.value = data.files || []
    }
  } catch (error) {
    console.error('刷新文件列表错误:', error)
  } finally {
    isLoading.value = false
  }
}

// 刷新统计信息
const refreshStats = async () => {
  try {
    const response = await fetch(`${props.apiUrl}/index/info`, {
      headers: {
        ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
      }
    })

    if (response.ok) {
      const data = await response.json()
      totalDocuments.value = data.index_docs || 0
      // indexSize需要从API获取或计算
    }
  } catch (error) {
    console.error('刷新统计错误:', error)
  }
}

// 删除文件
const deleteFile = async (file) => {
  if (!confirm(`确定要删除 "${file.name}" 吗？`)) {
    return
  }

  try {
    const response = await fetch(`${props.apiUrl}/rag/delete/${file.id}`, {
      method: 'DELETE',
      headers: {
        ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
      }
    })

    if (response.ok) {
      const index = files.value.findIndex(f => f.id === file.id)
      if (index > -1) {
        files.value.splice(index, 1)
      }
      await refreshStats()
    }
  } catch (error) {
    console.error('删除文件错误:', error)
    alert('删除失败: ' + error.message)
  }
}

// 查看文件
const viewFile = (file) => {
  // 打开文件详情或预览
  console.log('查看文件:', file)
}

// 清空所有文件
const clearAllFiles = async () => {
  if (!confirm('确定要清空所有文件吗？此操作不可恢复！')) {
    return
  }

  try {
    const response = await fetch(`${props.apiUrl}/index/clear`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
      }
    })

    if (response.ok) {
      files.value = []
      await refreshStats()
    }
  } catch (error) {
    console.error('清空文件错误:', error)
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 初始化
onMounted(async () => {
  await refreshFiles()
  await refreshStats()
})
</script>

<style scoped>
.rag-file-manager {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.rag-file-manager-header {
  margin-bottom: 24px;
}

.rag-file-manager-header h2 {
  margin: 0 0 12px 0;
  font-size: 24px;
  font-weight: 600;
}

.rag-stats {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: var(--text-secondary, #666);
}

.rag-upload-section {
  margin-bottom: 32px;
}

.rag-upload-area {
  border: 2px dashed var(--border-color, #ddd);
  border-radius: 8px;
  padding: 48px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.rag-upload-area:hover {
  border-color: var(--primary-color, #3b82f6);
  background: rgba(59, 130, 246, 0.05);
}

.rag-upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.rag-upload-content svg {
  color: var(--text-secondary, #999);
}

.rag-upload-hint {
  font-size: 12px;
  color: var(--text-secondary, #999);
}

.rag-upload-button {
  padding: 10px 20px;
  background: var(--primary-color, #3b82f6);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.rag-upload-button:hover {
  opacity: 0.9;
}

.rag-upload-progress {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rag-upload-item {
  padding: 12px;
  background: var(--bg-secondary, #f5f5f5);
  border-radius: 6px;
}

.rag-upload-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.rag-upload-filename {
  font-weight: 500;
}

.rag-upload-status {
  color: var(--text-secondary, #666);
  font-size: 12px;
}

.rag-progress-bar {
  height: 4px;
  background: var(--border-color, #e5e5e5);
  border-radius: 2px;
  overflow: hidden;
}

.rag-progress-fill {
  height: 100%;
  background: var(--primary-color, #3b82f6);
  transition: width 0.3s;
}

.rag-files-section {
  background: white;
  border-radius: 8px;
  padding: 24px;
  border: 1px solid var(--border-color, #e5e5e5);
}

.rag-files-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.rag-files-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.rag-files-actions {
  display: flex;
  gap: 8px;
}

.rag-refresh-button,
.rag-clear-all-button {
  padding: 8px 16px;
  background: var(--bg-secondary, #f5f5f5);
  border: 1px solid var(--border-color, #ddd);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.rag-refresh-button:hover:not(:disabled),
.rag-clear-all-button:hover:not(:disabled) {
  background: var(--bg-tertiary, #e5e5e5);
}

.rag-refresh-button:disabled,
.rag-clear-all-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.rag-loading,
.rag-empty {
  padding: 48px;
  text-align: center;
  color: var(--text-secondary, #666);
}

.rag-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(59, 130, 246, 0.2);
  border-top-color: var(--primary-color, #3b82f6);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin: 0 auto 16px;
}

.rag-empty-hint {
  font-size: 12px;
  margin-top: 8px;
}

.rag-files-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rag-file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--bg-secondary, #f5f5f5);
  border-radius: 6px;
  border: 1px solid var(--border-color, #e5e5e5);
  transition: all 0.2s;
}

.rag-file-item:hover {
  border-color: var(--primary-color, #3b82f6);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.rag-file-info {
  display: flex;
  gap: 12px;
  flex: 1;
}

.rag-file-icon {
  color: var(--text-secondary, #999);
}

.rag-file-details {
  flex: 1;
}

.rag-file-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.rag-file-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary, #666);
}

.rag-file-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.rag-file-status.已索引 {
  background: #d4edda;
  color: #155724;
}

.rag-file-actions {
  display: flex;
  gap: 8px;
}

.rag-view-button,
.rag-delete-button {
  padding: 6px;
  background: none;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary, #666);
}

.rag-view-button:hover {
  border-color: var(--primary-color, #3b82f6);
  color: var(--primary-color, #3b82f6);
}

.rag-delete-button:hover {
  border-color: #dc3545;
  color: #dc3545;
}
</style>

