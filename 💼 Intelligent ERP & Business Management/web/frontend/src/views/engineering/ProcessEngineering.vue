<template>
  <div class="process-engineering">
    <div class="page-header">
      <h2>工艺管理</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        新增工艺路线
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
              <el-icon size="24"><Connection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">工艺路线数</div>
              <div class="stat-value">{{ stats.totalRoutes }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)">
              <el-icon size="24"><Operation /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">工序总数</div>
              <div class="stat-value">{{ stats.totalOperations }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)">
              <el-icon size="24"><DocumentCopy /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">标准工艺</div>
              <div class="stat-value">{{ stats.standardRoutes }}</div>
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
              <div class="stat-label">平均工时</div>
              <div class="stat-value">{{ stats.avgHours }}h</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 工艺路线列表 -->
    <el-card class="table-card">
      <el-table :data="routes" v-loading="loading">
        <el-table-column prop="route_code" label="工艺编码" width="120" />
        <el-table-column prop="product_name" label="产品名称" width="180" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="operation_count" label="工序数" width="80" />
        <el-table-column prop="total_hours" label="总工时" width="100">
          <template #default="{ row }">
            {{ row.total_hours }}小时
          </template>
        </el-table-column>
        <el-table-column prop="difficulty" label="难度" width="100">
          <template #default="{ row }">
            <el-tag :type="getDifficultyType(row.difficulty)">
              {{ getDifficultyText(row.difficulty) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_date" label="创建日期" width="120" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewRouteDetails(row)">查看工序</el-button>
            <el-button size="small" type="primary" @click="editRoute(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 工序详情卡片 -->
    <el-card class="table-card mt-20" v-if="selectedRoute">
      <template #header>
        <div class="card-header">
          <span>工序详情 - {{ selectedRoute.product_name }}</span>
        </div>
      </template>
      <div class="operations-timeline">
        <el-steps :active="operations.length" align-center>
          <el-step
            v-for="(op, index) in operations"
            :key="index"
            :title="`工序${index + 1}: ${op.name}`"
            :description="`${op.hours}小时 | ${op.equipment}`"
          />
        </el-steps>
      </div>
    </el-card>

    <!-- 新增工艺路线对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="工艺编码">
          <el-input v-model="form.route_code" placeholder="如：PROC001" />
        </el-form-item>
        <el-form-item label="产品名称">
          <el-input v-model="form.product_name" />
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="form.version" placeholder="如：v1.0" />
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="form.difficulty" style="width: 100%">
            <el-option label="简单" value="easy" />
            <el-option label="中等" value="medium" />
            <el-option label="困难" value="hard" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRoute">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Connection, Operation, DocumentCopy, Clock, Setting, CircleCheck, Tools, TrendCharts } from '@element-plus/icons-vue'
import request from '../../api/axios'

const loading = ref(false)
const routes = ref([])
const selectedRoute = ref(null)
const operations = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增工艺路线')

const form = ref({
  route_code: '',
  product_name: '',
  version: '',
  difficulty: ''
})

// 统计数据
const stats = computed(() => {
  const totalRoutes = routes.value.length
  const totalOps = routes.value.reduce((sum, r) => sum + r.operation_count, 0)
  const standardRoutes = routes.value.filter(r => r.status === 'active').length
  const avgHours = routes.value.reduce((sum, r) => sum + r.total_hours, 0) / (totalRoutes || 1)
  
  return {
    totalRoutes,
    totalOperations: totalOps,
    standardRoutes,
    avgHours: avgHours.toFixed(1)
  }
})

// 加载工艺路线
const loadRoutes = () => {
  routes.value = [
    {
      id: 1,
      route_code: 'PROC001',
      product_name: '智能控制器A型',
      version: 'v1.0',
      operation_count: 5,
      total_hours: 8.5,
      difficulty: 'medium',
      status: 'active',
      created_date: '2025-09-01'
    },
    {
      id: 2,
      route_code: 'PROC002',
      product_name: '传感器B型',
      version: 'v1.2',
      operation_count: 4,
      total_hours: 6.0,
      difficulty: 'easy',
      status: 'active',
      created_date: '2025-09-15'
    },
    {
      id: 3,
      route_code: 'PROC003',
      product_name: '显示屏C型',
      version: 'v2.0',
      operation_count: 7,
      total_hours: 12.5,
      difficulty: 'hard',
      status: 'active',
      created_date: '2025-10-01'
    }
  ]
  
  operations.value = [
    { name: 'PCB准备', hours: 1.0, equipment: 'SMT贴片机' },
    { name: '元件贴装', hours: 2.5, equipment: 'SMT贴片机' },
    { name: '回流焊接', hours: 1.5, equipment: '回流焊接炉' },
    { name: '光学检测', hours: 2.0, equipment: 'AOI检测仪' },
    { name: '功能测试', hours: 1.5, equipment: '测试设备' }
  ]
}

const showAddDialog = () => {
  dialogTitle.value = '新增工艺路线'
  form.value = {
    route_code: '',
    product_name: '',
    version: '',
    difficulty: ''
  }
  dialogVisible.value = true
}

const editRoute = (row) => {
  dialogTitle.value = '编辑工艺路线'
  form.value = { ...row }
  dialogVisible.value = true
}

const saveRoute = () => {
  ElMessage.success('工艺路线保存成功')
  dialogVisible.value = false
  loadRoutes()
}

const viewRouteDetails = (row) => {
  selectedRoute.value = row
  ElMessage.success(`查看工艺详情：${row.product_name}`)
}

const getDifficultyType = (difficulty) => {
  const types = {
    'easy': 'success',
    'medium': 'warning',
    'hard': 'danger'
  }
  return types[difficulty] || 'info'
}

const getDifficultyText = (difficulty) => {
  const texts = {
    'easy': '简单',
    'medium': '中等',
    'hard': '困难'
  }
  return texts[difficulty] || difficulty
}

onMounted(() => {
  loadRoutes()
})
</script>

<style scoped>
.process-engineering {
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

.operations-timeline {
  padding: 20px;
}
</style>

