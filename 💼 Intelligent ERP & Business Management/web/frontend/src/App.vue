<template>
  <div id="app">
    <el-container class="layout-container">
      <!-- 侧边栏 -->
      <el-aside width="220px" class="sidebar">
        <div class="logo">
          <h2>智能ERP系统</h2>
        </div>
        <el-menu
          :default-active="activeMenu"
          class="el-menu-vertical"
          router
          background-color="#2c3e50"
          text-color="#fff"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          
          <el-sub-menu index="finance">
            <template #title>
              <el-icon><Coin /></el-icon>
              <span>财务管理</span>
            </template>
            <el-menu-item index="/finance/dashboard">财务看板</el-menu-item>
            <el-menu-item index="/finance/data">财务数据</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="analytics">
            <template #title>
              <el-icon><TrendCharts /></el-icon>
              <span>经营分析</span>
            </template>
            <el-menu-item index="/analytics/revenue">开源分析</el-menu-item>
            <el-menu-item index="/analytics/cost">成本分析</el-menu-item>
            <el-menu-item index="/analytics/output">产出效益</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="process">
            <template #title>
              <el-icon><Connection /></el-icon>
              <span>流程管理</span>
            </template>
            <el-menu-item index="/process/list">流程列表</el-menu-item>
            <el-menu-item index="/process/tracking">流程跟踪</el-menu-item>
            <el-menu-item index="/process/exceptions">异常监控</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="business">
            <template #title>
              <el-icon><Management /></el-icon>
              <span>业务管理</span>
            </template>
            <el-menu-item index="/business/customers">客户管理</el-menu-item>
            <el-menu-item index="/business/orders">订单管理</el-menu-item>
            <el-menu-item index="/business/projects">项目管理</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-container>
        <!-- 顶部导航栏 -->
        <el-header class="header">
          <div class="header-left">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item v-if="breadcrumb">{{ breadcrumb }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="header-right">
            <el-icon class="header-icon"><Bell /></el-icon>
            <el-icon class="header-icon"><User /></el-icon>
          </div>
        </el-header>

        <!-- 内容区 -->
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  HomeFilled,
  Coin,
  TrendCharts,
  Connection,
  Management,
  Bell,
  User
} from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => route.path)

const breadcrumb = computed(() => {
  const path = route.path
  if (path.includes('finance')) return '财务管理'
  if (path.includes('analytics')) return '经营分析'
  if (path.includes('process')) return '流程管理'
  if (path.includes('business')) return '业务管理'
  return ''
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #2c3e50;
  height: 100vh;
  overflow-y: auto;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border-bottom: 1px solid #34495e;
}

.logo h2 {
  margin: 0;
  font-size: 18px;
}

.el-menu-vertical {
  border-right: none;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.header-left {
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-icon {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
}

.header-icon:hover {
  color: #409EFF;
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>

