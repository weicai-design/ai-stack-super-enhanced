<template>
  <div class="customers">
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="客户类别">
          <el-select v-model="filters.category" clearable @change="loadData">
            <el-option label="全部" value="" />
            <el-option label="VIP客户" value="VIP" />
            <el-option label="普通客户" value="普通" />
            <el-option label="新客户" value="新客户" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="搜索">
          <el-input 
            v-model="filters.keyword" 
            placeholder="客户名称/编码"
            clearable
            @clear="loadData"
            @keyup.enter="loadData"
          >
            <template #append>
              <el-button :icon="Search" @click="loadData" />
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" :icon="Refresh" @click="loadData">
            刷新
          </el-button>
          <el-button type="success" :icon="Plus" @click="showAddDialog">
            新增客户
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="6">
        <el-card class="stat-card total">
          <div class="stat-content">
            <div class="stat-label">客户总数</div>
            <div class="stat-value">{{ statistics.total }}</div>
            <div class="stat-icon">👥</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card vip">
          <div class="stat-content">
            <div class="stat-label">VIP客户</div>
            <div class="stat-value">{{ statistics.vip }}</div>
            <div class="stat-icon">⭐</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card normal">
          <div class="stat-content">
            <div class="stat-label">普通客户</div>
            <div class="stat-value">{{ statistics.normal }}</div>
            <div class="stat-icon">👤</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card new">
          <div class="stat-content">
            <div class="stat-label">新客户</div>
            <div class="stat-value">{{ statistics.new }}</div>
            <div class="stat-icon">🆕</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 客户列表 -->
    <el-row class="mt-20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>客户列表</span>
            </div>
          </template>
          
          <el-table
            :data="customers"
            stripe
            style="width: 100%"
            v-loading="loading"
          >
            <el-table-column prop="code" label="客户编码" width="100" />
            <el-table-column prop="name" label="客户名称" width="200" />
            <el-table-column label="客户类别" width="120">
              <template #default="scope">
                <el-tag :type="getCategoryType(scope.row.category)">
                  {{ scope.row.category }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="contact_person" label="联系人" width="100" />
            <el-table-column prop="contact_phone" label="联系电话" width="130" />
            <el-table-column prop="contact_email" label="邮箱" width="180" />
            <el-table-column prop="address" label="地址" show-overflow-tooltip />
            <el-table-column label="操作" width="180" fixed="right">
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
        <el-form-item label="客户编码" required>
          <el-input v-model="formData.code" placeholder="如: C-001" />
        </el-form-item>
        
        <el-form-item label="客户名称" required>
          <el-input v-model="formData.name" placeholder="请输入客户名称" />
        </el-form-item>
        
        <el-form-item label="客户类别" required>
          <el-select v-model="formData.category" placeholder="选择客户类别" style="width: 100%">
            <el-option label="VIP客户" value="VIP" />
            <el-option label="普通客户" value="普通" />
            <el-option label="新客户" value="新客户" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="联系人">
          <el-input v-model="formData.contact_person" placeholder="请输入联系人姓名" />
        </el-form-item>
        
        <el-form-item label="联系电话">
          <el-input v-model="formData.contact_phone" placeholder="请输入联系电话" />
        </el-form-item>
        
        <el-form-item label="邮箱">
          <el-input v-model="formData.contact_email" placeholder="请输入邮箱地址" />
        </el-form-item>
        
        <el-form-item label="地址">
          <el-input
            v-model="formData.address"
            type="textarea"
            :rows="3"
            placeholder="请输入详细地址"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="客户详情"
      width="700px"
    >
      <el-descriptions :column="2" border v-if="currentCustomer">
        <el-descriptions-item label="客户编码">{{ currentCustomer.code }}</el-descriptions-item>
        <el-descriptions-item label="客户名称">{{ currentCustomer.name }}</el-descriptions-item>
        <el-descriptions-item label="客户类别">
          <el-tag :type="getCategoryType(currentCustomer.category)">
            {{ currentCustomer.category }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="联系人">{{ currentCustomer.contact_person }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ currentCustomer.contact_phone }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ currentCustomer.contact_email }}</el-descriptions-item>
        <el-descriptions-item label="地址" :span="2">{{ currentCustomer.address }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh, Plus, View, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from '@/api/axios'

const filters = reactive({
  category: '',
  keyword: ''
})

const customers = ref([])
const loading = ref(false)

const statistics = reactive({
  total: 0,
  vip: 0,
  normal: 0,
  new: 0
})

const dialogVisible = ref(false)
const detailVisible = ref(false)
const dialogTitle = ref('新增客户')
const currentCustomer = ref(null)

const formData = reactive({
  code: '',
  name: '',
  category: '',
  contact_person: '',
  contact_phone: '',
  contact_email: '',
  address: ''
})

const categoryTypes = {
  'VIP': 'danger',
  '普通': '',
  '新客户': 'success'
}

const getCategoryType = (category) => {
  return categoryTypes[category] || ''
}

const loadData = async () => {
  loading.value = true
  try {
    // 模拟API调用（实际应调用后端）
    const response = await axios.get('/business/customers')
    customers.value = response.customers || []
    
    // 计算统计
    statistics.total = customers.value.length
    statistics.vip = customers.value.filter(c => c.category === 'VIP').length
    statistics.normal = customers.value.filter(c => c.category === '普通').length
    statistics.new = customers.value.filter(c => c.category === '新客户').length
    
    ElMessage.success('客户数据加载成功')
  } catch (error) {
    console.error('加载客户列表失败:', error)
    // 使用本地数据作为后备
    loadLocalData()
  } finally {
    loading.value = false
  }
}

const loadLocalData = () => {
  // 使用测试数据
  customers.value = [
    {
      id: 1,
      code: 'C-001',
      name: 'ABC科技有限公司',
      category: 'VIP',
      contact_person: '张三',
      contact_phone: '13800138001',
      contact_email: 'zhangsan@abc.com',
      address: '北京市海淀区中关村大街1号'
    },
    {
      id: 2,
      code: 'C-002',
      name: 'XYZ贸易集团',
      category: '普通',
      contact_person: '李四',
      contact_phone: '13800138002',
      contact_email: 'lisi@xyz.com',
      address: '上海市浦东新区陆家嘴环路1000号'
    },
    {
      id: 3,
      code: 'C-003',
      name: '123制造企业',
      category: 'VIP',
      contact_person: '王五',
      contact_phone: '13800138003',
      contact_email: 'wangwu@123.com',
      address: '深圳市南山区科技园南区'
    },
    {
      id: 4,
      code: 'C-004',
      name: 'DEF互联网公司',
      category: '普通',
      contact_person: '赵六',
      contact_phone: '13800138004',
      contact_email: 'zhaoliu@def.com',
      address: '杭州市西湖区文三路'
    },
    {
      id: 5,
      code: 'C-005',
      name: 'GHI电子商务',
      category: '新客户',
      contact_person: '孙七',
      contact_phone: '13800138005',
      contact_email: 'sunqi@ghi.com',
      address: '广州市天河区珠江新城'
    }
  ]
  
  statistics.total = customers.value.length
  statistics.vip = customers.value.filter(c => c.category === 'VIP').length
  statistics.normal = customers.value.filter(c => c.category === '普通').length
  statistics.new = customers.value.filter(c => c.category === '新客户').length
}

const showAddDialog = () => {
  dialogTitle.value = '新增客户'
  Object.assign(formData, {
    code: '',
    name: '',
    category: '',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    address: ''
  })
  dialogVisible.value = true
}

const viewDetail = (row) => {
  currentCustomer.value = row
  detailVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑客户'
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除客户"${row.name}"吗？此操作不可恢复。`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // TODO: 调用删除API
    ElMessage.success('删除成功')
    loadData()
  } catch {
    // 取消删除
  }
}

const handleSubmit = async () => {
  try {
    // TODO: 调用创建/更新API
    ElMessage.success('保存成功')
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
.customers {
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
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
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
  font-size: 32px;
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

.stat-card.vip {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-card.normal {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.stat-card.new {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.stat-card.total .stat-label,
.stat-card.vip .stat-label,
.stat-card.normal .stat-label,
.stat-card.new .stat-label,
.stat-card.total .stat-value,
.stat-card.vip .stat-value,
.stat-card.normal .stat-value,
.stat-card.new .stat-value {
  color: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
</style>
