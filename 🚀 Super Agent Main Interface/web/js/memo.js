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
        // 检查元素是否存在
        const refreshBtn = document.getElementById('refresh-memos');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadMemos());
        }
        
        // 延迟加载，等待DOM完全加载
        setTimeout(() => {
            this.loadMemos();
        }, 500);
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
        const memosList = document.getElementById('memo-list');
        if (!memosList) {
            console.warn('备忘录列表元素不存在');
            return;
        }
        
        // 如果API返回了数据，使用API数据
        if (this.memos.length > 0) {
            memosList.innerHTML = this.memos.map(memo => `
                <div class="memo-item">
                    <div class="memo-content">${memo.content || memo.text || ''}</div>
                    <div class="memo-time">${this.formatTime(memo.created_at || memo.time)}</div>
                </div>
            `).join('');
        }
        // 否则保持HTML中的默认内容
    }
    
    formatTime(timeStr) {
        if (!timeStr) return '刚刚';
        try {
            const date = new Date(timeStr);
            const now = new Date();
            const diff = now - date;
            const minutes = Math.floor(diff / 60000);
            const hours = Math.floor(diff / 3600000);
            
            if (minutes < 1) return '刚刚';
            if (minutes < 60) return `${minutes}分钟前`;
            if (hours < 24) return `${hours}小时前`;
            return date.toLocaleDateString('zh-CN');
        } catch (e) {
            return timeStr;
        }
    }
}

// 初始化备忘录管理器
const memoManager = new MemoManager();

