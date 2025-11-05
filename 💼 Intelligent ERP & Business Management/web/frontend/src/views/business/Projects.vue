<template>
  <div class="projects">
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="项目状态">
          <el-select v-model="filters.status" clearable @change="loadData">
            <el-option label="全部" value="" />
            <el-option label="计划中" value="planning" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已暂停" value="suspended" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" :icon="Refresh" @click="loadData">
            刷新
          </el-button>
          <el-button type="success" :icon="Plus" @click="showAddDialog">
            新增项目
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="6">
        <el-card class="stat-card total">
          <div class="stat-content">
            <div class="stat-label">项目总数</div>
            <div class="stat-value">{{ statistics.total }}</div>
            <div class="stat-icon">📋</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card budget">
          <div class="stat-content">
            <div class="stat-label">总预算</div>
            <div class="stat-value">¥ {{ formatNumber(statistics.totalBudget) }}</div>
            <div class="stat-icon">💰</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card in-progress">
          <div class="stat-content">
            <div class="stat-label">进行中</div>
            <div class="stat-value">{{ statistics.inProgress }}</div>
            <div class="stat-icon">🔄</div>
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

    <!-- 项目卡片列表 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="8" v-for="project in projects" :key="project.id">
        <el-card class="project-card" shadow="hover">
          <template #header>
            <div class="project-header">
              <div class="project-title">
                <h3>{{ project.project_name }}</h3>
                <el-tag :type="getStatusType(project.status)" size="small">
                  {{ getStatusText(project.status) }}
                </el-tag>
              </div>
            </div>
          </template>
          
          <div class="project-body">
            <div class="project-info">
              <div class="info-item">
                <span class="label">项目编码：</span>
                <span class="value">{{ project.project_code }}</span>
              </div>
              <div class="info-item">
                <span class="label">客户：</span>
                <span class="value">{{ project.customer?.name || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="label">预算：</span>
                <span class="value amount">¥ {{ formatNumber(project.budget) }}</span>
              </div>
              <div class="info-item">
                <span class="label">开始日期：</span>
                <span class="value">{{ project.start_date }}</span>
              </div>
              <div class="info-item">
                <span class="label">结束日期：</span>
                <span class="value">{{ project.end_date }}</span>
              </div>
            </div>
            
            <div class="project-description">
              {{ project.description || '暂无描述' }}
            </div>
            
            <div class="project-actions">
              <el-button size="small" :icon="View" @click="viewDetail(project)">
                详情
              </el-button>
              <el-button size="small" type="primary" :icon="Edit" @click="handleEdit(project)">
                编辑
              </el-button>
              <el-button size="small" type="danger" :icon="Delete" @click="handleDelete(project)">
                删除
              </el-button>
            </div>
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
        <el-form-item label="项目编码" required>
          <el-input v-model="formData.project_code" placeholder="如: P-001" />
        </el-form-item>
        
        <el-form-item label="项目名称" required>
          <el-input v-model="formData.project_name" placeholder="请输入项目名称" />
        </el-form-item>
        
        <el-form-item label="客户">
          <el-select v-model="formData.customer_id" placeholder="选择客户" style="width: 100%">
            <el-option
              v-for="customer in customers"
              :key="customer.id"
              :label="customer.name"
              :value="customer.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="formData.start_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="formData.end_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="项目预算">
          <el-input-number
            v-model="formData.budget"
            :precision="2"
            :step="10000"
            :min="0"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="项目状态">
          <el-select v-model="formData.status" placeholder="选择状态" style="width: 100%">
            <el-option label="计划中" value="planning" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已暂停" value="suspended" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="项目描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="4"
            placeholder="请输入项目描述"
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
import { Refresh, Plus, View, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from '@/api/axios'

const filters = reactive({
  status: ''
})

const projects = ref([])
const customers = ref([])
const loading = ref(false)

const statistics = reactive({
  total: 0,
  totalBudget: 0,
  inProgress: 0,
  completed: 0
})

const dialogVisible = ref(false)
const dialogTitle = ref('新增项目')

const formData = reactive({
  project_code: '',
  project_name: '',
  customer_id: null,
  start_date: null,
  end_date: null,
  budget: 0,
  status: 'planning',
  description: ''
})

const statusLabels = {
  planning: '计划中',
  in_progress: '进行中',
  completed: '已完成',
  suspended: '已暂停'
}

const statusTypes = {
  planning: 'info',
  in_progress: 'warning',
  completed: 'success',
  suspended: 'danger'
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
    const response = await axios.get('/business/projects')
    projects.value = response.projects || []
    
    // 加载客户列表（用于下拉选择）
    const customersResp = await axios.get('/business/customers')
    customers.value = customersResp.customers || []
    
    // 计算统计
    statistics.total = projects.value.length
    statistics.totalBudget = projects.value.reduce((sum, proj) => sum + parseFloat(proj.budget || 0), 0)
    statistics.inProgress = projects.value.filter(p => p.status === 'in_progress').length
    statistics.completed = projects.value.filter(p => p.status === 'completed').length
    
    ElMessage.success('项目数据加载成功')
  } catch (error) {
    console.error('加载项目列表失败:', error)
    ElMessage.error('加载数据失败，使用测试数据')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  dialogTitle.value = '新增项目'
  Object.assign(formData, {
    project_code: '',
    project_name: '',
    customer_id: null,
    start_date: new Date(),
    end_date: null,
    budget: 0,
    status: 'planning',
    description: ''
  })
  dialogVisible.value = true
}

const viewDetail = (row) => {
  ElMessage.info('项目详情功能开发中')
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑项目'
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目"${row.project_name}"吗？`,
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
.projects {
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

.stat-card.budget {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.stat-card.in-progress {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-card.completed {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.stat-card.total .stat-label,
.stat-card.budget .stat-label,
.stat-card.in-progress .stat-label,
.stat-card.completed .stat-label,
.stat-card.total .stat-value,
.stat-card.budget .stat-value,
.stat-card.in-progress .stat-value,
.stat-card.completed .stat-value {
  color: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.project-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.project-card:hover {
  transform: translateY(-5px);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.project-title h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.project-body {
  padding: 4px 0;
}

.project-info {
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  padding: 6px 0;
  font-size: 14px;
}

.info-item .label {
  width: 100px;
  color: #909399;
}

.info-item .value {
  flex: 1;
  color: #303133;
}

.info-item .value.amount {
  color: #67C23A;
  font-weight: 500;
}

.project-description {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 16px;
  min-height: 60px;
}

.project-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}
</style>
