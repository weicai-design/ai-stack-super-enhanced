/**
 * 备忘录功能
 */

const API_BASE = '/api/super-agent';

class MemoManager {
    constructor() {
        this.memos = [];
        this.init();
    }

    init() {
        const refreshBtn = document.getElementById('refresh-memos');
        refreshBtn.addEventListener('click', () => this.loadMemos());
        
        this.loadMemos();
    }

    async loadMemos() {
        try {
            const response = await fetch(`${API_BASE}/memos`);
            const data = await response.json();
            this.memos = data.memos || [];
            this.renderMemos();
        } catch (error) {
            console.error('加载备忘录失败:', error);
        }
    }

    renderMemos() {
        const memosList = document.getElementById('memos-list');
        if (this.memos.length === 0) {
            memosList.innerHTML = '<div class="empty-state">暂无备忘录</div>';
            return;
        }

        memosList.innerHTML = this.memos.map(memo => `
            <div class="memo-item">
                <div class="memo-content">${memo.content}</div>
                <div class="memo-meta">
                    <span class="memo-type">${memo.type}</span>
                    <span class="memo-time">${new Date(memo.created_at).toLocaleString()}</span>
                </div>
            </div>
        `).join('');
    }
}

// 初始化备忘录管理器
const memoManager = new MemoManager();

