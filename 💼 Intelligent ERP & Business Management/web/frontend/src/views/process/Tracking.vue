<template>
  <div class="process-tracking">
    <el-card v-if="processDetail">
      <template #header>
        <div class="card-header">
          <div>
            <h3>{{ processDetail.instance_name }}</h3>
            <el-tag :type="getStatusType(processDetail.status)" class="ml-10">
              {{ getStatusText(processDetail.status) }}
            </el-tag>
          </div>
          <el-button :icon="Back" @click="goBack">返回</el-button>
        </div>
      </template>

      <!-- 进度概览 -->
      <div class="progress-overview">
        <div class="overview-item">
          <span class="label">当前阶段：</span>
          <span class="value">{{ processDetail.current_stage }}</span>
        </div>
        <div class="overview-item">
          <span class="label">整体进度：</span>
          <el-progress 
            :percentage="processDetail.progress_percentage || 0"
            :color="getProgressColor(processDetail.progress_percentage)"
          />
        </div>
      </div>

      <!-- 16阶段流程图 -->
      <div class="process-flow">
        <h4>全流程视图（16个标准阶段）</h4>
        <div class="flow-stages">
          <div 
            v-for="(stage, index) in flowStages"
            :key="index"
            class="flow-stage"
            :class="getStageClass(stage, index)"
          >
            <div class="stage-number">{{ index + 1 }}</div>
            <div class="stage-info">
              <div class="stage-name">{{ stage.name }}</div>
              <div class="stage-status">
                <template v-if="isStageCompleted(stage.name)">
                  <el-icon color="#67C23A"><CircleCheck /></el-icon>
                  <span class="completed-text">已完成</span>
                </template>
                <template v-else-if="isCurrentStage(stage.name)">
                  <el-icon color="#409EFF"><Loading /></el-icon>
                  <span class="current-text">进行中</span>
                </template>
                <template v-else>
                  <el-icon color="#C0C4CC"><Clock /></el-icon>
                  <span class="pending-text">待处理</span>
                </template>
              </div>
            </div>
            <div class="stage-connector" v-if="index < flowStages.length - 1"></div>
          </div>
        </div>
      </div>

      <!-- 时间线 -->
      <div class="timeline-section mt-30">
        <h4>流程跟踪时间线</h4>
        <el-timeline>
          <el-timeline-item
            v-for="track in timeline"
            :key="track.id"
            :timestamp="formatDateTime(track.created_at)"
            :type="getTimelineType(track.status)"
            :color="getTimelineColor(track.status)"
            size="large"
          >
            <div class="timeline-content">
              <div class="timeline-stage">{{ track.stage }}</div>
              <div class="timeline-action">{{ track.action || '进入此阶段' }}</div>
              <div class="timeline-meta">
                <span v-if="track.operator">操作人：{{ track.operator }}</span>
                <span v-if="track.duration" class="ml-20">
                  耗时：{{ formatDuration(track.duration) }}
                </span>
              </div>
              <div v-if="track.notes" class="timeline-notes">
                备注：{{ track.notes }}
              </div>
            </div>
          </el-timeline-item>
          
          <el-timeline-item
            v-if="!timeline.length"
            timestamp="等待中"
            type="info"
          >
            暂无跟踪记录
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-card>
    
    <el-card v-else>
      <el-empty description="请选择流程实例" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Back, CircleCheck, Loading, Clock, Calendar } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from '@/api/axios'

const route = useRoute()
const router = useRouter()

const processDetail = ref(null)
const timeline = ref([])
const flowStages = ref([
  { name: "市场调研" },
  { name: "客户开发" },
  { name: "项目开发" },
  { name: "投产管理" },
  { name: "订单管理" },
  { name: "生产计划" },
  { name: "物料需求计划" },
  { name: "采购计划" },
  { name: "到料" },
  { name: "生产执行" },
  { name: "检验" },
  { name: "入库" },
  { name: "储存" },
  { name: "交付" },
  { name: "发运" },
  { name: "客户账款回款" }
])

