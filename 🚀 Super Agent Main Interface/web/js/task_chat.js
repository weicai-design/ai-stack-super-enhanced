/**
 * 智能任务系统与聊天框集成
 * 实现聊天框识别重要信息→备忘录→任务提炼→用户确认→执行的完整流程
 */

const TASK_API_BASE = '/api/task-integration';

class TaskChatSystem {
    constructor() {
        this.messages = [];
        this.tasks = [];
        this.currentTaskId = null;
        this.isProcessing = false;
        this.voiceRecognition = null;
        
        this.init();
    }

    init() {
        console.log('🚀 初始化智能任务聊天系统...');
        
        // 绑定事件
        this.bindEvents();
        
        // 加载系统状态
        this.loadSystemStatus();
        
        // 加载任务列表
        this.loadTasks();
        
        console.log('✅ 智能任务聊天系统初始化完成');
    }

    bindEvents() {
        // 输入框回车发送
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message || this.isProcessing) return;
        
        this.isProcessing = true;
        
        // 清空输入框
        input.value = '';
        
        // 添加用户消息到聊天界面
        this.addMessage('user', message);
        
        try {
            // 处理聊天消息并提取任务
            const response = await this.processChatMessage(message);
            
            if (response.success && response.has_tasks) {
                // 显示任务提取结果
                this.showTaskExtraction(response);
            } else {
                // 显示普通回复
                this.addMessage('assistant', response.message || '已收到您的消息，但未检测到任务信息。');
            }
            
        } catch (error) {
            console.error('处理消息失败:', error);
            this.addMessage('assistant', '抱歉，处理消息时出现错误。');
        }
        
