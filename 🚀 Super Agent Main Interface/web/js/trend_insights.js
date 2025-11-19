class TrendInsightsConsole {
    constructor() {
        this.API_BASE = '/api/super-agent/trend';
        this.currentCategory = 'all';
        this.indicators = [];
        this.dashboards = [];
        this.insights = [];
        this.backtestIndicator = 'industry_demand_velocity';
        this.backtestWindow = 90;
        this.backtestLoaded = false;
        this.scenarioIndicator = 'industry_demand_velocity';
        this.bindActions();
        this.setupAdvancedControls();
        this.refreshAll();
    }

    bindActions() {
        const refreshAll = document.getElementById('refreshAll');
        if (refreshAll) refreshAll.addEventListener('click', () => this.refreshAll());
        const refreshInsights = document.getElementById('refreshInsights');
        if (refreshInsights) refreshInsights.addEventListener('click', () => this.loadInsights());
        const downloadTemplate = document.getElementById('downloadTemplate');
        if (downloadTemplate) downloadTemplate.addEventListener('click', () => this.downloadTemplate());
        document.querySelectorAll('#categoryFilter .chip').forEach(chip => {
            chip.addEventListener('click', () => {
                document.querySelectorAll('#categoryFilter .chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                this.currentCategory = chip.dataset.cat;
                this.renderIndicators();
                this.renderDashboards();
                this.renderInsights();
            });
        });
        const refreshCompliance = document.getElementById('btnRefreshCompliance');
        if (refreshCompliance) {
            refreshCompliance.addEventListener('click', () => {
                this.loadCompliance();
                this.loadAuditLog();
            });
        }
        const refreshCollection = document.getElementById('btnRefreshCollection');
        if (refreshCollection) {
            refreshCollection.addEventListener('click', () => {
                this.loadCollectionStats();
                this.loadProcessingPipeline();
            });
        }
        const refreshRAG = document.getElementById('btnRefreshRAG');
        if (refreshRAG) {
            refreshRAG.addEventListener('click', () => {
                this.loadRAGStats();
                this.loadRAGConnections();
            });
        }
    }

    setupAdvancedControls() {
        const refreshBacktest = document.getElementById('refreshBacktest');
        if (refreshBacktest) refreshBacktest.addEventListener('click', () => this.loadBacktest());
        const backtestIndicatorSelect = document.getElementById('backtestIndicator');
        if (backtestIndicatorSelect) backtestIndicatorSelect.addEventListener('change', (e) => {
            this.backtestIndicator = e.target.value;
            this.loadBacktest();
        });
        const backtestWindowSelect = document.getElementById('backtestWindow');
        if (backtestWindowSelect) backtestWindowSelect.addEventListener('change', (e) => {
            this.backtestWindow = parseInt(e.target.value, 10);
            this.loadBacktest();
        });
        const runScenario = document.getElementById('runScenario');
        if (runScenario) runScenario.addEventListener('click', () => this.runScenario());
        const scenarioIndicator = document.getElementById('scenarioIndicator');
        if (scenarioIndicator) scenarioIndicator.addEventListener('change', (e) => {
            this.scenarioIndicator = e.target.value;
        });
    }

    async refreshAll() {
        await Promise.all([
            this.loadIndicators(),
            this.loadDashboards(),
            this.loadInsights(),
            this.loadCompliance(),
            this.loadAuditLog(),
            this.loadCollectionStats(),
            this.loadProcessingPipeline(),
            this.loadRAGStats(),
            this.loadRAGConnections()
        ]);
    }

    async fetchJson(path) {
        const res = await fetch(`${this.API_BASE}${path}`);
        if (!res.ok) {
            const text = await res.text();
            throw new Error(text || `HTTP ${res.status}`);
        }
        return res.json();
    }

    async loadIndicators() {
        try {
            const data = await this.fetchJson('/indicators');
            this.indicators = data.indicators || [];
            this.updateStats(data);
            this.renderIndicators();
            this.populateIndicatorSelectors();
        } catch (error) {
            console.error('加载指标失败', error);
            const grid = document.getElementById('indicatorGrid');
            if (grid) grid.innerHTML = `<div class="muted">加载失败：${error.message}</div>`;
        }
    }

    async loadDashboards() {
        try {
            const data = await this.fetchJson('/dashboards');
            this.dashboards = data.dashboards || [];
            document.getElementById('statDashboards').textContent = this.dashboards.length;
            this.renderDashboards();
        } catch (error) {
            console.error('加载看板失败', error);
            const grid = document.getElementById('dashboardGrid');
            if (grid) grid.innerHTML = `<div class="muted">加载失败：${error.message}</div>`;
        }
    }

    async loadInsights() {
        try {
            const query = this.currentCategory !== 'all' ? `?category=${this.currentCategory}` : '';
            const data = await this.fetchJson(`/insights${query}`);
            this.insights = data.insights || [];
            this.renderInsights();
        } catch (error) {
            console.error('加载洞察失败', error);
            const timeline = document.getElementById('insightTimeline');
            if (timeline) timeline.innerHTML = `<div class="muted">加载失败：${error.message}</div>`;
        }
    }

    updateStats(data) {
        const total = data.count || this.indicators.length;
        document.getElementById('statIndicators').textContent = total;
        const industry = this.indicators.filter(i => i.category === 'industry').length;
        const region = this.indicators.filter(i => i.category === 'region').length;
        const policy = this.indicators.filter(i => i.category === 'policy').length;
        document.getElementById('statIndustry').textContent = industry;
        document.getElementById('statRegion').textContent = region;
        document.getElementById('statPolicy').textContent = policy;
    }

    filterByCategory(items) {
        if (this.currentCategory === 'all') return items;
        return items.filter(item => item.category === this.currentCategory);
    }

    badgeClass(category) {
        if (category === 'industry') return 'badge industry';
        if (category === 'region') return 'badge region';
        return 'badge policy';
    }

    badgeLabel(category) {
        if (category === 'industry') return '行业';
        if (category === 'region') return '区域';
        return '政策';
    }

    renderIndicators() {
        const grid = document.getElementById('indicatorGrid');
        if (!grid) return;
        const items = this.filterByCategory(this.indicators);
        if (!items.length) {
            grid.innerHTML = '<div class="muted">暂无指标数据</div>';
            return;
        }
        grid.innerHTML = '';
        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'indicator-card';
            div.innerHTML = `
                <div class="${this.badgeClass(item.category)}">${this.badgeLabel(item.category)}</div>
                <h3>${item.name}</h3>
                <p class="muted">${item.description}</p>
                <p style="margin:8px 0;font-weight:600;">当前：${item.current_value}${item.unit || ''}（${item.trend}）</p>
                <div class="muted">驱动因素：${(item.drivers || []).join(' / ')}</div>
                <div class="muted">风险：${(item.risks || []).join(' / ') || '—'}</div>
                <div style="margin-top:8px;font-size:13px;">建议：${(item.recommended_actions || []).join('；')}</div>
            `;
            grid.appendChild(div);
        });
    }

    populateIndicatorSelectors() {
        const options = this.indicators.map(ind => `<option value="${ind.id}">${ind.name}</option>`).join('');
        const backtestSelect = document.getElementById('backtestIndicator');
        const scenarioSelect = document.getElementById('scenarioIndicator');
        if (backtestSelect) {
            backtestSelect.innerHTML = options;
            if (!this.indicators.find(ind => ind.id === this.backtestIndicator) && this.indicators.length) {
                this.backtestIndicator = this.indicators[0].id;
            }
            backtestSelect.value = this.backtestIndicator;
        }
        if (scenarioSelect) {
            scenarioSelect.innerHTML = options;
            if (!this.indicators.find(ind => ind.id === this.scenarioIndicator) && this.indicators.length) {
                this.scenarioIndicator = this.indicators[0].id;
            }
            scenarioSelect.value = this.scenarioIndicator;
        }
        if (!this.backtestLoaded && this.indicators.length) {
            this.backtestLoaded = true;
            this.loadBacktest();
            this.runScenario();
        }
    }

    async loadBacktest() {
        const placeholder = document.getElementById('backtestSeries');
        if (placeholder) placeholder.textContent = '⏳ 回测计算中...';
        try {
            const data = await this.fetchJson(`/backtest?indicator=${encodeURIComponent(this.backtestIndicator)}&window=${this.backtestWindow}`);
            this.renderBacktest(data);
        } catch (error) {
            console.error('加载回测失败', error);
            if (placeholder) placeholder.textContent = `❌ 回测失败：${error.message}`;
        }
    }

    renderBacktest(data) {
        if (!data) return;
        const metrics = data.metrics || {};
        document.getElementById('btMAPE').textContent = metrics.mape ? `${metrics.mape}%` : '-';
        document.getElementById('btHitRate').textContent = metrics.hit_rate ? `${(metrics.hit_rate * 100).toFixed(0)}%` : '-';
        document.getElementById('btSharpe').textContent = metrics.sharpe ?? '-';
        const signal = metrics.last_signal ? `${metrics.last_signal}（Δ${metrics.predicted_change ?? 0}）` : '-';
        document.getElementById('btSignal').textContent = signal;

        const seriesBox = document.getElementById('backtestSeries');
        if (seriesBox) {
            const latest = (data.series || []).slice(-20);
            if (!latest.length) {
                seriesBox.textContent = '暂无时间序列数据';
            } else {
                seriesBox.textContent = latest.map(item => {
                    return `${item.date} | 实际 ${item.actual} | 预测 ${item.predicted}`;
                }).join('\n');
            }
        }

        const eventsBox = document.getElementById('backtestEvents');
        if (eventsBox) {
            const events = data.events || [];
            if (!events.length) {
                eventsBox.innerHTML = '<div class="muted">暂无回测事件</div>';
            } else {
                eventsBox.innerHTML = events.map(ev => `
                    <div class="timeline-item">
                        <strong>${ev.event}</strong>
                        <div class="muted">${ev.date} · ${ev.impact}</div>
                    </div>
                `).join('');
            }
        }
    }

    async runScenario() {
        const recBox = document.getElementById('scenarioRecommendations');
        if (recBox) recBox.textContent = '⏳ 情景计算中...';
        const payload = {
            indicator: this.scenarioIndicator,
            scenario_name: document.getElementById('scenarioName')?.value || '自定义情景',
            demand_shift: parseFloat(document.getElementById('scenarioDemand')?.value || '0') || 0,
            policy_intensity: parseFloat(document.getElementById('scenarioPolicy')?.value || '0') || 0,
            supply_shift: parseFloat(document.getElementById('scenarioSupply')?.value || '0') || 0
        };
        try {
            const res = await fetch(`${this.API_BASE}/what-if`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) {
                const text = await res.text();
                throw new Error(text || `HTTP ${res.status}`);
            }
            const data = await res.json();
            this.renderScenario(data);
        } catch (error) {
            console.error('情景模拟失败', error);
            if (recBox) recBox.textContent = `❌ 情景模拟失败：${error.message}`;
        }
    }

    renderScenario(data) {
        if (!data) return;
        document.getElementById('scenarioBase').textContent = data.forecast?.base ?? '-';
        document.getElementById('scenarioValue').textContent = data.forecast?.scenario ?? '-';
        document.getElementById('scenarioDelta').textContent = data.forecast?.delta ?? '-';
        document.getElementById('scenarioProb').textContent = data.forecast?.probability ? `${(data.forecast.probability * 100).toFixed(0)}%` : '-';

        const timeline = document.getElementById('scenarioTimeline');
        if (timeline) {
            const rows = data.timeline || [];
            if (!rows.length) {
                timeline.innerHTML = '<div class="muted">暂无时间线</div>';
            } else {
                timeline.innerHTML = rows.map(row => `
                    <div class="timeline-item">
                        <strong>${row.period}</strong>
                        <div class="muted">基准 ${row.base} · 情景 ${row.scenario}</div>
                    </div>
                `).join('');
            }
        }

        const recBox = document.getElementById('scenarioRecommendations');
        if (recBox) {
            const recs = data.recommendations || [];
            if (!recs.length) {
                recBox.textContent = '暂无建议';
            } else {
                let content = recs.map(rec => `• ${rec}`).join('<br>');
                // 显示RAG输出信息（如果有）
                if (data.rag_document_id) {
                    content += `<br><br><div class="muted">✅ 已输出到RAG系统（文档ID: ${data.rag_document_id}）</div>`;
                }
                recBox.innerHTML = content;
            }
        }
    }

    renderDashboards() {
        const grid = document.getElementById('dashboardGrid');
        if (!grid) return;
        const items = this.filterByCategory(
            this.dashboards.map(db => {
                if (!db.category && this.currentCategory === 'all') return db;
                return db;
            })
        );
        if (!this.dashboards.length) {
            grid.innerHTML = '<div class="muted">暂无看板模板</div>';
            return;
        }
        grid.innerHTML = '';
        this.dashboards.forEach(db => {
            if (this.currentCategory !== 'all') {
                const scenario = (db.scenario || '').toLowerCase();
                if (!scenario.includes(this.currentCategory)) {
                    // fallback: skip unmatched scenario
                    return;
                }
            }
            const card = document.createElement('div');
            card.className = 'dashboard-card';
            card.innerHTML = `
                <h3>${db.title}</h3>
                <p class="muted">${db.scenario}</p>
                <ul class="widget-list">
                    ${(db.widgets || []).map(w => `<li>${w.type.toUpperCase()} · ${w.label}</li>`).join('')}
                </ul>
                <p class="muted">适用角色：${(db.recommended_audience || []).join(' / ')}</p>
                <p style="font-size:13px;">动作建议：${db.call_to_action || '--'}</p>
            `;
            grid.appendChild(card);
        });
        if (!grid.children.length) {
            grid.innerHTML = '<div class="muted">该分类暂无看板模板</div>';
        }
    }

    async loadCompliance() {
        try {
            const data = await this.fetchJson('/compliance');
            this.renderCompliance(data.report || {});
        } catch (error) {
            console.error('加载合规报表失败', error);
            const tbody = document.getElementById('compliancePolicyTable');
            if (tbody) tbody.innerHTML = `<tr><td colspan="5" class="muted">加载失败：${error.message}</td></tr>`;
        }
    }

    renderCompliance(report) {
        const summary = report.summary || {};
        const coverageEl = document.getElementById('compPolicyCoverage');
        const qualityEl = document.getElementById('compDataQuality');
        const pendingEl = document.getElementById('compPendingActions');
        const blockedEl = document.getElementById('compBlockedSources');
        if (coverageEl) coverageEl.textContent = this.formatPercent(summary.policy_coverage);
        if (qualityEl) qualityEl.textContent = this.formatPercent(summary.data_quality);
        if (pendingEl) pendingEl.textContent = summary.pending_actions ?? '-';
        if (blockedEl) blockedEl.textContent = summary.blocked_sources ?? '-';

        const tbody = document.getElementById('compliancePolicyTable');
        if (tbody) {
            const policies = report.policies || [];
            if (!policies.length) {
                tbody.innerHTML = '<tr><td colspan="5" class="muted">暂无策略数据</td></tr>';
            } else {
                tbody.innerHTML = policies.map(policy => `
                    <tr>
                        <td>${policy.name}</td>
                        <td>${policy.owner}</td>
                        <td>${(policy.status || '').toUpperCase()}</td>
                        <td>${this.formatPercent(policy.coverage)}</td>
                        <td>${this.formatTime(policy.last_review)}</td>
                    </tr>
                `).join('');
            }
        }

        const sourceGrid = document.getElementById('complianceSources');
        if (sourceGrid) {
            const sources = report.ingestion?.sources || [];
            if (!sources.length) {
                sourceGrid.innerHTML = '<div class="muted">暂无采集来源</div>';
            } else {
                sourceGrid.innerHTML = sources.map(src => `
                    <div class="indicator-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <h3>${src.name}</h3>
                            <span class="badge ${this.statusBadgeClass(src.status)}">${src.status}</span>
                        </div>
                        <p class="muted">记录数 ${src.records ?? 0}</p>
                        <p class="muted">延迟 ${src.latency_min != null ? `${src.latency_min} 分钟` : '—'}</p>
                    </div>
                `).join('');
            }
        }
    }

    async loadAuditLog() {
        try {
            const data = await this.fetchJson('/audit?limit=20');
            this.renderAuditLog(data.audit || []);
        } catch (error) {
            console.error('加载审计日志失败', error);
            const timeline = document.getElementById('auditTimeline');
            if (timeline) timeline.innerHTML = `<div class="muted">加载失败：${error.message}</div>`;
        }
    }

    renderAuditLog(logs) {
        const container = document.getElementById('auditTimeline');
        if (!container) return;
        if (!logs.length) {
            container.innerHTML = '<div class="timeline-item"><strong>暂无审计记录</strong></div>';
            return;
        }
        container.innerHTML = logs.map(log => `
            <div class="timeline-item">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <strong>${log.source}</strong>
                    <span class="impact-tag ${this.impactClass(log.risk === 'high' ? 'negative' : log.risk === 'medium' ? 'warning' : 'positive')}">
                        ${log.status}
                    </span>
                </div>
                <div class="muted">${this.formatTime(log.timestamp)} · ${log.action} · ${log.records || 0} 条</div>
                <p>${log.notes || '--'}</p>
                <div class="muted">Reviewer: ${log.reviewer || 'system'}</div>
            </div>
        `).join('');
    }

    statusBadgeClass(status) {
        if (status === 'blocked') return 'badge policy';
        if (status === 'manual_review') return 'badge region';
        return 'badge industry';
    }

    renderInsights() {
        const timeline = document.getElementById('insightTimeline');
        if (!timeline) return;
        const items = this.filterByCategory(this.insights);
        if (!items.length) {
            timeline.innerHTML = '<div class="muted">暂无洞察</div>';
            return;
        }
        timeline.innerHTML = '';
        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'timeline-item';
            div.innerHTML = `
                <div style="display:flex;align-items:center;gap:8px;">
                    <strong>${item.title}</strong>
                    <span class="impact-tag ${this.impactClass(item.impact)}">${this.impactLabel(item.impact)}</span>
                </div>
                <div class="muted">${item.region || ''} · ${this.formatTime(item.timestamp)}</div>
                <p>${item.summary}</p>
                <p class="muted">推荐动作：${item.action || '--'}</p>
                <div class="muted">${(item.tags || []).map(tag => `#${tag}`).join(' ')}</div>
            `;
            timeline.appendChild(div);
        });
    }

    impactClass(impact) {
        if (impact === 'positive') return 'impact-positive';
        if (impact === 'negative') return 'impact-negative';
        return 'impact-warning';
    }

    impactLabel(impact) {
        if (impact === 'positive') return '利好';
        if (impact === 'negative') return '风险';
        return '预警';
    }

    formatTime(ts) {
        if (!ts) return '';
        try {
            const date = new Date(ts);
            return date.toLocaleString('zh-CN', { hour12: false });
        } catch {
            return ts;
        }
    }

    formatPercent(value, digits = 0) {
        if (typeof value !== 'number') return '--';
        return `${(value * 100).toFixed(digits)}%`;
    }

    downloadTemplate() {
        const payload = {
            indicators: this.indicators,
            dashboards: this.dashboards,
            insights: this.insights
        };
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'trend_dashboard_template.json';
        a.click();
        URL.revokeObjectURL(url);
    }

    // ==================== P2-011: 数据采集/处理可视化 ====================
    
    async loadCollectionStats() {
        try {
            const data = await this.fetchJson('/data/collection/stats?days=7');
            this.renderCollectionStats(data);
        } catch (error) {
            console.error('加载采集统计失败', error);
        }
    }

    renderCollectionStats(data) {
        if (!data) return;
        
        const summary = data.source_summary || {};
        const totalCollections = data.total_collections || 0;
        const totalProcessings = data.total_processings || 0;
        
        // 计算平均处理时间
        let avgTime = 0.0;
        let totalTime = 0.0;
        let count = 0;
        for (const src in summary) {
            if (summary[src].avg_processing_time) {
                totalTime += summary[src].avg_processing_time;
                count++;
            }
        }
        avgTime = count > 0 ? totalTime / count : 0.0;
        
        // 计算成功率
        let totalSuccess = 0;
        let totalAttempts = 0;
        for (const src in summary) {
            totalAttempts += summary[src].collection_count || 0;
            totalSuccess += Math.round((summary[src].success_rate || 0) / 100 * (summary[src].collection_count || 0));
        }
        const successRate = totalAttempts > 0 ? (totalSuccess / totalAttempts * 100) : 0.0;
        
        document.getElementById('collectionTotal').textContent = totalCollections;
        document.getElementById('processingTotal').textContent = totalProcessings;
        document.getElementById('avgProcessingTime').textContent = `${avgTime.toFixed(2)}s`;
        document.getElementById('collectionSuccessRate').textContent = `${successRate.toFixed(1)}%`;
        
        // 渲染数据源统计
        const sourceGrid = document.getElementById('collectionSourceStats');
        if (sourceGrid) {
            const sources = Object.keys(summary);
            if (!sources.length) {
                sourceGrid.innerHTML = '<div class="muted">暂无数据源统计</div>';
            } else {
                sourceGrid.innerHTML = sources.map(src => {
                    const stats = summary[src];
                    return `
                        <div class="indicator-card">
                            <h3>${src}</h3>
                            <p class="muted">采集: ${stats.total_collected} 条</p>
                            <p class="muted">处理: ${stats.total_processed} 条</p>
                            <p class="muted">成功率: ${stats.success_rate.toFixed(1)}%</p>
                            <p class="muted">平均处理时间: ${stats.avg_processing_time.toFixed(2)}s</p>
                        </div>
                    `;
                }).join('');
            }
        }
    }

    async loadProcessingPipeline() {
        try {
            const data = await this.fetchJson('/data/processing/pipeline?limit=20');
            this.renderProcessingPipeline(data);
        } catch (error) {
            console.error('加载处理流水线失败', error);
        }
    }

    renderProcessingPipeline(data) {
        const container = document.getElementById('processingPipeline');
        if (!container) return;
        
        const pipeline = data.pipeline || [];
        if (!pipeline.length) {
            container.innerHTML = '<div class="timeline-item"><strong>暂无处理流水线数据</strong></div>';
            return;
        }
        
        container.innerHTML = pipeline.map(batch => {
            const steps = batch.steps || [];
            return `
                <div class="timeline-item">
                    <strong>${batch.source}</strong>
                    <div class="muted">${this.formatTime(batch.timestamp)}</div>
                    <div style="margin-top:8px;">
                        ${steps.map(step => `
                            <div style="margin-left:16px;margin-top:4px;font-size:13px;">
                                ${step.step}: ${step.input_count} → ${step.output_count} 
                                (效率: ${step.efficiency.toFixed(1)}%, 耗时: ${step.processing_time.toFixed(2)}s)
                                <span class="badge ${step.status === 'success' ? 'industry' : 'policy'}">${step.status}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }).join('');
    }

    // ==================== P2-011: RAG 输出 ====================
    
    async loadRAGStats() {
        try {
            const data = await this.fetchJson('/rag/output/stats?days=7');
            this.renderRAGStats(data);
        } catch (error) {
            console.error('加载RAG统计失败', error);
        }
    }

    renderRAGStats(data) {
        if (!data) return;
        
        document.getElementById('ragTotalOutputs').textContent = data.total_outputs || 0;
        document.getElementById('ragSuccessCount').textContent = data.success_count || 0;
        document.getElementById('ragSuccessRate').textContent = `${data.success_rate.toFixed(1)}%`;
        document.getElementById('ragIndicators').textContent = Object.keys(data.indicator_stats || {}).length;
    }

    async loadRAGConnections() {
        try {
            const data = await this.fetchJson('/rag/connections');
            this.renderRAGConnections(data);
        } catch (error) {
            console.error('加载RAG关联失败', error);
        }
    }

    renderRAGConnections(data) {
        const container = document.getElementById('ragConnections');
        if (!container) return;
        
        if (data.total_indicators) {
            // 全部关联信息
            container.innerHTML = `
                <div><strong>总指标数:</strong> ${data.total_indicators}</div>
                <div><strong>总文档数:</strong> ${data.total_documents}</div>
                <div style="margin-top:12px;">
                    <strong>关联详情:</strong>
                    <ul style="margin-top:8px;padding-left:20px;">
                        ${Object.entries(data.connections || {}).map(([ind, conn]) => 
                            `<li>${ind}: ${conn.count} 个文档</li>`
                        ).join('')}
                    </ul>
                </div>
            `;
        } else {
            // 单个指标关联信息
            container.innerHTML = `
                <div><strong>指标:</strong> ${data.indicator}</div>
                <div><strong>关联文档数:</strong> ${data.count}</div>
                <div style="margin-top:12px;">
                    <strong>文档ID列表:</strong>
                    <ul style="margin-top:8px;padding-left:20px;">
                        ${(data.rag_documents || []).map(doc => `<li>${doc}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // 加载最近输出记录
        this.loadRAGOutputLogs();
    }

    async loadRAGOutputLogs() {
        try {
            // 这里可以从stats中获取，或者新增一个专门的日志端点
            const stats = await this.fetchJson('/rag/output/stats?days=7');
            const container = document.getElementById('ragOutputLogs');
            if (container) {
                const indicatorStats = stats.indicator_stats || {};
                if (Object.keys(indicatorStats).length === 0) {
                    container.innerHTML = '<div class="timeline-item"><strong>暂无输出记录</strong></div>';
                } else {
                    container.innerHTML = Object.entries(indicatorStats).map(([ind, stat]) => `
                        <div class="timeline-item">
                            <strong>${ind}</strong>
                            <div class="muted">成功: ${stat.success} | 失败: ${stat.error}</div>
                        </div>
                    `).join('');
                }
            }
        } catch (error) {
            console.error('加载RAG输出记录失败', error);
        }
    }
}

window.addEventListener('DOMContentLoaded', () => {
    new TrendInsightsConsole();
});

