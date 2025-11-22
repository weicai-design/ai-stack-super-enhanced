class ExpertCenterConsole {
    constructor() {
        this.API = '/api/super-agent/experts';
        this.lastSessionId = null;
        this.eventSource = null;
        this.streamRetryTimer = null;
        this.collabRefreshTimer = null;
        this.notificationsEnabled = false;
        this.bindEvents();
        this.loadAll();
        this.initNotifications();
        this.initCollabStream();
    }

    bindEvents() {
        document.getElementById('btnRefreshExperts')?.addEventListener('click', () => this.loadAll());
        document.getElementById('btnSyncRouting')?.addEventListener('click', () => this.loadRouting());
        document.getElementById('btnSimulateRoute')?.addEventListener('click', () => this.simulateRoute());
        document.getElementById('btnToggleHeuristics')?.addEventListener('click', () => {
            const list = document.getElementById('heuristicList');
            if (!list) return;
            list.style.display = list.style.display === 'none' ? 'block' : 'none';
        });
        document.getElementById('btnLoadHistory')?.addEventListener('click', () => this.loadSimulationHistory());
        document.getElementById('btnCreateSession')?.addEventListener('click', () => this.createSession());
        document.getElementById('btnAddContribution')?.addEventListener('click', () => this.addContribution());
        document.getElementById('btnFinalizeSession')?.addEventListener('click', () => this.finalizeSession());
    }

    loadAll() {
        this.loadAbilityMap();
        this.loadRouting();
        this.loadAcceptance();
        this.loadCollaboration();
    }

    async request(path, options) {
        const resp = await fetch(`${this.API}${path}`, options);
        if (!resp.ok) {
            const text = await resp.text();
            throw new Error(text || `HTTP ${resp.status}`);
        }
        return resp.json();
    }

    async loadAbilityMap() {
        try {
            const data = await this.request('/ability-map');
            this.renderAbilitySummary(data.summary || {});
            this.renderAbilityMap(data.abilities || []);
        } catch (error) {
            const grid = document.getElementById('abilityGrid');
            if (grid) grid.innerHTML = `<div class="muted">加载失败：${error.message}</div>`;
        }
    }

    renderAbilitySummary(summary) {
        document.getElementById('statExpertCount').textContent = summary.total_experts ?? '-';
        document.getElementById('statAvgConfidence').textContent = summary.avg_confidence ? `${(summary.avg_confidence * 100).toFixed(0)}%` : '-';
        document.getElementById('statModuleCount').textContent = summary.modules ? summary.modules.length : '-';
        document.getElementById('statReadyCapabilities').textContent = summary.ready_capabilities ?? '-';
    }

    renderAbilityMap(abilities) {
        const grid = document.getElementById('abilityGrid');
        if (!grid) return;
        if (!abilities.length) {
            grid.innerHTML = '<div class="muted">暂无专家配置</div>';
            return;
        }
        grid.innerHTML = abilities.map((ability) => `
            <div class="ability-card">
                <h3>${ability.icon || '🧠'} ${ability.name}</h3>
                <div style="margin:8px 0;">
                    <span class="tag level">Lv.${ability.level || '-'}</span>
                    ${(ability.modules || []).map(m => `<span class="tag module">${m.toUpperCase()}</span>`).join('')}
                </div>
                <div class="muted" style="margin-top:4px;">信心度 ${(ability.confidence * 100).toFixed(0)}% · 覆盖 ${ability.coverage?.scenarios || 0} 场景</div>
                <ul class="list">
                    ${(ability.capabilities || []).map(cap => `<li>${cap.name} · <span style="color:${cap.status === 'ready' ? '#16a34a' : '#f97316'}">${cap.status}</span></li>`).join('')}
                </ul>
                <div class="muted" style="margin-top:8px;">信号：${(ability.signals || []).join(' / ') || '--'}</div>
                <div class="muted">Playbook：${(ability.playbooks || []).join('，') || '--'}</div>
            </div>
        `).join('');
    }

    async loadRouting() {
        try {
            const data = await this.request('/routing');
            this.renderRouting(data.strategy || {}, data.summary || {});
        } catch (error) {
            const timeline = document.getElementById('routeTimeline');
            if (timeline) timeline.innerHTML = `<div class="muted">路由策略加载失败：${error.message}</div>`;
        }
    }

    renderRouting(strategy, summary) {
        const thresholds = strategy.confidence_thresholds || {};
        document.getElementById('statDirectThreshold').textContent = thresholds.direct_route ? thresholds.direct_route.toFixed(2) : '-';
        document.getElementById('statClarifyThreshold').textContent = thresholds.needs_clarification ? thresholds.needs_clarification.toFixed(2) : '-';
        document.getElementById('statFallbackThreshold').textContent = thresholds.fallback ? thresholds.fallback.toFixed(2) : '-';
        const moduleLoad = strategy.module_load || {};
        const busiest = Object.keys(moduleLoad).sort((a, b) => moduleLoad[b] - moduleLoad[a])[0];
        document.getElementById('statBusyModule').textContent = busiest ? `${busiest.toUpperCase()} ${(moduleLoad[busiest] * 100).toFixed(0)}%` : '-';

        const heuristics = strategy.heuristics || [];
        const list = document.getElementById('heuristicList');
        if (list) {
            list.innerHTML = heuristics.map(h => `<p>· <strong>${h.signal}</strong>（权重 ${Math.round((h.weight || 0) * 100)}%）：${h.description}</p>`).join('');
        }

        const timeline = document.getElementById('routeTimeline');
        if (timeline) {
            const routes = strategy.recent_routes || [];
            if (!routes.length) {
                timeline.innerHTML = '<div class="muted">暂无路由记录</div>';
            } else {
                timeline.innerHTML = routes.map(route => `
                    <div class="timeline-item">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <strong>${route.query}</strong>
                            <span class="tag module">${route.expert || ''}</span>
                        </div>
                        <div class="muted">${route.domain || '--'} · ${(route.confidence * 100).toFixed(0)}% · ${this.formatTime(route.timestamp)}</div>
                    </div>
                `).join('');
            }
        }
    }

    async simulateRoute() {
        const query = document.getElementById('routeQuery')?.value.trim();
        if (!query) {
            alert('请先输入路由语句');
            return;
        }
        const contextRaw = document.getElementById('routeContext')?.value || '';
        const hints = contextRaw.split('\n').map(line => line.trim()).filter(Boolean);
        const expected = document.getElementById('routeExpected')?.value.trim();
        const consoleBox = document.getElementById('routeConsole');
        if (consoleBox) consoleBox.textContent = '⏳ 正在模拟路由...';
        try {
            const data = await this.request('/simulate-route', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    knowledge_hints: hints,
                    expected_domain: expected || undefined
                })
            });
            if (consoleBox) {
                const route = data.route || {};
                const comparison = data.comparison || {};
                const alternatives = route.alternatives || [];
                
                let output = [
                    `Query: ${query}`,
                    `Expert: ${route.name || route.expert}`,
                    `Domain: ${route.domain}`,
                    `Confidence: ${(route.confidence * 100).toFixed(0)}%`,
                    `Score: ${route.score || 0}`,
                    `Simulated At: ${route.simulated_at || route.routed_at || '-'}`
                ];
                
                if (comparison.router_confidence !== null && comparison.router_confidence !== undefined) {
                    output.push(`Router Confidence: ${(comparison.router_confidence * 100).toFixed(0)}%`);
                }
                
                if (alternatives.length > 0) {
                    output.push('');
                    output.push('Alternatives:');
                    alternatives.forEach((alt, idx) => {
                        output.push(`  ${idx + 1}. ${alt.name} (${alt.expert}) - Score: ${alt.score}`);
                    });
                }
                
                consoleBox.textContent = output.join('\n');
            }
            this.loadRouting();
            this.loadSimulationHistory();
        } catch (error) {
            if (consoleBox) consoleBox.textContent = `❌ 路由失败：${error.message}`;
        }
    }

    async loadAcceptance() {
        try {
            const data = await this.request('/acceptance');
            this.renderAcceptance(data.matrix || [], data.summary || {});
        } catch (error) {
            const tbody = document.getElementById('acceptanceTable');
            if (tbody) tbody.innerHTML = `<tr><td colspan="5" class="muted">加载失败：${error.message}</td></tr>`;
        }
    }

    async loadCollaboration() {
        const container = document.getElementById('collabSessions');
        if (container) container.innerHTML = '<div class="muted">加载中...</div>';
        try {
            const [active, summary] = await Promise.all([
                this.request('/collaboration/active'),
                this.request('/collaboration/summary')
            ]);
            this.renderCollabSessions(active.sessions || []);
            this.renderCollabSummary(summary.summary || {});
        } catch (error) {
            if (container) container.innerHTML = `<div class="muted">协同数据加载失败：${error.message}</div>`;
        }
    }

    renderCollabSummary(summary) {
        document.getElementById('statCollabActive').textContent = summary.active_sessions ?? '-';
        document.getElementById('statCollabTotal').textContent = summary.total_sessions ?? '-';
        document.getElementById('statCollabSynergy').textContent = summary.avg_synergy !== undefined ? `${(summary.avg_synergy * 100).toFixed(0)}%` : '-';
        document.getElementById('statCollabLatency').textContent = summary.avg_response_latency_ms ? `${summary.avg_response_latency_ms} ms` : '--';
    }

    renderCollabSessions(sessions) {
        const container = document.getElementById('collabSessions');
        if (!container) return;
        if (!sessions.length) {
            container.innerHTML = '<div class="muted">暂无活跃会话，可在右侧发起。</div>';
            return;
        }
        container.innerHTML = sessions.map((session) => {
            const contributions = session.contributions || [];
            const last = contributions[contributions.length - 1];
            return `
                <div class="session-card">
                    <h4>${session.topic}</h4>
                    <div class="session-meta">
                        会话ID：${session.session_id}<br>
                        发起人：${session.initiator} · 专家数：${(session.experts || []).length} · 协同指数 ${(((session.metadata?.synergy_score ?? 0) * 100)).toFixed(0)}%
                    </div>
                    <p class="muted" style="margin:6px 0;">目标：${(session.goals || []).join(' / ') || '--'}</p>
                    <p style="margin:6px 0;font-size:13px;">最近贡献：${last ? `${last.expert_name} · ${last.summary}` : '—'}</p>
                    <button class="btn-secondary" style="margin-top:8px;" data-session="${session.session_id}">复制ID</button>
                </div>
            `;
        }).join('');
        container.querySelectorAll('button[data-session]').forEach((btn) => {
            btn.addEventListener('click', (event) => {
                const sessionId = event.currentTarget.getAttribute('data-session');
                navigator.clipboard?.writeText(sessionId);
                this.lastSessionId = sessionId;
                this.updateCollabConsole(`已复制会话ID：${sessionId}`);
            });
        });
    }

    parseList(text) {
        return (text || '').split('\n').map((line) => line.trim()).filter(Boolean);
    }

    parseExperts(text) {
        const lines = this.parseList(text);
        return lines.map((line) => {
            const [expert_id, name, domain, role] = line.split(',').map((part) => part?.trim());
            return { expert_id, name, domain, role: role || 'delegate' };
        }).filter((item) => item.expert_id && item.name && item.domain);
    }

    updateCollabConsole(message) {
        const box = document.getElementById('collabConsole');
        if (box) box.textContent = message;
    }

    initCollabStream() {
        if (!window.EventSource) {
            this.updateCollabConsole('浏览器不支持 SSE 实时推送');
            return;
        }
        if (this.eventSource) {
            this.eventSource.close();
        }
        this.eventSource = new EventSource(`${this.API}/collaboration/stream`);
        this.eventSource.onmessage = (event) => {
            if (!event.data) return;
            try {
                const data = JSON.parse(event.data);
                this.handleCollabEvent(data);
            } catch (error) {
                console.warn('协同事件解析失败', error);
            }
        };
        this.eventSource.onerror = () => {
            this.updateCollabConsole('实时协同连接中断，5 秒后重试...');
            if (this.eventSource) {
                this.eventSource.close();
                this.eventSource = null;
            }
            clearTimeout(this.streamRetryTimer);
            this.streamRetryTimer = setTimeout(() => this.initCollabStream(), 5000);
        };
    }

    handleCollabEvent(event) {
        const payload = event.payload || {};
        const ts = event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
        const messageLines = [
            `[${ts}] ${event.event_type || 'collaboration.event'}`,
            `主题：${payload.topic || '--'}`,
            `状态：${payload.status || '--'}`,
            payload.owner ? `责任人：${payload.owner}` : null,
        ].filter(Boolean);
        this.updateCollabConsole(messageLines.join('\n'));
        this.notifyCollabEvent(payload);
        clearTimeout(this.collabRefreshTimer);
        this.collabRefreshTimer = setTimeout(() => this.loadCollaboration(), 300);
    }

    initNotifications() {
        if (typeof window === 'undefined' || !('Notification' in window)) {
            return;
        }
        if (Notification.permission === 'granted') {
            this.notificationsEnabled = true;
        } else if (Notification.permission === 'default') {
            Notification.requestPermission().then((permission) => {
                this.notificationsEnabled = permission === 'granted';
            });
        }
    }

    notifyCollabEvent(payload) {
        if (!this.notificationsEnabled || !payload.topic) return;
        const bodyParts = [
            `状态：${payload.status || '—'}`,
            payload.owner ? `责任人：${payload.owner}` : null,
        ].filter(Boolean);
        try {
            new Notification(`专家协同：${payload.topic}`, {
                body: bodyParts.join('\n') || '协同事件更新',
                tag: payload.session_id || payload.topic,
            });
        } catch (error) {
            console.warn('桌面通知失败', error);
            this.notificationsEnabled = false;
        }
    }

    async createSession() {
        const topic = document.getElementById('collabTopic')?.value.trim();
        const initiator = document.getElementById('collabInitiator')?.value.trim();
        const goals = this.parseList(document.getElementById('collabGoals')?.value || '');
        const experts = this.parseExperts(document.getElementById('collabExperts')?.value || '');
        if (!topic || !initiator) {
            alert('请填写主题与发起人');
            return;
        }
        if (!experts.length) {
            alert('请至少配置一位专家（格式：expert_id,name,domain,role）');
            return;
        }
        this.updateCollabConsole('⏳ 正在创建会话...');
        try {
            const data = await this.request('/collaboration/session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic, initiator, goals, experts })
            });
            this.lastSessionId = data.session?.session_id;
            this.updateCollabConsole(`✅ 会话创建成功：${this.lastSessionId}`);
            this.loadCollaboration();
        } catch (error) {
            this.updateCollabConsole(`❌ 会话创建失败：${error.message}`);
        }
    }

    async addContribution() {
        const sessionIdInput = document.getElementById('collabSessionId');
        const sessionId = sessionIdInput?.value.trim() || this.lastSessionId;
        const expertId = document.getElementById('collabExpertId')?.value.trim();
        const expertName = document.getElementById('collabExpertName')?.value.trim();
        const channel = document.getElementById('collabChannel')?.value.trim() || 'workflow';
        const summary = document.getElementById('collabSummary')?.value.trim();
        const actionItems = this.parseList(document.getElementById('collabActions')?.value || '');
        if (!sessionId || !expertId || !expertName || !summary) {
            alert('请填写会话ID、专家信息与贡献摘要');
            return;
        }
        this.updateCollabConsole('⏳ 正在追加贡献...');
        try {
            const data = await this.request(`/collaboration/session/${sessionId}/contribution`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    expert_id: expertId,
                    expert_name: expertName,
                    channel,
                    summary,
                    action_items: actionItems,
                    impact_score: 0.7
                })
            });
            this.lastSessionId = data.session?.session_id;
            this.updateCollabConsole(`✅ 贡献已记录，当前协同指数 ${(((data.session?.metadata?.synergy_score ?? 0) * 100)).toFixed(0)}%`);
            this.loadCollaboration();
            if (sessionIdInput && !sessionIdInput.value) sessionIdInput.value = this.lastSessionId;
        } catch (error) {
            this.updateCollabConsole(`❌ 贡献记录失败：${error.message}`);
        }
    }

    async finalizeSession() {
        const sessionId = document.getElementById('collabDecisionSessionId')?.value.trim() || this.lastSessionId;
        const owner = document.getElementById('collabDecisionOwner')?.value.trim();
        const summary = document.getElementById('collabDecisionSummary')?.value.trim();
        const kpis = this.parseList(document.getElementById('collabDecisionKpis')?.value || '');
        const followups = this.parseList(document.getElementById('collabDecisionFollowups')?.value || '');
        if (!sessionId || !owner || !summary) {
            alert('请填写会话ID、责任人与决策摘要');
            return;
        }
        this.updateCollabConsole('⏳ 正在完成会话...');
        try {
            await this.request(`/collaboration/session/${sessionId}/decision`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ owner, summary, kpis, followups })
            });
            this.updateCollabConsole('✅ 会话已闭环，决策与KPI记录完成');
            this.loadCollaboration();
        } catch (error) {
            this.updateCollabConsole(`❌ 决策记录失败：${error.message}`);
        }
    }

    renderAcceptance(matrix, summary) {
        const tbody = document.getElementById('acceptanceTable');
        if (!tbody) return;
        if (!matrix.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="muted">暂无测试记录</td></tr>';
            return;
        }
        tbody.innerHTML = matrix.map(item => `
            <tr>
                <td>${item.capability}</td>
                <td>${item.owner}</td>
                <td>
                    ${(item.tests || []).map(test => `<div>${test.name} · <span style="color:${test.status === 'pass' ? '#16a34a' : '#f97316'}">${test.status}</span> (${test.metric || ''})</div>`).join('')}
                </td>
                <td>${item.acceptance}</td>
                <td>${this.formatTime(item.last_run)}</td>
            </tr>
        `).join('');
        
        // 显示摘要信息（如果有）
        if (summary.pass_rate !== undefined) {
            const summaryText = `总计: ${summary.total_capabilities} 能力, ${summary.total_tests} 测试, 通过率: ${summary.pass_rate}%`;
            // 可以在表格上方或下方显示摘要
        }
    }
    
    async loadSimulationHistory() {
        try {
            const data = await this.request('/simulation/history?limit=10');
            this.renderSimulationHistory(data.history || []);
        } catch (error) {
            const historyContainer = document.getElementById('simulationHistory');
            if (historyContainer) historyContainer.innerHTML = `<div class="muted">加载历史失败：${error.message}</div>`;
        }
    }
    
    renderSimulationHistory(history) {
        const container = document.getElementById('simulationHistory');
        if (!container) return;
        if (!history.length) {
            container.innerHTML = '<div class="muted">暂无模拟历史</div>';
            return;
        }
        container.innerHTML = history.map(item => {
            const result = item.result || {};
            return `
                <div class="timeline-item">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <strong>${item.query}</strong>
                        <span class="tag module">${result.expert || '-'}</span>
                    </div>
                    <div class="muted">${result.domain || '--'} · ${(result.confidence * 100).toFixed(0)}% · ${this.formatTime(item.timestamp)}</div>
                </div>
            `;
        }).join('');
    }

    formatTime(value) {
        if (!value) return '--';
        try {
            return new Date(value).toLocaleString('zh-CN', { hour12: false });
        } catch {
            return value;
        }
    }
}

window.addEventListener('DOMContentLoaded', () => {
    new ExpertCenterConsole();
});

