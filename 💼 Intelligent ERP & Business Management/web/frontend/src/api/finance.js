import axios from './axios'

/**
 * 财务API
 */

// 获取财务看板数据
export const getFinanceDashboard = (params) => {
  return axios.get('/finance/dashboard', { params })
}

// 获取财务数据列表
export const getFinanceData = (params) => {
  return axios.get('/finance/data', { params })
}

// 创建财务数据
export const createFinanceData = (data) => {
  return axios.post('/finance/data', data)
}

// 更新财务数据
export const updateFinanceData = (financialId, data) => {
  return axios.put(`/finance/data/${financialId}`, data)
}

// 删除财务数据
export const deleteFinanceData = (financialId) => {
  return axios.delete(`/finance/data/${financialId}`)
}

// 获取财务报表
export const getFinanceReport = (reportType, params) => {
  return axios.get(`/finance/reports/${reportType}`, { params })
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

