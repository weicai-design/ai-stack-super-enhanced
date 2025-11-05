<template>
  <div class="equipment-management">
    <div class="page-header">
      <h2>设备管理</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        新增设备
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
              <el-icon size="24"><Setting /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">设备总数</div>
              <div class="stat-value">{{ stats.total }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)">
              <el-icon size="24"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">运行中设备</div>
              <div class="stat-value">{{ stats.running }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)">
              <el-icon size="24"><Tools /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">维护中设备</div>
              <div class="stat-value">{{ stats.maintenance }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)">
              <el-icon size="24"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">设备完好率</div>
              <div class="stat-value">{{ stats.healthRate }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 设备列表 -->
    <el-card class="table-card">
      <el-table :data="equipment" v-loading="loading">
        <el-table-column prop="code" label="设备编码" width="120" />
        <el-table-column prop="name" label="设备名称" width="180" />
        <el-table-column prop="category" label="设备类别" width="120">
          <template #default="{ row }">
            <el-tag>{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model" label="型号" width="150" />
        <el-table-column prop="location" label="位置" width="120" />
        <el-table-column prop="purchase_date" label="购置日期" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="health_score" label="健康度" width="100">
          <template #default="{ row }">
            <el-progress
              :percentage="row.health_score"
              :color="getHealthColor(row.health_score)"
              :stroke-width="12"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetails(row)">详情</el-button>
            <el-button size="small" type="primary" @click="editEquipment(row)">编辑</el-button>
            <el-button size="small" type="warning" @click="scheduleMaintenance(row)">
              维护
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 维护记录 -->
    <el-card class="table-card mt-20">
      <template #header>
        <div class="card-header">
          <span>维护记录</span>
        </div>
      </template>
      <el-table :data="maintenanceRecords" max-height="300">
        <el-table-column prop="equipment_name" label="设备名称" width="180" />
        <el-table-column prop="maintenance_type" label="维护类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.maintenance_type === 'preventive' ? 'success' : 'warning'">
              {{ row.maintenance_type === 'preventive' ? '预防性' : '故障维修' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="technician" label="技术员" width="100" />
        <el-table-column prop="maintenance_date" label="维护日期" width="150" />
        <el-table-column prop="cost" label="费用" width="100">
          <template #default="{ row }">
            ¥{{ row.cost.toLocaleString() }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增设备对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="设备编码">
          <el-input v-model="form.code" placeholder="如：EQ001" />
        </el-form-item>
        <el-form-item label="设备名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="设备类别">
          <el-select v-model="form.category" style="width: 100%">
            <el-option label="生产设备" value="生产设备" />
            <el-option label="检测设备" value="检测设备" />
            <el-option label="辅助设备" value="辅助设备" />
          </el-select>
        </el-form-item>
        <el-form-item label="型号">
          <el-input v-model="form.model" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="form.location" placeholder="如：A车间-01" />
        </el-form-item>
        <el-form-item label="购置日期">
          <el-date-picker v-model="form.purchase_date" type="date" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEquipment">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Setting, CircleCheck, Tools, TrendCharts } from '@element-plus/icons-vue'
import request from '../../api/axios'

const loading = ref(false)
const equipment = ref([])
const maintenanceRecords = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增设备')

const form = ref({
  code: '',
  name: '',
  category: '',
  model: '',
  location: '',
  purchase_date: ''
})

// 统计数据
const stats = computed(() => {
  const total = equipment.value.length
  const running = equipment.value.filter(e => e.status === 'running').length
  const maintenance = equipment.value.filter(e => e.status === 'maintenance').length
  const avgHealth = equipment.value.reduce((sum, e) => sum + e.health_score, 0) / (total || 1)
  
  return {
    total,
    running,
    maintenance,
    healthRate: avgHealth.toFixed(1)
  }
})

// 加载设备列表
const loadEquipment = () => {
  equipment.value = [
    {
      id: 1,
      code: 'EQ001',
      name: 'SMT贴片机',
      category: '生产设备',
      model: 'SMT-2000',
      location: 'A车间-01',
      purchase_date: '2023-05-15',
      status: 'running',
      health_score: 95
    },
    {
      id: 2,
      code: 'EQ002',
      name: '回流焊接炉',
      category: '生产设备',
      model: 'RF-3000',
      location: 'A车间-02',
      purchase_date: '2023-06-20',
      status: 'running',
      health_score: 92
    },
    {
      id: 3,
      code: 'EQ003',
      name: 'AOI光学检测仪',
      category: '检测设备',
      model: 'AOI-500',
      location: 'B车间-01',
      purchase_date: '2023-08-10',
      status: 'maintenance',
      health_score: 75
    },
    {
      id: 4,
      code: 'EQ004',
      name: '激光打标机',
      category: '辅助设备',
      model: 'LM-100',
      location: 'C车间-01',
      purchase_date: '2024-01-15',
      status: 'running',
      health_score: 98
    }
  ]
  
  maintenanceRecords.value = [
    {
      id: 1,
      equipment_name: 'SMT贴片机',
      maintenance_type: 'preventive',
      description: '定期保养，更换润滑油',
      technician: '王师傅',
      maintenance_date: '2025-11-01 14:30',
      cost: 500
    },
    {
      id: 2,
      equipment_name: 'AOI光学检测仪',
      maintenance_type: 'corrective',
      description: '镜头清洁，校准',
      technician: '李技师',
      maintenance_date: '2025-11-03 10:00',
      cost: 800
    }
  ]
}

const showAddDialog = () => {
  dialogTitle.value = '新增设备'
  form.value = {
    code: '',
    name: '',
    category: '',
    model: '',
    location: '',
    purchase_date: ''
  }
  dialogVisible.value = true
}

const editEquipment = (row) => {
  dialogTitle.value = '编辑设备'
  form.value = { ...row }
  dialogVisible.value = true
}

const saveEquipment = () => {
  ElMessage.success('设备保存成功')
  dialogVisible.value = false
  loadEquipment()
}

const scheduleMaintenance = (row) => {
  ElMessage.success(`已为设备 ${row.name} 安排维护`)
}

const viewDetails = (row) => {
  ElMessage.info(`查看设备详情：${row.name}`)
}

const getStatusType = (status) => {
  const types = {
    'running': 'success',
    'maintenance': 'warning',
    'stopped': 'danger',
    'idle': 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    'running': '运行中',
    'maintenance': '维护中',
    'stopped': '已停机',
    'idle': '闲置'
  }
  return texts[status] || status
}

const getHealthColor = (score) => {
  if (score >= 90) return '#67c23a'
  if (score >= 75) return '#e6a23c'
  return '#f56c6c'
}

onMounted(() => {
  loadEquipment()
})
</script>

<style scoped>
.equipment-management {
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

.mt-20 {
  margin-top: 20px;
}

.card-header {
  font-weight: bold;
}
</style>

