class BpmnRuntime {
    constructor() {
        this.API_BASE = '/api/super-agent/erp/bpmn/runtime';
        this.instances = [];
        this.selectedInstance = null;
        this.autoRefreshInterval = null;
        this.table = document.getElementById('instanceTable');
        this.timelineBox = document.getElementById('timelineBox');
        this.timelineHint = document.getElementById('timelineHint');
        this.bindAutoRefresh();
        this.refresh();
    }
    
    bindAutoRefresh() {
        const toggle = document.getElementById('autoRefreshToggle');
        if (!toggle) return;
        const schedule = () => {
            if (toggle.checked) {
                this.autoRefreshInterval = setInterval(() => this.refresh(false), 8000);
            } else if (this.autoRefreshInterval) {
                clearInterval(this.autoRefreshInterval);
                this.autoRefreshInterval = null;
            }
        };
        toggle.addEventListener('change', schedule);
        schedule();
    }
    
    async refresh(showToast = true) {
        try {
            const res = await fetch(`${this.API_BASE}/instances`);
            const data = await res.json();
            this.instances = data.instances || [];
            this.renderInstances();
            this.renderStats();
            if (showToast) {
                console.log('runtime refreshed');
            }
            if (this.selectedInstance) {
                this.loadInstance(this.selectedInstance);
            }
        } catch (error) {
            console.error('加载运行数据失败', error);
            this.table.innerHTML = `<tr><td colspan="5" class="muted">加载失败：${error.message}</td></tr>`;
        }
    }
    
    renderStats() {
        const active = this.instances.length;
        const events = this.instances.reduce((sum, inst) => sum + (inst.events_count || 0), 0);
        const success = this.instances.filter(inst => inst.last_status === 'completed').length;
        const successRate = active ? Math.round(success / active * 100) + '%' : '0%';
        document.getElementById('statActive').textContent = active;
        document.getElementById('statEvents').textContent = events;
        document.getElementById('statSuccess').textContent = successRate;
        document.getElementById('statDuration').textContent = this.estimateDuration();
    }
    
    estimateDuration() {
        if (!this.instances.length) return '-';
        const durations = this.instances
            .map(inst => {
                const start = inst.started_at || inst.updated_at;
                if (!start || !inst.updated_at) return null;
                try {
                    return (new Date(inst.updated_at) - new Date(start)) / 1000 / 60;
                } catch {
                    return null;
                }
            })
            .filter(Boolean);
        if (!durations.length) return '-';
        const avg = durations.reduce((a, b) => a + b, 0) / durations.length;
        return `${Math.round(avg)} min`;
    }
    
    renderInstances() {
        if (!this.instances.length) {
            this.table.innerHTML = '<tr><td colspan="5" class="muted">暂无运行中的流程实例</td></tr>';
            return;
        }
        this.table.innerHTML = '';
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
            tr.onclick = () => this.loadInstance(inst.instance_id);
            this.table.appendChild(tr);
        });
    }
    
    renderStatus(status) {
        const map = {
            completed: 'success',
            started: 'warning',
            error: 'error',
            failed: 'error'
        };
        const cls = map[status] || 'warning';
        return `<span class="tag ${cls}">${status || 'unknown'}</span>`;
    }
    
    async loadInstance(instanceId) {
        try {
            const res = await fetch(`${this.API_BASE}/instance/${instanceId}`);
            if (!res.ok) throw new Error('实例不存在');
            const data = await res.json();
            this.selectedInstance = instanceId;
            this.timelineHint.textContent = `${instanceId} · 正在查看 ${data.instance?.current_node || ''}`;
            this.renderTimeline(data.events || []);
        } catch (error) {
            this.timelineBox.innerHTML = `<div class="muted">加载实例失败：${error.message}</div>`;
        }
    }
    
    renderTimeline(events) {
        if (!events.length) {
            this.timelineBox.innerHTML = '<div class="muted">暂无事件</div>';
            return;
        }
        this.timelineBox.innerHTML = '';
        events.forEach(evt => {
            const div = document.createElement('div');
            div.className = 'timeline-item';
            div.innerHTML = `
                <h4>${evt.node_name || evt.node_id}</h4>
                <div class="muted">${evt.timestamp || ''}</div>
                <p>${evt.message || '无描述'}</p>
                ${evt.status ? `<span class="tag ${this.statusClass(evt.status)}">${evt.status}</span>` : ''}
            `;
            this.timelineBox.appendChild(div);
        });
    }
    
    statusClass(status) {
        if (status === 'completed') return 'success';
        if (status === 'error') return 'error';
        return 'warning';
    }
}

const runtime = new BpmnRuntime();










