<template>
  <div class="process-list">
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="流程状态">
          <el-select v-model="filters.status" clearable @change="loadData">
            <el-option label="全部" value="" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="待处理" value="pending" />
            <el-option label="已暂停" value="suspended" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" :icon="Refresh" @click="loadData">
            刷新
          </el-button>
          <el-button type="success" :icon="Plus" @click="showCreateDialog">
            新建流程
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="6">
        <el-card class="stat-card total">
          <div class="stat-content">
            <div class="stat-label">流程总数</div>
            <div class="stat-value">{{ statistics.total }}</div>
            <div class="stat-icon">📋</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card in-progress">
          <div class="stat-content">
            <div class="stat-label">进行中</div>
            <div class="stat-value">{{ statistics.in_progress }}</div>
            <div class="stat-icon">🔄</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card completed">
          <div class="stat-content">
            <div class="stat-label">已完成</div>
            <div class="stat-value">{{ statistics.completed }}</div>
            <div class="stat-icon">✅</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card exceptions">
          <div class="stat-content">
            <div class="stat-label">异常数</div>
            <div class="stat-value">{{ statistics.exceptions }}</div>
            <div class="stat-icon">⚠️</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 流程列表 -->
    <el-row class="mt-20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>流程实例列表</span>
            </div>
          </template>
          
          <div class="process-items" v-loading="loading">
            <div 
              v-for="instance in processInstances" 
              :key="instance.id"
              class="process-item"
              @click="viewDetail(instance)"
            >
              <div class="process-header">
                <div class="process-info">
                  <h3>{{ instance.instance_name }}</h3>
                  <el-tag :type="getStatusType(instance.status)" size="small">
                    {{ getStatusText(instance.status) }}
                  </el-tag>
                </div>
                <div class="process-actions">
                  <el-button size="small" :icon="View" @click.stop="viewDetail(instance)">
                    查看详情
                  </el-button>
                </div>
              </div>
              
              <div class="process-body">
                <div class="process-stage">
                  <span class="label">当前阶段：</span>
                  <span class="value">{{ instance.current_stage }}</span>
                </div>
                
                <div class="process-progress">
                  <div class="progress-info">
                    <span>进度：{{ instance.progress_percentage || 0 }}%</span>
                  </div>
                  <el-progress 
                    :percentage="instance.progress_percentage || 0" 
                    :color="getProgressColor(instance.progress_percentage)"
                    :stroke-width="10"
                  />
                </div>
                
                <div class="process-meta">
                  <span class="meta-item">
                    <el-icon><Calendar /></el-icon>
                    开始时间：{{ formatDate(instance.started_at) }}
                  </span>
                  <span class="meta-item" v-if="instance.completed_at">
                    <el-icon><CircleCheck /></el-icon>
                    完成时间：{{ formatDate(instance.completed_at) }}
                  </span>
                  <span class="meta-item" v-else>
                    <el-icon><Clock /></el-icon>
                    运行时长：{{ calculateDuration(instance.started_at) }}天
                  </span>
                </div>
              </div>
            </div>
            
            <el-empty v-if="!processInstances.length" description="暂无流程数据" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Plus, View, Calendar, Clock, CircleCheck } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from '@/api/axios'

const router = useRouter()

const filters = reactive({
  status: ''
})

const processInstances = ref([])
const loading = ref(false)

const statistics = reactive({
  total: 0,
  in_progress: 0,
  completed: 0,
  exceptions: 0
})

const statusLabels = {
  pending: '待处理',
  in_progress: '进行中',
  completed: '已完成',
  suspended: '已暂停',
  cancelled: '已取消'
}

const statusTypes = {
  pending: 'info',
  in_progress: 'warning',
  completed: 'success',
  suspended: 'info',
  cancelled: 'danger'
}

const getStatusText = (status) => {
  return statusLabels[status] || status
}

const getStatusType = (status) => {
  return statusTypes[status] || ''
}

const getProgressColor = (percentage) => {
  if (percentage < 30) return '#F56C6C'
  if (percentage < 70) return '#E6A23C'
  return '#67C23A'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const calculateDuration = (startDate) => {
  if (!startDate) return 0
  const start = new Date(startDate)
  const now = new Date()
  const days = Math.floor((now - start) / (1000 * 60 * 60 * 24))
  return days
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.status) {
      params.status = filters.status
    }
    
    const response = await axios.get('/process/instances', { params })
    processInstances.value = response.instances || []
    
    // 计算统计数据
    statistics.total = processInstances.value.length
    statistics.in_progress = processInstances.value.filter(p => p.status === 'in_progress').length
    statistics.completed = processInstances.value.filter(p => p.status === 'completed').length
    
    // 获取异常数量
    const exceptionsResp = await axios.get('/process/exceptions')
    statistics.exceptions = exceptionsResp.exceptions?.length || 0
    
    ElMessage.success('数据加载成功')
  } catch (error) {
    console.error('加载流程列表失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const viewDetail = (instance) => {
  router.push(`/process/tracking?id=${instance.id}`)
}

const showCreateDialog = () => {
  ElMessage.info('新建流程功能开发中')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.process-list {
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
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
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

.stat-card.in-progress {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-card.completed {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.stat-card.exceptions {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
}

.stat-card.total .stat-label,
.stat-card.in-progress .stat-label,
.stat-card.completed .stat-label,
.stat-card.exceptions .stat-label,
.stat-card.total .stat-value,
.stat-card.in-progress .stat-value,
.stat-card.completed .stat-value,
.stat-card.exceptions .stat-value {
  color: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.process-items {
  min-height: 300px;
}

.process-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.process-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border-color: #409EFF;
}

.process-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.process-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.process-info h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.process-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.process-stage {
  font-size: 14px;
}

.process-stage .label {
  color: #909399;
  margin-right: 8px;
}

.process-stage .value {
  color: #303133;
  font-weight: 500;
}

.process-progress {
  margin-top: 8px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.process-meta {
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: #909399;
  margin-top: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
