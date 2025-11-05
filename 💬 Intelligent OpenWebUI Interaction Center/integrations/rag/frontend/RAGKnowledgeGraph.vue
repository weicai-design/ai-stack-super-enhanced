<!--
RAG Knowledge Graph Component
RAG知识图谱可视化组件 - 用于OpenWebUI

功能：
1. 知识图谱可视化
2. 节点交互
3. 实体查询
4. 子图展示
-->

<template>
  <div class="rag-knowledge-graph">
    <!-- 工具栏 -->
    <div class="rag-kg-toolbar">
      <div class="rag-kg-search">
        <input
          v-model="searchQuery"
          @keyup.enter="searchEntity"
          type="text"
          class="rag-kg-search-input"
          placeholder="搜索实体..."
        />
        <button @click="searchEntity" class="rag-kg-search-button">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
        </button>
      </div>
      
      <div class="rag-kg-actions">
        <button @click="refreshGraph" class="rag-kg-action-button" title="刷新">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <polyline points="23 4 23 10 17 10"></polyline>
            <polyline points="1 20 1 14 7 14"></polyline>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
        </button>
        <button @click="resetView" class="rag-kg-action-button" title="重置视图">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M12 6v6l4 2"></path>
          </svg>
        </button>
        <button @click="downloadGraph" class="rag-kg-action-button" title="下载图谱">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
        </button>
        <button @click="exportGraph" class="rag-kg-action-button" title="导出为图片">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <rect x="3" y="3" width="18" height="18" rx="2"></rect>
            <path d="M9 9h6v6H9z"></path>
          </svg>
        </button>
        <button @click="toggleFullscreen" class="rag-kg-action-button" title="全屏">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- 图谱容器 -->
    <div class="rag-kg-container">
      <div ref="graphContainer" class="rag-kg-canvas"></div>
      
      <!-- 加载状态 -->
      <div v-if="isLoading" class="rag-kg-loading">
        <div class="rag-spinner"></div>
        <p>加载知识图谱...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!hasGraph" class="rag-kg-empty">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <p>暂无知识图谱数据</p>
        <p class="rag-kg-hint">上传文档以构建知识图谱</p>
      </div>

      <!-- 节点详情面板 -->
      <div v-if="selectedNode" class="rag-kg-details">
        <div class="rag-kg-details-header">
          <h3>实体详情</h3>
          <button @click="closeDetails" class="rag-kg-close-button">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="rag-kg-details-content">
          <div class="rag-kg-detail-item">
            <label>类型:</label>
            <span>{{ selectedNode.type }}</span>
          </div>
          <div class="rag-kg-detail-item">
            <label>值:</label>
            <span>{{ selectedNode.value }}</span>
          </div>
          <div v-if="selectedNode.count" class="rag-kg-detail-item">
            <label>出现次数:</label>
            <span>{{ selectedNode.count }}</span>
          </div>
          <div v-if="selectedNode.degree" class="rag-kg-detail-item">
            <label>连接数:</label>
            <span>{{ selectedNode.degree }}</span>
          </div>
          <div class="rag-kg-details-actions">
            <button @click="focusOnNode" class="rag-kg-focus-button">聚焦节点</button>
            <button @click="expandSubgraph" class="rag-kg-expand-button">展开子图</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计信息 -->
    <div v-if="statistics" class="rag-kg-stats">
      <div class="rag-kg-stat-item">
        <span class="rag-kg-stat-label">节点:</span>
        <span class="rag-kg-stat-value">{{ statistics.total_nodes }}</span>
      </div>
      <div class="rag-kg-stat-item">
        <span class="rag-kg-stat-label">边:</span>
        <span class="rag-kg-stat-value">{{ statistics.total_edges }}</span>
      </div>
      <div class="rag-kg-stat-item">
        <span class="rag-kg-stat-label">平均度数:</span>
        <span class="rag-kg-stat-value">{{ statistics.average_degree?.toFixed(2) || 0 }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

// Props
const props = defineProps({
  apiUrl: {
    type: String,
    default: 'http://127.0.0.1:8011'
  },
  apiKey: {
    type: String,
    default: null
  },
  width: {
    type: Number,
    default: 800
  },
  height: {
    type: Number,
    default: 600
  }
})

// 响应式数据
const graphContainer = ref(null)
const searchQuery = ref('')
const isLoading = ref(false)
const hasGraph = ref(false)
const selectedNode = ref(null)
const statistics = ref(null)

let simulation = null
let svg = null
let g = null

// 初始化图谱
onMounted(async () => {
  await loadGraph()
  await loadStatistics()
})

onUnmounted(() => {
  if (simulation) {
    simulation.stop()
  }
})

// 加载知识图谱
const loadGraph = async () => {
  isLoading.value = true
  
  try {
    const response = await fetch(`${props.apiUrl}/kg/snapshot`, {
      headers: {
        ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
      }
    })

    if (!response.ok) {
      throw new Error('加载知识图谱失败')
    }

    const data = await response.json()
    
    if (data.nodes > 0) {
      hasGraph.value = true
      await nextTick()
      await renderGraph(data)
    }
  } catch (error) {
    console.error('加载知识图谱错误:', error)
  } finally {
    isLoading.value = false
  }
}

// 渲染图谱
const renderGraph = async (graphData) => {
  if (!graphContainer.value) return

  // 清除旧内容
  d3.select(graphContainer.value).selectAll('*').remove()

  // 创建SVG
  svg = d3.select(graphContainer.value)
    .append('svg')
    .attr('width', props.width)
    .attr('height', props.height)

  g = svg.append('g')

  // 缩放和平移
  const zoom = d3.zoom()
    .scaleExtent([0.1, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    })

  svg.call(zoom)

  // 获取子图数据
  const subgraphData = await fetchSubgraph()
  
  if (!subgraphData || subgraphData.nodes.length === 0) {
    return
  }

  // 创建节点和边
  const nodes = subgraphData.nodes.map(node => ({
    id: node.id,
    type: node.type,
    value: node.value,
    count: node.count || 0
  }))

  const links = subgraphData.edges.map(edge => ({
    source: edge.src,
    target: edge.dst,
    type: edge.type
  }))

  // 创建力导向图
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(props.width / 2, props.height / 2))

  // 绘制边（增强样式）
  const link = g.append('g')
    .selectAll('line')
    .data(links)
    .enter()
    .append('line')
    .attr('stroke', d => getLinkColor(d.type))
    .attr('stroke-opacity', 0.6)
    .attr('stroke-width', d => getLinkWidth(d.type))
    .attr('stroke-dasharray', d => getLinkStyle(d.type))
    .style('cursor', 'pointer')
    .on('mouseover', function(event, d) {
      d3.select(this)
        .attr('stroke-opacity', 1)
        .attr('stroke-width', getLinkWidth(d.type) + 1)
    })
    .on('mouseout', function(event, d) {
      d3.select(this)
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', getLinkWidth(d.type))
    })

  // 绘制节点（增强样式和交互）
  const node = g.append('g')
    .selectAll('circle')
    .data(nodes)
    .enter()
    .append('circle')
    .attr('r', d => getNodeSize(d))
    .attr('fill', d => getNodeColor(d.type))
    .attr('stroke', '#fff')
    .attr('stroke-width', d => getNodeStrokeWidth(d))
    .style('cursor', 'pointer')
    .style('opacity', 0.9)
    .on('click', (event, d) => {
      selectedNode.value = d
      // 高亮连接的节点和边
      highlightNodeConnections(d, nodes, links)
    })
    .on('mouseover', function(event, d) {
      d3.select(this)
        .attr('stroke-width', getNodeStrokeWidth(d) + 2)
        .attr('opacity', 1)
      
      // 显示工具提示
      showTooltip(event, d)
    })
    .on('mouseout', function(event, d) {
      d3.select(this)
        .attr('stroke-width', getNodeStrokeWidth(d))
        .attr('opacity', 0.9)
      
      hideTooltip()
    })
    .call(drag(simulation))

  // 添加标签（增强样式）
  const label = g.append('g')
    .selectAll('text')
    .data(nodes)
    .enter()
    .append('text')
    .text(d => d.value?.substring(0, 30) || d.id) // 增加显示长度
    .attr('font-size', d => getNodeFontSize(d))
    .attr('font-weight', '500')
    .attr('dx', d => getNodeSize(d) + 5)
    .attr('dy', 5)
    .attr('fill', '#333')
    .style('pointer-events', 'none')
    .style('user-select', 'none')

  // 更新位置
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    node
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)

    label
      .attr('x', d => d.x)
      .attr('y', d => d.y)
  })
}

