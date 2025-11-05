import axios from './axios'

/**
 * 业务管理API
 */

// ============ 客户管理 ============

// 获取客户列表
export const getCustomers = (params) => {
  return axios.get('/business/customers', { params })
}

// 获取客户详情
export const getCustomerDetail = (id) => {
  return axios.get(`/business/customers/${id}`)
}

// 创建客户
export const createCustomer = (data) => {
  return axios.post('/business/customers', data)
}

// 更新客户
export const updateCustomer = (id, data) => {
  return axios.put(`/business/customers/${id}`, data)
}

// 删除客户
export const deleteCustomer = (id) => {
  return axios.delete(`/business/customers/${id}`)
}

// ============ 订单管理 ============

// 获取订单列表
export const getOrders = (params) => {
  return axios.get('/business/orders', { params })
}

// 获取订单详情
export const getOrderDetail = (id) => {
  return axios.get(`/business/orders/${id}`)
}

// 创建订单
export const createOrder = (data) => {
  return axios.post('/business/orders', data)
}

// 更新订单
export const updateOrder = (id, data) => {
  return axios.put(`/business/orders/${id}`, data)
}

// 删除订单
export const deleteOrder = (id) => {
  return axios.delete(`/business/orders/${id}`)
}

// ============ 项目管理 ============

// 获取项目列表
export const getProjects = (params) => {
  return axios.get('/business/projects', { params })
}

// 获取项目详情
export const getProjectDetail = (id) => {
  return axios.get(`/business/projects/${id}`)
}

// 创建项目
export const createProject = (data) => {
  return axios.post('/business/projects', data)
}

// 更新项目
export const updateProject = (id, data) => {
  return axios.put(`/business/projects/${id}`, data)
}

// 删除项目
export const deleteProject = (id) => {
  return axios.delete(`/business/projects/${id}`)
}

