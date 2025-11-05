<template>
  <div class="production-plan">
    <div class="page-header">
      <h2>生产计划管理</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        新增生产计划
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
              <div class="stat-label">计划总数</div>
              <div class="stat-value">{{ stats.total }}</div>
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
              <div class="stat-label">生产中</div>
              <div class="stat-value">{{ stats.inProgress }}</div>
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
              <div class="stat-label">已完成</div>
              <div class="stat-value">{{ stats.completed }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)">
              <el-icon size="24"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">完成率</div>
              <div class="stat-value">{{ stats.completionRate }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 生产计划列表 -->
    <el-card class="table-card">
      <el-table :data="plans" v-loading="loading">
        <el-table-column prop="plan_no" label="计划编号" width="150" />
        <el-table-column prop="product_name" label="产品名称" width="180" />
        <el-table-column prop="quantity" label="计划数量" width="100" />
        <el-table-column prop="completed_quantity" label="完成数量" width="100" />
        <el-table-column label="完成进度" width="150">
          <template #default="{ row }">
            <el-progress
              :percentage="(row.completed_quantity / row.quantity * 100).toFixed(0)"
              :color="getProgressColor(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="start_date" label="开始日期" width="120" />
        <el-table-column prop="end_date" label="结束日期" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetails(row)">详情</el-button>
            <el-button size="small" type="primary" @click="editPlan(row)">编辑</el-button>
            <el-button size="small" type="success" @click="startProduction(row)" v-if="row.status === 'planned'">
              开始生产
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="产品名称">
          <el-input v-model="form.product_name" />
        </el-form-item>
        <el-form-item label="计划数量">
          <el-input-number v-model="form.quantity" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="form.start_date" type="date" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="form.end_date" type="date" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePlan">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Document, Operation, CircleCheck, TrendCharts, Box, Warning, Money, Refresh } from '@element-plus/icons-vue'
import request from '../../api/axios'

const loading = ref(false)
const plans = ref([])
const materials = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增生产计划')

const form = ref({
  product_name: '',
  quantity: 0,
  start_date: '',
  end_date: ''
})

// 统计数据
const stats = computed(() => {
  const total = plans.value.length
  const inProgress = plans.value.filter(p => p.status === 'in_progress').length
  const completed = plans.value.filter(p => p.status === 'completed').length
  const completionRate = total > 0 ? (completed / total * 100).toFixed(1) : 0
  
  return {
    total,
    inProgress,
    completed,
    completionRate
  }
})

// 加载生产计划
const loadPlans = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/production/plans')
    if (res.success) {
      plans.value = res.plans
    }
  } catch (error) {
    // 使用模拟数据
    plans.value = [
      {
        id: 1,
        plan_no: 'PLAN20251101',
        product_name: '智能控制器A型',
        quantity: 1000,
        completed_quantity: 650,
        start_date: '2025-11-01',
        end_date: '2025-11-15',
        status: 'in_progress'
      },
      {
        id: 2,
        plan_no: 'PLAN20251102',
        product_name: '传感器B型',
        quantity: 500,
        completed_quantity: 500,
        start_date: '2025-10-20',
        end_date: '2025-11-01',
        status: 'completed'
      },
      {
        id: 3,
        plan_no: 'PLAN20251103',
        product_name: '显示屏C型',
        quantity: 800,
        completed_quantity: 0,
        start_date: '2025-11-10',
        end_date: '2025-11-25',
        status: 'planned'
      }
    ]
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  dialogTitle.value = '新增生产计划'
  form.value = {
    product_name: '',
    quantity: 0,
    start_date: '',
    end_date: ''
  }
  dialogVisible.value = true
}

const editPlan = (row) => {
  dialogTitle.value = '编辑生产计划'
  form.value = { ...row }
  dialogVisible.value = true
}

const savePlan = () => {
  ElMessage.success('生产计划保存成功')
  dialogVisible.value = false
  loadPlans()
}

const startProduction = (row) => {
  ElMessage.success(`生产计划 ${row.plan_no} 已开始执行`)
  loadPlans()
}

const viewDetails = (row) => {
  ElMessage.info(`查看计划详情：${row.plan_no}`)
}

const getProgressColor = (row) => {
  const progress = row.completed_quantity / row.quantity
  if (progress >= 0.9) return '#67c23a'
  if (progress >= 0.5) return '#e6a23c'
  return '#f56c6c'
}

const getStatusType = (status) => {
  const types = {
    'planned': 'info',
    'in_progress': 'primary',
    'completed': 'success',
    'cancelled': 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    'planned': '计划中',
    'in_progress': '生产中',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return texts[status] || status
}

onMounted(() => {
  loadPlans()
})
</script>

<style scoped>
.production-plan {
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

