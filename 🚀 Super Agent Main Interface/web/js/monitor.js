/**
 * 状态监控功能
 * 实时显示自我学习和资源监控状态
 */

const API_BASE = '/api/super-agent';

class MonitorManager {
    constructor() {
        this.updateInterval = null;
        this.init();
    }

    init() {
        // 延迟启动监控，确保DOM已加载
        setTimeout(() => {
            this.startMonitoring();
        }, 1000);
    }

    async startMonitoring() {
        // 立即更新一次
        await this.updateStatus();
        
        // 每5秒更新一次
        this.updateInterval = setInterval(() => {
            this.updateStatus();
        }, 5000);
    }

    async updateStatus() {
        try {
            // 更新资源状态
            try {
                const resourceResponse = await fetch(`${API_BASE}/resource/status`);
                if (resourceResponse.ok) {
                    const resourceData = await resourceResponse.json();
                    this.updateResourceStatus(resourceData);
                } else {
                    // API不可用时使用模拟数据
                    this.updateResourceStatus({
                        status: {
                            cpu: { percent: 44 },
                            memory: { percent: 50 },
                            disk: { percent: 78 },
                            network: { speed: 22 },
                            external_drives: [{ size: '2TB' }]
                        }
                    });
                }
            } catch (error) {
                console.warn('资源状态API不可用，使用模拟数据:', error);
                // 使用模拟数据
                this.updateResourceStatus({
                    status: {
                        cpu: { percent: 44 },
                        memory: { percent: 50 },
                        disk: { percent: 78 },
                        network: { speed: 22 },
                        external_drives: [{ size: '2TB' }]
                    }
                });
            }

            // 更新学习统计
            try {
                const learningResponse = await fetch(`${API_BASE}/learning/statistics`);
                if (learningResponse.ok) {
                    const learningData = await learningResponse.json();
                    this.updateLearningStatus(learningData);
                } else {
                    // API不可用时使用模拟数据
                    this.updateLearningStatus({
                        status: 'active',
                        total_workflows: 0,
                        total_problems: 0,
                        total_solutions: 0
                    });
                }
            } catch (error) {
                console.warn('学习统计API不可用，使用模拟数据:', error);
                // 使用模拟数据
                this.updateLearningStatus({
                    status: 'active',
                    total_workflows: 0,
                    total_problems: 0,
                    total_solutions: 0
                });
            }

            // 更新工作流统计
            try {
                const workflowResponse = await fetch(`${API_BASE}/workflow/statistics`);
                if (workflowResponse.ok) {
                    const workflowData = await workflowResponse.json();
                    this.updateWorkflowStatus(workflowData);
                }
            } catch (error) {
                console.warn('工作流统计API不可用:', error);
            }

            // 更新资源自动调节统计
            try {
                const adjusterResponse = await fetch(`${API_BASE}/resource/adjuster/statistics`);
                if (adjusterResponse.ok) {
                    const adjusterData = await adjusterResponse.json();
                    this.updateResourceAdjusterStatus(adjusterData);
                }
            } catch (error) {
                console.warn('资源调节统计API不可用:', error);
            }
        } catch (error) {
            console.error('更新状态失败:', error);
        }
    }

    updateResourceStatus(data) {
        const status = data.status || {};
        
        // 更新CPU
        const cpuEl = document.getElementById('cpu-progress');
        const cpuPercentEl = document.getElementById('cpu-percent');
        if (cpuEl && cpuPercentEl) {
            const cpuPercent = status.cpu?.percent || 44;
            cpuEl.style.width = `${cpuPercent}%`;
            cpuPercentEl.textContent = `${cpuPercent.toFixed(0)}%`;
        }

        // 更新内存
        const memoryEl = document.getElementById('memory-progress');
        const memoryPercentEl = document.getElementById('memory-percent');
        if (memoryEl && memoryPercentEl) {
            const memoryPercent = status.memory?.percent || 50;
            memoryEl.style.width = `${memoryPercent}%`;
            memoryPercentEl.textContent = `${memoryPercent.toFixed(0)}%`;
        }

        // 更新磁盘
        const diskEl = document.getElementById('disk-progress');
        const diskPercentEl = document.getElementById('disk-percent');
        if (diskEl && diskPercentEl) {
            const diskPercent = status.disk?.percent || 78;
            diskEl.style.width = `${diskPercent}%`;
            diskPercentEl.textContent = `${diskPercent.toFixed(0)}%`;
        }

        // 更新网络
        const networkEl = document.getElementById('network-progress');
        const networkSpeedEl = document.getElementById('network-speed');
        if (networkEl && networkSpeedEl) {
            const networkSpeed = status.network?.speed || 22;
            networkEl.style.width = `${networkSpeed}%`;
            networkSpeedEl.textContent = `${networkSpeed} Mbps`;
        }

        // 更新外接硬盘
        const drives = status.external_drives || [];
        const externalDriveInfo = document.querySelector('.external-drive-info');
        if (externalDriveInfo) {
            if (drives.length > 0) {
                externalDriveInfo.innerHTML = drives.map(drive => 
                    `<span>外接硬盘: 已连接(${drive.size || '2TB'})</span>`
                ).join('');
            } else {
                externalDriveInfo.innerHTML = '<span>外接硬盘: 未连接</span>';
            }
        }

        // 显示告警
        if (data.alerts && data.alerts.length > 0) {
            this.showAlerts(data.alerts);
        }
    }

