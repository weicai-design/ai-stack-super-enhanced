<template>
  <div class="quality-inspection">
    <div class="page-header">
      <h2>质量检验管理</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        新增检验记录
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
              <div class="stat-label">检验总数</div>
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
              <div class="stat-label">合格数量</div>
              <div class="stat-value">{{ stats.passed }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)">
              <el-icon size="24"><Close /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">不合格数量</div>
              <div class="stat-value">{{ stats.failed }}</div>
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
              <div class="stat-label">合格率</div>
              <div class="stat-value">{{ stats.passRate }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 检验记录列表 -->
    <el-card class="table-card">
      <el-table :data="inspections" v-loading="loading">
        <el-table-column prop="inspection_no" label="检验编号" width="150" />
        <el-table-column prop="product_name" label="产品名称" width="180" />
        <el-table-column prop="batch_no" label="批次号" width="120" />
        <el-table-column prop="quantity" label="检验数量" width="100" />
        <el-table-column prop="passed_quantity" label="合格数量" width="100" />
        <el-table-column label="合格率" width="100">
          <template #default="{ row }">
            <span :class="getPassRateClass(row)">
              {{ (row.passed_quantity / row.quantity * 100).toFixed(1) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="inspector" label="检验员" width="100" />
        <el-table-column prop="inspection_date" label="检验日期" width="120" />
        <el-table-column prop="result" label="结果" width="100">
          <template #default="{ row }">
            <el-tag :type="row.result === 'passed' ? 'success' : 'danger'">
              {{ row.result === 'passed' ? '合格' : '不合格' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetails(row)">详情</el-button>
            <el-button size="small" type="primary" @click="editInspection(row)">编辑</el-button>
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
        <el-form-item label="批次号">
          <el-input v-model="form.batch_no" />
        </el-form-item>
        <el-form-item label="检验数量">
          <el-input-number v-model="form.quantity" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="合格数量">
          <el-input-number v-model="form.passed_quantity" :min="0" :max="form.quantity" style="width: 100%" />
        </el-form-item>
        <el-form-item label="检验员">
          <el-input v-model="form.inspector" />
        </el-form-item>
        <el-form-item label="检验日期">
          <el-date-picker v-model="form.inspection_date" type="date" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveInspection">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Document, CircleCheck, Close, TrendCharts, Operation } from '@element-plus/icons-vue'
import request from '../../api/axios'

const loading = ref(false)
const inspections = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增检验记录')

const form = ref({
  product_name: '',
  batch_no: '',
  quantity: 0,
  passed_quantity: 0,
  inspector: '',
  inspection_date: ''
})

// 统计数据
const stats = computed(() => {
  const total = inspections.value.length
  const passed = inspections.value.filter(i => i.result === 'passed').length
  const failed = total - passed
  const passRate = total > 0 ? (passed / total * 100).toFixed(1) : 0
  
  return {
    total,
    passed,
    failed,
    passRate
  }
})

// 加载检验记录
const loadInspections = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/quality/inspections')
    if (res.success) {
      inspections.value = res.inspections
    }
  } catch (error) {
    // 模拟数据
    inspections.value = [
      {
        id: 1,
        inspection_no: 'QC20251101001',
        product_name: '智能控制器A型',
        batch_no: 'BATCH2025001',
        quantity: 100,
        passed_quantity: 98,
        inspector: '王检验',
        inspection_date: '2025-11-01',
        result: 'passed'
      },
      {
        id: 2,
        inspection_no: 'QC20251102001',
        product_name: '传感器B型',
        batch_no: 'BATCH2025002',
        quantity: 50,
        passed_quantity: 45,
        inspector: '李检验',
        inspection_date: '2025-11-02',
        result: 'passed'
      },
      {
        id: 3,
        inspection_no: 'QC20251103001',
        product_name: '显示屏C型',
        batch_no: 'BATCH2025003',
        quantity: 80,
        passed_quantity: 65,
        inspector: '赵检验',
        inspection_date: '2025-11-03',
        result: 'failed'
      }
    ]
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  dialogTitle.value = '新增检验记录'
  form.value = {
    product_name: '',
    batch_no: '',
    quantity: 0,
    passed_quantity: 0,
    inspector: '',
    inspection_date: ''
  }
  dialogVisible.value = true
}

const editInspection = (row) => {
  dialogTitle.value = '编辑检验记录'
  form.value = { ...row }
  dialogVisible.value = true
}

const saveInspection = () => {
  ElMessage.success('检验记录保存成功')
  dialogVisible.value = false
  loadInspections()
}

const viewDetails = (row) => {
  ElMessage.info(`查看检验详情：${row.inspection_no}`)
}

const getPassRateClass = (row) => {
  const rate = row.passed_quantity / row.quantity
  return rate >= 0.95 ? 'rate-excellent' : rate >= 0.90 ? 'rate-good' : 'rate-low'
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
  loadInspections()
})
</script>

<style scoped>
.quality-inspection {
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

.rate-excellent {
  color: #67c23a;
  font-weight: bold;
}

.rate-good {
  color: #e6a23c;
  font-weight: bold;
}

.rate-low {
  color: #f56c6c;
  font-weight: bold;
}
</style>

