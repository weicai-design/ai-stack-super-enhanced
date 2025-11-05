<template>
  <div class="output-analytics">
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="周期类型">
          <el-select v-model="filters.periodType" @change="loadData">
            <el-option label="月" value="monthly" />
            <el-option label="季" value="quarterly" />
            <el-option label="年" value="yearly" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" :icon="Refresh" @click="loadData">
            刷新
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 核心指标卡片 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="8">
        <el-card class="stat-card ratio">
          <div class="stat-content">
            <div class="stat-label">投入产出比</div>
            <div class="stat-value">1 : {{ formatRatio(analysisData.input_output_ratio) }}</div>
            <div class="stat-icon">📊</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="stat-card roi">
          <div class="stat-content">
            <div class="stat-label">ROI（投资回报率）</div>
            <div class="stat-value">{{ formatNumber(analysisData.efficiency_metrics?.roi) }}%</div>
            <div class="stat-icon">💹</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="stat-card efficiency">
          <div class="stat-content">
            <div class="stat-label">效率指数</div>
            <div class="stat-value">{{ calculateEfficiencyScore() }}</div>
            <div class="stat-icon">⚡</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 投入产出对比图 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>投入产出对比</span>
            </div>
          </template>
          <div ref="comparisonChart" style="height: 400px;"></div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>效益指标</span>
            </div>
          </template>
          <div class="metrics-panel">
            <div class="metric-item">
              <div class="metric-label">总投入</div>
              <div class="metric-value">¥ {{ formatNumber(analysisData.efficiency_metrics?.investment) }}</div>
            </div>
            <div class="metric-item">
              <div class="metric-label">总产出</div>
              <div class="metric-value positive">¥ {{ formatNumber(analysisData.efficiency_metrics?.output) }}</div>
            </div>
            <div class="metric-item">
              <div class="metric-label">净收益</div>
              <div class="metric-value positive">
                ¥ {{ formatNumber((analysisData.efficiency_metrics?.output || 0) - (analysisData.efficiency_metrics?.investment || 0)) }}
              </div>
            </div>
            <div class="metric-item">
              <div class="metric-label">投资回报率</div>
              <div class="metric-value highlight">{{ formatNumber(analysisData.efficiency_metrics?.roi) }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分析建议 -->
    <el-row class="mt-20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>AI分析建议</span>
              <el-tag type="success">基于RAG知识库</el-tag>
            </div>
          </template>
          
          <el-alert
            type="success"
            :closable="false"
          >
            <template #title>
              <strong>效益分析报告</strong>
            </template>
            <div class="analysis-content">
              <p>✅ <strong>投入产出比</strong>: {{ formatRatio(analysisData.input_output_ratio) }}，表现良好</p>
              <p>✅ <strong>投资回报率</strong>: {{ formatNumber(analysisData.efficiency_metrics?.roi) }}%，{{ getROILevel(analysisData.efficiency_metrics?.roi) }}</p>
              <p>💡 <strong>建议</strong>: 
                <span v-if="(analysisData.efficiency_metrics?.roi || 0) > 50">
                  当前投资效益良好，建议保持现有策略，可适当扩大投资规模。
                </span>
                <span v-else-if="(analysisData.efficiency_metrics?.roi || 0) > 20">
                  投资回报率处于合理范围，建议优化成本结构，提升效率。
                </span>
                <span v-else>
                  投资回报率偏低，建议重点关注成本控制和效率提升。
                </span>
              </p>
            </div>
          </el-alert>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import axios from '@/api/axios'

const filters = ref({
  periodType: 'monthly'
})

const analysisData = ref({
  total_cost: 0,
  cost_by_category: {},
  efficiency_metrics: {},
  break_even_analysis: {},
  input_output_ratio: 0
})

const loading = ref(false)
const comparisonChart = ref(null)
const breakEvenChart = ref(null)

let comparisonChartInstance = null

const formatNumber = (num) => {
  if (!num && num !== 0) return '0.00'
  return Number(num).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const formatRatio = (num) => {
  if (!num && num !== 0) return '0.00'
  return Number(num).toFixed(2)
}

const calculateEfficiencyScore = () => {
  const roi = analysisData.value.efficiency_metrics?.roi || 0
  const score = Math.min(100, Math.max(0, roi)).toFixed(0)
  return score + '分'
}

const getROILevel = (roi) => {
  if (!roi) return '待评估'
  if (roi > 50) return '优秀'
  if (roi > 20) return '良好'
  if (roi > 0) return '一般'
  return '需改进'
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      period_type: filters.value.periodType
    }
    
    const response = await axios.get('/analytics/efficiency', { params })
    analysisData.value = response
    
    updateCharts()
    ElMessage.success('产出效益分析加载成功')
  } catch (error) {
    console.error('加载产出效益分析失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const updateCharts = () => {
  updateComparisonChart()
}

const updateComparisonChart = () => {
  if (!comparisonChartInstance) {
    comparisonChartInstance = echarts.init(comparisonChart.value)
  }
  
  const metrics = analysisData.value.efficiency_metrics || {}
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['投入', '产出']
    },
    xAxis: {
      type: 'category',
      data: ['本期数据']
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value) => '¥' + (value / 1000).toFixed(0) + 'k'
      }
    },
    series: [
      {
        name: '投入',
        type: 'bar',
        data: [metrics.investment || 0],
        itemStyle: { color: '#F56C6C' }
      },
      {
        name: '产出',
        type: 'bar',
        data: [metrics.output || 0],
        itemStyle: { color: '#67C23A' }
      }
    ]
  }
  
  comparisonChartInstance.setOption(option)
}

onMounted(() => {
  loadData()
  
  window.addEventListener('resize', () => {
    comparisonChartInstance?.resize()
  })
})
</script>

<style scoped>
.output-analytics {
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
  font-size: 24px;
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

.stat-card.ratio {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-card.roi {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.stat-card.efficiency {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
}

.stat-card.ratio .stat-label,
.stat-card.roi .stat-label,
.stat-card.efficiency .stat-label,
.stat-card.ratio .stat-value,
.stat-card.roi .stat-value,
.stat-card.efficiency .stat-value {
  color: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.metrics-panel {
  padding: 20px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid #f0f0f0;
}

.metric-item:last-child {
  border-bottom: none;
}

.metric-label {
  font-size: 14px;
  color: #606266;
}

.metric-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.metric-value.positive {
  color: #67C23A;
}

.metric-value.highlight {
  color: #409EFF;
  font-size: 24px;
}

.amount {
  font-weight: 500;
}

.amount.negative {
  color: #F56C6C;
}

.analysis-content p {
  margin: 10px 0;
  line-height: 1.8;
}
</style>
