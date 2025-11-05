import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/finance/dashboard',
    name: 'FinanceDashboard',
    component: () => import('@/views/finance/Dashboard.vue')
  },
  {
    path: '/finance/data',
    name: 'FinanceData',
    component: () => import('@/views/finance/Data.vue')
  },
  {
    path: '/analytics/revenue',
    name: 'RevenueAnalytics',
    component: () => import('@/views/analytics/Revenue.vue')
  },
  {
    path: '/analytics/cost',
    name: 'CostAnalytics',
    component: () => import('@/views/analytics/Cost.vue')
  },
  {
    path: '/analytics/output',
    name: 'OutputAnalytics',
    component: () => import('@/views/analytics/Output.vue')
  },
  {
    path: '/process/list',
    name: 'ProcessList',
    component: () => import('@/views/process/List.vue')
  },
  {
    path: '/process/tracking',
    name: 'ProcessTracking',
    component: () => import('@/views/process/Tracking.vue')
  },
  {
    path: '/process/exceptions',
    name: 'ProcessExceptions',
    component: () => import('@/views/process/Exceptions.vue')
  },
  {
    path: '/business/customers',
    name: 'Customers',
    component: () => import('@/views/business/Customers.vue')
  },
  {
    path: '/business/orders',
    name: 'Orders',
    component: () => import('@/views/business/Orders.vue')
  },
  {
    path: '/business/projects',
    name: 'Projects',
    component: () => import('@/views/business/Projects.vue')
  },
  {
    path: '/procurement/suppliers',
    name: 'Suppliers',
    component: () => import('@/views/procurement/Suppliers.vue')
  },
  {
    path: '/procurement/orders',
    name: 'PurchaseOrders',
    component: () => import('@/views/procurement/PurchaseOrders.vue')
  },
  {
    path: '/material/list',
    name: 'MaterialList',
    component: () => import('@/views/material/MaterialList.vue')
  },
  {
    path: '/production/plan',
    name: 'ProductionPlan',
    component: () => import('@/views/production/ProductionPlan.vue')
  },
  {
    path: '/quality/inspection',
    name: 'QualityInspection',
    component: () => import('@/views/quality/QualityInspection.vue')
  },
  {
    path: '/warehouse/management',
    name: 'WarehouseManagement',
    component: () => import('@/views/warehouse/WarehouseManagement.vue')
  },
  {
    path: '/equipment/management',
    name: 'EquipmentManagement',
    component: () => import('@/views/equipment/EquipmentManagement.vue')
  },
  {
    path: '/engineering/process',
    name: 'ProcessEngineering',
    component: () => import('@/views/engineering/ProcessEngineering.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

