<template>
  <div class="warehouse-management">
    <div class="page-header">
      <h2>仓储管理</h2>
      <el-button-group>
        <el-button type="primary" @click="showInboundDialog">
          <el-icon><Bottom /></el-icon>
          入库
        </el-button>
        <el-button type="success" @click="showOutboundDialog">
          <el-icon><Top /></el-icon>
          出库
        </el-button>
      </el-button-group>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
              <el-icon size="24"><HomeFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">仓库数量</div>
              <div class="stat-value">{{ stats.warehouseCount }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)">
              <el-icon size="24"><Box /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">在库物料</div>
              <div class="stat-value">{{ stats.materialCount }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)">
              <el-icon size="24"><Bottom /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">本月入库</div>
              <div class="stat-value">{{ stats.monthlyInbound }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)">
              <el-icon size="24"><Top /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">本月出库</div>
              <div class="stat-value">{{ stats.monthlyOutbound }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 库存记录列表 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>库存记录</span>
          <el-radio-group v-model="viewMode" size="small">
            <el-radio-button label="stock">库存视图</el-radio-button>
            <el-radio-button label="transaction">交易记录</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <!-- 库存视图 -->
      <el-table v-if="viewMode === 'stock'" :data="stockRecords" v-loading="loading">
        <el-table-column prop="material_code" label="物料编码" width="120" />
        <el-table-column prop="material_name" label="物料名称" width="180" />
        <el-table-column prop="warehouse_name" label="仓库" width="120" />
        <el-table-column prop="location" label="库位" width="100" />
        <el-table-column prop="quantity" label="数量" width="100" />
        <el-table-column prop="unit" label="单位" width="80" />
        <el-table-column label="库存状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStockStatusType(row)">
              {{ getStockStatusText(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_update" label="最后更新" width="150" />
      </el-table>

      <!-- 交易记录视图 -->
      <el-table v-else :data="transactions" v-loading="loading">
        <el-table-column prop="transaction_no" label="单号" width="150" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.type === 'inbound' ? 'success' : 'warning'">
              {{ row.type === 'inbound' ? '入库' : '出库' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="material_name" label="物料名称" width="180" />
        <el-table-column prop="quantity" label="数量" width="100" />
        <el-table-column prop="warehouse_name" label="仓库" width="120" />
        <el-table-column prop="operator" label="操作员" width="100" />
        <el-table-column prop="transaction_date" label="日期" width="150" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetails(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 入库对话框 -->
    <el-dialog v-model="inboundDialogVisible" title="物料入库" width="600px">
      <el-form :model="inboundForm" label-width="120px">
        <el-form-item label="物料">
          <el-select v-model="inboundForm.material_id" placeholder="请选择物料" style="width: 100%">
            <el-option label="PCB电路板" :value="1" />
            <el-option label="电阻" :value="2" />
            <el-option label="包装盒" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="入库数量">
          <el-input-number v-model="inboundForm.quantity" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="仓库">
          <el-select v-model="inboundForm.warehouse_id" style="width: 100%">
            <el-option label="原材料仓库" :value="1" />
            <el-option label="成品仓库" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="库位">
          <el-input v-model="inboundForm.location" placeholder="如：A01-B03" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="inboundDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmInbound">确认入库</el-button>
      </template>
    </el-dialog>

    <!-- 出库对话框 -->
    <el-dialog v-model="outboundDialogVisible" title="物料出库" width="600px">
      <el-form :model="outboundForm" label-width="120px">
        <el-form-item label="物料">
          <el-select v-model="outboundForm.material_id" placeholder="请选择物料" style="width: 100%">
            <el-option label="PCB电路板" :value="1" />
            <el-option label="电阻" :value="2" />
            <el-option label="包装盒" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="出库数量">
          <el-input-number v-model="outboundForm.quantity" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="用途">
          <el-select v-model="outboundForm.purpose" style="width: 100%">
            <el-option label="生产领用" value="production" />
            <el-option label="客户交付" value="delivery" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="outboundDialogVisible = false">取消</el-button>
        <el-button type="success" @click="confirmOutbound">确认出库</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Bottom, Top, HomeFilled, Box } from '@element-plus/icons-vue'
import request from '../../api/axios'

const loading = ref(false)
const viewMode = ref('stock')
const stockRecords = ref([])
const transactions = ref([])
const inboundDialogVisible = ref(false)
const outboundDialogVisible = ref(false)

const inboundForm = ref({
  material_id: null,
  quantity: 0,
  warehouse_id: null,
  location: ''
})

const outboundForm = ref({
  material_id: null,
  quantity: 0,
  purpose: ''
})

const stats = computed(() => {
  return {
    warehouseCount: 3,
    materialCount: stockRecords.value.length,
    monthlyInbound: 45,
    monthlyOutbound: 38
  }
})

// 加载库存记录
const loadStockRecords = () => {
  stockRecords.value = [
    {
      id: 1,
      material_code: 'MAT001',
      material_name: 'PCB电路板',
      warehouse_name: '原材料仓库',
      location: 'A01-B03',
      quantity: 500,
      unit: '片',
      min_stock: 200,
      last_update: '2025-11-04 14:30'
    },
    {
      id: 2,
      material_code: 'MAT002',
      material_name: '电阻',
      warehouse_name: '原材料仓库',
      location: 'A02-B05',
      quantity: 150,
      unit: '个',
      min_stock: 500,
      last_update: '2025-11-04 10:20'
    },
    {
      id: 3,
      material_code: 'MAT003',
      material_name: '包装盒',
      warehouse_name: '包材仓库',
      location: 'B01-C02',
      quantity: 800,
      unit: '个',
      min_stock: 300,
      last_update: '2025-11-03 16:45'
    }
  ]
  
  transactions.value = [
    {
      id: 1,
      transaction_no: 'IN20251104001',
      type: 'inbound',
      material_name: 'PCB电路板',
      quantity: 200,
      warehouse_name: '原材料仓库',
      operator: '张三',
      transaction_date: '2025-11-04 14:30'
    },
    {
      id: 2,
      transaction_no: 'OUT20251104001',
      type: 'outbound',
      material_name: '电阻',
      quantity: 350,
      warehouse_name: '原材料仓库',
      operator: '李四',
      transaction_date: '2025-11-04 10:20'
    }
  ]
}

const showInboundDialog = () => {
  inboundForm.value = {
    material_id: null,
    quantity: 0,
    warehouse_id: null,
    location: ''
  }
  inboundDialogVisible.value = true
}

const showOutboundDialog = () => {
  outboundForm.value = {
    material_id: null,
    quantity: 0,
    purpose: ''
  }
  outboundDialogVisible.value = true
}

const confirmInbound = () => {
  ElMessage.success('入库成功')
  inboundDialogVisible.value = false
  loadStockRecords()
}

const confirmOutbound = () => {
  ElMessage.success('出库成功')
  outboundDialogVisible.value = false
  loadStockRecords()
}

const viewDetails = (row) => {
  ElMessage.info(`查看详情`)
}

const getStockStatusType = (row) => {
  if (row.quantity < row.min_stock) {
    return 'danger'
  } else if (row.quantity < row.min_stock * 1.5) {
    return 'warning'
  } else {
    return 'success'
  }
}

const getStockStatusText = (row) => {
  if (row.quantity < row.min_stock) {
    return '库存不足'
  } else if (row.quantity < row.min_stock * 1.5) {
    return '库存预警'
  } else {
    return '库存充足'
  }
}

onMounted(() => {
  loadStockRecords()
})
</script>

<style scoped>
.warehouse-management {
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>

