class OperationsFinanceConsole {
    constructor() {
        this.API_BASE = '/api/super-agent';
        this.API = '/api/super-agent/operations/analytics';
        this.latest = null;
        this.bindEvents();
        this.refresh();
    }

    bindEvents() {
        const refreshBtn = document.getElementById('btnRefresh');
        if (refreshBtn) refreshBtn.addEventListener('click', () => this.refresh());
        const exportBtn = document.getElementById('btnExport');
        if (exportBtn) exportBtn.addEventListener('click', () => this.exportData());
        const refreshStrategyBtn = document.getElementById('btnRefreshStrategy');
        if (refreshStrategyBtn) refreshStrategyBtn.addEventListener('click', () => this.loadStrategyData());
        const refreshSyncBtn = document.getElementById('btnRefreshSync');
        if (refreshSyncBtn) refreshSyncBtn.addEventListener('click', () => this.loadSyncData());
    }

    async refresh() {
        try {
            // 并行加载所有数据
            const [analyticsRes, kpisRes, insightsRes, strategyRes, syncStatusRes] = await Promise.all([
                fetch(this.API),
                fetch(`${this.API_BASE}/operations-finance/kpis`),
                fetch(`${this.API_BASE}/operations-finance/insights`),
                fetch(`${this.API_BASE}/operations-finance/strategy/status`),
                fetch(`${this.API_BASE}/operations-finance/erp/sync/status`)
            ]);
            
            if (!analyticsRes.ok) throw new Error(`HTTP ${analyticsRes.status}`);
            this.latest = await analyticsRes.json();
            
            // 加载KPI数据
            if (kpisRes.ok) {
                const kpisData = await kpisRes.json();
                this.latest.kpis = kpisData.kpis || {};
                this.latest.kpi_definitions = kpisData.definitions || {};
            }
            
            // 加载洞察数据
            if (insightsRes.ok) {
                const insightsData = await insightsRes.json();
                this.latest.finance_insights = insightsData.insights || [];
            }
            
            // 加载策略状态
            if (strategyRes.ok) {
                const strategyData = await strategyRes.json();
                this.latest.strategy_status = strategyData;
            }
            
            // 加载ERP同步状态
            if (syncStatusRes.ok) {
                const syncData = await syncStatusRes.json();
                this.latest.erp_sync_status = syncData.status || {};
            }
            
            this.render();
        } catch (error) {
            console.error('加载运营财务数据失败', error);
            alert(`加载数据失败：${error.message}`);
        }
    }

    render() {
        if (!this.latest?.success) return;
        this.renderStats();
        this.renderScorecards();
        this.renderCharts();
        this.renderInsights();
        this.renderTrend();
        this.renderStrategyLinks();
        this.renderReportingMatrix();
        this.renderStrategyData();
        this.renderSyncData();
    }

    renderStats() {
        // 优先使用新的KPI数据
        const kpis = this.latest.kpis || {};
        const kpi = this.latest.kpi_summary || {};
        
        const formatCurrency = (val) => {
            if (val === null || val === undefined) return '-';
            return `¥${Number(val).toLocaleString('zh-CN', { maximumFractionDigits: 0 })}`;
        };
        
        // 使用新的KPI数据（如果可用）
        const netCash = kpis.net_cash?.value || kpi.net_cash;
        const burnRate = kpis.burn_rate?.value || kpi.burn_rate;
        const collections = kpis.collections?.value || kpi.collections;
        const payments = kpis.payments?.value || kpi.payments;
        const runway = kpis.runway?.value || kpi.runway_months;
        
        document.getElementById('kpiNetCash').textContent = formatCurrency(netCash);
        document.getElementById('kpiBurnRate').textContent = formatCurrency(burnRate);
        document.getElementById('kpiCollections').textContent = formatCurrency(collections);
        document.getElementById('kpiPayments').textContent = formatCurrency(payments);
        document.getElementById('kpiRunway').textContent = runway ? `${runway.toFixed(1)} 月` : '∞';
    }

