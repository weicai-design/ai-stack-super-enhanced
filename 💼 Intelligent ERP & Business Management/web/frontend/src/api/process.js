import axios from './axios'

/**
 * 流程管理API
 */

// 获取流程列表
export const getProcessList = (params) => {
  return axios.get('/process/list', { params })
}

// 获取流程详情
export const getProcessDetail = (id) => {
  return axios.get(`/process/${id}`)
}

// 创建流程实例
export const createProcessInstance = (data) => {
  return axios.post('/process/instances', data)
}

// 获取流程跟踪
export const getProcessTracking = (instanceId) => {
  return axios.get(`/process/instances/${instanceId}/tracking`)
}

// 获取流程异常
export const getProcessExceptions = (params) => {
  return axios.get('/process/exceptions', { params })
}

// 获取改进计划
export const getImprovementPlans = (params) => {
  return axios.get('/process/improvements', { params })
}

