/**
 * 聊天功能
 * 实现AI工作流9步骤的前端交互
 */

const API_BASE = '/api/super-agent';

class ChatManager {
    constructor() {
        this.messages = [];
        this.currentContext = {};
        this.isInitialized = false;
        // 立即尝试初始化，如果DOM未准备好则延迟
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                console.log('📋 DOMContentLoaded触发，初始化ChatManager');
                this.init();
            });
        } else {
            // DOM已加载，延迟一点确保所有元素都渲染完成
            console.log('📋 DOM已加载，延迟初始化ChatManager');
            setTimeout(() => this.init(), 200);
        }
    }

    init() {
        if (this.isInitialized) {
            console.log('聊天管理器已初始化，跳过重复初始化');
            return;
        }
        
        console.log('🚀 初始化聊天管理器...');
        
        const playBtn = document.getElementById('play-btn');
        const squareBtn = document.getElementById('square-btn');
        const chatInput = document.getElementById('chat-input');
        const voiceBtn = document.getElementById('voice-btn');
        const fileBtn = document.getElementById('file-btn');
        const searchIconBtn = document.getElementById('search-icon-btn');

        // 检查所有必需元素
        if (!playBtn || !chatInput || !voiceBtn || !fileBtn || !searchIconBtn) {
            console.error('❌ 缺少必需的元素:', {
                playBtn: !!playBtn,
                chatInput: !!chatInput,
                voiceBtn: !!voiceBtn,
                fileBtn: !!fileBtn,
                searchIconBtn: !!searchIconBtn
            });
            // 增加重试延迟，确保DOM完全加载
            setTimeout(() => this.init(), 1000);
            return;
        }
        
        console.log('✅ 所有必需元素已找到，开始绑定事件...');

        // 发送按钮（播放按钮）- 使用事件委托确保绑定成功
        playBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('✅✅✅ 播放按钮被点击 - onclick方式');
            if (this.sendMessage) {
                this.sendMessage();
            } else {
                console.error('❌ sendMessage方法不存在');
            }
        };
        // 同时使用addEventListener作为备用
        playBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('✅✅✅ 播放按钮被点击 - addEventListener方式');
            if (this.sendMessage) {
                this.sendMessage();
            } else {
                console.error('❌ sendMessage方法不存在');
            }
        });
        
        // 停止按钮
        if (squareBtn) {
            squareBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('✅ 停止按钮被点击');
                this.stopMessage();
            });
        }
        
        // 输入框回车发送（Ctrl+Enter或Enter）
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                console.log('✅ Ctrl+Enter发送消息');
                this.sendMessage();
            } else if (e.key === 'Enter' && !e.shiftKey) {
                // 普通Enter也可以发送
                e.preventDefault();
                console.log('✅ Enter发送消息');
                this.sendMessage();
            }
        });
        
        // 输入框获得焦点时显示提示
        chatInput.addEventListener('focus', () => {
            console.log('✅ 输入框获得焦点');
        });

        // 左侧导航栏点击事件 - 使用onclick和addEventListener双重绑定
        const navItems = document.querySelectorAll('.nav-item');
        console.log(`✅ 找到 ${navItems.length} 个导航项`);
        navItems.forEach((item, index) => {
            const module = item.dataset.module;
            
            // 使用onclick方式
            item.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log(`✅✅✅ 导航项被点击 (onclick): ${module}`);
                if (this.openModule) {
                    this.openModule(module);
                } else {
                    console.error('❌ openModule方法不存在');
                }
            };
            
            // 同时使用addEventListener作为备用
            item.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log(`✅✅✅ 导航项被点击 (addEventListener): ${module}`);
                if (this.openModule) {
                    this.openModule(module);
                }
            });
        });
        
        // 语音按钮 - 使用onclick和addEventListener双重绑定
        voiceBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('✅✅✅ 语音按钮被点击');
            if (this.startVoiceInput) {
                this.startVoiceInput();
            }
        };
        voiceBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('✅✅✅ 语音按钮被点击 - addEventListener');
            if (this.startVoiceInput) {
                this.startVoiceInput();
            }
        });
        
        // 文件按钮 - 使用onclick和addEventListener双重绑定
        fileBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('✅✅✅ 文件按钮被点击');
            if (this.toggleFileUpload) {
                this.toggleFileUpload();
            }
        };
        fileBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('✅✅✅ 文件按钮被点击 - addEventListener');
            if (this.toggleFileUpload) {
                this.toggleFileUpload();
            }
        });
        
        // 搜索按钮 - 使用onclick和addEventListener双重绑定
        searchIconBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('✅✅✅ 搜索按钮被点击');
            if (this.toggleSearchMode) {
                this.toggleSearchMode();
            }
        };
        searchIconBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('✅✅✅ 搜索按钮被点击 - addEventListener');
            if (this.toggleSearchMode) {
                this.toggleSearchMode();
            }
        });
        
        // 模型选择器
        const modelSelector = document.getElementById('model-selector');
        if (modelSelector) {
            modelSelector.addEventListener('change', async (e) => {
                const selectedModel = e.target.value;
                console.log('✅ 模型选择改变:', selectedModel);
                
                // 更新LLM配置
                try {
                    const response = await fetch(`${API_BASE}/llm/config`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            provider: 'ollama',
                            model: selectedModel,
                            base_url: 'http://localhost:11434'
                        })
                    });
                    const result = await response.json();
                    if (result.success) {
                        console.log('✅ LLM配置更新成功:', selectedModel);
                        this.showNotification(`模型已切换为: ${selectedModel}`);
                    }
                } catch (error) {
                    console.error('❌ LLM配置更新失败:', error);
                }
            });
            console.log('✅ 模型选择器事件已绑定');
        } else {
            console.warn('⚠️ 模型选择器未找到');
        }
        
        this.isInitialized = true;
        console.log('✅✅✅ 聊天管理器初始化完成！所有按钮已绑定事件');
        
        // 测试：尝试触发一个测试点击
        setTimeout(() => {
            console.log('🧪 测试：检查按钮是否可点击');
            const testBtn = document.getElementById('play-btn');
            if (testBtn) {
                console.log('✅ 发送按钮元素存在');
                // 尝试手动触发点击事件测试
                testBtn.style.cursor = 'pointer';
                console.log('✅ 设置cursor为pointer');
            }
        }, 500);
    }
    
    stopMessage() {
        // 停止当前消息处理
        console.log('停止消息处理');
    }
    
    openModule(module) {
        const moduleNames = {
            'chat': '智能聊天',
            'rag': 'RAG知识库',
            'erp': 'ERP全流程',
            'content': '内容创作',
            'trend': '趋势分析',
            'stock': '股票量化',
            'operations': '运营·财务',
            'coding': 'AI编程助手',
            'workplan': '工作计划',
            'websearch': '网络搜索',
            'translation': '多语言翻译',
            'filegen': '文件生成'
        };
        
        const moduleName = moduleNames[module] || module;
        this.addSystemMessage(`正在打开"${moduleName}"模块...`, '实际使用中，这里会打开对应的二级界面。');
        
        // 实际打开模块的逻辑
        if (module === 'rag') {
            window.open('http://localhost:8011/rag-management', '_blank');
        } else if (module === 'erp') {
            window.open('http://localhost:8012', '_blank');
        }
        // 其他模块...
    }
    
    addSystemMessage(message, note = null) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-item system-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const messageP = document.createElement('p');
        messageP.textContent = message;
        contentDiv.appendChild(messageP);
        
        if (note) {
            const noteP = document.createElement('p');
            noteP.className = 'message-note';
            noteP.textContent = note;
            contentDiv.appendChild(noteP);
        }
        
        messageDiv.appendChild(contentDiv);
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        const now = new Date();
        timeSpan.textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        messageDiv.appendChild(timeSpan);
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;

        // 显示用户消息
        this.addMessage('user', message, {});
        input.value = '';

        // 发送到后端
        try {
            let result;
            try {
                const response = await fetch(`${API_BASE}/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: message,
                        input_type: 'text',
                        context: this.currentContext
                    })
                });

                if (response.ok) {
                    result = await response.json();
                } else {
                    throw new Error('API响应错误');
                }
            } catch (error) {
                console.warn('后端API不可用，使用模拟响应:', error);
                // 使用模拟响应
                result = {
                    success: true,
                    response: `收到您的消息："${message}"\n\n（后端API当前不可用，这是模拟响应）`,
                    response_time: 0.5
                };
            }
            
            if (result.success) {
                const messageDiv = this.addMessage('assistant', result.response, { module: '智能助手' });
                
                // 更新上下文
                if (result.rag_retrievals) {
                    this.currentContext.rag_retrievals = result.rag_retrievals;
                }
                
                // 显示响应时间（2秒目标）
                if (result.response_time) {
                    const responseTime = result.response_time;
                    console.log(`响应时间: ${responseTime.toFixed(2)}秒`);
                    
                    // 如果超过2秒，显示警告
                    if (responseTime > 2.0) {
                        this.showWarning(`响应时间 ${responseTime.toFixed(2)}秒，超过2秒目标`);
                    }
                    
                    // 显示响应时间提示
                    const timeIndicator = document.createElement('span');
                    timeIndicator.className = 'response-time';
                    timeIndicator.textContent = `${responseTime.toFixed(2)}s`;
                    timeIndicator.style.color = responseTime > 2.0 ? '#f56c6c' : '#67c23a';
                    timeIndicator.style.fontSize = '12px';
                    timeIndicator.style.marginLeft = '10px';
                    messageDiv.appendChild(timeIndicator);
                }
                
                // 如果创建了备忘录，显示提示
                if (result.memo_created) {
                    this.showNotification('📝 已自动创建备忘录');
                }
                
                // 可选：自动语音输出（如果用户启用）
                if (localStorage.getItem('auto_voice_output') === 'true') {
                    this.synthesizeAndPlay(result.response);
                }
            } else {
                this.addMessage('assistant', `错误: ${result.error || '未知错误'}`);
            }
        } catch (error) {
            console.error('发送消息失败:', error);
            this.addMessage('assistant', `发送失败: ${error.message}`);
        }
    }

    addMessage(role, content, options = {}) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        
        if (role === 'user') {
            messageDiv.className = 'message-item user-message';
        } else if (role === 'assistant') {
            messageDiv.className = 'message-item agent-message';
        } else {
            messageDiv.className = 'message-item system-message';
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // 如果是助手消息，添加模块标识
        if (role === 'assistant' && options.module) {
            const headerDiv = document.createElement('div');
            headerDiv.className = 'message-header';
            const moduleSpan = document.createElement('span');
            moduleSpan.className = 'message-module';
            moduleSpan.textContent = options.module;
            headerDiv.appendChild(moduleSpan);
            
            const timeSpan = document.createElement('span');
            timeSpan.className = 'message-time';
            const now = new Date();
            timeSpan.textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
            headerDiv.appendChild(timeSpan);
            
            messageDiv.appendChild(headerDiv);
        }
        
        // 添加文本内容
        const textP = document.createElement('p');
        textP.textContent = content;
        contentDiv.appendChild(textP);
        
        // 如果是语音消息，添加播放按钮
        if (options.audioUrl) {
            const audioPlayer = document.createElement('audio');
            audioPlayer.src = options.audioUrl;
            audioPlayer.controls = true;
            audioPlayer.style.marginTop = '10px';
            contentDiv.appendChild(audioPlayer);
        }
        
        // 如果是助手消息，添加语音播放按钮
        if (role === 'assistant' && content.length > 10) {
            const voiceBtn = document.createElement('button');
            voiceBtn.className = 'voice-play-btn';
            voiceBtn.textContent = '🔊';
            voiceBtn.title = '播放语音';
            voiceBtn.onclick = () => this.synthesizeAndPlay(content);
            voiceBtn.style.marginLeft = '10px';
            voiceBtn.style.cursor = 'pointer';
            voiceBtn.style.background = 'none';
            voiceBtn.style.border = 'none';
            voiceBtn.style.color = '#4ec9b0';
            contentDiv.appendChild(voiceBtn);
        }
        
        messageDiv.appendChild(contentDiv);
        
        // 添加时间戳（如果没有header）
        if (!options.module) {
            const timeSpan = document.createElement('span');
            timeSpan.className = 'message-time';
            const now = new Date();
            timeSpan.textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
            messageDiv.appendChild(timeSpan);
        }
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.messages.push({ role, content, timestamp: new Date(), options });
        return messageDiv;
    }
    
    async synthesizeAndPlay(text) {
        try {
            const response = await fetch(`${API_BASE}/voice/synthesize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    language: 'zh-CN',
                    speed: 1.0,
                    pitch: 1.0
                })
            });
            
            const result = await response.json();
            
            if (result.audio_data) {
                // 将base64音频数据转换为Blob URL
                const binaryString = atob(result.audio_data);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                const blob = new Blob([bytes], { type: 'audio/mp3' });
                const audioUrl = URL.createObjectURL(blob);
                
                // 播放音频
                const audio = new Audio(audioUrl);
                audio.play();
                
                audio.onended = () => {
                    URL.revokeObjectURL(audioUrl);
                };
            }
        } catch (error) {
            console.error('语音合成失败:', error);
        }
    }
    
    showNotification(message) {
        // 显示非交互类信息弹窗
        const modal = document.getElementById('modal-overlay');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        
        modalTitle.textContent = '通知';
        modalBody.textContent = message;
        modal.style.display = 'flex';
        
        // 3秒后自动关闭
        setTimeout(() => {
            modal.style.display = 'none';
        }, 3000);
    }
    
    showWarning(message) {
        console.warn(message);
        // 可以添加警告提示UI
    }

    async startVoiceInput() {
        const voiceBtn = document.getElementById('voice-btn');
        const chatInput = document.getElementById('chat-input');
        
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            alert('您的浏览器不支持语音识别功能');
            return;
        }
        
        const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new Recognition();
        recognition.lang = 'zh-CN';
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onstart = () => {
            voiceBtn.textContent = '🔴';
            voiceBtn.style.color = 'red';
            chatInput.placeholder = '正在聆听...';
        };
        
        recognition.onresult = async (event) => {
            const transcript = event.results[0][0].transcript;
            chatInput.value = transcript;
            chatInput.placeholder = '输入消息... (支持语音、文件、搜索)';
            
            // 可选：发送到后端进行二次识别和优化
            try {
                const response = await fetch(`${API_BASE}/voice/recognize`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ audio_text: transcript, language: 'zh-CN' })
                });
                const result = await response.json();
                if (result.text && result.text !== transcript) {
                    chatInput.value = result.text;
                }
            } catch (error) {
                console.error('语音识别优化失败:', error);
            }
        };
        
        recognition.onerror = (event) => {
            console.error('语音识别错误:', event.error);
            alert(`语音识别失败: ${event.error}`);
            voiceBtn.textContent = '🎤';
            voiceBtn.style.color = '';
            chatInput.placeholder = '输入消息... (支持语音、文件、搜索)';
        };
        
        recognition.onend = () => {
            voiceBtn.textContent = '🎤';
            voiceBtn.style.color = '';
            chatInput.placeholder = '输入消息... (支持语音、文件、搜索)';
        };
        
        recognition.start();
    }

    toggleFileUpload() {
        // 创建文件输入
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.multiple = true;
        fileInput.accept = '*/*';
        fileInput.style.display = 'none';
        fileInput.addEventListener('change', (e) => {
            this.handleFileUpload(e);
            document.body.removeChild(fileInput);
        });
        document.body.appendChild(fileInput);
        fileInput.click();
    }
    
    async handleFileUpload(event) {
        const files = Array.from(event.target.files);
        for (const file of files) {
            await this.uploadFile(file);
        }
    }
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            this.addMessage('system', `文件 "${file.name}" 上传成功`);
        } catch (error) {
            console.error('文件上传失败:', error);
            this.addMessage('system', `文件 "${file.name}" 上传失败: ${error.message}`);
        }
    }

    async toggleSearchMode() {
        const chatInput = document.getElementById('chat-input');
        const currentText = chatInput.value.trim();
        
        if (!currentText) {
            chatInput.placeholder = '输入搜索关键词...';
            return;
        }
        
        // 执行搜索
        try {
            const response = await fetch(`${API_BASE}/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: currentText,
                    search_type: 'web',
                    max_results: 10
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.results && result.results.length > 0) {
                let searchResults = `🔍 搜索结果 (${result.total}条):\n\n`;
                result.results.slice(0, 5).forEach((item, index) => {
                    searchResults += `${index + 1}. ${item.title}\n   ${item.snippet}\n   ${item.url}\n\n`;
                });
                this.addMessage('assistant', searchResults);
            } else {
                this.addMessage('assistant', '未找到相关搜索结果');
            }
        } catch (error) {
            console.error('搜索失败:', error);
            this.addMessage('assistant', `搜索失败: ${error.message}`);
        }
    }
    
    async translateText() {
        const chatInput = document.getElementById('chat-input');
        const text = chatInput.value.trim();
        
        if (!text) {
            alert('请先输入要翻译的文本');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/translate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    target_lang: 'zh',
                    source_lang: null  // 自动检测
                })
            });
            
            const result = await response.json();
            
            if (result.translated_text) {
                this.addMessage('assistant', 
                    `🌐 翻译结果:\n原文 (${result.source_language}): ${result.original_text}\n译文 (${result.target_language}): ${result.translated_text}`
                );
            } else {
                this.addMessage('assistant', `翻译失败: ${result.error || '未知错误'}`);
            }
        } catch (error) {
            console.error('翻译失败:', error);
            this.addMessage('assistant', `翻译失败: ${error.message}`);
        }
    }
    
    async generateFile() {
        const chatInput = document.getElementById('chat-input');
        const content = chatInput.value.trim();
        
        if (!content) {
            alert('请先输入要生成文件的内容');
            return;
        }
        
        // 显示文件类型选择对话框
        const fileType = prompt('请选择文件类型:\n1. word\n2. excel\n3. pdf\n4. ppt', 'word');
        
        if (!fileType) return;
        
        try {
            const response = await fetch(`${API_BASE}/generate/file`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file_type: fileType,
                    content: content,
                    title: '生成的文件'
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.file_data_base64) {
                // 下载文件
                const binaryString = atob(result.file_data_base64);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                const blob = new Blob([bytes], { type: `application/${result.format}` });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = result.filename;
                a.click();
                URL.revokeObjectURL(url);
                
                this.addMessage('assistant', `✅ 文件 "${result.filename}" 生成成功！`);
            } else {
                this.addMessage('assistant', `文件生成失败: ${result.error || '未知错误'}`);
            }
        } catch (error) {
            console.error('文件生成失败:', error);
            this.addMessage('assistant', `文件生成失败: ${error.message}`);
        }
    }
}

// 初始化聊天管理器 - 延迟到DOM加载完成后
// 注意：main.js也会初始化，这里只作为备用
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.chatManager) {
            window.chatManager = new ChatManager();
        }
    });
} else {
    if (!window.chatManager) {
        window.chatManager = new ChatManager();
    }
}

