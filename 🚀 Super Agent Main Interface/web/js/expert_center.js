class ExpertCenterConsole {
    constructor() {
        this.API = '/api/super-agent/experts';
        this.bindEvents();
        this.loadAll();
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
    }

    loadAll() {
        this.loadAbilityMap();
        this.loadRouting();
        this.loadAcceptance();
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

