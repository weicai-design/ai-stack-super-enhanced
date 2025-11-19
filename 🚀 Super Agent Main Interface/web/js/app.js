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
        this.securityAuditFilter = (typeof window !== 'undefined' && window.localStorage && localStorage.getItem('securityAuditFilter')) || 'all'; // all | orchestrator_task_status
        this.taskPage = 1;
        this.taskPageSize = 10;
        this.taskPageOrch = (typeof window !== 'undefined' && window.localStorage && parseInt(localStorage.getItem('taskPageOrch') || '1', 10)) || 1;
        this.taskPagePlan = (typeof window !== 'undefined' && window.localStorage && parseInt(localStorage.getItem('taskPagePlan') || '1', 10)) || 1;
        this.selectedPlanTaskIds = new Set();
        this.searchEngines = {};
        this.selectedSearchEngines = [];
        this.lastSearchResults = null;
        this.voiceLanguages = [];
        this.learningStatsTimer = null;
        this.memos = [];
        this.planningTasksData = [];
        this.taskImpacts = [];
        this.taskAutoRag = true;
        this.taskAutoResource = true;
        try {
            if (typeof window !== 'undefined' && window.localStorage) {
                const storedEngines = localStorage.getItem('selectedSearchEngines');
                if (storedEngines) {
                    this.selectedSearchEngines = JSON.parse(storedEngines);
                }
            }
        } catch (_) {
            this.selectedSearchEngines = [];
        }
        
        // 立即初始化
        this.init();
    }
    
    async streamChatMessage(message, loadingId) {
        const response = await fetch(`${API_BASE}/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'
            },
            body: JSON.stringify({
                message,
                input_type: 'text',
                context: {}
            })
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        if (!response.body || !response.body.getReader) {
            throw new Error('浏览器不支持流式响应');
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        let partial = '';
        let finalPayload = null;
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const events = buffer.split('\n\n');
            buffer = events.pop() || '';
            for (const event of events) {
                const line = event.trim();
                if (!line.startsWith('data:')) continue;
                const dataStr = line.replace(/^data:\s*/, '');
                if (!dataStr) continue;
                let payload;
                try {
                    payload = JSON.parse(dataStr);
                } catch {
                    continue;
                }
                if (payload.type === 'status') {
                    this.updateMessageContent(loadingId, payload.message || '…');
                } else if (payload.type === 'token') {
                    partial += payload.data || '';
                    this.updateMessageContent(loadingId, partial);
                } else if (payload.type === 'final') {
                    finalPayload = payload.payload;
                } else if (payload.type === 'error') {
                    throw new Error(payload.message || '流式响应异常');
                }
            }
        }
        this.attachTimestamp(loadingId);
        if (!finalPayload) {
            throw new Error('流式接口未返回结果');
        }
        return finalPayload;
    }
    
    async fetchChatResult(message) {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message,
                input_type: 'text',
                context: {}
            })
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    }
    
    handleChatResult(result, options = {}) {
        const streaming = options.streaming;
        const messageId = options.messageId;
        if (!result) {
            this.addMessage('assistant', '未收到AI回复');
            return;
        }
        if (!result.success) {
            const errorText = `错误: ${result.error || '未知错误'}`;
            if (streaming && messageId) {
                this.updateMessageContent(messageId, errorText);
                this.attachTimestamp(messageId);
            } else {
                this.addMessage('assistant', errorText);
            }
            return;
        }
        if (!streaming) {
            this.addMessage('assistant', result.response);
        }
        this.addActivity('💬', '收到AI回复');
        if (this.ttsEnabled) {
            this.playTTS(result.response, this.ttsLanguage);
        }
        if (result.rag_retrievals) {
            const firstCount = (result.rag_retrievals.first?.knowledge?.length) || (result.rag_retrievals.first?.count) || 0;
            const secondExp = (result.rag_retrievals.second?.experience?.length) || 0;
            const secondCases = (result.rag_retrievals.second?.similar_cases?.length) || 0;
            const secondBest = (result.rag_retrievals.second?.best_practices?.length) || 0;
            const summary = `📚 RAG检索摘要：首检${firstCount}条；二检 经验${secondExp} / 案例${secondCases} / 最佳实践${secondBest}`;
            this.addMessage('assistant', summary);
        }
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
        const ttsBtn = document.getElementById('tts-btn');
        if (ttsBtn) {
            const handler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleTTS();
            };
            ttsBtn.onclick = handler;
            ttsBtn.addEventListener('click', handler);
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

        const memoSaveBtn = document.getElementById('memo-save');
        if (memoSaveBtn) {
            const handler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.saveMemoFromForm();
            };
            memoSaveBtn.onclick = handler;
            memoSaveBtn.addEventListener('click', handler);
        }
        const memoExtractBtn = document.getElementById('memo-extract');
        if (memoExtractBtn) {
            const handler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.extractTasksFromMemos();
            };
            memoExtractBtn.onclick = handler;
            memoExtractBtn.addEventListener('click', handler);
        }

        const fileGenRun = document.getElementById('filegen-run');
        if (fileGenRun) {
            const handler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.generateFileFromPanel();
            };
            fileGenRun.onclick = handler;
            fileGenRun.addEventListener('click', handler);
        }

        // 终端运行绑定
        const termRun = document.getElementById('terminal-run');
        const termReplay = document.getElementById('terminal-replay-btn');
        const termSandboxStatus = document.getElementById('terminal-sandbox-status');
        const btnCodeReview = document.getElementById('btn-code-review');
        const btnCodeOptimize = document.getElementById('btn-code-optimize');
        const btnGenerateDoc = document.getElementById('btn-generate-doc');
        const btnCursorOpen = document.getElementById('btn-cursor-open');
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
        const voiceLangSelect = document.getElementById('voice-lang-select');
        if (voiceLangSelect) {
            voiceLangSelect.addEventListener('change', (e) => this.changeVoiceLanguage(e.target.value));
        }
        
        // P0-014: 资源诊断按钮
        const runDiagnosticBtn = document.getElementById('run-diagnostic-btn');
        if (runDiagnosticBtn) {
            const handler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.runResourceDiagnostic();
            };
            runDiagnosticBtn.onclick = handler;
            runDiagnosticBtn.addEventListener('click', handler);
        }
        const refreshResourceOverviewBtn = document.getElementById('refreshResourceOverview');
        if (refreshResourceOverviewBtn) {
            const handler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.loadResourceOverview();
            };
            refreshResourceOverviewBtn.onclick = handler;
            refreshResourceOverviewBtn.addEventListener('click', handler);
        }
        const searchEngineRefreshBtn = document.getElementById('search-engine-refresh');
        if (searchEngineRefreshBtn) {
            const handler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.loadSearchEngines(true);
            };
            searchEngineRefreshBtn.onclick = handler;
            searchEngineRefreshBtn.addEventListener('click', handler);
        }
        const learningRefreshBtn = document.getElementById('learning-refresh');
        if (learningRefreshBtn) {
            const handler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.loadLearningStats(true);
            };
            learningRefreshBtn.onclick = handler;
            learningRefreshBtn.addEventListener('click', handler);
        }
        const learningSuggestionContainer = document.getElementById('learning-suggestions');
        if (learningSuggestionContainer && !learningSuggestionContainer.dataset.bound) {
            learningSuggestionContainer.dataset.bound = 'true';
            learningSuggestionContainer.addEventListener('click', (event) => {
                const btn = event.target.closest('[data-learning-action="apply"]');
                if (!btn) return;
                event.preventDefault();
                const recId = btn.getAttribute('data-rec-id');
                if (recId) {
                    this.applyLearningRecommendation(recId);
                }
            });
        }
        const autoRagCheckbox = document.getElementById('task-auto-rag');
        if (autoRagCheckbox) {
            this.taskAutoRag = autoRagCheckbox.checked;
            autoRagCheckbox.addEventListener('change', () => {
                this.taskAutoRag = autoRagCheckbox.checked;
            });
        }
        const autoResourceCheckbox = document.getElementById('task-auto-resource');
        if (autoResourceCheckbox) {
            this.taskAutoResource = autoResourceCheckbox.checked;
            autoResourceCheckbox.addEventListener('change', () => {
                this.taskAutoResource = autoResourceCheckbox.checked;
            });
        }
        const lifecycleContainer = document.getElementById('task-lifecycle');
        if (lifecycleContainer && !lifecycleContainer.dataset.bound) {
            lifecycleContainer.dataset.bound = 'true';
            lifecycleContainer.addEventListener('click', (event) => {
                const btn = event.target.closest('[data-task-action]');
                if (!btn) return;
                event.preventDefault();
                const taskId = parseInt(btn.getAttribute('data-task-id'), 10);
                const action = btn.getAttribute('data-task-action');
                if (!taskId || !action) return;
                if (action === 'confirm') {
                    this.confirmPlanningTask(taskId, true);
                } else if (action === 'reject') {
                    this.confirmPlanningTask(taskId, false);
                } else if (action === 'schedule') {
                    this.schedulePlanningTask(taskId);
                } else if (action === 'execute') {
                    this.executePlanningTask(taskId);
                } else if (action === 'retrospect') {
                    this.retrospectPlanningTask(taskId);
                }
            });
        }
        const resourceExecList = document.getElementById('resource-execution-list');
        if (resourceExecList && !resourceExecList.dataset.bound) {
            resourceExecList.dataset.bound = 'true';
            resourceExecList.addEventListener('click', (event) => {
                const target = event.target.closest('[data-rollback]');
                if (target) {
                    event.preventDefault();
                    const suggestionId = target.getAttribute('data-rollback');
                    this.triggerResourceRollback(suggestionId);
                }
            });
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
        this.loadResourceOverview();
        setInterval(() => this.loadResourceOverview(), 15000);
        this.loadTTSSettings();
        this.loadVoiceLanguages();
        this.loadSearchEngines();
        this.renderSearchResultsPanel(this.lastSearchResults?.data || null, this.lastSearchResults?.query || null);
        this.loadLearningStats();
        this.loadModelConfig();
        if (this.learningStatsTimer) {
            clearInterval(this.learningStatsTimer);
        }
        this.learningStatsTimer = setInterval(() => this.loadLearningStats(), 20000);
        // 任务筛选按钮
        const filterBtn = document.getElementById('task-filter-apply');
        if (filterBtn) {
            const handler = (e) => {
                e.preventDefault();
                try {
                    const q = document.getElementById('task-filter-q');
                    const s = document.getElementById('task-filter-status');
                    if (q) localStorage.setItem('taskFilterQ', q.value || '');
                    if (s) localStorage.setItem('taskFilterStatus', s.value || '');
                } catch(_) {}
                this.refreshTasks(true);
            };
            filterBtn.onclick = handler;
            filterBtn.addEventListener('click', handler);
        }
        const resetBtn = document.getElementById('task-filter-reset');
        if (resetBtn) {
            const handler = (e) => {
                e.preventDefault();
                const q = document.getElementById('task-filter-q'); if (q) q.value = '';
                const s = document.getElementById('task-filter-status'); if (s) s.value = '';
                try { localStorage.removeItem('taskFilterQ'); localStorage.removeItem('taskFilterStatus'); } catch(_) {}
                this.taskPage = 1;
                this.refreshTasks(true);
            };
            resetBtn.onclick = handler;
            resetBtn.addEventListener('click', handler);
        }
        // 分页
        const sizeSel = document.getElementById('task-page-size');
        if (sizeSel) {
            // 初始从本地持久化恢复
            try {
                const savedSize = localStorage.getItem('taskPageSize');
                if (savedSize) {
                    sizeSel.value = savedSize;
                    this.taskPageSize = parseInt(savedSize, 10);
                }
                const savedQ = localStorage.getItem('taskFilterQ');
                const savedS = localStorage.getItem('taskFilterStatus');
                const qEl = document.getElementById('task-filter-q');
                const sEl = document.getElementById('task-filter-status');
                if (qEl && savedQ !== null) qEl.value = savedQ;
                if (sEl && savedS !== null) sEl.value = savedS;
            } catch(_) {}
            sizeSel.addEventListener('change', () => {
                this.taskPageSize = parseInt(sizeSel.value || '10', 10);
                try { localStorage.setItem('taskPageSize', String(this.taskPageSize)); } catch(_) {}
                this.taskPage = 1;
                this.refreshTasks(true);
            });
        }
        const prevBtn = document.getElementById('task-prev');
        const nextBtn = document.getElementById('task-next');
        if (prevBtn) prevBtn.onclick = (e) => { e.preventDefault(); if (this.taskPage > 1) { this.taskPage--; this.refreshTasks(true); } };
        if (nextBtn) nextBtn.onclick = (e) => { e.preventDefault(); this.taskPage++; this.refreshTasks(true); };
        const delGuard = document.getElementById('task-delete-guard');
        if (delGuard) delGuard.addEventListener('change', () => this.refreshTasks(true));
        // 安全审计过滤快捷键
        const btnAllEvt = document.getElementById('security-filter-all');
        const btnOtEvt = document.getElementById('security-filter-otstatus');
        if (btnAllEvt) btnAllEvt.onclick = (e) => { e.preventDefault(); this.securityAuditFilter = 'all'; try { localStorage.setItem('securityAuditFilter', 'all'); } catch(_){} this.updateSecurityAudit(); };
        if (btnOtEvt) btnOtEvt.onclick = (e) => { e.preventDefault(); this.securityAuditFilter = 'orchestrator_task_status'; try { localStorage.setItem('securityAuditFilter', 'orchestrator_task_status'); } catch(_){} this.updateSecurityAudit(); };
        // 编排器筛选持久化恢复
        try {
            const oq = localStorage.getItem('taskOrchQ');
            const os = localStorage.getItem('taskOrchStatus');
            const oqEl = document.getElementById('task-orch-q');
            const osEl = document.getElementById('task-orch-status');
            if (oqEl && oq !== null) oqEl.value = oq;
            if (osEl && os !== null) osEl.value = os;
        } catch(_) {}
        // 编排器筛选按钮
        const orchApply = document.getElementById('task-orch-apply');
        if (orchApply) {
            const handler = (e) => {
                e.preventDefault();
                try {
                    const oqEl = document.getElementById('task-orch-q');
                    const osEl = document.getElementById('task-orch-status');
                    if (oqEl) localStorage.setItem('taskOrchQ', oqEl.value || '');
                    if (osEl) localStorage.setItem('taskOrchStatus', osEl.value || '');
                } catch(_) {}
                this.refreshTasks(true);
            };
            orchApply.onclick = handler;
            orchApply.addEventListener('click', handler);
        }
        const orchReset = document.getElementById('task-orch-reset');
        if (orchReset) {
            const handler = (e) => {
                e.preventDefault();
                const oqEl = document.getElementById('task-orch-q'); if (oqEl) oqEl.value = '';
                const osEl = document.getElementById('task-orch-status'); if (osEl) osEl.value = '';
                try { localStorage.removeItem('taskOrchQ'); localStorage.removeItem('taskOrchStatus'); } catch(_) {}
                this.refreshTasks(true);
            };
            orchReset.onclick = handler;
            orchReset.addEventListener('click', handler);
        }
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
        
        this.loadMemos();
        this.loadPlanningTasks();
        this.loadTaskImpacts();
        setInterval(() => this.loadPlanningTasks(), 20000);
        setInterval(() => this.loadTaskImpacts(), 25000);
        setInterval(() => this.loadMemos(), 60000);
        
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
                const engines = (this.selectedSearchEngines && this.selectedSearchEngines.length > 0)
                    ? this.selectedSearchEngines
                    : [];
                const useMulti = engines.length > 1;
                const endpoint = useMulti ? `${API_BASE}/search/multi` : `${API_BASE}/search`;
                const payload = useMulti
                    ? {
                        query: message,
                        search_type: 'web',
                        engines,
                        max_results_per_engine: 5
                    }
                    : {
                        query: message,
                        search_type: 'web',
                        max_results: 10,
                        engine: engines.length === 1 ? engines[0] : undefined
                    };
                response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    const searchResult = await response.json();
                    this.removeMessage(loadingId);
                    
                    if ((searchResult.success !== false) && searchResult.results && searchResult.results.length > 0) {
                        // 格式化搜索结果
                        let total = searchResult.total_results ?? searchResult.total ?? searchResult.results.length;
                        let searchContent = `🔍 搜索"${message}"找到 ${total} 条结果（引擎：${(searchResult.engines_used || engines || ['auto']).join(', ')}）：\n\n`;
                        searchResult.results.slice(0, 5).forEach((item, index) => {
                            searchContent += `${index + 1}. ${item.title || item.snippet || '无标题'}\n`;
                            if (item.snippet) {
                                searchContent += `   ${item.snippet.substring(0, 120)}...\n`;
                            }
                            if (item.url) {
                                searchContent += `   链接: ${item.url}\n`;
                            }
                            searchContent += '\n';
                        });
                        
                        this.addMessage('assistant', searchContent);
                        this.addActivity('🔍', `搜索: ${message}`);
                        this.lastSearchResults = { query: message, data: searchResult };
                        this.renderSearchResultsPanel(searchResult, message);
                        
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
                        this.renderSearchResultsPanel(null, message);
                        this.addMessage('assistant', `未找到相关搜索结果。${searchResult.error || ''}`);
                    }
                } else {
                    throw new Error(`搜索请求失败: HTTP ${response.status}`);
                }
            } else {
                try {
                    const streamResult = await this.streamChatMessage(message, loadingId);
                    this.handleChatResult(streamResult, { streaming: true, messageId: loadingId });
                } catch (streamError) {
                    console.warn('流式响应失败，降级到普通请求', streamError);
                    this.removeMessage(loadingId);
                    const fallbackResult = await this.fetchChatResult(message);
                    this.handleChatResult(fallbackResult, { streaming: false });
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
    
    updateMessageContent(messageId, content) {
        const message = document.getElementById(messageId);
        if (!message) return;
        const contentDiv = message.querySelector('.message-content');
        if (contentDiv) {
            contentDiv.textContent = content;
        }
    }
    
    attachTimestamp(messageId) {
        const message = document.getElementById(messageId);
        if (!message) return;
        if (!message.querySelector('.message-time')) {
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            const now = new Date();
            timeDiv.textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
            message.appendChild(timeDiv);
        }
    }
    
    switchModule(module) {
        console.log('🔄 切换模块:', module);
        const route = (window.ROUTE_MAP || {})[module];
        
        // 更新按钮状态
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.module === module);
        });
        
        if (!route) {
            this.addMessage('assistant', `模块 "${module}" 暂无配置的路由，请联系管理员补充。`);
            return;
        }
        
        this.currentModule = module;
        const moduleName = this.getModuleName(module);
        this.addMessage('assistant', `已切换到"${moduleName}"模块`);
        this.addActivity('🔄', `切换到${moduleName}`);
        
        if (route.type === 'internal') {
            return;
        }
        
        if (route.external) {
            window.open(route.external, '_blank');
            return;
        }
        
        if (route.path) {
            window.open(route.path, '_blank');
            return;
        }
        
        if (route.url) {
            window.open(route.url, '_blank');
        }
    }
    
    getModuleName(module) {
        return (window.ROUTE_MAP && window.ROUTE_MAP[module] && window.ROUTE_MAP[module].label) || module;
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
                    this.loadModelConfig();
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
    mediaRecorder = null;
    fallbackStream = null;
    isFallbackRecording = false;
    
    startVoiceInput() {
        console.log('🎤 启动语音输入');
        if (this.isFallbackRecording) {
            this.stopFallbackRecording();
            return;
        }
        
        // 检查浏览器支持
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.startFallbackRecording();
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
            // 降级到后端录音识别
            this.startFallbackRecording();
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
        const searchPanel = document.getElementById('search-panel');
        
        if (this.searchMode) {
            input.placeholder = '输入搜索关键词...';
            if (searchBtn) {
                searchBtn.style.background = 'var(--primary-color)';
                searchBtn.style.color = 'white';
            }
            if (searchPanel) {
                searchPanel.classList.add('active');
            }
        } else {
            input.placeholder = '输入您的问题或指令...';
            if (searchBtn) {
                searchBtn.style.background = '';
                searchBtn.style.color = '';
            }
            if (searchPanel) {
                searchPanel.classList.remove('active');
            }
        }
    }
    
    createMemo() {
        console.log('📝 创建备忘录');
        const panel = document.getElementById('memo-task-panel');
        const input = document.getElementById('memo-content');
        if (panel) {
            panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        if (input) {
            input.focus();
        }
        this.addMessage('assistant', '请在右侧备忘录区域填写内容并点击“保存备忘录”。');
    }
    
    createTask() {
        console.log('📋 新建任务');
        const lifecycle = document.getElementById('task-lifecycle');
        if (lifecycle) {
            lifecycle.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        this.addMessage('assistant', '可在“备忘录 · 智能任务闭环”区域确认/排期/执行任务。');
    }

    updateMemoStatus(message, isError = false) {
        const statusEl = document.getElementById('memo-status');
        if (!statusEl) return;
        statusEl.textContent = message;
        statusEl.style.color = isError ? '#ff6b6b' : '#888';
    }

    async saveMemoFromForm() {
        const title = (document.getElementById('memo-title')?.value || '').trim();
        const content = (document.getElementById('memo-content')?.value || '').trim();
        const type = document.getElementById('memo-type')?.value || 'note';
        const importance = parseInt(document.getElementById('memo-importance')?.value || '4', 10);
        const tagsRaw = (document.getElementById('memo-tags')?.value || '').trim();
        if (!content) {
            this.updateMemoStatus('请输入内容再保存', true);
            return;
        }
        const tags = tagsRaw ? tagsRaw.split(/[,，]/).map(t => t.trim()).filter(Boolean) : [];
        this.updateMemoStatus('正在保存...', false);
        try {
            const resp = await fetch(`${API_BASE}/memos`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title,
                    content,
                    type,
                    importance,
                    tags
                })
            });
            if (!resp.ok) {
                throw new Error(`HTTP ${resp.status}`);
            }
            this.updateMemoStatus('保存成功', false);
            this.addMessage('assistant', '✅ 备忘录已保存，可继续提炼任务。');
            const contentInput = document.getElementById('memo-content');
            if (contentInput) {
                contentInput.value = '';
            }
            this.loadMemos();
        } catch (error) {
            console.error('保存备忘录失败:', error);
            this.updateMemoStatus(`保存失败：${error.message}`, true);
        }
    }

    async extractTasksFromMemos() {
        this.updateMemoStatus('正在提炼任务...', false);
        try {
            const resp = await fetch(`${API_BASE}/tasks/extract`, {
                method: 'POST'
            });
            if (!resp.ok) {
                throw new Error(`HTTP ${resp.status}`);
            }
            const data = await resp.json();
            const count = data.total || (data.tasks || []).length;
            this.updateMemoStatus(`提炼完成：${count} 条任务`, false);
            this.addMessage('assistant', `🧠 已从备忘录提炼 ${count} 条任务，请在任务列表中确认/排期。`);
            this.loadPlanningTasks();
            this.refreshTasks(true);
        } catch (error) {
            console.error('提炼任务失败:', error);
            this.updateMemoStatus(`提炼失败：${error.message}`, true);
        }
    }

    async loadMemos() {
        try {
            const resp = await fetch(`${API_BASE}/memos`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            const memos = (data.memos || []).slice().sort((a, b) => {
                return new Date(b.created_at || 0) - new Date(a.created_at || 0);
            });
            this.memos = memos.slice(0, 6);
            this.renderMemoList();
        } catch (error) {
            console.warn('加载备忘录失败:', error);
        }
    }

    renderMemoList() {
        const listEl = document.getElementById('memo-list');
        if (!listEl) return;
        if (!this.memos.length) {
            listEl.innerHTML = '<div style="color:#666;">暂无备忘录</div>';
            return;
        }
        listEl.innerHTML = '';
        this.memos.forEach((memo) => {
            const item = document.createElement('div');
            item.style.borderBottom = '1px solid #222';
            item.style.padding = '4px 0';
            const title = memo.title || memo.content?.slice(0, 40) || '未命名';
            const created = memo.created_at ? this.formatRelativeTime(memo.created_at) : '';
            item.innerHTML = `
                <div style="display:flex;justify-content:space-between;">
                    <span>${title}</span>
                    <span style="color:#777;font-size:11px;">${created}</span>
                </div>
                <div style="color:#aaa;font-size:11px;">类型：${memo.type || 'note'} · 重要度${memo.importance || 3}</div>
            `;
            listEl.appendChild(item);
        });
    }

    async loadPlanningTasks() {
        try {
            const resp = await fetch(`${API_BASE}/planning/tasks`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            this.planningTasksData = data.tasks || [];
            this.renderTaskLifecycle();
        } catch (error) {
            console.warn('加载规划任务失败:', error);
            const lifecycle = document.getElementById('task-lifecycle');
            if (lifecycle) {
                lifecycle.innerHTML = `<div style="color:#666;">无法获取任务：${error.message}</div>`;
            }
        }
    }

    getPlanningTask(taskId) {
        return this.planningTasksData.find(t => String(t.id) === String(taskId));
    }

    renderTaskLifecycle() {
        const container = document.getElementById('task-lifecycle');
        if (!container) return;
        if (!this.planningTasksData.length) {
            container.innerHTML = '<div style="color:#666;">暂无任务，尝试从备忘录提炼</div>';
            return;
        }
        const sections = [
            {
                title: '待确认',
                tasks: this.planningTasksData.filter(t => t.needs_confirmation),
                empty: '暂无需要确认的任务',
                actions: ['confirm', 'reject', 'schedule']
            },
            {
                title: '已确认 / 待执行',
                tasks: this.planningTasksData.filter(t => !t.needs_confirmation && (t.status === 'confirmed' || t.status === 'pending')),
                empty: '暂无待执行任务',
                actions: ['schedule', 'execute']
            },
            {
                title: '已排期 / 进行中',
                tasks: this.planningTasksData.filter(t => ['scheduled', 'in_progress'].includes(t.status)),
                empty: '暂无排期任务',
                actions: ['execute', 'retrospect']
            },
            {
                title: '已完成',
                tasks: this.planningTasksData.filter(t => t.status === 'completed'),
                empty: '尚无完成任务',
                actions: ['retrospect']
            }
        ];
        container.innerHTML = '';
        sections.forEach(section => {
            const block = document.createElement('div');
            block.style.marginBottom = '8px';
            const header = document.createElement('div');
            header.style.display = 'flex';
            header.style.justifyContent = 'space-between';
            header.style.alignItems = 'center';
            header.style.fontWeight = '600';
            header.textContent = `${section.title}（${section.tasks.length}）`;
            block.appendChild(header);
            if (!section.tasks.length) {
                const empty = document.createElement('div');
                empty.style.color = '#666';
                empty.style.fontSize = '12px';
                empty.textContent = section.empty;
                block.appendChild(empty);
            } else {
                section.tasks.slice(0, 4).forEach(task => {
                    block.appendChild(this.renderTaskLifecycleItem(task, section.actions));
                });
            }
            container.appendChild(block);
        });
    }

    renderTaskLifecycleItem(task, actions) {
        const item = document.createElement('div');
        item.style.border = '1px solid #222';
        item.style.borderRadius = '6px';
        item.style.padding = '6px';
        item.style.marginTop = '4px';
        const due = task.due_date ? ` · 截止 ${task.due_date}` : '';
        const scheduled = task.scheduled_for ? ` · 排期 ${task.scheduled_for}` : '';
        const owner = task.owner ? ` · 负责人 ${task.owner}` : '';
        item.innerHTML = `
            <div style="display:flex;justify-content:space-between;">
                <span>${task.title || '未命名任务'}</span>
                <span style="color:#aaa;font-size:11px;">${this.toTaskStatusLabel(task.status)}</span>
            </div>
            <div style="color:#888;font-size:11px;">优先级 ${task.priority || 'medium'}${due}${scheduled}${owner}</div>
            <div style="color:#aaa;font-size:11px;">${(task.tags || []).join(' / ')}</div>
        `;
        const btnRow = document.createElement('div');
        btnRow.style.display = 'flex';
        btnRow.style.flexWrap = 'wrap';
        btnRow.style.gap = '4px';
        actions.forEach(action => {
            const btn = document.createElement('button');
            btn.className = 'action-btn-small';
            btn.dataset.taskAction = action;
            btn.dataset.taskId = task.id;
            btn.textContent = this.getTaskActionLabel(action);
            btnRow.appendChild(btn);
        });
        item.appendChild(btnRow);
        return item;
    }

    getTaskActionLabel(action) {
        return {
            confirm: '确认',
            reject: '拒绝',
            schedule: '排期',
            execute: '执行',
            retrospect: '复盘'
        }[action] || action;
    }

    toTaskStatusLabel(status) {
        const map = {
            pending: '待确认',
            confirmed: '已确认',
            scheduled: '已排期',
            in_progress: '进行中',
            completed: '已完成',
            rejected: '已拒绝',
            failed: '失败'
        };
        return map[status] || status || '未知';
    }

    async confirmPlanningTask(taskId, confirmed) {
        try {
            const body = { confirmed };
            if (!confirmed) {
                body.reason = prompt('请输入拒绝原因（可选）：', '') || '';
            }
            const resp = await fetch(`${API_BASE}/tasks/${taskId}/confirm`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            this.addActivity(confirmed ? '✅' : '⚠️', confirmed ? `已确认任务 ${taskId}` : `已拒绝任务 ${taskId}`);
            this.loadPlanningTasks();
            this.refreshTasks(true);
        } catch (error) {
            this.addMessage('assistant', `❌ 更新任务失败：${error.message}`);
        }
    }

    async schedulePlanningTask(taskId) {
        const when = prompt('输入排期时间（例如 2025-11-18 14:00 或 ISO8601）：', '');
        const owner = prompt('负责人（可选）：', '') || undefined;
        const notes = prompt('备注说明（可选）：', '') || undefined;
        if (!when && !owner && !notes) {
            return;
        }
        let scheduledFor = when;
        if (when) {
            const parsed = new Date(when);
            if (!Number.isNaN(parsed.getTime())) {
                scheduledFor = parsed.toISOString();
            }
        }
        try {
            const resp = await fetch(`${API_BASE}/tasks/${taskId}/schedule`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    scheduled_for: scheduledFor,
                    owner,
                    notes
                })
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            this.addActivity('🗂️', `任务 ${taskId} 已排期`);
            this.loadPlanningTasks();
            this.refreshTasks(true);
        } catch (error) {
            this.addMessage('assistant', `❌ 排期失败：${error.message}`);
        }
    }

    async executePlanningTask(taskId) {
        const task = this.getPlanningTask(taskId);
        const summary = prompt('请输入任务执行摘要（将写回RAG，可选）：', task?.description?.slice(0, 120) || '');
        const resourceNote = (document.getElementById('task-resource-impact-text')?.value || '').trim();
        const body = {
            writeback_to_rag: this.taskAutoRag && !!summary,
            rag_title: summary ? `${task?.title || '任务'} · 执行纪要` : undefined,
            rag_summary: summary || undefined,
            rag_tags: task?.tags
        };
        if (this.taskAutoResource) {
            body.resource_impact = {
                summary: resourceNote || `任务 ${task?.title || taskId} 执行完成`,
                category: 'task',
                severity: task?.priority === 'high' ? 'high' : 'medium',
                delta: task?.estimated_duration ? `耗时 ${task.estimated_duration} 分钟` : undefined,
                owner: task?.owner || 'user'
            };
        }
        try {
            const resp = await fetch(`${API_BASE}/tasks/${taskId}/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            this.addActivity('⚙️', `任务 ${taskId} 执行完成`);
            this.loadPlanningTasks();
            this.refreshTasks(true);
            this.loadTaskImpacts();
            this.loadResourceOverview();
            if (data.execution_time) {
                this.addMessage('assistant', `执行耗时 ${(data.execution_time / 60).toFixed(2)} 分钟`);
            }
        } catch (error) {
            this.addMessage('assistant', `❌ 执行任务失败：${error.message}`);
        }
    }

    async retrospectPlanningTask(taskId) {
        const task = this.getPlanningTask(taskId);
        const success = window.confirm('任务是否成功完成？');
        const summary = prompt('复盘总结：', '') || '';
        const lessonsRaw = prompt('关键经验（用逗号分隔，可选）：', '') || '';
        const lessons = lessonsRaw ? lessonsRaw.split(/[,，]/).map(s => s.trim()).filter(Boolean) : undefined;
        try {
            const payload = { success, summary };
            if (lessons && lessons.length) {
                payload.lessons = lessons;
            }
            const resp = await fetch(`${API_BASE}/tasks/${taskId}/retrospect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            this.addActivity(success ? '🏁' : '📉', `已复盘任务 ${taskId}`);
            this.loadPlanningTasks();
            this.refreshTasks(true);
            if (this.taskAutoRag && summary) {
                try {
                    const ragResp = await fetch(`${API_BASE}/task-loop/rag-writeback`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            task_id: taskId,
                            title: `${task?.title || '任务'} · 复盘总结`,
                            summary,
                            content: summary,
                            tags: task?.tags,
                            metadata: { phase: 'retrospect' }
                        })
                    });
                    if (!ragResp.ok) {
                        throw new Error(`HTTP ${ragResp.status}`);
                    }
                } catch (ragError) {
                    console.warn('复盘写回RAG失败:', ragError);
                }
            }
        } catch (error) {
            this.addMessage('assistant', `❌ 复盘失败：${error.message}`);
        }
    }

    async loadTaskImpacts() {
        try {
            const resp = await fetch(`${API_BASE}/resources/task-impacts?limit=6`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            this.taskImpacts = data.impacts || [];
            this.renderTaskImpacts();
        } catch (error) {
            console.warn('加载任务资源影响失败:', error);
        }
    }

    renderTaskImpacts() {
        const list = document.getElementById('task-impact-list');
        if (!list) return;
        if (!this.taskImpacts.length) {
            list.innerHTML = '<div style="color:#666;">暂无资源影响记录</div>';
            return;
        }
        list.innerHTML = this.taskImpacts.map(impact => {
            const ts = this.formatRelativeTime(impact.timestamp);
            return `<div>⚡ ${impact.summary || ''} <span style="color:#777;">(${impact.severity || 'medium'} · ${ts})</span></div>`;
        }).join('');
    }

    async applyLearningRecommendation(recId) {
        try {
            const resp = await fetch(`${API_BASE}/learning/recommendations/${recId}/apply`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            this.addActivity('🧠', `已执行学习建议 (${data.result?.type || 'info'})`);
            this.loadLearningStats(true);
            this.loadResourceOverview();
            this.loadTaskImpacts();
        } catch (error) {
            this.addMessage('assistant', `❌ 执行建议失败：${error.message}`);
        }
    }

    formatRelativeTime(timestamp) {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        if (Number.isNaN(date.getTime())) return timestamp;
        const diffMs = Date.now() - date.getTime();
        const minutes = Math.floor(diffMs / 60000);
        if (minutes < 1) return '刚刚';
        if (minutes < 60) return `${minutes} 分钟前`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours} 小时前`;
        const days = Math.floor(hours / 24);
        return `${days} 天前`;
    }
    
    // ==================== P3-014: 编程助手功能 ====================
    
    async loadCodingAssistantPanel() {
        // 检查是否有代码相关的命令，显示编程助手面板
        const cmdInput = document.getElementById('terminal-command');
        if (cmdInput && cmdInput.value) {
            const cmd = cmdInput.value.toLowerCase();
            const codingKeywords = ['code', 'review', 'optimize', 'doc', 'python', 'js', 'ts', '.py', '.js', '.ts'];
            const showPanel = codingKeywords.some(kw => cmd.includes(kw));
            const panel = document.getElementById('coding-assistant-panel');
            if (panel) {
                panel.style.display = showPanel ? 'block' : 'none';
            }
        }
    }
    
    async showCodeReview() {
        const cmdInput = document.getElementById('terminal-command');
        const output = document.getElementById('coding-assistant-output');
        if (!cmdInput || !output) return;
        
        const filePath = cmdInput.value.trim();
        if (!filePath) {
            alert('请先输入文件路径');
            return;
        }
        
        try {
            // 读取文件内容
            const fileContent = await this.readFileContent(filePath);
            if (!fileContent) {
                output.textContent = '无法读取文件内容';
                output.style.display = 'block';
                return;
            }
            
            // 调用代码审查API
            const response = await fetch(`${API_BASE}/coding/review`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: fileContent, language: 'python' })
            });
            
            const result = await response.json();
            if (result.success) {
                const issues = result.issues || [];
                const summary = result.summary || {};
                output.innerHTML = `
                    <div style="margin-bottom:8px;"><strong>代码审查结果</strong></div>
                    <div>总计: ${summary.total_issues || 0} 问题</div>
                    <div>严重: ${summary.critical || 0} | 高: ${summary.high || 0} | 中: ${summary.medium || 0} | 低: ${summary.low || 0}</div>
                    <div style="margin-top:8px;max-height:150px;overflow-y:auto;">
                        ${issues.slice(0, 10).map(issue => `
                            <div style="margin:4px 0;padding:4px;background:#2a2a2a;border-radius:4px;">
                                <span style="color:${issue.severity === 'critical' ? '#ff4444' : issue.severity === 'high' ? '#ff8844' : '#ffaa44'}">[${issue.severity}]</span>
                                ${issue.message} (行 ${issue.line || '?'})
                            </div>
                        `).join('')}
                    </div>
                `;
                output.style.display = 'block';
            } else {
                output.textContent = `审查失败: ${result.error || '未知错误'}`;
                output.style.display = 'block';
            }
        } catch (error) {
            output.textContent = `错误: ${error.message}`;
            output.style.display = 'block';
        }
    }
    
    async showCodeOptimize() {
        const cmdInput = document.getElementById('terminal-command');
        const output = document.getElementById('coding-assistant-output');
        if (!cmdInput || !output) return;
        
        const filePath = cmdInput.value.trim();
        if (!filePath) {
            alert('请先输入文件路径');
            return;
        }
        
        try {
            const fileContent = await this.readFileContent(filePath);
            if (!fileContent) {
                output.textContent = '无法读取文件内容';
                output.style.display = 'block';
                return;
            }
            
            const response = await fetch(`${API_BASE}/coding/optimize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    problem_description: '优化代码性能',
                    context: { code: fileContent, language: 'python' }
                })
            });
            
            const result = await response.json();
            if (result.success && result.optimization) {
                const opt = result.optimization;
                output.innerHTML = `
                    <div style="margin-bottom:8px;"><strong>性能优化建议</strong></div>
                    <div>${opt.expected_improvement || '性能提升'}</div>
                    <div style="margin-top:8px;">
                        <strong>建议:</strong>
                        <ul style="margin:4px 0;padding-left:20px;">
                            ${(opt.suggestions || []).slice(0, 5).map(s => `<li>${s}</li>`).join('')}
                        </ul>
                    </div>
                `;
                output.style.display = 'block';
            } else {
                output.textContent = `优化失败: ${result.error || '未知错误'}`;
                output.style.display = 'block';
            }
        } catch (error) {
            output.textContent = `错误: ${error.message}`;
            output.style.display = 'block';
        }
    }
    
    async showGenerateDoc() {
        const cmdInput = document.getElementById('terminal-command');
        const output = document.getElementById('coding-assistant-output');
        if (!cmdInput || !output) return;
        
        const filePath = cmdInput.value.trim();
        if (!filePath) {
            alert('请先输入文件路径');
            return;
        }
        
        try {
            const fileContent = await this.readFileContent(filePath);
            if (!fileContent) {
                output.textContent = '无法读取文件内容';
                output.style.display = 'block';
                return;
            }
            
            const response = await fetch(`${API_BASE}/coding/documentation/generate-docstring`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: fileContent, language: 'python', style: 'google' })
            });
            
            const result = await response.json();
            if (result.success && result.docstrings) {
                output.innerHTML = `
                    <div style="margin-bottom:8px;"><strong>生成的文档字符串</strong></div>
                    <div style="max-height:150px;overflow-y:auto;font-family:monospace;font-size:11px;">
                        ${result.docstrings.map(ds => `
                            <div style="margin:4px 0;padding:4px;background:#2a2a2a;border-radius:4px;">
                                <div><strong>${ds.name}</strong> (${ds.type}) - 行 ${ds.line}</div>
                                <pre style="margin:4px 0;white-space:pre-wrap;">${ds.docstring}</pre>
                            </div>
                        `).join('')}
                    </div>
                `;
                output.style.display = 'block';
            } else {
                output.textContent = `生成失败: ${result.error || '未知错误'}`;
                output.style.display = 'block';
            }
        } catch (error) {
            output.textContent = `错误: ${error.message}`;
            output.style.display = 'block';
        }
    }
    
    async openInCursor() {
        const cmdInput = document.getElementById('terminal-command');
        if (!cmdInput) return;
        
        const filePath = cmdInput.value.trim();
        if (!filePath) {
            alert('请先输入文件路径');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/coding/cursor/open-file-enhanced`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_path: filePath })
            });
            
            const result = await response.json();
            if (result.success) {
                this.addActivity('💻', `已在Cursor中打开: ${filePath}`);
            } else {
                alert(`打开失败: ${result.error || '未知错误'}`);
            }
        } catch (error) {
            alert(`错误: ${error.message}`);
        }
    }
    
    async showCommandReplay() {
        try {
            const response = await fetch(`${API_BASE}/coding/command-replay/history?limit=20`);
            const result = await response.json();
            
            if (result.success) {
                const history = result.history || [];
                const output = document.getElementById('terminal-output');
                if (output) {
                    if (history.length === 0) {
                        output.textContent = '暂无命令回放历史';
                    } else {
                        output.textContent = history.map((h, idx) => {
                            const cmd = h.command || '';
                            const result = h.result || {};
                            const success = result.success ? '✅' : '❌';
                            return `${idx + 1}. ${success} ${cmd} (${h.timestamp || ''})`;
                        }).join('\n');
                    }
                }
            }
        } catch (error) {
            console.error('加载命令回放历史失败:', error);
        }
    }
    
    async showSandboxStatus() {
        try {
            const response = await fetch(`${API_BASE}/coding/sandbox/main-interface-status`);
            const result = await response.json();
            
            if (result.success) {
                const output = document.getElementById('terminal-output');
                if (output) {
                    output.textContent = [
                        `沙箱状态: ${result.sandbox_enabled ? '✅ 已启用' : '❌ 未启用'}`,
                        `沙箱目录: ${result.sandbox_dir || '未设置'}`,
                        `命令历史: ${result.command_history_count || 0} 条`,
                        `回放历史: ${result.replay_history_count || 0} 条`,
                        `Cursor可用: ${result.cursor_available ? '✅' : '❌'}`
                    ].join('\n');
                }
            }
        } catch (error) {
            console.error('加载沙箱状态失败:', error);
        }
    }
    
    async readFileContent(filePath) {
        // 简化实现：通过API读取文件
        // 真实实现应该调用文件读取API
        try {
            // 这里应该调用文件读取API，暂时返回null
            return null;
        } catch (error) {
            console.error('读取文件失败:', error);
            return null;
        }
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
                
                // P3-014: 安全沙箱与主界面联动
                if (result.success && result.command_id) {
                    try {
                        await fetch(`${API_BASE}/coding/sandbox/link-main-interface`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                command_id: result.command_id,
                                action: 'execute'
                            })
                        });
                    } catch (linkError) {
                        console.warn('联动主界面失败:', linkError);
                    }
                }
            } else {
                if (out) out.textContent += `执行失败：HTTP ${resp.status}\n`;
            }
        } catch (e) {
            if (out) out.textContent += `执行异常：${e.message}\n`;
        }
    }

    async loadVoiceLanguages() {
        try {
            const response = await fetch(`${API_BASE}/voice/languages`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            this.voiceLanguages = data.languages || [];
            this.renderVoiceLanguages(this.voiceLanguages, data.current || this.ttsLanguage);
        } catch (error) {
            if (!this.voiceLanguages || this.voiceLanguages.length === 0) {
                this.voiceLanguages = ['zh-CN', 'en-US'];
            }
            this.renderVoiceLanguages(this.voiceLanguages, this.ttsLanguage);
            console.warn('加载语音语言失败:', error);
        }
    }

    renderVoiceLanguages(languages, current) {
        const select = document.getElementById('voice-lang-select');
        if (!select) return;
        select.innerHTML = '';
        const list = (languages && languages.length > 0) ? languages : [current || 'zh-CN'];
        list.forEach(lang => {
            const option = document.createElement('option');
            option.value = lang;
            option.textContent = lang;
            select.appendChild(option);
        });
        select.value = current || this.ttsLanguage;
    }

    changeVoiceLanguage(language) {
        if (!language) return;
        this.ttsLanguage = language;
        try {
            localStorage.setItem('ttsLanguage', language);
        } catch (_) {}
        this.addActivity('🎧', `语音语言切换为 ${language}`);
    }

    startFallbackRecording() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.addMessage('assistant', '❌ 当前浏览器不支持语音输入，请使用最新的 Chrome / Edge。');
            return;
        }
        if (this.isFallbackRecording) {
            this.stopFallbackRecording();
            return;
        }
        this.isFallbackRecording = true;
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            voiceBtn.style.background = 'var(--warning-color)';
            voiceBtn.textContent = '⏺️ 录音中';
        }
        this.addMessage('assistant', '🎙️ 正在录音（约5秒）...', true);
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                this.fallbackStream = stream;
                this.mediaRecorder = new MediaRecorder(stream);
                const chunks = [];
                this.mediaRecorder.ondataavailable = (event) => {
                    if (event.data && event.data.size) {
                        chunks.push(event.data);
                    }
                };
                this.mediaRecorder.onstop = async () => {
                    this.isFallbackRecording = false;
                    if (voiceBtn) {
                        voiceBtn.style.background = '';
                        voiceBtn.textContent = '🎤';
                    }
                    const blob = new Blob(chunks, { type: 'audio/webm' });
                    chunks.length = 0;
                    if (this.fallbackStream) {
                        this.fallbackStream.getTracks().forEach(track => track.stop());
                        this.fallbackStream = null;
                    }
                    await this.uploadVoiceBlob(blob);
                };
                this.mediaRecorder.start();
                setTimeout(() => {
                    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                        this.mediaRecorder.stop();
                    }
                }, 5000);
            })
            .catch(error => {
                this.isFallbackRecording = false;
                if (voiceBtn) {
                    voiceBtn.style.background = '';
                    voiceBtn.textContent = '🎤';
                }
                this.addMessage('assistant', `❌ 无法访问麦克风：${error.message}`);
            });
    }

    stopFallbackRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        if (this.fallbackStream) {
            this.fallbackStream.getTracks().forEach(track => track.stop());
            this.fallbackStream = null;
        }
        this.isFallbackRecording = false;
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            voiceBtn.style.background = '';
            voiceBtn.textContent = '🎤';
        }
    }

    async uploadVoiceBlob(blob) {
        try {
            const formData = new FormData();
            formData.append('audio_data', blob, 'voice.webm');
            const languageParam = encodeURIComponent(this.ttsLanguage || 'zh-CN');
            const response = await fetch(`${API_BASE}/voice/recognize?language=${languageParam}`, {
                method: 'POST',
                body: formData
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            if (data && data.text) {
                this.handleVoiceRecognitionResult(data.text);
            } else {
                this.addMessage('assistant', '❌ 语音识别失败：未获取到文本');
            }
        } catch (error) {
            this.addMessage('assistant', `❌ 上传语音失败: ${error.message}`);
        }
    }

    handleVoiceRecognitionResult(text) {
        if (!text) {
            this.addActivity('⚠️', '语音识别失败');
            return;
        }
        const input = document.getElementById('chat-input');
        if (input) {
            input.value = text;
        }
        this.addActivity('🎙️', `语音识别：${text.slice(0, 24)}${text.length > 24 ? '…' : ''}`);
        this.sendMessage();
    }

    async loadSearchEngines(force = false) {
        try {
            const response = await fetch(`${API_BASE}/search/engines`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            this.searchEngines = data.engines || {};
            if (!this.selectedSearchEngines.length || force) {
                this.selectedSearchEngines = Object.keys(this.searchEngines).filter(engine => this.searchEngines[engine].enabled);
            }
            try {
                localStorage.setItem('selectedSearchEngines', JSON.stringify(this.selectedSearchEngines));
            } catch (_) {}
            this.renderSearchEngines();
        } catch (error) {
            console.warn('搜索引擎列表加载失败:', error);
            const container = document.getElementById('search-engine-list');
            if (container) {
                container.innerHTML = '<span style="color:#666;">无法加载搜索引擎</span>';
            }
        }
    }

    renderSearchEngines() {
        const container = document.getElementById('search-engine-list');
        if (!container) return;
        container.innerHTML = '';
        const entries = Object.entries(this.searchEngines || {});
        if (!entries.length) {
            container.innerHTML = '<span style="color:#666;">暂无可用引擎</span>';
            return;
        }
        entries.forEach(([name, config]) => {
            const label = document.createElement('label');
            label.style.cssText = 'display:flex;align-items:center;gap:6px;border:1px solid #222;border-radius:999px;padding:2px 10px;font-size:12px;';
            label.className = 'engine-pill';
            const input = document.createElement('input');
            input.type = 'checkbox';
            input.value = name;
            input.checked = this.selectedSearchEngines.includes(name);
            input.disabled = !config.enabled;
            input.addEventListener('change', () => this.handleSearchEngineToggle(name, input.checked));
            const span = document.createElement('span');
            span.textContent = name;
            span.style.color = config.enabled ? '#ddd' : '#555';
            label.appendChild(input);
            label.appendChild(span);
            container.appendChild(label);
        });
    }

    handleSearchEngineToggle(engine, checked) {
        if (checked) {
            if (!this.selectedSearchEngines.includes(engine)) {
                this.selectedSearchEngines.push(engine);
            }
        } else {
            this.selectedSearchEngines = this.selectedSearchEngines.filter(e => e !== engine);
        }
        try {
            localStorage.setItem('selectedSearchEngines', JSON.stringify(this.selectedSearchEngines));
        } catch (_) {}
    }

    renderSearchResultsPanel(result, query) {
        const panel = document.getElementById('search-results-panel');
        const badge = document.getElementById('search-query-badge');
        if (badge) {
            badge.textContent = query ? `最近搜索：${query}` : '暂无搜索';
        }
        if (!panel) return;
        panel.innerHTML = '';
        if (!result || !result.results || result.results.length === 0) {
            panel.innerHTML = '<div style="color:#666;">暂无搜索结果</div>';
            return;
        }
        const engines = (result.engines_used || this.selectedSearchEngines || []).join(', ') || 'auto';
        const meta = document.createElement('div');
        meta.style.color = '#888';
        meta.style.marginBottom = '4px';
        meta.textContent = `引擎：${engines} · 结果 ${result.total_results ?? result.total ?? result.results.length}`;
        panel.appendChild(meta);
        result.results.slice(0, 5).forEach((item, index) => {
            const block = document.createElement('div');
            block.style.marginBottom = '6px';
            block.innerHTML = `<strong>${index + 1}. ${item.title || '无标题'}</strong><br><span style="color:#aaa;">${item.snippet ? item.snippet.substring(0, 140) : ''}</span>`;
            if (item.url) {
                const link = document.createElement('a');
                link.href = item.url;
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                link.textContent = item.url;
                link.style.display = 'block';
                link.style.color = '#5dade2';
                block.appendChild(link);
            }
            panel.appendChild(block);
        });
    }

    async loadLearningStats(force = false) {
        try {
            const response = await fetch(`${API_BASE}/learning/statistics`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const stats = await response.json();
            this.renderLearningStats(stats);
        } catch (error) {
            this.renderLearningStats(null, error.message);
        }
    }

    renderLearningStats(stats, errorMessage) {
        const grid = document.getElementById('learning-stats-grid');
        const trendEl = document.getElementById('learning-trend');
        const suggestionsEl = document.getElementById('learning-suggestions');
        const alertEl = document.getElementById('learning-alert');
        const signalsEl = document.getElementById('learning-resource-signals');
        if (!grid || !trendEl || !suggestionsEl || !alertEl || !signalsEl) return;
        if (!stats) {
            grid.innerHTML = `<div style="grid-column:span 2;color:#666;">${errorMessage || '无法获取自我学习状态'}</div>`;
            trendEl.textContent = '性能趋势：--';
            alertEl.textContent = '告警级别：--';
            suggestionsEl.innerHTML = '<div style="color:#666;">暂无建议</div>';
            signalsEl.innerHTML = '<div style="color:#666;">暂无资源信号</div>';
            return;
        }
        grid.innerHTML = `
            <div>流程总数<br><strong>${stats.total_workflows || 0}</strong></div>
            <div>问题数<br><strong>${stats.total_problems || 0}</strong></div>
            <div>解决方案<br><strong>${stats.total_solutions || 0}</strong></div>
            <div>平均响应(秒)<br><strong>${(stats.average_response_time || 0).toFixed ? (stats.average_response_time || 0).toFixed(2) : stats.average_response_time || 0}</strong></div>
        `;
        const trend = stats.performance_trend?.trend || '未知';
        trendEl.textContent = `性能趋势：${trend}`;
        alertEl.textContent = `告警级别：${(stats.alert_level || 'low').toUpperCase()}`;

        const recs = stats.interaction_recommendations || [];
        if (recs.length) {
            suggestionsEl.innerHTML = '';
            recs.forEach(rec => {
                const card = document.createElement('div');
                card.style.border = '1px solid #222';
                card.style.borderRadius = '6px';
                card.style.padding = '6px';
                card.innerHTML = `
                    <div style="display:flex;justify-content:space-between;">
                        <span>${rec.title || '建议'}</span>
                        <span style="color:#888;font-size:11px;">${(rec.severity || '').toUpperCase()}</span>
                    </div>
                    <div style="color:#aaa;font-size:12px;margin:4px 0;">${rec.description || ''}</div>
                `;
                const btn = document.createElement('button');
                btn.className = 'action-btn-small';
                btn.textContent = rec.action_type === 'resource_authorization' ? '执行授权' : '查看指引';
                btn.dataset.learningAction = 'apply';
                btn.dataset.recId = rec.id;
                card.appendChild(btn);
                suggestionsEl.appendChild(card);
            });
        } else {
            suggestionsEl.innerHTML = '<div style="color:#666;">暂无建议</div>';
        }
        const optSuggestions = stats.optimization_suggestions || [];
        if (optSuggestions.length) {
            suggestionsEl.insertAdjacentHTML('beforeend', `<div style="color:#888;">其他建议：${optSuggestions.join('；')}</div>`);
        }

        const signals = stats.resource_signals || [];
        if (signals.length) {
            signalsEl.innerHTML = signals.map(sig => `• ${sig.resource} ${sig.value}% (阈值 ${sig.threshold}%) — ${sig.suggestion}`).join('<br>');
        } else {
            signalsEl.innerHTML = '<div style="color:#666;">暂无资源信号</div>';
        }
    }

    renderResourceAlerts(alerts) {
        const alertEl = document.getElementById('resource-alerts');
        if (!alertEl) return;
        if (!alerts || alerts.length === 0) {
            alertEl.textContent = '';
            return;
        }
        const topAlert = alerts[alerts.length - 1];
        alertEl.textContent = `⚠️ ${topAlert.suggestion || topAlert.message || '资源告警'}（${Math.round(topAlert.value || 0)}%）`;
    }

    renderExternalDrives(drives) {
        const container = document.getElementById('external-drive-list');
        if (!container) return;
        if (!drives || drives.length === 0) {
            container.textContent = '';
            return;
        }
        container.innerHTML = drives.map(d => `外接 ${d.mountpoint || d.device}: ${Math.round(d.percent || 0)}%`).join(' · ');
    }

    async loadModelConfig() {
        try {
            const response = await fetch(`${API_BASE}/llm/config`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            const metaEl = document.getElementById('model-meta');
            if (metaEl) {
                metaEl.textContent = `LLM：${data.provider || '-'} · ${data.model || '-'}`;
            }
            const modelSelector = document.getElementById('model-selector');
            if (modelSelector && data.model) {
                const option = Array.from(modelSelector.options).find(opt => opt.value === data.model);
                if (option) {
                    modelSelector.value = data.model;
                }
            }
        } catch (error) {
            const metaEl = document.getElementById('model-meta');
            if (metaEl) {
                metaEl.textContent = 'LLM：未加载';
            }
            console.warn('加载LLM配置失败:', error);
        }
    }

    updateTaskSummaryCard(stats) {
        const el = document.getElementById('task-summary-content');
        if (!el) return;
        try {
            const orch = stats.orch || {};
            const plan = stats.plan || {};
            // 简单完成率估计（完成 / (完成+进行中+已确认)）
            const denom = (plan.completed || 0) + (plan.in_progress || 0) + (plan.confirmed || 0);
            const rateEst = denom > 0 ? Math.round((plan.completed / denom) * 100) : 0;
            // 拉取24h真实完成率
            const apply24h = async () => {
                try {
                    const r = await fetch(`${API_BASE}/tasks/summary/24h`);
                    if (r.ok) {
                        const j = await r.json();
                        const rate24 = j?.plan?.completion_rate ?? rateEst;
                        el.textContent = `编排器：总 ${orch.total || 0} · 阻塞 ${orch.blocked || 0}（本页 ${orch.page || 0}）\n规划：总 ${plan.total || 0} · 已确认 ${plan.confirmed || 0} · 进行中 ${plan.in_progress || 0} · 已完成 ${plan.completed || 0} · 已拒绝 ${plan.rejected || 0}（本页 ${plan.page || 0}）\n完成率（24h）：${Math.round(rate24)}%（估：${rateEst}%）`;
                        return;
                    }
                } catch(_) {}
                el.textContent = `编排器：总 ${orch.total || 0} · 阻塞 ${orch.blocked || 0}（本页 ${orch.page || 0}）\n规划：总 ${plan.total || 0} · 已确认 ${plan.confirmed || 0} · 进行中 ${plan.in_progress || 0} · 已完成 ${plan.completed || 0} · 已拒绝 ${plan.rejected || 0}（本页 ${plan.page || 0}）\n完成率（估）：${rateEst}%`;
            };
            apply24h();
        } catch (_) {
            el.textContent = '任务概览不可用';
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
            // 编排器筛选（关键字+状态）
            const oqEl = document.getElementById('task-orch-q');
            const osEl = document.getElementById('task-orch-status');
            const oq = oqEl ? (oqEl.value || '').toLowerCase() : '';
            const os = osEl ? (osEl.value || '') : '';
            if (oq) {
                const contains2 = (txt) => (String(txt || '').toLowerCase().includes(oq));
                orchTasks = orchTasks.filter(t => contains2(t.task_id) || contains2(t.title) || contains2(t.status));
            }
            if (os) {
                orchTasks = orchTasks.filter(t => String(t.status || '').toLowerCase() === os);
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
            // 编排器统计（本页/总数/blocked）
            const orchStats = document.createElement('div');
            orchStats.className = 'activity-item';
            orchStats.style.color = '#aaa';
            const blockedAll = orchTasks.filter(t => String(t.status || '').toLowerCase() === 'blocked').length;
            orchStats.textContent = `本页 ${orchPage.length} · 总数 ${orchTasks.length} · 阻塞 ${blockedAll}`;
            listEl.appendChild(orchStats);
            // 分页控制（编排器）
            const orchPager = document.createElement('div');
            orchPager.className = 'activity-item';
            const orchPrev = document.createElement('button'); orchPrev.className='action-btn-small'; orchPrev.textContent='上一页';
            orchPrev.onclick = () => { if (this.taskPageOrch > 1) { this.taskPageOrch--; try { localStorage.setItem('taskPageOrch', String(this.taskPageOrch)); } catch(_) {} this.refreshTasks(true); } };
            const orchNext = document.createElement('button'); orchNext.className='action-btn-small'; orchNext.textContent='下一页';
            orchNext.onclick = () => { if (this.taskPageOrch < orchTotalPages) { this.taskPageOrch++; try { localStorage.setItem('taskPageOrch', String(this.taskPageOrch)); } catch(_) {} this.refreshTasks(true); } };
            orchPager.appendChild(orchPrev); orchPager.appendChild(orchNext);
            listEl.appendChild(orchPager);
            orchPage.forEach(t => {
                const item = document.createElement('div');
                item.className = 'activity-item';
                // 长按菜单：编排器任务
                this.attachLongPressMenu(item, () => this.buildOrchestratorTaskMenu(t));
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
                // 可视化阻塞标识
                if (String(t.status || '').toLowerCase() === 'blocked') {
                    item.style.border = '1px solid #7a1a1a';
                    item.style.borderRadius = '6px';
                    item.style.position = 'relative';
                    const badge = document.createElement('span');
                    badge.textContent = 'Blocked';
                    badge.style.position = 'absolute';
                    badge.style.left = '8px';
                    badge.style.top = '-8px';
                    badge.style.background = '#5a1010';
                    badge.style.color = '#f2dede';
                    badge.style.border = '1px solid #7a1a1a';
                    badge.style.fontSize = '11px';
                    badge.style.padding = '2px 6px';
                    badge.style.borderRadius = '999px';
                    item.appendChild(badge);
                }
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
            // 规划统计（本页/总数/已确认/进行中/已完成/已拒绝）
            const planStats = document.createElement('div');
            planStats.className = 'activity-item';
            planStats.style.color = '#aaa';
            const countConfirmed = tasks.filter(t => String(t.status || '').toLowerCase() === 'confirmed').length;
            const countInProgress = tasks.filter(t => String(t.status || '').toLowerCase() === 'in_progress').length;
            const countCompleted = tasks.filter(t => String(t.status || '').toLowerCase() === 'completed').length;
            const countRejected = tasks.filter(t => String(t.status || '').toLowerCase() === 'rejected').length;
            planStats.textContent = `本页 ${planPage.length} · 总数 ${tasks.length} · 已确认 ${countConfirmed} · 进行中 ${countInProgress} · 已完成 ${countCompleted} · 已拒绝 ${countRejected}`;
            listEl.appendChild(planStats);
            // 分页控制（规划）
            const planPager = document.createElement('div');
            planPager.className = 'activity-item';
            const planPrev = document.createElement('button'); planPrev.className='action-btn-small'; planPrev.textContent='上一页';
            planPrev.onclick = () => { if (this.taskPagePlan > 1) { this.taskPagePlan--; try { localStorage.setItem('taskPagePlan', String(this.taskPagePlan)); } catch(_) {} this.refreshTasks(true); } };
            const planNext = document.createElement('button'); planNext.className='action-btn-small'; planNext.textContent='下一页';
            planNext.onclick = () => { if (this.taskPagePlan < planTotalPages) { this.taskPagePlan++; try { localStorage.setItem('taskPagePlan', String(this.taskPagePlan)); } catch(_) {} this.refreshTasks(true); } };
            planPager.appendChild(planPrev); planPager.appendChild(planNext);
            listEl.appendChild(planPager);
            planPage.forEach(t => {
                const item = document.createElement('div');
                item.className = 'activity-item';
                // 长按菜单（移动端/桌面均可用）
                this.attachLongPressMenu(item, () => this.buildPlanningTaskMenu(t));
                // 勾选框（批量）
                const sel = document.createElement('input');
                sel.type = 'checkbox';
                sel.checked = this.selectedPlanTaskIds.has(t.id);
                sel.style.marginRight = '6px';
                sel.onchange = () => {
                    if (sel.checked) {
                        this.selectedPlanTaskIds.add(t.id);
                    } else {
                        this.selectedPlanTaskIds.delete(t.id);
                    }
                    this.updateBulkCount();
                    // 勾选即时提示（1.5s自动消失）
                    try {
                        const guardEl = document.getElementById('task-delete-guard');
                        const guardOn = guardEl ? guardEl.checked : false;
                        const st = String(t.status || '').toLowerCase();
                        const canConfirm = (st === 'pending' || st === 'created');
                        const canExec = (st === 'confirmed');
                        const canReject = (st !== 'completed' && st !== 'rejected');
                        const canDelete = guardOn ? (st === 'rejected' || st === 'completed') : true;
                        if (sel.checked) {
                            const hintParts = [];
                            if (canConfirm) hintParts.push('可确认');
                            if (canExec) hintParts.push('可执行');
                            if (canReject) hintParts.push('可拒绝');
                            if (canDelete) hintParts.push(`可删除${guardOn ? '(守护)' : ''}`);
                            const txt = `状态：${st || '未知'} · ${hintParts.join(' / ') || '无可操作'}`;
                            // 颜色优先级：执行(蓝) > 删除(红) > 确认(绿) > 拒绝(橙) > 默认(灰)
                            let color = '#2b2b2b';
                            if (canExec) color = '#10345a';
                            else if (canDelete) color = '#5a1010';
                            else if (canConfirm) color = '#0b3d0b';
                            else if (canReject) color = '#5a3a10';
                            this.showTransientHint(item, txt, color);
                        } else {
                            this.showTransientHint(item, '已移除选择', '#3a3a3a');
                        }
                    } catch (_) {}
                };
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
            // 更新系统状态中的任务概览卡片
            this.updateTaskSummaryCard({
                orch: { total: orchTasks.length, blocked: blockedAll, page: orchPage.length },
                plan: {
                    total: tasks.length,
                    confirmed: countConfirmed,
                    in_progress: countInProgress,
                    completed: countCompleted,
                    rejected: countRejected,
                    page: planPage.length
                }
            });
            // 更新任务中心标题徽标（24h完成率）
            this.updateTaskCenterBadge();
            // 统计提示（基于当前页）
            try {
                const hintEl = document.getElementById('task-bulk-hint');
                if (hintEl) {
                    const guardEl = document.getElementById('task-delete-guard');
                    const guardOn = guardEl ? guardEl.checked : false;
                    let confirmable = 0, executable = 0, rejectable = 0, deletable = 0;
                    // 已选统计（仅统计当前页内已选项，避免不必要的跨页开销）
                    let selTotal = 0, selConfirmable = 0, selExecutable = 0, selRejectable = 0, selDeletable = 0;
                    planPage.forEach(t => {
                        const st = String(t.status || '').toLowerCase();
                        if (st === 'pending' || st === 'created') confirmable++;
                        if (st === 'confirmed') executable++;
                        if (st !== 'completed' && st !== 'rejected') rejectable++;
                        if (guardOn) {
                            if (st === 'rejected' || st === 'completed') deletable++;
                        } else {
                            deletable++;
                        }
                        if (this.selectedPlanTaskIds.has(t.id)) {
                            selTotal++;
                            if (st === 'pending' || st === 'created') selConfirmable++;
                            if (st === 'confirmed') selExecutable++;
                            if (st !== 'completed' && st !== 'rejected') selRejectable++;
                            if (guardOn) {
                                if (st === 'rejected' || st === 'completed') selDeletable++;
                            } else {
                                selDeletable++;
                            }
                        }
                    });
                    hintEl.textContent = `可确认 ${confirmable}（已选 ${selConfirmable}/${selTotal}） · 可执行 ${executable}（已选 ${selExecutable}/${selTotal}） · 可拒绝 ${rejectable}（已选 ${selRejectable}/${selTotal}） · 可删除 ${deletable}（已选 ${selDeletable}/${selTotal}）${guardOn?'（守护开）':'（守护关）'}`;
                    // 设置各批量按钮的悬浮提示
                    const btnConfirm = document.getElementById('task-bulk-confirm');
                    const btnExec = document.getElementById('task-bulk-execute');
                    const btnReject = document.getElementById('task-bulk-reject');
                    const btnDelete = document.getElementById('task-bulk-delete');
                    if (btnConfirm) btnConfirm.title = `将确认已选 ${selConfirmable}/${selTotal}（本页可确认 ${confirmable}）`;
                    if (btnExec) btnExec.title = `将执行已选可执行 ${selExecutable}/${selTotal}（本页可执行 ${executable}，仅 confirmed）`;
                    if (btnReject) btnReject.title = `将拒绝已选可拒绝 ${selRejectable}/${selTotal}（本页可拒绝 ${rejectable}，跳过 completed/rejected）`;
                    if (btnDelete) btnDelete.title = `将删除已选可删除 ${selDeletable}/${selTotal}（本页可删除 ${deletable}，守护${guardOn?'开':'关'}）`;
                }
            } catch (_) {}
        } catch (e) {
            // 静默
        }
    }

    buildOrchestratorTaskMenu(task) {
        const oid = task.task_id;
        const items = [];
        items.push({ label: '详情', action: () => window.open(`task_detail.html?oid=${encodeURIComponent(oid)}`, '_blank') });
        items.push({ label: '推送步骤', action: () => this.pushStepsToOrchestratorInline(oid) });
        items.push({ label: '刷新任务', action: async () => {
            try {
                const r = await fetch(`${API_BASE}/tasks/${encodeURIComponent(oid)}`);
                if (r.ok) {
                    this.addActivity('🔄', `已刷新 ${oid}`);
                    this.refreshTasks(true);
                } else {
                    alert('刷新失败');
                }
            } catch (_) { alert('刷新异常'); }
        }});
        items.push({ label: '标记阻塞', action: async () => {
            const reason = prompt('请输入阻塞原因：', '') || '';
            const ok = await this.setOrchestratorStatus(oid, 'blocked', { blocked_reason: reason });
            if (ok) {
                this.addActivity('⛔', `已标记阻塞 ${oid}`);
                this.refreshTasks(true);
                window.open(`task_detail.html?oid=${encodeURIComponent(oid)}&flash=1`, '_blank');
            }
        }});
        items.push({ label: '解除阻塞', action: async () => {
            const ok = await this.setOrchestratorStatus(oid, 'in_progress', {});
            if (ok) {
                this.addActivity('✅', `已解除阻塞 ${oid}`);
                this.refreshTasks(true);
                window.open(`task_detail.html?oid=${encodeURIComponent(oid)}&flash=1`, '_blank');
            }
        }});
        return items;
    }

    async setOrchestratorStatus(taskId, status, updates) {
        try {
            const r = await fetch(`${API_BASE}/tasks/${encodeURIComponent(taskId)}/status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status, updates: updates || {} })
            });
            return r.ok;
        } catch (_) {
            return false;
        }
    }

    buildPlanningTaskMenu(task) {
        const id = task.id;
        const status = String(task.status || '').toLowerCase();
        const items = [];
        // 确认
        if (status === 'pending' || status === 'created') {
            items.push({ label: '确认', action: () => this.confirmTask(id, true) });
        }
        // 执行
        if (status === 'confirmed') {
            items.push({ label: '执行', action: () => this.executeTask(id) });
        }
        // 拒绝
        if (status !== 'completed' && status !== 'rejected') {
            items.push({ label: '拒绝', action: () => this.confirmTask(id, false) });
        }
        // 删除（守护受控）
        items.push({
            label: '删除',
            action: async () => {
                const guardEl = document.getElementById('task-delete-guard');
                const guardOn = guardEl ? guardEl.checked : false;
                if (guardOn && !(status === 'rejected' || status === 'completed')) {
                    alert('守护开启：仅可删除已拒绝/已完成的任务');
                    return;
                }
                const ok = confirm('确认删除该任务？');
                if (!ok) return;
                const r = await fetch(`${API_BASE}/planning/tasks/${id}`, { method: 'DELETE' });
                if (r.ok) {
                    this.addActivity('🗑️', `删除任务 #${id}`);
                    this.refreshTasks(true);
                } else {
                    alert('删除失败');
                }
            }
        });
        // 详情
        items.push({ label: '详情', action: () => window.open(`task_detail.html?pid=${encodeURIComponent(id)}`, '_blank') });
        return items;
    }

    attachLongPressMenu(el, getItemsFn) {
        let timer = null;
        const start = (ev) => {
            ev.preventDefault();
            if (timer) clearTimeout(timer);
            timer = setTimeout(() => {
                const items = getItemsFn();
                if (Array.isArray(items) && items.length > 0) {
                    this.showContextMenu(el, items);
                }
            }, 500); // 0.5s长按
        };
        const cancel = () => {
            if (timer) { clearTimeout(timer); timer = null; }
        };
        el.addEventListener('touchstart', start, { passive: false });
        el.addEventListener('touchend', cancel);
        el.addEventListener('touchmove', cancel);
        el.addEventListener('mousedown', start);
        el.addEventListener('mouseup', cancel);
        el.addEventListener('mouseleave', cancel);
        el.addEventListener('contextmenu', (e) => { e.preventDefault(); const items = getItemsFn(); this.showContextMenu(el, items); });
    }

    showContextMenu(anchorEl, items) {
        // 清理旧菜单
        const old = document.getElementById('task-context-menu');
        if (old && old.parentNode) old.parentNode.removeChild(old);
        const menu = document.createElement('div');
        menu.id = 'task-context-menu';
        menu.style.position = 'absolute';
        menu.style.zIndex = '9999';
        menu.style.background = '#121212';
        menu.style.border = '1px solid #333';
        menu.style.borderRadius = '8px';
        menu.style.boxShadow = '0 6px 20px rgba(0,0,0,0.4)';
        menu.style.minWidth = '140px';
        menu.style.padding = '6px 0';
        items.forEach(it => {
            const btn = document.createElement('div');
            btn.textContent = it.label;
            btn.style.padding = '8px 12px';
            btn.style.cursor = 'pointer';
            btn.style.color = '#ddd';
            btn.onmouseenter = () => { btn.style.background = '#1f1f1f'; };
            btn.onmouseleave = () => { btn.style.background = 'transparent'; };
            btn.onclick = () => {
                try { it.action && it.action(); } finally {
                    if (menu && menu.parentNode) menu.parentNode.removeChild(menu);
                }
            };
            menu.appendChild(btn);
        });
        // 定位：桌面右侧；移动端下方
        const rect = anchorEl.getBoundingClientRect();
        const isMobile = window.matchMedia && window.matchMedia('(max-width: 600px)').matches;
        menu.style.left = `${rect.left + (isMobile ? 0 : rect.width - 10)}px`;
        menu.style.top = `${rect.top + (isMobile ? rect.height + 6 : -6)}px`;
        menu.style.transform = isMobile ? 'translateX(0)' : 'translateX(-100%)';
        menu.style.maxWidth = isMobile ? 'calc(100vw - 24px)' : '240px';
        document.body.appendChild(menu);
        const close = (e) => {
            if (!menu.contains(e.target)) {
                if (menu && menu.parentNode) menu.parentNode.removeChild(menu);
                document.removeEventListener('mousedown', close);
                document.removeEventListener('touchstart', close);
            }
        };
        setTimeout(() => {
            document.addEventListener('mousedown', close);
            document.addEventListener('touchstart', close, { passive: true });
        }, 0);
    }

    showTransientHint(parentEl, text, bgColor = '#1b1b1b') {
        const hint = document.createElement('div');
        hint.textContent = text;
        hint.style.position = 'relative';
        const bubble = document.createElement('div');
        bubble.textContent = text;
        bubble.style.position = 'absolute';
        bubble.style.background = bgColor;
        bubble.style.border = '1px solid #333';
        bubble.style.padding = '4px 8px';
        bubble.style.borderRadius = '6px';
        bubble.style.color = '#ccc';
        bubble.style.fontSize = '12px';
        bubble.style.pointerEvents = 'none';
        bubble.style.boxShadow = '0 2px 6px rgba(0,0,0,0.3)';
        // 自适应移动端：小屏幕放在条目下方并可换行；桌面放右上角
        const isMobile = window.matchMedia && window.matchMedia('(max-width: 600px)').matches;
        if (isMobile) {
            bubble.style.left = '8px';
            bubble.style.right = '8px';
            bubble.style.bottom = '-28px';
            bubble.style.top = 'auto';
            bubble.style.whiteSpace = 'normal';
            bubble.style.maxWidth = 'calc(100% - 16px)';
            bubble.style.lineHeight = '1.2';
        } else {
            bubble.style.right = '8px';
            bubble.style.top = '-4px';
            bubble.style.whiteSpace = 'nowrap';
        }
        parentEl.style.position = 'relative';
        parentEl.appendChild(bubble);
        setTimeout(() => {
            if (bubble && bubble.parentNode) {
                bubble.parentNode.removeChild(bubble);
            }
        }, 1500);
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
        // 预检：优先对 pending/created 确认
        const statuses = await this.getPlanningStatuses(ids);
        const eligible = ids.filter(id => {
            const st = statuses.get(id);
            return st === 'pending' || st === 'created';
        });
        const ineligible = ids.filter(id => !eligible.includes(id));
        const go = confirm(`批量确认预检：可确认 ${eligible.length} 项（pending/created），不推荐 ${ineligible.length} 项（其他状态）。继续对全部 ${ids.length} 项执行吗？`);
        if (!go) return;
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
        // 预检
        const statuses = await this.getPlanningStatuses(ids);
        const eligible = ids.filter(id => statuses.get(id) === 'confirmed');
        const ineligible = ids.filter(id => !eligible.includes(id));
        const go = confirm(`批量执行预检：符合条件 ${eligible.length} 项（confirmed），不符合 ${ineligible.length} 项。是否继续？`);
        if (!go) return;
        let okCount = 0, skipped = 0;
        for (const id of ids) {
            try {
                // 仅对已确认的任务执行
                const st = statuses.get(id);
                if (st !== 'confirmed') { skipped++; continue; }
                const ex = await fetch(`${API_BASE}/tasks/${id}/execute`, { method: 'POST' });
                if (ex.ok) okCount++; else skipped++;
            } catch (_) { skipped++; }
        }
        this.addActivity('⚙️', `批量执行完成：成功 ${okCount}，跳过 ${skipped}（仅执行已确认任务）`);
        this.refreshTasks(true);
    }
    async bulkReject() {
        if (this.selectedPlanTaskIds.size === 0) { alert('请先选择任务'); return; }
        const reason = prompt('请输入批量拒绝原因（将作用于所有选中任务）：', '') || '';
        const ids = Array.from(this.selectedPlanTaskIds);
        // 预检
        const statuses = await this.getPlanningStatuses(ids);
        const eligible = ids.filter(id => {
            const st = statuses.get(id);
            return st !== 'completed' && st !== 'rejected';
        });
        const ineligible = ids.filter(id => !eligible.includes(id));
        const go = confirm(`批量拒绝预检：可拒绝 ${eligible.length} 项，跳过 ${ineligible.length} 项（已完成/已拒绝）。是否继续？`);
        if (!go) return;
        let okCount = 0, skipped = 0;
        for (const id of ids) {
            try {
                // 不对已完成/已拒绝重复操作
                const st = statuses.get(id);
                if (st === 'completed' || st === 'rejected') { skipped++; continue; }
                const cf = await fetch(`${API_BASE}/tasks/${id}/confirm`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ confirmed: false, reason })
                });
                if (cf.ok) okCount++; else skipped++;
            } catch (_) { skipped++; }
        }
        this.addActivity('🚫', `批量拒绝完成：成功 ${okCount}，跳过 ${skipped}（已完成/已拒绝被跳过）`);
        this.refreshTasks(true);
    }
    async bulkDelete() {
        if (this.selectedPlanTaskIds.size === 0) { alert('请先选择任务'); return; }
        const ok = confirm('确认删除所选规划任务？该操作不可恢复。');
        if (!ok) return;
        const guardEl = document.getElementById('task-delete-guard');
        const guardOn = guardEl ? guardEl.checked : false;
        const ids = Array.from(this.selectedPlanTaskIds);
        // 预检
        const statuses = await this.getPlanningStatuses(ids);
        const eligible = guardOn ? ids.filter(id => {
            const st = statuses.get(id);
            return st === 'rejected' || st === 'completed';
        }) : ids.slice();
        const ineligible = ids.filter(id => !eligible.includes(id));
        const go2 = confirm(`批量删除预检：可删除 ${eligible.length} 项，跳过 ${ineligible.length} 项（守护=${guardOn?'开':'关'}）。是否继续？`);
        if (!go2) return;
        let done = 0;
        let skipped = 0;
        for (const id of ids) {
            try {
                if (guardOn) {
                    if (!eligible.includes(id)) { skipped++; continue; }
                }
                const del = await fetch(`${API_BASE}/planning/tasks/${id}`, { method: 'DELETE' });
                if (del.ok) done++; else skipped++;
            } catch (_) { skipped++; }
        }
        this.selectedPlanTaskIds.clear();
        this.updateBulkCount();
        this.addActivity('🗑️', `批量删除完成：成功 ${done}，跳过 ${skipped}（守护=${guardOn?'开':'关'}）`);
        this.refreshTasks(true);
    }

    // 预检：获取规划任务状态映射
    async getPlanningStatuses(ids) {
        const map = new Map();
        for (const id of ids) {
            try {
                const r = await fetch(`${API_BASE}/planning/tasks/${id}`);
                const j = await r.json();
                if (r.ok && j.task) {
                    map.set(id, String(j.task.status || '').toLowerCase());
                } else {
                    map.set(id, 'unknown');
                }
            } catch (_) {
                map.set(id, 'unknown');
            }
        }
        return map;
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
            const result = await this.requestFileGeneration({
                fileType,
                content,
                title: `生成的文件_${new Date().toISOString().slice(0, 10)}`
            });
            this.removeMessage(loadingId);
            this.downloadGeneratedFile(result, fileType);
            this.addActivity('📄', `生成文件: ${fileType}`);
            if (window.modalSystem) {
                window.modalSystem.showTaskComplete(`生成${fileType}文件`);
            }
        } catch (error) {
            console.error('文件生成失败:', error);
            this.removeMessage(loadingId);
            this.addMessage('assistant', `❌ 文件生成失败: ${error.message}`);
        }
    }

    async requestFileGeneration({ fileType, content, title }) {
        const response = await fetch(`${API_BASE}/generate/file`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_type: fileType,
                content,
                title,
                save_to_rag: true
            })
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const result = await response.json();
        if (!result.success) {
            throw new Error(result.error || '文件生成失败');
        }
        return result;
    }

    downloadGeneratedFile(result, fileType) {
        if (!result) return;
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
        } else {
            this.addMessage('assistant', `✅ 文件已生成：${result.message || '成功'}`);
        }
    }

    async generateFileFromPanel() {
        const typeEl = document.getElementById('filegen-type');
        const titleEl = document.getElementById('filegen-title');
        const contentEl = document.getElementById('filegen-content');
        if (!typeEl || !contentEl) return;
        const fileType = (typeEl.value || 'word').trim();
        const title = (titleEl?.value || `自定义文件_${new Date().toISOString().slice(0, 10)}`).trim();
        const content = (contentEl.value || '').trim();
        if (!content) {
            this.updateFileGeneratorStatus('请输入文件内容', true);
            return;
        }
        this.updateFileGeneratorStatus('⏳ 正在生成...', false);
        try {
            const result = await this.requestFileGeneration({ fileType, content, title });
            this.downloadGeneratedFile(result, fileType);
            this.updateFileGeneratorStatus(`已生成：${result.filename || 'file'}`, false);
        } catch (error) {
            console.error('文件生成失败:', error);
            this.updateFileGeneratorStatus(`失败：${error.message}`, true);
        }
    }

    updateFileGeneratorStatus(message, isError = false) {
        const statusEl = document.getElementById('filegen-status');
        if (!statusEl) return;
        statusEl.textContent = message;
        if (isError) {
            statusEl.style.color = '#ff6b6b';
        } else if (/成功|已生成|完成/.test(message)) {
            statusEl.style.color = '#2ecc71';
        } else {
            statusEl.style.color = '#f5c26b';
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
    
    // P0-014: 运行资源诊断
    async runResourceDiagnostic() {
        const diagnosticContent = document.getElementById('resource-diagnostic-content');
        const runBtn = document.getElementById('run-diagnostic-btn');
        
        if (!diagnosticContent) return;
        
        // 更新按钮状态
        if (runBtn) {
            runBtn.disabled = true;
            runBtn.textContent = '诊断中...';
        }
        
        diagnosticContent.innerHTML = '<div style="color:#888;font-size:11px;">正在运行资源诊断...</div>';
        
        try {
            const response = await fetch(`${API_BASE}/resources/diagnostic/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) {
                throw new Error(`诊断失败: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // 显示诊断结果
                let diagnosticHtml = '';
                
                if (data.diagnostics && data.diagnostics.length > 0) {
                    diagnosticHtml += '<div style="margin-bottom:8px;">';
                    data.diagnostics.forEach((diag, idx) => {
                        const severityColor = {
                            'critical': '#ff4444',
                            'error': '#ff8844',
                            'warning': '#ffaa44',
                            'info': '#44aaff'
                        }[diag.severity] || '#888';
                        
                        diagnosticHtml += `
                            <div style="margin-bottom:6px;padding:6px;border-left:3px solid ${severityColor};background:#1a1a1a;border-radius:4px;">
                                <div style="font-weight:bold;color:${severityColor};margin-bottom:4px;">${diag.title}</div>
                                <div style="color:#aaa;font-size:10px;margin-bottom:2px;">${diag.description}</div>
                                ${diag.root_cause ? `<div style="color:#888;font-size:10px;">根因: ${diag.root_cause}</div>` : ''}
                            </div>
                        `;
                    });
                    diagnosticHtml += '</div>';
                } else {
                    diagnosticHtml = '<div style="color:#4a4;font-size:11px;">✅ 未发现资源问题</div>';
                }
                
                diagnosticContent.innerHTML = diagnosticHtml;
                
                this.renderResourceSuggestions(data.suggestions || []);
                
                this.addActivity('🔍', `资源诊断完成: 发现 ${data.diagnostics_count} 个问题, ${data.suggestions_count} 条建议`);
                this.loadResourceOverview();
            } else {
                diagnosticContent.innerHTML = '<div style="color:#f44;font-size:11px;">诊断失败</div>';
            }
        } catch (error) {
            console.error('资源诊断错误:', error);
            diagnosticContent.innerHTML = `<div style="color:#f44;font-size:11px;">错误: ${error.message}</div>`;
        } finally {
            if (runBtn) {
                runBtn.disabled = false;
                runBtn.textContent = '运行诊断';
            }
        }
    }
    
    renderResourceSuggestions(suggestions = []) {
        const suggestionsCard = document.getElementById('resource-suggestions-card');
        const suggestionsContent = document.getElementById('resource-suggestions-content');
        if (!suggestionsCard || !suggestionsContent) return;
        if (!suggestions.length) {
            suggestionsCard.style.display = 'none';
            suggestionsContent.innerHTML = '';
            this.currentSuggestions = [];
            return;
        }
        suggestionsCard.style.display = 'block';
        suggestionsContent.innerHTML = suggestions.map((suggestion, idx) => {
                        const riskColor = {
                low: '#4a4',
                medium: '#ffaa44',
                high: '#ff4444'
                        }[suggestion.risk_level] || '#888';
            return `
                            <div style="margin-bottom:8px;padding:8px;border:1px solid #333;border-radius:4px;background:#1a1a1a;">
                                <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:4px;">
                                    <div style="font-weight:bold;color:#ddd;">${suggestion.description}</div>
                                    <span style="font-size:10px;padding:2px 6px;border-radius:3px;background:${riskColor};color:#fff;">${suggestion.risk_level}</span>
                                </div>
                    <div style="color:#aaa;font-size:10px;margin-bottom:4px;">预期改善: ${suggestion.expected_improvement || '--'}</div>
                    <button class="action-btn-small" onclick="app.requestResourceAuthorization(${idx})" style="padding:2px 8px;font-size:10px;margin-top:4px;">
                        ${suggestion.requires_approval ? '申请授权' : '执行'}
                    </button>
                            </div>
                        `;
        }).join('');
        this.currentSuggestions = suggestions;
    }

    async loadResourceOverview() {
        const execContainer = document.getElementById('resource-execution-list');
        if (!execContainer) return;
        try {
            const response = await fetch(`${API_BASE}/resources/overview`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            if (Array.isArray(data.executions)) {
                this.renderResourceExecutions(data.executions);
                const count = document.getElementById('resource-execution-count');
                if (count) count.textContent = data.executions.length;
            }
            if (Array.isArray(data.rollbacks)) {
                this.renderResourceRollbacks(data.rollbacks);
                const count = document.getElementById('resource-rollback-count');
                if (count) count.textContent = data.rollbacks.length;
            }
            if ((!this.currentSuggestions || !this.currentSuggestions.length) && Array.isArray(data.suggestions) && data.suggestions.length) {
                this.renderResourceSuggestions(data.suggestions);
            }
        } catch (error) {
            execContainer.innerHTML = `<div style="color:#f66;">资源视图加载失败：${error.message}</div>`;
        }
    }

    renderResourceExecutions(executions = []) {
        const container = document.getElementById('resource-execution-list');
        if (!container) return;
        if (!executions.length) {
            container.innerHTML = '<div style="color:#666;">暂无执行记录</div>';
            return;
        }
        container.innerHTML = executions.map((item) => {
            const statusColor = item.status === 'completed' ? '#4ade80' : item.status === 'failed' ? '#f87171' : '#facc15';
            const resultMsg = item.execution_result?.message || item.execution_result?.details || item.error || '执行完成';
            const rollbackBtn = item.can_rollback ? `<button class="action-btn-small" data-rollback="${item.suggestion_id}" style="margin-top:4px;padding:2px 8px;font-size:10px;">回滚</button>` : '';
            return `
                <div style="border-bottom:1px solid #1f2937;padding:6px 0;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;font-weight:600;color:#e2e8f0;">
                        <span>⚙️ ${item.description}</span>
                        <span style="font-size:11px;color:${statusColor};text-transform:uppercase;">${item.status}</span>
                    </div>
                    <div style="color:#94a3b8;font-size:11px;">执行: ${this.formatTimestamp(item.executed_at)} · 风险 ${item.risk_level || '--'}</div>
                    <div style="color:#cbd5f5;font-size:11px;">结果: ${resultMsg}</div>
                    ${item.rollback_plan ? `<div style="color:#64748b;font-size:11px;">回滚方案: ${item.rollback_plan}</div>` : ''}
                    ${rollbackBtn}
                </div>
            `;
        }).join('');
    }

    renderResourceRollbacks(rollbacks = []) {
        const container = document.getElementById('resource-rollback-list');
        if (!container) return;
        if (!rollbacks.length) {
            container.innerHTML = '<div style="color:#666;">暂无回滚操作</div>';
            return;
        }
        container.innerHTML = rollbacks.map((entry) => `
            <div style="border-bottom:1px solid #1f2937;padding:6px 0;">
                <div style="color:#e2e8f0;font-weight:600;">↩️ ${entry.description}</div>
                <div style="color:#94a3b8;font-size:11px;">${this.formatTimestamp(entry.rolled_back_at)} · ${entry.plan || '无回滚说明'}</div>
                <div style="color:#64748b;font-size:11px;">发起人: ${entry.requested_by || 'system'}</div>
                ${entry.reason ? `<div style="color:#94a3b8;font-size:11px;">原因: ${entry.reason}</div>` : ''}
            </div>
        `).join('');
    }

    async triggerResourceRollback(suggestionId) {
        if (!suggestionId) return;
        this.addActivity('↩️', `尝试回滚 ${suggestionId}`);
        try {
            const response = await fetch(`${API_BASE}/resources/rollback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ suggestion_id: suggestionId })
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || `HTTP ${response.status}`);
            }
            const data = await response.json();
            this.addActivity('✅', `回滚完成：${data.description || suggestionId}`);
            await this.loadResourceOverview();
        } catch (error) {
            console.error('回滚失败:', error);
            this.addActivity('❌', `回滚失败：${error.message}`);
        }
    }

    formatTimestamp(ts) {
        if (!ts) return '--';
        try {
            return new Date(ts).toLocaleString('zh-CN', { hour12: false });
        } catch {
            return ts;
        }
    }
    
    // P0-014: 请求资源操作授权
    async requestResourceAuthorization(suggestionIndex) {
        if (!this.currentSuggestions || suggestionIndex < 0 || suggestionIndex >= this.currentSuggestions.length) {
            this.addActivity('❌', '无效的建议索引');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/resources/authorization/request`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    suggestion_index: suggestionIndex,
                    requested_by: 'user',
                    reason: '用户请求执行资源优化'
                })
            });
            
            if (!response.ok) {
                throw new Error(`请求授权失败: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.addActivity('✅', `已申请授权: ${data.request.description}`);
                this.loadResourceOverview();
                
                // 如果是低风险且不需要授权，自动批准
                const suggestion = this.currentSuggestions[suggestionIndex];
                if (suggestion.risk_level === 'low' && !suggestion.requires_approval) {
                    // 自动批准并执行
                    await this.approveResourceAuthorization(data.request.suggestion_id);
                } else {
                    // 显示确认对话框
                    if (window.confirmationSystem) {
                        await window.confirmationSystem.showResourceAuthorizationConfirmation(data.request);
                    }
                }
            }
        } catch (error) {
            console.error('请求授权错误:', error);
            this.addActivity('❌', `授权请求失败: ${error.message}`);
        }
    }
    
    // P0-014: 批准资源操作授权
    async approveResourceAuthorization(suggestionId) {
        try {
            const response = await fetch(`${API_BASE}/resources/authorization/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    suggestion_id: suggestionId,
                    approved_by: 'user'
                })
            });
            
            if (!response.ok) {
                throw new Error(`批准授权失败: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.addActivity('✅', `已批准并执行: ${data.record.execution_result?.description || '资源优化操作'}`);
                this.loadResourceOverview();
                
                // 刷新资源状态
                setTimeout(() => this.updateSystemStatus(), 2000);
            }
        } catch (error) {
            console.error('批准授权错误:', error);
            this.addActivity('❌', `批准授权失败: ${error.message}`);
        }
    }
    
    async updateSystemStatus() {
        try {
            const response = await fetch(`${API_BASE}/resource/status`);
            if (!response.ok) return;
            const data = await response.json();
            const status = data.status || data || {};
            const alerts = data.alerts || status.alerts || [];
            
            if (alerts.length > 0 && window.confirmationSystem) {
                for (const alert of alerts) {
                    if (alert.requires_confirmation && !alert.confirmed) {
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
                        break;
                    }
                }
            }
            
            const cpuPercent = Math.round(status.cpu?.percent ?? status.cpu_percent ?? 0);
            const memoryPercent = Math.round(status.memory?.percent ?? status.memory_percent ?? 0);
            const diskPercent = Math.round(status.disk?.percent ?? status.disk_percent ?? 0);
            
            const cpuBar = document.getElementById('cpu-bar');
            const cpuValue = document.getElementById('cpu-value');
            if (cpuBar && cpuValue && cpuPercent >= 0) {
                cpuBar.style.width = `${cpuPercent}%`;
                cpuValue.textContent = `${cpuPercent}%`;
                if (cpuPercent > 80 && window.modalSystem) {
                    window.modalSystem.showResourceAlert('CPU', cpuPercent, 80);
                }
            }
            
            const memoryBar = document.getElementById('memory-bar');
            const memoryValue = document.getElementById('memory-value');
            if (memoryBar && memoryValue && memoryPercent >= 0) {
                memoryBar.style.width = `${memoryPercent}%`;
                memoryValue.textContent = `${memoryPercent}%`;
                if (memoryPercent > 85 && window.modalSystem) {
                    window.modalSystem.showResourceAlert('内存', memoryPercent, 85);
                }
            }
            
            const diskBar = document.getElementById('disk-bar');
            const diskValue = document.getElementById('disk-value');
            if (diskBar && diskValue && diskPercent >= 0) {
                diskBar.style.width = `${diskPercent}%`;
                diskValue.textContent = `${diskPercent}%`;
                if (diskPercent > 90 && window.modalSystem) {
                    window.modalSystem.showResourceAlert('磁盘', diskPercent, 90);
                }
            }
            this.renderResourceAlerts(alerts);
            this.renderExternalDrives(status.external_drives || []);
        } catch (error) {
            // 静默失败
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
            let events = data.events || [];
            if (this.securityAuditFilter === 'orchestrator_task_status') {
                events = events.filter(e => e.type === 'orchestrator_task_status');
            }
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

