<template>
  <div class="finance-dashboard">
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="周期类型">
          <el-select v-model="filters.periodType" @change="loadDashboard">
            <el-option label="日" value="daily" />
            <el-option label="周" value="weekly" />
            <el-option label="月" value="monthly" />
            <el-option label="季" value="quarterly" />
            <el-option label="年" value="yearly" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="filters.startDate"
            type="date"
            placeholder="选择日期"
            @change="loadDashboard"
          />
        </el-form-item>
        
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="filters.endDate"
            type="date"
            placeholder="选择日期"
            @change="loadDashboard"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" :icon="Refresh" @click="loadDashboard">
            刷新
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="6">
        <el-card class="stat-card revenue">
          <div class="stat-content">
            <div class="stat-label">收入</div>
            <div class="stat-value">¥ {{ formatNumber(dashboardData.revenue) }}</div>
            <div class="stat-icon">💰</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card expense">
          <div class="stat-content">
            <div class="stat-label">支出</div>
            <div class="stat-value">¥ {{ formatNumber(dashboardData.expense) }}</div>
            <div class="stat-icon">💸</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card profit">
          <div class="stat-content">
            <div class="stat-label">利润</div>
            <div class="stat-value">¥ {{ formatNumber(dashboardData.profit) }}</div>
            <div class="stat-icon">📈</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card assets">
          <div class="stat-content">
            <div class="stat-label">资产</div>
            <div class="stat-value">¥ {{ formatNumber(dashboardData.assets) }}</div>
            <div class="stat-icon">🏦</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>收入支出趋势</span>
              <el-button-group>
                <el-button size="small" @click="useChartExpert('trend')">
                  <el-icon><MagicStick /></el-icon>
                  智能推荐
                </el-button>
                <el-button size="small" @click="showChartSelector('trend')">
                  <el-icon><Setting /></el-icon>
                  切换图表
                </el-button>
              </el-button-group>
            </div>
          </template>
          <div ref="trendChart" style="height: 400px;"></div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>财务构成</span>
              <el-button-group>
                <el-button size="small" @click="useChartExpert('pie')">
                  <el-icon><MagicStick /></el-icon>
                  智能推荐
                </el-button>
                <el-button size="small" @click="showChartSelector('pie')">
                  <el-icon><Setting /></el-icon>
                  切换图表
                </el-button>
              </el-button-group>
            </div>
          </template>
          <div ref="pieChart" style="height: 400px;"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表选择对话框 -->
    <el-dialog v-model="chartSelectorVisible" title="选择图表类型" width="600px">
      <el-radio-group v-model="selectedChartType">
        <el-radio 
          v-for="chart in chartRecommendations" 
          :key="chart.chart_type" 
          :label="chart.chart_type"
        >
          <div>
            <strong>{{ chart.name }}</strong>
            <p style="margin: 5px 0; color: #909399; font-size: 12px;">
              {{ chart.description }}
            </p>
            <el-tag size="small" type="info">推荐度: {{ chart.score }}分</el-tag>
          </div>
        </el-radio>
      </el-radio-group>
      <template #footer>
        <el-button @click="chartSelectorVisible = false">取消</el-button>
        <el-button type="primary" @click="applyChartType">应用</el-button>
      </template>
    </el-dialog>

    <el-row class="mt-20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>详细数据</span>
              <el-button type="primary" size="small" :icon="Download">导出</el-button>
            </div>
          </template>
          
          <el-table
            :data="dashboardData.daily_data"
            stripe
            style="width: 100%"
            v-loading="loading"
          >
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column label="收入" width="150">
              <template #default="scope">
                <span class="amount positive">¥ {{ formatNumber(scope.row.revenue) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="支出" width="150">
              <template #default="scope">
                <span class="amount negative">¥ {{ formatNumber(scope.row.expense) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="利润">
              <template #default="scope">
                <span 
                  class="amount" 
                  :class="scope.row.profit >= 0 ? 'positive' : 'negative'"
                >
                  ¥ {{ formatNumber(scope.row.profit) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Refresh, Download, MagicStick, Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getFinanceDashboard, recommendChartType, generateChartConfig, smartChart } from '@/api/finance'

const filters = ref({
  periodType: 'monthly',
  startDate: null,
  endDate: null
})

const dashboardData = ref({
  revenue: 0,
  expense: 0,
  profit: 0,
  assets: 0,
  liabilities: 0,
  investment: 0,
  daily_data: []
})

const loading = ref(false)
const trendChart = ref(null)
const pieChart = ref(null)
const chartSelectorVisible = ref(false)
const selectedChartType = ref('')
const currentChartCategory = ref('') // 'trend' or 'pie'
const chartRecommendations = ref([])

let trendChartInstance = null
let pieChartInstance = null

const formatNumber = (num) => {
  if (!num && num !== 0) return '0.00'
  return Number(num).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const loadDashboard = async () => {
  loading.value = true
  try {
    const params = {
      period_type: filters.value.periodType
    }
    
    if (filters.value.startDate) {
      params.start_date = filters.value.startDate.toISOString().split('T')[0]
    }
    if (filters.value.endDate) {
      params.end_date = filters.value.endDate.toISOString().split('T')[0]
    }
    
    const data = await getFinanceDashboard(params)
    dashboardData.value = data
    
    updateCharts()
    ElMessage.success('数据加载成功')
  } catch (error) {
    console.error('加载财务看板失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const updateCharts = () => {
  updateTrendChart()
  updatePieChart()
}

// 使用图表专家推荐
const useChartExpert = async (category) => {
  try {
    currentChartCategory.value = category
    
    // 准备数据
    let chartData = {}
    let purpose = ''
    
    if (category === 'trend') {
      const dates = dashboardData.value.daily_data.map(item => item.date)
      const revenues = dashboardData.value.daily_data.map(item => item.revenue)
      const expenses = dashboardData.value.daily_data.map(item => item.expense)
      const profits = dashboardData.value.daily_data.map(item => item.profit)
      
      chartData = {
        keys: dates,
        values: [revenues, expenses, profits],
        series_names: ['收入', '支出', '利润'],
        title: '收入支出趋势',
        metadata: {
          has_time: true,
          series_count: 3
        }
      }
      purpose = '趋势分析'
    } else if (category === 'pie') {
      chartData = {
        keys: ['收入', '支出', '资产', '负债'],
        values: [
          dashboardData.value.revenue,
          dashboardData.value.expense,
          dashboardData.value.assets,
          dashboardData.value.liabilities
        ],
        title: '财务构成',
        metadata: {
          is_proportion: true
        }
      }
      purpose = '占比展示'
    }
    
    // 调用图表专家
    const response = await smartChart(chartData, purpose)
    
    if (response.success && response.config) {
      // 应用推荐的图表配置
      if (category === 'trend') {
        if (!trendChartInstance) {
          trendChartInstance = echarts.init(trendChart.value)
        }
        trendChartInstance.setOption(response.config)
        ElMessage.success(`已应用推荐图表: ${response.best_chart?.name || '折线图'}`)
      } else if (category === 'pie') {
        if (!pieChartInstance) {
          pieChartInstance = echarts.init(pieChart.value)
        }
        pieChartInstance.setOption(response.config)
        ElMessage.success(`已应用推荐图表: ${response.best_chart?.name || '饼图'}`)
      }
    }
  } catch (error) {
    console.error('图表专家推荐失败:', error)
    ElMessage.warning('图表专家推荐失败，使用默认图表')
  }
}

// 显示图表选择器
const showChartSelector = async (category) => {
  try {
    currentChartCategory.value = category
    
    // 准备数据
    let chartData = {}
    let purpose = ''
    
    if (category === 'trend') {
      const dates = dashboardData.value.daily_data.map(item => item.date)
      const revenues = dashboardData.value.daily_data.map(item => item.revenue)
      const expenses = dashboardData.value.daily_data.map(item => item.expense)
      const profits = dashboardData.value.daily_data.map(item => item.profit)
      
      chartData = {
        keys: dates,
        values: [revenues, expenses, profits],
        series_names: ['收入', '支出', '利润'],
        title: '收入支出趋势',
        metadata: {
          has_time: true,
          series_count: 3
        }
      }
      purpose = '趋势分析'
    } else if (category === 'pie') {
      chartData = {
        keys: ['收入', '支出', '资产', '负债'],
        values: [
          dashboardData.value.revenue,
          dashboardData.value.expense,
          dashboardData.value.assets,
          dashboardData.value.liabilities
        ],
        title: '财务构成',
        metadata: {
          is_proportion: true
        }
      }
      purpose = '占比展示'
    }
    
    // 获取推荐列表
    const response = await recommendChartType(chartData, purpose)
    
    if (response.success && response.recommendations) {
      chartRecommendations.value = response.recommendations
      selectedChartType.value = response.recommendations[0]?.chart_type || ''
      chartSelectorVisible.value = true
    }
  } catch (error) {
    console.error('获取图表推荐失败:', error)
    ElMessage.error('获取图表推荐失败')
  }
}

// 应用选中的图表类型
const applyChartType = async () => {
  if (!selectedChartType.value) {
    ElMessage.warning('请选择图表类型')
    return
  }
  
  try {
    const category = currentChartCategory.value
    
    // 准备数据
    let chartData = {}
    
    if (category === 'trend') {
      const dates = dashboardData.value.daily_data.map(item => item.date)
      const revenues = dashboardData.value.daily_data.map(item => item.revenue)
      const expenses = dashboardData.value.daily_data.map(item => item.expense)
      const profits = dashboardData.value.daily_data.map(item => item.profit)
      
      chartData = {
        keys: dates,
        values: [revenues, expenses, profits],
        series_names: ['收入', '支出', '利润'],
        title: '收入支出趋势'
      }
    } else if (category === 'pie') {
      chartData = {
        keys: ['收入', '支出', '资产', '负债'],
        values: [
          dashboardData.value.revenue,
          dashboardData.value.expense,
          dashboardData.value.assets,
          dashboardData.value.liabilities
        ],
        title: '财务构成'
      }
    }
    
    // 生成图表配置
    const response = await generateChartConfig(selectedChartType.value, chartData)
    
    if (response.success && response.config) {
      if (category === 'trend') {
        if (!trendChartInstance) {
          trendChartInstance = echarts.init(trendChart.value)
        }
        trendChartInstance.setOption(response.config)
      } else if (category === 'pie') {
        if (!pieChartInstance) {
          pieChartInstance = echarts.init(pieChart.value)
        }
        pieChartInstance.setOption(response.config)
      }
      
      chartSelectorVisible.value = false
      const chartName = chartRecommendations.value.find(c => c.chart_type === selectedChartType.value)?.name || selectedChartType.value
      ElMessage.success(`已切换到: ${chartName}`)
    }
  } catch (error) {
    console.error('应用图表类型失败:', error)
    ElMessage.error('应用图表类型失败')
  }
}

const updateTrendChart = () => {
  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChart.value)
  }
  
  const dates = dashboardData.value.daily_data.map(item => item.date)
  const revenues = dashboardData.value.daily_data.map(item => item.revenue)
  const expenses = dashboardData.value.daily_data.map(item => item.expense)
  const profits = dashboardData.value.daily_data.map(item => item.profit)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['收入', '支出', '利润']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value) => '¥' + (value / 1000).toFixed(0) + 'k'
      }
    },
    series: [
      {
        name: '收入',
        type: 'line',
        data: revenues,
        smooth: true,
        itemStyle: { color: '#67C23A' }
      },
      {
        name: '支出',
        type: 'line',
        data: expenses,
        smooth: true,
        itemStyle: { color: '#F56C6C' }
      },
      {
        name: '利润',
        type: 'line',
        data: profits,
        smooth: true,
        itemStyle: { color: '#409EFF' }
      }
    ]
  }
  
  trendChartInstance.setOption(option)
}

const updatePieChart = () => {
  if (!pieChartInstance) {
    pieChartInstance = echarts.init(pieChart.value)
  }
  
  const data = [
    { value: dashboardData.value.revenue, name: '收入' },
    { value: dashboardData.value.expense, name: '支出' },
    { value: dashboardData.value.assets, name: '资产' },
    { value: dashboardData.value.liabilities, name: '负债' }
  ]
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: ¥{c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '财务构成',
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
  
  pieChartInstance.setOption(option)
}

onMounted(() => {
  loadDashboard()
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    trendChartInstance?.resize()
    pieChartInstance?.resize()
  })
})
</script>

<style scoped>
.finance-dashboard {
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

.stat-card.revenue {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-card.expense {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-card.profit {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.stat-card.assets {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.stat-card.revenue .stat-label,
.stat-card.expense .stat-label,
.stat-card.profit .stat-label,
.stat-card.assets .stat-label,
.stat-card.revenue .stat-value,
.stat-card.expense .stat-value,
.stat-card.profit .stat-value,
.stat-card.assets .stat-value {
  color: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.amount {
  font-weight: 500;
}

.amount.positive {
  color: #67C23A;
}

.amount.negative {
  color: #F56C6C;
}
</style>

