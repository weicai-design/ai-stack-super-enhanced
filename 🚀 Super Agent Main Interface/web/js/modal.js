/**
 * 非交互类信息弹窗系统
 * 用于显示资源告警、任务完成、系统通知等非交互类信息
 */

class ModalSystem {
    constructor() {
        this.modals = [];
        this.init();
    }
    
    init() {
        // 创建弹窗容器
        if (!document.getElementById('modal-container')) {
            const container = document.createElement('div');
            container.id = 'modal-container';
            container.className = 'modal-container';
            document.body.appendChild(container);
        }
    }
    
    /**
     * 显示信息弹窗
     * @param {Object} options - 弹窗配置
     * @param {string} options.type - 类型：info, success, warning, error
     * @param {string} options.title - 标题
     * @param {string} options.message - 消息内容
     * @param {number} options.duration - 自动关闭时间（毫秒），0表示不自动关闭
     * @param {Function} options.onClose - 关闭回调
     */
    show(options) {
        const {
            type = 'info',
            title = '',
            message = '',
            duration = 5000,
            onClose = null
        } = options;
        
        const modalId = `modal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const container = document.getElementById('modal-container');
        
        const modal = document.createElement('div');
        modal.id = modalId;
        modal.className = `modal modal-${type}`;
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <span class="modal-icon">${this.getIcon(type)}</span>
                    <h3 class="modal-title">${title}</h3>
                    <button class="modal-close" onclick="window.modalSystem.close('${modalId}')">×</button>
                </div>
                <div class="modal-body">
                    <p>${message}</p>
                </div>
            </div>
        `;
        
        container.appendChild(modal);
        
        // 触发动画
        setTimeout(() => {
            modal.classList.add('modal-show');
        }, 10);
        
        // 自动关闭
        if (duration > 0) {
            setTimeout(() => {
                this.close(modalId, onClose);
            }, duration);
        }
        
        this.modals.push({
            id: modalId,
            element: modal,
            onClose
        });
        
        return modalId;
    }
    
    /**
     * 关闭弹窗
     */
    close(modalId, onClose = null) {
        const modal = this.modals.find(m => m.id === modalId);
        if (!modal) return;
        
        modal.element.classList.remove('modal-show');
        modal.element.classList.add('modal-hide');
        
        setTimeout(() => {
            modal.element.remove();
            this.modals = this.modals.filter(m => m.id !== modalId);
            
            if (onClose) {
                onClose();
            } else if (modal.onClose) {
                modal.onClose();
            }
        }, 300);
    }
    
    /**
     * 关闭所有弹窗
     */
    closeAll() {
        this.modals.forEach(modal => {
            this.close(modal.id);
        });
    }
    
    /**
     * 获取图标
     */
    getIcon(type) {
        const icons = {
            info: 'ℹ️',
            success: '✅',
            warning: '⚠️',
            error: '❌'
        };
        return icons[type] || icons.info;
    }
    
    /**
     * 显示资源告警
     */
    showResourceAlert(resource, usage, threshold) {
        return this.show({
            type: 'warning',
            title: '资源使用告警',
            message: `${resource}使用率已达到${usage}%，超过阈值${threshold}%`,
            duration: 8000
        });
    }
    
    /**
     * 显示任务完成通知
     */
    showTaskComplete(taskName) {
        return this.show({
            type: 'success',
            title: '任务完成',
            message: `任务"${taskName}"已成功完成`,
            duration: 5000
        });
    }
    
    /**
     * 显示系统通知
     */
    showSystemNotification(message, type = 'info') {
        return this.show({
            type,
            title: '系统通知',
            message,
            duration: 5000
        });
    }
}

// 全局实例
window.modalSystem = new ModalSystem();

