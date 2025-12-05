/**
 * 模块通用组件库（生产级）
 * 提供统一的列表、详情、执行界面组件
 */

// ============ API调用封装 ============

class ModuleAPI {
    constructor(moduleName, apiBase = '/api/super-agent') {
        this.moduleName = moduleName;
        this.apiBase = apiBase;
        this.apiKey = localStorage.getItem('api_key') || 'default_key';
    }

    async request(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const config = {
            ...options,
            headers: {
                'X-API-Key': this.apiKey,
                'Content-Type': 'application/json',
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return { success: true, data };
        } catch (error) {
            console.error(`API请求失败 [${endpoint}]:`, error);
            return { success: false, error: error.message };
        }
    }

    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    async post(endpoint, body = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    async put(endpoint, body = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body),
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

// ============ 列表组件 ============

class ModuleListComponent {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            pageSize: options.pageSize || 20,
            enableSearch: options.enableSearch !== false,
            enableFilter: options.enableFilter !== false,
            enableSort: options.enableSort !== false,
            enablePagination: options.enablePagination !== false,
            ...options,
        };
        this.data = [];
        this.filteredData = [];
        this.currentPage = 1;
        this.sortField = null;
        this.sortOrder = 'asc';
        this.filters = {};
    }

    render() {
        this.container.innerHTML = `
            <div class="module-list-container">
                ${this.renderToolbar()}
                ${this.renderStats()}
                ${this.renderList()}
                ${this.renderPagination()}
            </div>
        `;
    }

    renderToolbar() {
        return `
            <div class="module-toolbar">
                ${this.options.enableSearch ? `
                    <input type="text" 
                           class="module-search" 
                           id="moduleSearch" 
                           placeholder="搜索..." 
                           onkeyup="moduleList.handleSearch(event)">
                    <button class="btn btn-primary" onclick="moduleList.handleSearch()">🔍 搜索</button>
                ` : ''}
                ${this.options.enableFilter ? `
                    <select class="module-filter" id="moduleFilter" onchange="moduleList.handleFilter()">
                        <option value="">全部</option>
                        ${this.renderFilterOptions()}
                    </select>
                ` : ''}
                ${this.options.enableSort ? `
                    <select class="module-sort" id="moduleSort" onchange="moduleList.handleSort()">
                        <option value="">排序</option>
                        ${this.renderSortOptions()}
                    </select>
                ` : ''}
                <button class="btn btn-secondary" onclick="moduleList.refresh()">🔄 刷新</button>
                ${this.options.onCreate ? `
                    <button class="btn btn-primary" onclick="${this.options.onCreate}">➕ 新建</button>
                ` : ''}
            </div>
        `;
    }

    renderStats() {
        if (!this.options.showStats) return '';
        return `
            <div class="module-stats">
                <div class="stat-item">
                    <span class="stat-label">总数</span>
                    <span class="stat-value">${this.data.length}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">当前页</span>
                    <span class="stat-value">${this.filteredData.length}</span>
                </div>
            </div>
        `;
    }

    renderList() {
        const items = this.getCurrentPageData();
        
        if (items.length === 0) {
            return `
                <div class="module-empty">
                    <div class="empty-icon">📭</div>
                    <div class="empty-text">暂无数据</div>
                </div>
            `;
        }

        return `
            <div class="module-list" id="moduleListItems">
                ${items.map((item, index) => this.renderItem(item, index)).join('')}
            </div>
        `;
    }

    renderItem(item, index) {
        // 子类需要实现
        return `<div class="module-item">Item ${index}</div>`;
    }

    renderPagination() {
        if (!this.options.enablePagination) return '';
        
        const totalPages = Math.ceil(this.filteredData.length / this.options.pageSize);
        if (totalPages <= 1) return '';

        return `
            <div class="module-pagination">
                <button class="btn btn-secondary" 
                        onclick="moduleList.goToPage(${this.currentPage - 1})"
                        ${this.currentPage === 1 ? 'disabled' : ''}>
                    上一页
                </button>
                <span class="page-info">
                    第 ${this.currentPage} / ${totalPages} 页
                </span>
                <button class="btn btn-secondary" 
                        onclick="moduleList.goToPage(${this.currentPage + 1})"
                        ${this.currentPage === totalPages ? 'disabled' : ''}>
                    下一页
                </button>
            </div>
        `;
    }

    renderFilterOptions() {
        // 子类需要实现
        return '';
    }

    renderSortOptions() {
        // 子类需要实现
        return '';
    }

    handleSearch(event) {
        if (event && event.key !== 'Enter') return;
        
        const query = document.getElementById('moduleSearch')?.value.toLowerCase() || '';
        this.filteredData = this.data.filter(item => 
            this.searchItem(item, query)
        );
        this.currentPage = 1;
        this.updateList();
    }

    searchItem(item, query) {
        // 子类需要实现
        return true;
    }

    handleFilter() {
        const filterValue = document.getElementById('moduleFilter')?.value || '';
        // 子类需要实现过滤逻辑
        this.currentPage = 1;
        this.updateList();
    }

    handleSort() {
        const sortValue = document.getElementById('moduleSort')?.value || '';
        if (!sortValue) return;
        
        const [field, order] = sortValue.split(':');
        this.sortField = field;
        this.sortOrder = order || 'asc';
        this.sortData();
        this.updateList();
    }

    sortData() {
        if (!this.sortField) return;
        
        this.filteredData.sort((a, b) => {
            const aVal = this.getItemValue(a, this.sortField);
            const bVal = this.getItemValue(b, this.sortField);
            
            if (this.sortOrder === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
    }

    getItemValue(item, field) {
        // 子类需要实现
        return item[field] || '';
    }

    getCurrentPageData() {
        if (!this.options.enablePagination) {
            return this.filteredData;
        }
        
        const start = (this.currentPage - 1) * this.options.pageSize;
        const end = start + this.options.pageSize;
        return this.filteredData.slice(start, end);
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredData.length / this.options.pageSize);
        if (page < 1 || page > totalPages) return;
        
        this.currentPage = page;
        this.updateList();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    updateList() {
        const listContainer = this.container.querySelector('.module-list-container');
        if (listContainer) {
            listContainer.innerHTML = `
                ${this.renderToolbar()}
                ${this.renderStats()}
                ${this.renderList()}
                ${this.renderPagination()}
            `;
        }
    }

    setData(data) {
        this.data = data;
        this.filteredData = [...data];
        this.currentPage = 1;
        this.render();
    }

    refresh() {
        if (this.options.onRefresh) {
            this.options.onRefresh();
        }
    }

    showLoading() {
        this.container.innerHTML = `
            <div class="module-loading">
                <div class="loading-spinner"></div>
                <div class="loading-text">加载中...</div>
            </div>
        `;
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="module-error">
                <div class="error-icon">⚠️</div>
                <div class="error-text">${message || '加载失败'}</div>
                <button class="btn btn-primary" onclick="moduleList.refresh()">重试</button>
            </div>
        `;
    }
}

// ============ 详情组件 ============

class ModuleDetailComponent {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = options;
        this.data = null;
    }

    render() {
        if (!this.data) {
            this.showEmpty();
            return;
        }

        this.container.innerHTML = `
            <div class="module-detail-container">
                ${this.renderHeader()}
                ${this.renderInfo()}
                ${this.renderContent()}
                ${this.renderActions()}
            </div>
        `;
    }

    renderHeader() {
        return `
            <div class="module-detail-header">
                <h2>${this.getTitle()}</h2>
                <div class="header-actions">
                    ${this.renderHeaderActions()}
                </div>
            </div>
        `;
    }

    getTitle() {
        // 子类需要实现
        return '详情';
    }

    renderHeaderActions() {
        return `
            <button class="btn btn-secondary" onclick="moduleDetail.goBack()">← 返回</button>
            ${this.options.onEdit ? `
                <button class="btn btn-primary" onclick="${this.options.onEdit}">编辑</button>
            ` : ''}
        `;
    }

    renderInfo() {
        // 子类需要实现
        return '<div class="module-detail-info"></div>';
    }

    renderContent() {
        // 子类需要实现
        return '<div class="module-detail-content"></div>';
    }

    renderActions() {
        if (!this.options.actions || this.options.actions.length === 0) {
            return '';
        }

        return `
            <div class="module-detail-actions">
                ${this.options.actions.map(action => `
                    <button class="btn ${action.class || 'btn-primary'}" 
                            onclick="${action.onClick}">
                        ${action.label}
                    </button>
                `).join('')}
            </div>
        `;
    }

    setData(data) {
        this.data = data;
        this.render();
    }

    goBack() {
        if (this.options.onBack) {
            this.options.onBack();
        } else {
            window.history.back();
        }
    }

    showLoading() {
        this.container.innerHTML = `
            <div class="module-loading">
                <div class="loading-spinner"></div>
                <div class="loading-text">加载中...</div>
            </div>
        `;
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="module-error">
                <div class="error-icon">⚠️</div>
                <div class="error-text">${message || '加载失败'}</div>
                <button class="btn btn-primary" onclick="moduleDetail.load()">重试</button>
            </div>
        `;
    }

    showEmpty() {
        this.container.innerHTML = `
            <div class="module-empty">
                <div class="empty-icon">📭</div>
                <div class="empty-text">暂无数据</div>
            </div>
        `;
    }
}

// ============ 执行组件 ============

class ModuleExecuteComponent {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = options;
        this.formData = {};
    }

    render() {
        this.container.innerHTML = `
            <div class="module-execute-container">
                ${this.renderHeader()}
                ${this.renderForm()}
                ${this.renderResult()}
            </div>
        `;
    }

    renderHeader() {
        return `
            <div class="module-execute-header">
                <h2>${this.options.title || '执行操作'}</h2>
            </div>
        `;
    }

    renderForm() {
        // 子类需要实现
        return `
            <div class="module-execute-form">
                <form id="executeForm" onsubmit="moduleExecute.handleSubmit(event)">
                    ${this.renderFormFields()}
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">执行</button>
                        <button type="button" class="btn btn-secondary" onclick="moduleExecute.reset()">重置</button>
                    </div>
                </form>
            </div>
        `;
    }

    renderFormFields() {
        // 子类需要实现
        return '';
    }

    renderResult() {
        if (!this.result) return '';
        
        return `
            <div class="module-execute-result">
                <h3>执行结果</h3>
                <div class="result-content">
                    ${this.formatResult(this.result)}
                </div>
            </div>
        `;
    }

    formatResult(result) {
        // 子类需要实现
        return JSON.stringify(result, null, 2);
    }

    handleSubmit(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        this.formData = Object.fromEntries(formData);
        
        this.execute();
    }

    async execute() {
        this.showLoading();
        
        try {
            if (this.options.onExecute) {
                const result = await this.options.onExecute(this.formData);
                this.result = result;
                this.render();
            }
        } catch (error) {
            this.showError(error.message);
        }
    }

    reset() {
        const form = document.getElementById('executeForm');
        if (form) {
            form.reset();
        }
        this.formData = {};
        this.result = null;
        this.render();
    }

    showLoading() {
        const resultContainer = this.container.querySelector('.module-execute-result');
        if (resultContainer) {
            resultContainer.innerHTML = `
                <h3>执行结果</h3>
                <div class="module-loading">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">执行中...</div>
                </div>
            `;
        }
    }

    showError(message) {
        const resultContainer = this.container.querySelector('.module-execute-result');
        if (resultContainer) {
            resultContainer.innerHTML = `
                <h3>执行结果</h3>
                <div class="module-error">
                    <div class="error-icon">⚠️</div>
                    <div class="error-text">${message || '执行失败'}</div>
                </div>
            `;
        }
    }
}

// ============ 样式 ============

const moduleComponentsStyles = `
<style>
.module-list-container, .module-detail-container, .module-execute-container {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.module-toolbar {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.module-search, .module-filter, .module-sort {
    padding: 10px 15px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 14px;
}

.module-stats {
    display: flex;
    gap: 20px;
    margin-bottom: 20px;
    padding: 15px;
    background: #f9fafb;
    border-radius: 8px;
}

.stat-item {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.stat-label {
    font-size: 12px;
    color: #666;
}

.stat-value {
    font-size: 24px;
    font-weight: 600;
    color: #333;
}

.module-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.module-item {
    padding: 20px;
    border: 1px solid #eee;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s;
}

.module-item:hover {
    background: #f9fafb;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.module-pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 15px;
    margin-top: 20px;
    padding: 15px;
}

.page-info {
    font-size: 14px;
    color: #666;
}

.module-loading, .module-error, .module-empty {
    text-align: center;
    padding: 60px 20px;
}

.loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 15px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.loading-text, .error-text, .empty-text {
    font-size: 14px;
    color: #666;
    margin-top: 10px;
}

.error-icon, .empty-icon {
    font-size: 48px;
    margin-bottom: 10px;
}

.module-detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid #eee;
}

.module-detail-info {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
}

.info-item {
    padding: 15px;
    background: #f9fafb;
    border-radius: 8px;
}

.info-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 5px;
}

.info-value {
    font-size: 16px;
    font-weight: 600;
    color: #333;
}

.module-detail-content {
    margin: 20px 0;
    padding: 20px;
    background: #f9fafb;
    border-radius: 8px;
}

.module-detail-actions {
    display: flex;
    gap: 10px;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 2px solid #eee;
}

.module-execute-form {
    margin: 20px 0;
}

.form-group {
    margin-bottom: 20px;
}

.form-label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 8px;
    color: #333;
}

.form-input, .form-textarea, .form-select {
    width: 100%;
    padding: 12px 15px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 14px;
    font-family: inherit;
}

.form-textarea {
    min-height: 120px;
    resize: vertical;
}

.form-actions {
    display: flex;
    gap: 10px;
    margin-top: 20px;
}

.module-execute-result {
    margin-top: 30px;
    padding: 20px;
    background: #f9fafb;
    border-radius: 8px;
}

.result-content {
    margin-top: 15px;
    padding: 15px;
    background: white;
    border-radius: 8px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.6;
    max-height: 500px;
    overflow-y: auto;
}
</style>
`;

// 注入样式
if (document.head) {
    document.head.insertAdjacentHTML('beforeend', moduleComponentsStyles);
}

