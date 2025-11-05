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