    renderScorecards() {
        const container = document.getElementById('scorecardGrid');
        if (!container) return;
        
        // 使用新的KPI数据生成评分卡
        const kpis = this.latest.kpis || {};
        const cards = this.latest.scorecards || [];
        
        // 如果没有评分卡，从KPI生成
        if (!cards.length && Object.keys(kpis).length > 0) {
            const kpiCards = Object.entries(kpis).map(([key, kpi]) => {
                const status = kpi.status || 'normal';
                const statusClass = status === 'critical' ? 'critical' : status === 'warning' ? 'warning' : 'positive';
                return {
                    label: kpi.name || key,
                    value: `${kpi.value} ${kpi.unit || ''}`,
                    status: statusClass,
                    formula: kpi.formula
                };
            });
            
            container.innerHTML = '';
            kpiCards.forEach(card => {
                const div = document.createElement('div');
                div.className = `scorecard ${card.status || 'neutral'}`;
                div.innerHTML = `
                    <div class="label">${card.label}</div>
                    <div class="value">${card.value}</div>
                    <div class="muted">${card.formula || ''}</div>
                `;
                container.appendChild(div);
            });
            return;
        }
        
        if (!cards.length) {
            container.innerHTML = '<div class="muted">暂无指标口径</div>';
            return;
        }
        container.innerHTML = '';
        cards.forEach(card => {
            const div = document.createElement('div');
            div.className = `scorecard ${card.status || 'neutral'}`;
            div.innerHTML = `
                <div class="label">${card.label}</div>
                <div class="value">${card.value}</div>
                <div class="muted">${card.trend || ''}</div>
            `;
            container.appendChild(div);
        });
    }

    renderCharts() {
        const grid = document.getElementById('chartGrid');
        if (!grid) return;
        const charts = this.latest.chart_blueprints || [];
        if (!charts.length) {
            grid.innerHTML = '<div class="muted">暂无图表模板</div>';
            return;
        }
        grid.innerHTML = '';
        charts.forEach(chart => {
            const div = document.createElement('div');
            div.className = 'blueprint-card';
            div.innerHTML = `
                <div class="badge chart">${chart.owner || '图表专家'}</div>
                <h3>${chart.title}</h3>
                <p class="muted">类型：${chart.chart_type} · 维度：${(chart.dimensions || []).join('/')}</p>
                <p>指标：${(chart.metrics || []).join(' / ')}</p>
                <p class="muted">${chart.explanation || ''}</p>
                <p style="font-size:13px; color:#475569;">使用场景：${chart.recommended_usage || '--'}</p>
            `;
            grid.appendChild(div);
        });
    }

