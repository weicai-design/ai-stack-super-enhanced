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
        this.taskPage = 1;
        this.taskPageSize = 10;
        this.taskPageOrch = 1;
        this.taskPagePlan = 1;
        this.selectedPlanTaskIds = new Set();
        
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
        this.refreshTasks();
        setInterval(() => this.refreshTasks(), 7000);
        this.updateTerminalSecurity(true);
        setInterval(() => this.updateTerminalSecurity(), 4000);
        this.updateSecurityAudit();
        setInterval(() => this.updateSecurityAudit(), 8000);
        // 任务筛选按钮
        const filterBtn = document.getElementById('task-filter-apply');
        if (filterBtn) {
            const handler = (e) => { e.preventDefault(); this.refreshTasks(true); };
            filterBtn.onclick = handler;
            filterBtn.addEventListener('click', handler);
        }
        const resetBtn = document.getElementById('task-filter-reset');
        if (resetBtn) {
            const handler = (e) => {
                e.preventDefault();
                const q = document.getElementById('task-filter-q'); if (q) q.value = '';
                const s = document.getElementById('task-filter-status'); if (s) s.value = '';
                this.taskPage = 1;
                this.refreshTasks(true);
            };
            resetBtn.onclick = handler;
            resetBtn.addEventListener('click', handler);
        }
        // 分页
        const sizeSel = document.getElementById('task-page-size');
        if (sizeSel) {
            sizeSel.addEventListener('change', () => {
                this.taskPageSize = parseInt(sizeSel.value || '10', 10);
                this.taskPage = 1;
                this.refreshTasks(true);
            });
        }
        const prevBtn = document.getElementById('task-prev');
        const nextBtn = document.getElementById('task-next');
        if (prevBtn) prevBtn.onclick = (e) => { e.preventDefault(); if (this.taskPage > 1) { this.taskPage--; this.refreshTasks(true); } };
        if (nextBtn) nextBtn.onclick = (e) => { e.preventDefault(); this.taskPage++; this.refreshTasks(true); };
        // 批量操作
        const bulkSel = document.getElementById('task-bulk-select-all');
        const bulkClr = document.getElementById('task-bulk-clear');
        const bulkCfm = document.getElementById('task-bulk-confirm');
        const bulkExe = document.getElementById('task-bulk-execute');
        const bulkRetro = document.getElementById('task-bulk-retro');
        const bulkReject = document.getElementById('task-bulk-reject');
        const bulkDelete = document.getElementById('task-bulk-delete');
        if (bulkSel) bulkSel.onclick = (e) => { e.preventDefault(); this.bulkSelectCurrentPage(); };
        if (bulkClr) bulkClr.onclick = (e) => { e.preventDefault(); this.selectedPlanTaskIds.clear(); this.updateBulkCount(); this.refreshTasks(true); };
        if (bulkCfm) bulkCfm.onclick = async (e) => { e.preventDefault(); await this.bulkConfirm(true); };
        if (bulkExe) bulkExe.onclick = async (e) => { e.preventDefault(); await this.bulkExecute(); };
        if (bulkRetro) bulkRetro.onclick = async (e) => { e.preventDefault(); await this.bulkRetrospect(); };
        if (bulkReject) bulkReject.onclick = async (e) => { e.preventDefault(); await this.bulkReject(); };
        if (bulkDelete) bulkDelete.onclick = async (e) => { e.preventDefault(); await this.bulkDelete(); };
        
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
        } else if (module === 'rag-ingest') {
            window.open('rag_ingest.html', '_blank');
        } else if (module === 'stock-backtest') {
            window.open('stock_backtest.html', '_blank');
        } else if (module === 'bpmn-runtime') {
            window.open('bpmn_runtime.html', '_blank');
        } else if (module === 'erp-orders') {
            window.open('erp_orders.html', '_blank');
        } else if (module === 'erp-production') {
            window.open('erp_production.html', '_blank');
        } else if (module === 'erp-procurements') {
            window.open('erp_procurements.html', '_blank');
        } else if (module === 'erp-inventory') {
            window.open('erp_inventory.html', '_blank');
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

    async refreshTasks(force = false) {
        try {
            const listEl = document.getElementById('task-list');
            if (!listEl) return;
            // 并行拉取：编排器任务 + 规划任务
            const qEl = document.getElementById('task-filter-q');
            const sEl = document.getElementById('task-filter-status');
            const q = qEl ? (qEl.value || '').toLowerCase() : '';
            const statusFilter = sEl ? (sEl.value || '') : '';
            const planUrl = new URL(`${location.origin}${API_BASE}/planning/tasks`);
            if (statusFilter) planUrl.searchParams.set('status', statusFilter);
            const [rOrch, rPlan] = await Promise.all([
                fetch(`${API_BASE}/tasks`),
                fetch(planUrl.toString())
            ]);
            const orchPayload = await rOrch.json();
            const planPayload = await rPlan.json();
            // 过滤
            let orchTasks = orchPayload.tasks || [];
            let tasks = planPayload.tasks || [];
            if (q) {
                const contains = (txt) => (String(txt || '').toLowerCase().includes(q));
                orchTasks = orchTasks.filter(t => contains(t.task_id) || contains(t.title) || contains(t.status));
                tasks = tasks.filter(t => contains(t.id) || contains(t.title) || contains(t.description) || contains(t.status));
            }
            // 分页应用到每个区块
            const pageSize = this.taskPageSize || 10;
            const page = Math.max(1, this.taskPage || 1);
            const orchTotalPages = Math.max(1, Math.ceil(orchTasks.length / pageSize));
            const planTotalPages = Math.max(1, Math.ceil(tasks.length / pageSize));
            const totalPages = Math.max(orchTotalPages, planTotalPages);
            const pageInfo = document.getElementById('task-pageinfo');
            if (pageInfo) pageInfo.textContent = `第 ${Math.min(page, totalPages)} / ${totalPages} 页`;
            // 独立页码
            this.taskPageOrch = Math.min(Math.max(1, this.taskPageOrch), orchTotalPages);
            this.taskPagePlan = Math.min(Math.max(1, this.taskPagePlan), planTotalPages);
            const sliceByPage = (arr, p) => {
                const start = (p - 1) * pageSize;
                return arr.slice(start, start + pageSize);
            };
            const orchPage = sliceByPage(orchTasks, this.taskPageOrch);
            const planPage = sliceByPage(tasks, this.taskPagePlan);
            listEl.innerHTML = '';
            if (orchTasks.length === 0 && tasks.length === 0) {
                const empty = document.createElement('div');
                empty.className = 'activity-item';
                empty.textContent = '暂无任务';
                listEl.appendChild(empty);
                return;
            }
            // 编排器任务区
            const headerOrch = document.createElement('div');
            headerOrch.className = 'activity-item';
            headerOrch.style.fontWeight = '600';
            headerOrch.textContent = `编排器任务（第 ${this.taskPageOrch}/${orchTotalPages} 页）`;
            listEl.appendChild(headerOrch);
            // 分页控制（编排器）
            const orchPager = document.createElement('div');
            orchPager.className = 'activity-item';
            const orchPrev = document.createElement('button'); orchPrev.className='action-btn-small'; orchPrev.textContent='上一页';
            orchPrev.onclick = () => { if (this.taskPageOrch > 1) { this.taskPageOrch--; this.refreshTasks(true); } };
            const orchNext = document.createElement('button'); orchNext.className='action-btn-small'; orchNext.textContent='下一页';
            orchNext.onclick = () => { if (this.taskPageOrch < orchTotalPages) { this.taskPageOrch++; this.refreshTasks(true); } };
            orchPager.appendChild(orchPrev); orchPager.appendChild(orchNext);
            listEl.appendChild(orchPager);
            orchPage.forEach(t => {
                const item = document.createElement('div');
                item.className = 'activity-item';
                const icon = document.createElement('span');
                icon.className = 'activity-icon';
                icon.textContent = t.status === 'completed' ? '✅' : (t.status === 'blocked' ? '⛔' : '🧩');
                const text = document.createElement('span');
                text.className = 'activity-text';
                text.textContent = `${t.task_id || ''} ${t.title || ''}`;
                text.style.cursor = 'pointer';
                text.title = '点击查看任务详情';
                if (t.task_id) text.onclick = () => window.open(`task_detail.html?oid=${encodeURIComponent(t.task_id)}`, '_blank');
                const time = document.createElement('span');
                time.className = 'activity-time';
                time.textContent = t.updated_at ? new Date(t.updated_at).toLocaleTimeString('zh-CN', { hour12: false }) : '';
                item.appendChild(icon);
                item.appendChild(text);
                item.appendChild(time);
                // 状态彩色标签
                const statusTag = document.createElement('span');
                statusTag.className = 'tag';
                statusTag.textContent = t.status || 'unknown';
                statusTag.style.marginLeft = '8px';
                statusTag.style.border = '1px solid #333';
                statusTag.style.padding = '2px 6px';
                statusTag.style.borderRadius = '999px';
                statusTag.style.background = (t.status==='completed'?'#0b3d0b':t.status==='in_progress'?'#10345a':t.status==='blocked'?'#5a1010':'#262626');
                item.appendChild(statusTag);
                const actions = document.createElement('div');
                actions.style.marginTop = '4px';
                // 简易进度（基于执行历史步数推测）
                const hist = (t.metadata && Array.isArray(t.metadata.execution_history)) ? t.metadata.execution_history : [];
                const totalSteps = t.metadata && t.metadata.total_steps ? Number(t.metadata.total_steps) : null;
                let percent = null;
                if (totalSteps && totalSteps > 0) {
                    percent = Math.min(100, Math.floor((hist.length / totalSteps) * 100));
                } else if (hist.length > 0) {
                    percent = Math.min(95, hist.length * 20); // 估算
                }
                if (percent !== null) {
                    const barWrap = document.createElement('div');
                    barWrap.style.margin = '4px 0';
                    barWrap.style.background = '#1a1a1a';
                    barWrap.style.border = '1px solid #333';
                    barWrap.style.height = '8px';
                    barWrap.style.borderRadius = '4px';
                    const bar = document.createElement('div');
                    bar.style.height = '100%';
                    bar.style.width = `${percent}%`;
                    bar.style.background = '#7fbf4d';
                    bar.style.borderRadius = '4px';
                    barWrap.appendChild(bar);
                    actions.appendChild(barWrap);
                }
                const btnD = document.createElement('button');
                btnD.className = 'action-btn-small';
                btnD.textContent = '详情';
                btnD.onclick = () => window.open(`task_detail.html?oid=${encodeURIComponent(t.task_id)}`, '_blank');
                actions.appendChild(btnD);
                // 推送步骤（从规划任务导入或手动输入JSON）
                const btnPush = document.createElement('button');
                btnPush.className = 'action-btn-small';
                btnPush.textContent = '推送步骤';
                btnPush.onclick = () => this.pushStepsToOrchestratorInline(t.task_id);
                actions.appendChild(btnPush);
                item.appendChild(actions);
                listEl.appendChild(item);
            });
            // 规划任务区
            const headerPlan = document.createElement('div');
            headerPlan.className = 'activity-item';
            headerPlan.style.fontWeight = '600';
            headerPlan.textContent = `规划任务（第 ${this.taskPagePlan}/${planTotalPages} 页）`;
            listEl.appendChild(headerPlan);
            // 分页控制（规划）
            const planPager = document.createElement('div');
            planPager.className = 'activity-item';
            const planPrev = document.createElement('button'); planPrev.className='action-btn-small'; planPrev.textContent='上一页';
            planPrev.onclick = () => { if (this.taskPagePlan > 1) { this.taskPagePlan--; this.refreshTasks(true); } };
            const planNext = document.createElement('button'); planNext.className='action-btn-small'; planNext.textContent='下一页';
            planNext.onclick = () => { if (this.taskPagePlan < planTotalPages) { this.taskPagePlan++; this.refreshTasks(true); } };
            planPager.appendChild(planPrev); planPager.appendChild(planNext);
            listEl.appendChild(planPager);
            planPage.forEach(t => {
                const item = document.createElement('div');
                item.className = 'activity-item';
                // 勾选框（批量）
                const sel = document.createElement('input');
                sel.type = 'checkbox';
                sel.checked = this.selectedPlanTaskIds.has(t.id);
                sel.style.marginRight = '6px';
                sel.onchange = () => { if (sel.checked) { this.selectedPlanTaskIds.add(t.id); } else { this.selectedPlanTaskIds.delete(t.id); } this.updateBulkCount(); };
                item.appendChild(sel);
                const icon = document.createElement('span');
                icon.className = 'activity-icon';
                icon.textContent = t.status === 'completed' ? '✅' : (t.needs_confirmation ? '⏳' : '📋');
                const text = document.createElement('span');
                text.className = 'activity-text';
                text.textContent = `${t.id || ''} ${t.title || t.description || ''}`;
                if (t.id !== undefined) {
                    text.style.cursor = 'pointer';
                    text.title = '点击查看任务详情';
                    text.onclick = () => window.open(`task_detail.html?pid=${encodeURIComponent(t.id)}`, '_blank');
                }
                const time = document.createElement('span');
                time.className = 'activity-time';
                time.textContent = t.created_at ? new Date(t.created_at).toLocaleTimeString('zh-CN', { hour12: false }) : '';
                item.appendChild(icon);
                item.appendChild(text);
                item.appendChild(time);
                // 操作区
                const actions = document.createElement('div');
                actions.style.marginTop = '4px';
                // 状态彩色标签
                const statusTag2 = document.createElement('span');
                statusTag2.className = 'tag';
                statusTag2.textContent = t.status || 'unknown';
                statusTag2.style.marginLeft = '8px';
                statusTag2.style.border = '1px solid #333';
                statusTag2.style.padding = '2px 6px';
                statusTag2.style.borderRadius = '999px';
                statusTag2.style.background = (t.status==='completed'?'#0b3d0b':t.status==='in_progress'?'#10345a':t.status==='blocked'?'#5a1010':'#262626');
                actions.appendChild(statusTag2);
                // 进度条
                if (typeof t.progress === 'number') {
                    const barWrap = document.createElement('div');
                    barWrap.style.margin = '4px 0';
                    barWrap.style.background = '#1a1a1a';
                    barWrap.style.border = '1px solid #333';
                    barWrap.style.height = '8px';
                    barWrap.style.borderRadius = '4px';
                    const bar = document.createElement('div');
                    bar.style.height = '100%';
                    bar.style.width = `${Math.max(0, Math.min(100, t.progress))}%`;
                    bar.style.background = '#4c8bf5';
                    bar.style.borderRadius = '4px';
                    barWrap.appendChild(bar);
                    actions.appendChild(barWrap);
                }
                if (t.needs_confirmation && t.id !== undefined) {
                    const btnC = document.createElement('button');
                    btnC.className = 'action-btn-small';
                    btnC.textContent = '确认';
                    btnC.onclick = () => this.confirmTask(t.id, true);
                    const btnR = document.createElement('button');
                    btnR.className = 'action-btn-small';
                    btnR.textContent = '拒绝';
                    btnR.onclick = () => this.confirmTask(t.id, false);
                    actions.appendChild(btnC);
                    actions.appendChild(btnR);
                } else if ((t.status === 'pending' || t.status === 'created') && t.id !== undefined) {
                    const btnE = document.createElement('button');
                    btnE.className = 'action-btn-small';
                    btnE.textContent = '执行';
                    btnE.onclick = () => this.executeTask(t.id);
                    actions.appendChild(btnE);
                }
                // 详情（规划任务）
                {
                    const btnD = document.createElement('button');
                    btnD.className = 'action-btn-small';
                    btnD.textContent = '详情';
                    btnD.onclick = () => window.open(`task_detail.html?pid=${encodeURIComponent(t.id)}`, '_blank');
                    actions.appendChild(btnD);
                }
                if (t.status === 'completed' && t.id !== undefined) {
                    const btnRp = document.createElement('button');
                    btnRp.className = 'action-btn-small';
                    btnRp.textContent = '复盘';
                    btnRp.onclick = () => this.retrospectTask(t.id);
                    actions.appendChild(btnRp);
                }
                item.appendChild(actions);
                listEl.appendChild(item);
            });
        } catch (e) {
            // 静默
        }
    }
    updateBulkCount() {
        const el = document.getElementById('task-bulk-count');
        if (el) el.textContent = `已选 ${this.selectedPlanTaskIds.size} 项`;
    }
    bulkSelectCurrentPage() {
        // 选中当前页“规划任务”区域展示的复选框
        const listEl = document.getElementById('task-list');
        if (!listEl) return;
        const checkboxes = Array.from(listEl.querySelectorAll('.activity-item input[type="checkbox"]'));
        checkboxes.forEach(cb => { cb.checked = true; });
        // 收集ID（从相邻文本里解析或绑定自定义属性）
        const items = Array.from(listEl.querySelectorAll('.activity-item'));
        items.forEach(it => {
            const text = it.querySelector('.activity-text');
            if (!text) return;
            const parts = (text.textContent || '').trim().split(' ');
            const idStr = parts[0] || '';
            const idNum = Number(idStr);
            if (!Number.isNaN(idNum)) this.selectedPlanTaskIds.add(idNum);
        });
        this.updateBulkCount();
    }
    async bulkConfirm(confirmed) {
        if (this.selectedPlanTaskIds.size === 0) { alert('请先选择任务'); return; }
        const ids = Array.from(this.selectedPlanTaskIds);
        for (const id of ids) {
            try {
                await fetch(`${API_BASE}/tasks/${id}/confirm`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ confirmed, reason: '' })
                });
            } catch (_) {}
        }
        this.addActivity('📋', `批量${confirmed ? '确认' : '拒绝'} ${ids.length} 项`);
        this.refreshTasks(true);
    }
    async bulkExecute() {
        if (this.selectedPlanTaskIds.size === 0) { alert('请先选择任务'); return; }
        const ids = Array.from(this.selectedPlanTaskIds);
        for (const id of ids) {
            try {
                await fetch(`${API_BASE}/tasks/${id}/execute`, { method: 'POST' });
            } catch (_) {}
        }
        this.addActivity('⚙️', `批量执行 ${ids.length} 项`);
        this.refreshTasks(true);
    }
    async bulkReject() {
        if (this.selectedPlanTaskIds.size === 0) { alert('请先选择任务'); return; }
        const reason = prompt('请输入批量拒绝原因（将作用于所有选中任务）：', '') || '';
        const ids = Array.from(this.selectedPlanTaskIds);
        let done = 0;
        for (const id of ids) {
            try {
                await fetch(`${API_BASE}/tasks/${id}/confirm`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ confirmed: false, reason })
                });
                done++;
            } catch (_) {}
        }
        this.addActivity('🚫', `批量拒绝完成：${done}/${ids.length}`);
        this.refreshTasks(true);
    }
    async bulkDelete() {
        if (this.selectedPlanTaskIds.size === 0) { alert('请先选择任务'); return; }
        const ok = confirm('确认删除所选规划任务？该操作不可恢复。');
        if (!ok) return;
        const ids = Array.from(this.selectedPlanTaskIds);
        let done = 0;
        for (const id of ids) {
            try {
                await fetch(`${API_BASE}/planning/tasks/${id}`, { method: 'DELETE' });
                done++;
            } catch (_) {}
        }
        this.selectedPlanTaskIds.clear();
        this.updateBulkCount();
        this.addActivity('🗑️', `批量删除完成：${done}/${ids.length}`);
        this.refreshTasks(true);
    }
    async bulkRetrospect() {
        if (this.selectedPlanTaskIds.size === 0) { alert('请先选择任务'); return; }
        const ok = confirm('批量复盘将为已选择的任务提交相同复盘内容，继续？');
        if (!ok) return;
        const success = confirm('复盘结果：确定=成功，取消=失败');
        const summary = prompt('复盘总结（将应用于所有选中任务）：', '') || '';
        const lessonsRaw = prompt('关键经验要点（中文逗号分隔，可留空）：', '') || '';
        const lessons = lessonsRaw ? lessonsRaw.split('，').map(s => s.trim()).filter(Boolean) : [];
        const ids = Array.from(this.selectedPlanTaskIds);
        let done = 0;
        for (const id of ids) {
            try {
                await fetch(`${API_BASE}/tasks/${id}/retrospect`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ success, summary, lessons, metrics: {} })
                });
                done++;
            } catch (_) {}
        }
        this.addActivity('🧠', `批量复盘完成：${done}/${ids.length}`);
        this.refreshTasks(true);
    }

    async pushStepsToOrchestratorInline(orchestratorTaskId) {
        try {
            const mode = prompt('输入模式：1=从规划任务导入  2=手动粘贴JSON（默认1）', '1');
            let steps = [];
            if (mode === null) return;
            if (mode === '2') {
                const txt = prompt('粘贴步骤数组（JSON）：', '');
                if (!txt) return;
                try {
                    steps = JSON.parse(txt);
                } catch (e) {
                    alert('JSON解析失败');
                    return;
                }
                if (!Array.isArray(steps)) {
                    alert('必须为数组');
                    return;
                }
            } else {
                const pid = prompt('输入规划任务ID（数字）：', '');
                if (!pid) return;
                const r = await fetch(`${API_BASE}/planning/tasks/${encodeURIComponent(pid)}`);
                const j = await r.json();
                if (!r.ok || !j.task) {
                    alert('未找到该规划任务');
                    return;
                }
                steps = j.task.steps || [];
                if (!Array.isArray(steps) || steps.length === 0) {
                    alert('该规划任务没有可用的 steps');
                    return;
                }
            }
            const resp = await fetch(`${API_BASE}/tasks/${encodeURIComponent(orchestratorTaskId)}/metadata`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ updates: { steps } })
            });
            const data = await resp.json();
            if (!resp.ok) {
                alert('推送失败：' + (data.detail || '未知错误'));
                return;
            }
            this.addActivity('🧩', `已推送步骤到 ${orchestratorTaskId}（total_steps=${(data.task && data.task.metadata && data.task.metadata.total_steps) || '未知'}）`);
            this.refreshTasks(true);
            // 成功后询问是否打开详情页
            const go = confirm('步骤已推送，是否立即打开该任务详情查看？');
            if (go) {
                window.open(`task_detail.html?oid=${encodeURIComponent(orchestratorTaskId)}`, '_blank');
            }
        } catch (e) {
            alert('推送异常：' + e.message);
        }
    }

    async confirmTask(taskId, confirmed) {
        try {
            const reason = confirmed ? '' : (prompt('请输入拒绝原因（可选）：', '') || '');
            const r = await fetch(`${API_BASE}/tasks/${taskId}/confirm`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ confirmed, reason })
            });
            if (r.ok) {
                this.addActivity(confirmed ? '✅' : '🚫', `任务${confirmed ? '已确认' : '已拒绝'} #${taskId}`);
                this.refreshTasks();
            } else {
                const data = await r.json();
                this.addMessage('assistant', `❌ 任务确认失败：${data.detail || '未知错误'}`);
            }
        } catch (e) {
            this.addMessage('assistant', `❌ 任务确认异常：${e.message}`);
        }
    }

    async executeTask(taskId) {
        try {
            const r = await fetch(`${API_BASE}/tasks/${taskId}/execute`, { method: 'POST' });
            const data = await r.json();
            if (r.ok && data.success) {
                this.addActivity('⚙️', `任务已执行 #${taskId}`);
                this.refreshTasks();
                // 执行后提示复盘或查看详情
                setTimeout(async () => {
                    const doRetro = confirm('任务已执行完成。是否立即进行复盘？（取消=稍后再说）');
                    if (doRetro) {
                        await this.retrospectTask(taskId);
                        const openDetail = confirm('复盘已提交。是否打开任务详情查看？');
                        if (openDetail) {
                            window.open(`task_detail.html?pid=${encodeURIComponent(taskId)}`, '_blank');
                        }
                    } else {
                        const openDetail = confirm('是否直接打开任务详情查看执行结果？');
                        if (openDetail) {
                            window.open(`task_detail.html?pid=${encodeURIComponent(taskId)}`, '_blank');
                        }
                    }
                }, 400);
            } else {
                this.addMessage('assistant', `❌ 执行失败：${data.detail || data.error || '未知错误'}`);
            }
        } catch (e) {
            this.addMessage('assistant', `❌ 执行异常：${e.message}`);
        }
    }

    async retrospectTask(taskId) {
        try {
            const success = confirm('任务是否成功完成？点击“确定”为成功，“取消”为失败。');
            const summary = prompt('请填写简要复盘总结：', '') || '';
            const lessonsRaw = prompt('关键经验要点（用中文逗号分隔，可留空）：', '') || '';
            const lessons = lessonsRaw ? lessonsRaw.split('，').map(s => s.trim()).filter(Boolean) : [];
            const r = await fetch(`${API_BASE}/tasks/${taskId}/retrospect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ success, summary, lessons, metrics: {} })
            });
            const data = await r.json();
            if (r.ok && data.success) {
                this.addActivity('🧠', `已复盘任务 #${taskId}`);
                this.refreshTasks();
            } else {
                this.addMessage('assistant', `❌ 复盘失败：${data.detail || '未知错误'}`);
            }
        } catch (e) {
            this.addMessage('assistant', `❌ 复盘异常：${e.message}`);
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

    async updateSecurityAudit() {
        const listEl = document.getElementById('security-audit-list');
        if (!listEl) return;
        try {
            const r = await fetch(`${API_BASE}/security/audit/overview?limit=10`);
            if (!r.ok) return;
            const data = await r.json();
            listEl.innerHTML = '';
            const events = data.events || [];
            if (events.length === 0) {
                listEl.innerHTML = '<div class="security-empty">暂无审计事件</div>';
                return;
            }
            events.forEach(e => {
                const item = document.createElement('div');
                item.className = `security-event ${e.success ? 'success' : 'error'}`;
                const header = document.createElement('div');
                header.className = 'event-header';
                const time = new Date(e.timestamp).toLocaleTimeString('zh-CN', { hour12: false });
                header.innerHTML = `<span>${time}</span><span>${e.type}/${e.severity}</span>`;
                const detail = document.createElement('div');
                detail.className = 'event-meta';
                detail.textContent = `${e.source} · ${e.short}`;
                item.appendChild(header);
                item.appendChild(detail);
                listEl.appendChild(item);
            });
        } catch (e) {
            // 静默
        }
    }
}

// 初始化应用
const app = new App();
window.app = app; // 暴露到全局，方便调试

console.log('✅ 应用脚本已加载');