// 获取子图数据
const fetchSubgraph = async () => {
  try {
    // 先获取一个中心节点
    const snapshotResponse = await fetch(`${props.apiUrl}/kg/snapshot`, {
      headers: {
        ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
      }
    })

    const snapshot = await snapshotResponse.json()
    
    if (!snapshot.entities || snapshot.entities.length === 0) {
      return null
    }

    // 使用第一个实体作为中心
    const centerEntity = snapshot.entities[0]
    const centerId = `${centerEntity.type}:${centerEntity.value}`

    // 查询子图
    const subgraphResponse = await fetch(
      `${props.apiUrl}/kg/query?query_type=subgraph&source=${encodeURIComponent(centerId)}&max_depth=2&limit=50`,
      {
        headers: {
          ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
        }
      }
    )

    if (!subgraphResponse.ok) {
      return null
    }

    const result = await subgraphResponse.json()
    return result.subgraph
  } catch (error) {
    console.error('获取子图错误:', error)
    return null
  }
}

// 拖拽功能
const drag = (simulation) => {
  function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    event.subject.fx = event.subject.x
    event.subject.fy = event.subject.y
  }

  function dragged(event) {
    event.subject.fx = event.x
    event.subject.fy = event.y
  }

  function dragended(event) {
    if (!event.active) simulation.alphaTarget(0)
    event.subject.fx = null
    event.subject.fy = null
  }

  return d3.drag()
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended)
}

