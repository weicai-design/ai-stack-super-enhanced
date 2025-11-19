class DouyinConsole {
    constructor() {
        this.API_ROOT = '/api/super-agent';
        this.status = null;
        this.jobs = [];
        this.callbacks = [];
        this.pendingState = null;
        this.bindEvents();
        this.refreshAll();
    }

    bindEvents() {
        const beginBtn = document.getElementById('btnBeginAuth');
        if (beginBtn) beginBtn.addEventListener('click', () => this.beginAuth());
        const completeBtn = document.getElementById('btnCompleteAuth');
        if (completeBtn) completeBtn.addEventListener('click', () => this.completeAuth());
        const revokeBtn = document.getElementById('btnRevokeAuth');
        if (revokeBtn) revokeBtn.addEventListener('click', () => this.revokeAuth());
        const publishBtn = document.getElementById('btnPublish');
        if (publishBtn) publishBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.publish();
        });
        const form = document.getElementById('publishForm');
        if (form) form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.publish();
        });
        const refreshJobs = document.getElementById('btnRefreshJobs');
        if (refreshJobs) refreshJobs.addEventListener('click', () => this.loadJobs());
        const refreshCallbacks = document.getElementById('btnRefreshCallbacks');
        if (refreshCallbacks) refreshCallbacks.addEventListener('click', () => this.loadCallbacks());
        const runCopyright = document.getElementById('btnRunCopyright');
        if (runCopyright) runCopyright.addEventListener('click', () => this.runCopyrightCheck());
        const btnStoryboard = document.getElementById('btnGenerateStoryboard');
        if (btnStoryboard) btnStoryboard.addEventListener('click', () => this.generateStoryboard());
    }

    async refreshAll() {
        await Promise.all([this.loadStatus(), this.loadJobs(), this.loadCallbacks()]);
    }

    async request(path, options = {}) {
        const resp = await fetch(`${this.API_ROOT}${path}`, options);
        if (!resp.ok) {
            const detail = await resp.text();
            throw new Error(detail || `HTTP ${resp.status}`);
        }
        return resp.json();
    }

    async loadStatus() {
        try {
            this.status = await this.request('/douyin/status');
            this.pendingState = this.status.pending_state;
            document.getElementById('statusAuthorized').textContent = this.status.authorized ? '✅ 已授权' : '⚠️ 未授权';
            document.getElementById('statusExpire').textContent = this.status.expires_at || '-';
            document.getElementById('statusPending').textContent = this.status.active_jobs ?? 0;
            document.getElementById('statusFailed').textContent = this.status.failed_jobs ?? 0;
            document.getElementById('statusState').textContent = this.status.pending_state || '无';
        } catch (error) {
            console.error('加载状态失败', error);
        }
    }

    async beginAuth() {
        try {
            const result = await this.request('/douyin/begin-auth', { method: 'POST' });
            this.pendingState = result.state;
            document.getElementById('statusState').textContent = result.state;
            this.writeFeedback(`🔐 已生成授权链接（state=${result.state}）。\n请在新窗口完成登录：\n${result.auth_url}`);
        } catch (error) {
            this.writeFeedback(`❌ 无法启动授权：${error.message}`);
        }
    }

    async completeAuth() {
        try {
            const code = prompt('输入抖音回调提供的 code（可自定义模拟）：', 'mock_code');
            if (!code) return;
            const state = this.pendingState || prompt('请输入state（若未知）：', '');
            if (!state) return;
            const result = await this.request('/douyin/complete-auth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, state })
            });
            this.writeFeedback(`✅ 授权完成，Token 将于 ${result.expires_at} 过期。`);
            await this.loadStatus();
        } catch (error) {
            this.writeFeedback(`❌ 完成授权失败：${error.message}`);
        }
    }

    async revokeAuth() {
        try {
            await this.request('/douyin/revoke', { method: 'POST' });
            this.writeFeedback('ℹ️ 已清除授权信息。');
            await this.loadStatus();
        } catch (error) {
            this.writeFeedback(`❌ 取消授权失败：${error.message}`);
        }
    }

    collectPublishPayload() {
        const title = document.getElementById('inputTitle').value.trim();
        const content = document.getElementById('inputContent').value.trim();
        const tagsRaw = document.getElementById('inputTags').value.trim();
        const media = document.getElementById('inputMedia').value.trim();
        const referencesRaw = document.getElementById('inputReferences').value.trim();
        const minOrig = parseFloat(document.getElementById('inputOriginality').value || '60');
        const blockSensitive = document.getElementById('inputBlockSensitive').checked;
        if (!title || !content) {
            throw new Error('标题与正文不能为空');
        }
        return {
            title,
            content,
            tags: tagsRaw ? tagsRaw.split(',').map(t => t.trim()).filter(Boolean) : [],
            media_url: media || null,
            references: referencesRaw ? referencesRaw.split(',').map(t => t.trim()).filter(Boolean) : [],
            min_originality: isNaN(minOrig) ? 60 : minOrig,
            block_sensitive: blockSensitive
        };
    }

    async publish() {
        try {
            const payload = this.collectPublishPayload();
            this.writeFeedback('⏳ 正在执行合规检测与风控...');
            const result = await this.request('/douyin/publish', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const blocks = [];
            blocks.push(`任务ID：${result.job?.job_id}`);
            blocks.push(`状态：${result.job?.status}`);
            if (result.risk) {
                blocks.push(`风险：${result.risk.level} / ${result.risk.score}`);
                if ((result.risk.flags || []).length) {
                    blocks.push(`触发：${result.risk.flags.join('；')}`);
                }
            }
            if (result.job?.last_error) {
                blocks.push(`错误：${result.job.last_error}`);
            }
            this.writeFeedback(blocks.join('\n'));
            await this.loadJobs();
            await this.loadStatus();
        } catch (error) {
            this.writeFeedback(`❌ 发布失败：${error.message}`);
        }
    }

    async loadJobs() {
        try {
            const data = await this.request('/douyin/jobs');
            this.jobs = data.jobs || [];
            this.renderJobs();
        } catch (error) {
            console.error('加载 jobs 失败', error);
            const table = document.getElementById('jobTable');
            if (table) table.innerHTML = `<tr><td colspan="6" class="muted">加载失败：${error.message}</td></tr>`;
        }
    }

    renderJobs() {
        const table = document.getElementById('jobTable');
        if (!table) return;
        if (!this.jobs.length) {
            table.innerHTML = '<tr><td colspan="6" class="muted">暂无任务</td></tr>';
            return;
        }
        table.innerHTML = '';
        this.jobs.forEach(job => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${job.job_id}</td>
                <td>${job.title}</td>
                <td>${this.renderStatusPill(job.status)}</td>
                <td>${job.attempts}/${job.max_retries}</td>
                <td>${job.next_retry_at || '-'}</td>
                <td>${this.renderJobActions(job)}</td>
            `;
            tr.addEventListener('click', () => this.showJobDetail(job));
            table.appendChild(tr);
        });
    }

    renderStatusPill(status) {
        const cls = `status-pill ${status}`;
        const map = {
            success: '成功',
            failed: '失败',
            blocked: '拦截',
            publishing: '发布中',
            queued: '排队'
        };
        return `<span class="${cls}">${map[status] || status}</span>`;
    }

    renderJobActions(job) {
        const canRetry = ['failed', 'blocked'].includes(job.status) && job.attempts < job.max_retries;
        if (!canRetry) return '<span class="muted">-</span>';
        return `<button class="btn-secondary" data-job="${job.job_id}">重试</button>`;
    }

    attachJobActionHandlers() {
        document.querySelectorAll('[data-job]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const jobId = btn.getAttribute('data-job');
                this.retryJob(jobId);
            });
        });
    }

    showJobDetail(job) {
        const detail = document.getElementById('jobDetail');
        if (!detail) return;
        detail.textContent = JSON.stringify(job, null, 2);
    }

    async retryJob(jobId) {
        if (!jobId) return;
        try {
            const result = await this.request(`/douyin/retry/${jobId}`, { method: 'POST' });
            this.writeFeedback(`🔁 已重新提交 ${jobId}，当前状态：${result.job.status}`);
            await this.loadJobs();
            await this.loadStatus();
        } catch (error) {
            this.writeFeedback(`❌ 重试失败：${error.message}`);
        }
    }

    async loadCallbacks() {
        try {
            const data = await this.request('/douyin/callbacks');
            this.callbacks = data.callbacks || [];
            this.renderCallbacks();
        } catch (error) {
            console.error('加载回调失败', error);
        }
    }

    renderCallbacks() {
        const container = document.getElementById('callbackList');
        if (!container) return;
        if (!this.callbacks.length) {
            container.innerHTML = '<div class="timeline-item"><strong>暂无事件</strong><p class="muted">等待抖音回调...</p></div>';
            return;
        }
        container.innerHTML = '';
        this.callbacks.forEach(item => {
            const div = document.createElement('div');
            div.className = 'timeline-item';
            div.innerHTML = `
                <strong>${item.event}</strong>
                <div class="muted">${item.timestamp || item.received_at || ''}</div>
                <p>${item.job_id ? `job: ${item.job_id}` : ''} ${item.status ? `状态: ${item.status}` : ''}</p>
                ${item.error ? `<p class="muted">错误：${item.error}</p>` : ''}
            `;
            container.appendChild(div);
        });
    }

    writeFeedback(text) {
        const box = document.getElementById('publishFeedback');
        if (box) {
            box.textContent = text;
        }
    }

    async runCopyrightCheck() {
        const textInput = document.getElementById('copyrightText');
        const srcInput = document.getElementById('copyrightSources');
        const platformInput = document.getElementById('copyrightPlatforms');
        const thresholdInput = document.getElementById('copyrightThreshold');
        if (!textInput || !textInput.value.trim()) {
            alert('请粘贴需要检测的文本内容');
            return;
        }
        const payload = {
            text: textInput.value.trim(),
            sources: srcInput?.value ? srcInput.value.split('\n').map(line => line.trim()).filter(Boolean) : [],
            platforms: platformInput?.value ? platformInput.value.split(',').map(p => p.trim()).filter(Boolean) : [],
            threshold: parseFloat(thresholdInput?.value || '0.75') || 0.75
        };
        const summaryBox = document.getElementById('copyrightSummary');
        const workflowBox = document.getElementById('copyrightWorkflow');
        const matchesBox = document.getElementById('copyrightMatches');
        if (matchesBox) matchesBox.textContent = '⏳ 正在执行版权检测...';
        try {
            const data = await this.request('/content/copyright/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            this.renderCopyrightSummary(data.summary);
            this.renderCopyrightWorkflow(data.workflow);
            this.renderCopyrightMatches(data.matches);
        } catch (error) {
            if (matchesBox) matchesBox.textContent = `❌ 检测失败：${error.message}`;
        }
    }

    renderCopyrightSummary(summary) {
        if (!summary) return;
        const fields = {
            copyrightRisk: summary.risk_level || '-',
            copyrightMatchesCount: summary.total_matches ?? '-',
            copyrightHighCount: summary.high_count ?? '-',
            copyrightThresholdView: summary.threshold ?? '-'
        };
        Object.entries(fields).forEach(([id, val]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
        });
        const matchesBox = document.getElementById('copyrightMatches');
        if (matchesBox) matchesBox.textContent = summary.note || '';
    }

    renderCopyrightWorkflow(workflow) {
        const container = document.getElementById('copyrightWorkflow');
        if (!container) return;
        if (!workflow?.steps?.length) {
            container.innerHTML = '<div class="timeline-item"><strong>暂无工作流记录</strong></div>';
            return;
        }
        container.innerHTML = workflow.steps.map(step => `
            <div class="timeline-item">
                <strong>${step.stage}</strong>
                <div class="muted">${step.status}</div>
                <p>${step.description || ''}</p>
            </div>
        `).join('');
    }

    renderCopyrightMatches(matches) {
        const box = document.getElementById('copyrightMatches');
        if (!box) return;
        if (!matches?.length) {
            box.textContent = '未发现与参考源或平台的显著匹配。';
            return;
        }
        box.textContent = matches.map(m => {
            if (m.type === 'platform') {
                return `📺 平台 ${m.platform}: 相似度 ${(m.similarity * 100).toFixed(1)}% · 示例：${m.sample}`;
            }
            return `📚 参考源 ${m.source_id || ''}: ${(m.similarity * 100).toFixed(1)}%`;
        }).join('\n');
    }

    async generateStoryboard() {
        const conceptInput = document.getElementById('storyConcept');
        const templateSelect = document.getElementById('storyTemplate');
        if (!conceptInput || !conceptInput.value.trim()) {
            alert('请填写视频主题/创意概念');
            return;
        }
        const payload = {
            concept: conceptInput.value.trim(),
            template: templateSelect?.value || 'fast_promo'
        };
        const consoleBox = document.getElementById('storyboardConsole');
        if (consoleBox) consoleBox.textContent = '🎬 正在生成分镜脚本...';
        try {
            const data = await this.request('/content/storyboard/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            this.renderStoryboardMeta(data);
            this.renderStoryboardShots(data.shots || []);
        } catch (error) {
            if (consoleBox) consoleBox.textContent = `❌ 生成失败：${error.message}`;
        }
    }

    renderStoryboardMeta(data) {
        if (!data) return;
        const { concept, template, shots } = data;
        const mapping = {
            storyConceptView: concept || '-',
            storyTemplateView: template === 'narrative_story' ? '叙事故事线' : '快节奏推广',
            storyShotCount: shots?.length ?? 0,
            storyRhythmHint: shots && shots.length ? `${shots[0].rhythm} 起势` : '-'
        };
        Object.entries(mapping).forEach(([id, val]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
        });
    }

    renderStoryboardShots(shots) {
        const container = document.getElementById('storyboardShots');
        const consoleBox = document.getElementById('storyboardConsole');
        if (!container) return;
        if (!shots?.length) {
            container.innerHTML = '<p class="muted">尚未生成分镜。</p>';
            if (consoleBox) consoleBox.textContent = '待生成...';
            return;
        }
        container.innerHTML = shots.map(shot => `
            <div class="shot-card">
                <h4>${shot.index}. ${shot.name}</h4>
                <span>镜头语言：${shot.camera}</span>
                <span>节奏：${shot.rhythm}</span>
                <p>${shot.description}</p>
                <div class="muted">脚本：${shot.script}</div>
            </div>
        `).join('');
        if (consoleBox) consoleBox.textContent = '✅ 分镜生成完成，可复制到拍摄方案。';
    }
}

window.addEventListener('DOMContentLoaded', () => {
    const consoleApp = new DouyinConsole();
    const observer = new MutationObserver(() => {
        consoleApp.attachJobActionHandlers();
    });
    const table = document.getElementById('jobTable');
    if (table) {
        observer.observe(table, { childList: true });
    }
});

