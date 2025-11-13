/**
 * 智能工作计划功能
 */

const API_BASE = '/api/super-agent';

class TaskManager {
    constructor() {
        this.tasks = [];
        this.init();
    }

    init() {
        // 检查元素是否存在
        const extractBtn = document.getElementById('extract-tasks');
        if (extractBtn) {
            extractBtn.addEventListener('click', () => this.extractTasks());
        }
        
        // 延迟加载，等待DOM完全加载
        setTimeout(() => {
            this.loadTasks();
        }, 500);
    }

    async loadTasks() {
        try {
            const response = await fetch(`${API_BASE}/tasks`);
            const data = await response.json();
            this.tasks = data.tasks || [];
            this.renderTasks();
            this.updateStats();
        } catch (error) {
            console.error('加载任务失败:', error);
        }
    }

    async extractTasks() {
        try {
            const response = await fetch(`${API_BASE}/tasks/extract`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.tasks && data.tasks.length > 0) {
                this.tasks = [...this.tasks, ...data.tasks];
                this.renderTasks();
                this.updateStats();
                alert(`成功提取 ${data.tasks.length} 个任务，请确认后执行`);
            } else {
                alert('未找到可提取的任务');
            }
        } catch (error) {
            console.error('提取任务失败:', error);
            alert('提取任务失败');
        }
    }

    renderTasks() {
        const tasksList = document.getElementById('task-list');
        if (!tasksList) {
            console.warn('任务列表元素不存在');
            return;
        }
        
        // 如果API返回了数据，使用API数据
        if (this.tasks.length > 0) {
            tasksList.innerHTML = this.tasks.map(task => `
                <div class="task-item" data-task-id="${task.id || ''}">
                    <div class="task-title">${task.title || task.name || ''}</div>
                    <div class="task-status ${task.status || 'executing'}">${this.getStatusText(task.status || 'executing')}</div>
                    <div class="task-description">${task.description || task.desc || ''}</div>
                </div>
            `).join('');
        }
        // 否则保持HTML中的默认内容
    }

    async confirmTask(taskId, confirmed) {
        try {
            const response = await fetch(`${API_BASE}/tasks/${taskId}/confirm`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    confirmed: confirmed,
                    reason: confirmed ? null : '用户拒绝'
                })
            });

            const data = await response.json();
            if (data.success) {
                await this.loadTasks();
            }
        } catch (error) {
            console.error('确认任务失败:', error);
        }
    }

    updateStats() {
        const pending = this.tasks.filter(t => t.status === 'pending' && t.needs_confirmation).length;
        const inProgress = this.tasks.filter(t => t.status === 'in_progress' || t.status === 'executing').length;
        const completed = this.tasks.filter(t => t.status === 'completed').length;

        // 这些元素可能不存在，先检查
        const pendingEl = document.getElementById('pending-tasks');
        const inProgressEl = document.getElementById('in-progress-tasks');
        const completedEl = document.getElementById('completed-tasks');
        
        if (pendingEl) pendingEl.textContent = pending;
        if (inProgressEl) inProgressEl.textContent = inProgress;
        if (completedEl) completedEl.textContent = completed;
    }

    getStatusText(status) {
        const statusMap = {
            'pending': '待确认',
            'confirmed': '已确认',
            'in_progress': '进行中',
            'completed': '已完成',
            'rejected': '已拒绝'
        };
        return statusMap[status] || status;
    }
}

// 初始化任务管理器
const taskManager = new TaskManager();