    renderInsights() {
        const tbody = document.getElementById('insightTable');
        if (!tbody) return;
        
        // 优先使用新的财务专家洞察
        let insights = this.latest.finance_insights || [];
        
        // 如果没有洞察，尝试从旧数据转换
        if (!insights.length && this.latest.finance_insights_legacy) {
            insights = this.latest.finance_insights_legacy;
        }
        
        if (!insights.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="muted">暂无专家洞察</td></tr>';
            return;
        }
        tbody.innerHTML = '';
        insights.forEach(item => {
            const tr = document.createElement('tr');
            const severity = item.type || item.severity || 'info';
            const cls = severity === 'critical' ? 'impact-critical'
                : severity === 'warning' ? 'impact-warning' : 'impact-info';
            tr.innerHTML = `
                <td>${item.title}</td>
                <td>${item.owner || '财务专家'}</td>
                <td><span class="impact-tag ${cls}">${severity}</span></td>
                <td>${item.description || item.summary || ''}</td>
                <td>${(item.recommendations || item.recommended_actions || []).join('；')}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    renderTrend() {
        const board = document.getElementById('trendBoard');
        if (!board) return;
        const points = this.latest.trend_points || [];
        document.getElementById('trendUpdated').textContent = this.latest.last_refreshed || '';
        if (!points.length) {
            board.innerHTML = '<div class="muted">暂无趋势样本</div>';
            return;
        }
        board.innerHTML = '';
        points.forEach(point => {
            const div = document.createElement('div');
            div.className = 'trend-item';
            div.innerHTML = `
                <div>
                    <strong>${point.label}</strong>
                    <div class="muted">净现金：${point.net_cash}M</div>
                </div>
                <div class="muted">Burn：${point.burn}M</div>
            `;
            board.appendChild(div);
        });
    }

    renderStrategyLinks() {
        const data = this.latest.strategy_links || {};
        const metrics = data.metrics || {};
        const formatPercent = (val) => {
            if (typeof val !== 'number') return '-';
            return `${(val * 100).toFixed(0)}%`;
        };
        const formatLatency = (val) => (typeof val === 'number' ? `${val} ms` : '-');
        const automationEl = document.getElementById('bridgeAutomation');
        const alertEl = document.getElementById('bridgeAlerts');
        const latencyEl = document.getElementById('bridgeLatency');
        if (automationEl) automationEl.textContent = formatPercent(metrics.automation_rate);
        if (alertEl) alertEl.textContent = metrics.cross_system_alerts_24h ?? '-';
        if (latencyEl) latencyEl.textContent = formatLatency(metrics.expert_routing_latency_ms);

        const list = document.getElementById('bridgeList');
        if (list) {
            const bridges = data.bridges || [];
            if (!bridges.length) {
                list.innerHTML = '<div class="muted">暂无联动策略</div>';
            } else {
                list.innerHTML = bridges.map(bridge => `
                    <div class="bridge-card">
                        <h3>${bridge.name}</h3>
                        <div class="meta">
                            <span>${bridge.source} → ${bridge.target}</span>
                            <span>${bridge.status || ''}</span>
                        </div>
                        <p>${bridge.description || ''}</p>
                        <p class="muted">信号：${(bridge.signals || []).join(' / ') || '--'}</p>
                        <p class="muted">自动化：${(bridge.automation || []).join('，') || '--'}</p>
                    </div>
                `).join('');
            }
        }

        const playbookTable = document.getElementById('playbookTable');
        if (playbookTable) {
            const playbooks = data.playbooks || [];
            if (!playbooks.length) {
                playbookTable.innerHTML = '<tr><td colspan="4" class="muted">暂无 Playbook</td></tr>';
            } else {
                playbookTable.innerHTML = playbooks.map(item => `
                    <tr>
                        <td>${item.name}</td>
                        <td>${item.owner || '-'}</td>
                        <td>${(item.systems || []).join(' / ') || '--'}</td>
                        <td>${item.doc ? `<a href="${item.doc}" target="_blank">文档</a>` : '--'}</td>
                    </tr>
                `).join('');
            }
        }
    }

    renderReportingMatrix() {
        const table = document.getElementById('reportingTable');
        if (!table) return;
        const matrix = this.latest.strategy?.reporting_matrix || [];
        if (!matrix.length) {
            table.innerHTML = '<tr><td colspan="5" class="muted">暂无报表矩阵</td></tr>';
        } else {
            table.innerHTML = matrix.map(row => `
                <tr>
                    <td>${row.report}</td>
                    <td>${row.frequency}</td>
                    <td>${row.owner}</td>
                    <td>${(row.systems || []).join(' / ')}</td>
                    <td>${row.status || '-'}</td>
                </tr>
            `).join('');
        }
    }

    exportData() {
        if (!this.latest) return;
        const blob = new Blob([JSON.stringify(this.latest, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `operations_finance_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    formatPercent(value, digits = 0) {
        if (typeof value !== 'number') return '--';
        return `${(value * 100).toFixed(digits)}%`;
    }

    // ==================== P2-012: 策略联动 ====================
    
    async loadStrategyData() {
        try {
            const [statusRes, historyRes] = await Promise.all([
                fetch(`${this.API_BASE}/operations-finance/strategy/status`),
                fetch(`${this.API_BASE}/operations-finance/strategy/history?limit=20`)
            ]);
            
            if (statusRes.ok) {
                const statusData = await statusRes.json();
                this.latest.strategy_status = statusData;
            }
            
            if (historyRes.ok) {
                const historyData = await historyRes.json();
                this.latest.strategy_history = historyData.history || [];
            }
            
            this.renderStrategyData();
        } catch (error) {
            console.error('加载策略数据失败', error);
        }
    }

    renderStrategyData() {
        const status = this.latest.strategy_status || {};
        
        document.getElementById('strategyTotal').textContent = status.total_strategies || 0;
        document.getElementById('strategyEnabled').textContent = status.enabled_strategies || 0;
        document.getElementById('strategyExecutions').textContent = status.recent_executions || 0;
        
        // 渲染策略列表
        const strategyList = document.getElementById('strategyList');
        if (strategyList) {
            const strategies = status.strategies || [];
            if (!strategies.length) {
                strategyList.innerHTML = '<div class="muted">暂无策略</div>';
            } else {
                strategyList.innerHTML = strategies.map(s => `
                    <div class="bridge-card">
                        <h3>${s.name}</h3>
                        <div class="meta">
                            <span>触发: ${s.trigger}</span>
                            <span class="badge ${s.enabled ? 'chart' : 'finance'}">${s.enabled ? '启用' : '禁用'}</span>
                        </div>
                    </div>
                `).join('');
            }
        }
        
        // 渲染执行历史
        const historyContainer = document.getElementById('strategyHistory');
        if (historyContainer) {
            const history = this.latest.strategy_history || [];
            if (!history.length) {
                historyContainer.innerHTML = '<div class="muted">暂无执行历史</div>';
            } else {
                historyContainer.innerHTML = history.map(h => `
                    <div class="trend-item">
                        <div>
                            <strong>${h.strategy_name}</strong>
                            <div class="muted">${this.formatTime(h.executed_at)}</div>
                        </div>
                        <span class="badge ${h.status === 'success' ? 'chart' : 'finance'}">${h.status}</span>
                    </div>
                `).join('');
            }
        }
    }

    // ==================== P2-012: ERP 数据同步 ====================
    
    async loadSyncData() {
        try {
            const [statusRes, historyRes] = await Promise.all([
                fetch(`${this.API_BASE}/operations-finance/erp/sync/status`),
                fetch(`${this.API_BASE}/operations-finance/erp/sync/history?limit=20`)
            ]);
            
            if (statusRes.ok) {
                const statusData = await statusRes.json();
                this.latest.erp_sync_status = statusData.status || {};
            }
            
            if (historyRes.ok) {
                const historyData = await historyRes.json();
                this.latest.erp_sync_history = historyData.history || [];
            }
            
            this.renderSyncData();
        } catch (error) {
            console.error('加载同步数据失败', error);
        }
    }

    renderSyncData() {
        const syncStatus = this.latest.erp_sync_status || {};
        
        // 计算统计
        const statusByType = syncStatus.status_by_type || {};
        const types = Object.keys(statusByType);
        let totalSuccess = 0;
        let totalFailed = 0;
        
        types.forEach(type => {
            const status = statusByType[type];
            totalSuccess += status.recent_success || 0;
            totalFailed += status.recent_failed || 0;
        });
        
        const successRate = (totalSuccess + totalFailed) > 0 
            ? (totalSuccess / (totalSuccess + totalFailed) * 100).toFixed(1) 
            : '0.0';
        
        document.getElementById('syncTotalTypes').textContent = syncStatus.total_types || 0;
        document.getElementById('syncRecentSuccess').textContent = totalSuccess;
        document.getElementById('syncRecentFailed').textContent = totalFailed;
        document.getElementById('syncSuccessRate').textContent = `${successRate}%`;
        
        // 渲染按类型状态
        const statusContainer = document.getElementById('syncStatusByType');
        if (statusContainer) {
            if (!types.length) {
                statusContainer.innerHTML = '<div class="muted">暂无同步类型</div>';
            } else {
                statusContainer.innerHTML = types.map(type => {
                    const status = statusByType[type];
                    return `
                        <div class="bridge-card">
                            <h3>${type}</h3>
                            <div class="meta">
                                <span>方向: ${status.direction || '-'}</span>
                                <span>频率: ${status.frequency || '-'}</span>
                            </div>
                            <p class="muted">最后同步: ${this.formatTime(status.last_sync) || '-'}</p>
                            <p class="muted">成功率: ${status.success_rate.toFixed(1)}%</p>
                            <p class="muted">成功: ${status.recent_success} | 失败: ${status.recent_failed}</p>
                        </div>
                    `;
                }).join('');
            }
        }
        
        // 渲染同步历史
        const historyContainer = document.getElementById('syncHistory');
        if (historyContainer) {
            const history = this.latest.erp_sync_history || [];
            if (!history.length) {
                historyContainer.innerHTML = '<div class="muted">暂无同步记录</div>';
            } else {
                historyContainer.innerHTML = history.map(h => {
                    const statusClass = h.status === 'success' ? 'chart' : 'finance';
                    return `
                        <div class="trend-item">
                            <div>
                                <strong>${h.data_type}</strong>
                                <div class="muted">${h.direction} · ${this.formatTime(h.started_at)}</div>
                            </div>
                            <span class="badge ${statusClass}">${h.status}</span>
                        </div>
                    `;
                }).join('');
            }
        }
    }

    formatTime(ts) {
        if (!ts) return '-';
        try {
            const date = new Date(ts);
            return date.toLocaleString('zh-CN', { hour12: false });
        } catch {
            return ts;
        }
    }
}

window.addEventListener('DOMContentLoaded', () => {
    new OperationsFinanceConsole();
});

