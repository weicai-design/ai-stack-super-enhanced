class ErpBpmConsole {
    constructor() {
        this.API_BPMN = '/api/super-agent/erp/bpmn';
        this.API_RUNTIME = '/api/super-agent/erp/bpmn/runtime';
        this.API_TRIAL = '/api/super-agent/erp/trial/calc';
        this.processes = [];
        this.instances = [];
        this.selectedProcessId = null;
        this.selectedInstanceId = null;
        this.autoTimer = null;

        this.processListEl = document.getElementById('processList');
        this.processSearchEl = document.getElementById('processSearch');
        this.nodeContainer = document.getElementById('nodeContainer');
        this.jsonPreview = document.getElementById('jsonPreview');
        this.runtimeTable = document.getElementById('runtimeTable');
        this.timelineBox = document.getElementById('timelineBox');
        this.runtimeHint = document.getElementById('runtimeHint');
        this.trialResult = document.getElementById('trialResult');

        this.bindEvents();
        this.refreshProcesses();
        this.refreshRuntime();
    }

    bindEvents() {
        const refreshBtn = document.getElementById('refreshProcesses');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshProcesses());
        }
        const runtimeRefresh = document.getElementById('refreshRuntime');
        if (runtimeRefresh) {
            runtimeRefresh.addEventListener('click', () => this.refreshRuntime());
        }
        if (this.processSearchEl) {
            this.processSearchEl.addEventListener('input', () => this.renderProcessList());
        }
        const autoToggle = document.getElementById('runtimeAuto');
        if (autoToggle) {
            autoToggle.addEventListener('change', () => this.toggleAuto(autoToggle.checked));
            this.toggleAuto(autoToggle.checked);
        }
        const trialForm = document.getElementById('trialForm');
        if (trialForm) {
            trialForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.runTrial();
            });
        }
        const openDesigner = document.getElementById('openDesigner');
        if (openDesigner) {
            openDesigner.addEventListener('click', () => window.open('bpmn_designer.html', '_blank'));
        }
        const openRuntime = document.getElementById('openRuntime');
        if (openRuntime) {
            openRuntime.addEventListener('click', () => window.open('bpmn_runtime.html', '_blank'));
        }
    }

    toggleAuto(enabled) {
        if (this.autoTimer) {
            clearInterval(this.autoTimer);
            this.autoTimer = null;
        }
        if (enabled) {
            this.autoTimer = setInterval(() => this.refreshRuntime(false), 10000);
        }
    }

    async fetchJson(url, options) {
        const res = await fetch(url, options);
        if (!res.ok) {
            const text = await res.text();
            throw new Error(text || `HTTP ${res.status}`);
        }
        return res.json();
    }

    async refreshProcesses() {
        try {
            const data = await this.fetchJson(`${this.API_BPMN}/processes`);
            this.processes = data.processes || [];
            if (!this.selectedProcessId && this.processes.length) {
                this.selectedProcessId = this.processes[0].id;
            }
            this.renderProcessList();
            if (this.selectedProcessId) {
                this.loadProcess(this.selectedProcessId);
            } else {
                this.renderProcessDetail(null);
            }
        } catch (error) {
            console.error('加载流程列表失败', error);
            if (this.processListEl) {
                this.processListEl.innerHTML = `<li class="muted">加载失败：${error.message}</li>`;
            }
        }
    }

    renderProcessList() {
        if (!this.processListEl) return;
        const keyword = (this.processSearchEl?.value || '').toLowerCase();
        const filtered = this.processes.filter(item => {
            if (!keyword) return true;
            return (
                item.id.toLowerCase().includes(keyword) ||
                (item.filename || '').toLowerCase().includes(keyword)
            );
        });
        if (!filtered.length) {
            this.processListEl.innerHTML = '<li class="muted">未找到匹配流程</li>';
            return;
        }
        this.processListEl.innerHTML = '';
        filtered.forEach(item => {
            const li = document.createElement('li');
            li.dataset.id = item.id;
            li.className = item.id === this.selectedProcessId ? 'active' : '';
            li.innerHTML = `
                <div style="font-weight:600;">${item.id}</div>
                <div class="muted">${item.updated_at ? item.updated_at.replace('T', ' ').slice(0, 16) : ''}</div>
            `;
            li.addEventListener('click', () => {
                this.selectedProcessId = item.id;
                this.highlightProcess();
                this.loadProcess(item.id);
            });
            this.processListEl.appendChild(li);
        });
    }

    highlightProcess() {
        if (!this.processListEl) return;
        Array.from(this.processListEl.children).forEach(li => {
            li.classList.toggle('active', li.dataset.id === this.selectedProcessId);
        });
    }

    async loadProcess(id) {
        if (!id) return;
        try {
            const data = await this.fetchJson(`${this.API_BPMN}/process/${id}`);
            this.renderProcessDetail(data);
        } catch (error) {
            console.error('加载流程详情失败', error);
            this.renderProcessDetail(null, error.message);
        }
    }

    renderProcessDetail(payload, errorMessage) {
        const data = payload?.data;
        document.getElementById('detailProcessId').textContent = payload?.id || '--';
        document.getElementById('detailProcessName').textContent = data?.name || '--';
        document.getElementById('detailProcessVersion').textContent = data?.version ?? '--';
        document.getElementById('detailProcessDomain').textContent = data?.domain || '--';
        const descEl = document.getElementById('detailProcessDesc');
        if (errorMessage) {
            descEl.textContent = `加载失败：${errorMessage}`;
        } else {
            descEl.textContent = data?.description || '暂无流程描述';
        }
        this.renderNodes(data?.nodes || []);
        this.jsonPreview.textContent = JSON.stringify(
            {
                id: payload?.id,
                ...data
            },
            null,
            2
        );
    }

    renderNodes(nodes) {
        if (!this.nodeContainer) return;
        if (!nodes.length) {
            this.nodeContainer.innerHTML = '<div class="muted">暂无节点定义</div>';
            return;
        }
        this.nodeContainer.innerHTML = '';
        nodes.forEach(node => {
            const div = document.createElement('div');
            div.className = 'node-card';
            div.innerHTML = `
                <strong>${node.name || node.id}</strong>
                <div class="muted">ID: ${node.id || '-'}</div>
                <div>类型：${node.type || '-'}</div>
                <div>负责人：${node.owner || '未指定'}</div>
                <div>SLA：${node.sla_days ?? '--'} 天</div>
                <div class="muted">前置：${(node.incoming || []).join(', ') || '无'}</div>
                <div class="muted">后续：${(node.outgoing || []).join(', ') || '无'}</div>
            `;
            this.nodeContainer.appendChild(div);
        });
    }

    async refreshRuntime(showToast = true) {
        try {
            const data = await this.fetchJson(`${this.API_RUNTIME}/instances`);
            this.instances = data.instances || [];
            this.renderRuntimeTable();
            if (showToast && this.runtimeHint) {
                this.runtimeHint.textContent = `共 ${this.instances.length} 个活跃/近期实例`;
            }
            if (this.selectedInstanceId) {
                this.loadInstance(this.selectedInstanceId);
            } else if (this.instances.length) {
                this.loadInstance(this.instances[0].instance_id);
            } else {
                this.renderTimeline([]);
            }
        } catch (error) {
            console.error('加载运行数据失败', error);
            if (this.runtimeTable) {
                this.runtimeTable.innerHTML = `<tr><td colspan="5" class="muted">加载失败：${error.message}</td></tr>`;
            }
        }
    }

    renderRuntimeTable() {
        if (!this.runtimeTable) return;
        if (!this.instances.length) {
            this.runtimeTable.innerHTML = '<tr><td colspan="5" class="muted">暂无流程实例</td></tr>';
            return;
        }
        this.runtimeTable.innerHTML = '';
        this.instances.forEach(inst => {
            const tr = document.createElement('tr');
            tr.className = 'instance-row';
            tr.innerHTML = `
                <td>${inst.instance_id}</td>
                <td>${inst.process_id || '-'}</td>
                <td>${inst.last_node || '-'}</td>
                <td>${this.renderStatus(inst.last_status)}</td>
                <td>${inst.updated_at || '-'}</td>
            `;
            tr.addEventListener('click', () => {
                this.selectedInstanceId = inst.instance_id;
                this.loadInstance(inst.instance_id);
            });
            this.runtimeTable.appendChild(tr);
        });
    }

    renderStatus(status) {
        const map = {
            completed: 'success',
            started: 'warning',
            in_progress: 'warning',
            error: 'error',
            failed: 'error'
        };
        const cls = map[status] || 'warning';
        return `<span class="status-pill ${cls}">${status || '未知'}</span>`;
    }

    async loadInstance(instanceId) {
        if (!instanceId) return;
        try {
            const data = await this.fetchJson(`${this.API_RUNTIME}/instance/${instanceId}`);
            this.selectedInstanceId = instanceId;
            if (this.runtimeHint) {
                const proc = data.instance?.process_id || '--';
                const node = data.instance?.current_node || '--';
                this.runtimeHint.textContent = `${instanceId} · ${proc} · 当前节点 ${node}`;
            }
            this.renderTimeline(data.events || []);
        } catch (error) {
            console.error('加载实例失败', error);
            this.timelineBox.innerHTML = `<div class="muted">加载实例失败：${error.message}</div>`;
        }
    }

    renderTimeline(events) {
        if (!this.timelineBox) return;
        if (!events.length) {
            this.timelineBox.innerHTML = '<div class="muted">暂无事件</div>';
            return;
        }
        this.timelineBox.innerHTML = '';
        events.forEach(evt => {
            const div = document.createElement('div');
            div.className = 'timeline-item';
            div.innerHTML = `
                <strong>${evt.node_name || evt.node_id}</strong>
                <div class="muted">${evt.timestamp || ''}</div>
                <p>${evt.message || '无描述'}</p>
                ${evt.status ? `<span class="status-pill ${this.statusClass(evt.status)}">${evt.status}</span>` : ''}
            `;
            this.timelineBox.appendChild(div);
        });
    }

    statusClass(status) {
        if (status === 'completed') return 'success';
        if (status === 'error' || status === 'failed') return 'error';
        return 'warning';
    }

    async runTrial() {
        const weekly = parseFloat(document.getElementById('trialWeekly').value) || null;
        const daily = parseFloat(document.getElementById('trialDaily').value) || null;
        const product = document.getElementById('trialProduct').value.trim();
        const order = document.getElementById('trialOrder').value.trim();

        if (!weekly && !daily) {
            this.trialResult.textContent = '请至少输入目标周营收或目标日产量';
            return;
        }
        if (!product && !order) {
            this.trialResult.textContent = '请提供产品编码或订单号以拉取参考参数';
            return;
        }

        this.trialResult.textContent = '计算中...';
        try {
            const payload = {
                target_weekly_revenue: weekly,
                target_daily_units: daily,
                product_code: product || null,
                order_id: order || null
            };
            const data = await this.fetchJson(this.API_TRIAL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            this.renderTrialResult(data);
        } catch (error) {
            console.error('试算失败', error);
            this.trialResult.textContent = `试算失败：${error.message}`;
        }
    }

    renderTrialResult(data) {
        const lines = [];
        const product = data.product || {};
        lines.push(`产品：${product.product_name || product.product_code || '--'}（订单 ${product.order_id || '--'}）`);
        if (data.trial?.type === 'by_weekly_revenue') {
            lines.push(`目标周营收：¥${data.inputs?.target_weekly_revenue || 0}`);
            lines.push(`建议日产出：${data.trial.required_units_per_day} 件/天`);
        } else if (data.trial?.type === 'by_daily_units') {
            lines.push(`目标日产：${data.inputs?.target_daily_units || 0} 件`);
            lines.push(`预计周营收：¥${data.trial.expected_weekly_revenue}`);
        } else if (data.trial?.type === 'by_order_quantity') {
            lines.push(`订单总量：${data.trial.assumptions?.order_quantity || 0}`);
            lines.push(`可用天数：${data.trial.assumptions?.available_days || 0}`);
            lines.push(`建议日产出：${data.trial.required_units_per_day} 件/天`);
        } else if (data.trial?.message) {
            lines.push(data.trial.message);
        }
        if (data.history?.length) {
            lines.push('');
            lines.push('近30天交付参考：');
            data.history.slice(0, 3).forEach(item => {
                lines.push(`• ${item.date || item.timestamp}: ${item.quantity || item.units} 件`);
            });
        }
        this.trialResult.textContent = lines.join('\n');
    }
}

window.addEventListener('DOMContentLoaded', () => {
    new ErpBpmConsole();
});


