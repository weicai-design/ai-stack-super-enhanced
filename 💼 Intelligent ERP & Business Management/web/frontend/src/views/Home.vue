<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in cards" :key="card.title">
        <el-card class="stat-card" shadow="hover" @click="navigateTo(card.route)">
          <div class="card-content">
            <div class="card-icon" :style="{ backgroundColor: card.color }">
              <component :is="card.icon" />
            </div>
            <div class="card-info">
              <div class="card-title">{{ card.title }}</div>
              <div class="card-value">{{ card.value }}</div>
              <div class="card-trend" :class="card.trendClass">
                {{ card.trend }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快捷入口</span>
            </div>
          </template>
          <div class="quick-links">
            <el-button
              v-for="link in quickLinks"
              :key="link.title"
              :icon="link.icon"
              @click="navigateTo(link.route)"
            >
              {{ link.title }}
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统信息</span>
            </div>
          </template>
          <div class="system-info">
            <div class="info-item">
              <span class="label">系统版本：</span>
              <span class="value">v1.0.0</span>
            </div>
            <div class="info-item">
              <span class="label">部署环境：</span>
              <span class="value">Docker</span>
            </div>
            <div class="info-item">
              <span class="label">数据库：</span>
              <span class="value">PostgreSQL 15</span>
            </div>
            <div class="info-item">
              <span class="label">AI模型：</span>
              <span class="value">Qwen2.5-7B</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row class="mt-20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>欢迎使用智能ERP系统</span>
            </div>
          </template>
          <el-alert
            title="系统说明"
            type="info"
            :closable="false"
          >
            <p>本系统集成了财务管理、经营分析、流程管理等核心功能，帮助企业实现智能化管理。</p>
            <p class="mt-10">✅ 财务管理：支持日/周/月/季/年财务看板，实时掌握财务状况</p>
            <p class="mt-10">✅ 经营分析：提供开源分析、成本分析、产出效益分析</p>
            <p class="mt-10">✅ 流程管理：全流程跟踪，异常监控，持续改进</p>
            <p class="mt-10">✅ AI支持：基于大语言模型的智能分析和建议</p>
          </el-alert>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Coin,
  TrendCharts,
  Connection,
  Management,
  Plus,
  Search,
  Document
} from '@element-plus/icons-vue'

const router = useRouter()

const cards = ref([
  {
    title: '财务看板',
    value: '¥ 1,234,567',
    trend: '↑ 12.5%',
    trendClass: 'up',
    icon: Coin,
    color: '#409EFF',
    route: '/finance/dashboard'
  },
  {
    title: '经营分析',
    value: '85分',
    trend: '↑ 5.2%',
    trendClass: 'up',
    icon: TrendCharts,
    color: '#67C23A',
    route: '/analytics/revenue'
  },
  {
    title: '流程管理',
    value: '23个',
    trend: '进行中',
    trendClass: 'normal',
    icon: Connection,
    color: '#E6A23C',
    route: '/process/list'
  },
  {
    title: '业务管理',
    value: '156个',
    trend: '客户总数',
    trendClass: 'normal',
    icon: Management,
    color: '#F56C6C',
    route: '/business/customers'
  },
  {
    title: '采购管理',
    value: '15个',
    trend: '供应商',
    trendClass: 'normal',
    icon: Management,
    color: '#9C27B0',
    route: '/procurement/suppliers'
  },
  {
    title: '物料管理',
    value: '320种',
    trend: 'MRP',
    trendClass: 'normal',
    icon: Document,
    color: '#009688',
    route: '/material/list'
  },
  {
    title: '生产计划',
    value: '8个',
    trend: '进行中',
    trendClass: 'normal',
    icon: TrendCharts,
    color: '#FF9800',
    route: '/production/plan'
  },
  {
    title: '质量管理',
    value: '98.5%',
    trend: '合格率',
    trendClass: 'up',
    icon: TrendCharts,
    color: '#4CAF50',
    route: '/quality/inspection'
  },
  {
    title: '仓储管理',
    value: '3个',
    trend: '仓库',
    trendClass: 'normal',
    icon: Management,
    color: '#795548',
    route: '/warehouse/management'
  },
  {
    title: '设备管理',
    value: '28台',
    trend: '95%完好率',
    trendClass: 'up',
    icon: Management,
    color: '#607D8B',
    route: '/equipment/management'
  },
  {
    title: '工艺管理',
    value: '15条',
    trend: '工艺路线',
    trendClass: 'normal',
    icon: Document,
    color: '#9E9E9E',
    route: '/engineering/process'
  }
])

const quickLinks = ref([
  { title: '新建订单', icon: Plus, route: '/business/orders' },
  { title: '查看报表', icon: Document, route: '/finance/dashboard' },
  { title: '流程跟踪', icon: Search, route: '/process/tracking' },
  { title: '采购订单', icon: Document, route: '/procurement/orders' },
  { title: '生产计划', icon: TrendCharts, route: '/production/plan' },
  { title: '质量检验', icon: Search, route: '/quality/inspection' },
  { title: '仓库管理', icon: Management, route: '/warehouse/management' }
])

const navigateTo = (route) => {
  if (route) {
    router.push(route)
  }
}
</script>

<style scoped>
.home {
  padding: 20px;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 20px;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.card-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
}

.card-info {
  flex: 1;
}

.card-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.card-trend {
  font-size: 12px;
}

.card-trend.up {
  color: #67C23A;
}

.card-trend.down {
  color: #F56C6C;
}

.card-trend.normal {
  color: #909399;
}

.mt-20 {
  margin-top: 20px;
}

.mt-10 {
  margin-top: 10px;
}

.card-header {
  font-weight: bold;
}

.quick-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.system-info {
  padding: 10px 0;
}

.info-item {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .label {
  width: 120px;
  color: #909399;
}

.info-item .value {
  flex: 1;
  color: #303133;
  font-weight: 500;
}
</style>

