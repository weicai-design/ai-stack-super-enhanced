import request from './axios'

export default {
  // 获取供应商列表
  getSuppliers(params) {
    return request.get('/api/procurement/suppliers', { params })
  },

  // 创建供应商
  createSupplier(data) {
    return request.post('/api/procurement/suppliers', data)
  },

  // 更新供应商
  updateSupplier(id, data) {
    return request.put(`/api/procurement/suppliers/${id}`, data)
  },

  // 删除供应商
  deleteSupplier(id) {
    return request.delete(`/api/procurement/suppliers/${id}`)
  },

  // 获取采购订单列表
  getPurchaseOrders(params) {
    return request.get('/api/procurement/purchase-orders', { params })
  },

  // 创建采购订单
  createPurchaseOrder(data) {
    return request.post('/api/procurement/purchase-orders', data)
  },

  // 获取采购统计
  getProcurementStats(params) {
    return request.get('/api/procurement/stats', { params })
  },
}

