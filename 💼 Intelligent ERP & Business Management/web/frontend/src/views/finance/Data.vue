<template>
  <div class="finance-data">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>财务数据管理</span>
          <el-button type="primary" :icon="Plus" @click="showAddDialog">
            新增数据
          </el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="类别">
          <el-select v-model="filters.category" clearable placeholder="选择类别">
            <el-option label="收入" value="revenue" />
            <el-option label="支出" value="expense" />
            <el-option label="资产" value="asset" />
            <el-option label="负债" value="liability" />
            <el-option label="利润" value="profit" />
            <el-option label="投入" value="investment" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="filters.startDate"
            type="date"
            placeholder="选择日期"
          />
        </el-form-item>
        
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="filters.endDate"
            type="date"
            placeholder="选择日期"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadData">
            查询
          </el-button>
          <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table
        :data="tableData"
        stripe
        v-loading="loading"
        style="width: 100%"
      >
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="category" label="类别" width="100">
          <template #default="scope">
            <el-tag :type="getCategoryType(scope.row.category)">
              {{ getCategoryLabel(scope.row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="subcategory" label="子类别" width="120" />
        <el-table-column label="金额" width="150">
          <template #default="scope">
            <span class="amount">¥ {{ formatNumber(scope.row.amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="source_document" label="来源单据" width="120" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(scope.row)">
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

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    >
      <el-form :model="formData" label-width="100px">
        <el-form-item label="日期" required>
          <el-date-picker
            v-model="formData.date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="类别" required>
          <el-select v-model="formData.category" placeholder="选择类别" style="width: 100%">
            <el-option label="收入" value="revenue" />
            <el-option label="支出" value="expense" />
            <el-option label="资产" value="asset" />
            <el-option label="负债" value="liability" />
            <el-option label="利润" value="profit" />
            <el-option label="投入" value="investment" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="子类别">
          <el-input v-model="formData.subcategory" placeholder="输入子类别" />
        </el-form-item>
        
        <el-form-item label="金额" required>
          <el-input-number
            v-model="formData.amount"
            :precision="2"
            :step="100"
            :min="0"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="输入描述"
          />
        </el-form-item>
        
        <el-form-item label="来源单据">
          <el-input v-model="formData.source_document" placeholder="输入来源单据编号" />
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
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getFinanceData, createFinanceData, updateFinanceData, deleteFinanceData } from '@/api/finance'

const filters = reactive({
  category: '',
  startDate: null,
  endDate: null
})

const tableData = ref([])
const loading = ref(false)

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const dialogVisible = ref(false)
const dialogTitle = ref('新增财务数据')
const formData = reactive({
  date: null,
  category: '',
  subcategory: '',
  amount: 0,
  description: '',
  source_document: ''
})

const categoryLabels = {
  revenue: '收入',
  expense: '支出',
  asset: '资产',
  liability: '负债',
  profit: '利润',
  investment: '投入'
}

const categoryTypes = {
  revenue: 'success',
  expense: 'danger',
  asset: 'primary',
  liability: 'warning',
  profit: 'info',
  investment: ''
}

const formatNumber = (num) => {
  if (!num && num !== 0) return '0.00'
  return Number(num).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const getCategoryLabel = (category) => {
  return categoryLabels[category] || category
}

const getCategoryType = (category) => {
  return categoryTypes[category] || ''
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      limit: pagination.pageSize
    }
    
    if (filters.category) {
      params.category = filters.category
    }
    if (filters.startDate) {
      params.start_date = filters.startDate.toISOString().split('T')[0]
    }
    if (filters.endDate) {
      params.end_date = filters.endDate.toISOString().split('T')[0]
    }
    
    const data = await getFinanceData(params)
    tableData.value = data
    pagination.total = data.length
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.category = ''
  filters.startDate = null
  filters.endDate = null
  loadData()
}

const showAddDialog = () => {
  dialogTitle.value = '新增财务数据'
  Object.assign(formData, {
    date: new Date(),
    category: '',
    subcategory: '',
    amount: 0,
    description: '',
    source_document: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑财务数据'
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这条数据吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deleteFinanceData(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

const handleSubmit = async () => {
  try {
    const data = {
      date: formData.date.toISOString().split('T')[0],
      category: formData.category,
      subcategory: formData.subcategory,
      amount: formData.amount,
      description: formData.description,
      source_document: formData.source_document
    }
    
    if (formData.id) {
      // 更新
      await updateFinanceData(formData.id, data)
      ElMessage.success('更新成功')
    } else {
      // 创建
      await createFinanceData(data)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadData()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.finance-data {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-form {
  margin-bottom: 20px;
}

.amount {
  font-weight: 500;
  color: #303133;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>

