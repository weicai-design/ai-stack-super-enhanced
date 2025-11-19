class StockSimulatorConsole {
    constructor() {
        this.API = '/api/super-agent';
        this.state = null;
        this.riskReport = null;
        this.executionReport = null;
        this.trades = [];
        this.factorData = null;
        this.sourceState = null;
        this.bindEvents();
        this.refreshAll();
        this.setupFactorControls();
        this.loadFactorInsights('600519.SS');
    }

    bindEvents() {
        const byId = (id) => document.getElementById(id);
        byId('btnRefresh')?.addEventListener('click', () => this.refreshAll());
        byId('btnDownload')?.addEventListener('click', () => this.downloadReport());
        byId('btnPlaceOrder')?.addEventListener('click', () => this.placeOrder());
        byId('btnFetchQuote')?.addEventListener('click', () => this.fetchQuote());
        byId('btnUpdateRisk')?.addEventListener('click', () => this.updateRisk());
        byId('btnLoadRisk')?.addEventListener('click', () => this.loadRiskConfig());
        byId('btnApplySource')?.addEventListener('click', () => this.applySource());
        byId('btnRefreshSources')?.addEventListener('click', () => this.loadSources());
    }

    setupFactorControls() {
        const btn = document.getElementById('btnRefreshFactors');
        if (!btn) return;
        btn.addEventListener('click', () => {
            const factorInput = document.getElementById('factorSymbolInput');
            const orderSymbol = document.getElementById('orderSymbol');
            const symbol = (factorInput?.value || orderSymbol?.value || '').trim();
            if (!symbol) {
                alert('请先填写股票代码');
                return;
            }
            this.loadFactorInsights(symbol);
        });
    }

    async refreshAll() {
        await Promise.all([
            this.loadState(),
            this.loadRiskReport(),
            this.loadExecutionReport(),
            this.loadRiskConfig()
        ]);
        this.loadTrades();
        this.loadSources();
    }

    async request(path, options) {
        const res = await fetch(`${this.API}${path}`, options);
        if (!res.ok) {
            const detail = await res.text();
            throw new Error(detail || `HTTP ${res.status}`);
        }
        return res.json();
    }

    async loadState() {
        try {
            this.state = await this.request('/stock/sim/state');
            this.renderStats();
            this.renderPositions();
        } catch (error) {
            this.log(`❌ 加载状态失败：${error.message}`);
        }
    }

    async loadRiskReport() {
        try {
            const data = await this.request('/stock/sim/risk-report');
            this.riskReport = data.report;
            this.renderRiskAlerts();
        } catch (error) {
            this.log(`❌ 风险报表失败：${error.message}`);
        }
    }

    async loadExecutionReport() {
        try {
            const data = await this.request('/stock/sim/execution-report');
            this.executionReport = data.report;
            this.renderExecution();
        } catch (error) {
            this.log(`❌ 执行报表失败：${error.message}`);
        }
    }

    async loadTrades() {
        try {
            const data = await this.request('/stock/sim/trades?limit=50');
            this.trades = data.trades || [];
            this.renderTrades();
        } catch (error) {
            this.log(`❌ 加载成交失败：${error.message}`);
        }
    }

    async loadRiskConfig() {
        try {
            const data = await this.request('/stock/sim/risk-config');
            const cfg = data.config || {};
            document.getElementById('riskMaxPos').value = cfg.max_position_ratio ?? '';
            document.getElementById('riskStopLoss').value = cfg.stop_loss_ratio ?? '';
            document.getElementById('riskSlip').value = cfg.slip_bps ?? '';
        } catch (error) {
            this.log(`⚠️ 风控配置加载失败：${error.message}`);
        }
    }

    async placeOrder() {
        try {
            const symbol = document.getElementById('orderSymbol').value.trim();
            if (!symbol) throw new Error('股票代码不能为空');
            const side = document.getElementById('orderSide').value;
            const qty = parseInt(document.getElementById('orderQty').value, 10);
            const order_type = document.getElementById('orderType').value;
            const priceInput = document.getElementById('orderPrice').value;
            const price = priceInput ? parseFloat(priceInput) : null;
            const payload = {
                symbol,
                side,
                qty,
                order_type,
                price
            };
            const data = await this.request('/stock/sim/place-order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            this.log(`✅ 订单已提交：${data.order.order_id}`);
        } catch (error) {
            this.log(`❌ 下单失败：${error.message}`);
        }
    }

    async fetchQuote() {
        try {
            const symbol = document.getElementById('orderSymbol').value.trim();
            if (!symbol) throw new Error('请先填写股票代码');
            const data = await this.request(`/stock/quote?symbol=${encodeURIComponent(symbol)}&market=A`);
            const src = data.quote?.source || 'NA';
            this.log(`📈 [${src}] ${symbol} = ${data.quote.price}，撮合 ${data.sim_fills.length} 笔`);
            this.refreshAll();
        } catch (error) {
            this.log(`❌ 获取行情失败：${error.message}`);
        }
    }

    async updateRisk() {
        try {
            const body = {
                max_position_ratio: parseFloat(document.getElementById('riskMaxPos').value),
                stop_loss_ratio: parseFloat(document.getElementById('riskStopLoss').value),
                slip_bps: parseFloat(document.getElementById('riskSlip').value)
            };
            const data = await this.request('/stock/sim/risk-config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            this.log(`⚙️ 风控已更新：max=${data.config.max_position_ratio}`);
            this.refreshAll();
        } catch (error) {
            this.log(`❌ 更新风控失败：${error.message}`);
        }
    }

    renderStats() {
        if (!this.state) return;
        document.getElementById('statCash').textContent = this.formatCurrency(this.state.cash);
        document.getElementById('statMarketValue').textContent = this.formatCurrency(this.state.market_value);
        document.getElementById('statEquity').textContent = this.formatCurrency(this.state.equity);
        document.getElementById('statPnL').textContent = this.formatCurrency(this.state.realized_pnl);
    }

    renderPositions() {
        const table = document.getElementById('positionTable');
        if (!this.state || !table) return;
        const positions = this.state.positions || {};
        const symbols = Object.keys(positions);
        if (!symbols.length) {
            table.innerHTML = '<tr><td colspan="5" class="muted">暂无持仓</td></tr>';
            return;
        }
        table.innerHTML = '';
        symbols.forEach(sym => {
            const qty = positions[sym];
            const avg = this.state.avg_cost?.[sym] ?? 0;
            const last = this.riskReport?.exposures?.find(e => e.symbol === sym)?.last_price ?? '-';
            const value = qty * avg;
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${sym}</td>
                <td>${qty}</td>
                <td>${avg.toFixed ? avg.toFixed(3) : avg}</td>
                <td>${last}</td>
                <td>${this.formatCurrency(value)}</td>
            `;
            table.appendChild(tr);
        });
    }

    renderRiskAlerts() {
        const container = document.getElementById('riskAlerts');
        if (!container) return;
        const alerts = this.riskReport?.alerts || [];
        if (!alerts.length) {
            container.innerHTML = '<div class="timeline-item"><strong>暂无风险事件</strong><p class="muted">等待下一笔交易</p></div>';
            return;
        }
        container.innerHTML = '';
        alerts.forEach(alert => {
            const div = document.createElement('div');
            div.className = 'timeline-item';
            const cls = alert.level === 'error' ? 'tag error' : alert.level === 'warning' ? 'tag warning' : 'tag success';
            div.innerHTML = `
                <div style="display:flex;align-items:center;gap:8px;">
                    <span class="${cls}">${alert.level.toUpperCase()}</span>
                    <strong>${alert.message}</strong>
                </div>
                <div class="muted">${alert.timestamp}</div>
            `;
            container.appendChild(div);
        });
    }

    renderExecution() {
        if (!this.executionReport) return;
        const summary = `成交 ${this.executionReport.total_trades} 笔 · 胜率 ${(this.executionReport.win_rate * 100).toFixed(1)}% · PnL ${this.formatCurrency(this.executionReport.realized_pnl)} · 平均滑点 ${(this.executionReport.avg_slippage_bps || 0).toFixed(2)} bps`;
        document.getElementById('execSummary').textContent = summary;
        const curveBox = document.getElementById('equityCurve');
        const curve = this.executionReport.equity_curve || [];
        if (!curve.length) {
            curveBox.textContent = '暂无权益曲线数据';
        } else {
            curveBox.textContent = curve.slice(-10).map(point => `${point.timestamp.split('T')[1] || point.timestamp} | Equity ${point.equity}`).join('\n');
        }
    }

    renderTrades() {
        const table = document.getElementById('tradeTable');
        if (!table) return;
        if (!this.trades.length) {
            table.innerHTML = '<tr><td colspan="5" class="muted">暂无成交</td></tr>';
            return;
        }
        table.innerHTML = '';
        this.trades.slice().reverse().forEach(trade => {
            const tr = document.createElement('tr');
            const pnl = trade.pnl || 0;
            const pnlClass = pnl > 0 ? 'success' : pnl < 0 ? 'error' : 'warning';
            tr.innerHTML = `
                <td>${trade.timestamp?.replace('T', ' ').slice(5,19)}</td>
                <td>${trade.symbol}</td>
                <td>${trade.side.toUpperCase()}</td>
                <td>${trade.exec_price}</td>
                <td><span class="tag ${pnlClass}">${pnl.toFixed(2)}</span></td>
            `;
            table.appendChild(tr);
        });
    }

    async loadFactorInsights(symbol) {
        try {
            const data = await this.request(`/stock/analysis/factors?stock_code=${encodeURIComponent(symbol)}`);
            this.factorData = data;
            const input = document.getElementById('factorSymbolInput');
            if (input) input.value = symbol;
            this.renderFactorBoard();
        } catch (error) {
            this.log(`❌ 因子洞察失败：${error.message}`);
            this.factorData = null;
            this.renderFactorBoard();
        }
    }

    renderFactorBoard() {
        const summary = document.getElementById('factorSummary');
        const grid = document.getElementById('factorGrid');
        const drivers = document.getElementById('factorDrivers');
        if (!summary || !grid || !drivers) return;
        if (!this.factorData) {
            summary.textContent = '暂无因子数据';
            grid.innerHTML = '<div class="muted">点击刷新获取最新因子</div>';
            drivers.innerHTML = '<div class="timeline-item"><strong>暂无驱动项</strong></div>';
            return;
        }
        const prediction = this.factorData.prediction || {};
        summary.textContent = `信号 ${prediction.signal || '-'} · 置信度 ${this.formatPercent(prediction.confidence)} · Alpha ${this.formatPercent(prediction.alpha_score)} · 视角 ${prediction.horizon || '--'}`;
        const factors = this.factorData.factors || {};
        const entries = Object.entries(factors);
        grid.innerHTML = entries.length
            ? entries.map(([key, val]) => `
                <div class="factor-card">
                    <span>${this.formatFactorLabel(key)}</span>
                    <strong>${this.formatPercent(val.score)}</strong>
                    <div class="muted">${val.label || ''}</div>
                </div>
            `).join('')
            : '<div class="muted">未获取到因子信息</div>';
        const items = [];
        (prediction.drivers || []).forEach(text => items.push({ text, type: 'driver' }));
        (prediction.risks || []).forEach(text => items.push({ text, type: 'risk' }));
        if (!items.length && this.factorData.factors?.news_sentiment?.samples) {
            items.push({ text: this.factorData.factors.news_sentiment.samples[0], type: 'driver' });
        }
        if (!items.length) {
            items.push({ text: '暂无显著驱动', type: 'neutral' });
        }
        drivers.innerHTML = items.map(entry => `
            <div class="timeline-item">
                <strong>${entry.type === 'risk' ? '⚠️ ' : '✨ '}${entry.text}</strong>
            </div>
        `).join('');
    }

    async loadSources() {
        try {
            const data = await this.request('/stock/sources');
            this.sourceState = data;
            this.renderSources(data);
        } catch (error) {
            const list = document.getElementById('sourceList');
            if (list) {
                list.innerHTML = `<div style="color:#f87171;">数据源加载失败：${error.message}</div>`;
            }
        }
    }

    renderSources(data) {
        if (!data) return;
        const select = document.getElementById('sourceSelect');
        const activeLabel = document.getElementById('sourceActive');
        const msg = document.getElementById('sourceStatusMessage');
        const list = document.getElementById('sourceList');
        if (activeLabel) activeLabel.textContent = data.active || '-';
        if (select) {
            select.innerHTML = (data.available || []).map(src => `
                <option value="${src.id}" ${src.id === data.active ? 'selected' : ''} ${!src.ready && src.id !== 'mock' ? 'disabled' : ''}>
                    ${src.label} ${src.ready || src.id === 'mock' ? '' : '(未配置)'}
                </option>
            `).join('');
        }
        if (msg) {
            const readyCount = (data.available || []).filter(src => src.ready || src.id === 'mock').length;
            msg.textContent = readyCount
                ? `可用数据源 ${readyCount} 个，支持热切换。`
                : '暂无可用数据源，仅可使用内置模拟行情。';
        }
        if (list) {
            list.innerHTML = (data.available || []).map(src => `
                <div class="source-item">
                    <strong>${src.label}</strong>
                    <div class="muted">${src.vendor} · ${src.ready || src.id === 'mock' ? '✅ 就绪' : '⚠️ 未配置'}</div>
                    <div class="muted">延迟 ${this.formatLatency(src.latency_ms)} · 最近成功 ${src.last_success || '—'}</div>
                    ${src.last_error ? `<div style="color:#f97316;font-size:12px;">错误: ${src.last_error}</div>` : ''}
                </div>
            `).join('');
        }
    }

    async applySource() {
        const select = document.getElementById('sourceSelect');
        if (!select || !select.value) {
            alert('请选择一个数据源');
            return;
        }
        try {
            await this.request('/stock/switch-source', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source: select.value })
            });
            this.log(`🔄 已切换数据源：${select.value}`);
            this.loadSources();
        } catch (error) {
            this.log(`❌ 切换数据源失败：${error.message}`);
        }
    }

    formatFactorLabel(key) {
        const map = {
            news_sentiment: '新闻情绪',
            social_buzz: '社交流量',
            announcement_heat: '公告热度',
            financial_health: '财务健康',
            capital_flow: '资金流',
            risk_events: '风险事件'
        };
        return map[key] || key;
    }

    formatPercent(value) {
        if (typeof value !== 'number') return '--';
        return `${(value * 100).toFixed(0)}%`;
    }

    formatCurrency(value) {
        return typeof value === 'number' ? `¥${value.toLocaleString('zh-CN', { maximumFractionDigits: 2 })}` : value;
    }

    formatLatency(value) {
        if (typeof value !== 'number') return '—';
        return `${value} ms`;
    }

    log(message) {
        const logBox = document.getElementById('orderLog');
        if (!logBox) return;
        const time = new Date().toLocaleTimeString('zh-CN', { hour12: false });
        logBox.textContent = `[${time}] ${message}\n` + logBox.textContent;
    }

    downloadReport() {
        const payload = {
            state: this.state,
            risk_report: this.riskReport,
            execution_report: this.executionReport,
            trades: this.trades
        };
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `stock_sim_report_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    new StockSimulatorConsole();
});

