<template>
  <div class="process-exceptions">
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="异常状态">
          <el-select v-model="filters.status" clearable @change="loadData">
            <el-option label="全部" value="" />
            <el-option label="未处理" value="open" />
            <el-option label="处理中" value="investigating" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="异常级别">
          <el-select v-model="filters.level" clearable @change="loadData">
            <el-option label="全部" value="" />
            <el-option label="信息" value="info" />
            <el-option label="警告" value="warning" />
            <el-option label="错误" value="error" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" :icon="Refresh" @click="loadData">
            刷新
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="6">
        <el-card class="stat-card total">
          <div class="stat-content">
            <div class="stat-label">异常总数</div>
            <div class="stat-value">{{ statistics.total }}</div>
            <div class="stat-icon">⚠️</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card open">
          <div class="stat-content">
            <div class="stat-label">未处理</div>
            <div class="stat-value">{{ statistics.open }}</div>
            <div class="stat-icon">🔴</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card investigating">
          <div class="stat-content">
            <div class="stat-label">处理中</div>
            <div class="stat-value">{{ statistics.investigating }}</div>
            <div class="stat-icon">🟡</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card resolved">
          <div class="stat-content">
            <div class="stat-label">已解决</div>
            <div class="stat-value">{{ statistics.resolved }}</div>
            <div class="stat-icon">🟢</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 异常列表 -->
    <el-row class="mt-20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>异常监控列表</span>
              <el-button type="primary" size="small" :icon="Plus">
                记录异常
              </el-button>
            </div>
          </template>
          
          <div class="exception-items" v-loading="loading">
            <div 
              v-for="exception in exceptions"
              :key="exception.id"
              class="exception-item"
              :class="'level-' + exception.exception_level"
            >
              <div class="exception-header">
                <div class="exception-info">
                  <el-tag :type="getLevelType(exception.exception_level)" size="large">
                    {{ getLevelIcon(exception.exception_level) }} {{ getLevelText(exception.exception_level) }}
                  </el-tag>
                  <span class="exception-type">{{ exception.exception_type }}</span>
                </div>
                <el-tag :type="getStatusType(exception.status)">
                  {{ getStatusText(exception.status) }}
                </el-tag>
              </div>
              
              <div class="exception-body">
                <div class="exception-description">
                  {{ exception.description }}
                </div>
                
                <div class="exception-meta">
                  <span class="meta-item">
                    <el-icon><Clock /></el-icon>
                    检测时间：{{ formatDateTime(exception.detected_at) }}
                  </span>
                  <span class="meta-item" v-if="exception.resolved_at">
                    <el-icon><CircleCheck /></el-icon>
                    解决时间：{{ formatDateTime(exception.resolved_at) }}
                  </span>
                  <span class="meta-item" v-if="exception.resolver">
                    <el-icon><User /></el-icon>
                    处理人：{{ exception.resolver }}
                  </span>
                </div>
                
                <div v-if="exception.resolution" class="exception-resolution">
                  <strong>解决方案：</strong>{{ exception.resolution }}
                </div>
              </div>
              
              <div class="exception-actions">
                <el-button size="small" type="primary" v-if="exception.status === 'open'">
                  开始处理
                </el-button>
                <el-button size="small" type="success" v-if="exception.status === 'investigating'">
                  标记已解决
                </el-button>
                <el-button size="small" :icon="Link">创建改进计划</el-button>
                <el-button size="small" :icon="View">查看详情</el-button>
              </div>
            </div>
            
            <el-empty v-if="!exceptions.length" description="暂无异常记录" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 改进计划 -->
    <el-row class="mt-20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>改进计划（闭环管理）</span>
            </div>
          </template>
          
          <el-table :data="improvements" stripe v-loading="loadingImprovements">
            <el-table-column prop="title" label="改进计划" width="200" />
            <el-table-column prop="description" label="描述" />
            <el-table-column label="优先级" width="100">
              <template #default="scope">
                <el-tag :type="getPriorityType(scope.row.priority)">
                  {{ getPriorityText(scope.row.priority) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="进度" width="200">
              <template #default="scope">
                <el-progress :percentage="scope.row.progress || 0" />
              </template>
            </el-table-column>
            <el-table-column prop="responsible" label="负责人" width="120" />
            <el-table-column label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Refresh, Plus, View, Link, Clock, CircleCheck, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from '@/api/axios'

const filters = reactive({
  status: '',
  level: ''
})

const exceptions = ref([])
const improvements = ref([])
const loading = ref(false)
const loadingImprovements = ref(false)

const statistics = reactive({
  total: 0,
  open: 0,
  investigating: 0,
  resolved: 0
})

const levelLabels = {
  info: '信息',
  warning: '警告',
  error: '错误',
  critical: '严重'
}

const levelTypes = {
  info: 'info',
  warning: 'warning',
  error: 'danger',
  critical: 'danger'
}

const levelIcons = {
  info: 'ℹ️',
  warning: '⚠️',
  error: '❌',
  critical: '🔥'
}

const statusLabels = {
  open: '未处理',
  investigating: '处理中',
  resolved: '已解决',
  closed: '已关闭',
  planned: '计划中',
  in_progress: '进行中',
  completed: '已完成'
}

const statusTypes = {
  open: 'danger',
  investigating: 'warning',
  resolved: 'success',
  closed: 'info',
  planned: 'info',
  in_progress: 'warning',
  completed: 'success'
}

const priorityLabels = {
  low: '低',
  medium: '中',
  high: '高',
  urgent: '紧急'
}

const priorityTypes = {
  low: 'info',
  medium: '',
  high: 'warning',
  urgent: 'danger'
}

const getLevelText = (level) => levelLabels[level] || level
const getLevelType = (level) => levelTypes[level] || ''
const getLevelIcon = (level) => levelIcons[level] || ''

const getStatusText = (status) => statusLabels[status] || status
const getStatusType = (status) => statusTypes[status] || ''

const getPriorityText = (priority) => priorityLabels[priority] || priority
const getPriorityType = (priority) => priorityTypes[priority] || ''

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.status) params.status = filters.status
    if (filters.level) params.level = filters.level
    
    const response = await axios.get('/process/exceptions', { params })
    exceptions.value = response.exceptions || []
    
    // 计算统计
    statistics.total = exceptions.value.length
    statistics.open = exceptions.value.filter(e => e.status === 'open').length
    statistics.investigating = exceptions.value.filter(e => e.status === 'investigating').length
    statistics.resolved = exceptions.value.filter(e => e.status === 'resolved').length
    
    ElMessage.success('异常数据加载成功')
  } catch (error) {
    console.error('加载异常列表失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const loadImprovements = async () => {
  loadingImprovements.value = true
  try {
    const response = await axios.get('/process/improvements')
    improvements.value = response.improvements || []
  } catch (error) {
    console.error('加载改进计划失败:', error)
  } finally {
    loadingImprovements.value = false
  }
}

onMounted(() => {
  loadData()
  loadImprovements()
})
</script>

<style scoped>
.process-exceptions {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.mt-20 {
  margin-top: 20px;
}

.stat-card {
  height: 120px;
}

.stat-content {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}

.stat-icon {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 48px;
  opacity: 0.3;
}

.stat-card.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-card.open {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-card.investigating {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
}

.stat-card.resolved {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.stat-card.total .stat-label,
.stat-card.open .stat-label,
.stat-card.investigating .stat-label,
.stat-card.resolved .stat-label,
.stat-card.total .stat-value,
.stat-card.open .stat-value,
.stat-card.investigating .stat-value,
.stat-card.resolved .stat-value {
  color: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.exception-items {
  min-height: 300px;
}

.exception-item {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  background: white;
  transition: all 0.3s;
}

.exception-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.exception-item.level-warning {
  border-left: 4px solid #E6A23C;
}

.exception-item.level-error {
  border-left: 4px solid #F56C6C;
}

.exception-item.level-critical {
  border-left: 4px solid #F56C6C;
  background: #fef0f0;
}

.exception-item.level-info {
  border-left: 4px solid #409EFF;
}

.exception-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.exception-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.exception-type {
  font-size: 14px;
  color: #606266;
  background: #f5f7fa;
  padding: 4px 12px;
  border-radius: 4px;
}

.exception-body {
  margin-bottom: 16px;
}

.exception-description {
  font-size: 15px;
  color: #303133;
  line-height: 1.6;
  margin-bottom: 12px;
}

.exception-meta {
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.exception-resolution {
  padding: 12px;
  background: #f0f9ff;
  border-left: 3px solid #67C23A;
  font-size: 14px;
  color: #606266;
  margin-top: 12px;
}

.exception-resolution strong {
  color: #303133;
}

.exception-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}
</style>