const statusLabels = {
  pending: '待处理',
  in_progress: '进行中',
  completed: '已完成',
  suspended: '已暂停'
}

const statusTypes = {
  pending: 'info',
  in_progress: 'warning',
  completed: 'success',
  suspended: 'info'
}

const getStatusText = (status) => statusLabels[status] || status
const getStatusType = (status) => statusTypes[status] || ''

const getProgressColor = (percentage) => {
  if (percentage < 30) return '#F56C6C'
  if (percentage < 70) return '#E6A23C'
  return '#67C23A'
}

const isStageCompleted = (stageName) => {
  return timeline.value.some(t => t.stage === stageName && t.status === 'completed')
}

const isCurrentStage = (stageName) => {
  return processDetail.value?.current_stage === stageName
}

const getStageClass = (stage, index) => {
  if (isStageCompleted(stage.name)) return 'completed'
  if (isCurrentStage(stage.name)) return 'current'
  return 'pending'
}

const getTimelineType = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'error') return 'danger'
  return 'primary'
}

const getTimelineColor = (status) => {
  if (status === 'completed') return '#67C23A'
  if (status === 'error') return '#F56C6C'
  return '#409EFF'
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDuration = (seconds) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}小时${minutes}分钟`
}

const loadProcessDetail = async (instanceId) => {
  try {
    const response = await axios.get(`/process/instances/${instanceId}/progress`)
    processDetail.value = response
    timeline.value = response.timeline || []
  } catch (error) {
    console.error('加载流程详情失败:', error)
    ElMessage.error('加载流程详情失败')
  }
}

const goBack = () => {
  router.push('/process/list')
}

onMounted(() => {
  const instanceId = route.query.id
  if (instanceId) {
    loadProcessDetail(instanceId)
  }
})
</script>

<style scoped>
.process-tracking {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  display: inline-block;
}

.ml-10 {
  margin-left: 10px;
}

.ml-20 {
  margin-left: 20px;
}

.mt-30 {
  margin-top: 30px;
}

.progress-overview {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.overview-item {
  margin-bottom: 16px;
}

.overview-item:last-child {
  margin-bottom: 0;
}

.overview-item .label {
  font-weight: bold;
  color: #606266;
  margin-right: 12px;
}

.overview-item .value {
  color: #303133;
  font-size: 16px;
}

.process-flow {
  margin-top: 30px;
}

.process-flow h4 {
  margin-bottom: 20px;
  color: #303133;
}

.flow-stages {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.flow-stage {
  position: relative;
  padding: 16px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  background: white;
  transition: all 0.3s;
}

.flow-stage.completed {
  border-color: #67C23A;
  background: #f0f9ff;
}

.flow-stage.current {
  border-color: #409EFF;
  background: #ecf5ff;
  box-shadow: 0 0 10px rgba(64, 158, 255, 0.3);
}

.flow-stage.pending {
  border-color: #e4e7ed;
  background: #fafafa;
}

.stage-number {
  position: absolute;
  top: -12px;
  left: 12px;
  width: 24px;
  height: 24px;
  background: #409EFF;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

.flow-stage.completed .stage-number {
  background: #67C23A;
}

.flow-stage.pending .stage-number {
  background: #C0C4CC;
}

.stage-info {
  margin-top: 8px;
}

.stage-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
}

.stage-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.completed-text {
  color: #67C23A;
}

.current-text {
  color: #409EFF;
}

.pending-text {
  color: #909399;
}

.timeline-section {
  margin-top: 30px;
  padding-top: 30px;
  border-top: 1px solid #e4e7ed;
}

.timeline-section h4 {
  margin-bottom: 20px;
  color: #303133;
}

.timeline-content {
  padding: 8px 0;
}

.timeline-stage {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.timeline-action {
  font-size: 14px;
  color: #606266;
  margin-bottom: 6px;
}

.timeline-meta {
  font-size: 13px;
  color: #909399;
}

.timeline-notes {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-left: 3px solid #409EFF;
  font-size: 13px;
  color: #606266;
}
</style>
