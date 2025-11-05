<template>
  <div class="procurement-suppliers">
    <div class="page-header">
      <h2>供应商管理</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        新增供应商
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
              <el-icon size="24"><OfficeBuilding /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">供应商总数</div>
              <div class="stat-value">{{ stats.totalSuppliers }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)">
              <el-icon size="24"><Star /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">A级供应商</div>
              <div class="stat-value">{{ stats.aLevelSuppliers }}</div>
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
              <div class="stat-label">采购总额</div>
              <div class="stat-value">¥{{ (stats.totalPurchase / 10000).toFixed(1) }}万</div>
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
              <div class="stat-label">准时交付率</div>
              <div class="stat-value">{{ (stats.onTimeRate * 100).toFixed(1) }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选条件 -->
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="供应商类别">
          <el-select v-model="filters.category" placeholder="全部" clearable>
            <el-option label="电子元器件" value="电子元器件" />
            <el-option label="原材料" value="原材料" />
            <el-option label="包装材料" value="包装材料" />
            <el-option label="辅料" value="辅料" />
          </el-select>
        </el-form-item>
        <el-form-item label="供应商等级">
          <el-select v-model="filters.level" placeholder="全部" clearable>
            <el-option label="A级" value="A" />
            <el-option label="B级" value="B" />
            <el-option label="C级" value="C" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable>
            <el-option label="活跃" value="active" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadSuppliers">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 供应商列表 -->
    <el-card class="table-card">
      <el-table :data="suppliers" v-loading="loading" style="width: 100%">
        <el-table-column prop="code" label="供应商编码" width="120" />
        <el-table-column prop="name" label="供应商名称" width="200" />
        <el-table-column prop="category" label="类别" width="120">
          <template #default="{ row }">
            <el-tag>{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="level" label="等级" width="80">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)">{{ row.level }}级</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="contact_person" label="联系人" width="100" />
        <el-table-column prop="phone" label="联系电话" width="130" />
        <el-table-column prop="total_purchase_amount" label="采购总额" width="120">
          <template #default="{ row }">
            ¥{{ (row.total_purchase_amount / 10000).toFixed(1) }}万
          </template>
        </el-table-column>
        <el-table-column prop="on_time_delivery_rate" label="准时率" width="100">
          <template #default="{ row }">
            <span :class="getRateClass(row.on_time_delivery_rate)">
              {{ (row.on_time_delivery_rate * 100).toFixed(1) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="quality_pass_rate" label="合格率" width="100">
          <template #default="{ row }">
            <span :class="getRateClass(row.quality_pass_rate)">
              {{ (row.quality_pass_rate * 100).toFixed(1) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '活跃' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetails(row)">详情</el-button>
            <el-button size="small" type="primary" @click="editSupplier(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteSupplier(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑供应商对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form :model="form" label-width="120px">
        <el-form-item label="供应商编码">
          <el-input v-model="form.code" placeholder="如：SUP001" />
        </el-form-item>
        <el-form-item label="供应商名称">
          <el-input v-model="form.name" placeholder="请输入供应商名称" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="form.category" placeholder="请选择类别">
            <el-option label="电子元器件" value="电子元器件" />
            <el-option label="原材料" value="原材料" />
            <el-option label="包装材料" value="包装材料" />
            <el-option label="辅料" value="辅料" />
          </el-select>
        </el-form-item>
        <el-form-item label="供应商等级">
          <el-select v-model="form.level" placeholder="请选择等级">
            <el-option label="A级" value="A" />
            <el-option label="B级" value="B" />
            <el-option label="C级" value="C" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact_person" placeholder="请输入联系人" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.phone" placeholder="请输入联系电话" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSupplier">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, OfficeBuilding, Star, Money, CircleCheck } from '@element-plus/icons-vue'
import procurementApi from '../../api/procurement'

const loading = ref(false)
const suppliers = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增供应商')
const currentId = ref(null)

const filters = ref({
  category: '',
  level: '',
  status: ''
})

const form = ref({
  code: '',
  name: '',
  category: '',
  level: 'B',
  contact_person: '',
  phone: ''
})

// 统计数据
const stats = computed(() => {
  const total = suppliers.value.length
  const aLevel = suppliers.value.filter(s => s.level === 'A').length
  const totalPurchase = suppliers.value.reduce((sum, s) => sum + s.total_purchase_amount, 0)
  const avgOnTime = suppliers.value.reduce((sum, s) => sum + s.on_time_delivery_rate, 0) / (total || 1)
  
  return {
    totalSuppliers: total,
    aLevelSuppliers: aLevel,
    totalPurchase: totalPurchase,
    onTimeRate: avgOnTime
  }
})

// 加载供应商列表
const loadSuppliers = async () => {
  loading.value = true
  try {
    const res = await procurementApi.getSuppliers(filters.value)
    if (res.success) {
      suppliers.value = res.suppliers
    }
  } catch (error) {
    ElMessage.error('加载失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 显示新增对话框
const showAddDialog = () => {
  dialogTitle.value = '新增供应商'
  currentId.value = null
  form.value = {
    code: '',
    name: '',
    category: '',
    level: 'B',
    contact_person: '',
    phone: ''
  }
  dialogVisible.value = true
}

// 编辑供应商
const editSupplier = (row) => {
  dialogTitle.value = '编辑供应商'
  currentId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

// 保存供应商
const saveSupplier = async () => {
  try {
    if (currentId.value) {
      await procurementApi.updateSupplier(currentId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await procurementApi.createSupplier(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadSuppliers()
  } catch (error) {
    ElMessage.error('保存失败：' + error.message)
  }
}

// 删除供应商
const deleteSupplier = (row) => {
  ElMessageBox.confirm(
    `确定要删除供应商"${row.name}"吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await procurementApi.deleteSupplier(row.id)
      ElMessage.success('删除成功')
      loadSuppliers()
    } catch (error) {
      ElMessage.error('删除失败：' + error.message)
    }
  }).catch(() => {})
}

// 查看详情
const viewDetails = (row) => {
  ElMessage.info(`查看供应商详情：${row.name}`)
}

// 重置筛选
const resetFilters = () => {
  filters.value = {
    category: '',
    level: '',
    status: ''
  }
  loadSuppliers()
}

// 等级标签类型
const getLevelType = (level) => {
  return level === 'A' ? 'danger' : level === 'B' ? 'warning' : 'info'
}

// 比率样式类
const getRateClass = (rate) => {
  return rate >= 0.95 ? 'rate-excellent' : rate >= 0.90 ? 'rate-good' : 'rate-normal'
}

onMounted(() => {
  loadSuppliers()
})
</script>

<style scoped>
.procurement-suppliers {
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

.filter-card {
  margin-bottom: 20px;
  border-radius: 12px;
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

.rate-normal {
  color: #f56c6c;
  font-weight: bold;
}
</style>

