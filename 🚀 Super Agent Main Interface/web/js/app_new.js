/**
 * AI-STACK 超级Agent - 全新界面应用逻辑
 */

const API_BASE = '/api/super-agent';

class App {
    constructor() {
        this.messages = [];
        this.currentModule = null;
        this.isInitialized = false;
        
        // 立即初始化
        this.init();
    }
    
    init() {
        console.log('🚀 初始化应用...');
        
        // 等待DOM加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupEventListeners());
        } else {
            this.setupEventListeners();
        }
    }
    
    setupEventListeners() {
        console.log('📋 设置事件监听器...');
        
        // 发送按钮
        const sendBtn = document.getElementById('send-btn');
        if (sendBtn) {
            sendBtn.onclick = () => this.sendMessage();
            sendBtn.addEventListener('click', () => this.sendMessage());
            console.log('✅ 发送按钮已绑定');
        }
        
        // 输入框回车发送
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            console.log('✅ 输入框已绑定');
        }
        
        // 工具按钮
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            voiceBtn.onclick = () => this.startVoiceInput();
            voiceBtn.addEventListener('click', () => this.startVoiceInput());
        }
        
        const fileBtn = document.getElementById('file-btn');
        if (fileBtn) {
            fileBtn.onclick = () => this.uploadFile();
            fileBtn.addEventListener('click', () => this.uploadFile());
        }
        
        const searchBtn = document.getElementById('search-btn');
        if (searchBtn) {
            searchBtn.onclick = () => this.toggleSearch();
            searchBtn.addEventListener('click', () => this.toggleSearch());
        }
        
        // 导航按钮
        const navButtons = document.querySelectorAll('.nav-btn');
        navButtons.forEach(btn => {
            const module = btn.dataset.module;
            btn.onclick = () => this.switchModule(module);
            btn.addEventListener('click', () => this.switchModule(module));
        });
        console.log(`✅ ${navButtons.length} 个导航按钮已绑定`);
        
        // 快速操作按钮
        const quickMemo = document.getElementById('quick-memo');
        if (quickMemo) {
            quickMemo.onclick = () => this.createMemo();
            quickMemo.addEventListener('click', () => this.createMemo());
        }
        
        const quickTask = document.getElementById('quick-task');
        if (quickTask) {
            quickTask.onclick = () => this.createTask();
            quickTask.addEventListener('click', () => this.createTask());
        }
        
        const quickFile = document.getElementById('quick-file');
        if (quickFile) {
            quickFile.onclick = () => this.generateFile();
            quickFile.addEventListener('click', () => this.generateFile());
        }
        
        // 模型选择器
        const modelSelector = document.getElementById('model-selector');
        if (modelSelector) {
            modelSelector.addEventListener('change', (e) => this.changeModel(e.target.value));
        }
        
        // 更新系统状态
        this.updateSystemStatus();
        setInterval(() => this.updateSystemStatus(), 5000);
        
        this.isInitialized = true;
        console.log('✅✅✅ 应用初始化完成！');
    }
    
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) {
            console.warn('消息为空');
            return;
        }
        
        console.log('📤 发送消息:', message);
        
        // 清空输入框
        input.value = '';
        
        // 显示用户消息
        this.addMessage('user', message);
        
        // 显示加载状态
        const loadingId = this.addMessage('assistant', '正在思考...', true);
        
        try {
            const response = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    input_type: 'text',
                    context: {}
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                
                // 移除加载消息
                this.removeMessage(loadingId);
                
                // 显示回复
                if (result.success) {
                    this.addMessage('assistant', result.response);
                    this.addActivity('💬', '收到AI回复');
                } else {
                    this.addMessage('assistant', `错误: ${result.error || '未知错误'}`);
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('发送消息失败:', error);
            this.removeMessage(loadingId);
            this.addMessage('assistant', `发送失败: ${error.message}\n\n（这是模拟响应，请检查后端服务）`);
        }
    }
    
    addMessage(role, content, isLoading = false) {
        const messagesContainer = document.getElementById('chat-messages');
        
        // 如果是第一条消息，移除欢迎消息
        if (this.messages.length === 0) {
            const welcomeMsg = messagesContainer.querySelector('.welcome-message');
            if (welcomeMsg) {
                welcomeMsg.remove();
            }
        }
        
        const messageId = `msg-${Date.now()}-${Math.random()}`;
        const messageDiv = document.createElement('div');
        messageDiv.id = messageId;
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        messageDiv.appendChild(contentDiv);
        
        if (!isLoading) {
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            const now = new Date();
            timeDiv.textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
            messageDiv.appendChild(timeDiv);
        }
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.messages.push({ id: messageId, role, content });
        
        return messageId;
    }
    
    removeMessage(messageId) {
        const message = document.getElementById(messageId);
        if (message) {
            message.remove();
        }
    }
    
    switchModule(module) {
        console.log('🔄 切换模块:', module);
        
        // 更新按钮状态
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.module === module) {
                btn.classList.add('active');
            }
        });
        
        this.currentModule = module;
        this.addMessage('assistant', `已切换到"${this.getModuleName(module)}"模块`);
        this.addActivity('🔄', `切换到${this.getModuleName(module)}`);
        
        // 打开模块（如果是外部模块）
        if (module === 'rag') {
            window.open('http://localhost:8011/rag-management', '_blank');
        } else if (module === 'erp') {
            window.open('http://localhost:8012', '_blank');
        }
    }
    
    getModuleName(module) {
        const names = {
            'chat': '智能聊天',
            'rag': 'RAG知识库',
            'erp': 'ERP管理',
            'content': '内容创作',
            'trend': '趋势分析',
            'stock': '股票量化',
            'operations': '运营财务',
            'coding': 'AI编程',
            'websearch': '网络搜索',
            'translation': '多语言翻译',
            'filegen': '文件生成'
        };
        return names[module] || module;
    }
    
    async changeModel(model) {
        console.log('🔄 切换模型:', model);
        
        try {
            const response = await fetch(`${API_BASE}/llm/config`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    provider: 'ollama',
                    model: model,
                    base_url: 'http://localhost:11434'
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.addActivity('⚙️', `模型已切换为: ${model}`);
                }
            }
        } catch (error) {
            console.error('切换模型失败:', error);
        }
    }
    
    startVoiceInput() {
        console.log('🎤 启动语音输入');
        this.addMessage('assistant', '语音输入功能开发中...');
    }
    
    uploadFile() {
        console.log('📎 上传文件');
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.onchange = (e) => {
            const files = Array.from(e.target.files);
            files.forEach(file => {
                this.addActivity('📎', `上传文件: ${file.name}`);
            });
        };
        input.click();
    }
    
    toggleSearch() {
        console.log('🔍 切换搜索模式');
        const input = document.getElementById('chat-input');
        input.placeholder = input.placeholder.includes('搜索') 
            ? '输入您的问题或指令...' 
            : '输入搜索关键词...';
    }
    
    createMemo() {
        console.log('📝 创建备忘录');
        this.addMessage('assistant', '备忘录功能开发中...');
    }
    
    createTask() {
        console.log('📋 新建任务');
        this.addMessage('assistant', '任务管理功能开发中...');
    }
    
    generateFile() {
        console.log('📄 生成文件');
        this.addMessage('assistant', '文件生成功能开发中...');
    }
    
    addActivity(icon, text) {
        const activityList = document.getElementById('activity-list');
        if (!activityList) return;
        
        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item';
        
        const iconSpan = document.createElement('span');
        iconSpan.className = 'activity-icon';
        iconSpan.textContent = icon;
        
        const textSpan = document.createElement('span');
        textSpan.className = 'activity-text';
        textSpan.textContent = text;
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'activity-time';
        timeSpan.textContent = '刚刚';
        
        activityItem.appendChild(iconSpan);
        activityItem.appendChild(textSpan);
        activityItem.appendChild(timeSpan);
        
        activityList.insertBefore(activityItem, activityList.firstChild);
        
        // 限制最多显示10条
        while (activityList.children.length > 10) {
            activityList.removeChild(activityList.lastChild);
        }
    }
    
    async updateSystemStatus() {
        try {
            const response = await fetch(`${API_BASE}/resource/status`);
            if (response.ok) {
                const data = await response.json();
                
                // 更新CPU
                const cpuBar = document.getElementById('cpu-bar');
                const cpuValue = document.getElementById('cpu-value');
                if (cpuBar && cpuValue && data.cpu_percent !== undefined) {
                    cpuBar.style.width = `${data.cpu_percent}%`;
                    cpuValue.textContent = `${Math.round(data.cpu_percent)}%`;
                }
                
                // 更新内存
                const memoryBar = document.getElementById('memory-bar');
                const memoryValue = document.getElementById('memory-value');
                if (memoryBar && memoryValue && data.memory_percent !== undefined) {
                    memoryBar.style.width = `${data.memory_percent}%`;
                    memoryValue.textContent = `${Math.round(data.memory_percent)}%`;
                }
                
                // 更新磁盘
                const diskBar = document.getElementById('disk-bar');
                const diskValue = document.getElementById('disk-value');
                if (diskBar && diskValue && data.disk_percent !== undefined) {
                    diskBar.style.width = `${data.disk_percent}%`;
                    diskValue.textContent = `${Math.round(data.disk_percent)}%`;
                }
            }
        } catch (error) {
            // 静默失败，不影响主功能
        }
    }
}

// 初始化应用
const app = new App();
window.app = app; // 暴露到全局，方便调试

console.log('✅ 应用脚本已加载');