// 获取节点颜色
const getNodeColor = (type) => {
  const colors = {
    'doc': '#3b82f6',
    'email': '#10b981',
    'url': '#f59e0b',
    'phone': '#8b5cf6',
    'ip_address': '#ef4444',
    'date': '#06b6d4',
  }
  return colors[type] || '#6b7280'
}

// 搜索实体
const searchEntity = async () => {
  if (!searchQuery.value.trim()) return

  try {
    const response = await fetch(
      `${props.apiUrl}/kg/query?query_type=entities&value_pattern=.*${encodeURIComponent(searchQuery.value)}.*&limit=10`,
      {
        headers: {
          ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
        }
      }
    )

    if (response.ok) {
      const result = await response.json()
      if (result.results && result.results.length > 0) {
        // 聚焦到第一个结果
        const entity = result.results[0]
        const entityId = `${entity.type}:${entity.value}`
        
        // 查询以该实体为中心的子图
        const subgraphResponse = await fetch(
          `${props.apiUrl}/kg/query?query_type=subgraph&source=${encodeURIComponent(entityId)}&max_depth=2&limit=50`,
          {
            headers: {
              ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
            }
          }
        )

        if (subgraphResponse.ok) {
          const subgraphResult = await subgraphResponse.json()
          await renderGraph({ subgraph: subgraphResult.subgraph })
        }
      }
    }
  } catch (error) {
    console.error('搜索实体错误:', error)
  }
}

// 加载统计信息
const loadStatistics = async () => {
  try {
    const response = await fetch(
      `${props.apiUrl}/kg/query?query_type=statistics`,
      {
        headers: {
          ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
        }
      }
    )

    if (response.ok) {
      const result = await response.json()
      statistics.value = result.statistics
    }
  } catch (error) {
    console.error('加载统计信息错误:', error)
  }
}

