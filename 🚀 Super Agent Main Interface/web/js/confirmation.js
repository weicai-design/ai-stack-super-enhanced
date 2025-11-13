/**
 * 用户确认对话框系统
 * 用于任务规划、资源调节等需要用户确认的场景
 */

class ConfirmationSystem {
    constructor() {
        this.pendingConfirmations = new Map();
        this.confirmationHistory = [];
        this.init();
    }
    
    init() {
        // 创建确认对话框容器
        if (!document.getElementById('confirmation-container')) {
            const container = document.createElement('div');
            container.id = 'confirmation-container';
            container.className = 'confirmation-container';
            document.body.appendChild(container);
        }
    }
    
    /**
     * 显示确认对话框
     * @param {Object} options - 确认选项
     * @param {string} options.type - 类型：task_plan, resource_adjust, code_fix等
     * @param {string} options.title - 标题
     * @param {string} options.message - 消息内容
     * @param {string} options.details - 详细信息（可选）
     * @param {Object} options.data - 相关数据（可选）
     * @param {Array} options.options - 选项按钮（默认：['确认', '拒绝', '稍后']）
     * @param {Function} options.onConfirm - 确认回调
     * @param {Function} options.onReject - 拒绝回调
     * @param {Function} options.onCancel - 取消回调
     * @returns {Promise} 返回用户选择的结果
     */
    async show(options) {
        const {
            type = 'general',
            title = '需要您的确认',
            message = '',
            details = '',
            data = {},
            options: buttonOptions = ['确认', '拒绝', '稍后'],
            onConfirm = null,
            onReject = null,
            onCancel = null
        } = options;
        
        return new Promise((resolve) => {
            const confirmationId = `conf_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            
            // 创建确认对话框
            const dialog = this._createDialog({
                id: confirmationId,
                type,
                title,
                message,
                details,
                data,
                buttonOptions,
                onConfirm: async () => {
                    const result = { confirmed: true, confirmationId, type, data };
                    this.confirmationHistory.push({ ...result, timestamp: new Date().toISOString() });
                    if (onConfirm) await onConfirm(result);
                    this._removeDialog(confirmationId);
                    resolve(result);
                },
                onReject: async () => {
                    const result = { confirmed: false, confirmationId, type, data };
                    this.confirmationHistory.push({ ...result, timestamp: new Date().toISOString() });
                    if (onReject) await onReject(result);
                    this._removeDialog(confirmationId);
                    resolve(result);
                },
                onCancel: async () => {
                    const result = { confirmed: false, cancelled: true, confirmationId, type, data };
                    this.confirmationHistory.push({ ...result, timestamp: new Date().toISOString() });
                    if (onCancel) await onCancel(result);
                    this._removeDialog(confirmationId);
                    resolve(result);
                }
            });
            
            this.pendingConfirmations.set(confirmationId, dialog);
            this._showDialog(dialog);
        });
    }
    
    /**
     * 显示任务规划确认对话框
     */
    async showTaskPlanConfirmation(plan) {
        return this.show({
            type: 'task_plan',
            title: '📋 任务计划确认',
            message: `系统已为您生成了一个包含 ${plan.total_tasks || plan.tasks?.length || 0} 个任务的工作计划。`,
            details: this._formatTaskPlanDetails(plan),
            data: { plan },
            options: ['确认计划', '修改计划', '稍后确认'],
            onConfirm: async (result) => {
                // 调用API确认计划
                try {
                    const response = await fetch(`${API_BASE}/task-planning/plans/${plan.id}/confirm`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ confirmed: true })
                    });
                    const data = await response.json();
                    if (data.success) {
                        window.modalSystem?.show({
                            type: 'success',
                            title: '计划已确认',
                            message: '工作计划已确认，可以开始执行任务了。',
                            duration: 3000
                        });
                    }
                } catch (error) {
                    console.error('确认计划失败:', error);
                    window.modalSystem?.show({
                        type: 'error',
                        title: '确认失败',
                        message: '确认计划时发生错误，请稍后重试。',
                        duration: 5000
                    });
                }
            }
        });
    }
    
    /**
     * 显示资源调节确认对话框
     */
    async showResourceAdjustmentConfirmation(suggestion) {
        const riskLevel = suggestion.risk_level || 'medium';
        const riskColors = {
            low: '#52c41a',
            medium: '#faad14',
            high: '#ff4d4f',
            critical: '#ff1744'
        };
        
        return this.show({
            type: 'resource_adjust',
            title: '⚙️ 资源调节建议',
            message: suggestion.description || '系统检测到资源问题，建议进行调节。',
            details: this._formatResourceAdjustmentDetails(suggestion),
            data: { suggestion },
            options: ['执行调节', '拒绝', '稍后'],
            onConfirm: async (result) => {
                // 调用API执行资源调节
                try {
                    const response = await fetch(`${API_BASE}/resources/adjust`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            suggestion_id: suggestion.id || suggestion.issue?.issue_type,
                            action: suggestion.action,
                            approved: true
                        })
                    });
                    const data = await response.json();
                    if (data.success) {
                        window.modalSystem?.show({
                            type: 'success',
                            title: '资源调节已执行',
                            message: data.message || '资源调节已成功执行。',
                            duration: 3000
                        });
                    }
                } catch (error) {
                    console.error('执行资源调节失败:', error);
                    window.modalSystem?.show({
                        type: 'error',
                        title: '执行失败',
                        message: '执行资源调节时发生错误，请稍后重试。',
                        duration: 5000
                    });
                }
            }
        });
    }
    
    /**
     * 显示代码修复确认对话框
     */
    async showCodeFixConfirmation(fixProposal) {
        return this.show({
            type: 'code_fix',
            title: '🔧 代码修复请求',
            message: '系统检测到问题并生成了修复方案，需要您的确认。',
            details: this._formatCodeFixDetails(fixProposal),
            data: { fixProposal },
            options: ['执行修复', '拒绝', '修改'],
            onConfirm: async (result) => {
                // 调用API执行代码修复
                try {
                    const response = await fetch(`${API_BASE}/self-learning/code-fix/execute`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            fix_id: fixProposal.fix_id,
                            approved: true
                        })
                    });
                    const data = await response.json();
                    if (data.success) {
                        window.modalSystem?.show({
                            type: 'success',
                            title: '代码修复已执行',
                            message: '代码修复已成功执行，系统正在重启相关服务。',
                            duration: 5000
                        });
                    }
                } catch (error) {
                    console.error('执行代码修复失败:', error);
                    window.modalSystem?.show({
                        type: 'error',
                        title: '执行失败',
                        message: '执行代码修复时发生错误，请稍后重试。',
                        duration: 5000
                    });
                }
            }
        });
    }
    
    /**
     * 创建确认对话框DOM
     */
    _createDialog({ id, type, title, message, details, data, buttonOptions, onConfirm, onReject, onCancel }) {
        const container = document.getElementById('confirmation-container');
        const dialog = document.createElement('div');
        dialog.id = id;
        dialog.className = 'confirmation-dialog';
        dialog.setAttribute('data-type', type);
        
        // 对话框内容
        dialog.innerHTML = `
            <div class="confirmation-overlay"></div>
            <div class="confirmation-content">
                <div class="confirmation-header">
                    <h3>${title}</h3>
                    <button class="confirmation-close" onclick="window.confirmationSystem._closeDialog('${id}')">×</button>
                </div>
                <div class="confirmation-body">
                    <div class="confirmation-message">${message}</div>
                    ${details ? `<div class="confirmation-details">${details}</div>` : ''}
                </div>
                <div class="confirmation-footer">
                    ${buttonOptions.map((option, index) => {
                        let onClick = 'onCancel';
                        if (index === 0) onClick = 'onConfirm';
                        else if (index === 1) onClick = 'onReject';
                        return `<button class="confirmation-btn confirmation-btn-${index === 0 ? 'primary' : index === 1 ? 'danger' : 'secondary'}" onclick="window.confirmationSystem._handleButtonClick('${id}', '${onClick}')">${option}</button>`;
                    }).join('')}
                </div>
            </div>
        `;
        
        // 存储回调函数
        dialog._callbacks = { onConfirm, onReject, onCancel };
        
        return dialog;
    }
    
    /**
     * 显示对话框
     */
    _showDialog(dialog) {
        const container = document.getElementById('confirmation-container');
        container.appendChild(dialog);
        
        // 添加显示动画
        setTimeout(() => {
            dialog.classList.add('show');
        }, 10);
    }
    
    /**
     * 移除对话框
     */
    _removeDialog(id) {
        const dialog = document.getElementById(id);
        if (dialog) {
            dialog.classList.remove('show');
            setTimeout(() => {
                dialog.remove();
                this.pendingConfirmations.delete(id);
            }, 300);
        }
    }
    
    /**
     * 关闭对话框
     */
    _closeDialog(id) {
        const dialog = document.getElementById(id);
        if (dialog && dialog._callbacks) {
            dialog._callbacks.onCancel();
        }
    }
    
    /**
     * 处理按钮点击
     */
    _handleButtonClick(id, callbackName) {
        const dialog = document.getElementById(id);
        if (dialog && dialog._callbacks && dialog._callbacks[callbackName]) {
            dialog._callbacks[callbackName]();
        }
    }
    
    /**
     * 格式化任务计划详情
     */
    _formatTaskPlanDetails(plan) {
        const tasks = plan.tasks || [];
        const taskList = tasks.slice(0, 5).map((task, index) => 
            `<div class="task-item">
                <span class="task-number">${index + 1}</span>
                <span class="task-title">${task.title || task.description || '未命名任务'}</span>
                ${task.estimated_duration ? `<span class="task-duration">预计 ${task.estimated_duration} 分钟</span>` : ''}
            </div>`
        ).join('');
        
        const moreTasks = tasks.length > 5 ? `<div class="task-more">还有 ${tasks.length - 5} 个任务...</div>` : '';
        
        return `
            <div class="plan-details">
                <div class="plan-stats">
                    <span>总任务数: ${plan.total_tasks || tasks.length}</span>
                    ${plan.total_duration_minutes ? `<span>预计总时长: ${plan.total_duration_minutes} 分钟</span>` : ''}
                </div>
                <div class="task-list">
                    ${taskList}
                    ${moreTasks}
                </div>
            </div>
        `;
    }
    
    /**
     * 格式化资源调节详情
     */
    _formatResourceAdjustmentDetails(suggestion) {
        const issue = suggestion.issue || {};
        return `
            <div class="adjustment-details">
                <div class="adjustment-info">
                    <div class="info-item">
                        <span class="info-label">问题类型:</span>
                        <span class="info-value">${issue.issue_type || '未知'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">严重程度:</span>
                        <span class="info-value risk-${issue.severity || 'medium'}">${issue.severity || '中等'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">当前值:</span>
                        <span class="info-value">${issue.current_value || 'N/A'}%</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">阈值:</span>
                        <span class="info-value">${issue.threshold || 'N/A'}%</span>
                    </div>
                </div>
                <div class="adjustment-action">
                    <div class="action-label">建议操作:</div>
                    <div class="action-description">${suggestion.description || '无描述'}</div>
                    <div class="action-impact">预期影响: ${suggestion.expected_impact || '未知'}</div>
                    ${suggestion.estimated_improvement ? `<div class="action-improvement">预计改善: ${suggestion.estimated_improvement}%</div>` : ''}
                </div>
            </div>
        `;
    }
    
    /**
     * 格式化代码修复详情
     */
    _formatCodeFixDetails(fixProposal) {
        const diagnosis = fixProposal.diagnosis || {};
        return `
            <div class="code-fix-details">
                <div class="fix-problem">
                    <div class="problem-label">问题诊断:</div>
                    <div class="problem-description">${diagnosis.diagnosis || '未知问题'}</div>
                </div>
                <div class="fix-solution">
                    <div class="solution-label">修复说明:</div>
                    <div class="solution-description">${fixProposal.explanation || '无说明'}</div>
                </div>
                ${fixProposal.steps ? `
                    <div class="fix-steps">
                        <div class="steps-label">修复步骤:</div>
                        <ol class="steps-list">
                            ${fixProposal.steps.map(step => `<li>${step}</li>`).join('')}
                        </ol>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    /**
     * 获取确认历史
     */
    getHistory(limit = 50) {
        return this.confirmationHistory.slice(-limit);
    }
    
    /**
     * 清除确认历史
     */
    clearHistory() {
        this.confirmationHistory = [];
    }
}

// 全局实例
window.confirmationSystem = new ConfirmationSystem();

