<template>
  <div class="eight-dimensions-page">
    <div class="page-header">
      <h2>📊 ERP 8维度深度分析</h2>
      <div class="header-actions">
        <el-button type="primary" @click="refreshAnalysis" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新分析
        </el-button>
        <el-button @click="exportReport">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
      </div>
    </div>

    <!-- 综合得分卡片 -->
    <div class="overall-score-card">
      <div class="score-main">
        <div class="score-value" :class="scoreLevelClass">
          {{ overallScore }}
        </div>
        <div class="score-label">综合得分</div>
        <div class="score-level">{{ overallLevelText }}</div>
      </div>
      <div class="score-breakdown">
        <div class="breakdown-item" v-for="dim in dimensionList" :key="dim.key">
          <div class="breakdown-label">{{ dim.name }}</div>
          <div class="breakdown-value">{{ dimensions[dim.key]?.score || 0 }}</div>
        </div>
      </div>
    </div>

    <!-- 8维度雷达图 -->
    <el-card class="radar-chart-card">
      <template #header>
        <span>8维度雷达图</span>
      </template>
      <div ref="radarChartRef" class="chart-container"></div>
    </el-card>

    <!-- 维度详情卡片 -->
    <div class="dimensions-grid">
      <el-card
        v-for="dim in dimensionList"
        :key="dim.key"
        class="dimension-card"
        :class="`dimension-${dim.key}`"
      >
        <template #header>
          <div class="dimension-header">
            <span class="dimension-icon">{{ dim.icon }}</span>
            <span class="dimension-name">{{ dim.name }}</span>
            <el-tag :type="getLevelTagType(dimensions[dim.key]?.level)" size="small">
              {{ dimensions[dim.key]?.level || 'N/A' }}
            </el-tag>
          </div>
        </template>
        
        <div class="dimension-content">
          <!-- 得分 -->
          <div class="dimension-score">
            <div class="score-number">{{ dimensions[dim.key]?.score || 0 }}</div>
            <div class="score-bar">
              <div 
                class="score-bar-fill" 
                :style="{ width: `${dimensions[dim.key]?.score || 0}%` }"
                :class="getScoreBarClass(dimensions[dim.key]?.score)"
              ></div>
            </div>
          </div>

          <!-- 指标 -->
          <div class="dimension-indicators">
            <div 
              class="indicator-item"
              v-for="(value, key) in dimensions[dim.key]?.indicators"
              :key="key"
            >
              <span class="indicator-label">{{ getIndicatorLabel(key) }}:</span>
              <span class="indicator-value">{{ value }}{{ getIndicatorUnit(key) }}</span>
            </div>
          </div>

          <!-- 分析 -->
          <div class="dimension-analysis">
            <div class="analysis-label">分析:</div>
            <div class="analysis-text">{{ dimensions[dim.key]?.analysis || '暂无分析' }}</div>
          </div>

          <!-- 建议 -->
          <div class="dimension-suggestions" v-if="dimensions[dim.key]?.suggestions?.length">
            <div class="suggestions-label">改进建议:</div>
            <ul class="suggestions-list">
              <li v-for="(suggestion, index) in dimensions[dim.key].suggestions" :key="index">
                {{ suggestion }}
              </li>
            </ul>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 综合报告 -->
    <el-card class="comprehensive-report-card">
      <template #header>
        <span>📋 综合分析报告</span>
      </template>
      <div class="report-content" v-html="reportContent"></div>
    </el-card>

    <!-- 改进建议 -->
    <el-card class="recommendations-card" v-if="recommendations.length">
      <template #header>
        <span>💡 优先级改进建议</span>
      </template>
      <div class="recommendations-list">
        <div 
          class="recommendation-item"
          v-for="(rec, index) in recommendations"
          :key="index"
        >
          <div class="recommendation-priority">{{ index + 1 }}</div>
          <div class="recommendation-content">
            <div class="recommendation-title">{{ rec.title || rec.dimension }}</div>
            <div class="recommendation-description">{{ rec.description || rec.suggestion }}</div>
            <div class="recommendation-impact" v-if="rec.expected_impact">
              预期影响: {{ rec.expected_impact }}
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Refresh, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import axios from 'axios'

const API_BASE = 'http://localhost:8013/api'

// 数据
const loading = ref(false)
const dimensions = ref({})
const overallScore = ref(0)
const overallLevel = ref('')
const reportContent = ref('')
const recommendations = ref([])
const radarChartRef = ref(null)
let radarChart = null