// 刷新图谱
const refreshGraph = async () => {
  await loadGraph()
  await loadStatistics()
}

// 重置视图
const resetView = () => {
  if (svg && g) {
    svg.transition()
      .duration(750)
      .call(
        d3.zoom().transform,
        d3.zoomIdentity
      )
  }
}

// 下载图谱
const downloadGraph = () => {
  // 导出图谱为JSON或图片
  console.log('下载图谱功能待实现')
}

// 关闭详情
const closeDetails = () => {
  selectedNode.value = null
}

// 聚焦节点
const focusOnNode = () => {
  if (!selectedNode.value) return
  // 实现节点聚焦逻辑
  console.log('聚焦节点:', selectedNode.value)
}

// 展开子图
const expandSubgraph = async () => {
  if (!selectedNode.value) return
  
  try {
    const entityId = `${selectedNode.value.type}:${selectedNode.value.value}`
    const response = await fetch(
      `${props.apiUrl}/kg/query?query_type=subgraph&source=${encodeURIComponent(entityId)}&max_depth=3&limit=100`,
      {
        headers: {
          ...(props.apiKey ? { 'X-API-Key': props.apiKey } : {})
        }
      }
    )

    if (response.ok) {
      const result = await response.json()
      await renderGraph({ subgraph: result.subgraph })
    }
  } catch (error) {
    console.error('展开子图错误:', error)
  }
}
</script>

<style scoped>
.rag-knowledge-graph {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary, white);
  border-radius: 8px;
}

.rag-kg-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid var(--border-color, #e5e5e5);
}

.rag-kg-search {
  display: flex;
  gap: 8px;
  flex: 1;
  max-width: 400px;
}

.rag-kg-search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 6px;
  font-size: 14px;
}

.rag-kg-search-button {
  padding: 8px 16px;
  background: var(--primary-color, #3b82f6);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.rag-kg-actions {
  display: flex;
  gap: 8px;
}

.rag-kg-action-button {
  padding: 8px;
  background: var(--bg-secondary, #f5f5f5);
  border: 1px solid var(--border-color, #ddd);
  border-radius: 6px;
  cursor: pointer;
}

.rag-kg-container {
  position: relative;
  flex: 1;
  overflow: hidden;
}

.rag-kg-canvas {
  width: 100%;
  height: 100%;
}

.rag-kg-loading,
.rag-kg-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: var(--text-secondary, #666);
}

.rag-kg-hint {
  font-size: 12px;
  margin-top: 8px;
}

.rag-kg-details {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 280px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10;
}

.rag-kg-details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid var(--border-color, #e5e5e5);
}

.rag-kg-details-header h3 {
  margin: 0;
  font-size: 16px;
}

.rag-kg-close-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
}

.rag-kg-details-content {
  padding: 12px;
}

.rag-kg-detail-item {
  margin-bottom: 12px;
}

.rag-kg-detail-item label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary, #666);
  margin-bottom: 4px;
}

.rag-kg-detail-item span {
  font-size: 14px;
  color: var(--text-primary, #333);
}

.rag-kg-details-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.rag-kg-focus-button,
.rag-kg-expand-button {
  flex: 1;
  padding: 8px;
  background: var(--primary-color, #3b82f6);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.rag-kg-stats {
  display: flex;
  gap: 24px;
  padding: 12px;
  border-top: 1px solid var(--border-color, #e5e5e5);
  background: var(--bg-secondary, #f5f5f5);
}

.rag-kg-stat-item {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.rag-kg-stat-label {
  color: var(--text-secondary, #666);
}

.rag-kg-stat-value {
  font-weight: 600;
  color: var(--text-primary, #333);
}

.rag-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(59, 130, 246, 0.2);
  border-top-color: var(--primary-color, #3b82f6);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

