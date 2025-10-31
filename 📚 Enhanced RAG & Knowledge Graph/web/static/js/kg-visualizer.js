/**
 * AI Stack Super Enhanced - 知识图谱可视化器
 * 文件: kg-visualizer.js
 * 路径: ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph/web/static/js/
 * 功能: 知识图谱的2D/3D可视化、交互操作、动态布局
 */

class KnowledgeGraphVisualizer {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            width: options.width || 1200,
            height: options.height || 800,
            nodeRadius: options.nodeRadius || 8,
            linkDistance: options.linkDistance || 120,
            chargeStrength: options.chargeStrength || -300,
            enable3D: options.enable3D || false,
            ...options
        };

        this.graphData = { nodes: [], links: [] };
        this.simulation = null;
        this.svg = null;
        this.isInitialized = false;

        this.initializeVisualizer();
    }

    initializeVisualizer() {
        if (!this.container) {
            console.error('KnowledgeGraphVisualizer: 容器不存在');
            return;
        }

        // 清理容器
        this.container.innerHTML = '';

        // 创建SVG元素
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', this.options.width)
            .attr('height', this.options.height)
            .attr('class', 'kg-visualization-svg');

        // 添加缩放行为
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.svg.selectAll('g').attr('transform', event.transform);
            });

        this.svg.call(this.zoom);

        // 创建主分组
        this.g = this.svg.append('g');

        // 创建箭头定义
        this.defs = this.g.append('defs');
        this.defs.append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 15)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('class', 'arrow-head');

        this.isInitialized = true;
        console.log('KnowledgeGraphVisualizer: 初始化完成');
    }

    async loadGraphData(dataUrl) {
        try {
            const response = await fetch(dataUrl);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const graphData = await response.json();
            this.updateGraph(graphData);

            console.log('KnowledgeGraphVisualizer: 图谱数据加载成功', graphData);
        } catch (error) {
            console.error('KnowledgeGraphVisualizer: 数据加载失败', error);
            this.showError('知识图谱数据加载失败: ' + error.message);
        }
    }

    updateGraph(graphData) {
        if (!this.isInitialized) {
            console.error('KnowledgeGraphVisualizer: 可视化器未初始化');
            return;
        }

        this.graphData = this.preprocessGraphData(graphData);
        this.renderGraph();
        this.startSimulation();
    }

    preprocessGraphData(graphData) {
        // 数据预处理和增强
        const processedData = {
            nodes: graphData.nodes.map((node, index) => ({
                id: node.id || `node_${index}`,
                name: node.name || '未命名节点',
                type: node.type || 'entity',
                group: node.group || 1,
                size: node.size || Math.random() * 10 + 5,
                color: this.getNodeColor(node.type),
                description: node.description || '',
                confidence: node.confidence || 1.0,
                ...node
            })),
            links: graphData.links.map((link, index) => ({
                source: link.source,
                target: link.target,
                relationship: link.relationship || 'related',
                strength: link.strength || 1,
                id: link.id || `link_${index}`,
                ...link
            }))
        };

        return processedData;
    }

    getNodeColor(nodeType) {
        const colorMap = {
            'entity': '#4e79a7',
            'concept': '#f28e2c',
            'event': '#e15759',
            'person': '#76b7b2',
            'organization': '#59a14f',
            'location': '#edc949',
            'product': '#af7aa1',
            'default': '#79706e'
        };
        return colorMap[nodeType] || colorMap.default;
    }

    renderGraph() {
        // 清理现有图形
        this.g.selectAll('.link').remove();
        this.g.selectAll('.node').remove();

        // 创建连线
        const link = this.g.append('g')
            .attr('class', 'links')
            .selectAll('.link')
            .data(this.graphData.links)
            .enter().append('line')
            .attr('class', 'link')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', d => Math.sqrt(d.strength))
            .attr('marker-end', 'url(#arrowhead)');

        // 创建节点
        const node = this.g.append('g')
            .attr('class', 'nodes')
            .selectAll('.node')
            .data(this.graphData.nodes)
            .enter().append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', this.dragStarted.bind(this))
                .on('drag', this.dragged.bind(this))
                .on('end', this.dragEnded.bind(this)));

        // 添加节点圆圈
        node.append('circle')
            .attr('r', d => d.size)
            .attr('fill', d => d.color)
            .attr('stroke', '#fff')
            .attr('stroke-width', 1.5)
            .attr('class', 'node-circle');

        // 添加节点标签
        node.append('text')
            .text(d => d.name)
            .attr('x', 12)
            .attr('y', 3)
            .attr('class', 'node-label')
            .attr('font-size', '10px')
            .attr('fill', '#333');

        // 添加鼠标交互
        node.on('mouseover', this.handleNodeMouseOver.bind(this))
            .on('mouseout', this.handleNodeMouseOut.bind(this))
            .on('click', this.handleNodeClick.bind(this));

        this.link = link;
        this.node = node;
    }

    startSimulation() {
        if (this.simulation) {
            this.simulation.stop();
        }

        this.simulation = d3.forceSimulation(this.graphData.nodes)
            .force('link', d3.forceLink(this.graphData.links)
                .id(d => d.id)
                .distance(this.options.linkDistance))
            .force('charge', d3.forceManyBody()
                .strength(this.options.chargeStrength))
            .force('center', d3.forceCenter(this.options.width / 2, this.options.height / 2))
            .force('collision', d3.forceCollide().radius(d => d.size + 5))
            .on('tick', this.ticked.bind(this));

        console.log('KnowledgeGraphVisualizer: 物理模拟启动');
    }

    ticked() {
        if (this.link && this.node) {
            this.link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            this.node
                .attr('transform', d => `translate(${d.x},${d.y})`);
        }
    }

    dragStarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragEnded(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    handleNodeMouseOver(event, d) {
        // 高亮相关节点和连线
        d3.select(event.currentTarget)
            .select('.node-circle')
            .attr('stroke', '#ff0000')
            .attr('stroke-width', 3);

        // 显示节点详情
        this.showNodeTooltip(event, d);
    }

    handleNodeMouseOut(event, d) {
        d3.select(event.currentTarget)
            .select('.node-circle')
            .attr('stroke', '#fff')
            .attr('stroke-width', 1.5);

        this.hideNodeTooltip();
    }

    handleNodeClick(event, d) {
        console.log('节点点击:', d);

        // 触发自定义事件
        const nodeClickEvent = new CustomEvent('kg-node-click', {
            detail: { node: d, event: event }
        });
        this.container.dispatchEvent(nodeClickEvent);

        // 显示详细节点信息
        this.showNodeDetails(d);
    }

    showNodeTooltip(event, node) {
        // 创建或更新工具提示
        let tooltip = d3.select('.kg-tooltip');
        if (tooltip.empty()) {
            tooltip = d3.select('body').append('div')
                .attr('class', 'kg-tooltip')
                .style('opacity', 0)
                .style('position', 'absolute')
                .style('background', 'rgba(0,0,0,0.8)')
                .style('color', 'white')
                .style('padding', '8px')
                .style('border-radius', '4px')
                .style('pointer-events', 'none')
                .style('z-index', 1000);
        }

        tooltip.html(`
            <strong>${node.name}</strong><br/>
            类型: ${node.type}<br/>
            ${node.description ? `描述: ${node.description}<br/>` : ''}
            置信度: ${(node.confidence * 100).toFixed(1)}%
        `)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 10) + 'px')
        .transition()
        .duration(200)
        .style('opacity', 1);
    }

    hideNodeTooltip() {
        d3.select('.kg-tooltip')
            .transition()
            .duration(200)
            .style('opacity', 0);
    }

    showNodeDetails(node) {
        // 创建节点详情模态框
        const modal = document.createElement('div');
        modal.className = 'kg-node-details-modal';
        modal.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 1001;
            max-width: 500px;
            max-height: 80vh;
            overflow-y: auto;
        `;

        modal.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="margin: 0;">${node.name}</h3>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 20px; cursor: pointer;">×</button>
            </div>
            <div>
                <p><strong>类型:</strong> ${node.type}</p>
                <p><strong>分组:</strong> ${node.group}</p>
                <p><strong>置信度:</strong> ${(node.confidence * 100).toFixed(1)}%</p>
                ${node.description ? `<p><strong>描述:</strong> ${node.description}</p>` : ''}
                <p><strong>关联数量:</strong> ${this.getNodeLinkCount(node.id)}</p>
            </div>
            <div style="margin-top: 15px;">
                <button onclick="kgVisualizer.expandNode('${node.id}')" style="margin-right: 10px;">扩展关联</button>
                <button onclick="kgVisualizer.isolateNode('${node.id}')">隔离查看</button>
            </div>
        `;

        document.body.appendChild(modal);

        // 点击背景关闭
        modal.addEventListener('click', (e) => e.stopPropagation());
        document.addEventListener('click', () => modal.remove(), { once: true });
    }

    getNodeLinkCount(nodeId) {
        return this.graphData.links.filter(link =>
            link.source.id === nodeId || link.target.id === nodeId
        ).length;
    }

    expandNode(nodeId) {
        // 扩展节点关联的逻辑
        console.log('扩展节点:', nodeId);
        // 这里可以添加API调用获取更多关联数据
    }

    isolateNode(nodeId) {
        // 隔离查看特定节点
        const isolatedNodes = new Set([nodeId]);
        const isolatedLinks = [];

        // 找到直接关联的节点和连线
        this.graphData.links.forEach(link => {
            if (link.source.id === nodeId) {
                isolatedNodes.add(link.target.id);
                isolatedLinks.push(link);
            } else if (link.target.id === nodeId) {
                isolatedNodes.add(link.source.id);
                isolatedLinks.push(link);
            }
        });

        const isolatedGraph = {
            nodes: this.graphData.nodes.filter(node => isolatedNodes.has(node.id)),
            links: isolatedLinks
        };

        this.updateGraph(isolatedGraph);
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'kg-error-message';
        errorDiv.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            background: #f44336;
            color: white;
            padding: 10px 15px;
            border-radius: 4px;
            z-index: 1000;
        `;
        errorDiv.textContent = message;
        this.container.appendChild(errorDiv);

        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }

    // 公共方法
    resetView() {
        this.svg.transition()
            .duration(750)
            .call(this.zoom.transform, d3.zoomIdentity);
    }

    exportAsImage(format = 'png') {
        const svgData = new XMLSerializer().serializeToString(this.svg.node());
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();

        canvas.width = this.options.width;
        canvas.height = this.options.height;

        img.onload = function() {
            ctx.drawImage(img, 0, 0);
            const dataURL = canvas.toDataURL(`image/${format}`);
            const link = document.createElement('a');
            link.download = `knowledge-graph.${format}`;
            link.href = dataURL;
            link.click();
        };

        img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
    }

    destroy() {
        if (this.simulation) {
            this.simulation.stop();
        }
        this.container.innerHTML = '';
        this.isInitialized = false;
        console.log('KnowledgeGraphVisualizer: 已销毁');
    }
}

// 全局访问
window.KnowledgeGraphVisualizer = KnowledgeGraphVisualizer;
console.log('kg-visualizer.js: 知识图谱可视化器加载完成');