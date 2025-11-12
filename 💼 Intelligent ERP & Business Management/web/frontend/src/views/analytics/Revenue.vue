<template>
  <div class="revenue-analytics">
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="周期类型">
          <el-select v-model="filters.periodType" @change="loadData">
            <el-option label="日" value="daily" />
            <el-option label="周" value="weekly" />
            <el-option label="月" value="monthly" />
            <el-option label="季" value="quarterly" />
            <el-option label="年" value="yearly" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="客户类别">
          <el-select v-model="filters.customerCategory" clearable @change="loadData">
            <el-option label="全部" value="" />
            <el-option label="VIP客户" value="VIP" />
            <el-option label="普通客户" value="普通" />
            <el-option label="新客户" value="新客户" />
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
        <el-card class="stat-card revenue">
          <div class="stat-content">
            <div class="stat-label">总营收</div>
            <div class="stat-value">¥ {{ formatNumber(analysisData.total_revenue) }}</div>
            <div class="stat-icon">💰</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card orders">
          <div class="stat-content">
            <div class="stat-label">订单总量</div>
            <div class="stat-value">{{ analysisData.order_stats?.total_orders || 0 }}</div>
            <div class="stat-icon">📦</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card average">
          <div class="stat-content">
            <div class="stat-label">平均订单金额</div>
            <div class="stat-value">¥ {{ formatNumber(analysisData.order_stats?.average_order_amount) }}</div>
            <div class="stat-icon">📊</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card customers">
          <div class="stat-content">
            <div class="stat-label">客户类别</div>
            <div class="stat-value">{{ Object.keys(analysisData.customer_category_stats || {}).length }}</div>
            <div class="stat-icon">👥</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>营收趋势</span>
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
              <span>客户类别分布</span>
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

    <!-- 产品统计 -->
    <el-row class="mt-20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>产品销售统计</span>
              <el-button type="primary" size="small" :icon="Download">导出</el-button>
            </div>
          </template>
          
          <el-table
            :data="analysisData.order_detail_summary"
            stripe
            style="width: 100%"
            v-loading="loading"
          >
            <el-table-column prop="product_code" label="产品编码" width="120" />
            <el-table-column prop="product_name" label="产品名称" width="200" />
            <el-table-column label="销售数量" width="120">
              <template #default="scope">
                {{ scope.row.total_quantity }}
              </template>
            </el-table-column>
            <el-table-column label="销售金额" width="150">
              <template #default="scope">
                <span class="amount positive">¥ {{ formatNumber(scope.row.total_amount) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="订单数量" width="120">
              <template #default="scope">
                {{ scope.row.order_count }}
              </template>
            </el-table-column>
            <el-table-column label="平均单价">
              <template #default="scope">
                ¥ {{ formatNumber(scope.row.total_amount / scope.row.total_quantity) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Refresh, Download, MagicStick, Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import axios from '@/api/axios'
import { getRevenueAnalysis, recommendChartType, generateChartConfig, smartChart } from '@/api/analytics'

const filters = ref({
  periodType: 'monthly',
  customerCategory: ''
})

const analysisData = ref({
  total_revenue: 0,
  customer_category_stats: {},
  order_stats: {},
  order_detail_summary: [],
  time_dimension_data: {}
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

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      period_type: filters.value.periodType
    }
    
    if (filters.value.customerCategory) {
      params.customer_category = filters.value.customerCategory
    }
    
    const response = await getRevenueAnalysis(params)
    analysisData.value = response
    
    updateCharts()
    ElMessage.success('数据加载成功')
  } catch (error) {
    console.error('加载开源分析失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 使用图表专家推荐
const useChartExpert = async (category) => {
  try {
    currentChartCategory.value = category
    
    let chartData = {}
    let purpose = ''
    
    if (category === 'trend') {
      const timeData = analysisData.value.time_dimension_data?.daily || []
      const dates = timeData.map(item => item.date)
      const revenues = timeData.map(item => item.revenue)
      
      chartData = {
        keys: dates,
        values: [revenues],
        series_names: ['营收'],
        title: '营收趋势',
        metadata: {
          has_time: true,
          series_count: 1
        }
      }
      purpose = '趋势分析'
    } else if (category === 'pie') {
      const categoryStats = analysisData.value.customer_category_stats || {}
      chartData = {
        keys: Object.keys(categoryStats),
        values: Object.values(categoryStats),
        title: '客户类别分布',
        metadata: {
          is_proportion: true
        }
      }
      purpose = '占比展示'
    }
    
    const response = await smartChart(chartData, purpose)
    
    if (response.success && response.config) {
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
    
    let chartData = {}
    let purpose = ''
    
    if (category === 'trend') {
      const timeData = analysisData.value.time_dimension_data?.daily || []
      const dates = timeData.map(item => item.date)
      const revenues = timeData.map(item => item.revenue)
      
      chartData = {
        keys: dates,
        values: [revenues],
        series_names: ['营收'],
        title: '营收趋势',
        metadata: {
          has_time: true,
          series_count: 1
        }
      }
      purpose = '趋势分析'
    } else if (category === 'pie') {
      const categoryStats = analysisData.value.customer_category_stats || {}
      chartData = {
        keys: Object.keys(categoryStats),
        values: Object.values(categoryStats),
        title: '客户类别分布',
        metadata: {
          is_proportion: true
        }
      }
      purpose = '占比展示'
    }
    
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
    
    let chartData = {}
    
    if (category === 'trend') {
      const timeData = analysisData.value.time_dimension_data?.daily || []
      const dates = timeData.map(item => item.date)
      const revenues = timeData.map(item => item.revenue)
      
      chartData = {
        keys: dates,
        values: [revenues],
        series_names: ['营收'],
        title: '营收趋势'
      }
    } else if (category === 'pie') {
      const categoryStats = analysisData.value.customer_category_stats || {}
      chartData = {
        keys: Object.keys(categoryStats),
        values: Object.values(categoryStats),
        title: '客户类别分布'
      }
    }
    
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

const updateCharts = () => {
  updateTrendChart()
  updatePieChart()
}

const updateTrendChart = () => {
  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChart.value)
  }
  
  const timeData = analysisData.value.time_dimension_data?.daily || []
  const dates = timeData.map(item => item.date)
  const revenues = timeData.map(item => item.revenue)
  
  const option = {
    title: {
      text: '营收趋势分析',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const param = params[0]
        return `${param.name}<br/>营收: ¥${formatNumber(param.value)}`
      }
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value) => '¥' + (value / 1000).toFixed(0) + 'k'
      }
    },
    series: [
      {
        name: '营收',
        type: 'line',
        data: revenues,
        smooth: true,
        itemStyle: { color: '#67C23A' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
              { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
            ]
          }
        }
      }
    ],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    }
  }
  
  trendChartInstance.setOption(option)
}

const updatePieChart = () => {
  if (!pieChartInstance) {
    pieChartInstance = echarts.init(pieChart.value)
  }
  
  const categoryStats = analysisData.value.customer_category_stats || {}
  const data = Object.keys(categoryStats).map(key => ({
    name: key,
    value: categoryStats[key]
  }))
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: ¥{c}<br/>占比: {d}%'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'center'
    },
    series: [
      {
        name: '客户类别',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{d}%'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: data,
        color: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']
      }
    ]
  }
  
  pieChartInstance.setOption(option)
}

onMounted(() => {
  loadData()
  
  window.addEventListener('resize', () => {
    trendChartInstance?.resize()
    pieChartInstance?.resize()
  })
})
</script>

<style scoped>
.revenue-analytics {
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

.stat-card.orders {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-card.average {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.stat-card.customers {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.stat-card.revenue .stat-label,
.stat-card.orders .stat-label,
.stat-card.average .stat-label,
.stat-card.customers .stat-label,
.stat-card.revenue .stat-value,
.stat-card.orders .stat-value,
.stat-card.average .stat-value,
.stat-card.customers .stat-value {
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

.amount.positive {
  color: #67C23A;
}
</style>
