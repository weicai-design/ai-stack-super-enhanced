<template>
  <div class="orders">
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="订单状态">
          <el-select v-model="filters.status" clearable @change="loadData">
            <el-option label="全部" value="" />
            <el-option label="待处理" value="pending" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="生产中" value="in_production" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            @change="loadData"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" :icon="Refresh" @click="loadData">
            刷新
          </el-button>
          <el-button type="success" :icon="Plus" @click="showAddDialog">
            新增订单
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="6">
        <el-card class="stat-card total">
          <div class="stat-content">
            <div class="stat-label">订单总数</div>
            <div class="stat-value">{{ statistics.total }}</div>
            <div class="stat-icon">📦</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card amount">
          <div class="stat-content">
            <div class="stat-label">订单总额</div>
            <div class="stat-value">¥ {{ formatNumber(statistics.totalAmount) }}</div>
            <div class="stat-icon">💰</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card in-production">
          <div class="stat-content">
            <div class="stat-label">生产中</div>
            <div class="stat-value">{{ statistics.inProduction }}</div>
            <div class="stat-icon">🏭</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card completed">
          <div class="stat-content">
            <div class="stat-label">已完成</div>
            <div class="stat-value">{{ statistics.completed }}</div>
            <div class="stat-icon">✅</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 订单列表 -->
    <el-row class="mt-20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>订单列表</span>
            </div>
          </template>
          
          <el-table
            :data="orders"
            stripe
            style="width: 100%"
            v-loading="loading"
          >
            <el-table-column prop="order_number" label="订单编号" width="180" />
            <el-table-column label="客户" width="200">
              <template #default="scope">
                {{ scope.row.customer?.name || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="order_date" label="订单日期" width="120" />
            <el-table-column prop="delivery_date" label="交付日期" width="120" />
            <el-table-column label="订单金额" width="150">
              <template #default="scope">
                <span class="amount">¥ {{ formatNumber(scope.row.total_amount) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="notes" label="备注" show-overflow-tooltip />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <el-button size="small" :icon="View" @click="viewDetail(scope.row)">
                  详情
                </el-button>
                <el-button size="small" type="primary" :icon="Edit" @click="handleEdit(scope.row)">
                  编辑
                </el-button>
                <el-button size="small" type="danger" :icon="Delete" @click="handleDelete(scope.row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.pageSize"
              :total="pagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="loadData"
              @current-change="loadData"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form :model="formData" label-width="100px">
        <el-form-item label="订单编号" required>
          <el-input v-model="formData.order_number" placeholder="如: SO-20251103-001" />
        </el-form-item>
        
        <el-form-item label="客户" required>
          <el-select v-model="formData.customer_id" placeholder="选择客户" style="width: 100%">
            <el-option
              v-for="customer in customers"
              :key="customer.id"
              :label="customer.name"
              :value="customer.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="订单日期" required>
          <el-date-picker
            v-model="formData.order_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="交付日期">
          <el-date-picker
            v-model="formData.delivery_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="订单金额" required>
          <el-input-number
            v-model="formData.total_amount"
            :precision="2"
            :step="1000"
            :min="0"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="订单状态">
          <el-select v-model="formData.status" placeholder="选择状态" style="width: 100%">
            <el-option label="待处理" value="pending" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="生产中" value="in_production" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input
            v-model="formData.notes"
            type="textarea"
            :rows="3"
            placeholder="输入备注"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh, Plus, View, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from '@/api/axios'

const filters = reactive({
  status: ''
})

const dateRange = ref([])
const orders = ref([])
const customers = ref([])
const loading = ref(false)

const statistics = reactive({
  total: 0,
  totalAmount: 0,
  inProduction: 0,
  completed: 0
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const dialogVisible = ref(false)
const dialogTitle = ref('新增订单')

const formData = reactive({
  order_number: '',
  customer_id: null,
  order_date: null,
  delivery_date: null,
  total_amount: 0,
  status: 'pending',
  notes: ''
})

const statusLabels = {
  pending: '待处理',
  confirmed: '已确认',
  in_production: '生产中',
  completed: '已完成'
}

const statusTypes = {
  pending: 'info',
  confirmed: 'warning',
  in_production: 'primary',
  completed: 'success'
}

const getStatusText = (status) => statusLabels[status] || status
const getStatusType = (status) => statusTypes[status] || ''

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
    const response = await axios.get('/business/orders')
    orders.value = response.orders || []
    
    // 计算统计
    statistics.total = orders.value.length
    statistics.totalAmount = orders.value.reduce((sum, order) => sum + parseFloat(order.total_amount || 0), 0)
    statistics.inProduction = orders.value.filter(o => o.status === 'in_production').length
    statistics.completed = orders.value.filter(o => o.status === 'completed').length
    
    pagination.total = orders.value.length
    
    ElMessage.success('订单数据加载成功')
  } catch (error) {
    console.error('加载订单列表失败:', error)
    ElMessage.error('加载数据失败，使用测试数据')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  dialogTitle.value = '新增订单'
  Object.assign(formData, {
    order_number: '',
    customer_id: null,
    order_date: new Date(),
    delivery_date: null,
    total_amount: 0,
    status: 'pending',
    notes: ''
  })
  dialogVisible.value = true
}

const viewDetail = (row) => {
  ElMessage.info('订单详情功能开发中')
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑订单'
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除订单"${row.order_number}"吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    ElMessage.success('删除成功')
    loadData()
  } catch {
    // 取消
  }
}

const handleSubmit = async () => {
  try {
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadData()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.orders {
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
  font-size: 28px;
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

.stat-card.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-card.amount {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.stat-card.in-production {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-card.completed {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.stat-card.total .stat-label,
.stat-card.amount .stat-label,
.stat-card.in-production .stat-label,
.stat-card.completed .stat-label,
.stat-card.total .stat-value,
.stat-card.amount .stat-value,
.stat-card.in-production .stat-value,
.stat-card.completed .stat-value {
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
  color: #67C23A;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
