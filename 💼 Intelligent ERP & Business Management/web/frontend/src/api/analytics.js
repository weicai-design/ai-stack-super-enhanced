import axios from './axios'

/**
 * 经营分析API
 */

// 开源分析
export const getRevenueAnalysis = (params) => {
  return axios.get('/analytics/revenue', { params })
}

// 成本分析
export const getCostAnalysis = (params) => {
  return axios.get('/analytics/cost', { params })
}

// 产出效益分析
export const getOutputAnalysis = (params) => {
  return axios.get('/analytics/output', { params })
}

/**
 * 图表专家API
 * 集成图表专家功能，智能推荐图表类型
 */
const CHART_EXPERT_API_URL = 'http://localhost:8000/api/chart-expert'

// 推荐图表类型
export const recommendChartType = (data, purpose) => {
  return axios.post(`${CHART_EXPERT_API_URL}/recommend`, {
    data,
    purpose
  })
}

// 生成图表配置
export const generateChartConfig = (chartType, data, options) => {
  return axios.post(`${CHART_EXPERT_API_URL}/generate-config`, {
    chart_type: chartType,
    data,
    options: options || {}
  })
}

// 智能图表生成（一站式）
export const smartChart = (data, purpose) => {
  return axios.post(`${CHART_EXPERT_API_URL}/smart-chart`, {
    data,
    purpose
  })
}

