/**
 * 智能工作计划 & 任务管理脚本
 */

const API_BASE = '/api/super-agent';

/**
 * 兼容旧版任务列表（index_old.html）
 */
class TaskManager {
    constructor() {
        this.tasks = [];
        this.init();
    }

    init() {
        const extractBtn = document.getElementById('extract-tasks');
        if (extractBtn) {
            extractBtn.addEventListener('click', () => this.extractTasks());
        }
        setTimeout(() => this.loadTasks(), 500);
    }

    async request(url, options = {}) {
        const res = await fetch(url, options);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    }

    async loadTasks() {
        try {
            const data = await this.request(`${API_BASE}/tasks`);
            this.tasks = data.tasks || [];
            this.renderTasks();
            this.updateStats();
        } catch (error) {
            console.error('加载任务失败:', error);
        }
    }

    async extractTasks() {
        try {
            const data = await this.request(`${API_BASE}/tasks/extract`, { method: 'POST' });
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
        if (!tasksList) return;
        if (this.tasks.length === 0) return;
            tasksList.innerHTML = this.tasks.map(task => `
                <div class="task-item" data-task-id="${task.id || ''}">
                    <div class="task-title">${task.title || task.name || ''}</div>
                    <div class="task-status ${task.status || 'executing'}">${this.getStatusText(task.status || 'executing')}</div>
                    <div class="task-description">${task.description || task.desc || ''}</div>
                </div>
            `).join('');
    }

    async confirmTask(taskId, confirmed) {
        try {
            await this.request(`${API_BASE}/tasks/${taskId}/confirm`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ confirmed, reason: confirmed ? null : '用户拒绝' })
            });
                await this.loadTasks();
        } catch (error) {
            console.error('确认任务失败:', error);
        }
    }

    updateStats() {
        const pending = this.tasks.filter(t => t.status === 'pending' && t.needs_confirmation).length;
        const inProgress = this.tasks.filter(t => ['in_progress', 'executing'].includes(t.status)).length;
        const completed = this.tasks.filter(t => t.status === 'completed').length;
        const pendingEl = document.getElementById('pending-tasks');
        const inProgressEl = document.getElementById('in-progress-tasks');
        const completedEl = document.getElementById('completed-tasks');
        if (pendingEl) pendingEl.textContent = pending;
        if (inProgressEl) inProgressEl.textContent = inProgress;
        if (completedEl) completedEl.textContent = completed;
    }

    getStatusText(status) {
        const statusMap = {
            pending: '待确认',
            confirmed: '已确认',
            in_progress: '进行中',
            executing: '进行中',
            completed: '已完成',
            rejected: '已拒绝'
        };
        return statusMap[status] || status;
    }
}

/**
 * 工作计划界面管理器
 */
class WorkplanPage {
    constructor(root) {
        this.root = root;
        this.plans = [];
        this.filteredPlans = [];
        this.planStats = {};
        this.availableTasks = [];
        this.selectedPlanId = null;
        this.apiBase = `${API_BASE}/task-planning`;
        this.bindElements();
        this.bindEvents();
    }

    bindElements() {
        this.planListEl = document.getElementById('plans-list');
        this.planDialog = document.getElementById('plan-dialog');
        this.planForm = document.getElementById('plan-form');
        this.planDetailPanel = document.getElementById('plan-detail-panel');
        this.planDetailTitle = document.getElementById('detail-title');
        this.planDetailStatus = document.getElementById('detail-status');
        this.planDetailBody = document.getElementById('detail-body');
        this.taskOptionsEl = document.getElementById('task-options');
        this.detailDialog = document.getElementById('plan-detail-dialog');
        this.detailDialogBody = document.getElementById('detail-dialog-body');
        this.detailDialogTitle = document.getElementById('detail-dialog-title');
    }

    bindEvents() {
        const filters = this.root.querySelectorAll('[data-filter]');
        filters.forEach(el => el.addEventListener('input', () => this.applyFilters()));

        this.root.addEventListener('click', (event) => {
            const action = event.target.closest('[data-action]');
            if (!action) return;
            const { action: act } = action.dataset;
            if (act === 'open-create-plan') {
                this.openCreatePlanDialog();
            } else if (act === 'refresh-plans') {
                this.refresh();
            } else if (act === 'close-plan-dialog') {
                this.closePlanDialog();
            } else if (act === 'close-detail-dialog') {
                this.closeDetailDialog();
            }
        });

        this.planListEl.addEventListener('click', (event) => {
            const card = event.target.closest('.plan-card');
            if (!card) return;
            const planId = Number(card.dataset.planId);
            const actionBtn = event.target.closest('button[data-plan-action]');
            if (actionBtn) {
                event.stopPropagation();
                this.handlePlanAction(actionBtn.dataset.planAction, planId);
                return;
            }
            this.setActivePlan(planId);
        });

        this.planForm.addEventListener('submit', (event) => {
            event.preventDefault();
            this.savePlan();
        });
    }

