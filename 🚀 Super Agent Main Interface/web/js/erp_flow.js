const ERP_API_BASE = '/api/super-agent/erp/process';

async function fetchJson(url) {
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error(`请求失败: ${res.status} ${res.statusText}`);
    }
    return res.json();
}

function createStageCard(stage) {
    const card = document.createElement('div');
    card.className = 'stage-card';
    card.innerHTML = `
        <div class="stage-status">${stage.status}</div>
        <h3>${stage.name}</h3>
        <div class="stage-meta">${stage.owner || '未分配'} · ${stage.duration_days || '--'} 天周期</div>
        <div class="progress-bar"><div class="progress-fill" style="width:${stage.progress || 0}%"></div></div>
        <div class="stage-meta">风险：${(stage.risks && stage.risks.length) ? stage.risks[0] : '暂无'}</div>
        <div class="stage-meta">下一步：${(stage.next_actions && stage.next_actions[0]) || '待定'}</div>
    `;
    card.addEventListener('click', () => {
        const url = new URL('erp_stage.html', window.location.href);
        url.searchParams.set('stage', stage.id);
        window.open(url.toString(), '_blank');
    });
    return card;
}

function renderTimeline(timeline) {
    const container = document.getElementById('timelineContainer');
    if (!container) return;
    if (!timeline || !timeline.length) {
        container.innerHTML = '<div class="muted">暂无时间线数据</div>';
        return;
    }
    container.innerHTML = '';
    timeline.forEach(item => {
        const div = document.createElement('div');
        div.className = 'timeline-item';
        div.innerHTML = `
            <h4>${item.title}</h4>
            <div class="timeline-meta">${item.timestamp || ''} · 阶段：${item.stage}</div>
            <p>${item.summary || ''}</p>
            ${item.impact ? `<span class="timeline-impact">${item.impact}</span>` : ''}
        `;
        container.appendChild(div);
    });
}

function renderStageLinks(stages) {
    const container = document.getElementById('stageLinks');
    if (!container) return;
    container.innerHTML = '';
    stages.forEach(stage => {
        const url = new URL('erp_stage.html', window.location.href);
        url.searchParams.set('stage', stage.id);
        const link = document.createElement('a');
        link.href = url.toString();
        link.target = '_blank';
        link.innerHTML = `
            <div class="link-card">
                <div style="font-weight:600;">${stage.name}</div>
                <div class="muted" style="margin-top:4px;">${stage.status} · ${stage.progress || 0}%</div>
            </div>
        `;
        container.appendChild(link);
    });
}

function updateSummary(stages) {
    if (!stages || !stages.length) return;
    const current = stages.find(s => s.status === 'in_progress') || stages.find(s => s.status === 'planned') || stages[0];
    const progressSum = stages.reduce((sum, s) => sum + (s.progress || 0), 0);
    const riskItems = stages.flatMap(s => s.risks || []);
    const riskText = riskItems.length ? `${riskItems.length} 项事项` : '无高风险';
    const overall = `${Math.round(progressSum / stages.length)}%`;
    
    const stageEl = document.getElementById('currentStage');
    const overallEl = document.getElementById('overallProgress');
    const riskEl = document.getElementById('riskSummary');
    if (stageEl) stageEl.textContent = current ? current.name : '-';
    if (overallEl) overallEl.textContent = overall;
    if (riskEl) riskEl.textContent = riskText;
}

async function initErpFlowOverview() {
    try {
        const [stageData, timelineData] = await Promise.all([
            fetchJson(`${ERP_API_BASE}/stages`),
            fetchJson(`${ERP_API_BASE}/timeline`)
        ]);
        const stages = stageData.stages || [];
        const stageGrid = document.getElementById('stageGrid');
        if (stageGrid) {
            stageGrid.innerHTML = '';
            stages.forEach(stage => stageGrid.appendChild(createStageCard(stage)));
        }
        renderTimeline(timelineData.timeline || []);
        renderStageLinks(stages);
        updateSummary(stages);
    } catch (error) {
        console.error('加载ERP流程数据失败', error);
        const grid = document.getElementById('stageGrid');
        if (grid) {
            grid.innerHTML = `<div class="muted">加载失败：${error.message}</div>`;
        }
    }
}

function renderStageDetail(stage) {
    const nameEl = document.getElementById('stageName');
    const infoEl = document.getElementById('stageInfo');
    const metricsEl = document.getElementById('stageMetrics');
    const timelineEl = document.getElementById('stageTimeline');
    if (nameEl) nameEl.textContent = stage.name || '-';
    if (infoEl) {
        infoEl.innerHTML = `
            <p class="muted">负责人：${stage.owner || '未分配'} · 周期：${stage.duration_days || '--'} 天</p>
            <p>状态：${stage.status} · 完成度：${stage.progress || 0}%</p>
            <p>风险：${stage.risks && stage.risks.length ? stage.risks.join('，') : '暂无'}</p>
            <p>下一步：${stage.next_actions && stage.next_actions.length ? stage.next_actions.join('，') : '待定'}</p>
            <p>文档：${stage.documents && stage.documents.length ? stage.documents.join(' / ') : '暂无'}</p>
        `;
    }
    if (metricsEl) {
        const metrics = stage.metrics || {};
        metricsEl.innerHTML = Object.keys(metrics).length
            ? Object.entries(metrics).map(([key, value]) => `<div><strong>${key}</strong>：${value}</div>`).join('')
            : '<div class="muted">暂无指标数据</div>';
    }
    if (timelineEl) {
        const logs = stage.related_timeline || [];
        timelineEl.innerHTML = logs.length
            ? logs.map(item => `
                <div class="timeline-item">
                    <h4>${item.title}</h4>
                    <div class="timeline-meta">${item.timestamp || ''}</div>
                    <p>${item.summary || ''}</p>
                    ${item.impact ? `<span class="timeline-impact">${item.impact}</span>` : ''}
                </div>
            `).join('')
            : '<div class="muted">该阶段尚无时间线记录</div>';
    }
}

async function initErpStagePage(stageId) {
    if (!stageId) {
        alert('缺少stage参数');
        return;
    }
    try {
        const data = await fetchJson(`${ERP_API_BASE}/stages/${stageId}`);
        if (data.stage) {
            renderStageDetail(data.stage);
        }
    } catch (error) {
        const info = document.getElementById('stageInfo');
        if (info) {
            info.innerHTML = `<div class="muted">加载失败：${error.message}</div>`;
        }
    }
}









