const API_BASE = '/api/super-agent';

class ThreeLevelExplorer {
    constructor() {
        this.modules = [];
        this.activeModule = null;
        this.activeStage = null;
        this.activeView = null;

        this.moduleListEl = document.getElementById('module-list');
        this.stageListEl = document.getElementById('stage-list');
        this.viewListEl = document.getElementById('view-list');
        this.viewDataEl = document.getElementById('view-data');
        this.capabilityEl = document.getElementById('capability-data');
    }

    async init() {
        await this.loadModules();
        if (this.modules.length > 0) {
            this.selectModule(this.modules[0].id);
        }
    }

    async loadModules() {
        try {
            const resp = await fetch(`${API_BASE}/modules/tree`);
            if (!resp.ok) throw new Error(`加载模块失败: ${resp.status}`);
            const data = await resp.json();
            this.modules = data.modules || [];
            this.renderModules();
        } catch (error) {
            this.moduleListEl.innerHTML = `<li style="color:#f55;">${error.message}</li>`;
        }
    }

    renderModules() {
        this.moduleListEl.innerHTML = '';
        this.modules.forEach((module) => {
            const li = document.createElement('li');
            li.className = 'tri-item';
            li.dataset.moduleId = module.id;
            li.innerHTML = `
                <div style="font-size:15px;font-weight:600;">${module.icon || ''} ${module.name}</div>
                <small>${module.description || ''}</small>
                ${
                    module.summary
                        ? `<small>• ${module.summary.primary_metric ?? '--'} ${module.summary.unit || ''}</small>`
                        : ''
                }
            `;
            li.onclick = () => this.selectModule(module.id);
            if (module.id === this.activeModule) {
                li.classList.add('active');
            }
            this.moduleListEl.appendChild(li);
        });
    }

    selectModule(moduleId) {
        if (this.activeModule === moduleId) return;
        this.activeModule = moduleId;
        this.activeStage = null;
        this.activeView = null;
        this.renderModules();
        const module = this.modules.find((m) => m.id === moduleId);
        if (!module) return;
        this.renderStages(module);
        if (module.stages && module.stages.length > 0) {
            this.selectStage(module.stages[0].id);
        }
    }

    renderStages(module) {
        this.stageListEl.innerHTML = '';
        module.stages.forEach((stage) => {
            const li = document.createElement('li');
            li.className = 'tri-item';
            li.dataset.stageId = stage.id;
            li.innerHTML = `<div style="font-size:14px;font-weight:500;">${stage.name}</div>`;
            li.onclick = () => this.selectStage(stage.id);
            if (stage.id === this.activeStage) {
                li.classList.add('active');
            }
            this.stageListEl.appendChild(li);
        });
    }

    selectStage(stageId) {
        if (this.activeStage === stageId) return;
        this.activeStage = stageId;
        this.activeView = null;
        const module = this.modules.find((m) => m.id === this.activeModule);
        if (!module) return;
        const stage = module.stages.find((s) => s.id === stageId);
        if (!stage) return;
        this.renderStages(module);
        this.renderViews(stage);
        if (stage.views && stage.views.length > 0) {
            this.selectView(stage.views[0].id);
        } else {
            this.viewListEl.innerHTML = '<li>该阶段暂无视图</li>';
        }
    }

    renderViews(stage) {
        this.viewListEl.innerHTML = '';
        stage.views.forEach((view) => {
            const li = document.createElement('li');
            li.className = 'tri-item';
            li.dataset.viewId = view.id;
            li.innerHTML = `
                <div style="font-weight:500;">${view.name}</div>
                <small>${view.description || ''}</small>
            `;
            li.onclick = () => this.selectView(view.id);
            if (view.id === this.activeView) {
                li.classList.add('active');
            }
            this.viewListEl.appendChild(li);
        });
    }

    async selectView(viewId) {
        if (!this.activeModule || !this.activeStage) return;
        this.activeView = viewId;
        const stage = this.getCurrentStage();
        if (!stage) return;
        this.renderViews(stage);
        await this.loadViewData(this.activeModule, this.activeStage, viewId);
    }

    getCurrentStage() {
        const module = this.modules.find((m) => m.id === this.activeModule);
        if (!module) return null;
        return module.stages.find((s) => s.id === this.activeStage) || null;
    }

