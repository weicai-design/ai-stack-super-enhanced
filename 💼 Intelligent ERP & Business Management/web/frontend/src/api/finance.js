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

// 获取财务报表
export const getFinanceReport = (reportType, params) => {
  return axios.get(`/finance/reports/${reportType}`, { params })
}

