/**
 * AI-STACK 超级Agent - 全新界面应用逻辑
 */

const API_BASE = '/api/super-agent';

class App {
    constructor() {
        this.messages = [];
        this.currentModule = null;
        this.isInitialized = false;
        this.latestSecurityEventId = null;
        
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
        
        // 延迟一点确保DOM完全加载
        setTimeout(() => {
            this.bindAllEvents();
        }, 100);
    }
    
    bindAllEvents() {
        // 发送按钮 - 多重绑定确保可靠
        const sendBtn = document.getElementById('send-btn');
        if (sendBtn) {
            // 清除旧的事件监听器
            sendBtn.onclick = null;
            const newSendBtn = sendBtn.cloneNode(true);
            sendBtn.parentNode.replaceChild(newSendBtn, sendBtn);
            
            // 绑定新事件
            newSendBtn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('✅✅✅ 发送按钮被点击 (onclick)');
                this.sendMessage();
            };
            newSendBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('✅✅✅ 发送按钮被点击 (addEventListener)');
                this.sendMessage();
            });
            console.log('✅ 发送按钮已绑定');
        } else {
            console.error('❌ 发送按钮未找到');
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
        
        // 工具按钮 - 多重绑定
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            voiceBtn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('✅✅✅ 语音按钮被点击');
                this.startVoiceInput();
            };
            voiceBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('✅✅✅ 语音按钮被点击 (addEventListener)');
                this.startVoiceInput();
            });
        }
        
        const fileBtn = document.getElementById('file-btn');
        if (fileBtn) {
            fileBtn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('✅✅✅ 文件按钮被点击');
                this.uploadFile();
            };
            fileBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('✅✅✅ 文件按钮被点击 (addEventListener)');
                this.uploadFile();
            });
        }
        
        const searchBtn = document.getElementById('search-btn');
        if (searchBtn) {
            searchBtn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('✅✅✅ 搜索按钮被点击');
                this.toggleSearch();
            };
            searchBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('✅✅✅ 搜索按钮被点击 (addEventListener)');
                this.toggleSearch();
            });
        }
        
        // 导航按钮 - 多重绑定
        const navButtons = document.querySelectorAll('.nav-btn');
        console.log(`找到 ${navButtons.length} 个导航按钮`);
        navButtons.forEach((btn, index) => {
            const module = btn.dataset.module;
            
            // 使用onclick
            btn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log(`✅✅✅ 导航按钮被点击 (onclick): ${module}`);
                this.switchModule(module);
            };
            
            // 使用addEventListener
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log(`✅✅✅ 导航按钮被点击 (addEventListener): ${module}`);
                this.switchModule(module);
            });
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
        const quickTrial = document.getElementById('quick-trial');
        if (quickTrial) {
            const handler = async () => {
                await this.openTrialDialog();
            };
            quickTrial.onclick = handler;
            quickTrial.addEventListener('click', handler);
        }
        const quickDouyin = document.getElementById('quick-douyin');
        if (quickDouyin) {
            const handler = async () => {
                await this.openDouyinDraftDialog();
            };
            quickDouyin.onclick = handler;
            quickDouyin.addEventListener('click', handler);
        }
        const quickCursor = document.getElementById('quick-cursor');
        if (quickCursor) {
            const handler = async () => {
                await this.cursorQuickActions();
            };
            quickCursor.onclick = handler;
            quickCursor.addEventListener('click', handler);
        }

        // 终端运行绑定
        const termRun = document.getElementById('terminal-run');
        const termClear = document.getElementById('terminal-clear');
        const termHistoryBtn = document.getElementById('terminal-history-btn');
        if (termRun) {
            const handler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.runTerminalCommand();
            };
            termRun.onclick = handler;
            termRun.addEventListener('click', handler);
        }
        if (termClear) {
            const handler = (e) => {
                e.preventDefault();
                const out = document.getElementById('terminal-output');
                if (out) out.textContent = '';
            };
            termClear.onclick = handler;
            termClear.addEventListener('click', handler);
        }
        if (termHistoryBtn) {
            const handler = async (e) => {
                e.preventDefault();
                await this.showTerminalHistory();
            };
            termHistoryBtn.onclick = handler;
            termHistoryBtn.addEventListener('click', handler);
        }

        const securityRefreshBtn = document.getElementById('terminal-security-refresh');
        if (securityRefreshBtn) {
            const handler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.updateTerminalSecurity(true);
            };
            securityRefreshBtn.onclick = handler;
            securityRefreshBtn.addEventListener('click', handler);
        }
        
        // 模型选择器
        const modelSelector = document.getElementById('model-selector');
        if (modelSelector) {
            modelSelector.addEventListener('change', (e) => this.changeModel(e.target.value));
        }
        
        // 更新系统状态
        this.updateSystemStatus();
        setInterval(() => this.updateSystemStatus(), 5000);
        this.updateTerminalSecurity(true);
        setInterval(() => this.updateTerminalSecurity(), 4000);
        
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
        const loadingId = this.addMessage('assistant', this.searchMode ? '正在搜索...' : '正在思考...', true);
        
        try {
            let response;
            let result;
            
            // 如果是搜索模式，或消息包含搜索关键词，执行搜索
            if (this.searchMode || this.isSearchQuery(message)) {
                // 执行网络搜索
                response = await fetch(`${API_BASE}/search`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        query: message,
                        search_type: 'web',
                        max_results: 10
                    })
                });
                
                if (response.ok) {
                    const searchResult = await response.json();
                    this.removeMessage(loadingId);
                    
                    if (searchResult.success && searchResult.results && searchResult.results.length > 0) {
                        // 格式化搜索结果
                        let searchContent = `🔍 搜索"${message}"找到 ${searchResult.total || searchResult.results.length} 条结果：\n\n`;
                        searchResult.results.slice(0, 5).forEach((item, index) => {
                            searchContent += `${index + 1}. ${item.title || item.snippet || '无标题'}\n`;
                            if (item.snippet) {
                                searchContent += `   ${item.snippet.substring(0, 100)}...\n`;
                            }
                            if (item.url) {
                                searchContent += `   链接: ${item.url}\n`;
                            }
                            searchContent += '\n';
                        });
                        
                        this.addMessage('assistant', searchContent);
                        this.addActivity('🔍', `搜索: ${message}`);
                        
                        // 同时发送到聊天API，让AI基于搜索结果生成回复
                        const chatResponse = await fetch(`${API_BASE}/chat`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                message: `基于以下搜索结果回答问题：\n\n${searchContent}\n\n问题：${message}`,
                                input_type: 'search',
                                context: { search_results: searchResult.results }
                            })
                        });
                        
                        if (chatResponse.ok) {
                            const chatResult = await chatResponse.json();
                            if (chatResult.success) {
                                this.addMessage('assistant', `\n\n💡 AI分析：\n${chatResult.response}`);
                            }
                        }
                    } else {
                        this.addMessage('assistant', `未找到相关搜索结果。${searchResult.error || ''}`);
                    }
                } else {
                    throw new Error(`搜索请求失败: HTTP ${response.status}`);
                }
            } else {
                // 正常聊天模式
                response = await fetch(`${API_BASE}/chat`, {
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
                    result = await response.json();
                    
                    // 移除加载消息
                    this.removeMessage(loadingId);
                    
                    // 显示回复
                    if (result.success) {
                        this.addMessage('assistant', result.response);
                        this.addActivity('💬', '收到AI回复');
                        
                        // 如果TTS已启用，播放语音
                        if (this.ttsEnabled) {
                            this.playTTS(result.response, this.ttsLanguage);
                        }
                        
                        // RAG双检索摘要提示
                        if (result.rag_retrievals) {
                            const firstCount = (result.rag_retrievals.first?.knowledge?.length) || (result.rag_retrievals.first?.count) || 0;
                            const secondExp = (result.rag_retrievals.second?.experience?.length) || 0;
                            const secondCases = (result.rag_retrievals.second?.similar_cases?.length) || 0;
                            const secondBest = (result.rag_retrievals.second?.best_practices?.length) || 0;
                            const summary = `📚 RAG检索摘要：首检${firstCount}条；二检 经验${secondExp} / 案例${secondCases} / 最佳实践${secondBest}`;
                            this.addMessage('assistant', summary);
                        }

                        // 检查是否需要显示弹窗（如备忘录创建）
                        if (result.memo_created && window.modalSystem) {
                            window.modalSystem.showSystemNotification(
                                `已自动创建备忘录：${result.memo_info?.title || '重要信息'}`,
                                'success'
                            );
                        }
                        
                        // 检查是否需要显示任务计划确认对话框
                        if (result.task_plan_created && result.task_plan && window.confirmationSystem) {
                            // 延迟显示，确保用户看到回复
                            setTimeout(() => {
                                window.confirmationSystem.showTaskPlanConfirmation(result.task_plan);
                            }, 1000);
                        }
                    } else {
                        this.addMessage('assistant', `错误: ${result.error || '未知错误'}`);
                    }
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            }
        } catch (error) {
            console.error('发送消息失败:', error);
            this.removeMessage(loadingId);
            this.addMessage('assistant', `发送失败: ${error.message}\n\n（请检查后端服务是否正常运行）`);
        }
    }
    
    isSearchQuery(message) {
        // 检测是否是搜索查询
        const searchKeywords = ['搜索', '查找', '找', 'search', 'find', '什么是', '什么是', '如何', '怎么', '？', '?'];
        return searchKeywords.some(keyword => message.includes(keyword)) || message.length < 20;
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
        } else if (module === 'rag-tools') {
            window.open('erp_bpmn.html'.replace('erp_bpmn','rag_tools'), '_blank');
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
    
    // 语音相关状态
    recognition = null;
    isListening = false;
    ttsEnabled = false;
    ttsLanguage = 'zh-CN';
    ttsSpeed = 1.0;
    
    startVoiceInput() {
        console.log('🎤 启动语音输入');
        
        // 检查浏览器支持
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.addMessage('assistant', '❌ 您的浏览器不支持语音识别功能。请使用Chrome、Edge或Safari浏览器。');
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // 配置
        this.recognition.lang = this.ttsLanguage;
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        
        // 开始识别
        this.recognition.onstart = () => {
            this.isListening = true;
            const voiceBtn = document.getElementById('voice-btn');
            if (voiceBtn) {
                voiceBtn.style.background = 'var(--danger-color)';
                voiceBtn.textContent = '🎤 正在聆听...';
            }
            this.addMessage('assistant', '🎤 正在聆听，请说话...', true);
        };
        
        // 识别结果
        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log('语音识别结果:', transcript);
            
            // 将识别结果填入输入框
            const input = document.getElementById('chat-input');
            if (input) {
                input.value = transcript;
            }
            
            // 自动发送消息
            this.sendMessage();
        };
        
        // 识别结束
        this.recognition.onend = () => {
            this.isListening = false;
            const voiceBtn = document.getElementById('voice-btn');
            if (voiceBtn) {
                voiceBtn.style.background = '';
                voiceBtn.textContent = '🎤';
            }
        };
        
        // 错误处理
        this.recognition.onerror = (event) => {
            console.error('语音识别错误:', event.error);
            this.addMessage('assistant', `❌ 语音识别失败: ${event.error}`);
            this.isListening = false;
            const voiceBtn = document.getElementById('voice-btn');
            if (voiceBtn) {
                voiceBtn.style.background = '';
                voiceBtn.textContent = '🎤';
            }
        };
        
        // 开始识别
        try {
            this.recognition.start();
        } catch (error) {
            console.error('启动语音识别失败:', error);
            this.addMessage('assistant', '❌ 启动语音识别失败，请稍后重试。');
        }
    }
    
    // TTS语音播放
    async playTTS(text, language = null) {
        if (!this.ttsEnabled) {
            return;
        }
        
        language = language || this.ttsLanguage;
        
        try {
            // 优先使用浏览器Web Speech API（免费且无需后端）
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = language;
                utterance.rate = this.ttsSpeed;
                utterance.volume = 1.0;
                
                // 选择语音
                const voices = speechSynthesis.getVoices();
                const targetVoice = voices.find(v => v.lang.startsWith(language.split('-')[0]));
                if (targetVoice) {
                    utterance.voice = targetVoice;
                }
                
                speechSynthesis.speak(utterance);
                return;
            }
            
            // 备用：使用后端TTS服务
            const response = await fetch(`${API_BASE}/voice/synthesize`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    language: language,
                    speed: this.ttsSpeed,
                    pitch: 1.0
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.audio_data) {
                    // 播放音频
                    const audio = new Audio(`data:audio/${result.format || 'mp3'};base64,${result.audio_data}`);
                    audio.play();
                }
            }
        } catch (error) {
            console.error('TTS播放失败:', error);
        }
    }
    
    // 切换TTS开关
    toggleTTS() {
        this.ttsEnabled = !this.ttsEnabled;
        const ttsBtn = document.getElementById('tts-btn');
        if (ttsBtn) {
            ttsBtn.style.background = this.ttsEnabled ? 'var(--success-color)' : '';
            ttsBtn.textContent = this.ttsEnabled ? '🔊' : '🔇';
        }
        
        // 保存设置到localStorage
        localStorage.setItem('ttsEnabled', this.ttsEnabled.toString());
        localStorage.setItem('ttsLanguage', this.ttsLanguage);
        localStorage.setItem('ttsSpeed', this.ttsSpeed.toString());
        
        this.addMessage('assistant', this.ttsEnabled ? '✅ 语音播放已开启' : '🔇 语音播放已关闭');
    }
    
    // 加载TTS设置
    loadTTSSettings() {
        const savedEnabled = localStorage.getItem('ttsEnabled');
        const savedLanguage = localStorage.getItem('ttsLanguage');
        const savedSpeed = localStorage.getItem('ttsSpeed');
        
        if (savedEnabled !== null) {
            this.ttsEnabled = savedEnabled === 'true';
        }
        if (savedLanguage) {
            this.ttsLanguage = savedLanguage;
        }
        if (savedSpeed) {
            this.ttsSpeed = parseFloat(savedSpeed);
        }
        
        // 更新按钮状态
        const ttsBtn = document.getElementById('tts-btn');
        if (ttsBtn) {
            ttsBtn.style.background = this.ttsEnabled ? 'var(--success-color)' : '';
            ttsBtn.textContent = this.ttsEnabled ? '🔊' : '🔇';
        }
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
    
    searchMode = false;
    
    toggleSearch() {
        console.log('🔍 切换搜索模式');
        this.searchMode = !this.searchMode;
        const input = document.getElementById('chat-input');
        const searchBtn = document.getElementById('search-btn');
        
        if (this.searchMode) {
            input.placeholder = '输入搜索关键词...';
            if (searchBtn) {
                searchBtn.style.background = 'var(--primary-color)';
                searchBtn.style.color = 'white';
            }
        } else {
            input.placeholder = '输入您的问题或指令...';
            if (searchBtn) {
                searchBtn.style.background = '';
                searchBtn.style.color = '';
            }
        }
    }
    
    createMemo() {
        console.log('📝 创建备忘录');
        this.addMessage('assistant', '备忘录功能开发中...');
    }
    
    createTask() {
        console.log('📋 新建任务');
        this.addMessage('assistant', '任务管理功能开发中...');
    }
    
    async runTerminalCommand() {
        const cmdInput = document.getElementById('terminal-command');
        const cwdInput = document.getElementById('terminal-cwd');
        const out = document.getElementById('terminal-output');
        const command = (cmdInput?.value || '').trim();
        const cwd = (cwdInput?.value || '').trim() || null;
        if (!command) {
            this.addActivity('🛠️', '请输入命令');
            return;
        }
        if (out) {
            out.textContent += `\n$ ${command}\n`;
        }
        try {
            const resp = await fetch(`${API_BASE}/terminal/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command, timeout: 30, cwd })
            });
            if (resp.ok) {
                const result = await resp.json();
                if (out) {
                    if (result.stdout) out.textContent += result.stdout + '\n';
                    if (result.stderr) out.textContent += result.stderr + '\n';
                }
                this.addActivity(result.success ? '🖥️' : '⚠️', `终端：${command}`);
            } else {
                if (out) out.textContent += `执行失败：HTTP ${resp.status}\n`;
            }
        } catch (e) {
            if (out) out.textContent += `执行异常：${e.message}\n`;
        }
    }

    async openDouyinDraftDialog() {
        try {
            // 检查授权状态
            let r = await fetch(`${API_BASE}/douyin/status`);
            let s = await r.json();
            if (!s.authorized) {
                const go = confirm('抖音未授权，是否进行授权（模拟）？');
                if (go) {
                    const auth = await fetch(`${API_BASE}/douyin/begin-auth`, { method: 'POST' });
                    if (auth.ok) {
                        this.addMessage('assistant', '🎬 抖音授权完成（模拟）。');
                    }
                } else {
                    return;
                }
            }
            const title = prompt('输入草稿标题：', '我的视频草稿');
            if (!title) return;
            const content = prompt('输入草稿正文（用于合规检测）：', '');
            if (!content) return;
            const minOriginality = parseFloat(prompt('最低原创度（0-100，默认60）：', '60') || '60');

            const resp = await fetch(`${API_BASE}/douyin/create-draft`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title,
                    content,
                    tags: [],
                    references: [],
                    min_originality: isNaN(minOriginality) ? 60 : minOriginality,
                    block_sensitive: true
                })
            });
            const data = await resp.json();
            if (!resp.ok) {
                this.addMessage('assistant', `❌ 草稿创建失败：${data.detail || '未知错误'}`);
                return;
            }
            if (data.blocked) {
                this.addMessage('assistant', `⛔ 已拦截草稿发布：${data.reason}\n原创度：${data.compliance?.originality_percent}% 敏感词：${(data.compliance?.sensitive_hits||[]).join(',')}`);
                return;
            }
            this.addMessage('assistant', `✅ 草稿创建成功（模拟）：${data.draft?.draft_id}\n原创度：${data.compliance?.originality_percent}%`);
            this.addActivity('🎬', '抖音草稿已创建');
        } catch (e) {
            this.addMessage('assistant', `❌ 抖音草稿失败：${e.message}`);
        }
    }

    async cursorQuickActions() {
        try {
            const st = await (await fetch(`${API_BASE}/coding/cursor/status`)).json();
            if (!st.available) {
                this.addMessage('assistant', '❌ 未检测到Cursor可用，请确认本机已安装。');
                return;
            }
            const action = prompt('Cursor操作：\n1. 打开文件\n2. 打开项目\n3. 代码补全\n4. 语法检查\n（输入数字）', '1');
            if (!action) return;
            if (action === '1') {
                const fp = prompt('输入文件绝对路径：', '');
                if (!fp) return;
                const ln = parseInt(prompt('行号（可选）', ''), 10);
                const r = await fetch(`${API_BASE}/coding/cursor/open-file`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_path: fp, line_number: isNaN(ln) ? null : ln })
                });
                const data = await r.json();
                this.addMessage('assistant', r.ok ? `✅ ${data.message || '已打开'}` : `❌ 打开失败：${data.detail || '未知错误'}`);
            } else if (action === '2') {
                const pp = prompt('输入项目根目录绝对路径：', '');
                if (!pp) return;
                const r = await fetch(`${API_BASE}/coding/cursor/open-project`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ project_path: pp })
                });
                const data = await r.json();
                this.addMessage('assistant', r.ok ? `✅ ${data.message || '项目已打开'}` : `❌ 打开失败：${data.detail || '未知错误'}`);
            } else if (action === '3') {
                const fp = prompt('文件路径：', '');
                const ln = parseInt(prompt('行号：', '1'), 10);
                const col = parseInt(prompt('列号：', '1'), 10);
                if (!fp || isNaN(ln) || isNaN(col)) return;
                const r = await fetch(`${API_BASE}/coding/cursor/completion`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_path: fp, line_number: ln, column: col })
                });
                const data = await r.json();
                if (r.ok) {
                    const suggestions = (data.suggestions || []).map(s => s.text).join(', ');
                    this.addMessage('assistant', `💡 补全建议：${suggestions || '无'}`);
                } else {
                    this.addMessage('assistant', `❌ 补全失败：${data.detail || '未知错误'}`);
                }
            } else if (action === '4') {
                const fp = prompt('文件路径：', '');
                if (!fp) return;
                const r = await fetch(`${API_BASE}/coding/cursor/detect-errors`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_path: fp })
                });
                const data = await r.json();
                if (r.ok) {
                    this.addMessage('assistant', `🔍 错误：${data.error_count}，警告：${data.warning_count}`);
                } else {
                    this.addMessage('assistant', `❌ 检查失败：${data.detail || '未知错误'}`);
                }
            }
        } catch (e) {
            this.addMessage('assistant', `❌ Cursor操作失败：${e.message}`);
        }
    }

    async showTerminalHistory() {
        const out = document.getElementById('terminal-output');
        try {
            const resp = await fetch(`${API_BASE}/terminal/history?limit=10`);
            if (!resp.ok) return;
            const payload = await resp.json();
            const history = payload.history || [];
            if (out) {
                out.textContent += '\n== 命令历史 ==\n';
                history.forEach(h => {
                    out.textContent += `[${h.timestamp}] ${h.command} (${h.success ? '成功' : '失败'})\n`;
                });
            }
        } catch (e) {
            if (out) out.textContent += `获取历史失败：${e.message}\n`;
        }
    }

    async generateFile() {
        console.log('📄 生成文件');
        
        // 显示文件生成对话框
        const fileType = prompt('请选择文件类型：\n1. Word文档 (word)\n2. Excel表格 (excel)\n3. PDF文档 (pdf)\n4. PPT演示 (ppt)\n\n请输入类型名称：', 'word');
        
        if (!fileType) {
            return;
        }
        
        const content = prompt('请输入文件内容（Word/PDF支持Markdown，Excel需要JSON格式）：', '');
        
        if (!content) {
            this.addMessage('assistant', '文件生成已取消');
            return;
        }
        
        // 显示生成中消息
        const loadingId = this.addMessage('assistant', '正在生成文件...', true);
        
        try {
            const response = await fetch(`${API_BASE}/generate/file`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    file_type: fileType,
                    content: content,
                    title: `生成的文件_${new Date().toISOString().slice(0, 10)}`
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.removeMessage(loadingId);
                
                if (result.success) {
                    // 下载文件
                    if (result.file_data_base64) {
                        const binaryString = atob(result.file_data_base64);
                        const bytes = new Uint8Array(binaryString.length);
                        for (let i = 0; i < binaryString.length; i++) {
                            bytes[i] = binaryString.charCodeAt(i);
                        }
                        const blob = new Blob([bytes], { type: result.mime_type || 'application/octet-stream' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = result.filename || `file.${fileType === 'word' ? 'docx' : fileType === 'excel' ? 'xlsx' : fileType === 'pdf' ? 'pdf' : 'pptx'}`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                        
                        this.addMessage('assistant', `✅ 文件已生成并下载：${result.filename || 'file'}`);
                        this.addActivity('📄', `生成文件: ${fileType}`);
                        
                        // 显示成功弹窗
                        if (window.modalSystem) {
                            window.modalSystem.showTaskComplete(`生成${fileType}文件`);
                        }
                    } else {
                        this.addMessage('assistant', `✅ 文件已生成：${result.message || '成功'}`);
                    }
                } else {
                    this.addMessage('assistant', `❌ 文件生成失败: ${result.error || '未知错误'}`);
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('文件生成失败:', error);
            this.removeMessage(loadingId);
            this.addMessage('assistant', `❌ 文件生成失败: ${error.message}`);
        }
    }

    async openTrialDialog() {
        const mode = prompt('运营试算：\n1. 按周营收目标试算（输入金额）\n2. 按日产能试算（输入件数）\n\n请输入 1 或 2：', '1');
        if (!mode) return;
        const productCode = prompt('请输入产品编码（可选）：', '') || null;
        try {
            let body = { product_code: productCode };
            if (mode.trim() === '1') {
                const rev = prompt('请输入周营收目标金额（数字）：', '');
                if (!rev) return;
                body.target_weekly_revenue = parseFloat(rev);
            } else {
                const units = prompt('请输入目标日产量（件）：', '');
                if (!units) return;
                body.target_daily_units = parseInt(units, 10);
            }
            const resp = await fetch(`${API_BASE}/erp/trial/calc`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (resp.ok) {
                const data = await resp.json();
                let msg = '🧮 试算结果：\n';
                if (data.trial?.type === 'by_weekly_revenue') {
                    msg += `建议日产量：${data.trial.required_units_per_day} 件（按单价 ${data.product?.unit_price} 元，7天周）`;
                } else if (data.trial?.type === 'by_daily_units') {
                    msg += `预计周营收：¥${data.trial.expected_weekly_revenue}`;
                } else if (data.trial?.type === 'by_order_quantity') {
                    msg += `按订单数量倒算建议日产量：${data.trial.required_units_per_day} 件（可用天数 ${data.trial.assumptions?.available_days}）`;
                } else {
                    msg += data.trial?.message || '参数不足，无法计算';
                }
                this.addMessage('assistant', msg);
                this.addActivity('🧮', '运营试算完成');
            } else {
                this.addMessage('assistant', `❌ 试算失败：HTTP ${resp.status}`);
            }
        } catch (e) {
            this.addMessage('assistant', `❌ 试算失败：${e.message}`);
        }
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
            const response = await fetch(`${API_BASE}/resources/status`);
            if (response.ok) {
                const data = await response.json();
                
                // 检查资源问题并显示确认对话框
                if (data.alerts && data.alerts.length > 0 && window.confirmationSystem) {
                    for (const alert of data.alerts) {
                        if (alert.requires_confirmation && !alert.confirmed) {
                            // 显示资源调节确认对话框
                            const suggestion = {
                                id: alert.id || alert.type,
                                description: alert.message || alert.description,
                                expected_impact: alert.expected_impact || '改善资源使用情况',
                                risk_level: alert.severity || 'medium',
                                action: alert.action || 'adjust',
                                issue: {
                                    issue_type: alert.type,
                                    severity: alert.severity || 'medium',
                                    current_value: alert.current_value,
                                    threshold: alert.threshold
                                }
                            };
                            
                            await window.confirmationSystem.showResourceAdjustmentConfirmation(suggestion);
                            break; // 一次只显示一个确认对话框
                        }
                    }
                }
                
                // 更新CPU
                const cpuBar = document.getElementById('cpu-bar');
                const cpuValue = document.getElementById('cpu-value');
                if (cpuBar && cpuValue && data.cpu_percent !== undefined) {
                    const cpuPercent = Math.round(data.cpu_percent);
                    cpuBar.style.width = `${cpuPercent}%`;
                    cpuValue.textContent = `${cpuPercent}%`;
                    
                    // 资源告警弹窗
                    if (cpuPercent > 80 && window.modalSystem) {
                        window.modalSystem.showResourceAlert('CPU', cpuPercent, 80);
                    }
                }
                
                // 更新内存
                const memoryBar = document.getElementById('memory-bar');
                const memoryValue = document.getElementById('memory-value');
                if (memoryBar && memoryValue && data.memory_percent !== undefined) {
                    const memoryPercent = Math.round(data.memory_percent);
                    memoryBar.style.width = `${memoryPercent}%`;
                    memoryValue.textContent = `${memoryPercent}%`;
                    
                    // 资源告警弹窗
                    if (memoryPercent > 85 && window.modalSystem) {
                        window.modalSystem.showResourceAlert('内存', memoryPercent, 85);
                    }
                }
                
                // 更新磁盘
                const diskBar = document.getElementById('disk-bar');
                const diskValue = document.getElementById('disk-value');
                if (diskBar && diskValue && data.disk_percent !== undefined) {
                    const diskPercent = Math.round(data.disk_percent);
                    diskBar.style.width = `${diskPercent}%`;
                    diskValue.textContent = `${diskPercent}%`;
                    
                    // 资源告警弹窗
                    if (diskPercent > 90 && window.modalSystem) {
                        window.modalSystem.showResourceAlert('磁盘', diskPercent, 90);
                    }
                }
            }
        } catch (error) {
            // 静默失败，不影响主功能
        }
    }

    async updateTerminalSecurity(force = false) {
        const statusEl = document.getElementById('terminal-security-status');
        const listEl = document.getElementById('terminal-event-list');
        if (!statusEl || !listEl) return;

        try {
            const response = await fetch(`${API_BASE}/workflow/system-events?event_type=terminal_command&limit=5`);
            if (!response.ok) return;
            const payload = await response.json();
            const events = payload.events || [];
            listEl.innerHTML = '';

            if (events.length === 0) {
                statusEl.textContent = '待监控';
                statusEl.classList.remove('alert');
                listEl.innerHTML = '<div class="security-empty">暂无命令记录</div>';
                return;
            }

            const latest = events[0];
            statusEl.textContent = latest.success ? '安全' : '异常';
            statusEl.classList.toggle('alert', !latest.success);

            events.forEach((event) => {
                const item = document.createElement('div');
                item.className = `security-event ${event.success ? 'success' : 'error'}`;

                const header = document.createElement('div');
                header.className = 'event-header';
                const time = new Date(event.timestamp).toLocaleTimeString('zh-CN', { hour12: false });
                header.innerHTML = `<span>${time}</span><span>${event.data?.phase || ''}</span>`;

                const command = document.createElement('div');
                command.className = 'event-command';
                command.textContent = event.data?.command || '';

                const meta = document.createElement('div');
                meta.className = 'event-meta';
                const returnCode = event.data?.metadata?.return_code;
                const duration = event.data?.metadata?.duration;
                const extra = [
                    returnCode !== undefined ? `返回码 ${returnCode}` : null,
                    duration !== undefined ? `耗时 ${duration.toFixed(2)}s` : null,
                    event.error ? `错误: ${event.error}` : null
                ].filter(Boolean).join(' · ');
                meta.textContent = extra || '执行完成';

                item.appendChild(header);
                item.appendChild(command);
                item.appendChild(meta);
                listEl.appendChild(item);
            });

            const latestId = latest.event_id;
            if (latestId && latestId !== this.latestSecurityEventId) {
                this.latestSecurityEventId = latestId;
                if (!latest.success) {
                    const cmd = latest.data?.command || '未知命令';
                    this.addActivity('🛡️', `终端告警：${cmd}`);
                } else if (force) {
                    this.addActivity('🛡️', '终端已开始监控');
                }
            }
        } catch (error) {
            // 静默处理
        }
    }
}

// 初始化应用
const app = new App();
window.app = app; // 暴露到全局，方便调试

console.log('✅ 应用脚本已加载');