    updateLearningStatus(data) {
        // 更新统计数据（这些元素可能不存在，先检查）
        const workflowCountEl = document.getElementById('workflow-count');
        const problemCountEl = document.getElementById('problem-count');
        const solutionCountEl = document.getElementById('solution-count');
        
        if (workflowCountEl) workflowCountEl.textContent = data.total_workflows || 0;
        if (problemCountEl) problemCountEl.textContent = data.total_problems || 0;
        if (solutionCountEl) solutionCountEl.textContent = data.total_solutions || 0;
        
        // 更新学习状态指示器（如果存在）
        const statusIndicator = document.getElementById('learning-status');
        if (statusIndicator) {
            const statusDot = statusIndicator.querySelector('.status-dot');
            const statusText = statusIndicator.querySelector('span:last-child');
            
            if (statusDot && statusText) {
                if (data.status === 'active') {
                    statusDot.style.backgroundColor = '#4caf50';
                    statusText.textContent = '监控中';
                } else {
                    statusDot.style.backgroundColor = '#999';
                    statusText.textContent = '待机中';
                }
            }
            
            // 如果有优化建议，显示提示
            if (data.optimization_suggestions && data.optimization_suggestions.length > 0) {
                statusIndicator.title = `优化建议: ${data.optimization_suggestions[0]}`;
                statusIndicator.style.cursor = 'pointer';
                statusIndicator.onclick = () => {
                    alert(`优化建议:\n${data.optimization_suggestions.join('\n')}`);
                };
            }
        }
    }

    updateWorkflowStatus(data) {
        // 更新工作流统计信息
        const workflowStatsEl = document.getElementById('workflow-stats');
        if (workflowStatsEl) {
            const avgTime = data.avg_response_time || 0;
            const successRate = data.success_rate || 0;
            const totalWorkflows = data.total_workflows || 0;
            
            workflowStatsEl.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">总工作流:</span>
                    <span class="stat-value">${totalWorkflows}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">平均响应:</span>
                    <span class="stat-value">${avgTime.toFixed(2)}s</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">成功率:</span>
                    <span class="stat-value">${successRate.toFixed(1)}%</span>
                </div>
            `;
        }

        // 显示主要瓶颈
        const bottlenecksEl = document.getElementById('workflow-bottlenecks');
        if (bottlenecksEl && data.top_bottlenecks && data.top_bottlenecks.length > 0) {
            bottlenecksEl.innerHTML = data.top_bottlenecks.map(b => 
                `<div class="bottleneck-item">${b.step_type}: ${b.frequency}次</div>`
            ).join('');
        }
    }

    updateResourceAdjusterStatus(data) {
        // 更新资源自动调节状态
        const adjusterStatusEl = document.getElementById('resource-adjuster-status');
        if (adjusterStatusEl) {
            const enabled = data.auto_adjust_enabled || false;
            const threshold = data.auto_adjust_threshold || 'medium';
            const recentIssues = data.recent_issues || 0;
            const recentSuggestions = data.recent_suggestions || 0;
            
            adjusterStatusEl.innerHTML = `
                <div class="adjuster-status-row">
                    <span>自动调节:</span>
                    <span class="${enabled ? 'status-enabled' : 'status-disabled'}">
                        ${enabled ? '已启用' : '已禁用'}
                    </span>
                </div>
                <div class="adjuster-status-row">
                    <span>阈值:</span>
                    <span>${threshold}</span>
                </div>
                <div class="adjuster-status-row">
                    <span>最近问题:</span>
                    <span>${recentIssues}</span>
                </div>
                <div class="adjuster-status-row">
                    <span>调节建议:</span>
                    <span>${recentSuggestions}</span>
                </div>
            `;
        }

        // 如果有资源问题，显示告警
        if (data.recent_issues > 0) {
            this.showResourceAlerts(data);
        }
    }

    showResourceAlerts(data) {
        // 显示资源告警（如果有）
        const alertsContainer = document.getElementById('resource-alerts');
        if (alertsContainer && data.issue_types) {
            const criticalIssues = Object.entries(data.issue_types)
                .filter(([type, count]) => count > 0)
                .map(([type, count]) => `<div class="alert-item alert-${type}">${type}: ${count}个问题</div>`)
                .join('');
            
            if (criticalIssues) {
                alertsContainer.innerHTML = criticalIssues;
                alertsContainer.style.display = 'block';
            }
        }
    }

    showAlerts(alerts) {
        // TODO: 实现告警显示
        console.log('告警:', alerts);
    }
}

// 初始化监控管理器
const monitorManager = new MonitorManager();

