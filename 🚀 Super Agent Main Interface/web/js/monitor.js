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
        this.startMonitoring();
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
            const resourceResponse = await fetch(`${API_BASE}/resource/status`);
            const resourceData = await resourceResponse.json();
            this.updateResourceStatus(resourceData);

            // 更新学习统计
            const learningResponse = await fetch(`${API_BASE}/learning/statistics`);
            const learningData = await learningResponse.json();
            this.updateLearningStatus(learningData);
        } catch (error) {
            console.error('更新状态失败:', error);
        }
    }

    updateResourceStatus(data) {
        const status = data.status || {};
        
        // 更新CPU
        const cpuPercent = status.cpu?.percent || 0;
        document.getElementById('cpu-progress').style.width = `${cpuPercent}%`;
        document.getElementById('cpu-percent').textContent = `${cpuPercent.toFixed(1)}%`;

        // 更新内存
        const memoryPercent = status.memory?.percent || 0;
        document.getElementById('memory-progress').style.width = `${memoryPercent}%`;
        document.getElementById('memory-percent').textContent = `${memoryPercent.toFixed(1)}%`;

        // 更新磁盘
        const diskPercent = status.disk?.percent || 0;
        document.getElementById('disk-progress').style.width = `${diskPercent}%`;
        document.getElementById('disk-percent').textContent = `${diskPercent.toFixed(1)}%`;

        // 更新外接硬盘
        const drives = status.external_drives || [];
        const drivesList = document.getElementById('drives-list');
        if (drives.length > 0) {
            drivesList.innerHTML = drives.map(drive => `
                <div class="drive-item">
                    <span>${drive.mountpoint}</span>
                    <span>${drive.percent.toFixed(1)}%</span>
                </div>
            `).join('');
        } else {
            drivesList.innerHTML = '<div class="drive-item">无外接硬盘</div>';
        }

        // 显示告警
        if (data.alerts && data.alerts.length > 0) {
            this.showAlerts(data.alerts);
        }
    }

    updateLearningStatus(data) {
        // 更新统计数据
        document.getElementById('workflow-count').textContent = data.total_workflows || 0;
        document.getElementById('problem-count').textContent = data.total_problems || 0;
        document.getElementById('solution-count').textContent = data.total_solutions || 0;
        
        // 更新学习状态指示器
        const statusIndicator = document.getElementById('learning-status');
        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('span:last-child');
        
        if (data.status === 'active') {
            statusDot.style.backgroundColor = '#4caf50';
            statusText.textContent = '监控中';
        } else {
            statusDot.style.backgroundColor = '#999';
            statusText.textContent = '待机中';
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

    showAlerts(alerts) {
        // TODO: 实现告警显示
        console.log('告警:', alerts);
    }
}

// 初始化监控管理器
const monitorManager = new MonitorManager();

