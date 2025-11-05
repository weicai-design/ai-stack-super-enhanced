<template>
  <div class="purchase-orders">
    <div class="page-header">
      <h2>采购订单管理</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        新增采购订单
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
              <el-icon size="24"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">采购订单总数</div>
              <div class="stat-value">{{ stats.total }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)">
              <el-icon size="24"><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">待确认订单</div>
              <div class="stat-value">{{ stats.pending }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)">
              <el-icon size="24"><Van /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">运输中订单</div>
              <div class="stat-value">{{ stats.inTransit }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)">
              <el-icon size="24"><Money /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">本月采购额</div>
              <div class="stat-value">¥{{ (stats.monthlyAmount / 10000).toFixed(1) }}万</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 订单列表 -->
    <el-card class="table-card">
      <el-table :data="orders" v-loading="loading">
        <el-table-column prop="po_no" label="采购单号" width="150" />
        <el-table-column prop="supplier_name" label="供应商" width="180" />
        <el-table-column prop="order_date" label="下单日期" width="120" />
        <el-table-column prop="expected_delivery_date" label="预计交付" width="120" />
        <el-table-column prop="total_amount" label="订单金额" width="120">
          <template #default="{ row }">
            ¥{{ row.total_amount.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="paid_amount" label="已付款" width="120">
          <template #default="{ row }">
            ¥{{ row.paid_amount.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetails(row)">详情</el-button>
            <el-button size="small" type="primary" @click="editOrder(row)">编辑</el-button>
            <el-button size="small" type="success" @click="confirmReceipt(row)" v-if="row.status === 'in_transit'">
              确认收货
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form :model="form" label-width="120px">
        <el-form-item label="供应商">
          <el-select v-model="form.supplier_id" placeholder="请选择供应商" style="width: 100%">
            <el-option label="深圳电子科技" :value="1" />
            <el-option label="上海材料供应商" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="预计交付日期">
          <el-date-picker
            v-model="form.expected_delivery_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="订单金额">
          <el-input-number v-model="form.total_amount" :min="0" :step="1000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveOrder">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document, Clock, Van, Money } from '@element-plus/icons-vue'
import procurementApi from '../../api/procurement'

const loading = ref(false)
const orders = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增采购订单')
const currentId = ref(null)

const form = ref({
  supplier_id: null,
  expected_delivery_date: '',
  total_amount: 0,
  notes: ''
})

// 统计数据
const stats = computed(() => {
  const total = orders.value.length
  const pending = orders.value.filter(o => o.status === 'confirmed').length
  const inTransit = orders.value.filter(o => o.status === 'in_transit').length
  const monthlyAmount = orders.value.reduce((sum, o) => sum + o.total_amount, 0)
  
  return {
    total,
    pending,
    inTransit,
    monthlyAmount
  }
})

// 加载订单列表
const loadOrders = async () => {
  loading.value = true
  try {
    const res = await procurementApi.getPurchaseOrders()
    if (res.success) {
      orders.value = res.orders
    }
  } catch (error) {
    ElMessage.error('加载失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 显示新增对话框
const showAddDialog = () => {
  dialogTitle.value = '新增采购订单'
  currentId.value = null
  form.value = {
    supplier_id: null,
    expected_delivery_date: '',
    total_amount: 0,
    notes: ''
  }
  dialogVisible.value = true
}

// 编辑订单
const editOrder = (row) => {
  dialogTitle.value = '编辑采购订单'
  currentId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

// 保存订单
const saveOrder = async () => {
  try {
    await procurementApi.createPurchaseOrder(form.value)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadOrders()
  } catch (error) {
    ElMessage.error('保存失败：' + error.message)
  }
}

// 确认收货
const confirmReceipt = (row) => {
  ElMessageBox.confirm(
    `确认收货采购单"${row.po_no}"吗？`,
    '确认收货',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'success',
    }
  ).then(() => {
    ElMessage.success('收货确认成功')
    loadOrders()
  }).catch(() => {})
}

// 查看详情
const viewDetails = (row) => {
  ElMessage.info(`查看订单详情：${row.po_no}`)
}

// 状态类型
const getStatusType = (status) => {
  const types = {
    'confirmed': 'warning',
    'in_transit': 'primary',
    'received': 'success',
    'cancelled': 'info'
  }
  return types[status] || 'info'
}

// 状态文本
const getStatusText = (status) => {
  const texts = {
    'confirmed': '已确认',
    'in_transit': '运输中',
    'received': '已收货',
    'cancelled': '已取消'
  }
  return texts[status] || status
}

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.purchase-orders {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
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

.table-card {
  border-radius: 12px;
}
</style>

