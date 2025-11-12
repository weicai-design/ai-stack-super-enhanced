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
        const extractBtn = document.getElementById('extract-tasks');
        extractBtn.addEventListener('click', () => this.extractTasks());
        
        this.loadTasks();
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
        const tasksList = document.getElementById('tasks-list');
        if (this.tasks.length === 0) {
            tasksList.innerHTML = '<div class="empty-state">暂无任务</div>';
            return;
        }

        tasksList.innerHTML = this.tasks.map(task => `
            <div class="task-item" data-task-id="${task.id}">
                <div class="task-header">
                    <span class="task-title">${task.title}</span>
                    ${task.needs_confirmation ? `
                        <div class="task-actions">
                            <button class="confirm-btn" onclick="taskManager.confirmTask(${task.id}, true)">✓</button>
                            <button class="reject-btn" onclick="taskManager.confirmTask(${task.id}, false)">×</button>
                        </div>
                    ` : ''}
                </div>
                <div class="task-description">${task.description}</div>
                <div class="task-meta">
                    <span class="task-status">${this.getStatusText(task.status)}</span>
                    <span class="task-time">${new Date(task.created_at).toLocaleString()}</span>
                </div>
            </div>
        `).join('');
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
        const inProgress = this.tasks.filter(t => t.status === 'in_progress').length;
        const completed = this.tasks.filter(t => t.status === 'completed').length;

        document.getElementById('pending-tasks').textContent = pending;
        document.getElementById('in-progress-tasks').textContent = inProgress;
        document.getElementById('completed-tasks').textContent = completed;
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

