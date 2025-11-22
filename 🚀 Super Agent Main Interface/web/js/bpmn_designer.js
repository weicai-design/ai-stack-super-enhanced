class BpmnDesigner {
    constructor() {
        this.API = '/api/super-agent/erp/bpmn';
        this.state = {
            id: '',
            data: {
                name: '',
                version: 1,
                description: '',
                domain: 'sales',
                nodes: []
            }
        };
        this.listEl = document.getElementById('processList');
        this.previewBox = document.getElementById('previewBox');
        this.bindInputs();
        this.refreshList();
        this.renderPreview();
    }
    
    bindInputs() {
        ['processId','processName','processVersion','processDesc','processDomain'].forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            el.addEventListener('input', () => this.syncProcessForm());
        });
    }
    
    syncProcessForm() {
        this.state.id = document.getElementById('processId').value.trim();
        this.state.data.name = document.getElementById('processName').value.trim();
        this.state.data.version = Number(document.getElementById('processVersion').value || 1);
        this.state.data.description = document.getElementById('processDesc').value.trim();
        this.state.data.domain = document.getElementById('processDomain').value;
        this.renderPreview();
    }
    
    renderPreview() {
        this.previewBox.textContent = JSON.stringify({
            id: this.state.id || undefined,
            ...this.state.data
        }, null, 2);
    }
    
    async refreshList() {
        const res = await fetch(`${this.API}/processes`);
        const data = await res.json();
        this.listEl.innerHTML = '';
        (data.processes || []).forEach(proc => {
            const li = document.createElement('li');
            li.textContent = `${proc.id} · ${proc.updated_at?.slice(0, 16).replace('T',' ') || ''}`;
            li.onclick = () => this.loadProcess(proc.id);
            this.listEl.appendChild(li);
        });
    }
    
    async loadProcess(id) {
        const res = await fetch(`${this.API}/process/${id}`);
        if (!res.ok) return alert('加载失败');
        const data = await res.json();
        this.state.id = data.id;
        this.state.data = Object.assign({ nodes: [] }, data.data || {});
        document.getElementById('processId').value = data.id;
        document.getElementById('processName').value = this.state.data.name || '';
        document.getElementById('processVersion').value = this.state.data.version || 1;
        document.getElementById('processDesc').value = this.state.data.description || '';
        document.getElementById('processDomain').value = this.state.data.domain || 'sales';
        this.renderNodes();
        this.renderPreview();
        this.highlightSelected(id);
    }
    
    highlightSelected(id) {
        [...this.listEl.children].forEach(li => {
            li.classList.toggle('active', li.textContent.startsWith(id));
        });
    }
    
    newProcess() {
        this.state = {
            id: '',
            data: {
                name: '新流程',
                version: 1,
                description: '',
                domain: 'sales',
                nodes: []
            }
        };
        ['processId','processName','processVersion','processDesc'].forEach(id => {
            const el = document.getElementById(id);
            el.value = id === 'processVersion' ? 1 : '';
        });
        document.getElementById('processDomain').value = 'sales';
        this.renderNodes();
        this.renderPreview();
    }
    
    async saveProcess() {
        this.syncProcessForm();
        const body = {
            id: this.state.id || null,
            data: this.state.data
        };
        const res = await fetch(`${this.API}/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!res.ok) {
            const err = await res.text();
            return alert(`保存失败：${err}`);
        }
        const data = await res.json();
        this.state.id = data.id;
        document.getElementById('processId').value = data.id;
        alert('流程已保存');
        this.refreshList();
    }
    
    async deleteProcess() {
        if (!this.state.id) return alert('请先选择流程');
        if (!confirm(`确定删除流程 ${this.state.id} ?`)) return;
        const res = await fetch(`${this.API}/process/${this.state.id}`, { method: 'DELETE' });
        if (!res.ok) return alert('删除失败');
        alert('已删除');
        this.newProcess();
        this.refreshList();
    }
    
    addOrUpdateNode() {
        const node = {
            id: document.getElementById('nodeId').value.trim(),
            name: document.getElementById('nodeName').value.trim(),
            type: document.getElementById('nodeType').value,
            owner: document.getElementById('nodeOwner').value.trim(),
            incoming: this.splitList(document.getElementById('nodeIncoming').value),
            outgoing: this.splitList(document.getElementById('nodeOutgoing').value),
            sla_days: Number(document.getElementById('nodeSla').value || 0),
            metadata: this.parseMeta(document.getElementById('nodeMeta').value)
        };
        if (!node.id) return alert('节点ID不能为空');
        const idx = this.state.data.nodes.findIndex(n => n.id === node.id);
        if (idx >= 0) {
            this.state.data.nodes[idx] = node;
        } else {
            this.state.data.nodes.push(node);
        }
        this.clearNodeForm();
        this.renderNodes();
        this.renderPreview();
    }
    
    splitList(value) {
        return value.split(',').map(v => v.trim()).filter(Boolean);
    }
    
    parseMeta(value) {
        if (!value) return {};
        try { return JSON.parse(value); }
        catch (e) { return { note: value }; }
    }
    
    clearNodeForm() {
        ['nodeId','nodeName','nodeOwner','nodeIncoming','nodeOutgoing','nodeMeta'].forEach(id => {
            document.getElementById(id).value = '';
        });
        document.getElementById('nodeType').value = 'task';
        document.getElementById('nodeSla').value = 3;
    }
    
    renderNodes() {
        const container = document.getElementById('nodesContainer');
        container.innerHTML = '';
        (this.state.data.nodes || []).forEach(node => {
            const div = document.createElement('div');
            div.className = 'node-card';
            div.innerHTML = `
                <strong>${node.name}</strong>
                <div class="muted">ID: ${node.id} · ${node.type}</div>
                <div>负责人：${node.owner || '未指定'}</div>
                <div>SLA：${node.sla_days || 0} 天</div>
                <div class="muted">前置：${(node.incoming || []).join(', ') || '无'}</div>
                <div class="muted">后续：${(node.outgoing || []).join(', ') || '无'}</div>
                <div class="node-actions">
                    <button class="btn-secondary" onclick="designer.editNode('${node.id}')">编辑</button>
                    <button class="btn-danger" onclick="designer.removeNode('${node.id}')">删除</button>
                </div>
            `;
            container.appendChild(div);
        });
    }
    
    editNode(id) {
        const node = this.state.data.nodes.find(n => n.id === id);
        if (!node) return;
        document.getElementById('nodeId').value = node.id;
        document.getElementById('nodeName').value = node.name || '';
        document.getElementById('nodeType').value = node.type || 'task';
        document.getElementById('nodeOwner').value = node.owner || '';
        document.getElementById('nodeIncoming').value = (node.incoming || []).join(', ');
        document.getElementById('nodeOutgoing').value = (node.outgoing || []).join(', ');
        document.getElementById('nodeSla').value = node.sla_days || 0;
        document.getElementById('nodeMeta').value = node.metadata ? JSON.stringify(node.metadata) : '';
    }
    
    removeNode(id) {
        this.state.data.nodes = this.state.data.nodes.filter(n => n.id !== id);
        this.renderNodes();
        this.renderPreview();
    }
}

const designer = new BpmnDesigner();










