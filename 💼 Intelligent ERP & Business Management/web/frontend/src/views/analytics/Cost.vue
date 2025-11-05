<template>
  <div class="cost-analytics">
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

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="8">
        <el-card class="stat-card total-cost">
          <div class="stat-content">
            <div class="stat-label">总成本</div>
            <div class="stat-value">¥ {{ formatNumber(analysisData.total_cost) }}</div>
            <div class="stat-icon">💸</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="stat-card profit-margin">
          <div class="stat-content">
            <div class="stat-label">利润率</div>
            <div class="stat-value">{{ formatNumber(analysisData.break_even_analysis?.profit_margin) }}%</div>
            <div class="stat-icon">📈</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="stat-card break-even">
          <div class="stat-content">
            <div class="stat-label">盈亏平衡点</div>
            <div class="stat-value">¥ {{ formatNumber(analysisData.break_even_analysis?.break_even_point) }}</div>
            <div class="stat-icon">⚖️</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>费用类别占比</span>
            </div>
          </template>
          <div ref="costPieChart" style="height: 400px;"></div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>盈亏平衡分析</span>
            </div>
          </template>
          <div ref="breakEvenChart" style="height: 400px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 费用明细 -->
    <el-row class="mt-20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>费用明细统计</span>
            </div>
          </template>
          
          <el-descriptions :column="3" border>
            <el-descriptions-item 
              v-for="(value, category) in analysisData.cost_by_category"
              :key="category"
              :label="category"
            >
              <span class="amount negative">¥ {{ formatNumber(value) }}</span>
            </el-descriptions-item>
          </el-descriptions>
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
  break_even_analysis: {},
  cost_reasonableness: {}
})

const loading = ref(false)
const costPieChart = ref(null)
const breakEvenChart = ref(null)

let costPieChartInstance = null
let breakEvenChartInstance = null

const formatNumber = (num) => {
  if (!num && num !== 0) return '0.00'
  return Number(num).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      period_type: filters.value.periodType
    }
    
    const response = await axios.get('/analytics/cost', { params })
    analysisData.value = response
    
    updateCharts()
    ElMessage.success('成本分析加载成功')
  } catch (error) {
    console.error('加载成本分析失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const updateCharts = () => {
  updateCostPieChart()
  updateBreakEvenChart()
}

const updateCostPieChart = () => {
  if (!costPieChartInstance) {
    costPieChartInstance = echarts.init(costPieChart.value)
  }
  
  const costData = analysisData.value.cost_by_category || {}
  const data = Object.keys(costData).map(key => ({
    name: key,
    value: costData[key]
  }))
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: ¥{c}<br/>占比: {d}%'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '费用类别',
        type: 'pie',
        radius: '70%',
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
  
  costPieChartInstance.setOption(option)
}

const updateBreakEvenChart = () => {
  if (!breakEvenChartInstance) {
    breakEvenChartInstance = echarts.init(breakEvenChart.value)
  }
  
  const breakEven = analysisData.value.break_even_analysis || {}
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    xAxis: {
      type: 'category',
      data: ['收入', '成本', '利润']
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value) => '¥' + (value / 1000).toFixed(0) + 'k'
      }
    },
    series: [
      {
        name: '金额',
        type: 'bar',
        data: [
          {
            value: breakEven.revenue || 0,
            itemStyle: { color: '#67C23A' }
          },
          {
            value: breakEven.cost || 0,
            itemStyle: { color: '#F56C6C' }
          },
          {
            value: breakEven.profit || 0,
            itemStyle: { color: '#409EFF' }
          }
        ],
        label: {
          show: true,
          position: 'top',
          formatter: (params) => '¥' + formatNumber(params.value)
        }
      }
    ],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    }
  }
  
  breakEvenChartInstance.setOption(option)
}

onMounted(() => {
  loadData()
  
  window.addEventListener('resize', () => {
    costPieChartInstance?.resize()
    breakEvenChartInstance?.resize()
  })
})
</script>

<style scoped>
.cost-analytics {
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

.stat-card.total-cost {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-card.profit-margin {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.stat-card.break-even {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
}

.stat-card.total-cost .stat-label,
.stat-card.profit-margin .stat-label,
.stat-card.break-even .stat-label,
.stat-card.total-cost .stat-value,
.stat-card.profit-margin .stat-value,
.stat-card.break-even .stat-value {
  color: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.amount {
  font-weight: 500;
}

.amount.negative {
  color: #F56C6C;
}
</style>