    async loadViewData(moduleId, stageId, viewId) {
        this.viewDataEl.innerHTML = '<div class="detail-block"><p style="margin:0;color:#888;">加载中...</p></div>';
        try {
            const resp = await fetch(
                `${API_BASE}/modules/view-data?module=${encodeURIComponent(moduleId)}&stage=${encodeURIComponent(
                    stageId
                )}&view=${encodeURIComponent(viewId)}`
            );
            if (!resp.ok) throw new Error(`加载视图失败: ${resp.status}`);
            const data = await resp.json();
            this.renderViewData(data.data || {});
            await this.loadViewCapabilities(moduleId, stageId, viewId);
        } catch (error) {
            this.viewDataEl.innerHTML = `<div class="detail-block" style="color:#f55;">${error.message}</div>`;
            this.renderCapabilities([]);
        }
    }

    renderViewData(viewData) {
        const metrics = Array.isArray(viewData.metrics) ? viewData.metrics : [];
        const insights = Array.isArray(viewData.insights) ? viewData.insights : [];
        const actions = Array.isArray(viewData.actions) ? viewData.actions : [];
        const details = viewData.details ? JSON.stringify(viewData.details, null, 2) : '暂无明细';

        const metricHtml = metrics
            .map(
                (metric) => `
                <div class="metric-card">
                    <h4>${metric.label || ''}</h4>
                    <strong>${metric.value ?? '--'}</strong>
                    ${metric.unit ? `<div style="font-size:12px;color:#999;">${metric.unit}</div>` : ''}
                </div>
            `
            )
            .join('');

        const insightHtml = insights.length
            ? `<ul style="padding-left:18px;margin:8px 0 0;">${insights.map((i) => `<li>${i}</li>`).join('')}</ul>`
            : '<p style="margin:0;color:#aaa;">暂无洞察</p>';

        const actionHtml = actions.length
            ? `<ol style="padding-left:18px;margin:8px 0 0;">${actions.map((a) => `<li>${a}</li>`).join('')}</ol>`
            : '<p style="margin:0;color:#aaa;">暂无建议</p>';

        this.viewDataEl.innerHTML = `
            <h3 style="margin-bottom:10px;">${viewData.title || '实时数据'}</h3>
            <div class="metrics-grid">
                ${metricHtml || '<div class="metric-card"><h4>指标</h4><strong>--</strong></div>'}
            </div>
            <div class="insight-panel">
                <strong>洞察</strong>
                ${insightHtml}
            </div>
            <div class="insight-panel" style="background:rgba(86,125,255,0.09);border-color:rgba(86,125,255,0.3);">
                <strong>建议/动作</strong>
                ${actionHtml}
            </div>
            <div class="detail-block">
                <strong>明细数据</strong>
                <pre>${details}</pre>
            </div>
            <p style="color:#888;font-size:12px;margin-top:8px;">更新时间：${viewData.timestamp || '--'}</p>
        `;
    }

    async loadViewCapabilities(moduleId, stageId, viewId) {
        if (!this.capabilityEl) return;
        this.capabilityEl.innerHTML = '<div class="detail-block"><p style="margin:0;color:#888;">加载能力信息...</p></div>';
        try {
            const resp = await fetch(
                `${API_BASE}/modules/view-capabilities?module=${encodeURIComponent(moduleId)}&stage=${encodeURIComponent(
                    stageId
                )}&view=${encodeURIComponent(viewId)}`
            );
            if (!resp.ok) throw new Error(`加载能力失败: ${resp.status}`);
            const data = await resp.json();
            this.renderCapabilities(data.capabilities || []);
        } catch (error) {
            this.capabilityEl.innerHTML = `<div class="detail-block" style="color:#f55;">${error.message}</div>`;
        }
    }

    renderCapabilities(list) {
        if (!this.capabilityEl) return;
        if (!list.length) {
            this.capabilityEl.innerHTML = `
                <div class="detail-block">
                    <strong>四级能力单元</strong>
                    <p style="color:#888;margin:6px 0 0;">暂无能力拆解</p>
                </div>
            `;
            return;
        }
        const items = list
            .map(
                (cap) => `
            <div style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
                <div style="font-weight:600;">${cap.name || cap.id}</div>
                <div style="font-size:12px;color:#bbb;">责任人：${cap.owner || '未指定'} · 产出：${cap.result || '--'}</div>
            </div>`
            )
            .join('');
        this.capabilityEl.innerHTML = `
            <div class="detail-block">
                <strong>四级能力单元</strong>
                <div style="margin-top:8px;">${items}</div>
            </div>
        `;
    }
}

window.addEventListener('DOMContentLoaded', () => {
    const explorer = new ThreeLevelExplorer();
    explorer.init();
    window.moduleExplorer = explorer;
});


