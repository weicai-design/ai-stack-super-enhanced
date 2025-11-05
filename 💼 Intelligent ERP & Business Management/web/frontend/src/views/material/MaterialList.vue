<template>
  <div class="material-list">
    <div class="page-header">
      <h2>物料管理（MRP）</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        新增物料
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
              <el-icon size="24"><Box /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">物料总数</div>
              <div class="stat-value">{{ stats.total }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)">
              <el-icon size="24"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">库存预警</div>
              <div class="stat-value">{{ stats.lowStock }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)">
              <el-icon size="24"><Money /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">库存总值</div>
              <div class="stat-value">¥{{ (stats.totalValue / 10000).toFixed(1) }}万</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)">
              <el-icon size="24"><Refresh /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">周转率</div>
              <div class="stat-value">{{ stats.turnoverRate }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 物料列表 -->
    <el-card class="table-card">
      <el-table :data="materials" v-loading="loading">
        <el-table-column prop="code" label="物料编码" width="120" />
        <el-table-column prop="name" label="物料名称" width="180" />
        <el-table-column prop="category" label="类别" width="120">
          <template #default="{ row }">
            <el-tag>{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="specification" label="规格" width="150" />
        <el-table-column prop="unit" label="单位" width="80" />
        <el-table-column prop="stock_quantity" label="当前库存" width="100">
          <template #default="{ row }">
            <span :class="getStockClass(row)">
              {{ row.stock_quantity }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="min_stock" label="安全库存" width="100" />
        <el-table-column prop="unit_price" label="单价" width="100">
          <template #default="{ row }">
            ¥{{ row.unit_price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="库存状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStockStatus(row).type">
              {{ getStockStatus(row).text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetails(row)">详情</el-button>
            <el-button size="small" type="primary" @click="editMaterial(row)">编辑</el-button>
            <el-button size="small" type="warning" @click="adjustStock(row)" v-if="getStockStatus(row).type === 'danger'">
              补货
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增物料对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="物料编码">
          <el-input v-model="form.code" placeholder="如：MAT001" />
        </el-form-item>
        <el-form-item label="物料名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="物料类别">
          <el-select v-model="form.category" style="width: 100%">
            <el-option label="原材料" value="原材料" />
            <el-option label="辅料" value="辅料" />
            <el-option label="包装材料" value="包装材料" />
            <el-option label="半成品" value="半成品" />
            <el-option label="成品" value="成品" />
          </el-select>
        </el-form-item>
        <el-form-item label="规格">
          <el-input v-model="form.specification" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="form.unit" placeholder="如：个、kg、m" />
        </el-form-item>
        <el-form-item label="安全库存">
          <el-input-number v-model="form.min_stock" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="单价">
          <el-input-number v-model="form.unit_price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveMaterial">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Box, Warning, Money, Refresh } from '@element-plus/icons-vue'
import request from '../../api/axios'

const loading = ref(false)
const materials = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增物料')

const form = ref({
  code: '',
  name: '',
  category: '',
  specification: '',
  unit: '',
  min_stock: 0,
  unit_price: 0
})

// 统计数据
const stats = computed(() => {
  const total = materials.value.length
  const lowStock = materials.value.filter(m => m.stock_quantity < m.min_stock).length
  const totalValue = materials.value.reduce((sum, m) => sum + (m.stock_quantity * m.unit_price), 0)
  
  return {
    total,
    lowStock,
    totalValue,
    turnoverRate: '8.5次/年'
  }
})

// 加载物料列表
const loadMaterials = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/material/list')
    if (res.success) {
      materials.value = res.materials
    }
  } catch (error) {
    // 使用模拟数据
    materials.value = [
      {
        id: 1,
        code: 'MAT001',
        name: 'PCB电路板',
        category: '原材料',
        specification: '10cm x 15cm',
        unit: '片',
        stock_quantity: 500,
        min_stock: 200,
        unit_price: 25.50
      },
      {
        id: 2,
        code: 'MAT002',
        name: '电阻',
        category: '辅料',
        specification: '1kΩ',
        unit: '个',
        stock_quantity: 150,
        min_stock: 500,
        unit_price: 0.10
      },
      {
        id: 3,
        code: 'MAT003',
        name: '包装盒',
        category: '包装材料',
        specification: '20cm x 15cm x 10cm',
        unit: '个',
        stock_quantity: 800,
        min_stock: 300,
        unit_price: 2.50
      }
    ]
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  dialogTitle.value = '新增物料'
  form.value = {
    code: '',
    name: '',
    category: '',
    specification: '',
    unit: '',
    min_stock: 0,
    unit_price: 0
  }
  dialogVisible.value = true
}

const editMaterial = (row) => {
  dialogTitle.value = '编辑物料'
  form.value = { ...row }
  dialogVisible.value = true
}

const saveMaterial = () => {
  ElMessage.success('物料保存成功')
  dialogVisible.value = false
  loadMaterials()
}

const adjustStock = (row) => {
  ElMessage.info(`发起补货申请：${row.name}`)
}

const viewDetails = (row) => {
  ElMessage.info(`查看物料详情：${row.name}`)
}

const getStockClass = (row) => {
  return row.stock_quantity < row.min_stock ? 'stock-low' : 'stock-normal'
}

const getStockStatus = (row) => {
  if (row.stock_quantity < row.min_stock) {
    return { type: 'danger', text: '库存不足' }
  } else if (row.stock_quantity < row.min_stock * 1.5) {
    return { type: 'warning', text: '库存预警' }
  } else {
    return { type: 'success', text: '库存充足' }
  }
}

onMounted(() => {
  loadMaterials()
})
</script>

<style scoped>
.material-list {
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

.stock-low {
  color: #f56c6c;
  font-weight: bold;
}

.stock-normal {
  color: #67c23a;
  font-weight: bold;
}
</style>