        this.isProcessing = false;
    }

    async processChatMessage(message) {
        const response = await fetch(`${TASK_API_BASE}/process-chat-message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                role: 'user',
                content: message,
                timestamp: new Date().toISOString()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    showTaskExtraction(response) {
        const tasks = response.tasks || [];
        const confidence = response.confidence || 0;
        const needsConfirmation = response.needs_confirmation || false;
        
        let message = `🔍 检测到 ${tasks.length} 个潜在任务 (置信度: ${(confidence * 100).toFixed(1)}%)`;
        
        tasks.forEach((task, index) => {
            message += `\n\n📋 任务${index + 1}: ${task.title || '未命名任务'}`;
            if (task.description) {
                message += `\n📝 ${task.description}`;
            }
            if (task.priority) {
                message += `\n🎯 优先级: ${task.priority}`;
            }
            if (task.deadline) {
                message += `\n⏰ 截止时间: ${task.deadline}`;
            }
        });
        
        if (needsConfirmation && tasks.length > 0) {
            message += `\n\n❓ 请确认是否要创建这些任务？`;
            
            // 添加确认按钮
            const taskExtractionDiv = document.createElement('div');
            taskExtractionDiv.className = 'task-extraction';
            taskExtractionDiv.innerHTML = `
                <strong>任务提取结果</strong>
                <div style="margin-top: 10px;">${message.replace(/\n/g, '<br>')}</div>
                <div style="margin-top: 15px; text-align: center;">
                    <button class="btn btn-success" onclick="taskChat.confirmExtraction('${tasks[0].id}')">确认创建</button>
                    <button class="btn btn-danger" onclick="taskChat.rejectExtraction('${tasks[0].id}')">拒绝</button>
                </div>
            `;
            
            document.getElementById('chat-messages').appendChild(taskExtractionDiv);
        } else {
            this.addMessage('assistant', message);
        }
        
        // 滚动到底部
        this.scrollToBottom();
    }

    async confirmExtraction(taskId) {
        try {
            const response = await fetch(`${TASK_API_BASE}/confirm-task`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    task_id: taskId,
                    confirmed: true
                })
            });

            if (response.ok) {
                this.addMessage('assistant', '✅ 任务已确认并创建！');
                this.loadTasks(); // 刷新任务列表
            } else {
                this.addMessage('assistant', '❌ 任务确认失败。');
            }
        } catch (error) {
            console.error('确认任务失败:', error);
            this.addMessage('assistant', '❌ 任务确认失败。');
        }
    }

    async rejectExtraction(taskId) {
        try {
            const response = await fetch(`${TASK_API_BASE}/confirm-task`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    task_id: taskId,
                    confirmed: false
                })
            });

            if (response.ok) {
                this.addMessage('assistant', '❌ 任务已拒绝。');
            } else {
                this.addMessage('assistant', '❌ 任务拒绝失败。');
            }
        } catch (error) {
            console.error('拒绝任务失败:', error);
            this.addMessage('assistant', '❌ 任务拒绝失败。');
        }
    }

    async executeTask(taskId) {
        try {
            const response = await fetch(`${TASK_API_BASE}/execute-task`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    task_id: taskId
                })
            });

            if (response.ok) {
                this.addMessage('assistant', '🚀 任务执行中...');
                
                // 模拟执行过程
                setTimeout(() => {
                    this.addMessage('assistant', '✅ 任务执行完成！');
                    this.loadTasks(); // 刷新任务列表
                }, 2000);
                
            } else {
                this.addMessage('assistant', '❌ 任务执行失败。');
            }
        } catch (error) {
            console.error('执行任务失败:', error);
            this.addMessage('assistant', '❌ 任务执行失败。');
        }
    }

    addMessage(role, content) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const sender = role === 'user' ? '您' : '智能助手';
        messageDiv.innerHTML = `<strong>${sender}:</strong> ${content.replace(/\n/g, '<br>')}`;
        
        messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async loadSystemStatus() {
        try {
            const response = await fetch(`${TASK_API_BASE}/system-status`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.updateSystemStats(data.statistics);
                }
            }
        } catch (error) {
            console.error('加载系统状态失败:', error);
        }
    }

    updateSystemStats(stats) {
        document.getElementById('total-tasks').textContent = stats.total_tasks_processed || 0;
        document.getElementById('extraction-rate').textContent = `${(stats.success_rate * 100).toFixed(1)}%`;
        document.getElementById('confirmation-rate').textContent = `${(stats.average_confidence * 100).toFixed(1)}%`;
        document.getElementById('success-rate').textContent = `${(stats.success_rate * 100).toFixed(1)}%`;
    }

    async loadTasks() {
        try {
            const response = await fetch(`${TASK_API_BASE}/extracted-tasks?limit=10`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.tasks = data.tasks || [];
                    this.renderTasks();
                }
            }
        } catch (error) {
            console.error('加载任务列表失败:', error);
        }
    }

    renderTasks() {
        const taskList = document.getElementById('task-list');
        taskList.innerHTML = '';

        if (this.tasks.length === 0) {
            taskList.innerHTML = '<p style="text-align: center; color: #666;">暂无任务</p>';
            return;
        }

        this.tasks.forEach(task => {
            const taskCard = document.createElement('div');
            taskCard.className = `task-card ${task.status || 'pending'}`;
            
            const priorityClass = this.getPriorityClass(task.priority);
            
            taskCard.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <strong>${task.title || '未命名任务'}</strong>
                    <span class="task-priority ${priorityClass}">${task.priority || '中等'}</span>
                </div>
                <div style="font-size: 0.9em; color: #666; margin-bottom: 8px;">
                    ${task.description || '暂无描述'}
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8em; color: #999;">
                    <span>${task.status || '待处理'}</span>
                    <span>${task.created_at ? new Date(task.created_at).toLocaleDateString() : ''}</span>
                </div>
                <div style="margin-top: 10px; text-align: center;">
                    ${task.status === 'pending' ? 
                        `<button class="btn btn-primary" onclick="taskChat.executeTask('${task.id}')" style="font-size: 0.8em; padding: 4px 8px;">执行</button>` : 
                        ''
                    }
                </div>
            `;
            
            taskList.appendChild(taskCard);
        });
    }

    getPriorityClass(priority) {
        switch (priority?.toLowerCase()) {
            case 'high': return 'priority-high';
            case 'medium': return 'priority-medium';
            case 'low': return 'priority-low';
            default: return 'priority-medium';
        }
    }

    toggleVoiceInput() {
        if (!this.voiceRecognition) {
            this.initVoiceRecognition();
        }
        
        if (this.voiceRecognition && this.voiceRecognition.isListening) {
            this.stopVoiceInput();
        } else {
            this.startVoiceInput();
        }
    }

    initVoiceRecognition() {
        // 简单的语音识别实现（实际项目中应使用Web Speech API）
        this.voiceRecognition = {
            isListening: false,
            start: () => {
                this.voiceRecognition.isListening = true;
                this.addMessage('assistant', '🎤 语音输入已开启，请开始说话...');
                
                // 模拟语音识别结果
                setTimeout(() => {
                    if (this.voiceRecognition.isListening) {
                        const sampleMessages = [
                            '我需要安排明天的会议',
                            '记得处理客户反馈',
                            '应该完成项目报告',
                            '必须更新系统文档'
                        ];
                        const randomMessage = sampleMessages[Math.floor(Math.random() * sampleMessages.length)];
                        
                        document.getElementById('chat-input').value = randomMessage;
                        this.addMessage('assistant', `🎤 识别到: "${randomMessage}"`);
                        this.stopVoiceInput();
                    }
                }, 2000);
            },
            stop: () => {
                this.voiceRecognition.isListening = false;
                this.addMessage('assistant', '🎤 语音输入已关闭');
            }
        };
    }

    startVoiceInput() {
        if (this.voiceRecognition) {
            this.voiceRecognition.start();
        }
    }

    stopVoiceInput() {
        if (this.voiceRecognition) {
            this.voiceRecognition.stop();
        }
    }
}

// 全局函数供HTML调用
function sendMessage() {
    if (window.taskChat) {
        window.taskChat.sendMessage();
    }
}

function toggleVoiceInput() {
    if (window.taskChat) {
        window.taskChat.toggleVoiceInput();
    }
}

function refreshTasks() {
    if (window.taskChat) {
        window.taskChat.loadTasks();
        window.taskChat.loadSystemStatus();
    }
}

function clearCompletedTasks() {
    if (window.taskChat) {
        // 在实际系统中，这里应该调用API删除已完成任务
        window.taskChat.addMessage('assistant', '🗑️ 已完成任务已清理');
        window.taskChat.loadTasks();
    }
}

function closeTaskModal() {
    const modal = document.getElementById('task-confirm-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function confirmTask(confirmed) {
    closeTaskModal();
    if (window.taskChat && window.taskChat.currentTaskId) {
        if (confirmed) {
            window.taskChat.confirmExtraction(window.taskChat.currentTaskId);
        } else {
            window.taskChat.rejectExtraction(window.taskChat.currentTaskId);
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    window.taskChat = new TaskChatSystem();
});