    async refresh() {
        await Promise.all([this.loadPlans(), this.loadTaskStats(), this.loadAvailableTasks()]);
        this.applyFilters();
        this.updateStats();
    }

    async init() {
        await this.refresh();
    }

    async request(path, options = {}) {
        const res = await fetch(path, options);
        if (!res.ok) {
            const message = await res.text();
            throw new Error(message || '请求失败');
        }
        return res.json();
    }

    async loadPlans() {
        const data = await this.request(`${this.apiBase}/plans`);
        this.plans = data.plans || [];
        this.filteredPlans = [...this.plans];
    }

    async loadTaskStats() {
        const data = await this.request(`${this.apiBase}/tasks/statistics`);
        this.planStats = data || {};
    }

    async loadAvailableTasks() {
        const data = await this.request(`${this.apiBase}/tasks?needs_confirmation=false`);
        this.availableTasks = (data.tasks || []).filter(t => !['completed', 'failed'].includes(t.status));
        this.renderTaskOptions();
    }

    renderTaskOptions(selected = []) {
        if (!this.taskOptionsEl) return;
        if (this.availableTasks.length === 0) {
            this.taskOptionsEl.innerHTML = '<div class="empty-placeholder">暂无可用任务，可先通过聊天或备忘录生成任务。</div>';
            return;
        }
        this.taskOptionsEl.innerHTML = this.availableTasks.map(task => `
            <label>
                <input type="checkbox" value="${task.id}" data-task-option ${selected.includes(task.id) ? 'checked' : ''}>
                <span>${task.title || task.description || '未命名任务'}</span>
                <small style="color:var(--text-secondary);">（${task.priority || 'medium'}）</small>
            </label>
        `).join('');
    }

    renderPlans() {
        if (!this.planListEl) return;
        if (this.filteredPlans.length === 0) {
            this.planListEl.innerHTML = '<div class="empty-placeholder">暂无工作计划，点击“新建计划”立即生成。</div>';
            this.setDetailPlaceholder();
            return;
        }
        this.planListEl.innerHTML = this.filteredPlans.map(plan => this.renderPlanCard(plan)).join('');
        if (this.selectedPlanId) {
            this.setActivePlan(this.selectedPlanId, true);
        }
    }

    renderPlanCard(plan) {
        const progress = plan.total_tasks ? Math.round((plan.completed_tasks / plan.total_tasks) * 100) : 0;
        const statusClass = this.statusClass(plan.status);
        return `
            <div class="plan-card ${plan.id === this.selectedPlanId ? 'active' : ''}" data-plan-id="${plan.id}">
                <div class="plan-header">
                    <div>
                        <div class="plan-title">${plan.title || '未命名计划'}</div>
                        <div class="plan-meta">
                            <span>📅 ${this.formatDate(plan.created_at)}</span>
                            <span>📋 ${plan.total_tasks || 0} 个任务</span>
                            <span>⏱️ ${this.formatDuration(plan.total_duration_minutes)}</span>
                        </div>
                    </div>
                    <div class="plan-actions">
                        <span class="plan-status ${statusClass}">${this.getStatusText(plan.status)}</span>
                        ${plan.status === 'pending' ? `<button class="btn btn-primary" data-plan-action="confirm">确认</button>` : ''}
                        ${plan.status === 'confirmed' ? `<button class="btn btn-secondary" data-plan-action="execute">执行</button>` : ''}
                        <button class="btn btn-secondary" data-plan-action="edit">编辑</button>
                        <button class="btn btn-danger" data-plan-action="delete">删除</button>
                    </div>
                </div>
                <div class="plan-progress">
                    <div class="bar" style="width:${progress}%"></div>
                </div>
                <div style="font-size:13px;color:var(--text-secondary);">进度 ${progress}% · 完成 ${plan.completed_tasks || 0}/${plan.total_tasks || 0}</div>
            </div>
        `;
    }