// 维度列表
const dimensionList = [
  { key: 'quality', name: '质量', icon: '✅' },
  { key: 'cost', name: '成本', icon: '💰' },
  { key: 'delivery', name: '交期', icon: '📦' },
  { key: 'safety', name: '安全', icon: '🛡️' },
  { key: 'profit', name: '利润', icon: '📈' },
  { key: 'efficiency', name: '效率', icon: '⚡' },
  { key: 'management', name: '管理', icon: '📋' },
  { key: 'technology', name: '技术', icon: '🔧' }
]

// 计算属性
const scoreLevelClass = computed(() => {
  if (overallScore.value >= 90) return 'score-excellent'
  if (overallScore.value >= 80) return 'score-good'
  if (overallScore.value >= 70) return 'score-average'
  if (overallScore.value >= 60) return 'score-poor'
  return 'score-critical'
})

const overallLevelText = computed(() => {
  const levelMap = {
    excellent: '优秀',
    good: '良好',
    average: '一般',
    poor: '较差',
    critical: '危险'
  }
  return levelMap[overallLevel.value] || '未知'
})

// 方法
const refreshAnalysis = async () => {
  loading.value = true
  try {
    // 获取ERP数据
    let erpData = {}
    try {
      const erpDataResponse = await axios.get(`${API_BASE}/analytics/eight-dimensions/data`)
      if (erpDataResponse.data.success) {
        erpData = erpDataResponse.data.data || {}
      }
    } catch (error) {
      console.warn('获取ERP数据失败，使用默认值:', error)
    }

    // 执行8维度分析
    const analysisResponse = await axios.post(`${API_BASE}/analytics/eight-dimensions`, erpData)
    const analysisResult = analysisResponse.data

    // 更新数据（兼容不同的响应格式）
    if (analysisResult.success && analysisResult.result) {
      // 旧格式：{success: true, result: {...}}
      dimensions.value = analysisResult.result.dimensions || {}
      overallScore.value = analysisResult.result.overall_score || 0
      overallLevel.value = analysisResult.result.overall_level || 'unknown'
      reportContent.value = analysisResult.result.report || ''
      recommendations.value = analysisResult.result.recommendations || []
    } else {
      // 新格式：直接返回分析结果
      dimensions.value = analysisResult.dimensions || {}
      overallScore.value = analysisResult.overall_score || 0
      overallLevel.value = analysisResult.overall_level || 'unknown'
      reportContent.value = analysisResult.report || ''
      recommendations.value = analysisResult.recommendations || []
    }

    // 更新雷达图
    updateRadarChart()

    ElMessage.success('分析完成')
  } catch (error) {
    console.error('分析失败:', error)
    ElMessage.error('分析失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const updateRadarChart = () => {
  if (!radarChartRef.value) return

  if (!radarChart) {
    radarChart = echarts.init(radarChartRef.value)
  }

  const option = {
    radar: {
      indicator: dimensionList.map(dim => ({
        name: dim.name,
        max: 100
      })),
      center: ['50%', '50%'],
      radius: '70%',
      nameGap: 20,
      splitNumber: 5,
      axisName: {
        color: '#666',
        fontSize: 14
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(250, 250, 250, 0.3)', 'rgba(200, 200, 200, 0.1)']
        }
      },
      splitLine: {
        lineStyle: {
          color: '#ddd'
        }
      },
      axisLine: {
        lineStyle: {
          color: '#ddd'
        }
      }
    },
    series: [{
      name: '8维度得分',
      type: 'radar',
      data: [{
        value: dimensionList.map(dim => dimensions.value[dim.key]?.score || 0),
        name: '当前得分',
        areaStyle: {
          color: 'rgba(64, 158, 255, 0.3)'
        },
        lineStyle: {
          color: '#409EFF',
          width: 2
        },
        itemStyle: {
          color: '#409EFF'
        }
      }]
    }]
  }

  radarChart.setOption(option)
}

const getLevelTagType = (level) => {
  const typeMap = {
    excellent: 'success',
    good: 'success',
    average: 'warning',
    poor: 'danger',
    critical: 'danger'
  }
  return typeMap[level] || 'info'
}

const getScoreBarClass = (score) => {
  if (score >= 90) return 'bar-excellent'
  if (score >= 80) return 'bar-good'
  if (score >= 70) return 'bar-average'
  if (score >= 60) return 'bar-poor'
  return 'bar-critical'
}

const getIndicatorLabel = (key) => {
  const labelMap = {
    pass_rate: '合格率',
    rework_rate: '返工率',
    defect_rate: '不良率',
    customer_complaint_rate: '客户投诉率',
    material_cost_ratio: '物料成本占比',
    labor_cost_ratio: '人工成本占比',
    overhead_cost_ratio: '制造费用占比',
    cost_reduction_rate: '成本降低率',
    on_time_delivery_rate: '准时交付率',
    delivery_cycle_time: '交付周期',
    delay_rate: '延期率',
    avg_delay_days: '平均延期天数',
    accident_count: '事故次数',
    safety_training_hours: '安全培训小时数',
    safety_compliance_rate: '安全合规率',
    safety_inspection_rate: '安全检查完成率',
    gross_profit_rate: '毛利率',
    net_profit_rate: '净利率',
    profit_margin: '利润率',
    revenue_growth_rate: '营收增长率',
    production_efficiency: '生产效率',
    equipment_utilization: '设备利用率',
    personnel_efficiency: '人员效率',
    oee: 'OEE综合效率',
    process_compliance_rate: '流程合规率',
    exception_handling_rate: '异常处理率',
    improvement_measures_count: '改进措施数',
    innovation_count: '创新项目数',
    process_improvement_rate: '工艺改进率',
    automation_level: '自动化水平'
  }
  return labelMap[key] || key
}

const getIndicatorUnit = (key) => {
  if (key.includes('rate') || key.includes('ratio') || key.includes('percent')) return '%'
  if (key.includes('hours')) return '小时'
  if (key.includes('days') || key.includes('cycle')) return '天'
  if (key.includes('count')) return '次'
  return ''
}

const exportReport = () => {
  // 导出报告功能
  const report = {
    overall_score: overallScore.value,
    overall_level: overallLevel.value,
    dimensions: dimensions.value,
    report: reportContent.value,
    recommendations: recommendations.value,
    timestamp: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ERP_8维度分析报告_${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('报告已导出')
}

onMounted(() => {
  refreshAnalysis()
  
  // 响应式调整图表大小
  window.addEventListener('resize', () => {
    if (radarChart) {
      radarChart.resize()
    }
  })
})
</script>

<style scoped>
.eight-dimensions-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.overall-score-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  color: white;
  display: flex;
  align-items: center;
  gap: 32px;
}

.score-main {
  text-align: center;
  min-width: 150px;
}

.score-value {
  font-size: 64px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 8px;
}

.score-label {
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.score-level {
  font-size: 18px;
  font-weight: 600;
  opacity: 0.95;
}

.score-breakdown {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.breakdown-item {
  text-align: center;
}

.breakdown-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.breakdown-value {
  font-size: 24px;
  font-weight: 600;
}

.radar-chart-card {
  margin-bottom: 24px;
}

.chart-container {
  width: 100%;
  height: 500px;
}

.dimensions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.dimension-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.dimension-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.dimension-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dimension-icon {
  font-size: 20px;
}

.dimension-name {
  flex: 1;
  font-weight: 600;
}

.dimension-content {
  padding: 16px 0;
}

.dimension-score {
  margin-bottom: 16px;
}

.score-number {
  font-size: 32px;
  font-weight: 700;
  color: var(--el-color-primary);
  margin-bottom: 8px;
}

.score-bar {
  width: 100%;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.score-bar-fill {
  height: 100%;
  transition: width 0.5s;
  border-radius: 4px;
}

.bar-excellent {
  background: #52c41a;
}

.bar-good {
  background: #73d13d;
}

.bar-average {
  background: #faad14;
}

.bar-poor {
  background: #ff7875;
}

.bar-critical {
  background: #ff4d4f;
}

.dimension-indicators {
  margin-bottom: 16px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
}

.indicator-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 14px;
}

.indicator-label {
  color: #666;
}

.indicator-value {
  font-weight: 600;
  color: #333;
}

.dimension-analysis {
  margin-bottom: 16px;
}

.analysis-label {
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.analysis-text {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.dimension-suggestions {
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.suggestions-label {
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.suggestions-list {
  margin: 0;
  padding-left: 20px;
}

.suggestions-list li {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
  margin-bottom: 4px;
}

.comprehensive-report-card {
  margin-bottom: 24px;
}

.report-content {
  line-height: 1.8;
  color: #333;
}

.recommendations-card {
  margin-bottom: 24px;
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recommendation-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #f9f9f9;
  border-radius: 8px;
  border-left: 4px solid var(--el-color-primary);
}

.recommendation-priority {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--el-color-primary);
  color: white;
  border-radius: 50%;
  font-weight: 600;
  flex-shrink: 0;
}

.recommendation-content {
  flex: 1;
}

.recommendation-title {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 8px;
  color: #333;
}

.recommendation-description {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 8px;
}

.recommendation-impact {
  font-size: 13px;
  color: var(--el-color-primary);
  font-weight: 500;
}

@media (max-width: 1200px) {
  .dimensions-grid {
    grid-template-columns: 1fr;
  }
  
  .score-breakdown {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