    updateStats() {
        const setText = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };
        setText('total-plans', this.plans.length);
        setText('pending-plans', this.plans.filter(p => p.status === 'pending').length);
        setText('executing-plans', this.plans.filter(p => p.status === 'executing').length);
        setText('completed-plans', this.plans.filter(p => p.status === 'completed').length);
        setText('active-plans', this.plans.filter(p => ['pending', 'confirmed', 'executing'].includes(p.status)).length);
        setText('pending-tasks-stat', this.planStats.pending || 0);
        setText('in-progress-tasks', this.planStats.in_progress || 0);
        const completionRate = this.planStats.completion_rate ? `${this.planStats.completion_rate.toFixed(1)}%` : '0%';
        setText('task-completion-rate', completionRate);
    }

    setActivePlan(planId, skipDetailUpdate = false) {
        this.selectedPlanId = planId;
        const cards = this.planListEl.querySelectorAll('.plan-card');
        cards.forEach(card => card.classList.toggle('active', Number(card.dataset.planId) === planId));
        if (!skipDetailUpdate) {
            const plan = this.plans.find(p => p.id === planId);
            if (plan) this.renderDetail(plan);
        }
    }

    setDetailPlaceholder() {
        if (!this.planDetailBody) return;
        this.planDetailTitle.textContent = '选择一个计划查看详情';
        this.planDetailStatus.textContent = '';
        this.planDetailBody.innerHTML = '<p class="empty-placeholder">计划详情将在此展示，包括任务列表、关键路径和建议。</p>';
    }

    renderDetail(plan) {
        if (!this.planDetailBody) return;
        this.planDetailTitle.textContent = plan.title || '未命名计划';
        this.planDetailStatus.textContent = this.getStatusText(plan.status);
        this.planDetailStatus.className = `panel-status ${this.statusClass(plan.status)}`;
        const tasks = plan.tasks || [];
        const suggestions = plan.suggestions || [];
        this.planDetailBody.innerHTML = `
            <div>
                <strong>计划概述</strong>
                <p style="margin:8px 0;">${plan.description || '暂无描述'}</p>
                <p style="font-size:13px;color:var(--text-secondary);">分类：${plan.category || 'work'} · 优先级：${plan.priority || 'medium'}</p>
            </div>
            <div>
                <h4>任务概览</h4>
                <div class="task-summary-list">
                    ${tasks.slice(0, 5).map(task => `
                        <div class="task-summary-item">
                            <div>${task.title || task.description || '未命名任务'}</div>
                            <small>状态：${this.getStatusText(task.status)} · 预计 ${task.estimated_duration || 0} 分钟</small>
                        </div>
                    `).join('') || '<div class="empty-placeholder">该计划暂未关联任务</div>'}
                    ${tasks.length > 5 ? `<small style="color:var(--text-secondary);">还有 ${tasks.length - 5} 个任务...</small>` : ''}
                </div>
            </div>
            <div>
                <h4>系统建议</h4>
                <ul style="padding-left:18px;font-size:13px;color:var(--text-secondary);">
                    ${(suggestions.length ? suggestions : ['暂无建议']).map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
            <div style="margin-top:12px;">
                <button class="btn btn-secondary" data-plan-action="view-detail" data-plan-id="${plan.id}">查看完整详情</button>
            </div>
        `;
    }

    openCreatePlanDialog(plan = null) {
        if (!this.planDialog) return;
        this.planDialog.classList.add('show');
        this.planForm.reset();
        document.getElementById('dialog-title').textContent = plan ? '编辑工作计划' : '新建工作计划';
        document.getElementById('plan-id').value = plan ? plan.id : '';
        document.getElementById('plan-title').value = plan?.title || '';
        document.getElementById('plan-description').value = plan?.description || '';
        document.getElementById('plan-category').value = plan?.category || 'work';
        document.getElementById('plan-priority').value = plan?.priority || 'medium';
        const selected = plan?.tasks?.map(t => t.id).filter(Boolean) || [];
        this.renderTaskOptions(selected);
    }

    closePlanDialog() {
        if (this.planDialog) this.planDialog.classList.remove('show');
    }

    openDetailDialog(plan) {
        if (!this.detailDialog) return;
        this.detailDialogTitle.textContent = plan.title || '计划详情';
        const tasks = plan.tasks || [];
        this.detailDialogBody.innerHTML = `
            <div>
                <p>创建时间：${this.formatDate(plan.created_at)} · 最近更新：${this.formatDate(plan.updated_at)}</p>
                <p>关键路径：${(plan.critical_path || []).join(' → ') || '暂无'}</p>
            </div>
            <h4>任务列表</h4>
            <div class="task-summary-list">
                ${tasks.map(task => `
                    <div class="task-summary-item">
                        <div>【${this.getStatusText(task.status)}】${task.title || task.description || '未命名任务'}</div>
                        <small>优先级：${task.priority || 'medium'} · 预计 ${task.estimated_duration || 0} 分钟</small>
                    </div>
                `).join('') || '<div class="empty-placeholder">暂无任务</div>'}
            </div>
        `;
        this.detailDialog.classList.add('show');
    }

    closeDetailDialog() {
        if (this.detailDialog) this.detailDialog.classList.remove('show');
    }

    async savePlan() {
        const planId = document.getElementById('plan-id').value;
        const payload = {
            title: document.getElementById('plan-title').value.trim(),
            description: document.getElementById('plan-description').value.trim(),
            category: document.getElementById('plan-category').value,
            priority: document.getElementById('plan-priority').value,
        };
        const selectedTasks = Array.from(this.taskOptionsEl.querySelectorAll('[data-task-option]:checked'))
            .map(input => Number(input.value));
        if (selectedTasks.length > 0) {
            payload.task_ids = selectedTasks;
        }
        try {
            if (planId) {
                await this.request(`${this.apiBase}/plans/${planId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            } else {
                await this.request(`${this.apiBase}/plans`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }
            this.closePlanDialog();
            await this.refresh();
            this.toast(planId ? '计划已更新' : '计划已创建');
        } catch (error) {
            console.error('保存计划失败:', error);
            this.toast('保存计划失败', 'error');
        }
    }

    async handlePlanAction(action, planId) {
        const plan = this.plans.find(p => p.id === planId);
        if (!plan) return;
        try {
            if (action === 'confirm') {
                await this.request(`${this.apiBase}/plans/${planId}/confirm`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ confirmed: true })
                });
                this.toast('计划已确认');
            } else if (action === 'execute') {
                await this.request(`${this.apiBase}/plans/${planId}/execute`, { method: 'POST' });
                this.toast('计划执行已触发');
            } else if (action === 'delete') {
                if (!confirm('确定要删除该计划吗？')) return;
                await this.request(`${this.apiBase}/plans/${planId}`, { method: 'DELETE' });
                this.toast('计划已删除');
            } else if (action === 'edit') {
                this.openCreatePlanDialog(plan);
                return;
            } else if (action === 'view-detail') {
                this.openDetailDialog(plan);
                return;
            }
            await this.refresh();
        } catch (error) {
            console.error(`计划操作失败: ${action}`, error);
            this.toast('操作失败，请稍后重试', 'error');
        }
    }

    applyFilters() {
        const status = (document.querySelector('[data-filter=\"status\"]')?.value || '').trim();
        const category = (document.querySelector('[data-filter=\"category\"]')?.value || '').trim();
        const search = (document.querySelector('[data-filter=\"search\"]')?.value || '').trim().toLowerCase();
        this.filteredPlans = this.plans.filter(plan => {
            const matchStatus = !status || plan.status === status;
            const matchCategory = !category || plan.category === category;
            const matchSearch = !search || (plan.title || '').toLowerCase().includes(search);
            return matchStatus && matchCategory && matchSearch;
        });
        this.renderPlans();
    }

    statusClass(status) {
        return `status-${status || 'pending'}`;
    }

    getStatusText(status) {
        const map = {
            draft: '草稿',
            pending: '待确认',
            confirmed: '已确认',
            executing: '执行中',
            completed: '已完成',
            rejected: '已拒绝'
        };
        return map[status] || '未知状态';
    }

    formatDate(dateStr) {
        if (!dateStr) return '未知日期';
        try {
            return new Date(dateStr).toLocaleString();
        } catch {
            return dateStr;
        }
    }

    formatDuration(minutes) {
        if (!minutes) return '未知';
        if (minutes < 60) return `${minutes} 分钟`;
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return `${hours} 小时 ${mins} 分钟`;
    }

    toast(message, type = 'success') {
        if (window.modalSystem) {
            window.modalSystem.show({
                type,
                title: type === 'success' ? '成功' : '提示',
                message,
                duration: 2200
            });
        } else {
            console.log(message);
        }
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    const workplanRoot = document.querySelector('[data-workplan=\"true\"]');
    if (workplanRoot) {
        window.workplanPage = new WorkplanPage(workplanRoot);
        await window.workplanPage.init();
    } else if (document.getElementById('task-list')) {
        window.taskManager = new TaskManager();
    }
});

